---
id: M28
slug: workflow-or-agent
title: Workflow or Agent
subtitle: >-
  You built an agent. Then you measured it. Ninety four percent of the time it
  walked the same path.
phase: 6
order: 28
duration: 240
difficulty: 4
lab: true
status: complete
objectives:
  - Instrument an agent loop and recover the actual path distribution
  - >-
    Decide when a state machine beats an agent on latency, cost, and on-call
    clarity
  - >-
    Rewrite the dominant path as an explicit workflow without losing the hard
    cases
  - Answer Janet's on-call question with a design she can page
concepts:
  - agent vs workflow
  - path instrumentation
  - control flow
  - on-call ownership
competencies:
  - architecture
  - agent-design
  - production-reliability
prereqs:
  - M27
condensed: true
durationCondensed: 96
---
## Where you are

Write tools no longer execute from chat. The remaining assistant still plans tool calls for every question. Marcus calls it an agent in every deck. You have started to believe him.

## The request

:::evidence{type=slack label="DM from Janet Osei, Monday 8:40 AM"}
```text
Janet:  who is on call for that

You:    for the assistant?

Janet:  for the thing that decides which tools to call and when it stops.
        if it loops at 2am, who gets the page, and what do they read
```
:::

## Your task

:::task{time="140 min"}
1. Reproduce the path table from one week of `ai_invocations` / path logs in the lab
   (seed includes the 1,200 question sample).
2. Implement `UnderwritingQuestionWorkflow` for the dominant path as plain code: fetch
   application, fetch transactions, search policy, then one model call to draft the
   answer with those results already in hand.
3. Keep an agent fallback only for fingerprints outside the dominant family, behind a
   flag.
4. Write the on-call runbook section Janet asked for: what pages, what to read, how to
   disable the agent fallback.
5. Document the wrong turn: keeping the agent because the dashboard said 94 percent
   success.
:::

## Stop and think

:::stopandthink
1. If the next step is known, what does the model add on steps 1 to 3 besides latency?
2. What does Janet need at 2 a.m. that a trace of "model chose get_application" does not
   give her?
3. Where should the 6 percent document questions go on day one of the rewrite?

Write your answers before you scroll. Two minutes.
:::

## One line to remember

:::judgment
**An agent is a control flow you cannot read. Use it when you cannot write the flow.
When you can, write it.**

The interesting demo and the operable system are different shapes. Measuring path
concentration is how you tell which one you have. Ninety four percent one path is not a
trophy for the agent. It is a specification for a state machine that was hiding inside
tool traces.

Janet's question is the real acceptance test. If a senior engineer cannot say who is on
call and what they will read, you do not have a production design yet. You have a loop.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A hospital scheduling "agent" books follow-up appointments. After two weeks of path
logs:

```
findPatient>findOpenSlots>bookSlot>answer     89%
findPatient>findOpenSlots>answer (no book)     7%
other                                          4%
```

The CIO loves the agent narrative. Nursing on-call hates 2 a.m. loops.

**Your task**

1. What do you rewrite as a workflow first?
2. What stays on an agent, if anything?
3. Write Janet's equivalent question for this domain.
4. Draft the three sentence CIO update that does not sound like a retreat.

---

**Notes, after you have written yours**

Rewrite `findPatient>findOpenSlots>bookSlot` as a workflow with an explicit confirm
before `bookSlot`. Keep an agent or human handoff for the 4 percent (multi-patient,
interpreter needed, outside referral rules).

On-call question: who pages when booking loops, and what code path do they read?

CIO update: lead with reliability and time-to-book, name that the common path is now
deterministic, and keep "flexible planner" language only for the exception path.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
