"""Enrollment API schemas; APAAR values are write-only."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import CamelModel
from app.schemas.identity import IdentityVerificationOut


class FindingOut(CamelModel):
    id: str
    rule_id: str
    code: str
    severity: str
    blocking: bool
    message: str
    field: str | None = None
    status: str
    evidence: dict[str, object] | None = None
    row_id: str | None = None


class EnrollmentCreate(CamelModel):
    student_local_id: str = Field(min_length=1, max_length=128)
    student_full_name: str = Field(min_length=2, max_length=255)
    apaar_id: str | None = Field(default=None, max_length=32)
    programme_id: str
    campus_id: str | None = None
    academic_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    admission_date: date
    exit_date: date | None = None
    enrollment_status: Literal[
        "PENDING", "ACTIVE", "WITHDRAWN", "TRANSFERRED", "COMPLETED", "CANCELLED", "UNDER_REVIEW"
    ] = "PENDING"
    seat_classification: Literal["APPROVED_REGULAR", "APPROVED_SUPERNUMERARY", "OTHER"] = (
        "APPROVED_REGULAR"
    )
    admission_category: str | None = Field(default=None, max_length=64)
    nri_status: Literal["YES", "NO", "UNKNOWN"] = "UNKNOWN"
    oci_status: Literal["YES", "NO", "UNKNOWN"] = "UNKNOWN"
    foreign_national_status: Literal["YES", "NO", "UNKNOWN"] = "UNKNOWN"
    supernumerary_approval_reference: str | None = Field(default=None, max_length=128)


class EnrollmentPatch(CamelModel):
    student_local_id: str | None = Field(default=None, min_length=1, max_length=128)
    student_full_name: str | None = Field(default=None, min_length=2, max_length=255)
    apaar_id: str | None = Field(default=None, max_length=32)
    programme_id: str | None = None
    campus_id: str | None = None
    academic_year: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    admission_date: date | None = None
    exit_date: date | None = None
    enrollment_status: str | None = None
    seat_classification: str | None = None
    admission_category: str | None = None
    nri_status: str | None = None
    oci_status: str | None = None
    foreign_national_status: str | None = None
    supernumerary_approval_reference: str | None = None
    reason: str = Field(min_length=3, max_length=512)


class EnrollmentVersionOut(CamelModel):
    id: str
    version: int
    snapshot: dict[str, object]
    change_reason: str | None = None
    changed_by: str | None = None
    actor_role: str | None = None
    created_at: datetime


class EnrollmentSummary(CamelModel):
    id: str
    institution_id: str
    institution_name: str | None = None
    campus_id: str | None = None
    campus_name: str | None = None
    programme_id: str
    programme_name: str | None = None
    student_local_id: str
    student_full_name: str
    masked_apaar: str
    identity_status: str | None = None
    academic_year: str
    admission_date: date
    exit_date: date | None = None
    enrollment_status: str
    seat_classification: str
    admission_category: str | None = None
    nri_status: str = "UNKNOWN"
    oci_status: str = "UNKNOWN"
    foreign_national_status: str = "UNKNOWN"
    version: int
    is_current: bool
    record_accepted_at: datetime | None = None
    updated_at: datetime | None = None


class EnrollmentDetail(EnrollmentSummary):
    supernumerary_approval_reference: str | None = None
    versions: list[EnrollmentVersionOut] = Field(default_factory=list)
    verifications: list[IdentityVerificationOut] = Field(default_factory=list)
    findings: list[FindingOut] = Field(default_factory=list)


class IdentityVerifyResponse(CamelModel):
    identity_status: str
    verification: IdentityVerificationOut
