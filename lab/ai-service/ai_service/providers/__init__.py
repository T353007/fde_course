"""Provider factory. One environment variable picks the model backend.

    LLM_PROVIDER=stub       default. offline, free, deterministic
    LLM_PROVIDER=ollama     a model on your own machine
    LLM_PROVIDER=openai     hosted
    LLM_PROVIDER=anthropic  hosted

Nothing above this layer knows which one is in use. That is the whole point.
When a route needs a model it calls get_provider() and reads the same fields off
CompletionResponse either way.
"""

from __future__ import annotations

from typing import Callable

from pydantic import BaseModel

from ai_service.config import get_settings
from ai_service.observability import span
from ai_service.parsing import (
    ParseFailure,
    ParsedResult,
    call_with_retry,
    parse_structured,
    schema_for,
)
from ai_service.providers.anthropic_provider import AnthropicProvider
from ai_service.providers.base import (
    CompletionRequest,
    CompletionResponse,
    FixtureMissing,
    LLMProvider,
    ModelNotAvailable,
    ProviderError,
    ProviderNotConfigured,
    ProviderUnavailable,
    ToolCall,
    estimate_tokens,
    input_sha256,
    normalize_input,
)
from ai_service.providers.ollama import OllamaProvider
from ai_service.providers.openai_provider import OpenAIProvider
from ai_service.providers.stub import SCENARIOS, StubProvider

__all__ = [
    "AnthropicProvider",
    "CompletionRequest",
    "CompletionResponse",
    "FixtureMissing",
    "LLMProvider",
    "ModelNotAvailable",
    "OllamaProvider",
    "OpenAIProvider",
    "ProviderError",
    "ProviderNotConfigured",
    "ProviderUnavailable",
    "SCENARIOS",
    "StubProvider",
    "ToolCall",
    "complete_structured",
    "estimate_tokens",
    "get_provider",
    "input_sha256",
    "normalize_input",
    "reset_provider_cache",
]

_BUILDERS: dict[str, Callable[[], LLMProvider]] = {
    "stub": StubProvider,
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

# The stub reads its whole fixture bank from disk, so we build it once. The
# others hold no state worth caching but the same handle keeps traces tidy.
_cache: dict[str, LLMProvider] = {}


def get_provider(name: str | None = None) -> LLMProvider:
    provider_name = name or get_settings().llm_provider
    if provider_name not in _BUILDERS:
        known = ", ".join(sorted(_BUILDERS))
        raise ProviderNotConfigured(
            f"Unknown LLM_PROVIDER {provider_name!r}. Pick one of: {known}."
        )
    if provider_name not in _cache:
        _cache[provider_name] = _BUILDERS[provider_name]()
    return _cache[provider_name]


def reset_provider_cache() -> None:
    """Drop built providers. Tests call this after changing the environment."""
    _cache.clear()


def complete_structured(
    req: CompletionRequest,
    model_cls: type[BaseModel],
    *,
    span_name: str,
    provider: LLMProvider | None = None,
    retry_policy: str | None = None,
) -> tuple[CompletionResponse, ParsedResult]:
    """One model call, all four levels of the ladder, one span, retry policy applied.

    Every route goes through here. That is what makes the trace records
    consistent and it is what makes the retry behavior consistent, including the
    part of it that is wrong on purpose.

    Level 2 of the ladder happens right here: if the provider can enforce a JSON
    schema, we hand it one. If it cannot, we do not pretend, and the repair
    steps downstream earn their keep.
    """
    provider = provider or get_provider()

    if req.response_schema is None and provider.supports_json_schema():
        req = req.model_copy(update={"response_schema": schema_for(model_cls)})

    attempts_used = 0
    last_response: dict[str, CompletionResponse] = {}

    with span(span_name) as sp:

        def attempt() -> ParsedResult:
            nonlocal attempts_used
            attempts_used += 1
            response = provider.complete(req)
            last_response["value"] = response
            sp.apply_completion(response)
            return parse_structured(
                response.text,
                model_cls,
                finish_reason=response.finish_reason,
                prompt_version=req.prompt_version,
            )

        try:
            result = call_with_retry(attempt, policy=retry_policy)
        except ParseFailure as failure:
            sp.attempts = attempts_used
            sp.validation_result = failure.kind.value
            sp.repairs_applied = failure.repairs_applied
            sp.fallback_reason = f"parse_failure:{failure.kind.value}"
            raise

        sp.attempts = attempts_used
        sp.repairs_applied = result.repairs_applied
        sp.validation_result = "repaired" if result.repairs_applied else "ok"

    return last_response["value"], result
