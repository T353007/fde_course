"""FastAPI entry point for ai-service.

Every request gets a tenant id and a trace id. The stub scenario can be set per
request with X-Stub-Scenario without restarting the process.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from ai_service import __version__
from ai_service.config import get_settings
from ai_service.observability import RequestContext, set_context, setup_logging
from ai_service.routes import classify, extract, health, memo, policy, tools

HEADER_TENANT = "X-Tenant-Id"
HEADER_TRACE = "X-Trace-Id"
HEADER_SCENARIO = "X-Stub-Scenario"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Pull the three lab headers into a request-scoped context."""

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        tenant = request.headers.get(HEADER_TENANT)
        trace = request.headers.get(HEADER_TRACE)
        scenario = request.headers.get(HEADER_SCENARIO) or settings.stub_scenario

        from ai_service.observability import new_trace_id

        ctx = RequestContext(
            trace_id=trace or new_trace_id(),
            tenant_id=tenant,
            stub_scenario=scenario,
            route=request.url.path,
        )
        set_context(ctx)

        response = await call_next(request)
        response.headers[HEADER_TRACE] = ctx.trace_id
        if ctx.tenant_id:
            response.headers[HEADER_TENANT] = ctx.tenant_id
        if ctx.stub_scenario:
            response.headers[HEADER_SCENARIO] = ctx.stub_scenario
        return response


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title="Northstar ai-service",
        version=__version__,
        description=(
            "Model work for the Northstar Capital lab. "
            "Default provider is stub (offline, deterministic)."
        ),
    )

    # CORS is optional. The reviewer portal on 5173 needs it when calling
    # ai-service directly from the browser.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)

    app.include_router(health.router)
    app.include_router(extract.router)
    app.include_router(classify.router)
    app.include_router(policy.router)
    app.include_router(memo.router)
    app.include_router(tools.router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "service": settings.service_name,
            "version": __version__,
            "provider": settings.llm_provider,
            "docs": "/docs",
        }

    return app


app = create_app()
