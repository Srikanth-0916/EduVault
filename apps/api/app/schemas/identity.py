"""Protected identity API shapes. Raw APAAR values are never response fields."""

from __future__ import annotations

from datetime import datetime

from app.schemas.common import CamelModel


class IdentitySummary(CamelModel):
    id: str
    masked_apaar: str
    apaar_last4: str | None = None
    status: str
    key_id: str | None = None
    verification_reference: str | None = None
    updated_at: datetime | None = None


class IdentityVerificationOut(CamelModel):
    id: str
    provider: str
    provider_reference: str | None = None
    result: str
    adapter_version: str
    is_mock: bool
    checked_at: datetime
    purpose: str | None = None
    consent_context: str | None = None
    resulting_status: str | None = None
    detail: dict[str, object] | None = None
