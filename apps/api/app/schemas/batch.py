"""Submission batch API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import CamelModel
from app.schemas.enrollment import FindingOut


class BatchCreate(CamelModel):
    academic_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    campus_id: str | None = None
    programme_id: str | None = None
    source_type: Literal["CSV_UPLOAD", "MANUAL_ENTRY", "API_INTEGRATION"] = "CSV_UPLOAD"


class BatchSummary(CamelModel):
    id: str
    institution_id: str
    campus_id: str | None = None
    programme_id: str | None = None
    academic_year: str
    source_type: str
    status: str
    version: int
    supersedes_batch_id: str | None = None
    file_name: str | None = None
    file_checksum: str | None = None
    file_size_bytes: int | None = None
    row_count: int | None = None
    summary: dict[str, object] = Field(default_factory=dict)
    created_at: datetime | None = None
    attested_at: datetime | None = None
    submitted_at: datetime | None = None
    decision: str | None = None
    decision_reason: str | None = None
    decision_reason_code: str | None = None
    decided_at: datetime | None = None
    decision_history: list[dict[str, object]] = Field(default_factory=list)


class BatchRowOut(CamelModel):
    id: str
    source_row_number: int
    student_name: str | None = None
    student_local_id: str | None = None
    masked_apaar: str
    row_status: str
    enrollment_id: str | None = None
    findings: list[FindingOut] = Field(default_factory=list)


class BatchDetail(BatchSummary):
    rows: list[BatchRowOut] = Field(default_factory=list)
    findings: list[FindingOut] = Field(default_factory=list)
    validation_run_id: str | None = None
    validation_summary: dict[str, object] | None = None


class AttestRequest(CamelModel):
    declaration: bool
    attestation_name: str = Field(min_length=2, max_length=255)


class DecisionRequest(CamelModel):
    decision: Literal["ACCEPT", "RETURN", "REJECT"]
    reason: str = Field(min_length=3, max_length=1024)
    reason_code: (
        Literal[
            "DATA_QUALITY",
            "INTAKE_EXCEPTION",
            "IDENTITY_REVIEW",
            "POLICY",
            "OTHER",
        ]
        | None
    ) = None


class RowPatch(CamelModel):
    student_name: str | None = None
    apaar_id: str | None = None
    student_local_id: str | None = None
    programme_code: str | None = None
    campus_code: str | None = None
    academic_year: str | None = None
    admission_date: str | None = None
    exit_date: str | None = None
    enrollment_status: str | None = None
    seat_classification: str | None = None
    admission_category: str | None = None
    nri_status: str | None = None
    oci_status: str | None = None
    foreign_national_status: str | None = None
    approval_reference: str | None = None


class BatchReceiptOut(CamelModel):
    batch_id: str
    checksum: str
    row_count: int
    submitted_by: str | None = None
    submitted_at: datetime | None = None
    payload: dict[str, object]
    signature: dict[str, str]


class BatchListResponse(CamelModel):
    items: list[BatchSummary]
    total: int
