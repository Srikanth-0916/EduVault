"""Dashboard response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import CamelModel


class KpiOut(CamelModel):
    key: str
    label: str
    value: int
    hint: str | None = None
    tone: str = "default"


class DashboardCapacityRow(CamelModel):
    programme_id: str
    programme_code: str
    programme_name: str
    campus_name: str | None = None
    approved_regular: int
    approved_supernumerary: int
    reported_regular: int
    reported_supernumerary: int
    reported_total: int
    status: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class DistributionRow(CamelModel):
    key: str
    label: str
    count: int


class DashboardBatchRow(CamelModel):
    id: str
    academic_year: str
    status: str
    source_type: str
    row_count: int
    version: int
    created_at: datetime | None = None
    submitted_at: datetime | None = None


class DashboardCaseRow(CamelModel):
    id: str
    match_type: str
    severity: str
    status: str
    opened_at: datetime


class InstitutionDashboard(CamelModel):
    institution_id: str
    institution_name: str
    academic_year: str
    generated_at: datetime
    data_freshness: str
    kpis: list[KpiOut]
    capacity: list[DashboardCapacityRow]
    identity_distribution: list[DistributionRow]
    enrollment_status_distribution: list[DistributionRow]
    recent_batches: list[DashboardBatchRow]
    open_cases: list[DashboardCaseRow]


class NationalDashboard(CamelModel):
    academic_year: str
    generated_at: datetime
    data_freshness: str
    kpis: list[KpiOut]
    institution_type_distribution: list[DistributionRow]
    batch_status_distribution: list[DistributionRow]
    possible_excess_programmes: list[DashboardCapacityRow]
    reporting_institutions: list[dict[str, Any]]
