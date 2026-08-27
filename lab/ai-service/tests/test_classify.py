"""Classification arithmetic boundary and HTTP smoke tests."""

from __future__ import annotations

from decimal import Decimal

from ai_service.routes.classify import compute_totals, transactions_key_material
from ai_service.schemas import (
    TransactionCategory,
    TransactionClassification,
    TransactionInput,
)
from tests.conftest import CANONICAL_TXNS


def test_compute_totals_canonical_boundary():
    txns = [TransactionInput.model_validate(t) for t in CANONICAL_TXNS]
    classifications = [
        TransactionClassification(
            index=0, classification=TransactionCategory.OPERATING_REVENUE
        ),
        TransactionClassification(
            index=1, classification=TransactionCategory.INTERNAL_TRANSFER
        ),
        TransactionClassification(
            index=2, classification=TransactionCategory.OPERATING_REVENUE
        ),
        TransactionClassification(
            index=3, classification=TransactionCategory.LOAN_PROCEEDS
        ),
        TransactionClassification(
            index=4, classification=TransactionCategory.OPERATING_REVENUE
        ),
    ]
    totals = compute_totals(txns, classifications, months=3)
    assert totals.naive_total_credits == Decimal("252400.00")
    assert totals.operating_revenue == Decimal("147400.00")
    assert totals.excluded_total == Decimal("105000.00")
    assert totals.computed_by == "python"
    assert len(totals.excluded) == 2


def test_classify_http_canonical(client):
    response = client.post(
        "/v1/classify/transactions",
        headers={"X-Tenant-Id": "NSC_DIRECT", "X-Trace-Id": "test-classify-1"},
        json={"transactions": CANONICAL_TXNS},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["totals"]["naiveTotalCredits"] == "252400.00"
    assert body["totals"]["operatingRevenue"] == "147400.00"
    assert body["totals"]["computedBy"] == "python"
    labels = [c["classification"] for c in body["classifications"]]
    assert labels[0] == "OPERATING_REVENUE"
    assert labels[1] == "INTERNAL_TRANSFER"
    assert labels[3] == "LOAN_PROCEEDS"


def test_revenue_as_string_returns_schema_error(client):
    response = client.post(
        "/v1/classify/transactions",
        headers={
            "X-Tenant-Id": "NSC_DIRECT",
            "X-Trace-Id": "test-rev-string",
            "X-Stub-Scenario": "revenue-as-string",
        },
        json={"transactions": CANONICAL_TXNS, "months": 3},
    )
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["kind"] == "SCHEMA_ERROR"
    assert "$78,231 approximately" in (detail.get("rawTextPreview") or "")


def test_key_material_normalizes_amounts():
    a = transactions_key_material(
        [TransactionInput(date="05/04", description="STRIPE PAYOUT", amount=48230)]
    )
    b = transactions_key_material(
        [TransactionInput(date="05/04", description="STRIPE PAYOUT", amount="48230.00")]
    )
    assert a == b
