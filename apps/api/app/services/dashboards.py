"""Institution dashboard aggregation."""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.batch import SubmissionBatch
from app.models.enrollment import StudentEnrollment
from app.models.enums import (
    BatchStatus,
    CapacityStatus,
    DuplicateCaseStatus,
    EnrollmentStatus,
    IdentityStatus,
    SeatClassification,
)
from app.models.identity import StudentIdentity
from app.models.master import Campus, Institution, Programme
from app.models.review import DuplicateCase
from app.schemas.dashboard import (
    DashboardBatchRow,
    DashboardCapacityRow,
    DashboardCaseRow,
    DistributionRow,
    InstitutionDashboard,
    KpiOut,
    NationalDashboard,
)
from app.services.capacity import calculate_capacity
from sqlalchemy import func, select
from sqlalchemy.orm import Session

_PENDING_BATCH_STATES = {
    BatchStatus.DRAFT.value,
    BatchStatus.VALIDATION_FAILED.value,
    BatchStatus.READY_FOR_ATTESTATION.value,
    BatchStatus.UNDER_AICTE_REVIEW.value,
}
_OPEN_CASE_STATES = {
    DuplicateCaseStatus.OPEN.value,
    DuplicateCaseStatus.IN_REVIEW.value,
}
_IDENTITY_LABELS = {
    IdentityStatus.MISSING.value: "Missing",
    IdentityStatus.MALFORMED.value: "Malformed",
    IdentityStatus.FORMAT_VALID.value: "Format valid",
    IdentityStatus.PENDING_EXTERNAL_CHECK.value: "Pending mock check",
    IdentityStatus.EXTERNALLY_CONFIRMED.value: "Mock check confirmed",
    IdentityStatus.EXTERNAL_MISMATCH.value: "Mock check mismatch",
    IdentityStatus.EXTERNAL_UNAVAILABLE.value: "Mock check unavailable",
    IdentityStatus.MANUAL_REVIEW.value: "Manual review",
}


