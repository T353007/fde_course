---
id: M30
slug: shipping-it
title: Shipping It
subtitle: >-
  Flags, versioned prompts, and a rollback you can run when your hands are not
  steady.
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
concepts:
  - feature flags
  - prompt versioning
  - rollback
  - progressive delivery
competencies:
  - production-reliability
  - coding
  - customer-communication
prereqs:
  - M29
condensed: true
durationCondensed: 96
---
## Where you are

Phase 6 left you with a copilot that proposes and a workflow that answers. Priya will let real `NSC_DIRECT` volume touch it only behind a flag.

## The request

:::evidence{type=slack label="#northstar-ai, Monday 9:05 AM"}
```text
Priya:  show me the blast radius

Janet:  who is on call for that

Sam:    if you name the flag USE_NEW_COPILOT_V2_TEMP I will revert you myself

You:    flag name is copilot.memo.enabled, default false, tenant scoped
```
:::

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

## One line to remember

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

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

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

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
