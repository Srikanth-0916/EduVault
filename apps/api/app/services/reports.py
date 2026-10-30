"""Aggregate-first reports and safe CSV export rows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models.batch import SubmissionBatch, ValidationFinding
from app.models.enrollment import StudentEnrollment
from app.models.enums import EnrollmentStatus, SeatClassification
from app.models.identity import StudentIdentity
from app.models.master import Campus, Institution, Programme
from app.models.review import DuplicateCase
from app.services.capacity import calculate_capacity
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _freshness() -> str:
    return "Computed from current synthetic records at request time."


def _count_case(status: str):
    return func.sum(case((StudentEnrollment.enrollment_status == status, 1), else_=0))


def enrollment_report(
    db: Session,
    *,
    academic_year: str,
    institution_id: str | None,
    programme_id: str | None,
    group_by: str,
    suppress_threshold: int | None,
) -> dict[str, Any]:
    columns = [
        Institution.id.label("institution_id"),
        Institution.name.label("institution_name"),
        func.count(StudentEnrollment.id).label("total"),
        _count_case(EnrollmentStatus.ACTIVE.value).label("active"),
        func.sum(
            case(
                (
                    StudentEnrollment.seat_classification
                    == SeatClassification.APPROVED_REGULAR.value,
                    1,
                ),
                else_=0,
            )
        ).label("regular"),
        func.sum(
            case(
                (
                    StudentEnrollment.seat_classification
                    == SeatClassification.APPROVED_SUPERNUMERARY.value,
                    1,
                ),
                else_=0,
            )
        ).label("supernumerary"),
    ]
    if group_by != "institution":
        columns.extend(
            [
                Programme.id.label("programme_id"),
                Programme.programme_code.label("programme_code"),
                Programme.programme_name.label("programme_name"),
            ]
        )
    statement = (
        select(*columns)
        .select_from(StudentEnrollment)
        .join(Institution, Institution.id == StudentEnrollment.institution_id)
        .join(Programme, Programme.id == StudentEnrollment.programme_id)
        .where(
            StudentEnrollment.is_current.is_(True),
            StudentEnrollment.academic_year == academic_year,
        )
    )
    if institution_id:
        statement = statement.where(StudentEnrollment.institution_id == institution_id)
    if programme_id:
        statement = statement.where(StudentEnrollment.programme_id == programme_id)
    if group_by == "institution":
        statement = statement.group_by(Institution.id, Institution.name).order_by(
            Institution.name.asc()
        )
    else:
        group_by = "programme"
        statement = statement.group_by(
            Institution.id,
            Institution.name,
            Programme.id,
            Programme.programme_code,
            Programme.programme_name,
        ).order_by(Programme.programme_code.asc())

    rows = db.execute(statement).all()
    items: list[dict[str, Any]] = []
    suppressed = 0
    for row in rows:
        total = int(row.total or 0)
        if suppress_threshold is not None and total < suppress_threshold:
            suppressed += 1
            items.append(
                {
                    "groupKey": "SUPPRESSED",
                    "groupLabel": "Suppressed group",
                    "count": None,
                    "suppressed": True,
                }
            )
            continue
        if group_by == "institution":
            key = row.institution_id
            label = row.institution_name
        else:
            key = row.programme_id
            label = f"{row.programme_code} — {row.programme_name}"
        item = {
            "groupKey": key,
            "groupLabel": label,
            "institutionName": row.institution_name,
            "count": total,
            "activeCount": int(row.active or 0),
            "regularCount": int(row.regular or 0),
            "supernumeraryCount": int(row.supernumerary or 0),
            "suppressed": False,
        }
        if group_by == "programme":
            item["programmeCode"] = row.programme_code
        items.append(item)
    return {
        "generatedAt": _now(),
        "filters": {
            "academicYear": academic_year,
            "institutionId": institution_id,
            "programmeId": programme_id,
            "groupBy": group_by,
        },
        "dataFreshness": _freshness(),
        "suppressedGroups": suppressed,
        "items": items,
    }


def intake_reconciliation_report(
    db: Session,
    *,
    academic_year: str,
    institution_id: str | None,
    programme_id: str | None,
    suppress_threshold: int | None = None,
) -> dict[str, Any]:
    statement = select(Programme).order_by(Programme.programme_code.asc())
    if institution_id:
        statement = statement.where(Programme.institution_id == institution_id)
    if programme_id:
        statement = statement.where(Programme.id == programme_id)
    programmes = db.scalars(statement).all()
    campuses = {campus.id: campus.name for campus in db.scalars(select(Campus)).all()}
    items: list[dict[str, Any]] = []
    suppressed = 0
    for programme in programmes:
        capacity = calculate_capacity(db, programme.id, academic_year)
        reported_total = int(capacity.evidence.get("regularReported", 0)) + int(
            capacity.evidence.get("supernumeraryReported", 0)
        )
        if suppress_threshold is not None and reported_total < suppress_threshold:
            suppressed += 1
            items.append(
                {
                    "groupLabel": "Suppressed group",
                    "suppressed": True,
                    "reportedTotal": None,
                }
            )
            continue
        items.append(
            {
                "programmeId": programme.id,
                "programmeCode": programme.programme_code,
                "programmeName": programme.programme_name,
                "campusName": campuses.get(programme.campus_id),
                "approvedRegular": capacity.allocations.get(
                    SeatClassification.APPROVED_REGULAR.value, 0
                ),
                "approvedSupernumerary": capacity.allocations.get(
                    SeatClassification.APPROVED_SUPERNUMERARY.value, 0
                ),
                "reportedRegular": capacity.evidence.get("regularReported", 0),
                "reportedSupernumerary": capacity.evidence.get("supernumeraryReported", 0),
                "reportedTotal": reported_total,
                "status": capacity.status,
                "evidence": capacity.evidence,
                "suppressed": False,
            }
        )
    return {
        "generatedAt": _now(),
        "filters": {
            "academicYear": academic_year,
            "institutionId": institution_id,
            "programmeId": programme_id,
        },
        "dataFreshness": _freshness(),
        "suppressedGroups": suppressed,
        "items": items,
    }


def data_quality_report(
    db: Session,
    *,
    academic_year: str,
    institution_id: str | None,
    suppress_threshold: int | None = None,
) -> dict[str, Any]:
    enrollment_filter = [
        StudentEnrollment.is_current.is_(True),
        StudentEnrollment.academic_year == academic_year,
    ]
    if institution_id:
        enrollment_filter.append(StudentEnrollment.institution_id == institution_id)
    identity_rows = db.execute(
        select(StudentIdentity.identifier_status, func.count(StudentEnrollment.id))
        .join(StudentIdentity, StudentIdentity.id == StudentEnrollment.student_identity_id)
        .where(*enrollment_filter)
        .group_by(StudentIdentity.identifier_status)
    ).all()
    finding_statement = (
        select(
            ValidationFinding.rule_id,
            ValidationFinding.severity,
            func.count(ValidationFinding.id),
        )
        .join(SubmissionBatch, SubmissionBatch.id == ValidationFinding.batch_id)
        .where(SubmissionBatch.academic_year == academic_year)
    )
    if institution_id:
        finding_statement = finding_statement.where(
            SubmissionBatch.institution_id == institution_id
        )
    findings = db.execute(
        finding_statement.group_by(ValidationFinding.rule_id, ValidationFinding.severity).order_by(
            ValidationFinding.rule_id.asc()
        )
    ).all()
    case_filter = [DuplicateCase.status.in_(["OPEN", "IN_REVIEW"])]
    if institution_id:
        case_filter.append(DuplicateCase.institution_id == institution_id)
    open_cases = int(db.scalar(select(func.count(DuplicateCase.id)).where(*case_filter)) or 0)
    items: list[dict[str, Any]] = []
    suppressed = 0
    for status, count_value in identity_rows:
        count = int(count_value)
        if suppress_threshold is not None and count < suppress_threshold:
            suppressed += 1
            items.append(
                {
                    "section": "identityStatus",
                    "label": "Suppressed group",
                    "count": None,
                    "suppressed": True,
                }
            )
        else:
            items.append(
                {
                    "section": "identityStatus",
                    "status": status,
                    "count": count,
                    "label": status.replace("_", " ").title(),
                    "suppressed": False,
                }
            )
    for rule, severity, count_value in findings:
        count = int(count_value)
        if suppress_threshold is not None and count < suppress_threshold:
            suppressed += 1
            items.append(
                {
                    "section": "finding",
                    "label": "Suppressed group",
                    "count": None,
                    "suppressed": True,
                }
            )
        else:
            items.append(
                {
                    "section": "finding",
                    "ruleId": rule,
                    "severity": severity,
                    "count": count,
                    "suppressed": False,
                }
            )
    if suppress_threshold is not None and open_cases < suppress_threshold:
        suppressed += 1
        items.append(
            {
                "section": "cases",
                "label": "Suppressed group",
                "count": None,
                "suppressed": True,
            }
        )
    else:
        items.append(
            {
                "section": "cases",
                "status": "OPEN_OR_IN_REVIEW",
                "count": open_cases,
                "suppressed": False,
            }
        )
    return {
        "generatedAt": _now(),
        "filters": {"academicYear": academic_year, "institutionId": institution_id},
        "dataFreshness": _freshness(),
        "suppressedGroups": suppressed,
        "items": items,
    }


def safe_csv_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text
