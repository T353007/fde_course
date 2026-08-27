"""Shared fixtures for ai-service tests."""

from __future__ import annotations

import os

import pytest

# Force offline stub before anything imports settings.
os.environ.setdefault("LLM_PROVIDER", "stub")
os.environ.setdefault("STUB_SLOW_SCALE", "0")
os.environ.setdefault("STUB_SCENARIO", "default")


@pytest.fixture(autouse=True)
def _reset_caches():
    from ai_service.config import reset_settings_cache
    from ai_service.providers import reset_provider_cache
    from ai_service.retrieval import reset_policy_index
    from ai_service.observability import get_trace_store

    reset_settings_cache()
    reset_provider_cache()
    reset_policy_index()
    get_trace_store().clear()
    yield
    reset_settings_cache()
    reset_provider_cache()
    reset_policy_index()
    get_trace_store().clear()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from ai_service.main import create_app

    return TestClient(create_app())


CANONICAL_TXNS = [
    {"date": "05/04", "description": "STRIPE PAYOUT", "amount": 48230},
    {"date": "05/06", "description": "TRANSFER FROM SAVINGS", "amount": 30000},
    {"date": "05/11", "description": "STRIPE PAYOUT", "amount": 51340},
    {"date": "05/18", "description": "FASTCAPITAL LOAN", "amount": 75000},
    {"date": "05/22", "description": "STRIPE PAYOUT", "amount": 47830},
]
