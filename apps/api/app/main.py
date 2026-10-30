"""FastAPI application factory (design §5.1).

Wires CORS, request trace IDs, baseline security headers, canonical error
payloads, the health endpoint, and prototype schema bootstrapping. Domain
routers are registered by later phases.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import API_VERSION, get_settings
from app.db import create_all
from app.errors import AppError
from app.routers import (
    admin,
    audit,
    auth,
    batches,
    cases,
    dashboards,
    enrollments,
    institutions,
    notifications,
    programmes,
    reports,
    review,
    student,
    users,
    verification,
)

logger = logging.getLogger(__name__)

TRACE_ID_HEADER = "X-Request-Id"

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def _json_safe(value: Any) -> Any:
    """Convert validation context exceptions into safe JSON values."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, BaseException):
        return str(value)
    return value


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a trace id to every request and echo it on the response."""

    async def dispatch(self, request: Request, call_next: Any) -> JSONResponse:
        trace_id = request.headers.get(TRACE_ID_HEADER) or f"trc_{uuid4()}"
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers[TRACE_ID_HEADER] = trace_id
        response.headers.setdefault("Cache-Control", "no-store")
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        return response


def _error_body(request: Request, code: str, message: str, details: Any = None) -> dict[str, Any]:
    trace_id = getattr(request.state, "trace_id", None) or f"trc_{uuid4()}"
    return {
        "error": {"code": code, "message": message, "details": details},
        "traceId": trace_id,
    }


async def health() -> JSONResponse:
    """GET /api/v1/health — liveness for compose, CI and demos."""
    return JSONResponse({"status": "ok", "version": API_VERSION})


def create_app() -> FastAPI:
    """Build the FastAPI application. Never connects to the database itself."""
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        # Prototype bootstrapping only; tests create/drop their own schema and
        # production migration tooling is a documented follow-on (design §11).
        if settings.env != "test":
            try:
                create_all()
            except Exception:  # pragma: no cover - surfaced at deploy time
                logger.exception("Schema bootstrap failed")
        logger.info("APAAR-SDMV API %s starting (env=%s)", API_VERSION, settings.env)
        yield
        logger.info("APAAR-SDMV API stopped")

    app = FastAPI(
        title="APAAR-SDMV API",
        description=(
            "Student Data Management & Verification Platform prototype. "
            "Synthetic data only; all external integrations are mock/sandbox."
        ),
        version=API_VERSION,
        lifespan=lifespan,
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", TRACE_ID_HEADER],
            expose_headers=[TRACE_ID_HEADER],
        )

    app.add_middleware(RequestContextMiddleware)

    app.get("/api/v1/health", include_in_schema=True)(health)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(institutions.router, prefix="/api/v1")
    app.include_router(programmes.router, prefix="/api/v1")
    app.include_router(enrollments.router, prefix="/api/v1")
    app.include_router(batches.router, prefix="/api/v1")
    app.include_router(batches.template_router, prefix="/api/v1")
    app.include_router(cases.router, prefix="/api/v1")
    app.include_router(dashboards.router, prefix="/api/v1")
    app.include_router(review.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")
    app.include_router(notifications.router, prefix="/api/v1")
    app.include_router(audit.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")
    app.include_router(verification.router, prefix="/api/v1")
    app.include_router(verification.public_router, prefix="/api/v1")
    app.include_router(student.router, prefix="/api/v1")

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        body = _error_body(request, exc.code, exc.message, exc.details)
        return JSONResponse(body, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = _json_safe(exc.errors())
        for err in details:
            err.pop("url", None)  # Swagger validator URL noise; keep payload small
        body = _error_body(request, "VALIDATION_ERROR", "Request payload is invalid", details)
        return JSONResponse(body, status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        body = _error_body(request, "HTTP_ERROR", str(exc.detail), exc.headers)
        return JSONResponse(body, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Log the real cause; the client never sees internal details.
        logger.exception("Unhandled error: %s", exc)
        body = _error_body(request, "INTERNAL_ERROR", "Unexpected server error")
        return JSONResponse(body, status_code=500)

    return app


app = create_app()
