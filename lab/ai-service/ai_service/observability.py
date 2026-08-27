"""Traces, spans, and the numbers you need when something goes wrong at 2 pm.

The rule here comes from the Mission 32 timeline. Monitoring was green while 214
applications sat stuck, because the health check tested the endpoint and not the
workflow. So a span in this service records what the model did, not whether the
process is alive.

Every model call writes one span with all of this:

    traceId, applicationId, tenantId, model, promptVersion,
    promptTokens, completionTokens, latencyMs, costUsd,
    toolsUsed, retrievedDocIds, validationResult, fallbackReason

Two outputs. Structured JSON on stdout, which is what a real deployment ships to
a log platform. And an in memory ring buffer behind GET /v1/traces/{traceId},
which is what the lab uses because nobody is running Datadog on a laptop.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from typing import Any, Iterator

from ai_service.config import get_settings

__all__ = [
    "RequestContext",
    "Span",
    "TraceStore",
    "current_context",
    "get_trace_store",
    "new_trace_id",
    "record_span",
    "set_context",
    "setup_logging",
    "span",
]

logger = logging.getLogger("ai_service.trace")


def new_trace_id() -> str:
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# Request context
# ---------------------------------------------------------------------------


@dataclass
class RequestContext:
    trace_id: str
    tenant_id: str | None = None
    application_id: str | None = None
    stub_scenario: str | None = None
    route: str | None = None


_context: ContextVar[RequestContext | None] = ContextVar("ai_service_ctx", default=None)


def set_context(ctx: RequestContext) -> None:
    _context.set(ctx)


def current_context() -> RequestContext:
    ctx = _context.get()
    if ctx is None:
        # A span outside a request, usually a test or a CLI tool. Give it a
        # trace id anyway so the record is still complete.
        ctx = RequestContext(trace_id=new_trace_id())
        _context.set(ctx)
    return ctx


# ---------------------------------------------------------------------------
# Spans
# ---------------------------------------------------------------------------


@dataclass
class Span:
    """One unit of work worth measuring. Usually one model call."""

    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    tenant_id: str | None = None
    application_id: str | None = None
    route: str | None = None

    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    scenario: str | None = None

    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    cost_basis: str | None = None
    finish_reason: str | None = None

    tools_used: list[str] = field(default_factory=list)
    retrieved_doc_ids: list[str] = field(default_factory=list)

    # "ok", "repaired", or a ParseFailureKind value. This field is why the
    # incident in Mission 32 is findable from a trace instead of from Carla's
    # ticket queue.
    validation_result: str | None = None
    repairs_applied: list[str] = field(default_factory=list)
    fallback_reason: str | None = None

    attempts: int = 1
    status: str = "ok"
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    duration_ms: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def to_json_dict(self) -> dict[str, Any]:
        """camelCase, because that is what the rest of the lab speaks."""
        return {
            "traceId": self.trace_id,
            "spanId": self.span_id,
            "name": self.name,
            "route": self.route,
            "tenantId": self.tenant_id,
            "applicationId": self.application_id,
            "provider": self.provider,
            "model": self.model,
            "promptVersion": self.prompt_version,
            "scenario": self.scenario,
            "promptTokens": self.prompt_tokens,
            "completionTokens": self.completion_tokens,
            "totalTokens": self.total_tokens,
            "latencyMs": self.latency_ms,
            "durationMs": self.duration_ms,
            "costUsd": self.cost_usd,
            "costBasis": self.cost_basis,
            "finishReason": self.finish_reason,
            "toolsUsed": self.tools_used,
            "retrievedDocIds": self.retrieved_doc_ids,
            "validationResult": self.validation_result,
            "repairsApplied": self.repairs_applied,
            "fallbackReason": self.fallback_reason,
            "attempts": self.attempts,
            "status": self.status,
            "error": self.error,
            "startedAt": self.started_at,
        }


# ---------------------------------------------------------------------------
# Trace store
# ---------------------------------------------------------------------------


class TraceStore:
    """A bounded, in memory list of spans grouped by trace id.

    This is not a tracing backend and it is not trying to be. It holds the last
    few hundred traces so a mission can curl one and read it. Restarting the
    service loses everything, which is fine, and is also a point Mission 31
    makes about why you do not build your own.
    """

    def __init__(self, max_traces: int | None = None) -> None:
        self.max_traces = max_traces or get_settings().trace_buffer_size
        self._traces: OrderedDict[str, list[Span]] = OrderedDict()

    def add(self, span_record: Span) -> None:
        trace = self._traces.get(span_record.trace_id)
        if trace is None:
            trace = []
            self._traces[span_record.trace_id] = trace
            while len(self._traces) > self.max_traces:
                self._traces.popitem(last=False)
        trace.append(span_record)
        self._traces.move_to_end(span_record.trace_id)

    def get(self, trace_id: str) -> list[Span]:
        return list(self._traces.get(trace_id, []))

    def trace_ids(self) -> list[str]:
        return list(reversed(self._traces.keys()))

    def summary(self, trace_id: str) -> dict[str, Any]:
        spans = self.get(trace_id)
        return {
            "traceId": trace_id,
            "spanCount": len(spans),
            "totalTokens": sum(s.total_tokens for s in spans),
            "totalCostUsd": round(sum(s.cost_usd for s in spans), 6),
            "totalLatencyMs": sum(s.latency_ms for s in spans),
            "modelCalls": len([s for s in spans if s.model]),
            "statuses": sorted({s.status for s in spans}),
        }

    def clear(self) -> None:
        self._traces.clear()


_store: TraceStore | None = None


def get_trace_store() -> TraceStore:
    global _store
    if _store is None:
        _store = TraceStore()
    return _store


def record_span(span_record: Span) -> None:
    """Put a span in the store and write it to the log."""
    get_trace_store().add(span_record)
    logger.info("model_call", extra={"span": span_record.to_json_dict()})


@contextmanager
def span(name: str, **overrides: Any) -> Iterator[Span]:
    """Open a span, fill it in as you go, and it gets recorded on the way out.

    Usage:

        with span("classify.transactions") as sp:
            response = provider.complete(req)
            sp.apply_completion(response)

    An exception still records the span, with status "error". A span that only
    exists on the happy path is worse than no span.
    """
    ctx = current_context()
    record = Span(
        name=name,
        trace_id=overrides.pop("trace_id", None) or ctx.trace_id,
        tenant_id=overrides.pop("tenant_id", None) or ctx.tenant_id,
        application_id=overrides.pop("application_id", None) or ctx.application_id,
        route=overrides.pop("route", None) or ctx.route,
        scenario=overrides.pop("scenario", None) or ctx.stub_scenario,
    )
    for key, value in overrides.items():
        setattr(record, key, value)

    started = time.perf_counter()
    try:
        yield record
    except Exception as exc:
        record.status = "error"
        record.error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        record.duration_ms = int((time.perf_counter() - started) * 1000)
        if not record.latency_ms:
            record.latency_ms = record.duration_ms
        record_span(record)


def apply_completion(record: Span, response: Any) -> None:
    """Copy the provider's numbers onto the span.

    Every provider returns the same fields, so this function does not care which
    one answered.
    """
    record.provider = getattr(response, "provider", None)
    record.model = response.model
    record.prompt_version = response.prompt_version
    record.prompt_tokens = response.prompt_tokens
    record.completion_tokens = response.completion_tokens
    record.latency_ms = response.latency_ms
    record.cost_usd = response.cost_usd
    record.cost_basis = response.cost_basis
    record.finish_reason = response.finish_reason
    if response.tool_calls:
        record.tools_used = [tc.tool_name for tc in response.tool_calls]
    scenario = (response.raw or {}).get("scenario")
    if scenario:
        record.scenario = scenario


# Attached as a method so route code reads well.
Span.apply_completion = apply_completion  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


class JsonLogFormatter(logging.Formatter):
    """One JSON object per line. Structured logs are not optional in fintech."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        span_data = getattr(record, "span", None)
        if span_data:
            payload["span"] = span_data
        extra = getattr(record, "fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging() -> None:
    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    if settings.log_format == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())
