"""Duplicate case API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import CamelModel


class CaseOut(CamelModel):
    id: str
    match_group_id: str
    match_type: str
    severity: str
    status: str
    primary_enrollment_id: str | None = None
    related_enrollment_id: str | None = None
    institution_id: str | None = None
    discovered_batch_id: str | None = None
    opened_at: datetime
    assigned_reviewer_id: str | None = None
    resolution_code: str | None = None
    resolution_reason: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    evidence: dict[str, object] | None = None


class CaseListResponse(CamelModel):
    items: list[CaseOut]
    total: int


class CaseResolveRequest(CamelModel):
    resolution_code: Literal[
        "VALID_TRANSFER",
        "PERMITTED_CONCURRENT_ENROLMENT",
        "DATA_ERROR",
        "UNRESOLVED",
        "POLICY_BREACH",
    ]
    reason: str = Field(min_length=3, max_length=1024)


class CaseInformationRequest(CamelModel):
    reason: str = Field(min_length=3, max_length=1024)


class CaseResponseRequest(CamelModel):
    message: str = Field(min_length=3, max_length=2000)
