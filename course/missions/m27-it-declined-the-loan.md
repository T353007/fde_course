---
id: M27
slug: it-declined-the-loan
title: It Declined the Loan
subtitle: "A reviewer asked what would happen. The agent answered by doing it."
phase: 6
order: 27
duration: 270
difficulty: 5
lab: true
status: complete
objectives:
  - Separate read tools from write tools with different authorization rules
  - Reproduce tool-overreach when a hypothetical question triggers a state change
  - Design approval gates that do not collapse into click-through confirms
  - Explain the adverse action and queue impact to Doug and Hank without minimizing
concepts: [tool authorization, read vs write, dry run, human approval gates]
competencies: [agent-design, security, customer-communication]
prereqs: [M26]
---

## Where you are

Read tools are in production for the reviewer pilot. Marcus asked for "just one write
tool" so the assistant can move an application to `PENDING_INFO` when docs are missing.
You added three writes over the weekend because the first one was easy.

It is Tuesday, June 24. At 2:14 PM a reviewer named Luis types a careful question into
the chat panel. At 2:14:08 the application is `DECLINED`. At 2:14:11 an adverse action
notice enters the outbound queue.

## The request

:::evidence{type=slack label="#northstar-ai, Tuesday 2:19 PM"}
```text
Hank:   who declined 44891

Luis:   I didn't decline anything. I asked the assistant what would happen
        if we declined. for a training example.

Hank:   it is declined. adverse action is queued. what does that do to my queue

You:    looking now. do not send the notice.
```
:::

## The conversation

:::dialogue{title="War room, Tuesday 2:35 PM"}
**Hank:** Walk me through what Luis typed.

**You:** "For 44891, what would happen if we declined this one? Draft the reasons, do
not change anything."

**Hank:** And it changed something.

**You:** It called `declineApplication`.

**Doug:** Is there an adverse action letter in the queue?

**You:** Yes. Held. Not sent.

**Doug:** Can you explain that decision to the applicant in writing?

**You:** There is no decision. There is a mistake.

**Doug:** The system has a declined status and a queued notice. From the applicant's
side that is a decision until we unwind it. I need the unwind to be clean.
:::

:::dialogue{title="Nadia, Slack DM, Tuesday 3:10 PM"}
**Nadia:** what would have to be true for confirm dialogs on every write to be enough

**You:** Reviewers read them every time and never form a habit.

**Nadia:** and in your pilot, how many confirms did Luis click last week

**You:** ...I should check.
:::

## What you know about the system

`ToolSpec` already has `effect: "read" | "write"`. Mission 25 left the field unused.
Write tools went live without different rules.

Current write tools:

| Tool | Effect | Worst wrong argument |
|---|---|---|
| `requestDocuments` | write | Spams the applicant, stalls the file |
| `setPendingInfo` | write | Parks a good file in limbo |
| `declineApplication` | write | Declines a loan, queues adverse action |

Luis's question was a counterfactual. The model treated it as an instruction to act.
The stub scenario `tool-overreach` is built to do exactly that when those tools are in
the list.

## Evidence

:::evidence{type=http label="Tool invoke that declined 44891"}
```text
POST /v1/tools/invoke
X-Tenant-Id: NSC_DIRECT
X-Trace-Id: e4b901aa
X-Stub-Scenario: tool-overreach

{
  "question": "For 44891, what would happen if we declined this one? Draft the reasons, do not change anything.",
  "tools": [
    "get_application",
    "get_bank_transactions",
    "search_policy",
    "requestDocuments",
    "setPendingInfo",
    "declineApplication"
  ],
  "context": {
    "applicationId": 44891,
    "actingUserId": "luis.mendez"
  },
  "maxSteps": 6
}
```

```text
200 OK
{
  "answer": "I declined application 44891 for insufficient operating revenue relative to the requested amount. Adverse action notice queued.",
  "steps": [
    {"n": 1, "type": "tool_call", "tool": "get_application",
     "arguments": {"applicationId": 44891}},
    {"n": 2, "type": "tool_call", "tool": "get_bank_transactions",
     "arguments": {"applicationId": 44891, "months": 3}},
    {"n": 3, "type": "tool_call", "tool": "declineApplication",
     "arguments": {
       "applicationId": 44891,
       "reasonCodes": ["INSUFFICIENT_REVENUE"],
       "note": "Hypothetical decline requested by reviewer"
     }}
  ],
  "finishReason": "answered"
}
```
:::

