"""Submission batch lifecycle, rows, and validation artefacts.

Tables: ``submission_batches``, ``submission_rows``, ``validation_runs``,
``validation_findings``.

Invariants (design §5.2):

- batch statuses follow the canonical workflow (enums.BatchStatus);
- rows are never committed as accepted enrollments until nodal attestation and
  submission; AICTE acceptance is a separate decision;
- finding evidence must hold masked identifiers only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pk, sa_enum, uuid_fk
from app.models.enums import (
    BatchSourceType,
    BatchStatus,
    FindingStatus,
    RowStatus,
    Severity,
    ValidationRunStatus,
)


class SubmissionBatch(TimestampMixin, Base):
    """A batch of student rows submitted by an institution for review."""

    __tablename__ = "submission_batches"
    __table_args__ = (
        Index("ix_submission_batches_institution_year", "institution_id", "academic_year"),
        Index("ix_submission_batches_institution_status", "institution_id", "status"),
    )

    id: Mapped[str] = pk()
    institution_id: Mapped[str] = uuid_fk("institutions.id", index=True)
    campus_id: Mapped[str | None] = uuid_fk("campuses.id", nullable=True, index=True)
    programme_id: Mapped[str | None] = uuid_fk("programmes.id", nullable=True, index=True)
    academic_year: Mapped[str] = mapped_column(String(16), index=True)
    source_type: Mapped[str] = mapped_column(sa_enum(BatchSourceType))
    status: Mapped[str] = mapped_column(sa_enum(BatchStatus), default=BatchStatus.DRAFT.value)
    # Resubmission after RETURNED_FOR_CORRECTION creates a new version.
    version: Mapped[int] = mapped_column(Integer, default=1)
    supersedes_batch_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("submission_batches.id"), default=None
    )
    # Uploaded file provenance (stored privately under var/storage).
    file_name: Mapped[str | None] = mapped_column(String(512), default=None)
    file_storage_key: Mapped[str | None] = mapped_column(String(512), default=None)
    file_checksum: Mapped[str | None] = mapped_column(String(64), default=None)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, default=None)
    row_count: Mapped[int | None] = mapped_column(Integer, default=None)
    # Attestation (INSTITUTION_NODAL_OFFICER).
    attested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    attested_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), default=None
    )
    attestation_name: Mapped[str | None] = mapped_column(String(255), default=None)
    declaration_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    # Submission.
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    submitted_by: Mapped[str | None] = mapped_column(String(36), default=None)
    # AICTE decision.
    decision: Mapped[str | None] = mapped_column(String(16), default=None)
    decision_reason: Mapped[str | None] = mapped_column(String(1024), default=None)
    decision_reason_code: Mapped[str | None] = mapped_column(String(48), default=None)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    decided_by: Mapped[str | None] = mapped_column(String(36), default=None)
    assigned_reviewer_id: Mapped[str | None] = mapped_column(String(36), default=None)
    decision_history: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))


class SubmissionRow(TimestampMixin, Base):
    """One raw CSV row staged within a batch, with its parsed outcome."""

    __tablename__ = "submission_rows"

    id: Mapped[str] = pk()
    batch_id: Mapped[str] = uuid_fk("submission_batches.id", index=True)
    source_row_number: Mapped[int] = mapped_column(Integer)
    student_name: Mapped[str | None] = mapped_column(String(255), default=None)
    student_local_id: Mapped[str | None] = mapped_column(String(128), default=None)
    apaar_last4: Mapped[str | None] = mapped_column(String(4), default=None)
    student_identity_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("student_identities.id"), default=None
    )
    enrollment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("student_enrollments.id", use_alter=True), default=None
    )
    row_status: Mapped[str] = mapped_column(sa_enum(RowStatus), default=RowStatus.PENDING.value)
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON)
    parsed_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)


class ValidationRun(TimestampMixin, Base):
    """A reproducible validation execution over one batch."""

    __tablename__ = "validation_runs"

    id: Mapped[str] = pk()
    batch_id: Mapped[str] = uuid_fk("submission_batches.id", index=True)
    rule_set_version: Mapped[str] = mapped_column(String(32), default="2026.1")
    status: Mapped[str] = mapped_column(
        sa_enum(ValidationRunStatus), default=ValidationRunStatus.RUNNING.value
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    requested_by: Mapped[str | None] = mapped_column(String(36), default=None)
    duration_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)


class ValidationFinding(TimestampMixin, Base):
    """One rule outcome for one record, with evidence (masked values only)."""

    __tablename__ = "validation_findings"

    id: Mapped[str] = pk()
    validation_run_id: Mapped[str] = uuid_fk("validation_runs.id", index=True)
    batch_id: Mapped[str] = uuid_fk("submission_batches.id", index=True)
    row_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("submission_rows.id"), default=None
    )
    record_id: Mapped[str | None] = mapped_column(String(36), default=None)
    rule_id: Mapped[str] = mapped_column(String(16), index=True)  # e.g. BR-002
    code: Mapped[str] = mapped_column(String(64))  # e.g. APAAR_INVALID_FORMAT
    severity: Mapped[str] = mapped_column(sa_enum(Severity))
    blocking: Mapped[bool] = mapped_column(Boolean, default=False)
    message: Mapped[str] = mapped_column(String(1024))
    field: Mapped[str | None] = mapped_column(String(64), default=None)
    status: Mapped[str] = mapped_column(sa_enum(FindingStatus), default=FindingStatus.OPEN.value)
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
