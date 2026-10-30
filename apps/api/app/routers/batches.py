"""CSV submission batch lifecycle: upload, validate, attest, submit, decide."""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.constants import INSTITUTION_STAFF_ROLES
from app.db import get_db
from app.deps import CurrentUser, Pagination
from app.errors import AppError, conflict, forbidden, not_found, validation_error
from app.models.base import utc_now
from app.models.batch import (
    SubmissionBatch,
    SubmissionRow,
    ValidationFinding,
    ValidationRun,
)
from app.models.enums import BatchStatus, RowStatus
from app.models.master import Campus, Programme
from app.schemas.batch import (
    AttestRequest,
    BatchCreate,
    BatchDetail,
    BatchListResponse,
    BatchReceiptOut,
    BatchRowOut,
    BatchSummary,
    DecisionRequest,
    RowPatch,
)
from app.schemas.enrollment import FindingOut
from app.security import sign_receipt
from app.services.csv_import import ALL_HEADERS, parse_csv, prepare_row
from app.services.enrollment import commit_batch_enrollments, mark_batch_accepted
from app.services.notifications import notify_institution_roles, notify_national_roles
from app.services.storage import MAX_UPLOAD_BYTES, save_upload
from app.services.validation import run_validation

router = APIRouter(prefix="/submission-batches", tags=["submission-batches"])
template_router = APIRouter(tags=["submission-batches"])

_NATIONAL_READ = {"AICTE_REVIEWER", "AICTE_SUPERVISOR", "SYSTEM_ADMIN", "AUDITOR"}
_NATIONAL_DECIDE = {"AICTE_REVIEWER", "AICTE_SUPERVISOR", "SYSTEM_ADMIN"}
_NATIONAL_NOTIFY = {"AICTE_REVIEWER", "AICTE_SUPERVISOR"}


