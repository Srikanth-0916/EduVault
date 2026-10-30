"""AICTE review queue and assignment schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import CamelModel


class ReviewQueueItem(CamelModel):
    batch_id: str
    institution_id: str
    institution_name: str
    academic_year: str
    status: str
    row_count: int
    version: int
    severity: str | None = None
    blocking_findings: int = 0
    warning_findings: int = 0
    created_at: datetime | None = None
    submitted_at: datetime | None = None
    age_days: int = 0
    assigned_reviewer_id: str | None = None
    decision: str | None = None


class ReviewQueueResponse(CamelModel):
    items: list[ReviewQueueItem]
    page: int
    page_size: int
    total: int


class ReviewSummary(CamelModel):
    under_review: int
    returned: int
    accepted: int
    rejected: int
    open_cases: int
    oldest_pending: datetime | None = None
    average_turnaround_days: float | None = None


class ReviewerAssignment(CamelModel):
    reviewer_id: str | None = Field(default=None, min_length=1)
    reason: str = Field(min_length=3, max_length=512)
