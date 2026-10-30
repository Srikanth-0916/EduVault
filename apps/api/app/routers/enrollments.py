"""Enrollment read/write endpoints with versioned corrections."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.constants import INSTITUTION_STAFF_ROLES
from app.db import get_db
from app.deps import CurrentUser, Pagination
from app.errors import forbidden, not_found
from app.models.batch import ValidationFinding
from app.models.enrollment import EnrollmentVersion, StudentEnrollment
from app.models.identity import StudentIdentity
from app.models.master import Campus, Institution, Programme
from app.models.review import IdentityVerification
from app.schemas.common import Page
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentDetail,
    EnrollmentPatch,
    EnrollmentSummary,
    EnrollmentVersionOut,
    FindingOut,
    IdentityVerifyResponse,
)
from app.schemas.identity import IdentityVerificationOut
from app.security import mask_apaar_last4
from app.services.enrollment import create_enrollment, supersede_enrollment, verify_identity

router = APIRouter(prefix="/enrollments", tags=["enrollments"])

_NATIONAL_READ = {
    "AICTE_REVIEWER",
    "AICTE_SUPERVISOR",
    "SYSTEM_ADMIN",
    "AUDITOR",
}


def _identity(db: Session, enrollment: StudentEnrollment) -> StudentIdentity | None:
    return db.get(StudentIdentity, enrollment.student_identity_id)


def _summary(db: Session, enrollment: StudentEnrollment) -> EnrollmentSummary:
    programme = db.get(Programme, enrollment.programme_id)
    campus = db.get(Campus, enrollment.campus_id) if enrollment.campus_id else None
    institution = db.get(Institution, enrollment.institution_id)
    identity = _identity(db, enrollment)
    return EnrollmentSummary(
        id=enrollment.id,
        institution_id=enrollment.institution_id,
        institution_name=institution.name if institution else None,
        campus_id=enrollment.campus_id,
        campus_name=campus.name if campus else None,
        programme_id=enrollment.programme_id,
        programme_name=programme.programme_name if programme else None,
        student_local_id=enrollment.student_local_id,
        student_full_name=enrollment.student_full_name,
        masked_apaar=mask_apaar_last4(identity.apaar_last4 if identity else None),
        identity_status=identity.identifier_status if identity else None,
        academic_year=enrollment.academic_year,
        admission_date=enrollment.admission_date,
        exit_date=enrollment.exit_date,
        enrollment_status=enrollment.enrollment_status,
        seat_classification=enrollment.seat_classification,
        admission_category=enrollment.admission_category,
        nri_status=enrollment.nri_status,
        oci_status=enrollment.oci_status,
        foreign_national_status=enrollment.foreign_national_status,
        version=enrollment.version,
        is_current=enrollment.is_current,
        record_accepted_at=enrollment.record_accepted_at,
        updated_at=enrollment.updated_at,
    )


def _finding_out(finding: ValidationFinding) -> FindingOut:
    return FindingOut(
        id=finding.id,
        rule_id=finding.rule_id,
        code=finding.code,
        severity=finding.severity,
        blocking=finding.blocking,
        message=finding.message,
        field=finding.field,
        status=finding.status,
        evidence=finding.evidence,
        row_id=finding.row_id,
    )


def _detail(db: Session, enrollment: StudentEnrollment) -> EnrollmentDetail:
    summary = _summary(db, enrollment)
    versions = db.scalars(
        select(EnrollmentVersion)
        .where(EnrollmentVersion.student_enrollment_id == enrollment.id)
        .order_by(EnrollmentVersion.version.desc())
    ).all()
    verifications = db.scalars(
        select(IdentityVerification)
        .where(IdentityVerification.student_identity_id == enrollment.student_identity_id)
        .order_by(IdentityVerification.checked_at.desc())
    ).all()
    findings: list[ValidationFinding] = []
    if enrollment.source_row_id:
        findings = list(
            db.scalars(
                select(ValidationFinding).where(
                    or_(
                        ValidationFinding.row_id == enrollment.source_row_id,
                        ValidationFinding.record_id == enrollment.source_row_id,
                    )
                )
            ).all()
        )
    return EnrollmentDetail(
        **summary.model_dump(),
        supernumerary_approval_reference=enrollment.supernumerary_approval_reference,
        versions=[
            EnrollmentVersionOut(
                id=version.id,
                version=version.version,
                snapshot=version.snapshot,
                change_reason=version.change_reason,
                changed_by=version.changed_by,
                actor_role=version.actor_role,
                created_at=version.created_at,
            )
            for version in versions
        ],
        verifications=[
            IdentityVerificationOut(
                id=item.id,
                provider=item.provider,
                provider_reference=item.provider_reference,
                result=item.result,
                adapter_version=item.adapter_version,
                is_mock=item.is_mock,
                checked_at=item.checked_at,
                purpose=item.purpose,
                consent_context=item.consent_context,
                resulting_status=item.resulting_status,
                detail=item.detail,
            )
            for item in verifications
        ],
        findings=[_finding_out(item) for item in findings],
    )


def _assert_read(user: CurrentUser, enrollment: StudentEnrollment) -> None:
    roles = set(user.roles)
    if "STUDENT" in roles:
        if user.student_identity_id == enrollment.student_identity_id:
            return
        raise forbidden()
    if roles & _NATIONAL_READ:
        return
    if user.institution_id and user.institution_id == enrollment.institution_id:
        return
    raise forbidden()


def _assert_institution_write(user: CurrentUser, institution_id: str) -> None:
    if user.institution_id != institution_id:
        raise forbidden()
    if not set(user.roles) & set(INSTITUTION_STAFF_ROLES):
        raise forbidden()


def _get_enrollment(db: Session, enrollment_id: str) -> StudentEnrollment:
    enrollment = db.get(StudentEnrollment, enrollment_id)
    if enrollment is None:
        raise not_found("Enrollment not found")
    return enrollment


@router.get("", response_model=Page[EnrollmentSummary])
def list_enrollments(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    pagination: Pagination,
    academic_year: Annotated[str | None, Query(alias="academicYear")] = None,
    programme_id: Annotated[str | None, Query(alias="programmeId")] = None,
    enrollment_status: Annotated[str | None, Query(alias="enrollmentStatus")] = None,
    identity_status: Annotated[str | None, Query(alias="identityStatus")] = None,
    search: Annotated[str | None, Query(max_length=120)] = None,
) -> Page[EnrollmentSummary]:
    roles = set(user.roles)
    if "AICTE_ANALYST" in roles:
        raise forbidden("Analysts receive aggregate reports, not student-level rows")

    statement = select(StudentEnrollment).where(StudentEnrollment.is_current.is_(True))
    count_statement = select(func.count(StudentEnrollment.id)).where(
        StudentEnrollment.is_current.is_(True)
    )
    if "STUDENT" in roles:
        if not user.student_identity_id:
            raise forbidden()
        statement = statement.where(
            StudentEnrollment.student_identity_id == user.student_identity_id
        )
        count_statement = count_statement.where(
            StudentEnrollment.student_identity_id == user.student_identity_id
        )
    elif user.institution_id:
        statement = statement.where(StudentEnrollment.institution_id == user.institution_id)
        count_statement = count_statement.where(
            StudentEnrollment.institution_id == user.institution_id
        )
    elif not roles & (_NATIONAL_READ | {"AICTE_ANALYST"}):
        raise forbidden()

    if academic_year:
        statement = statement.where(StudentEnrollment.academic_year == academic_year)
        count_statement = count_statement.where(StudentEnrollment.academic_year == academic_year)
    if programme_id:
        statement = statement.where(StudentEnrollment.programme_id == programme_id)
        count_statement = count_statement.where(StudentEnrollment.programme_id == programme_id)
    if enrollment_status:
        statement = statement.where(StudentEnrollment.enrollment_status == enrollment_status)
        count_statement = count_statement.where(
            StudentEnrollment.enrollment_status == enrollment_status
        )
    if identity_status:
        statement = statement.join(
            StudentIdentity, StudentIdentity.id == StudentEnrollment.student_identity_id
        ).where(StudentIdentity.identifier_status == identity_status)
        count_statement = count_statement.join(
            StudentIdentity, StudentIdentity.id == StudentEnrollment.student_identity_id
        ).where(StudentIdentity.identifier_status == identity_status)
    if search:
        term = f"%{search.strip()}%"
        predicate = or_(
            StudentEnrollment.student_full_name.ilike(term),
            StudentEnrollment.student_local_id.ilike(term),
        )
        statement = statement.where(predicate)
        count_statement = count_statement.where(predicate)

    page, page_size = pagination
    total = int(db.scalar(count_statement) or 0)
    rows = db.scalars(
        statement.order_by(StudentEnrollment.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page[EnrollmentSummary](
        items=[_summary(db, row) for row in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("", response_model=EnrollmentDetail, status_code=201)
def create_enrollment_route(
    payload: EnrollmentCreate,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> EnrollmentDetail:
    if not user.institution_id:
        raise forbidden("Only institution staff can create enrollments")
    _assert_institution_write(user, user.institution_id)
    data = payload.model_dump()
    data["raw_apaar"] = data.pop("apaar_id")
    enrollment = create_enrollment(db, actor=user, institution_id=user.institution_id, data=data)
    record_audit(
        db,
        actor=user,
        action="ENROLLMENT_CREATED",
        resource_type="student_enrollment",
        resource_ref=enrollment.id,
        institution_id=user.institution_id,
        metadata={"studentLocalId": enrollment.student_local_id},
        request=request,
    )
    db.commit()
    return _detail(db, enrollment)


@router.get("/{enrollment_id}", response_model=EnrollmentDetail)
def get_enrollment(
    enrollment_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> EnrollmentDetail:
    enrollment = _get_enrollment(db, enrollment_id)
    _assert_read(user, enrollment)
    return _detail(db, enrollment)


@router.patch("/{enrollment_id}", response_model=EnrollmentDetail)
def update_enrollment(
    enrollment_id: str,
    payload: EnrollmentPatch,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> EnrollmentDetail:
    enrollment = _get_enrollment(db, enrollment_id)
    _assert_institution_write(user, enrollment.institution_id)
    data = payload.model_dump(exclude_unset=True)
    reason = str(data.pop("reason"))
    data["raw_apaar"] = data.pop("apaar_id", None)
    data = {key: value for key, value in data.items() if value is not None}
    updated = supersede_enrollment(db, enrollment, actor=user, data=data, reason=reason)
    record_audit(
        db,
        actor=user,
        action="ENROLLMENT_CORRECTED",
        resource_type="student_enrollment",
        resource_ref=updated.id,
        institution_id=updated.institution_id,
        reason=reason,
        metadata={"previousId": enrollment.id, "version": updated.version},
        request=request,
    )
    db.commit()
    return _detail(db, updated)


@router.post("/{enrollment_id}/verify-identity", response_model=IdentityVerifyResponse)
def verify_enrollment_identity(
    enrollment_id: str,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> IdentityVerifyResponse:
    enrollment = _get_enrollment(db, enrollment_id)
    roles = set(user.roles)
    if not (
        (user.institution_id == enrollment.institution_id and roles & set(INSTITUTION_STAFF_ROLES))
        or roles & {"AICTE_REVIEWER", "AICTE_SUPERVISOR", "SYSTEM_ADMIN"}
    ):
        raise forbidden()
    identity = _identity(db, enrollment)
    if identity is None:
        raise not_found("Student identity not found")
    verification = verify_identity(
        db,
        identity,
        actor=user,
        purpose="enrollment identity verification",
    )
    record_audit(
        db,
        actor=user,
        action="IDENTITY_VERIFICATION_REQUESTED",
        resource_type="student_identity",
        resource_ref=identity.id,
        institution_id=enrollment.institution_id,
        metadata={
            "enrollmentId": enrollment.id,
            "mock": True,
            "result": verification.result,
        },
        request=request,
    )
    db.commit()
    return IdentityVerifyResponse(
        identity_status=identity.identifier_status,
        verification=IdentityVerificationOut(
            id=verification.id,
            provider=verification.provider,
            provider_reference=verification.provider_reference,
            result=verification.result,
            adapter_version=verification.adapter_version,
            is_mock=verification.is_mock,
            checked_at=verification.checked_at,
            purpose=verification.purpose,
            consent_context=verification.consent_context,
            resulting_status=verification.resulting_status,
            detail=verification.detail,
        ),
    )