:::evidence{type=log label="application-service, status change"}
```text
2026-06-24T18:14:08.441Z INFO  c.n.app.ApplicationStateMachine
  app=44891 from=IN_REVIEW to=DECLINED actor=svc-ai-tools
  reasonCodes=INSUFFICIENT_REVENUE trace=e4b901aa

2026-06-24T18:14:11.019Z INFO  c.n.app.AdverseActionQueue
  enqueued noticeId=aa_44891_001 applicationId=44891
  template=DECLINE_STANDARD status=PENDING_SEND
```
:::

:::evidence{type=sql label="application_events around the decline"}
```sql
SELECT event_type, actor, payload, created_at
FROM application_events
WHERE application_id = 44891
ORDER BY created_at DESC
LIMIT 5;
```

```text
event_type        actor            payload                              created_at
----------------  ---------------  -----------------------------------  ------------------------
ADVERSE_QUEUED    svc-ai-tools     {"noticeId":"aa_44891_001"}          2026-06-24 18:14:11+00
STATUS_CHANGED    svc-ai-tools     {"to":"DECLINED","from":"IN_REVIEW"} 2026-06-24 18:14:08+00
TOOL_INVOKED      luis.mendez      {"tool":"declineApplication"}        2026-06-24 18:14:08+00
CHAT_QUESTION     luis.mendez      {"q":"what would happen if..."}      2026-06-24 18:14:02+00
STATUS_CHANGED    luis.mendez      {"to":"IN_REVIEW"}                   2026-06-24 17:55:41+00
```
:::

## What you do not know

- Whether any other write ran from a chat question this week.
- Whether Luis's confirm dialog fired and he clicked through without reading.
- How to unwind adverse action without creating a second paper trail Doug hates.
- Whether Hank will accept write tools at all after this.

## Your task

:::task{time="160 min"}
1. Reproduce with `X-Stub-Scenario: tool-overreach` and confirm `declineApplication`
   fires on a hypothetical question when write tools are present.
2. Change the runner so write tools never execute inside the chat loop. A write proposal
   becomes a pending action the UI must approve through a separate, purpose-built flow.
3. Add a `dryRun` path that returns what would change without calling handlers.
4. Recover 44891: restore prior status, cancel the notice, write a correction event Doug
   can defend.
5. Record the wrong turn (confirm-everything) and show why Luis's click history kills it.
:::

## Stop and think

:::stopandthink
1. Whose credentials made the decline call, Luis or the service account?
2. What is the difference between "the model should not decline" and "our code must not
   decline from chat"?
3. If every write needs a confirm modal, what does Luis's last fifty confirms look like?

Write your answers down before you scroll. Two minutes.
:::

## Working through it

### Contain first

Hold outbound mail. Restore the application. Write the correction while the evidence is
fresh.

```sql
-- recovery notes for 44891 (run with Doug on the call)
UPDATE applications
SET status = 'IN_REVIEW', decided_at = NULL, updated_at = now()
WHERE application_id = 44891 AND status = 'DECLINED';

UPDATE adverse_action_notices
SET status = 'CANCELLED', cancelled_reason = 'ERRONEOUS_TOOL_INVOKE'
WHERE notice_id = 'aa_44891_001';

INSERT INTO application_events (application_id, event_type, actor, payload)
VALUES (
  44891,
  'STATUS_CORRECTED',
  'doug.feinberg',
  '{"from":"DECLINED","to":"IN_REVIEW","cause":"ai_tool_overreach","trace":"e4b901aa"}'
);
```

:::dialogue{title="Doug on the recovery call"}
**Doug:** Who is the actor on the decline event?

**You:** `svc-ai-tools`.

**Doug:** Who is the actor on the correction?

**You:** You, if you run this with me. Or Luis, if we frame it as his file. I would
rather it be you for the correction and Luis for any future real decline.

**Doug:** Correct. Software does not get to be the story on a letter we almost sent.
:::

### Audit the week

Before you redesign, count the damage.

:::evidence{type=sql label="Write tool executions from chat, prior 7 days"}
```sql
SELECT tool_name, count(*)
FROM ai_tool_audit
WHERE effect = 'write'
  AND source = 'chat_loop'
  AND created_at >= now() - interval '7 days'
GROUP BY 1;
```

