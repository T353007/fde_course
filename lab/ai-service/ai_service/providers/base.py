"""The provider contract.

Four providers implement this: stub, ollama, openai, anthropic. Code above this
layer never imports a provider directly. It calls get_provider() and works with
CompletionRequest and CompletionResponse.

The rule that keeps the lab honest: CompletionResponse always carries the same
fields, no matter which provider answered. A mission that measures cost or
latency reads the same attribute every time.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

# Cost per million tokens. Local and stub providers are not on this table
# because they are not billed per token.
PRICE_TABLE_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-5-haiku-20241022": (0.80, 4.00),
}

STUB_COST_BASIS = (
    "0.0 because nothing was called. The stub replays recorded output from disk."
)
LOCAL_COST_BASIS = (
    "0.0 because Ollama has no per-token billing. The real cost is hardware and "
    "it is fixed whether you make one call or ten thousand. Northstar's plan is "
    "two A10G instances, so the cost lives in the monthly instance bill."
)


class ToolCall(BaseModel):
    """A tool the model asked to run. Asking is not permission to run it."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    call_id: str | None = None


class CompletionRequest(BaseModel):
    """Everything a provider needs for one model call."""

    prompt: str
    prompt_version: str
    model: str | None = None
    system: str | None = None
    temperature: float = 0.0
    max_tokens: int = 1024
    # Level 2 of the structured output ladder. Providers that return True from
    # supports_json_schema() will enforce this. The rest ignore it.
    response_schema: dict[str, Any] | None = None
    json_mode: bool = False
    tools: list[dict[str, Any]] | None = None
    stop: list[str] | None = None
    # Routing and audit context, not sent to the model.
    scenario: str | None = None
    trace_id: str | None = None
    tenant_id: str | None = None
    # The text the fixture key is computed from. When it is None the stub keys
    # on the whole prompt. Routes set it to the caller's raw input so a prompt
    # template edit does not invalidate every fixture.
    fixture_input: str | None = None

    def key_material(self) -> str:
        return self.fixture_input if self.fixture_input is not None else self.prompt


class CompletionResponse(BaseModel):
    """One model answer, plus the numbers every mission needs.

    cost_basis exists because a bare 0.0 is misleading. A learner who sees
    cost_usd=0.0 on a local model should read one sentence and understand that
    the money moved to the hardware bill instead of disappearing.
    """

    text: str
    model: str
    prompt_version: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cost_usd: float
    cost_basis: str
    finish_reason: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    provider: str = "unknown"
    # Free-form provider detail. Handy in traces, never used for control flow.
    raw: dict[str, Any] = Field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def complete(self, req: CompletionRequest) -> CompletionResponse: ...

    def supports_json_schema(self) -> bool: ...


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ProviderError(RuntimeError):
    """Base class for anything the provider layer raises."""


class FixtureMissing(ProviderError):
    """The stub has no recorded answer for this key.

    This is deliberately loud. A quiet fallback would let a mission pass with a
    made up number, which is the exact failure the course is teaching people to
    catch.
    """

    def __init__(self, prompt_version: str, input_sha256: str, scenario: str) -> None:
        self.prompt_version = prompt_version
        self.input_sha256 = input_sha256
        self.scenario = scenario
        super().__init__(
            f"No recorded fixture for prompt_version={prompt_version!r} "
            f"scenario={scenario!r} input_sha256={input_sha256}. "
            "Add a fixture under fixtures/recorded/ or fix the caller. "
            "Run `python -m ai_service.tools.fixture_key` to print the key for "
            "a given input."
        )


class ProviderUnavailable(ProviderError):
    """The provider is configured but cannot be reached."""


class ModelNotAvailable(ProviderError):
    """The provider is up but does not have the requested model."""


class ProviderNotConfigured(ProviderError):
    """A required API key or package is missing."""


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_WHITESPACE = re.compile(r"\s+")


def normalize_input(text: str) -> str:
    """Flatten text so small formatting changes do not change the fixture key.

    Line endings, indentation, and letter case all vary between a PDF, a curl
    call, and a test. None of that should change which recorded answer we get
    back. What does change the key is different words or different numbers.
    """
    return _WHITESPACE.sub(" ", text.replace("\r\n", "\n").strip()).casefold()


def input_sha256(text: str) -> str:
    """The second part of the stub's lookup key."""
    return hashlib.sha256(normalize_input(text).encode("utf-8")).hexdigest()


def estimate_tokens(text: str) -> int:
    """Rough token count, about four characters per token.

    This is an estimate and the code says so out loud. Real tokenizers disagree
    with each other. When a provider reports real counts we use those instead.
    Mission 34 cares about the shape of the bill, not the third digit.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def compute_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Price a hosted call. Unknown models price at 0.0 and say so upstream."""
    prices = PRICE_TABLE_USD_PER_MTOK.get(model)
    if prices is None:
        return 0.0
    prompt_price, completion_price = prices
    cost = (prompt_tokens / 1_000_000) * prompt_price
    cost += (completion_tokens / 1_000_000) * completion_price
    return round(cost, 6)
