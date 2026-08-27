"""Request and response models for every endpoint.

Two kinds of model live in this file and the difference matters.

Wire models are the API contract. Northstar's Java services call these, so the
JSON is camelCase. Changing a field here breaks a caller.

Model output models are what we ask the language model to fill in. They are the
schema handed to the provider at level 2 of the ladder in parsing.py, and the
schema pydantic checks at level 4. They are smaller than the wire models on
purpose. The model is asked for the least it can be trusted with.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """camelCase on the wire, snake_case in Python. Both are accepted on input."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


class ModelCallMeta(ApiModel):
    """The numbers from one or more model calls, returned to the caller.

    This is on every response body, not just in the logs. A reviewer looking at
    a suggestion in the portal should be able to see which prompt version and
    which model produced it without opening a trace.
    """

    trace_id: str
    provider: str
    model: str
    prompt_version: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cost_usd: float
    cost_basis: str
    finish_reason: str
    scenario: str | None = None
    repairs_applied: list[str] = Field(default_factory=list)
    attempts: int = 1


class ErrorBody(ApiModel):
    error: str
    message: str
    trace_id: str | None = None
    kind: str | None = None
    detail: Any = None


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


class TransactionType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class ExtractedTransaction(ApiModel):
    date: str
    description: str
    amount: Decimal
    type: TransactionType = TransactionType.CREDIT


class StatementPeriod(ApiModel):
    start: str | None = None
    end: str | None = None


class BankStatementExtraction(ApiModel):
    """What we ask the model for on a bank statement.

    Note what is not here. No totals, no average revenue, no decision. The model
    reads text off a page. Arithmetic happens in Python. See routes/classify.py
    for why that line is drawn where it is.
    """

    account_holder: str | None = None
    statement_period: StatementPeriod = Field(default_factory=StatementPeriod)
    # Blank in the source more often than not. A model that fills this in from
    # nowhere is the Mission 14 problem.
    ein: str | None = None
    transactions: list[ExtractedTransaction] = Field(default_factory=list)
    # The model's own confidence. Mission 19 is about why this number is close
    # to useless when OCR is the thing that failed.
    ocr_confidence: float | None = None
    notes: str | None = None


class ExtractRequest(ApiModel):
    document_text: str = Field(min_length=1)
    document_id: str | None = None
    application_id: str | None = None
    # What the OCR vendor claimed. Kept next to the model's own number so a
    # mission can compare two confident wrong answers.
    vendor_ocr_confidence: float | None = None
    max_tokens: int = 1024


class ExtractResponse(ApiModel):
    application_id: str | None = None
    document_id: str | None = None
    extraction: BankStatementExtraction
    warnings: list[str] = Field(default_factory=list)
    meta: ModelCallMeta


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


class TransactionCategory(str, Enum):
    """The categories Renee actually uses.

    OPERATING_REVENUE is the only one that counts toward revenue. Everything
    else is a credit that looks like revenue to the old Java function.
    """

    OPERATING_REVENUE = "OPERATING_REVENUE"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    LOAN_PROCEEDS = "LOAN_PROCEEDS"
    REFUND = "REFUND"
    OWNER_CONTRIBUTION = "OWNER_CONTRIBUTION"
    OTHER_CREDIT = "OTHER_CREDIT"
    DEBIT = "DEBIT"
    UNKNOWN = "UNKNOWN"


# Which categories add up to operating revenue. This set lives in Python and
# nowhere else. The model never sees it as an instruction to do math.
REVENUE_CATEGORIES: frozenset[TransactionCategory] = frozenset(
    {TransactionCategory.OPERATING_REVENUE}
)


class TransactionInput(ApiModel):
    date: str | None = None
    description: str
    amount: Decimal


class ClassifyRequest(ApiModel):
    transactions: list[TransactionInput] = Field(min_length=1)
    application_id: str | None = None
    # Set this when you want a monthly average. Leaving it unset skips the
    # legacy summary call, see routes/classify.py.
    months: int | None = None


class TransactionClassification(ApiModel):
    """One classified transaction, as returned by the model.

    No amount field. The model is not given a chance to restate the number, so
    it cannot get it wrong. Python matches classifications back to the input by
    index.
    """

    index: int
    description: str | None = None
    classification: TransactionCategory
    confidence: float | None = None
    reason: str | None = None


class ClassificationModelOutput(ApiModel):
    classifications: list[TransactionClassification] = Field(default_factory=list)


class ExcludedTransaction(ApiModel):
    index: int
    description: str
    amount: Decimal
    classification: TransactionCategory
    reason: str | None = None


