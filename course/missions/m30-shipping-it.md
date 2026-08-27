---
id: M30
slug: shipping-it
title: Shipping It
subtitle: "Flags, versioned prompts, and a rollback you can run when your hands are not steady."
phase: 7
order: 30
duration: 240
difficulty: 3
lab: true
status: complete
objectives:
  - Deploy the copilot behind a tenant-aware feature flag with a kill switch
  - Version prompts so a bad change can be pinned back without a code revert
  - Practice a rollback drill that Janet will accept as on-call ready
  - Separate config changes from binary changes in the release notes
concepts: [feature flags, prompt versioning, rollback, progressive delivery]
competencies: [production-reliability, coding, customer-communication]
prereqs: [M29]
---

## Where you are

Phase 6 left you with a copilot that proposes and a workflow that answers. Priya will
let real `NSC_DIRECT` volume touch it only behind a flag.

It is Monday, July 27. Janet wants a rollback story before any flag turns on. Sam
already named the temporary flag pattern he hates.

## The request

:::evidence{type=slack label="#northstar-ai, Monday 9:05 AM"}
```text
Priya:  show me the blast radius

Janet:  who is on call for that

Sam:    if you name the flag USE_NEW_COPILOT_V2_TEMP I will revert you myself

You:    flag name is copilot.memo.enabled, default false, tenant scoped
```
:::

## The conversation

:::dialogue{title="Release review, Monday 11:00 AM"}
**Janet:** Walk the rollback.

**You:** Flip the flag off. Portal hides the panel. API still serves drafts for a day
in case something is mid-request, then we disable the route.

**Janet:** Prompts?

**You:** `memo-draft-v1` stays pinned. If we ship `v2` and it goes bad, we set
`PROMPT_MEMO_DRAFT=memo-draft-v1` without redeploying the jar.

**Sam:** ...Ah. So you found that.

**You:** Found what?

**Sam:** People redeploy to change a paragraph. Then the redeploy includes an unrelated
migration. Keep prompts out of the binary.
:::

:::dialogue{title="Nadia, short DM"}
**Nadia:** what would have to be true for "just ship it to everyone" to be safe

**You:** That we have already failed in production once and learned nothing.
:::

## What you know about the system

Lab deploy path:

```text
make up                 # local full stack
# production-shaped path in lab/ai-service and reviewer-portal
PROMPT_MEMO_DRAFT=memo-draft-v1
FLAG_COPILOT_MEMO_ENABLED=false
FLAG_COPILOT_MEMO_TENANTS=NSC_DIRECT
```

Prompts live as files:

```text
lab/ai-service/ai_service/prompts/memo-draft-v1.txt
lab/ai-service/ai_service/prompts/memo-draft-v2.txt
```

The running service reads the active version from config, not from an import that
bakes text into a wheel without a version string.

## Evidence

:::evidence{type=schema label="Flag and prompt config"}
```text
# lab/ai-service/ai_service/config/flags.py
COPILOT_MEMO = Flag(
    key="copilot.memo.enabled",
    default=False,
    tenants_allowlist_key="copilot.memo.tenants",  # e.g. NSC_DIRECT
    owner="ai-service",
    kill_switch="copilot.memo.kill",
)

PROMPT_PINS = {
    "memo.draft": env.get("PROMPT_MEMO_DRAFT", "memo-draft-v1"),
    "extract.bank": env.get("PROMPT_EXTRACT_BANK", "extract-v3"),
}
```
:::

:::evidence{type=http label="Portal gate before render"}
```text
GET /v1/flags?keys=copilot.memo.enabled
X-Tenant-Id: NSC_DIRECT

200 OK
{"copilot.memo.enabled": true}

GET /v1/flags?keys=copilot.memo.enabled
X-Tenant-Id: BAYLINE

200 OK
{"copilot.memo.enabled": false}
```
:::

:::evidence{type=log label="Bad prompt canary, rehearsal"}
```text
2026-07-27T15:12:01Z INFO  prompt.reload name=memo-draft-v2 pin=memo.draft
2026-07-27T15:18:44Z WARN  memo.draft validation_fail rate=0.41
       promptVersion=memo-draft-v2 tenant=NSC_DIRECT
2026-07-27T15:19:02Z INFO  prompt.pin.revert name=memo-draft-v1 by=you
2026-07-27T15:19:10Z INFO  memo.draft validation_fail rate=0.02
       promptVersion=memo-draft-v1
```
:::

## What you do not know

- Whether Bayline and Cascade will demand the panel the day Dale sees a demo.
- How fast validation_fail alerts page a human in real ops (lab uses a fake alert).
- Whether Marcus will treat a flag-off as a broken promise to Dale.

## Your task

:::task{time="130 min"}
1. Wire `copilot.memo.enabled` with tenant allowlist and a global kill switch.
2. Load memo prompts by version string from disk or object storage. Pin with env/config.
3. Run the lab rollback drill: enable for `NSC_DIRECT`, ship a deliberate bad
   `memo-draft-v2`, detect validation failures, pin back to `v1`, then kill the flag.
