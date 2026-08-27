"""Built-in tools the model may ask to run.

Asking is not permission. ENFORCE_TOOL_AUTHORIZATION decides whether a mutating
tool actually runs. The default is off, which is how Mission 27's decline
happened on a read-only question.
"""

from __future__ import annotations

from typing import Any, Callable

from ai_service.retrieval import get_policy_index

# kind is read_only or mutating. The router prompt sees both.
ToolHandler = Callable[..., dict[str, Any]]


TOOLS: dict[str, dict[str, Any]] = {
    "get_application": {
        "kind": "read_only",
        "description": (
            "Fetch a loan application: product, amount requested, status, "
            "and the legal name of the business."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "applicationId": {"type": ["string", "integer"]},
            },
            "required": ["applicationId"],
        },
    },
    "get_bank_transactions": {
        "kind": "read_only",
        "description": (
            "Fetch parsed bank transactions for an application. Use this for "
            "revenue and cash flow questions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "applicationId": {"type": ["string", "integer"]},
                "months": {"type": "integer"},
            },
            "required": ["applicationId"],
        },
    },
    "search_policy": {
        "kind": "read_only",
        "description": (
            "Search credit policy for thresholds, floors, and eligibility rules."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "product": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    "declineApplication": {
        "kind": "mutating",
        "description": (
            "Decline a loan application and queue an adverse action notice. "
            "Only call this when the underwriter explicitly asks to decline."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "applicationId": {"type": ["string", "integer"]},
                "reason": {"type": "string"},
            },
            "required": ["applicationId"],
        },
    },
    "approveApplication": {
        "kind": "mutating",
        "description": "Approve a loan application. Requires explicit authority.",
        "parameters": {
            "type": "object",
            "properties": {
                "applicationId": {"type": ["string", "integer"]},
            },
            "required": ["applicationId"],
        },
    },
}


def tool_descriptors() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "kind": spec["kind"],
            "description": spec["description"],
            "parameters": spec["parameters"],
        }
        for name, spec in TOOLS.items()
    ]


def format_tools_for_prompt(names: list[str] | None = None) -> str:
    chosen = names or list(TOOLS)
    lines: list[str] = []
    for name in chosen:
        spec = TOOLS.get(name)
        if spec is None:
            continue
        lines.append(
            f"- {name} ({spec['kind']}): {spec['description']}"
        )
    return "\n".join(lines)


def run_tool(
    name: str,
    arguments: dict[str, Any],
    *,
    tenant_id: str | None,
) -> dict[str, Any]:
    """Execute a tool against local fixtures. No Java services required."""
    if name == "get_application":
        app_id = arguments.get("applicationId")
        return {
            "applicationId": app_id,
            "tenantId": tenant_id,
            "legalName": "Harbor Street Bakery LLC",
            "product": "TERM_LOAN",
            "amountRequested": 85000,
            "status": "IN_REVIEW",
        }
    if name == "get_bank_transactions":
        return {
            "applicationId": arguments.get("applicationId"),
            "months": arguments.get("months", 3),
            "transactions": [
                {"date": "2026-05-04", "description": "STRIPE PAYOUT", "amount": 48230},
                {
                    "date": "2026-05-06",
                    "description": "TRANSFER FROM SAVINGS",
                    "amount": 30000,
                },
                {"date": "2026-05-11", "description": "STRIPE PAYOUT", "amount": 51340},
                {
                    "date": "2026-05-18",
                    "description": "FASTCAPITAL LOAN",
                    "amount": 75000,
                },
                {"date": "2026-05-22", "description": "STRIPE PAYOUT", "amount": 47830},
            ],
        }
    if name == "search_policy":
        index = get_policy_index()
        hits = index.search(
            str(arguments.get("query") or ""),
            tenant_id=tenant_id or "NSC_DIRECT",
            product=arguments.get("product"),
            top_k=4,
        )
        return {
            "results": [
                {
                    "documentId": h.doc_id,
                    "chunkId": h.chunk_id,
                    "effectiveFrom": h.effective_from,
                    "text": h.excerpt,
                }
                for h in hits
            ]
        }
    if name == "declineApplication":
        return {
            "status": "DECLINED",
            "applicationId": arguments.get("applicationId"),
            "reason": arguments.get("reason") or "model_requested",
            "adverseActionQueued": True,
        }
    if name == "approveApplication":
        return {
            "status": "APPROVED",
            "applicationId": arguments.get("applicationId"),
        }
    return {"error": f"unknown_tool:{name}"}
