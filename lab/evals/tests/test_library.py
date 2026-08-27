"""Basic library smoke tests that do not need the full golden set."""

from __future__ import annotations

from northstar_evals import Case, Dataset, Runner, Slice, metrics
from northstar_evals.matchers import exact
from northstar_evals.providers import baseline_classify


def test_baseline_classify_keywords():
    assert baseline_classify("STRIPE PAYOUT", 1000) == "OPERATING_REVENUE"
    assert baseline_classify("TRANSFER FROM SAVINGS", 30000) == "INTERNAL_TRANSFER"
    assert baseline_classify("FASTCAPITAL LOAN", 75000) == "LOAN_PROCEEDS"
    assert baseline_classify("FASTCAPITAL FUNDING", 75000) == "OPERATING_REVENUE"
    assert baseline_classify("### ||| [ILLEGIBLE]", 1000) == "UNKNOWN"


def test_runner_on_tiny_set():
    cases = [
        Case.from_dict(
            {
                "caseId": "T1",
                "input": {"description": "STRIPE PAYOUT", "amount": 100},
                "expected": {"classification": "OPERATING_REVENUE"},
                "tags": {"kind": "settlement"},
            }
        ),
        Case.from_dict(
            {
                "caseId": "T2",
                "input": {"description": "FASTCAPITAL FUNDING", "amount": 100},
                "expected": {"classification": "LOAN_PROCEEDS"},
                "tags": {"kind": "loan"},
            }
        ),
    ]
    ds = Dataset.from_cases(cases, name="tiny")

    def task(case):
        return {
            "classification": baseline_classify(
                case.input["description"], case.input["amount"]
            )
        }

    result = Runner(
        task=task,
        dataset=ds,
        slices=[Slice("loan", lambda c: c.tags.get("kind") == "loan")],
        matcher={"classification": exact()},
        label_field="classification",
    ).run()
    assert result.accuracy == 0.5
    assert result.slice_accuracy("loan") == 0.0
    assert metrics.accuracy(1, 2) == 0.5
