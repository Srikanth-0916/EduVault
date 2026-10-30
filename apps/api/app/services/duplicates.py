"""Idempotent duplicate-case creation and resolution helpers."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.errors import validation_error
from app.models.base import utc_now
from app.models.enums import (
    CaseResolutionCode,
    DuplicateCaseStatus,
    DuplicateMatchType,
    Severity,
)
from app.models.review import DuplicateCase
from sqlalchemy import select
from sqlalchemy.orm import Session


def date_overlap_days(
    primary_start: date | None,
    primary_end: date | None,
    related_start: date | None,
    related_end: date | None,
) -> int:
    if primary_start is None or related_start is None:
        return 0
    start = max(primary_start, related_start)
    end = min(primary_end or date.max, related_end or date.max)
    return max(0, (end - start).days + 1)


def _match_group_id(
    match_type: str,
    primary_enrollment_id: str | None,
    related_enrollment_id: str | None,
    match_key: str | None,
) -> str:
    if match_key:
        return f"{match_type}:{match_key}"
    left = primary_enrollment_id or "none"
    right = related_enrollment_id or "none"
    ordered = sorted((left, right))
    return f"{match_type}:{ordered[0]}:{ordered[1]}"


def create_case_for_match(
    db: Session,
    *,
    match_type: str,
    severity: str,
    evidence: dict[str, Any],
    primary_enrollment_id: str | None = None,
    related_enrollment_id: str | None = None,
    institution_id: str | None = None,
    discovered_batch_id: str | None = None,
    match_key: str | None = None,
) -> DuplicateCase:
    """Create or refresh one case per stable match group."""
    if match_type not in {item.value for item in DuplicateMatchType}:
        raise validation_error("Unknown duplicate match type")
    if severity not in {item.value for item in Severity}:
        raise validation_error("Unknown case severity")
    group_id = _match_group_id(match_type, primary_enrollment_id, related_enrollment_id, match_key)
    existing = db.scalar(select(DuplicateCase).where(DuplicateCase.match_group_id == group_id))
    if existing is not None:
        existing.evidence = evidence
        existing.severity = severity
        if existing.status == DuplicateCaseStatus.WITHDRAWN.value:
            existing.status = DuplicateCaseStatus.OPEN.value
        return existing

    case = DuplicateCase(
        match_group_id=group_id,
        match_type=match_type,
        severity=severity,
        status=DuplicateCaseStatus.OPEN.value,
        primary_enrollment_id=primary_enrollment_id,
        related_enrollment_id=related_enrollment_id,
        institution_id=institution_id,
        discovered_batch_id=discovered_batch_id,
        opened_at=utc_now(),
        evidence=evidence,
    )
    db.add(case)
    db.flush()
    return case


def resolve_case(
    db: Session,
    case: DuplicateCase,
    *,
    resolution_code: str,
    reason: str,
    actor_id: str,
) -> DuplicateCase:
    if resolution_code not in {item.value for item in CaseResolutionCode}:
        raise validation_error("Unknown case resolution code")
    if case.status == DuplicateCaseStatus.RESOLVED.value:
        raise validation_error("This case is already resolved")
    case.status = DuplicateCaseStatus.RESOLVED.value
    case.resolution_code = resolution_code
    case.resolution_reason = reason
    case.resolved_by = actor_id
    case.resolved_at = utc_now()
    db.flush()
    return case


def request_case_information(db: Session, case: DuplicateCase, *, reason: str) -> DuplicateCase:
    if case.status == DuplicateCaseStatus.RESOLVED.value:
        raise validation_error("A resolved case cannot be reopened for information")
    case.status = DuplicateCaseStatus.IN_REVIEW.value
    case.resolution_reason = reason
    db.flush()
    return case


def record_institution_response(
    db: Session,
    case: DuplicateCase,
    *,
    message: str,
    actor_id: str,
) -> DuplicateCase:
    """Append an institution response and move the case into review."""
    if case.status == DuplicateCaseStatus.RESOLVED.value:
        raise validation_error("A resolved case cannot receive a new response")
    evidence = dict(case.evidence or {})
    history = list(evidence.get("institutionResponses") or [])
    history.append({"message": message, "by": actor_id, "at": utc_now().isoformat()})
    evidence["institutionResponses"] = history
    case.evidence = evidence
    case.status = DuplicateCaseStatus.IN_REVIEW.value
    db.flush()
    return case
