"""Purpose-bound consent and public verification schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import EmailStr, Field, field_validator

from app.models.enums import VerificationClaim
from app.schemas.common import CamelModel


class VerificationRequestCreate(CamelModel):
    recipient_name: str = Field(min_length=2, max_length=255)
    recipient_org: str = Field(min_length=2, max_length=255)
    recipient_email: EmailStr
    purpose: str = Field(min_length=5, max_length=512)
    requested_claims: list[str] = Field(min_length=1, max_length=8)
    legal_basis: Literal["CONSENT", "STATUTORY_AUTHORITY", "CONTRACT", "LEGITIMATE_INTEREST"] = (
        "CONSENT"
    )
    expires_in_hours: int = Field(ge=1, le=168)
    single_use: bool = False

    @field_validator("requested_claims")
    @classmethod
    def claims_allow_list(cls, values: list[str]) -> list[str]:
        allowed = {item.value for item in VerificationClaim}
        if len(set(values)) != len(values) or any(item not in allowed for item in values):
            raise ValueError("requestedClaims contains an unsupported claim")
        return values


class VerificationRequestOut(CamelModel):
    id: str
    recipient_name: str
    recipient_org: str
    recipient_email: str
    purpose: str
    requested_claims: list[str]
    legal_basis: str
    expires_in_hours: int
    status: str
    single_use: bool
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    viewed_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    created_at: datetime


class VerificationRequestListResponse(CamelModel):
    items: list[VerificationRequestOut]
    total: int


class VerificationReceiptOut(CamelModel):
    id: str
    payload: dict[str, Any]
    signature: str
    algorithm: str = "HMAC-SHA256"
    key_id: str
    issued_at: datetime
    expires_at: datetime


class AuthorizeResponse(CamelModel):
    request: VerificationRequestOut
    token: str
    verify_url: str
    expires_at: datetime
    receipt: VerificationReceiptOut


class RevokeRequest(CamelModel):
    reason: str = Field(min_length=3, max_length=512)


class VerificationClaimOut(CamelModel):
    key: str
    label: str
    value: str
    source: str
    status: str
    as_of: datetime | None = None


class PublicVerificationResponse(CamelModel):
    valid: bool
    claims: list[VerificationClaimOut] = Field(default_factory=list)
    receipt: VerificationReceiptOut | None = None
    expires_at: datetime | None = None
    demo_notice: str


class StudentMeResponse(CamelModel):
    masked_apaar: str
    identity_status: str
    identity_last4: str | None = None
    enrollments: list[dict[str, Any]] = Field(default_factory=list)
    verification_requests: list[VerificationRequestOut] = Field(default_factory=list)
