---
id: M15
slug: prove-it-works
title: Prove It Works
subtitle: "Sixty labeled cases from Renee, an afternoon of work, and it immediately changes how you work."
phase: 3
order: 15
duration: 270
difficulty: 3
lab: true
status: complete
objectives:
  - Build a golden dataset with provenance fields that survive an argument
  - Run the northstar_evals Runner and read an overall accuracy number you can defend
  - Separate a demo that worked from a measurement that holds
  - Save a baseline so the next prompt change has something to regress against
concepts: [golden datasets, eval runners, baselines, labeling, accuracy, provenance]
competencies: [evals, ai-fundamentals, coding]
prereqs: [M14]
---

## Where you are

Classification returns JSON. Extraction clears invented EINs. Marcus keeps saying the
model "works" because the six statements in his deck come back clean.

Janet asked a different question in standup: "Works compared to what?"

You do not have an answer yet. Today you build one.

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

## The conversation

:::dialogue{title="Renee's desk, Thursday 10:00 AM"}
**You:** I need a small set of transactions with the right classification written down.

**Renee:** How many.

**You:** Sixty to start. Mix of easy card payouts and the ugly ones.

**Renee:** Ugly meaning transfers and loan deposits.

**You:** Yes.

**Renee:** I can do sixty. I will not do six hundred today. And I am not labeling from
the OCR garbage alone. I want the PDF open.

**You:** Fine. I will pull both.

*She opens a spreadsheet. The filename is not `revenue_check_v7_FINAL.xlsx`. She still
glances at it once, out of habit.*

**Renee:** One more thing. If a junior helps later, put their name on the row. People
disagree. I want to know who said what.
:::

:::dialogue{title="Nadia, Slack DM, Thursday 10:35 AM"}
**Nadia:** first eval day?

**You:** sixty cases with Renee

**Nadia:** good. write down the prompt version and the model alias on the run, or the
number is a souvenir.

**You:** and then I can tell Janet it works?

**Nadia:** you can tell Janet a number. "works" is her word, not yours.
:::

## What you know about the system

The eval library lives under `lab/evals/`. It is importable. It is not a pile of one-off
scripts.

```python
from northstar_evals import Dataset, Runner, Slice, metrics

ds = Dataset.load("data/golden/txn-classification-v3.jsonl")

result = Runner(
    task=classify_transactions,
    dataset=ds,
    slices=[
        Slice("loan_proceeds",     lambda c: c.tags.get("kind") == "loan"),
        Slice("internal_transfer", lambda c: c.tags.get("kind") == "transfer"),
        Slice("poor_ocr",          lambda c: c.tags.get("ocr_quality") == "poor"),
        Slice("card_settlement",   lambda c: c.tags.get("kind") == "settlement"),
    ],
).run()

result.report()
result.assert_no_regression(baseline="baselines/txn-v3-qwen8b.json")
```

Case format, one JSON object per line:

```json
{
  "caseId": "TX-10021",
  "input": {"description": "TRANSFER FROM SAVINGS ****1221", "amount": 30000},
  "expected": {"classification": "INTERNAL_TRANSFER"},
  "tags": {"kind": "transfer", "ocr_quality": "good", "tenant": "NSC_DIRECT"},
  "labeledBy": "renee.blackwell",
  "labeledAt": "2026-04-11",
  "confidence": "high"
}
```

`labeledBy` and `confidence` are not decoration. Mission 16 will need them. Put them on
every row now.

CLI entry points you will use today:

```bash
cd lab
make eval SUITE=txn-classification
# same thing:
python -m northstar_evals run --suite txn-classification --provider stub
python -m northstar_evals validate --suite txn-classification
```

Default provider is `stub`. No key, no network, same fixtures as `ai-service`.

## Evidence

Renee's first twenty rows look like this when you dump them.

