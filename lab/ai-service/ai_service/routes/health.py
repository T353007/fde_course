"""Health, model inventory, and trace lookup.

Read the note on /v1/health before you copy it into a real deployment. It is
shallow on purpose, and Mission 32 is about what that costs.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ai_service import __version__
from ai_service.config import get_settings
from ai_service.observability import get_trace_store
from ai_service.prompts import available_versions
from ai_service.providers import (
    SCENARIOS,
    ProviderError,
    get_provider,
)
from ai_service.providers.base import (
    LOCAL_COST_BASIS,
    PRICE_TABLE_USD_PER_MTOK,
    STUB_COST_BASIS,
)
from ai_service.providers.ollama import SUPPORTED_MODELS as OLLAMA_MODELS
from ai_service.providers.ollama import OllamaProvider
from ai_service.schemas import (
    HealthResponse,
    ModelInfo,
    ModelsResponse,
    TraceResponse,
)

router = APIRouter(tags=["ops"])


@router.get("/v1/health", response_model=HealthResponse)
def health(deep: bool = Query(default=False)) -> HealthResponse:
    """Is the service up.

    By default this answers "the process is listening and the provider is
    loadable". That is all it answers.

    During the Mission 32 outage this endpoint was green for two hours and 45
    minutes while 214 applications were stuck, because the workflow was broken
    and the endpoint was not. Pass ?deep=true for a check that actually calls
    the provider. A real deployment needs a workflow probe on top of both.
    """
    settings = get_settings()
    reachable: bool | None = None
    detail: str | None = None

    try:
        provider = get_provider()
    except ProviderError as exc:
        return HealthResponse(
            status="degraded",
            service=settings.service_name,
            version=__version__,
            provider=settings.llm_provider,
            scenario=settings.stub_scenario,
            provider_reachable=False,
            detail=str(exc),
        )

    if deep:
        try:
            if isinstance(provider, OllamaProvider):
                installed = provider.installed_model_names()
                reachable = True
                detail = f"Ollama has {len(installed)} model(s) pulled."
            elif provider.name == "stub":
                reachable = provider.fixture_count > 0  # type: ignore[attr-defined]
                detail = f"{provider.fixture_count} fixtures loaded."  # type: ignore[attr-defined]
            else:
                reachable = True
                detail = "Credentials present. No call made, that would cost money."
        except ProviderError as exc:
            reachable = False
            detail = str(exc)

    return HealthResponse(
        status="ok" if reachable is not False else "degraded",
        service=settings.service_name,
        version=__version__,
        provider=provider.name,
        scenario=settings.stub_scenario if provider.name == "stub" else None,
        provider_reachable=reachable,
        detail=detail,
    )


@router.get("/v1/models", response_model=ModelsResponse)
def models() -> ModelsResponse:
    """What providers and models this machine can actually use right now."""
    settings = get_settings()
    entries: list[ModelInfo] = []

    # stub
    try:
        stub = get_provider("stub")
        fixture_count = stub.fixture_count  # type: ignore[attr-defined]
        entries.append(
            ModelInfo(
                provider="stub",
                model="recorded",
                available=fixture_count > 0,
                supports_json_schema=False,
                cost_basis=STUB_COST_BASIS,
                detail=f"{fixture_count} recorded fixtures on disk.",
            )
        )
    except ProviderError as exc:
        entries.append(
            ModelInfo(
                provider="stub",
                model="recorded",
                available=False,
                supports_json_schema=False,
                cost_basis=STUB_COST_BASIS,
                detail=str(exc),
            )
        )

    # ollama
    try:
        installed = set(OllamaProvider().installed_model_names())
        ollama_detail = None
    except ProviderError as exc:
        installed = set()
        ollama_detail = str(exc).split("Original error")[0].strip()
    for model_name in OLLAMA_MODELS:
        entries.append(
            ModelInfo(
                provider="ollama",
                model=model_name,
                available=model_name in installed,
                supports_json_schema=True,
                cost_basis=LOCAL_COST_BASIS,
                detail=ollama_detail
                if ollama_detail
                else (None if model_name in installed else f"Run: ollama pull {model_name}"),
            )
        )

    # hosted
    for provider_name, model_name, key in (
        ("openai", settings.openai_model, settings.openai_api_key),
        ("anthropic", settings.anthropic_model, settings.anthropic_api_key),
    ):
        priced = model_name in PRICE_TABLE_USD_PER_MTOK
        entries.append(
            ModelInfo(
                provider=provider_name,
                model=model_name,
                available=bool(key),
                supports_json_schema=provider_name == "openai",
                cost_basis=(
                    f"Billed per token at the {model_name} rate."
                    if priced
                    else f"No price on file for {model_name}, cost will report 0.0."
                ),
                detail=None if key else "No API key set. Nothing in the course needs one.",
            )
        )

    return ModelsResponse(
        active_provider=settings.llm_provider,
        models=entries,
        stub_scenarios=dict(SCENARIOS),
        prompt_versions=available_versions(),
    )


@router.get("/v1/traces/{trace_id}", response_model=TraceResponse)
def get_trace(trace_id: str) -> TraceResponse:
    """Every span recorded under one trace id.

    Send X-Trace-Id on a request, then read it back here. This is how the lab
    does Mission 31 without asking anyone to install a tracing backend.
    """
    store = get_trace_store()
    spans = store.get(trace_id)
    if not spans:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No spans for trace {trace_id}. The buffer holds the most recent "
                f"{store.max_traces} traces and it empties on restart."
            ),
        )
    return TraceResponse(
        trace_id=trace_id,
        summary=store.summary(trace_id),
        spans=[s.to_json_dict() for s in spans],
    )


@router.get("/v1/traces")
def list_traces(limit: int = Query(default=25, ge=1, le=200)) -> dict[str, object]:
    """Recent trace ids, newest first. Handy when you forgot to set one."""
    store = get_trace_store()
    ids = store.trace_ids()[:limit]
    return {"traceIds": ids, "summaries": [store.summary(t) for t in ids]}
