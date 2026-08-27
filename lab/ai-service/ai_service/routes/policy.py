"""POST /v1/policy/answer

Question in, answer with citations out. Retrieval runs before the model call.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException

from ai_service.config import get_settings
from ai_service.observability import current_context, span
from ai_service.parsing import ParseFailure, build_json_instruction, schema_for
from ai_service.prompts import render
from ai_service.providers import CompletionRequest, complete_structured
from ai_service.retrieval import get_policy_index
from ai_service.schemas import (
    PolicyAnswerModelOutput,
    PolicyAnswerRequest,
    PolicyAnswerResponse,
    build_meta,
)

router = APIRouter(tags=["policy"])

PROMPT_VERSION = "policy_answer_v2"


@router.post("/v1/policy/answer", response_model=PolicyAnswerResponse)
def answer_policy(payload: PolicyAnswerRequest) -> PolicyAnswerResponse:
    settings = get_settings()
    ctx = current_context()
    tenant_id = payload.tenant_id or ctx.tenant_id
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="tenantId is required on the body or as X-Tenant-Id.",
        )
    ctx.tenant_id = tenant_id

    effective = payload.effective_date or date.today()
    index = get_policy_index()

    with span("policy.retrieve") as sp:
        citations = index.search(
            payload.question,
            tenant_id=tenant_id,
            product=payload.product,
            effective_on=effective,
            top_k=payload.top_k or settings.retrieval_top_k,
        )
        sp.retrieved_doc_ids = sorted({c.doc_id for c in citations})
        sp.validation_result = "ok"
        sp.model = "none"
        sp.prompt_version = "n/a"
        sp.cost_basis = "0.0 because retrieval is local math, not a model call."

    context = index.format_context(citations)
    schema = schema_for(PolicyAnswerModelOutput)
    prompt = render(
        PROMPT_VERSION,
        question=payload.question,
        tenant_id=tenant_id,
        product=payload.product or "n/a",
        effective_date=effective.isoformat(),
        context=context,
        json_instruction=build_json_instruction(schema),
    )

    req = CompletionRequest(
        prompt=prompt,
        prompt_version=PROMPT_VERSION,
        json_mode=True,
        scenario=ctx.stub_scenario,
        trace_id=ctx.trace_id,
        tenant_id=tenant_id,
        fixture_input=payload.question,
    )

    try:
        response, result = complete_structured(
            req, PolicyAnswerModelOutput, span_name="policy.answer"
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

    model_out: PolicyAnswerModelOutput = result.value
    cited = {c.chunk_id for c in citations}
    kept = [c for c in citations if c.chunk_id in set(model_out.cited_chunk_ids) | cited]
    # Prefer the model's cited ids when they match retrieval. Fall back to all
    # retrieved citations so the caller always sees where the context came from.
    if model_out.cited_chunk_ids:
        by_id = {c.chunk_id: c for c in citations}
        kept = [by_id[i] for i in model_out.cited_chunk_ids if i in by_id] or citations

    warnings: list[str] = []
    if result.repairs_applied:
        warnings.append(
            "The output needed repair before it parsed: "
            + ", ".join(result.repairs_applied)
        )
    if not citations:
        warnings.append("No policy excerpts matched. The answer may be incomplete.")

    return PolicyAnswerResponse(
        question=payload.question,
        answer=model_out.answer,
        citations=kept,
        warnings=warnings,
        meta=build_meta(
            response,
            trace_id=ctx.trace_id,
            repairs_applied=result.repairs_applied,
        ),
    )