:::evidence{type=spreadsheet label="Renee labeling sheet, first rows"}
```text
caseId     description                         amount    label                 conf
TX-10001   STRIPE PAYOUT                       48230     OPERATING_REVENUE     high
TX-10002   STRIPE PAYOUT                       51340     OPERATING_REVENUE     high
TX-10003   TRANSFER FROM SAVINGS ****1221      30000     INTERNAL_TRANSFER     high
TX-10004   FASTCAPITAL LOAN                    75000     LOAN_PROCEEDS         high
TX-10005   SQ *COFFEE SHOP POS                 2210      OPERATING_REVENUE     high
TX-10006   MOBILE DEP                          4000      OWNER_CONTRIBUTION    med
...
```
:::

She hesitates on `MOBILE DEP`. Medium confidence. You keep the tag. Do not "clean" it
to high so the sheet looks nicer.

:::evidence{type=slack label="DM from Tomás, Thursday 11:20 AM"}
```text
Tomás:  do we need sixty? I have unit tests for the parser

You:    unit tests check shape. this checks whether the answer is right

Tomás:  ah
Tomás:  ok yeah different thing
```
:::

## What you do not know

- Whether sixty cases cover the real monthly mix.
- Whether Renee's labels match what Hank's team would write under time pressure.
- Whether overall accuracy will still look good once you slice it. (Park that. Mission
  16 owns it on purpose.)
- Whether Marcus will quote the number without the sample size.

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

## Working through it

### Build the file, not a notebook

Keep the golden set in JSONL in git. Spreadsheets are for labeling. The runner reads
lines.

```python
# lab/evals/scripts/m15_write_cases.py
import json
from pathlib import Path

rows = [
    {
        "caseId": "TX-10001",
        "input": {"description": "STRIPE PAYOUT", "amount": 48230},
        "expected": {"classification": "OPERATING_REVENUE"},
        "tags": {
            "kind": "settlement",
            "ocr_quality": "good",
            "tenant": "NSC_DIRECT",
            "month": "2026-04",
        },
        "labeledBy": "renee.blackwell",
        "labeledAt": "2026-04-11",
        "confidence": "high",
    },
    # ... 59 more
]

out = Path("data/golden/txn-classification-v3.jsonl")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w") as f:
    for row in rows:
        f.write(json.dumps(row) + "\n")
print(f"wrote {len(rows)} cases to {out}")
```

Validate before you trust a score.

```bash
python -m northstar_evals validate --suite txn-classification
```

:::evidence{type=log label="validate output"}
```text
suite=txn-classification
cases=60
required_tags ok
allowed_labels ok
labeledBy present on 60/60
confidence present on 60/60
VALIDATION OK
```
:::

### Run it

```python
# lab/evals/scripts/m15_run.py
from northstar_evals import Dataset, Runner, Slice
from northstar_evals.providers import get_provider
from northstar_evals.suites import get as get_suite

suite = get_suite("txn-classification")
ds = Dataset.load(suite.resolve_dataset_path())
provider = get_provider("stub")

result = Runner(
    task=provider.task_for(suite.name),
    dataset=ds,
    slices=suite.slices,
    matchers=suite.matchers,
    label_field=suite.label_field,
).run()

result.report()
result.save("out/m15-txn-v3-stub.json")
```

Or the one liner:

```bash
python -m northstar_evals run --suite txn-classification --provider stub --detail
```

### The first number

:::evidence{type=metrics label="first full run, stub, txn-classification-v3"}
```text
suite          txn-classification
provider       stub
prompt         txn-classify-v2
cases          60

OVERALL        96.0%   (58/60)

# you glance at slices for curiosity and close the terminal
# Mission 16 is where those rows become the story
```
:::

Ninety six percent. On purpose, this mission ends here with you feeling good.

:::dialogue{title="Janet, standup, Friday 9:15 AM"}
**You:** First eval is in. Sixty labeled cases from Renee. Overall accuracy 96 percent
on the stub run. Baseline saved.

**Janet:** Who is on call if that number moves?

**You:** Me. It is gated in the notes and the baseline file is in the repo.

