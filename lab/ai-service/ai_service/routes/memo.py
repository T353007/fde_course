"""POST /v1/memo/draft

Application context in, first-pass credit memo out. The model drafts. A human
owns the decision.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ai_service.config import get_settings
from ai_service.observability import current_context, span
from ai_service.parsing import ParseFailure, build_json_instruction, schema_for
from ai_service.prompts import render
from ai_service.providers import CompletionRequest, complete_structured
from ai_service.retrieval import get_policy_index
from ai_service.schemas import (
    Citation,
    MemoModelOutput,
    MemoRequest,
    MemoResponse,
    build_meta,
)

router = APIRouter(tags=["memo"])

PROMPT_VERSION = "memo_draft_v1"


@router.post("/v1/memo/draft", response_model=MemoResponse)
def draft_memo(payload: MemoRequest) -> MemoResponse:
    settings = get_settings()
    ctx = current_context()
    ctx.application_id = payload.application_id
    index = get_policy_index()
    citations: list[Citation] = []

    with span("memo.policy_context") as sp:
        if settings.memo_policy_context == "retrieved":
            query = (
                f"{payload.product} credit memo "
                f"{' '.join(payload.reason_codes)}".strip()
            )
            citations = index.search(
                query,
                tenant_id=ctx.tenant_id or "NSC_DIRECT",
                product=payload.product,
            )
            policy_context = index.format_context(citations)
            sp.retrieved_doc_ids = sorted({c.doc_id for c in citations})
        else:
            # full_corpus is the February demo path. Marcus liked the answers.
            # Mission 34 measures what it costs.
            policy_context = index.full_corpus_text()
            sp.retrieved_doc_ids = sorted({c.doc_id for c in index.chunks})
            sp.fallback_reason = "memo_policy_context=full_corpus"
        sp.validation_result = "ok"
        sp.model = "none"
        sp.prompt_version = "n/a"
        sp.cost_basis = "0.0 because policy context is assembled in Python."

    schema = schema_for(MemoModelOutput)
    prompt = render(
        PROMPT_VERSION,
        application_id=payload.application_id,
        applicant_name=payload.applicant_name,
        product=payload.product,
        amount_requested=payload.amount_requested or "n/a",
        operating_revenue=payload.operating_revenue or "n/a",
        months_of_history=payload.months_of_history or "n/a",
        reason_codes=", ".join(payload.reason_codes) or "none",
        notes=payload.notes or "none",
        policy_context=policy_context,
        json_instruction=build_json_instruction(schema),
    )

    req = CompletionRequest(
        prompt=prompt,
        prompt_version=PROMPT_VERSION,
        json_mode=True,
        max_tokens=1536,
        scenario=ctx.stub_scenario,
        trace_id=ctx.trace_id,
        tenant_id=ctx.tenant_id,
        fixture_input=f"{payload.application_id}|{payload.product}",
    )

    try:
        response, result = complete_structured(
            req, MemoModelOutput, span_name="memo.draft"
        )
    except ParseFailure as failure:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "model_output_invalid",
                "traceId": ctx.trace_id,
                **failure.to_dict(),
            },
        ) from failure

    warnings: list[str] = []
    if result.repairs_applied:
        warnings.append(
            "The output needed repair before it parsed: "
            + ", ".join(result.repairs_applied)
        )

    return MemoResponse(
        application_id=payload.application_id,
        memo=result.value,
        citations=citations,
        warnings=warnings,
        meta=build_meta(
            response,
            trace_id=ctx.trace_id,
            repairs_applied=result.repairs_applied,
        ),
    )