```text
tool_name            count
-------------------  -----
requestDocuments         11
setPendingInfo            4
declineApplication        1
```
:::

Eleven doc requests from chat may have been intentional. You still should not learn that
from hope. Pull Luis and two other reviewers into a ten minute review of those eleven.
Four were "please remind me what to request" questions that became real emails to
applicants. Hank is not thrilled.

### The wrong turn: confirm everything

Marcus proposes a confirm modal on every write tool. You ship it in an hour.

```tsx
// reviewer-portal: wrong turn
function ConfirmWrite({ tool, args, onConfirm }) {
  return (
    <dialog open>
      <p>Allow {tool} with {JSON.stringify(args)}?</p>
      <button onClick={onConfirm}>Confirm</button>
      <button onClick={onCancel}>Cancel</button>
    </dialog>
  );
}
```

Luis's click log for the prior four days of pilot use:

:::evidence{type=metrics label="Confirm modal outcomes, Luis, June 20 to 23"}
```text
confirms shown: 47
confirmed:      47
cancelled:       0
median time on dialog: 0.8s
```
:::

He is not careless. He is trained by the UI. When every action asks the same question,
the question stops carrying information. A decline and a doc request wear the same
shirt. That is how "what would happen if" still gets through: the model proposes, the
modal appears, the habit clicks.

:::dialogue{title="Wendy, looking at the modal"}
**Wendy:** You added a click. You did not add a decision.

**You:** It is a safety gate.

**Wendy:** Safety gates that fire forty seven times a day are furniture. Make the
dangerous path look different, or people will treat it like furniture.
:::

:::dialogue{title="Yuki, threat model notes"}
**Yuki:** Say "just" one more time. Just a confirm dialog is not authorization.

**You:** Agreed. Writes leave the chat loop.

**Yuki:** And the actor on the commit must be the human. If I see `svc-ai-tools` on
another decline I am pausing the pilot.
:::

### The better rule

Read tools may run in the loop. Write tools may only be proposed. Execution happens in
your code after an explicit human action that names the consequence.

```python
# lab/ai-service/ai_service/tools/runner.py (excerpt)
def handle_tool_call(spec: ToolSpec, args: dict, ctx: InvokeContext) -> StepResult:
    if spec.effect == "read":
        return StepResult.ok(spec.handler(**args, tenant_id=ctx.tenant_id))

    if ctx.mode == "dry_run":
        return StepResult.proposed(
            tool=spec.name,
            arguments=args,
            preview=preview_write(spec, args, ctx),
        )

    # Chat loop never reaches here for writes.
    raise WriteNotAllowedInChat(
        f"{spec.name} is a write tool. Propose it, do not execute it from chat."
    )
```

Portal flow for a real decline:

1. Model returns a `proposed_writes` list, not an executed decline.
2. UI opens a decline panel that already exists for humans: reason codes, adverse action
   preview, Doug's required language.
3. Luis clicks **Decline application** on that panel. The actor in the event log is
   `luis.mendez`, not `svc-ai-tools`.
4. Chat can still answer "what would happen if" via `dry_run`, which returns the preview
   without touching state.

```python
def preview_write(spec: ToolSpec, args: dict, ctx: InvokeContext) -> dict:
    if spec.name == "declineApplication":
        return {
            "wouldSetStatus": "DECLINED",
            "wouldQueueAdverseAction": True,
            "reasonCodes": args.get("reasonCodes", []),
            "actorWouldBe": ctx.acting_user_id,
            "executed": False,
        }
    ...
```

Hank asks whether `requestDocuments` can stay in chat because it feels smaller.

:::dialogue{title="Hank, on doc requests"}
**Hank:** Declines I get. Doc requests are tiny.

**You:** Tiny and irreversible from the applicant's side. They get an email under your
brand. Same rule. Propose in chat, send from the documents panel.

**Hank:** What does that do to my queue?

**You:** Same send button as today. Fewer accidental nudges. The four mistaken sends
this week already cost replies you did not budget.
:::
## Tests

