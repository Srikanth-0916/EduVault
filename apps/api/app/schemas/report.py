"""Aggregate report and export schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.schemas.common import CamelModel


class ReportEnvelope(CamelModel):
    generated_at: datetime
    filters: dict[str, Any]
    data_freshness: str
    suppressed_groups: int = 0
    items: list[dict[str, Any]]


class IntakeReconciliationReport(ReportEnvelope):
    pass


class DataQualityReport(ReportEnvelope):
    pass
