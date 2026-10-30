"""Human review artefacts: duplicate cases and identity verifications.

Tables: ``duplicate_cases``, ``identity_verifications``.

Duplicate matches create review cases; they never auto-cancel, auto-merge, or
label fraud (plan constraints). Identity verifications are the evidence trail
of mock APAAR checks (adapter result, never mutation to a live-verified state).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pk, sa_enum, uuid_fk
from app.models.enums import (
    ApaarProviderOutcome,
    CaseResolutionCode,
    DuplicateCaseStatus,
    DuplicateMatchType,
    IdentityStatus,
    Severity,
)


class DuplicateCase(TimestampMixin, Base):
    """A duplicate identity/enrolment conflict awaiting human review.

    Idempotent per ``match_group_id``: re-validation against the same match
    updates the case instead of opening a new one.
    """

    __tablename__ = "duplicate_cases"

    id: Mapped[str] = pk()
    match_group_id: Mapped[str] = mapped_column(String(64), index=True)
    match_type: Mapped[str] = mapped_column(sa_enum(DuplicateMatchType))
    severity: Mapped[str] = mapped_column(sa_enum(Severity))
    status: Mapped[str] = mapped_column(
        sa_enum(DuplicateCaseStatus), default=DuplicateCaseStatus.OPEN.value
    )
    # The conflicting records (at least one side is always present).
    primary_enrollment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("student_enrollments.id"), default=None, index=True
    )
    related_enrollment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("student_enrollments.id"), default=None, index=True
    )
    institution_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("institutions.id"), default=None, index=True
    )
    discovered_batch_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("submission_batches.id"), default=None
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    assigned_reviewer_id: Mapped[str | None] = mapped_column(String(36), default=None)
    resolution_code: Mapped[str | None] = mapped_column(sa_enum(CaseResolutionCode))
    resolution_reason: Mapped[str | None] = mapped_column(String(1024), default=None)
    resolved_by: Mapped[str | None] = mapped_column(String(36), default=None)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    # Evidence echoes masked identifiers and dates only; never raw APAAR.
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)


class IdentityVerification(TimestampMixin, Base):
    """Evidence of one external APAAR check executed through an adapter."""

    __tablename__ = "identity_verifications"

    id: Mapped[str] = pk()
    student_identity_id: Mapped[str] = uuid_fk("student_identities.id", index=True)
    # e.g. MOCK_APAAR; always mock-labelled in the prototype.
    provider: Mapped[str] = mapped_column(String(64))
    provider_reference: Mapped[str | None] = mapped_column(String(128), default=None)
    result: Mapped[str] = mapped_column(sa_enum(ApaarProviderOutcome))
    adapter_version: Mapped[str] = mapped_column(String(32), default="mock-1.0")
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    purpose: Mapped[str | None] = mapped_column(String(128), default=None)
    consent_context: Mapped[str | None] = mapped_column(String(255), default=None)
    requested_by: Mapped[str | None] = mapped_column(String(36), default=None)
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    # Status the identity moved into as a consequence (never "live verified").
    resulting_status: Mapped[str | None] = mapped_column(sa_enum(IdentityStatus))