4. Write a one-page runbook section: enable, disable, pin prompt, who to call.
5. Capture the wrong turn: changing prompt text in code and redeploying the whole
   service as the only rollback.
:::

## Stop and think

:::stopandthink
1. What is the blast radius if `BAYLINE` inherits a flag default of true by mistake?
2. Why is prompt pin faster than `git revert` + redeploy during an incident?
3. Who has authority to flip the kill switch without a product meeting?

Write answers before you scroll. Two minutes.
:::

## Working through it

### Release notes that separate concerns

Before the flag flips, you write the release note the way Janet wants it: binary change,
config change, and prompt pin as three lines, not one paragraph.

:::evidence{type=email label="Release note draft you send to Janet"}
```text
Subject: copilot memo, NSC_DIRECT canary

Binary: ai-service 2026.07.27.1 (memo draft route + flag client)
        reviewer-portal 2026.07.27.1 (panel gated on flag)

Config: copilot.memo.enabled=false (default)
        copilot.memo.tenants=NSC_DIRECT (when enabled)
        copilot.memo.kill=false

Prompt pin: PROMPT_MEMO_DRAFT=memo-draft-v1

Rollback without redeploy:
  1) copilot.memo.kill=true
  2) or PROMPT_MEMO_DRAFT=memo-draft-v1 if only the prompt is bad

On-call: ai-service primary, portal secondary for UI only
```
:::

Sam replies with one line: "good. do not merge the prompt into the jar."

### Flag evaluation

```python
# lab/ai-service/ai_service/flags.py
def enabled(flag_key: str, tenant_id: str) -> bool:
    if config.get_bool(f"{flag_key}.kill", default=False):
        return False
    if not config.get_bool(flag_key, default=False):
        return False
    allow = config.get_list(f"{flag_key}.tenants", default=[])
    if allow and tenant_id not in allow:
        return False
    return True
```

Portal hides the entry point when false. API returns `403 flag_disabled` if something
calls draft directly. Fail closed.

:::dialogue{title="Wendy, reviewing the portal gate"}
**Wendy:** If the flag is off, is the menu item gone or grayed out?

**You:** Gone. Grayed out makes people file tickets.

**Wendy:** Good. Also do not leave a dead route that 500s when someone bookmarks it.
Return a quiet empty state from the BFF and keep the API at 403 for direct callers.
:::

### Versioned prompts

```python
# lab/ai-service/ai_service/prompts/loader.py
from pathlib import Path

PROMPT_DIR = Path(__file__).parent


def load_prompt(pin_key: str) -> tuple[str, str]:
    version = PROMPT_PINS[pin_key]
    path = PROMPT_DIR / f"{version}.txt"
    if not path.exists():
        raise PromptMissing(version)
    return version, path.read_text()
```

Every completion response already carries `prompt_version` (LAB_SPEC). Keep that honest.
When Renee screenshots a bad draft, the footer must show the pin she was on. Otherwise
you will argue about code revisions that never touched the paragraph.

:::evidence{type=policy label="Prompt change rule, pasted into RUNBOOK.md"}
```text
1. New prompt file gets a new version id. Never edit memo-draft-v1 in place.
2. Eval suite memo-draft must pass on the new version before pin moves in prod.
3. Pin moves are config changes with a named owner and a chat message in #northstar-ai.
4. If validation_fail rate > 5% for 10 minutes, on-call pins previous version without
   waiting for product approval.
```
:::

### Progressive enable

You do not go from false to all of NSC_DIRECT in one click if you can avoid it. Lab
supports a percentage sticky on `actingUserId` for rehearsal.

```python
def enabled_for_user(flag_key: str, tenant_id: str, user_id: str) -> bool:
    if not enabled(flag_key, tenant_id):
        return False
    pct = config.get_int(f"{flag_key}.percent", default=100)
    if pct >= 100:
        return True
    # stable hash so the same reviewer does not flicker in and out
    return (stable_bucket(user_id) % 100) < pct
```

Monday canary plan Priya accepts: 10 percent of NSC_DIRECT reviewers for one day, then
50 percent, then 100 percent of that tenant. Bayline still off.

### The wrong turn: rollback by redeploy

You break `memo-draft-v2` in the tree, redeploy ai-service, watch validation fail, then
start a full redeploy of `v1`. Tomás points out the deploy also picks up an unrelated
dependency bump in `common-lib`. Twenty five minutes later you are still waiting on
health checks while reviewers stare at errors.

:::dialogue{title="During the bad drill"}
**Tomás:** Why is Flyway running?

**You:** It should not be.

**Tomás:** It is. The image you tagged includes a migration from the other branch.

**Janet:** This is why prompt rollback is config. Stop the drill. Pin back. Then we talk
about how that image got built.
:::

Pinning the prompt takes one config change and a process signal. Practice that until it
is boring. The redeploy path stays available for binary bugs. It is not your first move
for a paragraph that went wrong.

### Rollback drill checklist

