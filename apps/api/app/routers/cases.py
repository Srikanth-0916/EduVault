"""Duplicate case review, resolution, and information requests."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.constants import INSTITUTION_STAFF_ROLES
from app.db import get_db
from app.deps import CurrentUser, Pagination
from app.errors import forbidden, not_found
from app.models.enums import DuplicateCaseStatus, Severity
from app.models.review import DuplicateCase
from app.schemas.case import (
    CaseInformationRequest,
    CaseListResponse,
    CaseOut,
    CaseResolveRequest,
    CaseResponseRequest,
)
from app.services.duplicates import (
    record_institution_response,
    request_case_information,
    resolve_case,
)
from app.services.notifications import notify_institution_roles, notify_national_roles

router = APIRouter(prefix="/duplicate-cases", tags=["duplicate-cases"])

_READ = {"AICTE_REVIEWER", "AICTE_SUPERVISOR", "SYSTEM_ADMIN", "AUDITOR"}
_DECIDE = {"AICTE_REVIEWER", "AICTE_SUPERVISOR", "SYSTEM_ADMIN"}
_RESOLVE = {"AICTE_SUPERVISOR", "SYSTEM_ADMIN"}


def _case_out(case: DuplicateCase) -> CaseOut:
    return CaseOut(
        id=case.id,
        match_group_id=case.match_group_id,
        match_type=case.match_type,
        severity=case.severity,
        status=case.status,
        primary_enrollment_id=case.primary_enrollment_id,
        related_enrollment_id=case.related_enrollment_id,
        institution_id=case.institution_id,
        discovered_batch_id=case.discovered_batch_id,
        opened_at=case.opened_at,
        assigned_reviewer_id=case.assigned_reviewer_id,
        resolution_code=case.resolution_code,
        resolution_reason=case.resolution_reason,
        resolved_by=case.resolved_by,
        resolved_at=case.resolved_at,
        evidence=case.evidence,
    )


def _get_case(db: Session, case_id: str) -> DuplicateCase:
    case = db.get(DuplicateCase, case_id)
    if case is None:
        raise not_found("Duplicate case not found")
    return case


def _assert_read(user: CurrentUser, case: DuplicateCase) -> None:
    if user.institution_id and case.institution_id == user.institution_id:
        return
    if set(user.roles) & _READ:
        return
    raise forbidden()


@router.get("", response_model=CaseListResponse)
def list_cases(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    pagination: Pagination,
    status: Annotated[str | None, Query()] = None,
    severity: Annotated[str | None, Query()] = None,
) -> CaseListResponse:
    if not user.institution_id and not set(user.roles) & _READ:
        raise forbidden("Analysts receive aggregate reports, not case evidence")
    statement = select(DuplicateCase)
    count_statement = select(func.count(DuplicateCase.id))
    if user.institution_id:
        statement = statement.where(DuplicateCase.institution_id == user.institution_id)
        count_statement = count_statement.where(DuplicateCase.institution_id == user.institution_id)
    if status:
        statement = statement.where(DuplicateCase.status == status)
        count_statement = count_statement.where(DuplicateCase.status == status)
    if severity:
        statement = statement.where(DuplicateCase.severity == severity)
        count_statement = count_statement.where(DuplicateCase.severity == severity)
    page, page_size = pagination
    total = int(db.scalar(count_statement) or 0)
    cases = db.scalars(
        statement.order_by(DuplicateCase.opened_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return CaseListResponse(items=[_case_out(case) for case in cases], total=total)


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    case_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CaseOut:
    case = _get_case(db, case_id)
    _assert_read(user, case)
    return _case_out(case)


@router.post("/{case_id}/resolve", response_model=CaseOut)
def resolve_duplicate_case(
    case_id: str,
    payload: CaseResolveRequest,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CaseOut:
    if not set(user.roles) & _RESOLVE:
        raise forbidden("A supervisor must confirm duplicate-case resolution")
    case = _get_case(db, case_id)
    resolve_case(
        db,
        case,
        resolution_code=payload.resolution_code,
        reason=payload.reason,
        actor_id=user.id,
    )
    if case.institution_id:
        notify_institution_roles(
            db,
            institution_id=case.institution_id,
            roles=INSTITUTION_STAFF_ROLES,
            event_type="DUPLICATE_CASE_RESOLVED",
            title="A duplicate case was resolved",
            body=f"Case {case.id} was resolved as {payload.resolution_code}. {payload.reason}",
            resource_type="duplicate_case",
            resource_ref=case.id,
        )
    record_audit(
        db,
        actor=user,
        action="DUPLICATE_CASE_RESOLVED",
        resource_type="duplicate_case",
        resource_ref=case.id,
        institution_id=case.institution_id,
        reason=payload.reason,
        metadata={"resolutionCode": payload.resolution_code},
        request=request,
    )
    db.commit()
    return _case_out(case)


@router.post("/{case_id}/request-information", response_model=CaseOut)
def request_more_information(
    case_id: str,
    payload: CaseInformationRequest,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CaseOut:
    if not set(user.roles) & _DECIDE:
        raise forbidden()
    case = _get_case(db, case_id)
    request_case_information(db, case, reason=payload.reason)
    if case.institution_id:
        notify_institution_roles(
            db,
            institution_id=case.institution_id,
            roles=INSTITUTION_STAFF_ROLES,
            event_type="DUPLICATE_CASE_INFORMATION_REQUESTED",
            title="More information is needed for a duplicate case",
            body=f"Case {case.id}: {payload.reason}",
            resource_type="duplicate_case",
            resource_ref=case.id,
        )
    record_audit(
        db,
        actor=user,
        action="DUPLICATE_CASE_INFORMATION_REQUESTED",
        resource_type="duplicate_case",
        resource_ref=case.id,
        institution_id=case.institution_id,
        reason=payload.reason,
        request=request,
    )
    db.commit()
    return _case_out(case)


__all__ = ["DuplicateCaseStatus", "Severity", "router"]


@router.post("/{case_id}/respond", response_model=CaseOut)
def respond_to_case(
    case_id: str,
    payload: CaseResponseRequest,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CaseOut:
    if not user.institution_id or not set(user.roles) & set(INSTITUTION_STAFF_ROLES):
        raise forbidden("Institution staff access is required")
    case = _get_case(db, case_id)
    if case.institution_id != user.institution_id:
        raise forbidden()
    record_institution_response(db, case, message=payload.message, actor_id=user.id)
    notify_national_roles(
        db,
        roles=_DECIDE,
        event_type="DUPLICATE_CASE_RESPONSE_RECEIVED",
        title="An institution responded to a duplicate case",
        body=f"Case {case.id}: {payload.message}",
        resource_type="duplicate_case",
        resource_ref=case.id,
    )
    record_audit(
        db,
        actor=user,
        action="DUPLICATE_CASE_RESPONSE_RECORDED",
        resource_type="duplicate_case",
        resource_ref=case.id,
        institution_id=case.institution_id,
        reason=payload.message,
        request=request,
    )
    db.commit()
    return _case_out(case)
