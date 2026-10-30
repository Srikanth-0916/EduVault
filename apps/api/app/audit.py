"""Append-only audit helper.

Every material action goes through :func:`record_audit`. The helper masks
sensitive values defensively even if a caller accidentally passes one: raw
APAAR-shaped 12-digit sequences, passwords, tokens, and secrets never reach the
audit table.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.base import utc_now
from app.models.enums import AuditOutcome
from app.models.ops import AuditEvent

_REDACT_KEYS = {
    "apaar",
    "apaar_id",
    "apaarid",
    "password",
    "password_hash",
    "hashed_password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "secret",
    "api_key",
    "mfa_secret",
}
_APAAR_SHAPE = re.compile(r"\b\d{12}\b")
_MAX_DEPTH = 4
_MAX_ITEMS = 100


def _mask_string(value: str) -> str:
    def _mask(match: re.Match[str]) -> str:
        digits = match.group(0)
        return f"••••••••{digits[-4:]}"

    return _APAAR_SHAPE.sub(_mask, value)


def sanitize_metadata(value: Any, *, _depth: int = 0) -> Any:
    """Recursively redact keys and mask APAAR-shaped strings."""
    if _depth > _MAX_DEPTH:
        return "[TRUNCATED]"
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= _MAX_ITEMS:
                cleaned["_truncated"] = True
                break
            text_key = str(key)
            if text_key.lower().replace("-", "_") in _REDACT_KEYS:
                cleaned[text_key] = "[REDACTED]"
            else:
                cleaned[text_key] = sanitize_metadata(item, _depth=_depth + 1)
        return cleaned
    if isinstance(value, (list, tuple)):
        return [sanitize_metadata(item, _depth=_depth + 1) for item in value[:_MAX_ITEMS]]
    if isinstance(value, str):
        return _mask_string(value)[:2048]
    return value


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return request.client.host[:64] if request.client else None


def record_audit(
    db: Session,
    *,
    action: str,
    resource_type: str,
    actor: Any = None,
    actor_email: str | None = None,
    resource_ref: str | None = None,
    outcome: str | AuditOutcome = AuditOutcome.SUCCESS,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
    institution_id: str | None = None,
    request: Request | None = None,
    commit: bool = False,
) -> AuditEvent:
    """Add one audit event. Caller commits unless ``commit=True``.

    ``commit=True`` is used for denied/security events so the evidence survives
    the request's rollback path.
    """
    actor_id = getattr(actor, "id", None)
    email = actor_email or getattr(actor, "email", None)
    role = getattr(actor, "primary_role", None)
    actor_institution = getattr(actor, "institution_id", None)
    trace_id = None
    ip_address = None
    user_agent = None
    if request is not None:
        trace_id = getattr(request.state, "trace_id", None)
        ip_address = _client_ip(request)
        user_agent = request.headers.get("user-agent", "")[:512] or None

    event = AuditEvent(
        actor_id=str(actor_id) if actor_id else None,
        actor_email=str(email)[:255] if email else None,
        actor_role=str(role)[:64] if role else None,
        action=action[:96],
        outcome=(
            outcome.value if isinstance(outcome, AuditOutcome) else str(outcome)
        )[:32],
        resource_type=resource_type[:64],
        resource_ref=resource_ref[:128] if resource_ref else None,
        institution_id=institution_id or actor_institution,
        reason=reason[:1024] if reason else None,
        metadata_=sanitize_metadata(metadata) if metadata else None,
        ip_address=ip_address,
        user_agent=user_agent,
        trace_id=trace_id,
        timestamp=utc_now(),
    )
    db.add(event)
    if commit:
        db.commit()
    else:
        db.flush()
    return event
