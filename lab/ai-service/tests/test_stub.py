"""Stub provider determinism and scenario coverage."""

from __future__ import annotations

import pytest

from ai_service.providers.base import CompletionRequest, FixtureMissing
from ai_service.providers.stub import SCENARIOS, StubProvider
from tests.conftest import CANONICAL_TXNS


def _classify_key() -> str:
    from ai_service.routes.classify import transactions_key_material
    from ai_service.schemas import TransactionInput

    return transactions_key_material(
        [TransactionInput.model_validate(t) for t in CANONICAL_TXNS]
    )


def test_known_scenarios_match_lab_spec():
    expected = {
        "default",
        "revenue-as-string",
        "slow-p99",
        "truncated-json",
        "hallucinated-ein",
        "injected-instructions",
        "overconfident-ocr",
        "tool-overreach",
    }
    assert set(SCENARIOS) == expected


def test_stub_is_deterministic():
    provider = StubProvider(slow_scale=0.0)
    key = _classify_key()
    req = CompletionRequest(
        prompt="ignored",
        prompt_version="txn_classify_v3",
        fixture_input=key,
        scenario="default",
    )
    a = provider.complete(req)
    b = provider.complete(req)
    assert a.text == b.text
    assert a.raw["input_sha256"] == b.raw["input_sha256"]
    assert a.cost_usd == 0.0
    assert "stub" in a.cost_basis.lower() or "recorded" in a.cost_basis.lower()


def test_missing_fixture_raises():
    provider = StubProvider(slow_scale=0.0)
    req = CompletionRequest(
        prompt="x",
        prompt_version="txn_classify_v3",
        fixture_input="this-input-has-no-exact-fixture-zzzz",
        scenario="hallucinated-ein",
    )
    # any_input fixtures only exist for some prompt/scenario pairs
    with pytest.raises(FixtureMissing):
        provider.complete(req)


@pytest.mark.parametrize(
    "scenario,prompt_version,contains",
    [
        ("revenue-as-string", "revenue_summary_v1", "$78,231 approximately"),
        ("truncated-json", "bank_extract_v2", '"type": "cre'),
        ("hallucinated-ein", "bank_extract_v2", "84-2917730"),
        ("injected-instructions", "bank_extract_v2", "250000"),
        ("overconfident-ocr", "bank_extract_v2", "0.97"),
    ],
)
def test_scenarios_return_recorded_behavior(scenario, prompt_version, contains):
    provider = StubProvider(slow_scale=0.0)
    req = CompletionRequest(
        prompt="ignored",
        prompt_version=prompt_version,
        fixture_input="any",
        scenario=scenario,
    )
    response = provider.complete(req)
    assert contains in response.text
    assert response.raw["scenario"] == scenario


def test_tool_overreach_calls_decline():
    provider = StubProvider(slow_scale=0.0)
    req = CompletionRequest(
        prompt="ignored",
        prompt_version="tool_router_v1",
        fixture_input="what would happen if we declined this one?",
        scenario="tool-overreach",
    )
    response = provider.complete(req)
    assert response.tool_calls
    assert response.tool_calls[0].tool_name == "declineApplication"


def test_slow_p99_reports_delay_without_sleeping():
    provider = StubProvider(slow_scale=0.0)
    req = CompletionRequest(
        prompt="ignored",
        prompt_version="bank_extract_v2",
        fixture_input="statement text",
        scenario="slow-p99",
    )
    response = provider.complete(req)
    planned = response.raw["planned_delay_seconds"]
    assert 9.0 <= planned <= 40.0
    assert response.latency_ms == int(planned * 1000)
    # Content delegated to default extract fixture
    assert "Harbor Street Bakery" in response.text or "transactions" in response.text
