"""Master data and approved-intake API schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import CamelModel


class InstitutionOut(CamelModel):
    id: str
    aicte_institution_code: str
    name: str
    institution_type: str
    status: str
    state: str | None = None
    city: str | None = None
    website_url: str | None = None
    contact_email: str | None = None
    campus_count: int = 0
    programme_count: int = 0


class CampusOut(CamelModel):
    id: str
    institution_id: str
    campus_code: str
    name: str
    location: str | None = None
    status: str


class ProgrammeOut(CamelModel):
    id: str
    institution_id: str
    campus_id: str
    programme_code: str
    programme_name: str
    award_level: str
    duration_years: int
    status: str
    campus_name: str | None = None
    institution_name: str | None = None
    approved_regular: int = 0
    approved_supernumerary: int = 0
    reported_regular: int = 0
    reported_supernumerary: int = 0
    capacity_status: str | None = None
    approval_reference: str | None = None


class InstitutionDetail(InstitutionOut):
    campuses: list[CampusOut] = Field(default_factory=list)
    programmes: list[ProgrammeOut] = Field(default_factory=list)


class IntakeAllocationOut(CamelModel):
    id: str
    approval_snapshot_id: str
    seat_classification: str
    approved_count: int
    authorization_reference: str | None = None


class ApprovalSnapshotOut(CamelModel):
    id: str
    programme_id: str
    academic_year: str
    approval_reference: str
    valid_from: date
    valid_to: date | None = None
    issued_by: str | None = None
    notes: str | None = None
    version: int
    status: str
    allocations: list[IntakeAllocationOut] = Field(default_factory=list)
    created_at: datetime | None = None


class CapacityOut(CamelModel):
    programme_id: str
    academic_year: str
    allocations: dict[str, int]
    reported: int
    projected: int
    status: str
    evidence: dict[str, Any]
    approval_snapshot_id: str | None = None
    approval_reference: str | None = None


class InstitutionCreate(CamelModel):
    aicte_institution_code: str = Field(min_length=3, max_length=32)
    name: str = Field(min_length=3, max_length=255)
    institution_type: str
    state: str | None = None
    city: str | None = None
    website_url: str | None = None
    contact_email: EmailStr | None = None

    @field_validator("institution_type")
    @classmethod
    def _known_type(cls, value: str) -> str:
        allowed = {
            "GOVERNMENT",
            "GOVERNMENT_AIDED",
            "PRIVATE_SELF_FINANCED",
            "DEEMED_UNIVERSITY",
            "OTHER",
        }
        if value not in allowed:
            raise ValueError(f"Unknown institution type: {value}")
        return value


class CampusCreate(CamelModel):
    campus_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=255)
    location: str | None = None


class ProgrammeCreate(CamelModel):
    programme_code: str = Field(min_length=1, max_length=32)
    programme_name: str = Field(min_length=3, max_length=255)
    award_level: Literal[
        "CERTIFICATE",
        "DIPLOMA",
        "PG_DIPLOMA",
        "UNDERGRADUATE",
        "POSTGRADUATE",
        "DOCTORAL",
    ]
    duration_years: int = Field(default=4, ge=1, le=8)


class AllocationCreate(CamelModel):
    seat_classification: Literal["APPROVED_REGULAR", "APPROVED_SUPERNUMERARY", "OTHER"]
    approved_count: int = Field(ge=0, le=1_000_000)
    authorization_reference: str | None = None


class IntakeSnapshotCreate(CamelModel):
    academic_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    approval_reference: str = Field(min_length=3, max_length=128)
    valid_from: date
    valid_to: date | None = None
    issued_by: str | None = None
    notes: str | None = None
    allocations: list[AllocationCreate] = Field(min_length=1)

    @field_validator("allocations")
    @classmethod
    def _one_regular_allocation(cls, values: list[AllocationCreate]) -> list[AllocationCreate]:
        regular = [value for value in values if value.seat_classification == "APPROVED_REGULAR"]
        if len(regular) != 1:
            raise ValueError("Exactly one APPROVED_REGULAR allocation is required")
        return values


class AllocationPatch(CamelModel):
    approved_count: int | None = Field(default=None, ge=0, le=1_000_000)
    authorization_reference: str | None = None
    reason: str | None = Field(default=None, max_length=512)
