---
id: M29
slug: the-copilot
title: The Copilot
subtitle: >-
  Human in the loop means the human still decides. It also means the clicks have
  to be worth it.
phase: 6
order: 29
duration: 300
difficulty: 4
lab: true
status: complete
objectives:
  - >-
    Build a hitl copilot that proposes underwriting actions without committing
    them
  - Produce explanation text Doug can put near an adverse action letter
  - Hear Wendy's click complaint and record it as a real adoption risk
  - 'Ship a vertical slice reviewers will try twice, not once'
concepts:
  - human in the loop
  - explainability
  - adverse action
  - adoption seeds
competencies:
  - agent-design
  - adoption
  - fintech-judgment
prereqs:
  - M28
condensed: true
durationCondensed: 120
---
## Where you are

The assistant answers questions on a workflow for most volume. Hank still wants help on the decision itself: a drafted recommendation the underwriter accepts or rejects.

## The request

:::evidence{type=email label="Marcus Webb, subject: Copilot MVP scope"}
```text
Need the underwriting copilot in pilot by end of month.

- AI reads the file and recommends Approve / Decline / Pending info
- Shows reasons and the numbers it used
- Underwriter confirms in one click
- Logs for Doug

Jordan already told Dale we are "putting a copilot in the underwriter's hands."
Please make that sentence true.
```
:::

## Your task

:::task{time="180 min"}
1. Implement the copilot panel against `POST /v1/memo/draft` with structured proposals
   only (recommendation, reason codes from the approved enum, numbers used, citations).
2. Wire Accept so it opens the existing decision panel with fields prefilled, actor =
   the reviewer. No silent status change from ai-service.
3. Generate applicant-facing adverse action text only from selected reason codes via
   Doug's templates, never from `internalRationale`.
4. Instrument clicks: panel open, proposal shown, accept, modify, reject. You will need
   this in Mission 37.
5. Write down Wendy's complaint in the mission notes you hand Marcus. Do not sand it off.
:::

## Stop and think

:::stopandthink
1. If Accept commits in one click with no reason code screen, what does Doug lose?
2. If Accept only prefills and still needs four more clicks, what does Wendy lose?
3. Which number on the proposal would Renee refuse to show the applicant?

Write answers before you scroll. Two minutes.
:::

## One line to remember

:::judgment
**A copilot that cannot explain a decline in approved language is not ready for lending.
A copilot that takes eight clicks is not ready for reviewers.**

HITL is not a checkbox. It is a specific split: model proposes structure, human commits
state, letters use templates a compliance officer already owns. The adoption risk shows
up as friction long before it shows up as accuracy. Wendy named the failure mode while
everyone else celebrated the panel existing. Write that down. You will need it when week
three usage falls off a cliff and someone blames the model.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A mortgage shop wants a "one-click AI underwriter." Compliance requires adverse action
reasons from a fixed list. Loan officers say the current tools already take too many
clicks.

**Your task**

1. Split proposal vs commit responsibilities in five bullets.
2. What text is allowed in the applicant letter?
3. Which metric do you refuse to put in the exec deck?
4. Write Wendy's warning in one sentence for the project risk register.

---

**Notes, after you have written yours**

Proposal: recommendation, enum reason codes, numbers, citations, internal notes.
Commit: human in existing decision UI, human as actor. Letter: templates from codes
only. Refuse "panel open rate" as adoption. Risk register: reviewers will abandon a
high-click copilot by week three even if quality is fine.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
