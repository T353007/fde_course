"""Anthropic provider. Same role as the OpenAI one, different wire format.

Two hosted providers exist so no mission can quietly depend on one vendor's
features. If a mission only works with one of them, the mission is wrong.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from ai_service.config import get_settings
from ai_service.providers.base import (
    CompletionRequest,
    CompletionResponse,
    ProviderNotConfigured,
    ProviderUnavailable,
    ToolCall,
    compute_cost_usd,
    estimate_tokens,
)

ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.anthropic_model
        self.base_url = (base_url or settings.anthropic_base_url).rstrip("/")
        self.timeout = settings.hosted_timeout_seconds
        self._client = client
        if not self.api_key and client is None:
            raise ProviderNotConfigured(
                "LLM_PROVIDER=anthropic needs ANTHROPIC_API_KEY. Set it, or go "
                "back to LLM_PROVIDER=stub."
            )

    def _http(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        return httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "x-api-key": self.api_key or "",
                "anthropic-version": ANTHROPIC_VERSION,
            },
        )

    def supports_json_schema(self) -> bool:
        """False.

        Anthropic has no response_format field. The usual trick is a tool with
        an input schema. That is a real technique and Mission 13 covers it, but
        it is not the same guarantee, so this returns False and the repair
        ladder stays in play.
        """
        return False

    def complete(self, req: CompletionRequest) -> CompletionResponse:
        model = req.model or self.model
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": req.max_tokens,
            "temperature": req.temperature,
            "messages": [{"role": "user", "content": req.prompt}],
        }
        if req.system:
            payload["system"] = req.system
        if req.tools:
            payload["tools"] = req.tools
        if req.stop:
            payload["stop_sequences"] = req.stop

        started = time.perf_counter()
        try:
            with self._http() as client:
                response = client.post("/messages", json=payload)
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(f"Anthropic call failed: {exc}") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)
        response.raise_for_status()
        body = response.json()

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in body.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(
                        tool_name=block.get("name", ""),
                        arguments=block.get("input", {}) or {},
                        call_id=block.get("id"),
                    )
                )
        text = "".join(text_parts)

        usage = body.get("usage", {})
        prompt_tokens = int(usage.get("input_tokens") or estimate_tokens(req.prompt))
        completion_tokens = int(usage.get("output_tokens") or estimate_tokens(text))
        stop_reason = body.get("stop_reason") or "end_turn"
        finish_reason = "length" if stop_reason == "max_tokens" else "stop"

        return CompletionResponse(
            text=text,
            model=model,
            prompt_version=req.prompt_version,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost_usd=compute_cost_usd(model, prompt_tokens, completion_tokens),
            cost_basis=f"Billed per token by Anthropic at the {model} rate.",
            finish_reason=finish_reason,
            tool_calls=tool_calls,
            provider=self.name,
            raw={"id": body.get("id"), "stop_reason": stop_reason},
        )
