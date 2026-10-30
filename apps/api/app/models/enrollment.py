"""Student enrolments and their immutable version history.

Tables: ``student_enrollments``, ``enrollment_versions``.

Invariants (design §5.2):

- every accepted change writes an ``EnrollmentVersion`` snapshot;
- the current record carries ``version``/``is_current``/``supersedes_id``;
- prior versions remain readable for audit/review roles only.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pk, sa_enum, utc_now, uuid_fk
from app.models.enums import DeclaredStatus, EnrollmentStatus, SeatClassification


class StudentEnrollment(TimestampMixin, Base):
    """A student's enrolment at one institution/campus/programme.

    A row is "current" for its identity+institution+programme+academic-year
    window when ``is_current`` is true. Corrections create a new row that
    supersedes the previous one; the superseded row keeps ``is_current=False``.
    """

    __tablename__ = "student_enrollments"
    __table_args__ = (
        Index(
            "ix_student_enrollments_current_window",
            "student_identity_id",
            "institution_id",
            "programme_id",
            "academic_year",
            "is_current",
        ),
        # The institutional student ID is unique among *current* records for the
        # institution/year namespace. Superseded versions keep proven history and
        # must not block a correction.
        Index(
            "uq_student_enrollments_current_local_id",
            "institution_id",
            "student_local_id",
            "academic_year",
            unique=True,
            sqlite_where=text("is_current = 1"),
            postgresql_where=text("is_current = true"),
        ),
    )

    id: Mapped[str] = pk()
    student_identity_id: Mapped[str] = uuid_fk("student_identities.id", index=True)
    institution_id: Mapped[str] = uuid_fk("institutions.id", index=True)
    campus_id: Mapped[str | None] = uuid_fk("campuses.id", index=True)
    programme_id: Mapped[str] = uuid_fk("programmes.id", index=True)
    student_local_id: Mapped[str] = mapped_column(String(128))
    student_full_name: Mapped[str] = mapped_column(String(255))
    academic_year: Mapped[str] = mapped_column(String(16), index=True)
    admission_date: Mapped[date] = mapped_column(Date)
    exit_date: Mapped[date | None] = mapped_column(Date, default=None)
    enrollment_status: Mapped[str] = mapped_column(
        sa_enum(EnrollmentStatus), default=EnrollmentStatus.PENDING.value
    )
    seat_classification: Mapped[str] = mapped_column(
        sa_enum(SeatClassification), default=SeatClassification.APPROVED_REGULAR.value
    )
    admission_category: Mapped[str | None] = mapped_column(String(64), default=None)
    # Tri-state attributes (YES/NO/UNKNOWN): blank never means false.
    nri_status: Mapped[str] = mapped_column(
        sa_enum(DeclaredStatus), default=DeclaredStatus.UNKNOWN.value
    )
    oci_status: Mapped[str] = mapped_column(
        sa_enum(DeclaredStatus), default=DeclaredStatus.UNKNOWN.value
    )
    foreign_national_status: Mapped[str] = mapped_column(
        sa_enum(DeclaredStatus), default=DeclaredStatus.UNKNOWN.value
    )
    supernumerary_approval_reference: Mapped[str | None] = mapped_column(String(128), default=None)
    # Version chain (design §5.2).
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    supersedes_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("student_enrollments.id"), default=None
    )
    correction_reason: Mapped[str | None] = mapped_column(String(512), default=None)
    # Provenance.
    source_channel: Mapped[str] = mapped_column(String(32), default="PORTAL")
    source_batch_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("submission_batches.id"), default=None
    )
    source_row_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("submission_rows.id", use_alter=True), default=None
    )
    created_by: Mapped[str | None] = mapped_column(String(36), default=None)
    updated_by: Mapped[str | None] = mapped_column(String(36), default=None)
    record_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class EnrollmentVersion(Base):
    """Immutable snapshot of an enrollment state at a point in time."""

    __tablename__ = "enrollment_versions"

    id: Mapped[str] = pk()
    student_enrollment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_enrollments.id"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    change_reason: Mapped[str | None] = mapped_column(String(512), default=None)
    changed_by: Mapped[str | None] = mapped_column(String(36), default=None)
    actor_role: Mapped[str | None] = mapped_column(String(64), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