def institution_dashboard(
    db: Session, institution: Institution, academic_year: str
) -> InstitutionDashboard:
    programmes = db.scalars(
        select(Programme)
        .where(
            Programme.institution_id == institution.id,
            Programme.status == "ACTIVE",
        )
        .order_by(Programme.programme_code.asc())
    ).all()
    campus_names = {
        campus.id: campus.name
        for campus in db.scalars(
            select(Campus).where(Campus.institution_id == institution.id)
        ).all()
    }
    capacity_rows: list[DashboardCapacityRow] = []
    approved_regular = 0
    approved_super = 0
    reported_total = 0
    for programme in programmes:
        capacity = calculate_capacity(db, programme.id, academic_year)
        regular = int(capacity.allocations.get(SeatClassification.APPROVED_REGULAR.value, 0))
        supernumerary = int(
            capacity.allocations.get(SeatClassification.APPROVED_SUPERNUMERARY.value, 0)
        )
        reported_regular = int(capacity.evidence.get("regularReported", 0))
        reported_super = int(capacity.evidence.get("supernumeraryReported", 0))
        approved_regular += regular
        approved_super += supernumerary
        reported_total += capacity.reported
        capacity_rows.append(
            DashboardCapacityRow(
                programme_id=programme.id,
                programme_code=programme.programme_code,
                programme_name=programme.programme_name,
                campus_name=campus_names.get(programme.campus_id),
                approved_regular=regular,
                approved_supernumerary=supernumerary,
                reported_regular=reported_regular,
                reported_supernumerary=reported_super,
                reported_total=reported_regular + reported_super,
                status=capacity.status,
                evidence=capacity.evidence,
            )
        )

    enrollment_filter = (
        StudentEnrollment.institution_id == institution.id,
        StudentEnrollment.academic_year == academic_year,
        StudentEnrollment.is_current.is_(True),
    )
    total_reported = int(
        db.scalar(select(func.count(StudentEnrollment.id)).where(*enrollment_filter)) or 0
    )
    active = int(
        db.scalar(
            select(func.count(StudentEnrollment.id)).where(
                *enrollment_filter,
                StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE.value,
            )
        )
        or 0
    )
    gaps = int(
        db.scalar(
            select(func.count(StudentEnrollment.id))
            .join(StudentIdentity, StudentIdentity.id == StudentEnrollment.student_identity_id)
            .where(
                *enrollment_filter,
                StudentIdentity.identifier_status.in_(
                    [IdentityStatus.MISSING.value, IdentityStatus.MALFORMED.value]
                ),
            )
        )
        or 0
    )
    unresolved_cases = int(
        db.scalar(
            select(func.count(DuplicateCase.id)).where(
                DuplicateCase.institution_id == institution.id,
                DuplicateCase.status.in_(list(_OPEN_CASE_STATES)),
            )
        )
        or 0
    )
    pending_batches = int(
        db.scalar(
            select(func.count(SubmissionBatch.id)).where(
                SubmissionBatch.institution_id == institution.id,
                SubmissionBatch.status.in_(list(_PENDING_BATCH_STATES)),
            )
        )
        or 0
    )

    identity_rows = db.execute(
        select(StudentIdentity.identifier_status, func.count(StudentEnrollment.id))
        .join(StudentIdentity, StudentIdentity.id == StudentEnrollment.student_identity_id)
        .where(*enrollment_filter)
        .group_by(StudentIdentity.identifier_status)
        .order_by(StudentIdentity.identifier_status.asc())
    ).all()
    identity_distribution = [
        DistributionRow(
            key=status,
            label=_IDENTITY_LABELS.get(status, status.replace("_", " ").title()),
            count=int(count),
        )
        for status, count in identity_rows
    ]

    status_rows = db.execute(
        select(StudentEnrollment.enrollment_status, func.count(StudentEnrollment.id))
        .where(*enrollment_filter)
        .group_by(StudentEnrollment.enrollment_status)
        .order_by(StudentEnrollment.enrollment_status.asc())
    ).all()
    enrollment_distribution = [
        DistributionRow(
            key=status,
            label=status.replace("_", " ").title(),
            count=int(count),
        )
        for status, count in status_rows
    ]

    recent_batches = db.scalars(
        select(SubmissionBatch)
        .where(SubmissionBatch.institution_id == institution.id)
        .order_by(SubmissionBatch.created_at.desc())
        .limit(5)
    ).all()
    open_cases = db.scalars(
        select(DuplicateCase)
        .where(
            DuplicateCase.institution_id == institution.id,
            DuplicateCase.status.in_(list(_OPEN_CASE_STATES)),
        )
        .order_by(DuplicateCase.opened_at.desc())
        .limit(5)
    ).all()

    return InstitutionDashboard(
        institution_id=institution.id,
        institution_name=institution.name,
        academic_year=academic_year,
        generated_at=datetime.now(UTC).replace(tzinfo=None),
        data_freshness="Prototype data refreshed on each request; all records are synthetic.",
        kpis=[
            KpiOut(
                key="approved_intake",
                label="Approved intake",
                value=approved_regular + approved_super,
                hint=f"{approved_regular} regular + {approved_super} supernumerary",
            ),
            KpiOut(
                key="reported_enrollment",
                label="Reported enrolment",
                value=total_reported,
                hint=f"{reported_total} total reported in {academic_year}",
            ),
            KpiOut(
                key="active_enrollment",
                label="Active enrolments",
                value=active,
                hint="Current records with ACTIVE status",
            ),
            KpiOut(
                key="apaar_gaps",
                label="APAAR gaps",
                value=gaps,
                hint="Missing or malformed identifiers",
                tone="warning" if gaps else "success",
            ),
            KpiOut(
                key="unresolved_cases",
                label="Unresolved cases",
                value=unresolved_cases,
                hint="Duplicate or overlap cases needing review",
                tone="warning" if unresolved_cases else "success",
            ),
            KpiOut(
                key="pending_batches",
                label="Pending batches",
                value=pending_batches,
                hint="Draft, validation, attestation or review",
            ),
        ],
        capacity=capacity_rows,
        identity_distribution=identity_distribution,
        enrollment_status_distribution=enrollment_distribution,
        recent_batches=[
            DashboardBatchRow(
                id=batch.id,
                academic_year=batch.academic_year,
                status=batch.status,
                source_type=batch.source_type,
                row_count=int(batch.row_count or 0),
                version=batch.version,
                created_at=batch.created_at,
                submitted_at=batch.submitted_at,
            )
            for batch in recent_batches
        ],
        open_cases=[
            DashboardCaseRow(
                id=case.id,
                match_type=case.match_type,
                severity=case.severity,
                status=case.status,
                opened_at=case.opened_at,
            )
            for case in open_cases
        ],
    )


