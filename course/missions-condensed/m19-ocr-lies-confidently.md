---
id: M19
slug: ocr-lies-confidently
title: OCR Lies Confidently
subtitle: >-
  OptiScan returns clean JSON, a 0.96 confidence score, and the wrong amount.
  The score never blinked.
phase: 4
order: 19
duration: 270
difficulty: 4
lab: true
status: complete
objectives:
  - >-
    Prove that vendor OCR confidence does not predict accuracy on real Northstar
    documents
  - >-
    Build reconciliation checks that catch confident wrong extractions before
    they reach underwriting
  - >-
    Choose a fallback path that routes bad pages to a human instead of more
    prompting
  - Resist the urge to fix a broken OCR vendor with prompt tuning
concepts:
  - OCR
  - confidence calibration
  - reconciliation
  - vendor failure modes
  - fallback
competencies:
  - debugging
  - evals
  - coding
  - ai-fundamentals
prereqs:
  - M18
condensed: true
durationCondensed: 108
---
## Where you are

Mission 18 left you with a note you were supposed to hold onto. Same statement, three copies, three extractions. Two said 252,400. One said 314,580. The wrong one had the highest confidence.

## The request

:::evidence{type=slack label="#northstar-ai, Wednesday 9:12 AM"}
```text
Marcus:  can we just raise the confidence threshold and drop the bad ones?

You:     raise it to what

Marcus:  like 0.95? the bad one was 0.96 wait

Sam:     ...

Sam:     Ah. So you found that.
```
:::

Marcus is not wrong to want a threshold. He is wrong about what the number means.

## Your task

:::task{time="120 min"}
1. Reproduce the overconfident OptiScan response on the faxed May statement. Confirm
   the Fastcapital line reads 137,180 at confidence 0.96.
2. Run the poor OCR slice through the lab eval suite. Report exact match rate by
   confidence bucket. Show that the relationship is flat.
3. Implement a reconciliation check in `document-service` that compares extracted line
   totals to statement header totals when the header is present, and flags the
   extraction when they disagree by more than one cent.
4. Route flagged extractions to a human review status. Do not send them to
   underwriting as completed.
5. Write down the prompt tuning idea you almost tried, then write why it cannot fix
   this.
:::

## Stop and think

:::stopandthink
1. If confidence does not predict accuracy, what signal would you trust instead?
2. Is this an AI problem or a vendor integration problem?
3. What happens to Hank's queue if every poor OCR page goes to human review?

Write your answers before you scroll. Two minutes.
:::

## One line to remember

:::judgment
**A confidence score from a vendor is a claim about the vendor's internal process, not
a claim about your business fact.**

The instinct to threshold on confidence is reasonable. It works for models that are
calibrated. OptiScan is not calibrated for "is this the amount on the page." It is
calibrated for "did our glyph model like these pixels." Those are different questions,
and treating them as the same question is how 137,180 enters underwriting with a smile.

When a number decides whether a business gets funded, trust checks that can fail hard.
Reconciliation against a printed total is one. Counting dropped lines is another.
Prompting a second model to "be careful" is not a check. It is hope with a temperature
parameter.

Next time a vendor shows you a green dashboard and a high confidence column, ask what
the score is a score of. If the answer is not the business fact you care about, build
your own check.
:::

## Practice

Same skill, different industry. Open the spoiler only after you write your answer.

:::spoiler{label="Certification practice, then the notes"}
**The setup**

A hospital network uses a third party service to read handwritten medication orders
from scanned charts. The vendor returns a drug name, a dose, and a confidence score.
Pharmacy dispenses when confidence is above 0.90.

What you learn in a week:

- On a labeled set of 1,000 orders, exact dose match is 81 percent overall.
- Above 0.95 confidence, exact dose match is 79 percent.
- Below 0.80 confidence, exact dose match is 84 percent.
- The vendor's confidence measures character clarity, not whether the dose is a
  plausible dose for that drug.
- Pharmacists already catch many errors by checking the dose against a formulary
  range. That check is not in the software path.
- A wrong dose that ships is a patient safety event. A delayed order that waits for a
  pharmacist is a throughput event.

**Your task**

1. Should pharmacy keep the 0.90 confidence gate? Why or why not?
2. Name two reconciliation style checks that would catch errors confidence misses.
3. What is the wrong turn that looks productive for a week?
4. How do you explain the change to a chief nursing officer who asked for "higher
   AI confidence"?

---

**Notes, after you have written yours**

Drop the confidence gate as a hard stop. Keep the score in the audit log. The data says
it does not sort safe from unsafe.

Two checks that work: dose within formulary min and max for that drug and route, and
a second pass that rejects orders where the drug name and dose were both changed from
a prior active order without a matching discontinue. The first is a range check. The
second is a continuity check. Neither needs the vendor's score.

The wrong turn is prompt tuning a second model to "verify the dose." If the OCR text
says 10 mg and the chart said 1.0 mg, the verifier reads 10. You are stacking readers
on broken pixels.

To the CNO: confidence went up and safety did not. We are putting the formulary range
check in the path that dispenses, and routing out-of-range orders to a pharmacist
before anything ships. Throughput takes a hit on the messy charts. Patient safety does
not take a hit on the clean looking wrong ones.
:::

---

*Compressed track: same lab commands, same save paths, same certification bar as the full mission. Switch to **Full engagement** in the header for dialogue and debriefs.*
