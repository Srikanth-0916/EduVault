"""Batch validation rules, duplicate detection, capacity, and summaries.

Rule IDs are stable API contract values. Findings contain masked identifiers
only; raw APAAR values exist only transiently inside this service.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from app.constants import INSTITUTION_STAFF_ROLES
from app.models.base import utc_now
from app.models.batch import (
    SubmissionBatch,
    SubmissionRow,
    ValidationFinding,
    ValidationRun,
)
from app.models.enrollment import StudentEnrollment
from app.models.enums import (
    BatchStatus,
    DeclaredStatus,
    DuplicateMatchType,
    EnrollmentStatus,
    FindingStatus,
    IdentityStatus,
    RowStatus,
    SeatClassification,
    Severity,
    ValidationRunStatus,
)
from app.models.identity import StudentIdentity
from app.models.master import Campus, Institution, Programme
from app.schemas.users import UserContext
from app.security import apaar_lookup_token, decrypt_apaar, mask_apaar, mask_apaar_last4
from app.services.apaar import upsert_student_identity, validate_apaar_format
from app.services.capacity import calculate_capacity
from app.services.duplicates import create_case_for_match, date_overlap_days
from app.services.enrollment import verify_identity
from app.services.notifications import notify_institution_roles
from sqlalchemy import select
from sqlalchemy.orm import Session

_SEVERITY_RANK = {item.value: index for index, item in enumerate(Severity)}


def _row_raw(row: SubmissionRow) -> str | None:
    safe = row.raw_data or {}
    ciphertext = safe.get("apaarIdCiphertext")
    if ciphertext:
        return decrypt_apaar(str(ciphertext))
    # Fallback for direct service tests; the API never persists plaintext.
    fallback = safe.get("apaar_id")
    return str(fallback) if fallback else None


def _masked_for(row: SubmissionRow) -> str:
    safe = row.raw_data or {}
    masked = safe.get("apaarMasked")
    if masked:
        return str(masked)
    return mask_apaar_last4(row.apaar_last4)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _as_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return _parse_date(value)
    return None


def _add_finding(
    db: Session,
    *,
    run: ValidationRun,
    batch: SubmissionBatch,
    row: SubmissionRow | None,
    rule_id: str,
    code: str,
    severity: str,
    blocking: bool,
    message: str,
    field: str | None = None,
    evidence: dict[str, Any] | None = None,
    findings: list[ValidationFinding],
    row_findings: dict[str, list[ValidationFinding]],
    row_errors: set[str],
) -> ValidationFinding:
    finding = ValidationFinding(
        validation_run_id=run.id,
        batch_id=batch.id,
        row_id=row.id if row else None,
        record_id=row.id if row else None,
        rule_id=rule_id,
        code=code,
        severity=severity,
        blocking=blocking,
        message=message,
        field=field,
        status=FindingStatus.OPEN.value,
        evidence=evidence,
    )
    db.add(finding)
    findings.append(finding)
    if row is not None:
        row_findings[row.id].append(finding)
        if blocking:
            row_errors.add(row.id)
    return finding


def run_validation(db: Session, batch: SubmissionBatch, actor: UserContext) -> ValidationRun:
    """Validate every row, create findings/cases, and set the batch state."""
    started = utc_now()
    run = ValidationRun(
        batch_id=batch.id,
        rule_set_version="2026.1",
        status=ValidationRunStatus.RUNNING.value,
        started_at=started,
        requested_by=actor.id,
    )
    db.add(run)
    db.flush()

    rows = db.scalars(
        select(SubmissionRow)
        .where(SubmissionRow.batch_id == batch.id)
        .order_by(SubmissionRow.source_row_number.asc())
    ).all()
    if not rows:
        run.status = ValidationRunStatus.COMPLETED.value
        run.completed_at = utc_now()
        run.summary = {"totalRows": 0, "errorRows": 1, "message": "No rows uploaded"}
        batch.status = BatchStatus.VALIDATION_FAILED.value
        db.flush()
        return run

    programmes = db.scalars(
        select(Programme).where(Programme.institution_id == batch.institution_id)
    ).all()
    programme_by_code = {programme.programme_code.upper(): programme for programme in programmes}
    campuses = db.scalars(
        select(Campus).where(Campus.institution_id == batch.institution_id)
    ).all()
    campus_by_code = {campus.campus_code.upper(): campus for campus in campuses}

    findings: list[ValidationFinding] = []
    row_findings: dict[str, list[ValidationFinding]] = defaultdict(list)
    row_errors: set[str] = set()
    row_values: dict[str, dict[str, Any]] = {}
    identity_cache: dict[str, StudentIdentity] = {}
    verified_ids: set[str] = set()
    token_rows: dict[str, list[SubmissionRow]] = defaultdict(list)

    for row in rows:
        raw = _row_raw(row)
        safe = row.raw_data or {}
        values = dict(safe)
        row_values[row.id] = values
        format_state = validate_apaar_format(raw)
        if raw is None and safe.get("apaarStatus") == IdentityStatus.MALFORMED.value:
            format_state = {
                "status": IdentityStatus.MALFORMED.value,
                "message": "APAAR ID must be exactly 12 digits",
            }

        identity: StudentIdentity | None = None
        if format_state["status"] == IdentityStatus.FORMAT_VALID.value and raw:
            identity = upsert_student_identity(
                db, raw, IdentityStatus.FORMAT_VALID.value
            )
            identity_cache[identity.id] = identity
            token_rows[apaar_lookup_token(raw)].append(row)
        else:
            existing = (
                db.get(StudentIdentity, row.student_identity_id)
                if row.student_identity_id
                else None
            )
            if existing is not None and existing.apaar_lookup_token is None:
                identity = existing
            else:
                identity = upsert_student_identity(db, raw, format_state["status"])
            identity.identifier_status = format_state["status"]
        row.student_identity_id = identity.id if identity else None
        row.apaar_last4 = identity.apaar_last4 if identity else None
        row.student_name = str(values.get("student_name") or "").strip() or None
        row.student_local_id = str(values.get("institution_student_id") or "").strip() or None

        if format_state["status"] == IdentityStatus.MISSING.value:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-001",
                code="APAAR_MISSING",
                severity=Severity.CRITICAL.value,
                blocking=True,
                message="APAAR ID is required for this student record",
                field="apaarId",
                evidence={"valueMasked": "••••••••••••", "status": "MISSING"},
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )
        elif format_state["status"] == IdentityStatus.MALFORMED.value:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-002",
                code="APAAR_INVALID_FORMAT",
                severity=Severity.HIGH.value,
                blocking=True,
                message="APAAR ID must be exactly 12 digits",
                field="apaarId",
                evidence={
                    "valueMasked": mask_apaar(raw),
                    "status": "MALFORMED",
                },
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )

        if not row.student_name:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-013",
                code="STUDENT_NAME_REQUIRED",
                severity=Severity.HIGH.value,
                blocking=True,
                message="Student name is required",
                field="studentName",
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )
        if not row.student_local_id:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-014",
                code="STUDENT_LOCAL_ID_REQUIRED",
                severity=Severity.HIGH.value,
                blocking=True,
                message="Institution student ID is required",
                field="institutionStudentId",
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )

        programme = programme_by_code.get(
            str(values.get("programme_code") or "").upper()
        )
        campus = campus_by_code.get(str(values.get("campus_code") or "").upper())
        if programme is None:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-007",
                code="UNMAPPED_PROGRAMME",
                severity=Severity.HIGH.value,
                blocking=True,
                message="Programme code is not mapped at your institution",
                field="programmeCode",
                evidence={"programmeCode": values.get("programme_code", "")},
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )
        if campus is None:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-007",
                code="UNMAPPED_CAMPUS",
                severity=Severity.HIGH.value,
                blocking=True,
                message="Campus code is not mapped at your institution",
                field="campusCode",
                evidence={"campusCode": values.get("campus_code", "")},
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )
        if (
            programme is not None
            and campus is not None
            and campus.id != programme.campus_id
        ):
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-007",
                code="CAMPUS_PROGRAMME_MISMATCH",
                severity=Severity.HIGH.value,
                blocking=True,
                message="The selected campus does not offer this programme",
                field="programmeCode",
                evidence={
                    "programmeCode": programme.programme_code,
                    "campusCode": campus.campus_code,
                },
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )

        academic_year = str(values.get("academic_year") or batch.academic_year)
        if academic_year != batch.academic_year:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-011",
                code="ACADEMIC_YEAR_MISMATCH",
                severity=Severity.HIGH.value,
                blocking=True,
                message="The row academic year does not match the batch",
                field="academicYear",
                evidence={"batchYear": batch.academic_year, "rowYear": academic_year},
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )

        admission = _parse_date(str(values.get("admission_date") or ""))
        exit_date = _parse_date(str(values.get("exit_date") or ""))
        if admission is None:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-006",
                code="INVALID_ADMISSION_DATE",
                severity=Severity.HIGH.value,
                blocking=True,
                message="Admission date is missing or invalid (use YYYY-MM-DD)",
                field="admissionDate",
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )
        if values.get("exit_date") and exit_date is None:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-006",
                code="INVALID_EXIT_DATE",
                severity=Severity.HIGH.value,
                blocking=True,
                message="Exit date is not a valid date (use YYYY-MM-DD)",
                field="exitDate",
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )
        if admission and exit_date and exit_date < admission:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-006",
                code="INVALID_DATE_ORDER",
                severity=Severity.HIGH.value,
                blocking=True,
                message="Exit date must not be before admission date",
                field="exitDate",
                evidence={
                    "admissionDate": str(admission),
                    "exitDate": str(exit_date),
                },
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )

        enrollment_status = str(values.get("enrollment_status") or "PENDING").upper()
        seat_classification = str(
            values.get("seat_classification") or SeatClassification.APPROVED_REGULAR.value
        ).upper()
        statuses = {item.value for item in EnrollmentStatus}
        seat_classes = {item.value for item in SeatClassification}
        if enrollment_status not in statuses:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-012",
                code="INVALID_ENROLLMENT_STATUS",
                severity=Severity.HIGH.value,
                blocking=True,
                message="Unknown enrollment status",
                field="enrollmentStatus",
                evidence={"value": enrollment_status},
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )
        if seat_classification not in seat_classes:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-012",
                code="INVALID_SEAT_CLASSIFICATION",
                severity=Severity.HIGH.value,
                blocking=True,
                message="Unknown seat classification",
                field="seatClassification",
                evidence={"value": seat_classification},
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )

        tri = {}
        for field, key in (
            ("nri_status", "nriStatus"),
            ("oci_status", "ociStatus"),
            ("foreign_national_status", "foreignNationalStatus"),
        ):
            value = str(values.get(field) or DeclaredStatus.UNKNOWN.value).upper()
            if value not in {item.value for item in DeclaredStatus}:
                value = DeclaredStatus.UNKNOWN.value
                _add_finding(
                    db,
                    run=run,
                    batch=batch,
                    row=row,
                    rule_id="BR-010",
                    code="ATTRIBUTE_POLICY_REVIEW",
                    severity=Severity.WARNING.value,
                    blocking=False,
                    message="An attribute value was blank or invalid; it was treated as UNKNOWN",
                    field=key,
                    findings=findings,
                    row_findings=row_findings,
                    row_errors=row_errors,
                )
            tri[key] = value

        super_ref = str(values.get("approval_reference") or "").strip() or None
        if (
            seat_classification == SeatClassification.APPROVED_SUPERNUMERARY.value
            and not super_ref
        ):
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-009",
                code="SUPERNUMERARY_REFERENCE_REQUIRED",
                severity=Severity.HIGH.value,
                blocking=True,
                message="A supernumerary approval reference is required",
                field="approvalReference",
                evidence={"seatClassification": seat_classification},
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )

        if (
            tri["nriStatus"] == "YES"
            or tri["ociStatus"] == "YES"
            or tri["foreignNationalStatus"] == "YES"
        ):
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-010",
                code="ATTRIBUTE_POLICY_REVIEW",
                severity=Severity.INFO.value,
                blocking=False,
                message=(
                    "NRI/OCI/foreign-national attributes are present; "
                    "confirm the applicable policy"
                ),
                field="nriStatus",
                evidence={
                    "nriStatus": tri["nriStatus"],
                    "ociStatus": tri["ociStatus"],
                    "foreignNationalStatus": tri["foreignNationalStatus"],
                    "seatClassification": seat_classification,
                },
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )

        if identity is not None and format_state["status"] == "FORMAT_VALID":
            if identity.id not in identity_cache:
                identity_cache[identity.id] = identity
            if identity.id not in verified_ids:
                verified_ids.add(identity.id)
                try:
                    verify_identity(
                        db, identity, actor=actor, purpose="batch validation"
                    )
                except Exception:
                    # External verification is advisory; a provider failure must
                    # not block the batch. The unavailable state is visible.
                    identity.identifier_status = IdentityStatus.EXTERNAL_UNAVAILABLE.value

        row.parsed_data = {
            "student_local_id": row.student_local_id,
            "student_full_name": row.student_name,
            "programme_id": programme.id if programme else None,
            "campus_id": campus.id if campus else None,
            "academic_year": academic_year,
            "admission_date": str(admission) if admission else None,
            "exit_date": str(exit_date) if exit_date else None,
            "enrollment_status": enrollment_status,
            "seat_classification": seat_classification,
            "admission_category": values.get("admission_category") or None,
            "nri_status": tri["nriStatus"],
            "oci_status": tri["ociStatus"],
            "foreign_national_status": tri["foreignNationalStatus"],
            "supernumerary_approval_reference": super_ref,
            "programme_code": programme.programme_code if programme else None,
            "campus_code": campus.campus_code if campus else None,
            "masked_apaar": _masked_for(row),
        }

    # Within-batch duplicates.
    for token, duplicate_rows in token_rows.items():
        if len(duplicate_rows) < 2:
            continue
        row_numbers = [item.source_row_number for item in duplicate_rows]
        for row in duplicate_rows:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-003",
                code="DUPLICATE_IN_BATCH",
                severity=Severity.HIGH.value,
                blocking=True,
                message="The same APAAR identifier appears more than once in this batch",
                field="apaarId",
                evidence={
                    "valueMasked": _masked_for(row),
                    "rowNumbers": row_numbers,
                    "matchKey": token[:12],
                },
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )
        create_case_for_match(
            db,
            match_type=DuplicateMatchType.WITHIN_BATCH.value,
            severity=Severity.HIGH.value,
            match_key=token[:32],
            discovered_batch_id=batch.id,
            institution_id=batch.institution_id,
            evidence={
                "matchType": "WITHIN_BATCH",
                "maskedIdentifiers": [_masked_for(item) for item in duplicate_rows],
                "rowNumbers": row_numbers,
                "statusContext": "Duplicate identifier staged in one batch",
            },
        )

    # Existing enrollment matches (same institution and cross-institution).
    identity_ids = [identity.id for identity in identity_cache.values()]
    existing_by_identity: dict[str, list[StudentEnrollment]] = defaultdict(list)
    if identity_ids:
        existing = db.scalars(
            select(StudentEnrollment).where(
                StudentEnrollment.student_identity_id.in_(identity_ids),
                StudentEnrollment.is_current.is_(True),
            )
        ).all()
        for enrollment in existing:
            existing_by_identity[enrollment.student_identity_id].append(enrollment)
    institution_names = {
        institution.id: institution.name
        for institution in db.scalars(select(Institution)).all()
    }

    for row in rows:
        if not row.student_identity_id:
            continue
        identity = identity_cache.get(row.student_identity_id)
        if identity is None:
            identity = db.get(StudentIdentity, row.student_identity_id)
        if identity is None:
            continue
        parsed = row.parsed_data or {}
        admission = _as_date(parsed.get("admission_date"))
        exit_date = _as_date(parsed.get("exit_date"))
        for other in existing_by_identity.get(identity.id, []):
            if (
                other.institution_id == batch.institution_id
                and other.student_local_id == row.student_local_id
                and other.academic_year == parsed.get("academic_year")
            ):
                continue
            overlap = date_overlap_days(
                admission,
                exit_date,
                other.admission_date,
                other.exit_date,
            )
            same_institution = other.institution_id == batch.institution_id
            match_type = (
                DuplicateMatchType.SAME_INSTITUTION.value
                if same_institution
                else DuplicateMatchType.CROSS_INSTITUTION.value
            )
            severity = Severity.HIGH.value if overlap else Severity.LOW.value
            blocking = bool(overlap)
            evidence = {
                "matchType": match_type,
                "maskedIdentifier": mask_apaar_last4(identity.apaar_last4),
                "existingEnrollmentId": other.id,
                "existingLocalId": other.student_local_id,
                "institutionName": institution_names.get(other.institution_id),
                "admissionDate": str(other.admission_date),
                "exitDate": str(other.exit_date) if other.exit_date else None,
                "overlapDays": overlap,
                "transferContext": "NON_OVERLAPPING" if not overlap else "OVERLAP",
                "statusContext": other.enrollment_status,
                "rowNumber": row.source_row_number,
            }
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-004" if same_institution else "BR-005",
                code=(
                    "DUPLICATE_SAME_INSTITUTION"
                    if same_institution
                    else "POSSIBLE_CROSS_INSTITUTION_OVERLAP"
                ),
                severity=severity,
                blocking=blocking,
                message=(
                    "This identifier already has a current enrolment at your institution"
                    if same_institution
                    else "This identifier has an enrolment at another institution; review the dates"
                ),
                field="apaarId",
                evidence=evidence,
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )
            create_case_for_match(
                db,
                match_type=match_type,
                severity=severity,
                primary_enrollment_id=other.id,
                institution_id=batch.institution_id,
                discovered_batch_id=batch.id,
                evidence=evidence,
            )

    # Capacity: projected counts include valid/warning rows not yet committed.
    capacity_groups: dict[tuple[str, str, str], list[SubmissionRow]] = defaultdict(list)
    for row in rows:
        if row.id in row_errors:
            continue
        parsed = row.parsed_data or {}
        if not parsed.get("programme_id"):
            continue
        key = (
            str(parsed["programme_id"]),
            str(parsed.get("academic_year") or batch.academic_year),
            str(parsed.get("seat_classification") or ""),
        )
        capacity_groups[key].append(row)

    for (programme_id, academic_year, seat_classification), group_rows in capacity_groups.items():
        capacity = calculate_capacity(db, programme_id, academic_year)
        approved = capacity.allocations.get(seat_classification, 0)
        if approved <= 0:
            continue
        existing_reported = (
            int(capacity.evidence.get("regularReported", 0))
            if seat_classification == SeatClassification.APPROVED_REGULAR.value
            else int(capacity.evidence.get("supernumeraryReported", 0))
        )
        projected = existing_reported + len(group_rows)
        if projected <= approved:
            continue
        for row in group_rows:
            _add_finding(
                db,
                run=run,
                batch=batch,
                row=row,
                rule_id="BR-008",
                code="POSSIBLE_INTAKE_EXCESS",
                severity=Severity.WARNING.value,
                blocking=False,
                message=(
                    "Projected reported enrolment exceeds the approved allocation "
                    "for this seat classification; review before submission"
                ),
                field="seatClassification",
                evidence={
                    "programmeId": programme_id,
                    "academicYear": academic_year,
                    "seatClassification": seat_classification,
                    "approved": approved,
                    "existingReported": existing_reported,
                    "batchRows": len(group_rows),
                    "projected": projected,
                },
                findings=findings,
                row_findings=row_findings,
                row_errors=row_errors,
            )

    for row in rows:
        if row.id in row_errors:
            row.row_status = RowStatus.ERROR.value
        elif row_findings[row.id]:
            row.row_status = RowStatus.WARNING.value
        else:
            row.row_status = RowStatus.VALID.value

    error_rows = sum(1 for row in rows if row.row_status == RowStatus.ERROR.value)
    warning_rows = sum(1 for row in rows if row.row_status == RowStatus.WARNING.value)
    valid_rows = sum(1 for row in rows if row.row_status == RowStatus.VALID.value)
    blocking_count = sum(1 for finding in findings if finding.blocking)
    by_rule: dict[str, int] = defaultdict(int)
    for finding in findings:
        by_rule[finding.rule_id] += 1

    summary = {
        "totalRows": len(rows),
        "validRows": valid_rows,
        "warningRows": warning_rows,
        "errorRows": error_rows,
        "blockingFindings": blocking_count,
        "findings": len(findings),
        "byRule": dict(sorted(by_rule.items())),
        "caseCount": len(
            {
                finding.evidence.get("existingEnrollmentId")
                for finding in findings
                if finding.evidence and finding.evidence.get("existingEnrollmentId")
            }
        ),
    }
    run.status = ValidationRunStatus.COMPLETED.value
    run.completed_at = utc_now()
    run.duration_ms = int((run.completed_at - started).total_seconds() * 1000)
    run.summary = summary
    batch.row_count = len(rows)
    batch.status = (
        BatchStatus.VALIDATION_FAILED.value
        if error_rows
        else BatchStatus.READY_FOR_ATTESTATION.value
    )
    db.flush()

    if error_rows:
        notify_institution_roles(
            db,
            institution_id=batch.institution_id,
            roles=INSTITUTION_STAFF_ROLES,
            event_type="BATCH_VALIDATION_FAILED",
            title="Submission needs correction",
            body=(
                f"Batch {batch.id} has {error_rows} row(s) with blocking errors. "
                "Open the batch results to review the rule evidence."
            ),
            resource_type="submission_batch",
            resource_ref=batch.id,
            extra_recipients=[batch.created_by],
        )
    db.flush()
    return run
