"""Ollama provider. A model running on the learner's own machine.

Why this exists is a compliance story, not a hardware hobby. Doug in compliance
and Yuki in security look at the design and ask why bank transaction text and
owner SSNs are leaving the building. Running the model locally is the answer.

Models the course uses:
  qwen3:8b     main path
  qwen3:1.7b   routing experiments, Mission 35
  llama3.1:8b  comparison runs

Cost is 0.0 per call and that number is true and misleading at the same time.
See LOCAL_COST_BASIS in base.py.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from ai_service.config import get_settings
from ai_service.providers.base import (
    LOCAL_COST_BASIS,
    CompletionRequest,
    CompletionResponse,
    ModelNotAvailable,
    ProviderUnavailable,
    ToolCall,
    estimate_tokens,
)

SUPPORTED_MODELS = ("qwen3:8b", "qwen3:1.7b", "llama3.1:8b")


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        settings = get_settings()
        self.host = (host or settings.ollama_host).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout_seconds
        self._client = client

    def _http(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        return httpx.Client(base_url=self.host, timeout=self.timeout)

    def supports_json_schema(self) -> bool:
        """Ollama accepts a JSON schema in the `format` field.

        It is weaker than a hosted provider's constrained decoding. The 8b model
        will still hand you a trailing sentence sometimes. Keep the repair
        ladder in parsing.py turned on.
        """
        return True

    # -- daemon inspection -------------------------------------------------

    def list_models(self) -> list[dict[str, Any]]:
        """Ask the daemon what is pulled. Raises if the daemon is not running."""
        try:
            with self._http() as client:
                response = client.get("/api/tags")
                response.raise_for_status()
                return response.json().get("models", [])
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(
                f"Cannot reach Ollama at {self.host}. Start it with `ollama serve`, "
                "or set LLM_PROVIDER=stub to run offline. "
                f"Original error: {exc}"
            ) from exc

    def installed_model_names(self) -> list[str]:
        return [m.get("name", "") for m in self.list_models()]

    def _assert_model_present(self, model: str) -> None:
        installed = self.installed_model_names()
        if model in installed:
            return
        # Ollama reports "qwen3:8b" but people type "qwen3". Accept the family
        # match for the error message so the advice is precise.
        family = model.split(":")[0]
        near = [m for m in installed if m.split(":")[0] == family]
        hint = f" You do have {', '.join(near)}." if near else ""
        raise ModelNotAvailable(
            f"Ollama is running at {self.host} but {model!r} is not pulled.{hint} "
            f"Fix it with:  ollama pull {model}\n"
            "The 8b models need about 6 GB of free RAM. If you have 8 GB total, "
            f"use qwen3:1.7b instead, or set LLM_PROVIDER=stub."
        )

    # -- the provider contract --------------------------------------------

    def complete(self, req: CompletionRequest) -> CompletionResponse:
        model = req.model or self.model
        payload: dict[str, Any] = {
            "model": model,
            "prompt": req.prompt,
            "stream": False,
            "options": {
                "temperature": req.temperature,
                "num_predict": req.max_tokens,
            },
        }
        if req.system:
            payload["system"] = req.system
        if req.stop:
            payload["options"]["stop"] = req.stop
        if req.response_schema is not None:
            payload["format"] = req.response_schema
        elif req.json_mode:
            payload["format"] = "json"

        # Time the whole round trip, not just the daemon's own number. A learner
        # comparing local to hosted needs wall clock, including model load.
        started = time.perf_counter()
        try:
            with self._http() as client:
                response = client.post("/api/generate", json=payload)
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(
                f"Cannot reach Ollama at {self.host}. Start it with `ollama serve`, "
                f"or set LLM_PROVIDER=stub. Original error: {exc}"
            ) from exc
        latency_ms = int((time.perf_counter() - started) * 1000)

        if response.status_code == 404:
            # Ollama returns 404 with "model not found" when it is not pulled.
            self._assert_model_present(model)
            raise ModelNotAvailable(
                f"Ollama returned 404 for model {model!r}. Try `ollama pull {model}`."
            )
        response.raise_for_status()
        body = response.json()

        text = body.get("response", "") or ""
        prompt_tokens = body.get("prompt_eval_count") or estimate_tokens(req.prompt)
        completion_tokens = body.get("eval_count") or estimate_tokens(text)
        finish_reason = "length" if body.get("done_reason") == "length" else "stop"

        return CompletionResponse(
            text=text,
            model=model,
            prompt_version=req.prompt_version,
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            latency_ms=latency_ms,
            cost_usd=0.0,
            cost_basis=LOCAL_COST_BASIS,
            finish_reason=finish_reason,
            tool_calls=[ToolCall(**tc) for tc in body.get("tool_calls", []) or []],
            provider=self.name,
            raw={
                # total_duration is nanoseconds from the daemon. Keep it next to
                # our wall clock number so a mission can show the gap.
                "daemon_total_duration_ns": body.get("total_duration"),
                "daemon_load_duration_ns": body.get("load_duration"),
                "wall_clock_ms": latency_ms,
                "host": self.host,
            },
        )
