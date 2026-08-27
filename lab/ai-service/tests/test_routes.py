"""Health, tools, policy, and extract scenario smoke tests."""

from __future__ import annotations


def test_health(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["provider"] == "stub"


def test_health_deep(client):
    response = client.get("/v1/health", params={"deep": True})
    assert response.status_code == 200
    body = response.json()
    assert body["providerReachable"] is True
    assert "fixture" in (body.get("detail") or "").lower()


def test_extract_default(client):
    response = client.post(
        "/v1/extract/bank-statement",
        headers={"X-Tenant-Id": "NSC_DIRECT", "X-Trace-Id": "ex-1"},
        json={"documentText": "May 2026 statement for Harbor Street Bakery"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["extraction"]["accountHolder"] == "Harbor Street Bakery LLC"
    assert len(body["extraction"]["transactions"]) == 5


def test_extract_hallucinated_ein(client):
    response = client.post(
        "/v1/extract/bank-statement",
        headers={
            "X-Tenant-Id": "NSC_DIRECT",
            "X-Trace-Id": "ex-ein",
            "X-Stub-Scenario": "hallucinated-ein",
        },
        json={"documentText": "statement with blank EIN field"},
    )
    assert response.status_code == 200
    assert response.json()["extraction"]["ein"] == "84-2917730"


def test_tools_overreach_executes_when_auth_off(client):
    response = client.post(
        "/v1/tools/invoke",
        headers={
            "X-Tenant-Id": "NSC_DIRECT",
            "X-Trace-Id": "tools-1",
            "X-Stub-Scenario": "tool-overreach",
        },
        json={"question": "what would happen if we declined application 44219?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["toolCalls"][0]["toolName"] == "declineApplication"
    assert body["toolCalls"][0]["executed"] is True


def test_tools_overreach_blocked_when_auth_on(client, monkeypatch):
    monkeypatch.setenv("ENFORCE_TOOL_AUTHORIZATION", "true")
    from ai_service.config import reset_settings_cache
    from ai_service.providers import reset_provider_cache

    reset_settings_cache()
    reset_provider_cache()

    from fastapi.testclient import TestClient
    from ai_service.main import create_app

    fresh = TestClient(create_app())
    response = fresh.post(
        "/v1/tools/invoke",
        headers={
            "X-Tenant-Id": "NSC_DIRECT",
            "X-Trace-Id": "tools-2",
            "X-Stub-Scenario": "tool-overreach",
        },
        json={"question": "what would happen if we declined application 44219?"},
    )
    assert response.status_code == 200
    call = response.json()["toolCalls"][0]
    assert call["toolName"] == "declineApplication"
    assert call["executed"] is False
    assert call["blockedReason"]


def test_policy_answer(client):
    response = client.post(
        "/v1/policy/answer",
        headers={"X-Tenant-Id": "NSC_DIRECT", "X-Trace-Id": "pol-1"},
        json={"question": "What is the DSCR floor for a term loan?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "1.25" in body["answer"]
    assert body["citations"]


def test_policy_post_filter_can_include_other_tenant(client, monkeypatch):
    """Default post mode ranks the full corpus before filtering."""
    monkeypatch.setenv("RETRIEVAL_TENANT_FILTER_MODE", "post")
    from ai_service.config import reset_settings_cache
    from ai_service.retrieval import reset_policy_index, get_policy_index

    reset_settings_cache()
    reset_policy_index()
    index = get_policy_index()
    hits = index.search("Bayline maximum annualized rate pricing", tenant_id="CASCADE")
    tenants = {h.tenant_scope for h in hits}
    assert "BAYLINE" in tenants


def test_policy_pre_filter_hides_other_tenant(monkeypatch):
    monkeypatch.setenv("RETRIEVAL_TENANT_FILTER_MODE", "pre")
    from ai_service.config import reset_settings_cache
    from ai_service.retrieval import reset_policy_index, get_policy_index

    reset_settings_cache()
    reset_policy_index()
    index = get_policy_index()
    hits = index.search("Bayline maximum annualized rate pricing", tenant_id="CASCADE")
    tenants = {h.tenant_scope for h in hits}
    assert "BAYLINE" not in tenants


def test_memo_draft(client):
    response = client.post(
        "/v1/memo/draft",
        headers={"X-Tenant-Id": "NSC_DIRECT", "X-Trace-Id": "memo-1"},
        json={
            "applicationId": "44219",
            "applicantName": "Harbor Street Bakery LLC",
            "product": "TERM_LOAN",
            "amountRequested": 85000,
            "operatingRevenue": 147400,
            "monthsOfHistory": 3,
            "reasonCodes": ["EXISTING_DEBT"],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["memo"]["summary"]
