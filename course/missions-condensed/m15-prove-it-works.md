---
id: M15
slug: prove-it-works
title: Prove It Works
subtitle: >-
  Sixty labeled cases from Renee, an afternoon of work, and it immediately
  changes how you work.
phase: 3
order: 15
duration: 270
difficulty: 3
lab: true
status: complete
objectives:
  - Build a golden dataset with provenance fields that survive an argument
  - >-
    Run the northstar_evals Runner and read an overall accuracy number you can
    defend
  - Separate a demo that worked from a measurement that holds
  - Save a baseline so the next prompt change has something to regress against
concepts:
  - golden datasets
  - eval runners
  - baselines
  - labeling
  - accuracy
  - provenance
competencies:
  - evals
  - ai-fundamentals
  - coding
prereqs:
  - M14
condensed: true
durationCondensed: 108
---
## Where you are

Classification returns JSON. Extraction clears invented EINs. Marcus keeps saying the model "works" because the six statements in his deck come back clean.

## The request

:::evidence{type=slack label="#northstar-ai, Thursday 8:51 AM"}
```text
Janet:   before we wire this deeper into underwriting I want a number
Janet:   not a vibe. a measured accuracy on real-ish cases

Marcus:  the demo cases all pass

Janet:   demo cases are not a test suite
Janet:   who owns labels

You:    asking Renee for a morning
```
:::

Renee agrees to ninety minutes. She does not agree to "label everything."

## Your task

:::task{time="150 min"}
1. Export 60 transactions from the seed data with this mix: about 50 card or ordinary
   operating credits, plus transfers, loan proceeds, and a few poor OCR lines. Do not
   build a set that is only clean Stripe payouts.
2. Sit with Renee (or use her completed sheet in `data/golden/` if she already finished
   for the lab) and produce `data/golden/txn-classification-v3.jsonl` with provenance
   fields filled in.
3. Validate the file:

```bash
python -m northstar_evals validate --suite txn-classification
```

4. Run the suite against the stub provider and save the console report to
   `customers/northstar/notes/m15-first-eval.txt`.
5. Save a baseline JSON so tomorrow's prompt tweak has a floor:

```bash
python -m northstar_evals run --suite txn-classification --provider stub \
  --save-baseline baselines/txn-v3-stub.json
```
:::

## Stop and think

:::stopandthink
1. Marcus says the six demo cases pass. Why is that not an eval?
2. If you leave `labeledBy` blank to save time, what argument can you no longer have in
   Mission 16?
3. You are about to celebrate 96 percent. What single extra table would you want before
   you send Janet a message? (You may not build it yet.)
4. What happens to your baseline if you change `PROMPT_VERSION` and forget to record it
   on the run?

Write answers. Question 1 is the one people shrug at, and it is the whole point.
:::

## One line to remember

:::judgment
**A demo that works is not evidence. A labeled set with provenance is the start of
evidence.**

The habit shift is small and permanent. Before you change a prompt, you run the suite.
Before you quote a number, you say what was labeled, by whom, on which prompt version.
Sixty cases will not impress a machine learning paper. They will change how you work by
Friday, because every debate moves from "it felt better" to "the score moved" or "the
score did not."

End this mission proud of 96 percent. Keep the baseline. Do not put the number on a
slide alone. Mission 16 exists because overall accuracy is a real number that can still
lie about risk.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A collections team scores a model that predicts which invoices get paid in 30 days.
Their engineer reports "94 percent accuracy" from a notebook.

What you find:

- 200 invoices in the notebook, all from one enterprise customer with autopay.
- No `labeledBy` field. The engineer labeled them himself using the payment outcome
  after the fact.
- Prompt version not recorded. He edited the prompt twice during the notebook run.
- No baseline file. Last week's number is gone.

**Your task**

1. Name three reasons the 94 percent is not usable in a steering meeting.
2. What label provenance would you require before re-running?
3. Why is labeling from the eventual payment outcome a different task than predicting
   from the invoice text alone?
4. Write the three fields you would force into every golden row before the next demo.

---

**Notes, after you have written yours**

**Unusable.** Single customer mix, self labeled without audit, prompt changed mid run,
no baseline. Any one of those would sink it.

**Provenance.** Who labeled, when, confidence, and whether the labeler saw future
payment data.

**Leakage.** If the label is the future outcome and the model saw features that only
exist after payment events, you measured a different problem than production inference.

**Required fields.** `labeledBy`, `labeledAt`, `confidence`, plus frozen `prompt_version`
and `model` on the run record, not only on the case.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