```text
1. FLAG on for NSC_DIRECT only, percent=10
2. Pin PROMPT_MEMO_DRAFT=memo-draft-v2 (bad canary fixture in lab)
3. Confirm validation_fail rate rises in metrics
4. Pin back to memo-draft-v1
5. Confirm rate drops
6. Set copilot.memo.kill=true
7. Confirm portal hides panel and API returns flag_disabled
8. Clear kill, leave enabled=false until Priya says otherwise
9. Write the time each step took. If any step needs you personally, fix the runbook.
```

:::evidence{type=metrics label="Drill timings, Monday rehearsal"}
```text
detect validation_fail rise .......... 3 min (alert) / would have been 18 min by Slack
pin to memo-draft-v1 ................. 40 sec
kill switch .......................... 25 sec
portal empty state confirmed ......... 1 min
total reviewer-visible pain .......... ~5 min with alert, ~20 min without
```
:::
## Tests

```python
def test_flag_tenant_scoped(client):
    assert client.flags.enabled("copilot.memo.enabled", "NSC_DIRECT") is True
    assert client.flags.enabled("copilot.memo.enabled", "BAYLINE") is False


def test_kill_switch_overrides_allowlist(client):
    client.flags.set("copilot.memo.kill", True)
    assert client.flags.enabled("copilot.memo.enabled", "NSC_DIRECT") is False


def test_prompt_pin_changes_without_code_edit(monkeypatch):
    monkeypatch.setenv("PROMPT_MEMO_DRAFT", "memo-draft-v1")
    v1, _ = load_prompt("memo.draft")
    monkeypatch.setenv("PROMPT_MEMO_DRAFT", "memo-draft-v2")
    v2, _ = load_prompt("memo.draft")
    assert v1 != v2
```

## Then this happens

Marcus wants Bayline enabled for a partner demo tomorrow.

:::dialogue{title="Priya, short call"}
**Marcus:** Can't we just turn it on for Bayline for the demo?

**Priya:** Show me the blast radius.

**You:** Bayline uses the same underwriting service and a different pricing overlay.
We have not run the memo eval slice on Bayline files. Flag stays NSC_DIRECT.

**Marcus:** Dale is bringing their CEO.

**You:** Then we show NSC_DIRECT with a recorded Bayline path, or we slip the demo. We
do not widen tenant scope from a hallway request.
:::

:::dialogue{title="Jordan, after the call"}
**Jordan:** I may have set expectations. I told their AE the copilot was "rolling out."

**You:** Rolling out to NSC_DIRECT under a flag is true. Rolling out to Bayline is not.
Help me keep those sentences different in the room tomorrow.

**Jordan:** What do I say when they ask why partners are later?

**You:** Because partner brands inherit our mistakes publicly. We earn the right with
eval evidence, not with a calendar invite.
:::

Bill Tran pings you about a cron.

:::evidence{type=slack label="Bill Tran, ops"}
```text
Bill:   if your flag dies overnight do I run something by hand
You:    no. kill switch is config. if ai-service is down the panel is gone.
Bill:   good. I already have fix_stuff.sh. I do not want another one.
```
:::

## Tracking it down

After the canary day you read the invocation rows. Ten percent of reviewers produced
enough drafts to see a real validation_fail blip on one prompt experiment. The pin
worked. Two reviewers asked why the panel vanished for twenty minutes during the drill.
You update the status page snippet Wendy drafted so the empty state says "temporarily
unavailable" instead of a blank hole.

The lesson is not that flags are clever. The lesson is that every enable path needs a
matching disable path that someone else has already practiced.

:::judgment
**Ship behind a flag you can kill, with prompts you can pin, and a drill you have
already run once with witnesses.**

Production is not "the code works on my laptop." Production is the ability to stop
damage while you are stressed. Tenant-scoped flags keep a partner brand out of your
first fire. Versioned prompts keep a paragraph from forcing a binary rollback. Janet's
on-call question is answered only when someone else can follow your runbook without you
on the call.

The hallway request to "just turn it on for the demo" will return for the rest of your
career. The answer is always blast radius and evidence, never the meeting time.
:::
:::commslab
#### To Janet

> Runbook section is in `lab/ai-service/RUNBOOK.md`: enable, pin, kill. Drill completed
> with validation_fail canary. On-call is ai-service; portal only reads flags.

#### To Priya

> Copilot memo is flagged off by default, allowlisted to NSC_DIRECT when we enable,
> kill switch tested. Prompt pin is independent of deploy. Bayline stays off until eval
> evidence exists.

#### To Marcus

> Demo on NSC_DIRECT or wait. Turning on Bayline for a meeting is a scope change, not a
> toggle. I will not do it from Slack.
:::

## Practice

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A bank wants to enable an AI collections email drafter for all regions on Friday.

**Your task**

1. Name three controls you require before any region goes true.
2. What do you pin separately from the service binary?
3. Write the kill order for an incident in four steps.
4. What do you say when sales asks for global enable for a demo?

---

**Notes, after you have written yours**

Controls: flag default false, region allowlist, kill switch, eval gate per region.
Pin: prompt version (and template ids). Kill order: kill switch, verify UI/API stopped,
pin last known good prompt if needed, leave flag false until postmortem. Demo answer:
narrow scope or recorded demo, not global true.
:::