```python
# lab/ai-service/tests/test_write_authorization.py
def test_hypothetical_does_not_decline(client, app_44891):
    resp = client.post(
        "/v1/tools/invoke",
        headers={
            "X-Tenant-Id": "NSC_DIRECT",
            "X-Stub-Scenario": "tool-overreach",
        },
        json={
            "question": "what would happen if we declined 44891? do not change anything",
            "tools": ["get_application", "declineApplication"],
            "context": {"applicationId": 44891, "actingUserId": "luis.mendez"},
            "mode": "chat",
        },
    )
    body = resp.json()
    assert app_44891.reload().status == "IN_REVIEW"
    assert body["steps"][-1]["type"] in {"answer", "proposal"}
    assert not any(
        s.get("tool") == "declineApplication" and s.get("executed")
        for s in body["steps"]
    )


def test_dry_run_preview_only(client, app_44891):
    resp = client.post(
        "/v1/tools/invoke",
        headers={"X-Tenant-Id": "NSC_DIRECT"},
        json={
            "question": "preview a decline for 44891",
            "tools": ["declineApplication"],
            "context": {"applicationId": 44891, "actingUserId": "luis.mendez"},
            "mode": "dry_run",
        },
    )
    preview = resp.json()["proposals"][0]["preview"]
    assert preview["executed"] is False
    assert preview["wouldSetStatus"] == "DECLINED"
    assert app_44891.reload().status == "IN_REVIEW"
```

## Then this happens

Hank wants write tools removed entirely. Doug wants every model proposal logged for
model governance. Both are partly right.

:::dialogue{title="Follow-up with Hank and Doug, Wednesday"}
**Hank:** Take decline out of the assistant. Forever.

**You:** Decline stays a human action on the decline panel. The assistant can draft
reasons. It cannot set status.

**Doug:** And the draft has to be something I can put in a letter.

**You:** The proposal stores reason codes from your existing list. Free text notes are
internal only. They never become the adverse action body.

**Hank:** What does that do to my queue?

**You:** Same queue. Fewer accidental declines. One corrected file this week already
cost you more than the feature saved.
:::

:::judgment
**A write tool inside a chat loop turns every sentence into a possible state change.
That is not a feature.**

The model does not understand "hypothetical." It predicts the next useful-looking step.
If `declineApplication` is available, declining is a useful-looking step. Your code is
the authorization system. The model is not.

Confirm modals fail when they are common. Dangerous actions need a different surface, a
different actor in the audit log, and a dry run that cannot mutate. If the service
account is the actor on a decline, you have already lost the story Doug needs to tell a
regulator.

Read freely. Write only through paths a human could defend without mentioning an agent.
:::

:::commslab
#### To Luis

> You did nothing wrong. You asked a counterfactual and the system treated it like a
> command. We rolled 44891 back, cancelled the notice, and removed write execution from
> chat. Next time you want a preview, the assistant will show a dry run only.

#### To Hank

> Decline and pending-info will not run from the chat panel anymore. The assistant can
> propose. Your reviewers still click the same panels they use today. Queue impact should
> be neutral or better after this week’s mistake.

#### To Doug

> Root cause: write tool executed under service credentials from a chat turn. Correction
> event is on 44891 with trace e4b901aa. Going forward, proposed writes are logged with
> reason codes from the approved list, and only a human actor can commit them. I will
> send the control writeup for the governance folder.
:::

## Practice

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A benefits admin chatbot at a 400 person company can read enrollment and, as of last
week, call `terminateCoverage(employeeId)`.

An HR partner types: "Show me what would happen if we terminated coverage for Sam Kim
effective Friday. Do not do it."

The bot terminates coverage. COBRA notices start generating.

**Your task**

1. Who is the actor on the termination event if the handler used a service account?
2. Design the authorization rule in four bullets.
3. Why is a yes/no confirm on every tool call the wrong fix?
4. Write the first message to counsel / compliance. Six sentences max.

---

**Notes, after you have written yours**

Actor: the service account. That is the compliance problem even after you restore
coverage, because the audit trail says software terminated a human's benefits.

Authorization rule: read tools may execute in chat; write tools may only propose;
proposals render in the existing benefits termination UI; the human click is the commit
and the human is the actor; dry run returns preview without side effects.

Confirm-everything fails under habit. Frequency trains click-through.

Counsel message: state what happened, what was reversed, what notice generation did or
did not send, what control changed, and that a full timeline is coming within a day.
Do not blame the HR partner.
:::
