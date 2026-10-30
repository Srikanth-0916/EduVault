"""Consent, third-party verification requests, receipts, and attempts.

Tables: ``consent_grants``, ``verification_requests``, ``verification_receipts``,
``verification_attempts``.

Token posture (design §7): opaque 32-byte URL-safe tokens are shown once and
stored only as SHA-256 hashes plus a JWT ``jti``; expiry and revocation are
checked server-side; denials are generic; every attempt is logged with no raw
token or student data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pk, sa_enum, utc_now, uuid_fk
from app.models.enums import (
    AttemptDenialReason,
    AttemptOutcome,
    ConsentStatus,
    LegalBasis,
    VerificationRequestStatus,
)


class ConsentGrant(TimestampMixin, Base):
    """A student's purpose-bound consent to share specific claims.

    Tied to one verification request (when applicable); describes recipient,
    purpose, field scope and the notice version shown at consent time.
    """

    __tablename__ = "consent_grants"

    id: Mapped[str] = pk()
    subject_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), default=None, index=True
    )
    student_identity_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("student_identities.id"), default=None, index=True
    )
    verification_request_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("verification_requests.id"), default=None, index=True
    )
    recipient_name: Mapped[str] = mapped_column(String(255))
    recipient_org: Mapped[str] = mapped_column(String(255))
    recipient_email: Mapped[str] = mapped_column(String(255))
    purpose: Mapped[str] = mapped_column(String(512))
    fields_scope: Mapped[dict[str, Any]] = mapped_column(JSON)  # list of claim keys
    legal_basis: Mapped[str] = mapped_column(sa_enum(LegalBasis))
    notice_version: Mapped[str] = mapped_column(String(32), default="2026-1")
    single_use: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(sa_enum(ConsentStatus), default=ConsentStatus.ACTIVE.value)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class VerificationRequest(TimestampMixin, Base):
    """A controlled third-party verification, optionally consent-scoped.

    Lifecycle: ``PENDING_AUTHORIZATION`` → ``AUTHORIZED`` → (``VIEWED`` |
    ``CONSUMED``) → (``EXPIRED`` | ``REVOKED``). The token itself is never
    stored; only its SHA-256 hash and JTI.
    """

    __tablename__ = "verification_requests"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_verification_requests_token_hash"),
        UniqueConstraint("token_jti", name="uq_verification_requests_token_jti"),
    )

    id: Mapped[str] = pk()
    subject_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), default=None, index=True
    )
    student_identity_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("student_identities.id"), default=None, index=True
    )
    created_by: Mapped[str | None] = mapped_column(String(36), default=None)
    # Requester (verifying organisation) details for the disclosure screen.
    recipient_name: Mapped[str] = mapped_column(String(255))
    recipient_org: Mapped[str] = mapped_column(String(255))
    recipient_email: Mapped[str] = mapped_column(String(255))
    purpose: Mapped[str] = mapped_column(String(512))
    requested_claims: Mapped[dict[str, Any]] = mapped_column(JSON)  # list of claim keys
    legal_basis: Mapped[str] = mapped_column(sa_enum(LegalBasis))
    expires_in_hours: Mapped[int] = mapped_column(Integer, default=24)
    status: Mapped[str] = mapped_column(
        sa_enum(VerificationRequestStatus),
        default=VerificationRequestStatus.PENDING_AUTHORIZATION.value,
    )
    single_use: Mapped[bool] = mapped_column(Boolean, default=False)
    # Link (token) material — hashed at rest only.
    token_hash: Mapped[str | None] = mapped_column(String(64), default=None, index=True)
    token_jti: Mapped[str | None] = mapped_column(String(64), default=None)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    revoked_reason: Mapped[str | None] = mapped_column(String(512), default=None)


class VerificationReceipt(Base):
    """HMAC-signed canonical JSON proof of what was disclosed and when."""

    __tablename__ = "verification_receipts"

    id: Mapped[str] = pk()
    verification_request_id: Mapped[str] = uuid_fk("verification_requests.id", index=True)
    claims_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    signature: Mapped[str] = mapped_column(String(512))
    key_id: Mapped[str] = mapped_column(String(64), default="primary")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class VerificationAttempt(Base):
    """Every resolution attempt against a verification token (success/denial)."""

    __tablename__ = "verification_attempts"

    id: Mapped[str] = pk()
    verification_request_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("verification_requests.id"), default=None, index=True
    )
    outcome: Mapped[str] = mapped_column(sa_enum(AttemptOutcome))
    denial_reason: Mapped[str | None] = mapped_column(sa_enum(AttemptDenialReason))
    claims_disclosed: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    # Request metadata, retained without any identifier values.
    ip_address: Mapped[str | None] = mapped_column(String(64), default=None)
    user_agent: Mapped[str | None] = mapped_column(String(512), default=None)
    trace_id: Mapped[str | None] = mapped_column(String(64), default=None)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    receipt_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("verification_receipts.id"), default=None
    )
