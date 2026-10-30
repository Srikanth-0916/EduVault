"""Enrollment creation, versioning, batch commit, and identity checks."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.adapters.apaar import get_apaar_provider
from app.errors import conflict, not_found, validation_error
from app.models.base import utc_now
from app.models.enrollment import EnrollmentVersion, StudentEnrollment
from app.models.enums import (
    ApaarProviderOutcome,
    DeclaredStatus,
    EnrollmentStatus,
    IdentityStatus,
    SeatClassification,
)
from app.models.identity import StudentIdentity
from app.models.master import Campus, Programme
from app.models.review import IdentityVerification
from app.schemas.users import UserContext
from app.security import decrypt_apaar, mask_apaar_last4, normalize_apaar
from app.services.apaar import upsert_student_identity, validate_apaar_format
from sqlalchemy import select
from sqlalchemy.orm import Session

_STATUS_BY_OUTCOME = {
    ApaarProviderOutcome.SUCCESS.value: IdentityStatus.EXTERNALLY_CONFIRMED.value,
    ApaarProviderOutcome.MISMATCH.value: IdentityStatus.EXTERNAL_MISMATCH.value,
    ApaarProviderOutcome.NOT_FOUND.value: IdentityStatus.MANUAL_REVIEW.value,
    ApaarProviderOutcome.UNAVAILABLE.value: IdentityStatus.EXTERNAL_UNAVAILABLE.value,
    ApaarProviderOutcome.TIMEOUT.value: IdentityStatus.EXTERNAL_UNAVAILABLE.value,
    ApaarProviderOutcome.UNAUTHORIZED.value: IdentityStatus.EXTERNAL_UNAVAILABLE.value,
    ApaarProviderOutcome.UNSUPPORTED.value: IdentityStatus.MANUAL_REVIEW.value,
}


def _resolve_place(
    db: Session,
    institution_id: str,
    programme_id: str,
    campus_id: str | None,
) -> tuple[Programme, Campus]:
    programme = db.get(Programme, programme_id)
    if programme is None or programme.institution_id != institution_id:
        raise not_found("Programme not found at your institution")
    campus = db.get(Campus, campus_id or programme.campus_id)
    if campus is None or campus.institution_id != institution_id:
        raise not_found("Campus not found at your institution")
    if campus.id != programme.campus_id:
        raise validation_error("The selected campus does not offer this programme")
    return programme, campus


def _validate_data(data: dict[str, Any]) -> None:
    for key in ("admission_date", "exit_date"):
        value = data.get(key)
        if isinstance(value, str):
            if not value:
                data[key] = None
            else:
                try:
                    data[key] = date.fromisoformat(value)
                except ValueError as exc:
                    raise validation_error(
                        "Dates must use YYYY-MM-DD", {"field": key}
                    ) from exc
    admission = data.get("admission_date")
    exit_date = data.get("exit_date")
    if isinstance(admission, date) and isinstance(exit_date, date) and exit_date < admission:
        raise validation_error("Exit date must not be before admission date")
    if data.get("seat_classification") == SeatClassification.APPROVED_SUPERNUMERARY.value:
        if not (data.get("supernumerary_approval_reference") or "").strip():
            raise validation_error(
                "A supernumerary approval reference is required for this seat classification",
                {"field": "approvalReference"},
            )
    if str(data.get("academic_year", "")).count("-") != 1:
        raise validation_error("Academic year must look like 2026-27")


def _snapshot(enrollment: StudentEnrollment, identity: StudentIdentity) -> dict[str, Any]:
    return {
        "studentLocalId": enrollment.student_local_id,
        "studentName": enrollment.student_full_name,
        "maskedApaar": mask_apaar_last4(identity.apaar_last4),
        "identityStatus": identity.identifier_status,
        "programmeId": enrollment.programme_id,
        "campusId": enrollment.campus_id,
        "academicYear": enrollment.academic_year,
        "admissionDate": str(enrollment.admission_date),
        "exitDate": str(enrollment.exit_date) if enrollment.exit_date else None,
        "enrollmentStatus": enrollment.enrollment_status,
        "seatClassification": enrollment.seat_classification,
        "nriStatus": enrollment.nri_status,
        "ociStatus": enrollment.oci_status,
        "foreignNationalStatus": enrollment.foreign_national_status,
        "supernumeraryApprovalReference": enrollment.supernumerary_approval_reference,
        "version": enrollment.version,
        "isCurrent": enrollment.is_current,
    }


def _add_version(
    db: Session,
    enrollment: StudentEnrollment,
    identity: StudentIdentity,
    *,
    actor: UserContext,
    reason: str,
) -> None:
    db.add(
        EnrollmentVersion(
            student_enrollment_id=enrollment.id,
            version=enrollment.version,
            snapshot=_snapshot(enrollment, identity),
            change_reason=reason,
            changed_by=actor.id,
            actor_role=actor.primary_role,
        )
    )


def _current_for_local_id(
    db: Session, institution_id: str, local_id: str, academic_year: str
) -> StudentEnrollment | None:
    return db.scalar(
        select(StudentEnrollment).where(
            StudentEnrollment.institution_id == institution_id,
            StudentEnrollment.student_local_id == local_id,
            StudentEnrollment.academic_year == academic_year,
            StudentEnrollment.is_current.is_(True),
        )
    )


def create_enrollment(
    db: Session,
    *,
    actor: UserContext,
    institution_id: str,
    data: dict[str, Any],
    source_channel: str = "PORTAL",
    source_batch_id: str | None = None,
    source_row_id: str | None = None,
) -> StudentEnrollment:
    """Create a new current enrollment and its first immutable snapshot."""
    _validate_data(data)
    raw = normalize_apaar(data.get("raw_apaar"))
    identity: StudentIdentity
    if data.get("student_identity_id"):
        identity = db.get(StudentIdentity, str(data["student_identity_id"]))  # type: ignore[assignment]
        if identity is None:
            raise not_found("Student identity not found")
    else:
        format_state = validate_apaar_format(raw)
        identity = upsert_student_identity(db, raw, format_state["status"])

    local_id = str(data["student_local_id"]).strip()
    academic_year = str(data["academic_year"]).strip()
    existing = _current_for_local_id(db, institution_id, local_id, academic_year)
    if existing is not None:
        raise conflict(
            "A current enrollment already uses this institution student ID for the academic year"
        )

    programme, campus = _resolve_place(
        db, institution_id, str(data["programme_id"]), data.get("campus_id")
    )
    enrollment = StudentEnrollment(
        student_identity_id=identity.id,
        institution_id=institution_id,
        campus_id=campus.id,
        programme_id=programme.id,
        student_local_id=local_id,
        student_full_name=str(data["student_full_name"]).strip(),
        academic_year=academic_year,
        admission_date=data["admission_date"],
        exit_date=data.get("exit_date"),
        enrollment_status=data.get("enrollment_status")
        or EnrollmentStatus.PENDING.value,
        seat_classification=data.get("seat_classification")
        or SeatClassification.APPROVED_REGULAR.value,
        admission_category=data.get("admission_category"),
        nri_status=data.get("nri_status") or DeclaredStatus.UNKNOWN.value,
        oci_status=data.get("oci_status") or DeclaredStatus.UNKNOWN.value,
        foreign_national_status=data.get("foreign_national_status")
        or DeclaredStatus.UNKNOWN.value,
        supernumerary_approval_reference=data.get("supernumerary_approval_reference"),
        version=1,
        is_current=True,
        source_channel=source_channel,
        source_batch_id=source_batch_id,
        source_row_id=source_row_id,
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.add(enrollment)
    db.flush()
    _add_version(db, enrollment, identity, actor=actor, reason="Initial enrollment")
    db.flush()
    return enrollment


def supersede_enrollment(
    db: Session,
    old: StudentEnrollment,
    *,
    actor: UserContext,
    data: dict[str, Any],
    reason: str,
) -> StudentEnrollment:
    """Create a new current row and keep the old row as immutable history."""
    merged: dict[str, Any] = {
        "student_identity_id": old.student_identity_id,
        "student_local_id": old.student_local_id,
        "student_full_name": old.student_full_name,
        "programme_id": old.programme_id,
        "campus_id": old.campus_id,
        "academic_year": old.academic_year,
        "admission_date": old.admission_date,
        "exit_date": old.exit_date,
        "enrollment_status": old.enrollment_status,
        "seat_classification": old.seat_classification,
        "admission_category": old.admission_category,
        "nri_status": old.nri_status,
        "oci_status": old.oci_status,
        "foreign_national_status": old.foreign_national_status,
        "supernumerary_approval_reference": old.supernumerary_approval_reference,
    }
    merged.update({key: value for key, value in data.items() if value is not None})
    _validate_data(merged)

    if data.get("raw_apaar") is not None:
        raw = normalize_apaar(data["raw_apaar"])
        state = validate_apaar_format(raw)
        identity = upsert_student_identity(db, raw, state["status"])
        merged["student_identity_id"] = identity.id
    else:
        identity = db.get(StudentIdentity, old.student_identity_id)
        if identity is None:
            raise not_found("Student identity not found")

    if merged["student_local_id"] != old.student_local_id or merged[
        "academic_year"
    ] != old.academic_year:
        existing = _current_for_local_id(
            db,
            old.institution_id,
            str(merged["student_local_id"]),
            str(merged["academic_year"]),
        )
        if existing is not None and existing.id != old.id:
            raise conflict("Another current enrollment uses that student ID")

    programme, campus = _resolve_place(
        db, old.institution_id, str(merged["programme_id"]), merged.get("campus_id")
    )
    old.is_current = False
    old.updated_by = actor.id
    db.flush()

    enrollment = StudentEnrollment(
        student_identity_id=identity.id,
        institution_id=old.institution_id,
        campus_id=campus.id,
        programme_id=programme.id,
        student_local_id=str(merged["student_local_id"]),
        student_full_name=str(merged["student_full_name"]),
        academic_year=str(merged["academic_year"]),
        admission_date=merged["admission_date"],
        exit_date=merged.get("exit_date"),
        enrollment_status=str(merged["enrollment_status"]),
        seat_classification=str(merged["seat_classification"]),
        admission_category=merged.get("admission_category"),
        nri_status=str(merged["nri_status"]),
        oci_status=str(merged["oci_status"]),
        foreign_national_status=str(merged["foreign_national_status"]),
        supernumerary_approval_reference=merged.get("supernumerary_approval_reference"),
        version=old.version + 1,
        is_current=True,
        supersedes_id=old.id,
        correction_reason=reason,
        source_channel=old.source_channel,
        source_batch_id=old.source_batch_id,
        source_row_id=old.source_row_id,
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.add(enrollment)
    db.flush()
    _add_version(db, enrollment, identity, actor=actor, reason=reason)
    db.flush()
    return enrollment


def verify_identity(
    db: Session,
    identity: StudentIdentity,
    *,
    actor: UserContext,
    purpose: str = "manual identity check",
) -> IdentityVerification:
    raw = decrypt_apaar(identity.apaar_ciphertext)
    if not raw:
        raise validation_error("There is no valid APAAR value to verify")
    result = get_apaar_provider().verify(raw, purpose, {"actorId": actor.id})
    resulting_status = _STATUS_BY_OUTCOME.get(
        result.outcome, IdentityStatus.MANUAL_REVIEW.value
    )
    identity.identifier_status = resulting_status
    verification = IdentityVerification(
        student_identity_id=identity.id,
        provider="MOCK_APAAR",
        provider_reference=result.reference,
        result=result.outcome,
        adapter_version=result.adapter_version,
        is_mock=True,
        checked_at=result.checked_at.replace(tzinfo=None),
        purpose=purpose,
        consent_context="prototype-demo",
        requested_by=actor.id,
        detail=result.detail,
        resulting_status=resulting_status,
    )
    db.add(verification)
    db.flush()
    return verification


def commit_batch_enrollments(db: Session, batch: Any, actor: UserContext) -> int:
    """Create/version enrollments for non-error rows, without double counting."""
    from app.models.batch import SubmissionBatch, SubmissionRow

    if not isinstance(batch, SubmissionBatch):
        raise TypeError("batch must be a SubmissionBatch")
    rows = db.scalars(
        select(SubmissionRow)
        .where(SubmissionRow.batch_id == batch.id)
        .order_by(SubmissionRow.source_row_number.asc())
    ).all()
    committed = 0
    for row in rows:
        if row.row_status not in {"VALID", "WARNING"}:
            continue
        parsed = dict(row.parsed_data or {})
        if not parsed:
            continue
        old: StudentEnrollment | None = None
        if row.enrollment_id:
            old = db.get(StudentEnrollment, row.enrollment_id)
        if old is None or not old.is_current:
            old = _current_for_local_id(
                db,
                batch.institution_id,
                str(parsed.get("student_local_id", "")),
                str(parsed.get("academic_year", batch.academic_year)),
            )
        parsed["student_identity_id"] = row.student_identity_id
        if old is not None:
            new = supersede_enrollment(
                db,
                old,
                actor=actor,
                data=parsed,
                reason=f"Batch {batch.id} resubmission",
            )
        else:
            new = create_enrollment(
                db,
                actor=actor,
                institution_id=batch.institution_id,
                data=parsed,
                source_channel="CSV_UPLOAD",
                source_batch_id=batch.id,
                source_row_id=row.id,
            )
        row.enrollment_id = new.id
        committed += 1
    db.flush()
    return committed


def mark_batch_accepted(db: Session, batch: Any) -> int:
    """Record AICTE acceptance on current enrollments linked to the batch."""
    from app.models.batch import SubmissionRow

    rows = db.scalars(
        select(SubmissionRow).where(SubmissionRow.batch_id == batch.id)
    ).all()
    accepted = 0
    for row in rows:
        if not row.enrollment_id:
            continue
        enrollment = db.get(StudentEnrollment, row.enrollment_id)
        if enrollment is not None and enrollment.is_current:
            enrollment.record_accepted_at = utc_now()
            accepted += 1
    db.flush()
    return accepted


__all__ = [
    "commit_batch_enrollments",
    "create_enrollment",
    "mark_batch_accepted",
    "supersede_enrollment",
    "verify_identity",
]