class RevenueTotals(ApiModel):
    """All four numbers, computed in Python from the classifications.

    naive_total_credits is what RevenueCalculator.java returns today. It is kept
    in the response so Mission 09 and Mission 20 can put the two numbers side by
    side without anyone doing mental arithmetic in a meeting.
    """

    naive_total_credits: Decimal
    operating_revenue: Decimal
    excluded_total: Decimal
    excluded: list[ExcludedTransaction] = Field(default_factory=list)
    months: int | None = None
    monthly_operating_revenue: Decimal | None = None
    computed_by: str = "python"


class LegacyRevenueSummary(ApiModel):
    """The old prompt asked the model to do the arithmetic. This is that shape.

    Kept because underwriting-service still reads it. Mission 21 removes it.
    """

    average_revenue: Decimal
    method: str | None = None


class ClassifyResponse(ApiModel):
    application_id: str | None = None
    classifications: list[TransactionClassification]
    totals: RevenueTotals
    model_revenue_summary: LegacyRevenueSummary | None = None
    warnings: list[str] = Field(default_factory=list)
    meta: ModelCallMeta


# ---------------------------------------------------------------------------
# Policy answering
# ---------------------------------------------------------------------------


class PolicyAnswerRequest(ApiModel):
    question: str = Field(min_length=1)
    # Falls back to the X-Tenant-Id header when not set in the body.
    tenant_id: str | None = None
    product: str | None = None
    # Which day the answer should be correct for. Defaults to today.
    effective_date: date | None = None
    top_k: int | None = None


class Citation(ApiModel):
    doc_id: str
    title: str
    chunk_id: str
    score: float
    excerpt: str
    tenant_scope: str | None = None
    product_scope: str | None = None
    effective_from: str | None = None


class PolicyAnswerModelOutput(ApiModel):
    answer: str
    cited_chunk_ids: list[str] = Field(default_factory=list)
    confident: bool = True


class PolicyAnswerResponse(ApiModel):
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    meta: ModelCallMeta


# ---------------------------------------------------------------------------
# Credit memo
# ---------------------------------------------------------------------------


class MemoRequest(ApiModel):
    application_id: str
    applicant_name: str
    product: str
    amount_requested: Decimal | None = None
    operating_revenue: Decimal | None = None
    months_of_history: int | None = None
    reason_codes: list[str] = Field(default_factory=list)
    notes: str | None = None


class MemoModelOutput(ApiModel):
    summary: str
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    recommendation: str | None = None


class MemoResponse(ApiModel):
    application_id: str
    memo: MemoModelOutput
    citations: list[Citation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    meta: ModelCallMeta


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


class ToolInvokeRequest(ApiModel):
    question: str = Field(min_length=1)
    application_id: str | None = None
    # When set, only these tools may run. When unset, see routes/tools.py.
    allowed_tools: list[str] | None = None
    dry_run: bool = False


class ToolCallRecord(ApiModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    kind: str = "unknown"  # read_only or mutating
    executed: bool = False
    blocked_reason: str | None = None
    result: Any = None


class ToolInvokeResponse(ApiModel):
    question: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    answer: str | None = None
    warnings: list[str] = Field(default_factory=list)
    meta: ModelCallMeta


class ToolDescriptor(ApiModel):
    name: str
    description: str
    kind: str
    parameters: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Health and models
# ---------------------------------------------------------------------------


class HealthResponse(ApiModel):
    status: str
    service: str
    version: str
    provider: str
    scenario: str | None = None
    # True when the configured provider answered a real probe. The Mission 32
    # health check only proved the process was listening, which is why it was
    # green during the outage.
    provider_reachable: bool | None = None
    detail: str | None = None


class ModelInfo(ApiModel):
    provider: str
    model: str
    available: bool
    supports_json_schema: bool
    cost_basis: str
    detail: str | None = None


class ModelsResponse(ApiModel):
    active_provider: str
    models: list[ModelInfo]
    stub_scenarios: dict[str, str] = Field(default_factory=dict)
    prompt_versions: list[str] = Field(default_factory=list)


class TraceSpanView(ApiModel):
    model_config = ConfigDict(extra="allow")


class TraceResponse(ApiModel):
    trace_id: str
    summary: dict[str, Any]
    spans: list[dict[str, Any]]


def build_meta(
    response: Any,
    *,
    trace_id: str,
    repairs_applied: list[str] | None = None,
    attempts: int = 1,
) -> ModelCallMeta:
    """Copy the provider numbers onto the response body.

    Takes any CompletionResponse without importing the provider layer, so the
    schema module stays free of dependencies.
    """
    return ModelCallMeta(
        trace_id=trace_id,
        provider=getattr(response, "provider", "unknown"),
        model=response.model,
        prompt_version=response.prompt_version,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        latency_ms=response.latency_ms,
        cost_usd=response.cost_usd,
        cost_basis=response.cost_basis,
        finish_reason=response.finish_reason,
        scenario=(getattr(response, "raw", {}) or {}).get("scenario"),
        repairs_applied=repairs_applied or [],
        attempts=attempts,
    )
