---
id: M16
slug: the-96-percent-that-lied
title: The 96 Percent That Lied
subtitle: "The number is real. The 84 percent of volume it comes from is the part that was never hard."
phase: 3
order: 16
duration: 240
difficulty: 4
lab: true
status: complete
objectives:
  - Read a slice report and explain why overall accuracy can be high while risk is high
  - Quantify the dollar cost of the weak slices using Northstar volume
  - Detect label noise and a Renee versus junior disagreement without discarding the set
  - Replace a single accuracy headline with a slice gate you are willing to ship on
concepts: [slice metrics, class imbalance, label noise, disagreement, risk concentration]
competencies: [evals, fintech-judgment, executive-communication]
prereqs: [M15]
---

## Where you are

Yesterday you told Janet the classifier scored 96 percent. Baseline saved. Jordan almost
emailed Dale. You stopped him, then felt slightly dramatic about it.

This morning you open the same report with the slices left on the screen.

## The request

:::evidence{type=slack label="#northstar-ai, Monday 8:44 AM"}
```text
Nadia:  look at the slice table before standup
Nadia:  overall is not the story

Marcus:  please do not make 96% go away I already told Priya it was good

You:    running the report again with slices
```
:::

## The conversation

:::dialogue{title="Nadia, voice call, Monday 9:05 AM"}
**Nadia:** Read the support column out loud.

**You:** Card settlement, fifty something cases...

**Nadia:** Volume share.

**You:** About 84 percent of the set.

**Nadia:** Accuracy on that slice.

**You:** 99 percent.

**Nadia:** Now loan proceeds.

**You:** 68 percent.

**Nadia:** So what did 96 percent mostly measure?

**You:** That we can recognize Stripe payouts.

**Nadia:** And what moves an approval by five figures?

**You:** The other slices.

*Silence for a second.*

**Nadia:** What would have to be true for 96 percent to be the number you take to Dale?
:::

## Evidence

Run the suite the way Mission 15 taught you, and this time keep the full table.

```bash
cd lab
python -m northstar_evals run --suite txn-classification --provider stub --detail
```

:::evidence{type=metrics label="txn-classification-v3 slice report (canon)"}
```text
suite          txn-classification
provider       stub
cases          60

OVERALL                 96.0%

slice                   acc     support   share of volume
card_settlement         99%     50        84%
internal_transfer       73%     4         ~
loan_proceeds           68%     4         ~
poor_ocr                61%     8         ~

# shares above are the production mix the suite is built to mirror, not
# "60 cases divided evenly." The golden set is small. The volume story is not.
```
:::

These numbers are fixed in the course bible. Do not "improve" them in your notes to make
the narrative softer.

```text
Overall accuracy ............................... 96.0%
  loan proceeds ................................ 68%
  poor OCR quality ............................. 61%
  internal transfers ........................... 73%
  standard card settlements .................... 99%
```

The 99 percent slice is 84 percent of volume. The failing slices are the ones that move
money.

:::evidence{type=log label="failures on loan_proceeds"}
```text
TX-10004  expected LOAN_PROCEEDS       predicted OPERATING_REVENUE
          desc=FASTCAPITAL LOAN   amount=75000

TX-10041  expected LOAN_PROCEEDS       predicted OTHER_CREDIT
          desc=BUSINESS LOAN DEP  amount=120000
```
:::

Renee sees the Fastcapital line in two seconds. The model called it operating revenue.
That is the Mission 20 bank statement problem peeking through early.

## What you do not know

- Exact dollars lost per mislabel in production (you will estimate, not pretend precision).
- Whether Hank will accept a queue for the weak slices.
- How many of the mismatches are bad model versus bad labels.
- Whether Dale can hear "96 percent is real and insufficient" without thinking you
  sandbagged him.

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

:::stopandthink
1. Why can overall accuracy be both correct and useless at the same time?
2. If you only report overall to Dale, what risk have you hidden?
3. About 2 percent of golden labels are wrong on purpose. If you "fix" every mismatch
   by changing the label to match the model, what have you built?
4. A loan proceeds miss on a $75,000 line: what goes wrong for Northstar if it is
   counted as operating revenue?

Answer all four before the dollar section. Question 4 is the fintech one.
:::

## Working through it

### The volume story

Card settlements are most of the traffic. That is why overall looks fine. The model is
excellent at the easy majority.

Production framing you can say out loud:

- 1,840 applications a month.
- If 84 percent of credit lines are ordinary card settlements, the headline metric is
  dominated by work that was never the hard part.
- The transfers and loan deposits are rare in the set and common in the deals that get
  argued about.

You do not need perfect counts to see the shape. You need to stop averaging them away.

### Dollar cost of the 68 percent slice

Take the signature statement shape from the course (you will meet it properly in Mission
20):

```text
Naive total of credits:        252,400
Correct operating revenue:     147,400
Excluded: transfer 30,000 + loan proceeds 75,000
```

If loan proceeds are labeled as operating revenue, revenue is overstated by $75,000 on
that file alone. Underwriting limits, pricing, and sometimes approval flip on that
swing.

:::evidence{type=spreadsheet label="back of envelope, monthly"}
```text
Assume 8% of applications include a loan-deposit style credit (conservative).
1,840 * 0.08 = 147 applications / month with a loan-like credit.

At 68% accuracy, 32% miss = about 47 applications / month.

If the median miscounted loan deposit is $60k (loan proceeds are chunky),
that is roughly $2.8M / month of credit volume with a wrong revenue story
touching the file.

Even if only one in five of those changes a decision, you still have a
decision-quality problem you cannot see in 96%.
```
:::

