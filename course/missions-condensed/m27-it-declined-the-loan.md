---
id: M27
slug: it-declined-the-loan
title: It Declined the Loan
subtitle: A reviewer asked what would happen. The agent answered by doing it.
phase: 6
order: 27
duration: 270
difficulty: 5
lab: true
status: complete
objectives:
  - Separate read tools from write tools with different authorization rules
  - >-
    Reproduce tool-overreach when a hypothetical question triggers a state
    change
  - Design approval gates that do not collapse into click-through confirms
  - >-
    Explain the adverse action and queue impact to Doug and Hank without
    minimizing
concepts:
  - tool authorization
  - read vs write
  - dry run
  - human approval gates
competencies:
  - agent-design
  - security
  - customer-communication
prereqs:
  - M26
condensed: true
durationCondensed: 108
---
## Where you are

Read tools are in production for the reviewer pilot. Marcus asked for "just one write tool" so the assistant can move an application to `PENDING_INFO` when docs are missing. You added three writes over the weekend because the first one was easy.

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

## One line to remember

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

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

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

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
