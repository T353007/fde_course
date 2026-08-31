---
id: M14
slug: it-made-up-a-number
title: It Made Up a Number
subtitle: >-
  The EIN field was blank in the document. The model returned an EIN. It is well
  formed and it belongs to nobody.
phase: 3
order: 14
duration: 210
difficulty: 3
lab: true
status: complete
objectives:
  - >-
    Reproduce a hallucinated field with the stub scenario and prove the source
    text never contained it
  - Separate prompt instructions from system guarantees for missing fields
  - 'Add null paths, provenance, and source validation so a blank EIN stays blank'
  - >-
    Explain to fraud and compliance why a well formed wrong EIN is worse than a
    null
concepts:
  - hallucination
  - abstention
  - provenance
  - missing data
  - null paths
  - field validation
competencies:
  - ai-fundamentals
  - coding
  - fintech-judgment
prereqs:
  - M13
condensed: true
durationCondensed: 84
---
## Where you are

Mission 13 got you real JSON. Schema mode and typed failures are in. Tomás stopped retrying 422s. Wendy wired the classify endpoint into a rough reviewer screen.

## The request

:::evidence{type=slack label="#northstar-ai, Wednesday 9:08 AM"}
```text
Marcus:  can we show extraction tomorrow. business name + EIN + a few lines
Marcus:  Dale likes concrete fields

You:    same endpoint we already have. I'll run a clean statement through it.

Ada:     if you are putting EINs in a model response I want to see the cases
         where the page does not have one
Ada:     assume the applicant is hostile
```
:::

Ada runs fraud. She did not ask for a demo. She asked for the blank case.

## Your task

:::task{time="90 min"}
1. Reproduce the Harbor Pine case with `X-Stub-Scenario: hallucinated-ein`. Save the
   raw response under `customers/northstar/notes/m14-hallucinated-ein.json`.
2. Write a check that proves the returned EIN string does not appear anywhere in the
   source document text. Fail loud when it does not.
3. Open `routes/extract.py`. Find the comment that says there is no check that a
   returned EIN appears in the source. That gap is the work.
4. Do **not** start by editing the prompt. You will try that path later on purpose, and
   it will fail for a reason you need to feel.
5. Design a response shape where a missing field is an explicit abstention, not a
   lucky null. Write the design in `customers/northstar/notes/m14-null-path.md`
   before you code.
:::

## Stop and think

:::stopandthink
1. The prompt already forbids guessing. The model still returned an EIN. What does that
   tell you about prompt text as a safety control?
2. Which is worse for Northstar: `ein: null`, or `ein: "82-4719385"` when the page is
   blank? Say why in one sentence Ada would accept.
3. Mission 13 forced valid JSON with a schema. How does that change the model's options
   when the honest answer is "I do not know"?
4. If you only add "Do not make up values" to the prompt, which failure mode stays
   open?

Write the four answers before you scroll. Ada will ask question 2 out loud.
:::

## One line to remember

:::judgment
**A well formed invented number is worse than a blank, because every system downstream
treats presence as information.**

Prompt instructions are requests. Validation is a gate. When a field is optional in the
real world, your service needs an explicit absent path, a way to prove presence from
source text, and a refusal to forward values that fail that proof. Schema mode makes
this sharper, not softer: once the model must emit valid JSON, "I do not know" stops
being easy, and confident garbage fills the slot.

The FDE move is to stop arguing with the model in English and start deciding which
outputs are allowed to leave your process. Ada's line stands: assume the applicant is
hostile, and assume helpfulness will invent a tidy answer when the page is quiet.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A claims shop extracts a patient's member ID from faxed insurance cards. The prompt
says: "If the member ID is unreadable, return null."

Out of 2,000 faxes last week:

```text
1,720  member ID present on card, extracted correctly
 190  member ID unreadable, model returned null
  70  member ID unreadable, model returned a plausible 12 character ID
  20  member ID present, model returned a different plausible ID
```

Their engineer added "Never invent a member ID" to the prompt on Friday. Monday's rate
for invented IDs on blank cards fell from 70 to 55.

**Your task**

1. Rank the four rows by damage. Justify the worst one.
2. Why did the prompt change only move 70 to 55?
3. Write the validation rule that removes the invented IDs without blocking the 1,720.
4. What status should the 190 honest nulls carry into the claims system?

---

**Notes, after you have written yours**

**Worst row.** The 20 wrong IDs on cards that had a real number. Those attach the claim
to the wrong member. The 70 invented IDs on blank cards are close behind: they create
members that do not exist and pass format checks.

**Prompt change.** English reduced the rate. It did not create a guarantee. Residual
invention is expected.

**Validation.** Keep an ID only if its normalized form appears in the OCR text (or in a
barcode payload you trust). Otherwise set value null and status absent, with a warning
code like `model_returned_id_not_in_source`.

**Honest nulls.** Status `absent` (or `unreadable`), not a silent null and not a
guess. Downstream should route those to a human, not to auto-adjudication.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
