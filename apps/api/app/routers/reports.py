"""Role-scoped aggregate reports and audited CSV exports."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.constants import (
    CURRENT_ACADEMIC_YEAR,
    INSTITUTION_STAFF_ROLES,
    INSTITUTION_TRAVERSAL_ROLES,
)
from app.db import get_db
from app.deps import CurrentUser
from app.errors import forbidden, validation_error
from app.models.ops import ReportExport
from app.schemas.report import DataQualityReport, IntakeReconciliationReport, ReportEnvelope
from app.services.reports import (
    data_quality_report,
    enrollment_report,
    intake_reconciliation_report,
    safe_csv_cell,
)

router = APIRouter(prefix="/reports", tags=["reports"])
_NATIONAL = set(INSTITUTION_TRAVERSAL_ROLES) | {"AICTE_ANALYST"}


def _scope(user: CurrentUser, requested: str | None) -> tuple[str | None, bool]:
    roles = set(user.roles)
    if user.institution_id and roles & set(INSTITUTION_STAFF_ROLES):
        if requested and requested != user.institution_id:
            raise forbidden("Institution reports are tenant scoped")
        return user.institution_id, False
    if roles & _NATIONAL:
        analyst = "AICTE_ANALYST" in roles and not roles & {
            "AICTE_REVIEWER",
            "AICTE_SUPERVISOR",
            "SYSTEM_ADMIN",
            "AUDITOR",
        }
        return requested, analyst
    raise forbidden("Report access is not available to this role")


@router.get("/enrolment", response_model=ReportEnvelope)
def enrolment_report_route(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
    institution_id: Annotated[str | None, Query(alias="institutionId")] = None,
    programme_id: Annotated[str | None, Query(alias="programmeId")] = None,
    group_by: Annotated[str, Query(alias="groupBy")] = "programme",
) -> ReportEnvelope:
    if group_by not in {"programme", "institution"}:
        raise validation_error("groupBy must be programme or institution")
    institution_id, analyst = _scope(user, institution_id)
    return ReportEnvelope(
        **enrollment_report(
            db,
            academic_year=academic_year,
            institution_id=institution_id,
            programme_id=programme_id,
            group_by=group_by,
            suppress_threshold=5 if analyst else None,
        )
    )


@router.get("/intake-reconciliation", response_model=IntakeReconciliationReport)
def intake_report_route(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
    institution_id: Annotated[str | None, Query(alias="institutionId")] = None,
    programme_id: Annotated[str | None, Query(alias="programmeId")] = None,
) -> IntakeReconciliationReport:
    institution_id, analyst = _scope(user, institution_id)
    return IntakeReconciliationReport(
        **intake_reconciliation_report(
            db,
            academic_year=academic_year,
            institution_id=institution_id,
            programme_id=programme_id,
            suppress_threshold=5 if analyst else None,
        )
    )


@router.get("/data-quality", response_model=DataQualityReport)
def quality_report_route(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
    institution_id: Annotated[str | None, Query(alias="institutionId")] = None,
) -> DataQualityReport:
    institution_id, analyst = _scope(user, institution_id)
    return DataQualityReport(
        **data_quality_report(
            db,
            academic_year=academic_year,
            institution_id=institution_id,
            suppress_threshold=5 if analyst else None,
        )
    )


def _csv_response(
    db: Session,
    *,
    report_type: str,
    rows: list[dict[str, Any]],
    user: CurrentUser,
    filters: dict[str, Any],
    institution_id: str | None,
    request: Request,
) -> Response:
    fields = sorted({key for row in rows for key in row}) if rows else ["message"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: safe_csv_cell(row.get(field)) for field in fields})
    export = ReportExport(
        report_type=report_type,
        requested_by=user.id,
        requested_role=user.primary_role,
        institution_id=institution_id,
        filters=filters,
        row_count=len(rows),
        format="CSV",
        generated_at=datetime.now(UTC).replace(tzinfo=None),
        contains_direct_identifiers=False,
    )
    db.add(export)
    db.flush()
    record_audit(
        db,
        actor=user,
        action="REPORT_EXPORTED",
        resource_type="report_export",
        resource_ref=export.id,
        institution_id=institution_id,
        metadata={"reportType": report_type, "rowCount": len(rows), "filters": filters},
        request=request,
    )
    db.commit()
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{report_type}.csv"'},
    )


@router.get("/enrolment/export.csv")
def export_enrolment(
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
    institution_id: Annotated[str | None, Query(alias="institutionId")] = None,
    programme_id: Annotated[str | None, Query(alias="programmeId")] = None,
    group_by: Annotated[str, Query(alias="groupBy")] = "programme",
) -> Response:
    if group_by not in {"programme", "institution"}:
        raise validation_error("groupBy must be programme or institution")
    institution_id, analyst = _scope(user, institution_id)
    report = enrollment_report(
        db,
        academic_year=academic_year,
        institution_id=institution_id,
        programme_id=programme_id,
        group_by=group_by,
        suppress_threshold=5 if analyst else None,
    )
    return _csv_response(
        db,
        report_type="enrolment",
        rows=report["items"],
        user=user,
        filters=report["filters"],
        institution_id=institution_id,
        request=request,
    )


@router.get("/{report_type}/export.csv")
def export_other_report(
    report_type: str,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
    institution_id: Annotated[str | None, Query(alias="institutionId")] = None,
) -> Response:
    institution_id, analyst = _scope(user, institution_id)
    if report_type == "intake-reconciliation":
        report = intake_reconciliation_report(
            db,
            academic_year=academic_year,
            institution_id=institution_id,
            programme_id=None,
            suppress_threshold=5 if analyst else None,
        )
    elif report_type == "data-quality":
        report = data_quality_report(
            db,
            academic_year=academic_year,
            institution_id=institution_id,
            suppress_threshold=5 if analyst else None,
        )
    else:
        raise validation_error("Unknown report type")
    return _csv_response(
        db,
        report_type=report_type,
        rows=report["items"],
        user=user,
        filters=report["filters"],
        institution_id=institution_id,
        request=request,
    )
