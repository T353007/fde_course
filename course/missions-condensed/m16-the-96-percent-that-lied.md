---
id: M16
slug: the-96-percent-that-lied
title: The 96 Percent That Lied
subtitle: >-
  The number is real. The 84 percent of volume it comes from is the part that
  was never hard.
phase: 3
order: 16
duration: 240
difficulty: 4
lab: true
status: complete
objectives:
  - >-
    Read a slice report and explain why overall accuracy can be high while risk
    is high
  - Quantify the dollar cost of the weak slices using Northstar volume
  - >-
    Detect label noise and a Renee versus junior disagreement without discarding
    the set
  - >-
    Replace a single accuracy headline with a slice gate you are willing to ship
    on
concepts:
  - slice metrics
  - class imbalance
  - label noise
  - disagreement
  - risk concentration
competencies:
  - evals
  - fintech-judgment
  - executive-communication
prereqs:
  - M15
condensed: true
durationCondensed: 96
---
## Where you are

Yesterday you told Janet the classifier scored 96 percent. Baseline saved. Jordan almost emailed Dale. You stopped him, then felt slightly dramatic about it.

## The request

:::evidence{type=slack label="#northstar-ai, Monday 8:44 AM"}
```text
Nadia:  look at the slice table before standup
Nadia:  overall is not the story

Marcus:  please do not make 96% go away I already told Priya it was good

You:    running the report again with slices
```
:::

## Your task

:::task{time="120 min"}
1. Re-run the suite and paste the full slice table into
   `customers/northstar/notes/m16-slice-report.txt`.
2. Using discovery volume (1,840 applications a month) and the canon mix, estimate how
   many applications a month touch the loan proceeds failure mode. Write the math in
   the same note.
3. Run the label audit helpers:

```bash
python -m northstar_evals labels --suite txn-classification
```

4. Find at least one case where a junior label and Renee disagree. Decide who is right
   using the source description, not job title alone. Record the case id.
5. Draft a slice gate: minimum scores you refuse to go below on
   `loan_proceeds`, `internal_transfer`, and `poor_ocr`, even if overall stays at 96.
:::

## Stop and think

:::stopandthink
1. Why can overall accuracy be both correct and useless at the same time?
2. If you only report overall to Dale, what risk have you hidden?
3. About 2 percent of golden labels are wrong on purpose. If you "fix" every mismatch
   by changing the label to match the model, what have you built?
4. A loan proceeds miss on a $75,000 line: what goes wrong for Northstar if it is
   counted as operating revenue?

Answer all four before the dollar section. Question 4 is the fintech one.
:::

## One line to remember

:::judgment
**Overall accuracy is a real number that can still hide the only failures that matter.**

When one slice is most of the volume and nearly perfect, it pulls the average up while
the rare slices stay wrong. In lending those rare slices are transfers and loan
proceeds, and they change revenue by five figures. Label noise around 2 percent is
expected. Disagreements are data. If Renee and a junior disagree, investigate the
business rule before you change the prompt or the label.

The FDE move is to put slice floors next to the headline and to refuse executive
readouts that only carry the headline. Ninety six percent lied by omission. The omit
was the support column.

Carry one operational habit out of this mission: never change a prompt because overall
ticked up. Change a prompt when a money slice moves, or when a disagreement taught you
a rule that was living only in someone's spreadsheet.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A hospital codes clinical notes into billing codes. Overall model accuracy: 97 percent.

Slices:

```text
routine follow-up codes     99% accuracy, 88% of volume
rare procedure codes        71% accuracy, 4% of volume
oncology notes              66% accuracy, 5% of volume
poor transcription          58% accuracy, 3% of volume
```

Finance loves 97 percent. Compliance asks about oncology.

**Your task**

1. Why is 97 percent the wrong steering metric?
2. Estimate qualitative risk of the 71 percent rare procedure slice.
3. You find 2 percent label noise and one oncologist vs coder disagreement. What do you
   do with the disagreement before changing the model?
4. Write a gate in one sentence for their CI.

---

**Notes, after you have written yours**

**Wrong metric.** The average is the routine work. Harm and money sit in rare and
oncology slices.

**Risk.** Wrong procedure codes drive denied claims and, worse, wrong clinical
analytics. Low support does not mean low severity.

**Disagreement.** Adjudicate with the specialist. Keep provenance. Do not average the
two labels.

**Gate.** Fail the build if oncology or rare procedure accuracy drops, even when overall
stays above 95 percent.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
