"""POST /v1/tools/invoke

The model proposes tool calls. This route decides what actually runs.

ENFORCE_TOOL_AUTHORIZATION defaults to false. That is the Mission 27 defect:
a read question can still trigger declineApplication until the flag is turned on.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ai_service.config import get_settings
from ai_service.observability import current_context, span
from ai_service.parsing import ParseFailure, parse_structured
from ai_service.prompts import render
from ai_service.providers import CompletionRequest, get_provider
from ai_service.providers.base import CompletionResponse
from ai_service.schemas import (
    ToolCallRecord,
    ToolDescriptor,
    ToolInvokeRequest,
    ToolInvokeResponse,
    build_meta,
)
from ai_service.tools import TOOLS, format_tools_for_prompt, run_tool, tool_descriptors
from pydantic import BaseModel, Field

router = APIRouter(tags=["tools"])

PROMPT_VERSION = "tool_router_v1"


class ToolRouterOutput(BaseModel):
    """What we ask the model to fill in for tool routing."""

    answer: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)


def _authorized(
    tool_name: str,
    *,
    allowed_tools: list[str] | None,
    enforce: bool,
) -> tuple[bool, str | None]:
    spec = TOOLS.get(tool_name)
    if spec is None:
        return False, f"Unknown tool {tool_name!r}."
    if allowed_tools is not None and tool_name not in allowed_tools:
        return False, f"{tool_name} is not in the caller's allowedTools list."
    if not enforce:
        return True, None
    if spec["kind"] == "mutating":
        # Even with an allowlist, mutating tools need the flag on and an
        # explicit allow. A missing allowlist means no mutating tools.
        if allowed_tools is None or tool_name not in allowed_tools:
            return (
                False,
                f"{tool_name} is mutating and was blocked by tool authorization.",
            )
    return True, None


@router.get("/v1/tools", response_model=list[ToolDescriptor])
def list_tools() -> list[ToolDescriptor]:
    return [ToolDescriptor(**d) for d in tool_descriptors()]


@router.post("/v1/tools/invoke", response_model=ToolInvokeResponse)
def invoke_tools(payload: ToolInvokeRequest) -> ToolInvokeResponse:
    settings = get_settings()
    ctx = current_context()
    ctx.application_id = payload.application_id or ctx.application_id

    names = payload.allowed_tools or list(TOOLS)
    prompt = render(
        PROMPT_VERSION,
        tools=format_tools_for_prompt(names),
        question=payload.question,
        application_id=payload.application_id or "n/a",
        json_instruction=(
            "Return JSON with an optional answer string and a toolCalls array. "
            "Each tool call needs toolName and arguments."
        ),
    )

    req = CompletionRequest(
        prompt=prompt,
        prompt_version=PROMPT_VERSION,
        json_mode=True,
        tools=[{"name": n, **TOOLS[n]} for n in names if n in TOOLS],
        scenario=ctx.stub_scenario,
        trace_id=ctx.trace_id,
        tenant_id=ctx.tenant_id,
        fixture_input=payload.question,
    )

    provider = get_provider()
    with span("tools.route") as sp:
        response: CompletionResponse = provider.complete(req)
        sp.apply_completion(response)

    records: list[ToolCallRecord] = []
    answer: str | None = None
    warnings: list[str] = []
    repairs: list[str] = []

    # Prefer structured tool_calls from the provider (stub scenarios use this).
    proposed: list[tuple[str, dict[str, Any]]] = [
        (tc.tool_name, dict(tc.arguments or {})) for tc in response.tool_calls
    ]

    if not proposed and response.text.strip():
        try:
            parsed = parse_structured(
                response.text,
                ToolRouterOutput,
                finish_reason=response.finish_reason,
                prompt_version=PROMPT_VERSION,
            )
            repairs = parsed.repairs_applied
            answer = parsed.value.answer
            for item in parsed.value.tool_calls:
                name = item.get("toolName") or item.get("tool_name") or item.get("name")
                args = item.get("arguments") or item.get("args") or {}
                if name:
                    proposed.append((str(name), dict(args)))
        except ParseFailure as failure:
            # A free-text answer with no tool calls is still useful.
            if response.tool_calls:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "error": "model_output_invalid",
                        "traceId": ctx.trace_id,
                        **failure.to_dict(),
                    },
                ) from failure
            answer = response.text.strip()
            warnings.append(
                "Model output was not structured tool JSON. Returned as answer text."
            )

    for tool_name, arguments in proposed:
        kind = TOOLS.get(tool_name, {}).get("kind", "unknown")
        ok, reason = _authorized(
            tool_name,
            allowed_tools=payload.allowed_tools,
            enforce=settings.enforce_tool_authorization,
        )
        record = ToolCallRecord(
            tool_name=tool_name,
            arguments=arguments,
            kind=kind,
            executed=False,
            blocked_reason=reason,
        )
        if not ok:
            records.append(record)
            continue
        if payload.dry_run:
            record.blocked_reason = "dry_run"
            records.append(record)
            continue
        with span(f"tools.execute.{tool_name}") as sp:
            result = run_tool(tool_name, arguments, tenant_id=ctx.tenant_id)
            record.executed = True
            record.result = result
            sp.tools_used = [tool_name]
            sp.validation_result = "ok"
            sp.model = "none"
            sp.prompt_version = "n/a"
            sp.cost_basis = "0.0 because the tool ran in-process."
        records.append(record)

    if answer is None and records:
        executed = [r for r in records if r.executed]
        blocked = [r for r in records if r.blocked_reason]
        if executed and not any(r.tool_name == "declineApplication" and r.executed for r in records):
            answer = "Tool calls completed. See toolCalls for results."
        elif any(r.tool_name == "declineApplication" and r.executed for r in records):
            answer = "Application decline was submitted."
        elif blocked and not executed:
            answer = "No tools ran. See blockedReason on each tool call."

    if repairs:
        warnings.append("The output needed repair before it parsed: " + ", ".join(repairs))

    return ToolInvokeResponse(
        question=payload.question,
        tool_calls=records,
        answer=answer,
        warnings=warnings,
        meta=build_meta(response, trace_id=ctx.trace_id, repairs_applied=repairs),
    )
