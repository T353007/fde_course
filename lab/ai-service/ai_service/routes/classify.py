"""POST /v1/classify/transactions

This is the endpoint the whole course points at, so read the boundary rule first.

    The model classifies. Python does the arithmetic.

Not "mostly". Not "except for the easy sums". The model is given a list of
transactions and asked for one label per transaction. It is never asked for a
total, an average, or a difference. Then compute_totals() below, which is plain
Python with Decimal, adds up the ones labeled OPERATING_REVENUE.

Two reasons, and the second one is the one people miss.

1. Models are bad at arithmetic on five figure numbers. Everyone knows this.
2. Even when the model gets the sum right, you cannot show your work. Doug in
   compliance has to explain a declined application to the applicant in writing.
   "The model added it up" is not an explanation. "These three deposits counted,
   these two did not, here is the rule for each" is one.

The classification is the judgment call, and judgment is what a model is for.
The addition is a fact, and facts belong in code you can unit test.

There is a counterexample in this same file, on purpose. See
_legacy_revenue_summary().
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, HTTPException

from ai_service.config import get_settings
from ai_service.observability import current_context, span
from ai_service.parsing import ParseFailure, build_json_instruction, schema_for
from ai_service.prompts import render
from ai_service.providers import CompletionRequest, complete_structured, get_provider
from ai_service.schemas import (
    REVENUE_CATEGORIES,
    ClassificationModelOutput,
    ClassifyRequest,
    ClassifyResponse,
    ExcludedTransaction,
    LegacyRevenueSummary,
    RevenueTotals,
    TransactionCategory,
    TransactionClassification,
    TransactionInput,
    build_meta,
)

router = APIRouter(tags=["classification"])

PROMPT_VERSION = "txn_classify_v3"
LEGACY_PROMPT_VERSION = "revenue_summary_v1"

CENTS = Decimal("0.01")


def transactions_key_material(transactions: list[TransactionInput]) -> str:
    """The text the stub fixture key is computed from.

    Amounts are formatted to two decimals so 48230 and 48230.00 hit the same
    fixture. A learner who curls this endpoint should not have to guess the
    formatting to get a recorded answer back.
    """
    lines = []
    for txn in transactions:
        amount = Decimal(txn.amount).quantize(CENTS, rounding=ROUND_HALF_UP)
        lines.append(f"{txn.date or ''}|{txn.description}|{amount}")
    return "\n".join(lines)


def transactions_for_prompt(transactions: list[TransactionInput]) -> str:
    lines = []
    for index, txn in enumerate(transactions):
        amount = Decimal(txn.amount).quantize(CENTS, rounding=ROUND_HALF_UP)
        lines.append(f"[{index}] {txn.date or 'n/a'}  {txn.description}  {amount:+}")
    return "\n".join(lines)


def compute_totals(
    transactions: list[TransactionInput],
    classifications: list[TransactionClassification],
    months: int | None = None,
) -> RevenueTotals:
    """Add up the money. No model involved, no network, fully unit testable.

    naive_total_credits is what RevenueCalculator.java produces today: every
    credit, added. operating_revenue is the same list minus whatever the model
    labeled as something other than earned revenue.

    On the canonical May statement from CANON.md those two numbers are 252,400
    and 147,400. The 105,000 gap is one internal transfer of 30,000 and one
    Fastcapital loan deposit of 75,000. Renee spots it in two seconds and the
    system has never once caught it.
    """
    by_index = {c.index: c for c in classifications}

    naive_total = Decimal("0")
    operating = Decimal("0")
    excluded: list[ExcludedTransaction] = []

    for index, txn in enumerate(transactions):
        amount = Decimal(txn.amount).quantize(CENTS, rounding=ROUND_HALF_UP)
        if amount <= 0:
            # Debits never counted toward revenue in either definition.
            continue

        naive_total += amount

        classification = by_index.get(index)
        category = (
            classification.classification
            if classification is not None
            else TransactionCategory.UNKNOWN
        )

        if category in REVENUE_CATEGORIES:
            operating += amount
            continue

        excluded.append(
            ExcludedTransaction(
                index=index,
                description=txn.description,
                amount=amount,
                classification=category,
                reason=classification.reason if classification else "No classification returned.",
            )
        )

    monthly: Decimal | None = None
    if months and months > 0:
        monthly = (operating / Decimal(months)).quantize(
            CENTS, rounding=ROUND_HALF_UP
        )

    return RevenueTotals(
        naive_total_credits=naive_total,
        operating_revenue=operating,
        excluded_total=(naive_total - operating),
        excluded=excluded,
        months=months,
        monthly_operating_revenue=monthly,
        computed_by="python",
    )


def _model_for_tier() -> str | None:
    """Pick the model by configured tier.

    CLASSIFY_MODEL_TIER was set to premium during the accuracy push in March,
    when the loan proceeds slice was failing. It was never set back. On the stub
    provider this changes nothing except what shows up in the trace.
    """
    settings = get_settings()
    if settings.llm_provider == "ollama":
        return (
            settings.ollama_model
            if settings.classify_model_tier == "premium"
            else settings.ollama_router_model
        )
    if settings.llm_provider == "openai":
        return "gpt-4o" if settings.classify_model_tier == "premium" else "gpt-4o-mini"
    return None


def _legacy_revenue_summary(
    payload: ClassifyRequest, key_material: str
) -> tuple[LegacyRevenueSummary, object]:
    """The counterexample. This asks the model to do the arithmetic.

    This is the February code path and it is the direct cause of the Mission 32
    incident. The prompt asks for an averageRevenue number. On 2026-04-14 the
    model answered with "$78,231 approximately" instead of 78231.00. The Java
    parser threw, the retry worker could not tell a schema error from a timeout,
    and 214 applications got stuck for two hours and 45 minutes.

    Compare this with compute_totals() above. Same question, two answers. One is
    a number you can test and explain. The other is whatever the model felt like
    formatting that day.

    Runs only when the caller asks for a monthly average, and only while
    LEGACY_REVENUE_SUMMARY is on.
    """
    ctx = current_context()
    prompt = render(
        LEGACY_PROMPT_VERSION,
        months=payload.months,
        transactions=transactions_for_prompt(payload.transactions),
    )
    req = CompletionRequest(
        prompt=prompt,
        prompt_version=LEGACY_PROMPT_VERSION,
        json_mode=True,
        scenario=ctx.stub_scenario,
        trace_id=ctx.trace_id,
        tenant_id=ctx.tenant_id,
        fixture_input=key_material,
    )
    response, result = complete_structured(
        req, LegacyRevenueSummary, span_name="classify.legacy_revenue_summary"
    )
    return result.value, response


@router.post("/v1/classify/transactions", response_model=ClassifyResponse)
def classify_transactions(payload: ClassifyRequest) -> ClassifyResponse:
    ctx = current_context()
    ctx.application_id = payload.application_id or ctx.application_id
    settings = get_settings()

    key_material = transactions_key_material(payload.transactions)
    schema = schema_for(ClassificationModelOutput)
    prompt = render(
        PROMPT_VERSION,
        transactions=transactions_for_prompt(payload.transactions),
        json_instruction=build_json_instruction(schema),
    )

    req = CompletionRequest(
        prompt=prompt,
        prompt_version=PROMPT_VERSION,
        model=_model_for_tier(),
        json_mode=True,
        max_tokens=1536,
        scenario=ctx.stub_scenario,
        trace_id=ctx.trace_id,
        tenant_id=ctx.tenant_id,
        fixture_input=key_material,
    )

    response, result = complete_structured(
        req, ClassificationModelOutput, span_name="classify.transactions"
    )
    model_output: ClassificationModelOutput = result.value
    classifications = model_output.classifications

    warnings: list[str] = []
    if len(classifications) != len(payload.transactions):
        warnings.append(
            f"Sent {len(payload.transactions)} transactions and got back "
            f"{len(classifications)} classifications. Unmatched rows count as "
            "UNKNOWN and are excluded from operating revenue."
        )
    if result.repairs_applied:
        warnings.append(
            "The output needed repair before it parsed: "
            + ", ".join(result.repairs_applied)
        )

    # -- the boundary. Everything above is the model. Everything here is code. --
    totals = compute_totals(payload.transactions, classifications, payload.months)

    with span("classify.totals") as sp:
        sp.validation_result = "ok"
        sp.model = "none"
        sp.prompt_version = "n/a"
        sp.cost_basis = "0.0 because no model was called. This is plain Python."
        sp.fallback_reason = None

    legacy_summary: LegacyRevenueSummary | None = None
    if payload.months and settings.legacy_revenue_summary:
        try:
            legacy_summary, _ = _legacy_revenue_summary(payload, key_material)
        except ParseFailure as failure:
            # The failure surfaces to the caller with its kind attached. What the
            # caller does with that is Mission 32's problem.
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "model_output_invalid",
                    "traceId": ctx.trace_id,
                    **failure.to_dict(),
                },
            ) from failure

    return ClassifyResponse(
        application_id=payload.application_id,
        classifications=classifications,
        totals=totals,
        model_revenue_summary=legacy_summary,
        warnings=warnings,
        meta=build_meta(
            response,
            trace_id=ctx.trace_id,
            repairs_applied=result.repairs_applied,
        ),
    )
