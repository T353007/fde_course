---
id: M20
slug: what-counts-as-revenue
title: What Counts as Revenue
subtitle: >-
  Five transactions. A naive sum of 252,400. The real number is 147,400. Renee
  saw it in two seconds.
phase: 4
order: 20
duration: 300
difficulty: 4
lab: true
status: complete
objectives:
  - Build a hybrid pipeline where the model classifies and code adds
  - 'Reproduce the CANON statement end to end and land on 147,400'
  - >-
    Show why overall accuracy of 96 percent still fails the cases that move
    money
  - >-
    Defend the boundary to a stakeholder who wants the model to "just do the
    math"
concepts:
  - hybrid pipelines
  - operating revenue
  - classification
  - deterministic arithmetic
  - eval slices
competencies:
  - coding
  - evals
  - fintech-judgment
  - ai-fundamentals
prereqs:
  - M19
condensed: true
durationCondensed: 120
---
## Where you are

Intake no longer clones documents. OCR no longer ships confident garbage as done. Now you have to answer the question the whole engagement was scoped around.

## The request

:::evidence{type=email label="Marcus Webb, subject: revenue demo Friday?"}
```text
Can we show Dale the AI pulling revenue off a real statement Friday?

I told him we were close. I may have set expectations a little. Just need the
number to look right on one clean example.

Marcus
```
:::

One clean example is how this always starts. The clean example is also where the
course has been pointing since Mission 01.

## Your task

:::task{time="150 min"}
1. Run the five transaction statement through `/v1/classify/transactions` with
   `LLM_PROVIDER=stub`. Confirm `operatingRevenue` is 147400.00 and
   `naiveTotalCredits` is 252400.00.
2. Write or extend unit tests for `compute_totals` that lock those two numbers in.
3. Run `make eval SUITE=txn-classification` and paste the slice table into your notes.
4. Build a side by side view Renee can check in ninety seconds: Java number, hybrid
   number, excluded lines with reasons.
5. Do not ask the model for a total. If you find a code path that still does, flag it
   and leave it alone for Mission 21.
:::

## Stop and think

:::stopandthink
1. If the model mislabels the Fastcapital line as OPERATING_REVENUE, who can explain
   the approval to the applicant in writing?
2. Why is "the model added it up correctly this time" not good enough?
3. Which slice would you put on slide one for Dale, and which would you put on slide
   two?

Write before you scroll.
:::

## One line to remember

:::judgment
**The model should never do the arithmetic.**

Not because models cannot add. Sometimes they can. Because a lending decision needs a
trail that names the two deposits that did not count, and a sum you can unit test
without a GPU. Classification is judgment. Addition is a fact. Put judgment where the
model is strong. Put facts in code.

The signature statement is small on purpose. Five lines. Anyone can add them. The
point is not the difficulty of the math. The point is that 252,400 and 147,400 are
both defensible looking numbers until you force the system to show its work. Renee
already showed her work. The software is catching up.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

An auto insurer prices renewal premiums using "annual miles driven." The mobile app
estimates miles from GPS. A legacy batch job sums raw trip lengths. A new model reads
trip summaries in English ("short commute", "weekend road trip") and outputs a single
annual miles number.

What you learn:

- Raw GPS sum for one driver: 11,400 miles.
- After removing trips that were the driver's spouse on a shared phone: 9,100.
- The model, asked for annual miles, returns 9,000 "approximately" on most runs and
  11,200 on others.
- Actuaries need a reproducible number for rate filings.
- Fraud wants a list of excluded trips with reasons, not a vibes total.
- Leadership wants "AI powered mileage" on a launch slide.

**Your task**

1. Where does the model belong in this pipeline?
2. What does code compute?
3. What do you put on the launch slide so leadership gets the AI story without
   shipping a non reproducible rate input?
4. Name the wrong turn.

---

**Notes, after you have written yours**

The model classifies trips: driver, spouse, commercial use, unclear. Code sums the
miles on trips labeled driver. The filing packet includes the excluded trips and the
rule ids. The launch slide shows a sample driver with three excluded spouse trips and
a stable total of 9,100. The wrong turn is asking the model for the annual miles
number directly because it photographs better. That path cannot survive a rate filing
or a fraud review, and it will drift run to run.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
