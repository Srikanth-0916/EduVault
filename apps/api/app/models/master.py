"""Master data, users, and organizational membership.

Tables: ``institutions``, ``campuses``, ``programmes``, ``approval_snapshots``,
``intake_allocations``, ``users``, ``organization_memberships``.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pk, sa_enum, uuid_fk
from app.models.enums import (
    ApprovalSnapshotStatus,
    AwardLevel,
    InstitutionStatus,
    InstitutionType,
    MembershipScope,
    RecordStatus,
    SeatClassification,
    UserRole,
    UserStatus,
)


class Institution(TimestampMixin, Base):
    """Institution master record (managed by AICTE roles)."""

    __tablename__ = "institutions"

    id: Mapped[str] = pk()
    aicte_institution_code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    institution_type: Mapped[str] = mapped_column(sa_enum(InstitutionType))
    status: Mapped[str] = mapped_column(
        sa_enum(InstitutionStatus), default=InstitutionStatus.ACTIVE.value
    )
    state: Mapped[str | None] = mapped_column(String(128), default=None)
    city: Mapped[str | None] = mapped_column(String(128), default=None)
    website_url: Mapped[str | None] = mapped_column(String(512), default=None)
    contact_email: Mapped[str | None] = mapped_column(String(255), default=None)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Institution {self.aicte_institution_code!r} {self.name!r}>"


class Campus(TimestampMixin, Base):
    """Campus within an institution; approval and programme scope."""

    __tablename__ = "campuses"
    __table_args__ = (UniqueConstraint("institution_id", "campus_code"),)

    id: Mapped[str] = pk()
    institution_id: Mapped[str] = uuid_fk("institutions.id")
    campus_code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255), default=None)
    status: Mapped[str] = mapped_column(sa_enum(RecordStatus), default=RecordStatus.ACTIVE.value)


class Programme(TimestampMixin, Base):
    """Approved programme run by a campus of an institution."""

    __tablename__ = "programmes"
    __table_args__ = (UniqueConstraint("campus_id", "programme_code"),)

    id: Mapped[str] = pk()
    institution_id: Mapped[str] = uuid_fk("institutions.id")
    campus_id: Mapped[str] = uuid_fk("campuses.id")
    programme_code: Mapped[str] = mapped_column(String(32))
    programme_name: Mapped[str] = mapped_column(String(255))
    award_level: Mapped[str] = mapped_column(sa_enum(AwardLevel))
    duration_years: Mapped[int] = mapped_column(Integer, default=4)
    status: Mapped[str] = mapped_column(sa_enum(RecordStatus), default=RecordStatus.ACTIVE.value)


class ApprovalSnapshot(TimestampMixin, Base):
    """Versioned authoritative approval/intake snapshot per programme year."""

    __tablename__ = "approval_snapshots"
    __table_args__ = (UniqueConstraint("programme_id", "academic_year", "version"),)

    id: Mapped[str] = pk()
    programme_id: Mapped[str] = uuid_fk("programmes.id", index=True)
    academic_year: Mapped[str] = mapped_column(String(16), index=True)
    approval_reference: Mapped[str] = mapped_column(String(128))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date, default=None)
    issued_by: Mapped[str | None] = mapped_column(String(255), default=None)
    notes: Mapped[str | None] = mapped_column(String(1024), default=None)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(
        sa_enum(ApprovalSnapshotStatus), default=ApprovalSnapshotStatus.ACTIVE.value
    )


class IntakeAllocation(TimestampMixin, Base):
    """Approved seat count for one seat classification under a snapshot.

    Regular and supernumerary allocations are separate rows; supernumerary
    requires an ``authorization_reference`` (design §5.4 BR-009).
    """

    __tablename__ = "intake_allocations"

    id: Mapped[str] = pk()
    approval_snapshot_id: Mapped[str] = uuid_fk("approval_snapshots.id", index=True)
    seat_classification: Mapped[str] = mapped_column(sa_enum(SeatClassification))
    approved_count: Mapped[int] = mapped_column(Integer, default=0)
    authorization_reference: Mapped[str | None] = mapped_column(String(128), default=None)


class User(TimestampMixin, Base):
    """Platform user; roles are granted through organization memberships."""

    __tablename__ = "users"

    id: Mapped[str] = pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(String(512), default=None)
    status: Mapped[str] = mapped_column(sa_enum(UserStatus), default=UserStatus.ACTIVE.value)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255), default=None)
    phone: Mapped[str | None] = mapped_column(String(32), default=None)
    student_identity_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("student_identities.id"), default=None, index=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class OrganizationMembership(TimestampMixin, Base):
    """Role mapping for a user, optionally scoped to an institution."""

    __tablename__ = "organization_memberships"

    id: Mapped[str] = pk()
    user_id: Mapped[str] = uuid_fk("users.id", index=True)
    institution_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("institutions.id"), default=None, index=True
    )
    role: Mapped[str] = mapped_column(sa_enum(UserRole))
    scope: Mapped[str] = mapped_column(
        sa_enum(MembershipScope), default=MembershipScope.INSTITUTION.value
    )
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_by: Mapped[str | None] = mapped_column(String(36), default=None)