def national_dashboard(db: Session, academic_year: str) -> NationalDashboard:
    institutions = db.scalars(select(Institution).order_by(Institution.name.asc())).all()
    programmes = db.scalars(select(Programme).where(Programme.status == "ACTIVE")).all()
    institution_types = db.execute(
        select(Institution.institution_type, func.count(Institution.id))
        .group_by(Institution.institution_type)
        .order_by(Institution.institution_type.asc())
    ).all()
    batch_statuses = db.execute(
        select(SubmissionBatch.status, func.count(SubmissionBatch.id))
        .group_by(SubmissionBatch.status)
        .order_by(SubmissionBatch.status.asc())
    ).all()
    current_filter = (
        StudentEnrollment.is_current.is_(True),
        StudentEnrollment.academic_year == academic_year,
    )
    total_enrolments = int(
        db.scalar(select(func.count(StudentEnrollment.id)).where(*current_filter)) or 0
    )
    active_enrolments = int(
        db.scalar(
            select(func.count(StudentEnrollment.id)).where(
                *current_filter,
                StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE.value,
            )
        )
        or 0
    )
    reporting = []
    for institution in institutions:
        count = int(
            db.scalar(
                select(func.count(StudentEnrollment.id)).where(
                    *current_filter,
                    StudentEnrollment.institution_id == institution.id,
                )
            )
            or 0
        )
        batches = int(
            db.scalar(
                select(func.count(SubmissionBatch.id)).where(
                    SubmissionBatch.institution_id == institution.id,
                    SubmissionBatch.academic_year == academic_year,
                )
            )
            or 0
        )
        reporting.append(
            {
                "institutionId": institution.id,
                "institutionName": institution.name,
                "institutionType": institution.institution_type,
                "enrollmentCount": count,
                "batchCount": batches,
                "reportingStatus": "REPORTING" if batches else "NOT_REPORTING",
            }
        )
    excess: list[DashboardCapacityRow] = []
    for programme in programmes:
        result = calculate_capacity(db, programme.id, academic_year)
        if result.status != CapacityStatus.POSSIBLE_EXCESS.value:
            continue
        excess.append(
            DashboardCapacityRow(
                programme_id=programme.id,
                programme_code=programme.programme_code,
                programme_name=programme.programme_name,
                campus_name=None,
                approved_regular=int(
                    result.allocations.get(SeatClassification.APPROVED_REGULAR.value, 0)
                ),
                approved_supernumerary=int(
                    result.allocations.get(SeatClassification.APPROVED_SUPERNUMERARY.value, 0)
                ),
                reported_regular=int(result.evidence.get("regularReported", 0)),
                reported_supernumerary=int(result.evidence.get("supernumeraryReported", 0)),
                reported_total=result.reported,
                status=result.status,
                evidence=result.evidence,
            )
        )
    open_cases = int(
        db.scalar(
            select(func.count(DuplicateCase.id)).where(
                DuplicateCase.status.in_(list(_OPEN_CASE_STATES))
            )
        )
        or 0
    )
    return NationalDashboard(
        academic_year=academic_year,
        generated_at=datetime.now(UTC).replace(tzinfo=None),
        data_freshness="Computed from current synthetic records at request time.",
        kpis=[
            KpiOut(
                key="institutions_reporting",
                label="Institutions reporting",
                value=sum(item["batchCount"] > 0 for item in reporting),
            ),
            KpiOut(key="total_enrolments", label="Current enrolments", value=total_enrolments),
            KpiOut(key="active_enrolments", label="Active enrolments", value=active_enrolments),
            KpiOut(
                key="under_review",
                label="Batches under review",
                value=(
                    batch_statuses
                    and sum(
                        int(count)
                        for status, count in batch_statuses
                        if status == BatchStatus.UNDER_AICTE_REVIEW.value
                    )
                )
                or 0,
            ),
            KpiOut(
                key="possible_excess",
                label="Possible excess programmes",
                value=len(excess),
                tone="warning" if excess else "success",
            ),
            KpiOut(
                key="open_cases",
                label="Open cases",
                value=open_cases,
                tone="warning" if open_cases else "success",
            ),
            KpiOut(
                key="reported_institutions",
                label="Configured institutions",
                value=len(institutions),
            ),
            KpiOut(
                key="batches",
                label="Submission batches",
                value=sum(int(count) for _, count in batch_statuses),
            ),
        ],
        institution_type_distribution=[
            DistributionRow(key=key, label=key.replace("_", " ").title(), count=int(count))
            for key, count in institution_types
        ],
        batch_status_distribution=[
            DistributionRow(key=key, label=key.replace("_", " ").title(), count=int(count))
            for key, count in batch_statuses
        ],
        possible_excess_programmes=excess,
        reporting_institutions=reporting,
    )