**Marcus:** Ship it. That is better than anything we had.

**Janet:** It is a start. Do not put 96 percent on a customer slide until we know what
it is made of.

**You:** Understood.
:::

You understood less than you think. That is fine for twenty four hours.

### What "96 percent" is allowed to mean today

Write this in the note next to the score so Friday-you cannot launder it:

```text
n = 60
labeled_by = renee.blackwell (primary)
prompt_version = txn-classify-v2
provider = stub
overall = 96.0%
slices = not yet briefed to leadership
```

That block is the difference between a measurement and a rumor. Mission 16 will force
the slice rows into the same note. Do not delete this header when that happens.

### How an FDE uses the baseline the next morning

Tomorrow you will change one line of the prompt because a single transfer case annoyed
you. Before you argue about feelings, run:

```bash
python -m northstar_evals run --suite txn-classification --provider stub \
  --baseline baselines/txn-v3-stub.json --gate
```

If overall stays flat and loan proceeds drop, you learned something. If you have no
baseline file, you only have a story.

## The wrong turn

A reasonable engineer, facing sixty cases and a calendar invite with Dale, does this:

```python
# the "eval" you must not ship
DEMO = ["TX-10001", "TX-10002", "TX-10005", "TX-10008", "TX-10011", "TX-10014"]

def score_demo(results):
    hits = sum(1 for r in results if r.case_id in DEMO and r.matched)
    return hits / len(DEMO)
```

That returns 100 percent forever. It measures whether your demo still demos. It does not
measure the product.

Delete it if you wrote it. The golden set is the point. Cherry picked IDs are a press
release.

## Tests

```python
# lab/evals/tests/test_m15_dataset.py
from northstar_evals import Dataset
from northstar_evals.suites import get as get_suite


def test_txn_v3_has_provenance():
    suite = get_suite("txn-classification")
    ds = Dataset.load(suite.resolve_dataset_path())
    assert len(ds) >= 60
    for case in ds:
        assert case.labeled_by, case.case_id
        assert case.confidence in {"high", "med", "low", "medium"}, case.case_id
        assert "kind" in case.tags
        assert "ocr_quality" in case.tags
```

```bash
cd lab/evals && pytest tests/test_m15_dataset.py -q
```

## Then this happens

Jordan forwards a draft customer update.

:::evidence{type=email label="Draft from Jordan, not yet sent"}
```text
Subject: Northstar AI update

Dale,

Quick win to share. Our transaction classifier is at 96% accuracy after the
first labeled set. Directionally we are ready to expand scope.

Jordan
```
:::

:::dialogue{title="You, before he hits send"}
**You:** Take the number out or put the sample size next to it. Sixty cases. Renee
labeled them. We have not sliced it.

**Jordan:** Dale likes clean numbers.

**You:** Clean numbers without a denominator become promises.

**Jordan:** ...I may have set expectations before. Fine. I will say "early eval, n=60."
:::

## The better version

An eval you can defend has four parts:

1. **Cases with provenance.** Who labeled, when, how sure.
2. **A runner that records model and prompt version.** Or the score is unmoored.
3. **A baseline file.** So "better" means something.
4. **A person who will not let a demo set pretend to be the suite.**

You have those four now. You do not yet have the slice report that ruins the 96
percent. That is tomorrow's job, and it is the reason this mission is allowed to end
happy.

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

:::commslab
#### To Janet

> Eval v1 is in: 60 cases, Renee labeled, overall 96 percent on stub, baseline at
> `baselines/txn-v3-stub.json`. I will follow with a slice breakdown before anyone uses
> the number externally.

#### To Renee

> Thank you for the sixty. I kept your medium confidence rows as medium. If a junior
> labels more later, their name stays on the row so we can compare.

#### To Marcus

> You can say we measured 96 percent on a 60 case set labeled by underwriting. Please
> do not say "the model is 96 percent accurate" on a customer call until we show slices.
:::

## Practice

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
