# northstar_evals

A small eval library for the Northstar lab. Load a golden set, run a task,
print the slice table, gate a regression.

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
result.assert_no_regression(baseline="baselines/txn-v3-stub.json")
```

## Layout

```
evals/
  northstar_evals/     the importable library
  baselines/           committed numbers for assert_no_regression
  scripts/             helpers (simulate_classifier.py)
  tests/               pytest
../data/golden/        labeled JSONL datasets
```

## Suites

| Suite | Dataset | What it measures |
|---|---|---|
| `txn-classification` | `txn-classification-v3.jsonl` (~400) | Bank line → category |
| `revenue-extraction` | `revenue-extraction-v2.jsonl` (~120) | Statement text → monthly revenue |
| `policy-qa` | `policy-qa-v1.jsonl` (~80) | Policy question → citation |
| `smoke` | `smoke.jsonl` (~20) | Tiny txn set for CI |

```bash
cd lab
PYTHONPATH=evals python -m northstar_evals run --suite txn-classification
PYTHONPATH=evals python -m northstar_evals run --suite smoke --gate
PYTHONPATH=evals python evals/scripts/simulate_classifier.py
```

The stub provider is the default. It needs no network and no API key. It is
the 2019 keyword classifier, not a straw man.

## Why the overall number is a trap

The txn set is built so overall accuracy reads about 96 percent while the
slices that move an approval sit much lower:

```
Overall accuracy ............................... 96.0%
  loan proceeds ................................ 68%
  poor OCR quality ............................. 61%
  internal transfers ........................... 73%
  standard card settlements .................... 99%
```

Card settlements are about 84 percent of the volume. That is why 96 percent
looks fine and is not.

About 2 percent of the labels are wrong on purpose. They are junior labels with
`confidence: "low"`. In at least one case Renee disagrees in `annotations`, and
she is right.

## Regenerating goldens

```bash
python lab/data/golden/tools/generate_golden.py
```

Only re-run that when you mean to change the teaching numbers. Then refresh
baselines:

```bash
cd lab
PYTHONPATH=evals python -m northstar_evals run --suite txn-classification \
  --save-baseline evals/baselines/txn-v3-stub.json
```

## Tests

```bash
cd lab/evals && pip install -e ".[dev]" && pytest
```
