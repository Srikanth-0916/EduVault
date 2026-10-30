"""AICTE review queue aggregation."""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.batch import SubmissionBatch, ValidationRun
from app.models.enums import BatchStatus, Severity
from app.models.master import Institution, OrganizationMembership, User
from app.models.review import DuplicateCase
from app.schemas.review import ReviewQueueItem, ReviewSummary
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def _severity_for(summary: dict[str, object] | None) -> str | None:
    if not summary:
        return None
    by_rule = summary.get("byRule")
    if not isinstance(by_rule, dict):
        return None
    if summary.get("blockingFindings", 0):
        return Severity.HIGH.value
    if summary.get("warningRows", 0):
        return Severity.WARNING.value
    return Severity.INFO.value


def _latest_run(db: Session, batch_id: str) -> ValidationRun | None:
    return db.scalar(
        select(ValidationRun)
        .where(ValidationRun.batch_id == batch_id)
        .order_by(ValidationRun.started_at.desc())
    )


def review_queue(
    db: Session,
    *,
    status: str | None,
    institution_id: str | None,
    severity: str | None,
    page: int,
    page_size: int,
) -> tuple[list[ReviewQueueItem], int]:
    target_status = status or BatchStatus.UNDER_AICTE_REVIEW.value
    statement = (
        select(SubmissionBatch, Institution)
        .join(Institution, Institution.id == SubmissionBatch.institution_id)
        .where(SubmissionBatch.status == target_status)
    )
    count_statement = select(func.count(SubmissionBatch.id)).where(
        SubmissionBatch.status == target_status
    )
    if institution_id:
        statement = statement.where(SubmissionBatch.institution_id == institution_id)
        count_statement = count_statement.where(SubmissionBatch.institution_id == institution_id)
    batches = db.execute(
        statement.order_by(SubmissionBatch.submitted_at.asc().nullslast())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items: list[ReviewQueueItem] = []
    for batch, institution in batches:
        run = _latest_run(db, batch.id)
        summary = run.summary if run else {}
        current_severity = _severity_for(summary)
        if severity and current_severity != severity:
            continue
        submitted_at = batch.submitted_at or batch.created_at
        submitted_naive = (
            submitted_at.replace(tzinfo=UTC) if submitted_at.tzinfo is None else submitted_at
        )
        age_days = max(0, (datetime.now(UTC) - submitted_naive).days)
        items.append(
            ReviewQueueItem(
                batch_id=batch.id,
                institution_id=batch.institution_id,
                institution_name=institution.name,
                academic_year=batch.academic_year,
                status=batch.status,
                row_count=int(batch.row_count or 0),
                version=batch.version,
                severity=current_severity,
                blocking_findings=int(summary.get("blockingFindings", 0) or 0),
                warning_findings=int(summary.get("warningRows", 0) or 0),
                created_at=batch.created_at,
                submitted_at=batch.submitted_at,
                age_days=age_days,
                assigned_reviewer_id=batch.assigned_reviewer_id,
                decision=batch.decision,
            )
        )
    total = int(db.scalar(count_statement) or 0)
    return items, total


def review_summary(db: Session) -> ReviewSummary:
    counts: dict[str, int] = {}
    for status in (
        BatchStatus.UNDER_AICTE_REVIEW.value,
        BatchStatus.RETURNED_FOR_CORRECTION.value,
        BatchStatus.ACCEPTED.value,
        BatchStatus.REJECTED.value,
    ):
        counts[status] = int(
            db.scalar(
                select(func.count(SubmissionBatch.id)).where(SubmissionBatch.status == status)
            )
            or 0
        )
    oldest = db.scalar(
        select(SubmissionBatch.submitted_at)
        .where(SubmissionBatch.status == BatchStatus.UNDER_AICTE_REVIEW.value)
        .order_by(SubmissionBatch.submitted_at.asc())
    )
    open_cases = int(
        db.scalar(
            select(func.count(DuplicateCase.id)).where(
                DuplicateCase.status.in_(["OPEN", "IN_REVIEW"])
            )
        )
        or 0
    )
    return ReviewSummary(
        under_review=counts[BatchStatus.UNDER_AICTE_REVIEW.value],
        returned=counts[BatchStatus.RETURNED_FOR_CORRECTION.value],
        accepted=counts[BatchStatus.ACCEPTED.value],
        rejected=counts[BatchStatus.REJECTED.value],
        open_cases=open_cases,
        oldest_pending=oldest,
        average_turnaround_days=None,
    )


def can_assign_reviewer(db: Session, reviewer_id: str) -> bool:
    user = db.get(User, reviewer_id)
    if user is None or user.status != "ACTIVE":
        return False
    roles = set(
        db.scalars(
            select(OrganizationMembership.role).where(
                OrganizationMembership.user_id == reviewer_id,
                OrganizationMembership.is_active.is_(True),
            )
        ).all()
    )
    return bool(roles & {"AICTE_REVIEWER", "AICTE_SUPERVISOR"})
