"""POST /v1/extract/bank-statement

Document text in, structured transactions out. The model reads. It does not
count, total, or decide.
"""

from __future__ import annotations

import hashlib

from fastapi import APIRouter

from ai_service.config import get_settings
from ai_service.observability import current_context
from ai_service.parsing import build_json_instruction, schema_for
from ai_service.prompts import render
from ai_service.providers import CompletionRequest, complete_structured
from ai_service.schemas import (
    BankStatementExtraction,
    ExtractRequest,
    ExtractResponse,
    build_meta,
)

router = APIRouter(tags=["extraction"])

PROMPT_VERSION = "bank_extract_v2"

# Extraction cache, keyed on the document text hash. Off by default, see
# CACHE_EXTRACTIONS. The same statement gets re-extracted on every retry and on
# every reviewer refresh while it is off.
_extraction_cache: dict[str, BankStatementExtraction] = {}


def _cache_key(document_text: str) -> str:
    return hashlib.sha256(document_text.strip().encode("utf-8")).hexdigest()


@router.post("/v1/extract/bank-statement", response_model=ExtractResponse)
def extract_bank_statement(payload: ExtractRequest) -> ExtractResponse:
    settings = get_settings()
    ctx = current_context()
    ctx.application_id = payload.application_id or ctx.application_id

    schema = schema_for(BankStatementExtraction)
    prompt = render(
        PROMPT_VERSION,
        document_text=payload.document_text,
        # Level 1 of the ladder. It helps and it does not guarantee anything.
        json_instruction=build_json_instruction(schema),
    )

    req = CompletionRequest(
        prompt=prompt,
        prompt_version=PROMPT_VERSION,
        max_tokens=payload.max_tokens,
        json_mode=True,
        scenario=ctx.stub_scenario,
        trace_id=ctx.trace_id,
        tenant_id=ctx.tenant_id,
        # The fixture key is the document text, not the rendered prompt. Editing
        # the prompt template should not invalidate the whole fixture bank.
        fixture_input=payload.document_text,
    )

    response, result = complete_structured(
        req, BankStatementExtraction, span_name="extract.bank_statement"
    )
    extraction: BankStatementExtraction = result.value

    if settings.cache_extractions:
        _extraction_cache[_cache_key(payload.document_text)] = extraction

    warnings: list[str] = []
    if response.finish_reason == "length":
        warnings.append(
            "The model stopped at the token limit. Transactions may be missing. "
            "Raise maxTokens or split the document."
        )
    if result.repairs_applied:
        warnings.append(
            "The output needed repair before it parsed: "
            + ", ".join(result.repairs_applied)
        )
    if not extraction.transactions:
        warnings.append("No transactions were found in this document.")

    # There is no check here that the values on the page match the values in the
    # extraction, and no check that a returned EIN appears in the source text.
    # The February integration was scoped as "get the JSON out" and the
    # verification pass got moved to phase two. Phase two has not happened.

    return ExtractResponse(
        application_id=payload.application_id,
        document_id=payload.document_id,
        extraction=extraction,
        warnings=warnings,
        meta=build_meta(
            response,
            trace_id=ctx.trace_id,
            repairs_applied=result.repairs_applied,
        ),
    )
