---
id: M37
slug: adoption-fell-to-29-percent
title: Adoption Fell to 29 Percent
subtitle: >-
  Week 1 was 67 percent. Week 3 is 29. The model did not get worse. The workflow
  did not get better.
phase: 8
order: 37
duration: 240
difficulty: 4
lab: false
status: complete
objectives:
  - Separate model quality regressions from workflow adoption failures
  - Run user interviews that reveal friction instead of opinions about AI
  - Map the click path that makes a correct suggestion useless
  - Repair the workflow with Wendy instead of "training users harder"
concepts:
  - adoption
  - user research
  - workflow friction
  - human in the loop
  - suggestion timing
competencies:
  - adoption
  - evals
prereqs:
  - M29
  - M36
condensed: true
durationCondensed: 96
---
## Where you are

Yuki and Doug signed off on the blockers. The flag is wider. Eval dashboards still look fine. Marcus sends a chart in the channel with no caption, which is how he panics.

## The request

:::evidence{type=metrics label="Reviewer suggestion acceptance, trailing weeks"}
```text
Week 1:  67%
Week 2:  48%
Week 3:  29%

Definition Marcus used: accepted suggestions / shown suggestions
among reviewers who logged in at least once that week
```
:::

:::evidence{type=slack label="#northstar-ai, Wednesday 8:41 AM"}
```text
Marcus:  adoption is falling off a cliff
Marcus:  is the model drifting
Marcus:  should we fine tune

Hank:    my people say it slowed them down
Hank:    What does that do to my queue?

Wendy:   I filed this in Phase 6
Wendy:   six clicks to accept. suggestion arrives after they already decided

Renee:   We don't use that number.
Renee:   Meaning the suggestion. By the time I see it I already have an answer.
```
:::

## Your task

:::task{time="120 min"}
1. Recompute adoption with at least two definitions: (a) Marcus's login-based rate,
   (b) accepts among suggestions that appeared before the human decision.
2. Interview six reviewers (use the lab personas / scripts if live interviews are not
   available). Ask them to open a real case and think aloud. Do not ask "do you like
   the AI?"
3. Produce a one page friction map: where the suggestion appears, when it appears, and
   what the click path is.
4. With Wendy, propose the smallest portal change that puts accept within one click of
   the decision surface and shows the suggestion before opinion hardens.
5. Write the note to Marcus explaining why fine tuning is the wrong next spend.
:::

## Stop and think

:::stopandthink
Before you schedule model work:

1. What evidence would convince you this *is* a model quality problem?
2. What evidence do you already have that it is not?
3. If you "train the users," what are you actually refusing to fix?
4. How will you bring Marcus along without making Wendy's "I told you" into the story?

Two minutes.
:::

## One line to remember

:::judgment
**When usage falls and evals are flat, stop tuning the model and start watching the
human's hands.**

Adoption is not a vibe and it is not logins. It is whether a correct answer arrives in
time, in place, with a cheap way to act. FDEs lose months fine tuning products that
lost the workflow argument in a design review. The tell is a domain expert saying they
already decided before the UI asked. Believe them. Instrument timing. Sit beside users.
Fix the click path with the frontend lead who warned you, and keep model work for the
slices that are actually wrong.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A hospital discharge AI drafts follow-up orders. Week 1 accept rate 62 percent. Week 3
is 24 percent. Model evals are flat. Nurses say the draft appears on a different tab
after they already entered orders in the EHR. Accept takes five clicks and a confirm.
A physician executive asks for a fine-tuned model on "hospital language."

**Your task**

1. What is your primary hypothesis?
2. Which two metrics prove or kill it?
3. What do you say to the physician executive?

---

**Notes, after you have written yours**

Primary hypothesis: workflow timing and placement, not model quality. Metrics:
suggestion-ready vs first order entry time, and accept rate for drafts shown before
entry. Tell the executive fine tuning waits until the draft appears where orders are
written with one-click accept. Otherwise you will polish text nobody uses.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