def _latest_run(db: Session, batch_id: str) -> ValidationRun | None:
    return db.scalar(
        select(ValidationRun)
        .where(ValidationRun.batch_id == batch_id)
        .order_by(ValidationRun.started_at.desc())
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


def _summary_out(db: Session, batch: SubmissionBatch) -> BatchSummary:
    run = _latest_run(db, batch.id)
    return BatchSummary(
        id=batch.id,
        institution_id=batch.institution_id,
        campus_id=batch.campus_id,
        programme_id=batch.programme_id,
        academic_year=batch.academic_year,
        source_type=batch.source_type,
        status=batch.status,
        version=batch.version,
        supersedes_batch_id=batch.supersedes_batch_id,
        file_name=batch.file_name,
        file_checksum=batch.file_checksum,
        file_size_bytes=batch.file_size_bytes,
        row_count=batch.row_count,
        summary=run.summary if run and run.summary else {},
        created_at=batch.created_at,
        attested_at=batch.attested_at,
        submitted_at=batch.submitted_at,
        decision=batch.decision,
        decision_reason=batch.decision_reason,
        decision_reason_code=batch.decision_reason_code,
        decided_at=batch.decided_at,
        decision_history=batch.decision_history or [],
    )


def _detail_out(db: Session, batch: SubmissionBatch) -> BatchDetail:
    summary = _summary_out(db, batch)
    run = _latest_run(db, batch.id)
    rows = db.scalars(
        select(SubmissionRow)
        .where(SubmissionRow.batch_id == batch.id)
        .order_by(SubmissionRow.source_row_number.asc())
    ).all()
    findings = (
        db.scalars(
            select(ValidationFinding)
            .where(ValidationFinding.validation_run_id == run.id)
            .order_by(ValidationFinding.created_at.asc())
        ).all()
        if run
        else []
    )
    by_row: dict[str, list[ValidationFinding]] = defaultdict(list)
    for finding in findings:
        if finding.row_id:
            by_row[finding.row_id].append(finding)
    row_outs = [
        BatchRowOut(
            id=row.id,
            source_row_number=row.source_row_number,
            student_name=row.student_name,
            student_local_id=row.student_local_id,
            masked_apaar=str(
                (row.raw_data or {}).get("apaarMasked")
                or (f"••••••••{row.apaar_last4}" if row.apaar_last4 else "••••••••••••")
            ),
            row_status=row.row_status,
            enrollment_id=row.enrollment_id,
            findings=[_finding_out(item) for item in by_row[row.id]],
        )
        for row in rows
    ]
    return BatchDetail(
        **summary.model_dump(),
        rows=row_outs,
        findings=[_finding_out(item) for item in findings],
        validation_run_id=run.id if run else None,
        validation_summary=run.summary if run else None,
    )


def _get_batch(db: Session, batch_id: str) -> SubmissionBatch:
    batch = db.get(SubmissionBatch, batch_id)
    if batch is None:
        raise not_found("Submission batch not found")
    return batch


def _assert_read(user: CurrentUser, batch: SubmissionBatch) -> None:
    if user.institution_id and user.institution_id == batch.institution_id:
        return
    if set(user.roles) & (_NATIONAL_READ | {"AICTE_ANALYST"}):
        if "AICTE_ANALYST" in user.roles and not set(user.roles) & _NATIONAL_READ:
            raise forbidden("Analysts receive aggregate reports")
        return
    raise forbidden()


def _assert_institution_staff(user: CurrentUser, batch: SubmissionBatch) -> None:
    if user.institution_id != batch.institution_id:
        raise forbidden()
    if not set(user.roles) & set(INSTITUTION_STAFF_ROLES):
        raise forbidden()


def _assert_nodal(user: CurrentUser, batch: SubmissionBatch) -> None:
    if user.institution_id != batch.institution_id:
        raise forbidden()
    if "INSTITUTION_NODAL_OFFICER" not in user.roles:
        raise forbidden("Only a nodal officer can attest or submit this batch")


def _template_bytes() -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(ALL_HEADERS)
    writer.writerow(
        [
            "AIT2026CSE001",
            "123456789012",
            "Synthetic Student One",
            "CSE",
            "AIT-MAIN",
            "2026-27",
            "2026-07-15",
            "",
            "ACTIVE",
            "APPROVED_REGULAR",
            "GENERAL",
            "NO",
            "NO",
            "NO",
            "",
            "2007-04-18",
            "FEMALE",
        ]
    )
    return output.getvalue().encode("utf-8")


@router.get("", response_model=BatchListResponse)
def list_batches(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    pagination: Pagination,
    academic_year: Annotated[str | None, Query(alias="academicYear")] = None,
    status: Annotated[str | None, Query()] = None,
) -> BatchListResponse:
    if not user.institution_id and not set(user.roles) & (_NATIONAL_READ | {"AICTE_ANALYST"}):
        raise forbidden()
    statement = select(SubmissionBatch)
    count_statement = select(func.count(SubmissionBatch.id))
    if user.institution_id:
        statement = statement.where(SubmissionBatch.institution_id == user.institution_id)
        count_statement = count_statement.where(
            SubmissionBatch.institution_id == user.institution_id
        )
    if academic_year:
        statement = statement.where(SubmissionBatch.academic_year == academic_year)
        count_statement = count_statement.where(
            SubmissionBatch.academic_year == academic_year
        )
    if status:
        statement = statement.where(SubmissionBatch.status == status)
        count_statement = count_statement.where(SubmissionBatch.status == status)
    page, page_size = pagination
    total = int(db.scalar(count_statement) or 0)
    batches = db.scalars(
        statement.order_by(SubmissionBatch.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return BatchListResponse(
        items=[_summary_out(db, batch) for batch in batches],
        total=total,
    )


@router.post("", response_model=BatchDetail, status_code=201)
def create_batch(
    payload: BatchCreate,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BatchDetail:
    if not user.institution_id:
        raise forbidden()
    if not set(user.roles) & set(INSTITUTION_STAFF_ROLES):
        raise forbidden()
    if payload.campus_id:
        campus = db.get(Campus, payload.campus_id)
        if campus is None or campus.institution_id != user.institution_id:
            raise not_found("Campus not found at your institution")
    if payload.programme_id:
        programme = db.get(Programme, payload.programme_id)
        if programme is None or programme.institution_id != user.institution_id:
            raise not_found("Programme not found at your institution")

    batch = SubmissionBatch(
        institution_id=user.institution_id,
        campus_id=payload.campus_id,
        programme_id=payload.programme_id,
        academic_year=payload.academic_year,
        source_type=payload.source_type,
        status=BatchStatus.DRAFT.value,
        version=1,
        created_by=user.id,
    )
    db.add(batch)
    db.flush()
    record_audit(
        db,
        actor=user,
        action="SUBMISSION_BATCH_CREATED",
        resource_type="submission_batch",
        resource_ref=batch.id,
        institution_id=user.institution_id,
        metadata={"academicYear": batch.academic_year},
        request=request,
    )
    db.commit()
    return _detail_out(db, batch)


@router.post("/{batch_id}/file", response_model=BatchDetail)
async def upload_batch_file(
    batch_id: str,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File()],
) -> BatchDetail:
    batch = _get_batch(db, batch_id)
    _assert_institution_staff(user, batch)
    if batch.status not in {
        BatchStatus.DRAFT.value,
        BatchStatus.VALIDATION_FAILED.value,
        BatchStatus.RETURNED_FOR_CORRECTION.value,
    }:
        raise conflict("This batch can no longer be replaced")
    existing_rows = db.scalars(
        select(SubmissionRow).where(SubmissionRow.batch_id == batch.id)
    ).all()
    if any(row.enrollment_id for row in existing_rows):
        raise conflict("This batch already has committed enrollments; use a new batch")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise AppError(413, "FILE_TOO_LARGE", "CSV uploads are limited to 5 MB")
    parsed = parse_csv(content)
    if parsed.errors:
        raise AppError(
            422,
            "CSV_PARSE_ERROR",
            "The CSV could not be accepted",
            {"errors": parsed.errors},
        )

    db.execute(delete(ValidationFinding).where(ValidationFinding.batch_id == batch.id))
    db.execute(delete(ValidationRun).where(ValidationRun.batch_id == batch.id))
    db.execute(delete(SubmissionRow).where(SubmissionRow.batch_id == batch.id))
    db.flush()

    storage_key, checksum, size = save_upload(content, batch.id)
    batch.file_name = Path(file.filename or "upload.csv").name
    batch.file_storage_key = storage_key
    batch.file_checksum = checksum
    batch.file_size_bytes = size
    batch.row_count = len(parsed.rows)
    batch.status = BatchStatus.DRAFT.value
    batch.source_type = "CSV_UPLOAD"

    for parsed_row in parsed.rows:
        values = parsed_row["data"]
        safe = prepare_row(values)
        db.add(
            SubmissionRow(
                batch_id=batch.id,
                source_row_number=int(parsed_row["row_number"]),
                student_name=str(values.get("student_name") or "").strip() or None,
                student_local_id=str(values.get("institution_student_id") or "").strip()
                or None,
                apaar_last4=str(safe.get("apaarLast4") or "") or None,
                row_status=RowStatus.PENDING.value,
                raw_data=safe,
            )
        )
    record_audit(
        db,
        actor=user,
        action="SUBMISSION_BATCH_FILE_UPLOADED",
        resource_type="submission_batch",
        resource_ref=batch.id,
        institution_id=batch.institution_id,
        metadata={"rowCount": len(parsed.rows), "checksum": checksum, "bytes": size},
        request=request,
    )
    db.commit()
    return _detail_out(db, batch)


@router.get("/{batch_id}", response_model=BatchDetail)
def get_batch(
    batch_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BatchDetail:
    batch = _get_batch(db, batch_id)
    _assert_read(user, batch)
    return _detail_out(db, batch)


@router.get("/{batch_id}/results", response_model=BatchDetail)
def get_batch_results(
    batch_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BatchDetail:
    return get_batch(batch_id, user, db)


@router.post("/{batch_id}/validate", response_model=BatchDetail)
def validate_batch(
    batch_id: str,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BatchDetail:
    batch = _get_batch(db, batch_id)
    _assert_institution_staff(user, batch)
    if batch.status == BatchStatus.UNDER_AICTE_REVIEW.value:
        raise conflict("A batch under AICTE review cannot be revalidated")
    if not db.scalar(
        select(func.count(SubmissionRow.id)).where(SubmissionRow.batch_id == batch.id)
    ):
        raise conflict("Upload a CSV before running validation")
    run = run_validation(db, batch, user)
    record_audit(
        db,
        actor=user,
        action="SUBMISSION_BATCH_VALIDATED",
        resource_type="submission_batch",
        resource_ref=batch.id,
        institution_id=batch.institution_id,
        metadata={"runId": run.id, "status": batch.status, "summary": run.summary},
        request=request,
    )
    db.commit()
    return _detail_out(db, batch)


@router.patch("/{batch_id}/rows/{row_id}", response_model=BatchDetail)
def patch_batch_row(
    batch_id: str,
    row_id: str,
    payload: RowPatch,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BatchDetail:
    batch = _get_batch(db, batch_id)
    _assert_institution_staff(user, batch)
    if batch.status not in {
        BatchStatus.DRAFT.value,
        BatchStatus.VALIDATION_FAILED.value,
        BatchStatus.RETURNED_FOR_CORRECTION.value,
    }:
        raise conflict("Rows are editable only before submission or after a return")
    row = db.get(SubmissionRow, row_id)
    if row is None or row.batch_id != batch.id:
        raise not_found("Batch row not found")

    safe = dict(row.raw_data or {})
    mapping = {
        "student_name": "student_name",
        "student_local_id": "institution_student_id",
        "programme_code": "programme_code",
        "campus_code": "campus_code",
        "academic_year": "academic_year",
        "admission_date": "admission_date",
        "exit_date": "exit_date",
        "enrollment_status": "enrollment_status",
        "seat_classification": "seat_classification",
        "admission_category": "admission_category",
        "nri_status": "nri_status",
        "oci_status": "oci_status",
        "foreign_national_status": "foreign_national_status",
        "approval_reference": "approval_reference",
    }
    updates = payload.model_dump(exclude_unset=True)
    for model_field, csv_field in mapping.items():
        if model_field in updates:
            safe[csv_field] = updates[model_field] or ""
    if "apaar_id" in updates and updates["apaar_id"] is not None:
        for key in ("apaarIdCiphertext", "apaarStatus", "apaarMasked", "apaarLast4"):
            safe.pop(key, None)
        source = {header: str(safe.get(header, "")) for header in ALL_HEADERS}
        source["apaar_id"] = str(updates["apaar_id"])
        prepared = prepare_row(source)
        for key in ("apaarIdCiphertext", "apaarStatus", "apaarMasked", "apaarLast4"):
            safe.pop(key, None)
        safe.update(
            {key: value for key, value in prepared.items() if key.startswith("apaar")}
        )
    row.raw_data = safe
    row.student_name = str(safe.get("student_name") or "") or None
    row.student_local_id = str(safe.get("institution_student_id") or "") or None
    row.apaar_last4 = str(safe.get("apaarLast4") or "") or None
    row.row_status = RowStatus.PENDING.value
    row.parsed_data = None
    batch.status = BatchStatus.DRAFT.value
    record_audit(
        db,
        actor=user,
        action="SUBMISSION_BATCH_ROW_EDITED",
        resource_type="submission_batch_row",
        resource_ref=row.id,
        institution_id=batch.institution_id,
        metadata={"batchId": batch.id, "fields": sorted(updates.keys())},
        request=request,
    )
    db.commit()
    return _detail_out(db, batch)


@router.post("/{batch_id}/attest", response_model=BatchDetail)
def attest_batch(
    batch_id: str,
    payload: AttestRequest,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BatchDetail:
    batch = _get_batch(db, batch_id)
    _assert_nodal(user, batch)
    if batch.status != BatchStatus.READY_FOR_ATTESTATION.value:
        raise conflict("Only a validated, error-free batch can be attested")
    if not payload.declaration:
        raise validation_error("The nodal declaration must be accepted")
    run = _latest_run(db, batch.id)
    if run is None or int((run.summary or {}).get("errorRows", 0)) > 0:
        raise conflict("Blocking validation errors must be corrected first")
    batch.attested_at = utc_now()
    batch.attested_by = user.id
    batch.attestation_name = payload.attestation_name
    batch.declaration_accepted = True
    record_audit(
        db,
        actor=user,
        action="SUBMISSION_BATCH_ATTESTED",
        resource_type="submission_batch",
        resource_ref=batch.id,
        institution_id=batch.institution_id,
        metadata={"attestationName": payload.attestation_name},
        request=request,
    )
    db.commit()
    return _detail_out(db, batch)


@router.post("/{batch_id}/submit", response_model=BatchDetail)
def submit_batch(
    batch_id: str,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BatchDetail:
    batch = _get_batch(db, batch_id)
    _assert_nodal(user, batch)
    if batch.status != BatchStatus.READY_FOR_ATTESTATION.value:
        raise conflict("The batch is not ready for submission")
    if not batch.attested_at:
        raise conflict("Nodal attestation is required before submission")
    run = _latest_run(db, batch.id)
    if run is None or int((run.summary or {}).get("errorRows", 0)) > 0:
        raise conflict("Blocking validation errors must be corrected first")

    if batch.submitted_at:
        batch.version += 1
    committed = commit_batch_enrollments(db, batch, user)
    batch.status = BatchStatus.UNDER_AICTE_REVIEW.value
    batch.submitted_at = utc_now()
    batch.submitted_by = user.id
    batch.decision = None
    batch.decision_reason = None
    batch.decision_reason_code = None
    batch.decided_at = None
    notify_national_roles(
        db,
        roles=_NATIONAL_NOTIFY,
        event_type="BATCH_SUBMITTED",
        title="A new submission is ready for review",
        body=(
            f"Batch {batch.id} has been submitted with "
            f"{batched_count(batch)} row(s) and is awaiting a decision."
        ),
        resource_type="submission_batch",
        resource_ref=batch.id,
    )
    record_audit(
        db,
        actor=user,
        action="SUBMISSION_BATCH_SUBMITTED",
        resource_type="submission_batch",
        resource_ref=batch.id,
        institution_id=batch.institution_id,
        metadata={"version": batch.version, "committedRows": committed},
        request=request,
    )
    db.commit()
    return _detail_out(db, batch)


def batched_count(batch: SubmissionBatch) -> int:
    return int(batch.row_count or 0)


@router.post("/{batch_id}/decision", response_model=BatchDetail)
def decide_batch(
    batch_id: str,
    payload: DecisionRequest,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BatchDetail:
    if not set(user.roles) & _NATIONAL_DECIDE:
        raise forbidden()
    batch = _get_batch(db, batch_id)
    if batch.status != BatchStatus.UNDER_AICTE_REVIEW.value:
        raise conflict("Only a batch under AICTE review can be decided")
    status_by_decision = {
        "ACCEPT": BatchStatus.ACCEPTED.value,
        "RETURN": BatchStatus.RETURNED_FOR_CORRECTION.value,
        "REJECT": BatchStatus.REJECTED.value,
    }
    batch.decision = payload.decision
    batch.decision_reason = payload.reason
    batch.decision_reason_code = payload.reason_code
    batch.decided_at = utc_now()
    batch.decided_by = user.id
    batch.status = status_by_decision[payload.decision]
    history = list(batch.decision_history or [])
    history.append(
        {
            "decision": payload.decision,
            "reason": payload.reason,
            "reasonCode": payload.reason_code,
            "decidedBy": user.id,
            "decidedAt": batch.decided_at.isoformat(),
        }
    )
    batch.decision_history = history
    if payload.decision == "ACCEPT":
        mark_batch_accepted(db, batch)
    notify_institution_roles(
        db,
        institution_id=batch.institution_id,
        roles=INSTITUTION_STAFF_ROLES,
        event_type=f"BATCH_{payload.decision}",
        title=f"Submission {payload.decision.lower()}ed",
        body=f"Batch {batch.id} was {payload.decision.lower()}ed. {payload.reason}",
        resource_type="submission_batch",
        resource_ref=batch.id,
    )
    record_audit(
        db,
        actor=user,
        action=f"SUBMISSION_BATCH_{payload.decision}",
        resource_type="submission_batch",
        resource_ref=batch.id,
        institution_id=batch.institution_id,
        reason=payload.reason,
        metadata={"reasonCode": payload.reason_code},
        request=request,
    )
    db.commit()
    return _detail_out(db, batch)


@router.get("/{batch_id}/receipt", response_model=BatchReceiptOut)
def batch_receipt(
    batch_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BatchReceiptOut:
    batch = _get_batch(db, batch_id)
    _assert_read(user, batch)
    if not batch.file_checksum or not batch.submitted_at:
        raise conflict("A receipt is available only after submission")
    payload: dict[str, Any] = {
        "batchId": batch.id,
        "institutionId": batch.institution_id,
        "academicYear": batch.academic_year,
        "version": batch.version,
        "checksum": batch.file_checksum,
        "rowCount": batch.row_count,
        "status": batch.status,
        "submittedBy": batch.submitted_by,
        "submittedAt": str(batch.submitted_at),
        "decision": batch.decision,
    }
    return BatchReceiptOut(
        batch_id=batch.id,
        checksum=batch.file_checksum,
        row_count=int(batch.row_count or 0),
        submitted_by=batch.submitted_by,
        submitted_at=batch.submitted_at,
        payload=payload,
        signature=sign_receipt(payload),
    )


@template_router.get("/template.csv")
def download_template() -> Response:
    return Response(
        content=_template_bytes(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="apaar-submission-template.csv"'},
    )
