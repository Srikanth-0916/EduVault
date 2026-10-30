"""Hardening middleware: in-process rate limits and log redaction.

The prototype uses a small sliding-window limiter keyed by client IP and route
bucket. It is deliberately process-local; production should replace it with a
shared Redis-backed limiter (documented in ``docs/security.md``).

Redaction is defence-in-depth: application code never logs raw APAAR values or
bearer tokens, and this filter scrubs accidental leaks from message text and
arguments before records reach a handler.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from collections import deque
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

TRACE_ID_HEADER = "X-Request-Id"

APAAR_PATTERN = re.compile(r"\b\d{12}\b")
BEARER_PATTERN = re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]+")
SECRET_FIELD_PATTERN = re.compile(
    r"(?i)([\"']?(?:password|token|access_token|refresh_token|apaar_id|apaarId|"
    r"jwt_secret|encryption_key)[\"']?\s*[:=]\s*)([\"']?)([^\"',}\s]+)"
)
REDACTED_APAAR = "[APAAR_REDACTED]"
REDACTED_TOKEN = r"\1 [TOKEN_REDACTED]"
REDACTED_FIELD = r"\1\2[REDACTED]"


def redact_text(value: str) -> str:
    """Redact APAAR-shaped digits, bearer tokens and sensitive key/value pairs."""
    value = APAAR_PATTERN.sub(REDACTED_APAAR, value)
    value = BEARER_PATTERN.sub(REDACTED_TOKEN, value)
    return SECRET_FIELD_PATTERN.sub(REDACTED_FIELD, value)


def _redact_value(value: object) -> object:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if str(key).lower()
            in {
                "password",
                "token",
                "access_token",
                "refresh_token",
                "apaar_id",
                "apaarid",
                "jwt_secret",
                "encryption_key",
            }
            else _redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value


class RedactSensitiveFilter(logging.Filter):
    """Scrub secrets from log messages and structured arguments."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact_text(record.msg)
            if record.args:
                record.args = _redact_value(record.args)
        except Exception:  # pragma: no cover - logging must never break a request
            return True
        return True


def install_log_redaction() -> None:
    """Attach the redaction filter once to root and uvicorn/app loggers."""
    redaction = RedactSensitiveFilter()
    loggers = [logging.getLogger()]
    loggers.extend(
        logging.getLogger(name) for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "app")
    )
    for logger in loggers:
        if not any(isinstance(item, RedactSensitiveFilter) for item in logger.filters):
            logger.addFilter(redaction)
        for handler in logger.handlers:
            if not any(isinstance(item, RedactSensitiveFilter) for item in handler.filters):
                handler.addFilter(redaction)


@dataclass(frozen=True)
class RateRule:
    method: str
    path_prefix: str
    limit: int
    window_seconds: int = 60


RATE_RULES: tuple[RateRule, ...] = (
    RateRule("POST", "/api/v1/auth/login", 10),
    RateRule("GET", "/api/v1/public/verify/", 30),
)


class SlidingWindowLimiter:
    """Thread-safe per-key sliding-window counter."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> int:
        """Record one attempt and return 0 when allowed or Retry-After seconds."""
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                return max(1, int(window_seconds - (now - events[0])) + 1)
            events.append(now)
            return 0

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


_LIMITER = SlidingWindowLimiter()


def reset_rate_limits() -> None:
    """Clear limiter state (tests and local operator tooling)."""
    _LIMITER.reset()


def _rule_for(request: Request) -> RateRule | None:
    for rule in RATE_RULES:
        if request.method == rule.method and request.url.path.startswith(rule.path_prefix):
            return rule
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Return 429 with ``Retry-After`` for configured sensitive endpoints."""

    async def dispatch(self, request: Request, call_next):
        rule = _rule_for(request)
        if rule is not None:
            client = request.client.host if request.client else "unknown"
            retry_after = _LIMITER.hit(
                f"{client}:{rule.method}:{rule.path_prefix}",
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )
            if retry_after:
                trace_id = getattr(request.state, "trace_id", None) or "trc_rate_limited"
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMITED",
                            "message": "Too many requests. Try again later.",
                            "details": None,
                        },
                        "traceId": trace_id,
                    },
                    headers={"Retry-After": str(retry_after)},
                )
        return await call_next(request)
