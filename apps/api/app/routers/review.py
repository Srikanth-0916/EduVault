"""AICTE reviewer queue endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.db import get_db
from app.deps import CurrentUser, Pagination
from app.errors import conflict, forbidden, not_found
from app.models.batch import SubmissionBatch
from app.models.enums import BatchStatus
from app.schemas.review import ReviewerAssignment, ReviewQueueResponse, ReviewSummary
from app.services.review import can_assign_reviewer, review_queue, review_summary

router = APIRouter(prefix="/review", tags=["review"])
_REVIEW_ROLES = {"AICTE_REVIEWER", "AICTE_SUPERVISOR"}


def _assert_reviewer(user: CurrentUser) -> None:
    if not set(user.roles) & _REVIEW_ROLES:
        raise forbidden("AICTE reviewer or supervisor access is required")


@router.get("/queue", response_model=ReviewQueueResponse)
def get_queue(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    pagination: Pagination,
    status: Annotated[str | None, Query()] = None,
    institution_id: Annotated[str | None, Query(alias="institutionId")] = None,
    severity: Annotated[str | None, Query()] = None,
) -> ReviewQueueResponse:
    _assert_reviewer(user)
    page, page_size = pagination
    items, total = review_queue(
        db,
        status=status,
        institution_id=institution_id,
        severity=severity,
        page=page,
        page_size=page_size,
    )
    return ReviewQueueResponse(items=items, page=page, page_size=page_size, total=total)


@router.get("/summary", response_model=ReviewSummary)
def get_review_summary(user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> ReviewSummary:
    _assert_reviewer(user)
    return review_summary(db)


@router.post("/queue/{batch_id}/assign", response_model=ReviewQueueResponse)
def assign_reviewer(
    batch_id: str,
    payload: ReviewerAssignment,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    pagination: Pagination,
) -> ReviewQueueResponse:
    if "AICTE_SUPERVISOR" not in user.roles and "SYSTEM_ADMIN" not in user.roles:
        raise forbidden("Only a supervisor can assign review work")
    batch = db.get(SubmissionBatch, batch_id)
    if batch is None:
        raise not_found("Submission batch not found")
    if batch.status != BatchStatus.UNDER_AICTE_REVIEW.value:
        raise conflict("Only batches under review can be assigned")
    if payload.reviewer_id and not can_assign_reviewer(db, payload.reviewer_id):
        raise not_found("Reviewer not found")
    batch.assigned_reviewer_id = payload.reviewer_id
    record_audit(
        db,
        actor=user,
        action="REVIEWER_ASSIGNED",
        resource_type="submission_batch",
        resource_ref=batch.id,
        institution_id=batch.institution_id,
        reason=payload.reason,
        metadata={"reviewerId": payload.reviewer_id},
        request=request,
    )
    db.commit()
    page, page_size = pagination
    items, total = review_queue(
        db,
        status=BatchStatus.UNDER_AICTE_REVIEW.value,
        institution_id=None,
        severity=None,
        page=page,
        page_size=page_size,
    )
    return ReviewQueueResponse(items=items, page=page, page_size=page_size, total=total)
