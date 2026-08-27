"""OpenAI provider. Only used by missions that opt into a hosted model.

No mission requires this. Every mission has to pass with LLM_PROVIDER=stub.
This exists so the model comparison missions have something real to compare
against, and so the cost numbers in Mission 34 come from a real price table.

We call the HTTP API with httpx instead of the openai package. One less
dependency, and the request body stays visible in the code, which matters when
a mission asks the learner what response_format actually sends.
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


class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.timeout = settings.hosted_timeout_seconds
        self._client = client
        if not self.api_key and client is None:
            raise ProviderNotConfigured(
                "LLM_PROVIDER=openai needs OPENAI_API_KEY. Set it, or go back to "
                "LLM_PROVIDER=stub. Nothing in the course requires a key."
            )

    def _http(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        return httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

    def supports_json_schema(self) -> bool:
        return True

    def complete(self, req: CompletionRequest) -> CompletionResponse:
        model = req.model or self.model
        messages: list[dict[str, Any]] = []
        if req.system:
            messages.append({"role": "system", "content": req.system})
        messages.append({"role": "user", "content": req.prompt})

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
        }
        if req.response_schema is not None:
            # Level 2 of the ladder. The provider rejects output that does not
            # fit the schema, so the repair step below almost never fires.
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": req.prompt_version,
                    "schema": req.response_schema,
                    "strict": True,
                },
            }
        elif req.json_mode:
            payload["response_format"] = {"type": "json_object"}
        if req.tools:
            payload["tools"] = req.tools
        if req.stop:
            payload["stop"] = req.stop

        started = time.perf_counter()
        try:
            with self._http() as client:
                response = client.post("/chat/completions", json=payload)
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(f"OpenAI call failed: {exc}") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)
        response.raise_for_status()
        body = response.json()

        choice = body["choices"][0]
        message = choice.get("message", {})
        text = message.get("content") or ""
        usage = body.get("usage", {})
        prompt_tokens = int(usage.get("prompt_tokens") or estimate_tokens(req.prompt))
        completion_tokens = int(usage.get("completion_tokens") or estimate_tokens(text))

        tool_calls = []
        for call in message.get("tool_calls") or []:
            function = call.get("function", {})
            tool_calls.append(
                ToolCall(
                    tool_name=function.get("name", ""),
                    arguments=_load_arguments(function.get("arguments")),
                    call_id=call.get("id"),
                )
            )

        return CompletionResponse(
            text=text,
            model=model,
            prompt_version=req.prompt_version,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost_usd=compute_cost_usd(model, prompt_tokens, completion_tokens),
            cost_basis=f"Billed per token by OpenAI at the {model} rate.",
            finish_reason=choice.get("finish_reason", "stop"),
            tool_calls=tool_calls,
            provider=self.name,
            raw={"id": body.get("id"), "system_fingerprint": body.get("system_fingerprint")},
        )


def _load_arguments(value: Any) -> dict[str, Any]:
    import json

    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return {"_unparsed": value}
    return loaded if isinstance(loaded, dict) else {"_value": loaded}
