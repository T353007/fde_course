"""Canon slice numbers for txn-classification-v3 under the stub provider."""

from __future__ import annotations

from pathlib import Path

import pytest

from northstar_evals import Runner, get_provider
from northstar_evals.suites import get as get_suite

LAB = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def txn_result():
    suite = get_suite("txn-classification")
    dataset = suite.load(LAB)
    provider = get_provider("stub")
    return Runner(
        task=provider.task_for(suite.name),
        dataset=dataset,
        slices=list(suite.slices),
        matcher=dict(suite.matchers),
        label_field=suite.label_field,
        name=suite.name,
        provider=provider.name,
        model=getattr(provider, "model", None),
    ).run()


def test_dataset_size():
    suite = get_suite("txn-classification")
    ds = suite.load(LAB)
    assert len(ds) == 400


def test_canon_overall(txn_result):
    assert abs(txn_result.accuracy - 0.96) <= 0.01


def test_canon_loan_proceeds(txn_result):
    assert abs(txn_result.slice_accuracy("loan_proceeds") - 0.68) <= 0.02


def test_canon_poor_ocr(txn_result):
    assert abs(txn_result.slice_accuracy("poor_ocr") - 0.61) <= 0.02


def test_canon_internal_transfer(txn_result):
    assert abs(txn_result.slice_accuracy("internal_transfer") - 0.73) <= 0.02


def test_canon_card_settlement(txn_result):
    s = txn_result.slice("card_settlement")
    assert abs(s.accuracy - 0.99) <= 0.015
    assert abs(s.share - 0.84) <= 0.02


def test_wrong_labels_about_two_percent():
    suite = get_suite("txn-classification")
    ds = suite.load(LAB)
    juniors = {"t.okafor", "j.pham", "junior.underwriter"}
    wrongish = [
        c
        for c in ds
        if c.confidence == "low" and (c.labeled_by or "").lower() in juniors
    ]
    assert 6 <= len(wrongish) <= 10
    # Renee disagrees on at least one of them.
    assert any(
        any(a.annotator == "renee.blackwell" for a in c.annotations)
        for c in wrongish
    )


def test_canon_five_transactions_present():
    suite = get_suite("txn-classification")
    ds = suite.load(LAB)
    ids = {c.case_id for c in ds}
    for i in range(1, 6):
        assert f"TX-CANON-{i:02d}" in ids


def test_baseline_no_regression(txn_result):
    baseline = LAB / "evals" / "baselines" / "txn-v3-stub.json"
    if not baseline.exists():
        pytest.skip("baseline not written yet")
    txn_result.assert_no_regression(baseline)


def test_smoke_suite_runs():
    suite = get_suite("smoke")
    ds = suite.load(LAB)
    assert len(ds) == 20
    provider = get_provider("stub")
    result = Runner(
        task=provider.task_for(suite.name),
        dataset=ds,
        slices=list(suite.slices),
        matcher=dict(suite.matchers),
        label_field=suite.label_field,
        name=suite.name,
        provider="stub",
    ).run()
    assert result.accuracy >= 0.80


def test_other_goldens_load():
    for name, n in (
        ("revenue-extraction", 120),
        ("policy-qa", 80),
    ):
        suite = get_suite(name)
        ds = suite.load(LAB)
        assert len(ds) == n
        report = suite.validate(LAB)
        assert report.ok, report.report()