The point is not the exact millions. The point is that 68 percent on the money slice is
an operational incident paced slowly enough to look like a metric.

### Label noise

About 2 percent of the golden labels are wrong on purpose. That is normal for hand
labels, not a scandal.

```python
# lab/evals/scripts/m16_label_audit.py
from northstar_evals import Dataset
from northstar_evals.labeling import agreement, label_audit, suspect_labels
from northstar_evals.suites import get as get_suite

suite = get_suite("txn-classification")
ds = Dataset.load(suite.resolve_dataset_path())

print(label_audit(ds))
print(suspect_labels(ds, max_cases=10))
```

:::evidence{type=log label="labels subcommand, abbreviated"}
```text
cases=60
approx_label_noise_rate ~= 0.02
disagreements=1

TX-10057
  renee.blackwell   LOAN_PROCEEDS     confidence=high
  j.pham            OPERATING_REVENUE confidence=low
  description       "FASTCAPITAL LOAN  ACH CREDIT"
  amount            75000
```
:::

:::dialogue{title="Renee and Jordan Pham, Monday 11:30 AM"}
**You:** TX-10057. Jordan called it operating revenue. You called it loan proceeds.

**Jordan:** It says credit. It hit the operating account. I see why I clicked that.

**Renee:** We don't use that number. Fastcapital is a lender. That deposit is not sales.

**Jordan:** Nobody wrote that in the wiki.

**Renee:** I know. It is in my spreadsheet. And now it is in this row with my name on it.
:::

Renee is right. The reason was not in the policy PDF. Keep her label. Do not silently
flip Jordan's rows to match the model either. Log the disagreement. Mission 11 already
taught you where undocumented rules live.

### The wrong turn

A reasonable engineer sees 96 percent overall and 68 percent on a tiny support count and
does this:

```python
# do not do this
def flatten_for_exec(result):
    return {"accuracy": result.overall}  # slices dropped "to keep the slide clean"
```

Or the cousin mistake: delete the four loan cases from the golden set so overall climbs
to 98 and the suite "looks healthier."

Both moves optimize the metric by hiding the work. The slice with low support is not a
rounding error. It is where the dollars are.

### Tracking it down in the library

The report code is trying to teach you. `Result.report()` prints overall first, then
every slice with support and a share bar. Read `lab/evals/northstar_evals/result.py` if
you want the exact formatting. The important behavior is already on your screen: the
99 percent line carries most of the volume.

```python
# quick check you can run in a REPL from lab/evals
from northstar_evals import Dataset
from northstar_evals.suites import get as get_suite
from northstar_evals.slicing import coverage

suite = get_suite("txn-classification")
ds = Dataset.load(suite.resolve_dataset_path())
print(coverage(ds, suite.slices))
```

If `card_settlement` dominates coverage, your overall metric is mostly a card detector.
That can still be valuable. It is not a loan detector.

### Saying the number without lying

Practice this sentence until it is boring:

> Overall 96 percent on n=60. Card settlements about 99 percent and most of volume.
> Loan proceeds 68 percent, transfers 73 percent, poor OCR 61 percent. About 2 percent
> label noise. One documented disagreement, Renee correct on Fastcapital.

If a room only wants the first clause, you are in a sales meeting, not a design review.
Bring the rest anyway.

## Then this happens

:::dialogue{title="Standup, Monday 1:40 PM"}
**Marcus:** So is it 96 or not?

**You:** It is 96 overall. Card settlements are 99 and they are most of the volume.
Loan proceeds are 68. Transfers 73. Poor OCR 61.

**Marcus:** That sounds like you buried the win.

**Janet:** That sounds like he finally measured the risk.

**Hank:** What does that do to my queue?

**You:** The weak slices should go to review until the score moves. The easy majority
can flow.

**Hank:** So AI means more review for the hard ones.

**You:** AI means we stop pretending the hard ones were solved because the easy ones
score well.
:::

Marcus is quiet, which is new.

## The better version

Replace the headline with a gate the suite already knows how to express.

```python
# from the registered suite gate (lab/evals/northstar_evals/suites.py)
gate=Gate(
    min_overall=0.94,
    min_slices={
        "card_settlement": 0.97,
        "loan_proceeds": 0.65,
        "internal_transfer": 0.70,
        "poor_ocr": 0.58,
    },
    ...
)
```

```bash
python -m northstar_evals run --suite txn-classification --provider stub --gate
```

Ship criteria become: overall may be high, but loan proceeds may not fall, and a
regression on that slice fails CI even if overall still says 96.

Write the sentence you will reuse in Phase 7 when someone waves a single number again:

> Overall accuracy is dominated by the easy 84 percent. We gate the money slices.

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

:::commslab
#### To Dale (via Priya, short)

> Our classifier is at 96 percent overall on a 60 case labeled set. That number is real.
> It is also mostly the easy card settlement traffic (about 84 percent of volume at 99
> percent). The slices that change revenue sit between 61 and 73 percent today. We are
> gating those before we widen scope.

#### To Hank

> Hard cases still need underwriter eyes. The win right now is auto-handling the easy
> majority without pretending loan deposits are solved.

#### To Marcus

> Please retire the bare "96 percent" line in customer updates. Use overall plus the
> loan proceeds slice, or send people to the note. I will help rewrite the sentence.
:::

## Practice

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
