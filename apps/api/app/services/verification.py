"""Consent-scoped verification token lifecycle and disclosure building."""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import timedelta
from typing import Any

from app.audit import record_audit
from app.errors import AppError, conflict, forbidden, not_found
from app.models.base import utc_now
from app.models.enrollment import StudentEnrollment
from app.models.enums import (
    AttemptDenialReason,
    AttemptOutcome,
    ConsentStatus,
    VerificationClaim,
    VerificationRequestStatus,
)
from app.models.identity import StudentIdentity
from app.models.master import Institution, Programme
from app.models.verification import (
    ConsentGrant,
    VerificationAttempt,
    VerificationReceipt,
    VerificationRequest,
)
from app.schemas.users import UserContext
from app.schemas.verification import (
    AuthorizeResponse,
    PublicVerificationResponse,
    StudentMeResponse,
    VerificationClaimOut,
    VerificationReceiptOut,
    VerificationRequestCreate,
    VerificationRequestOut,
)
from app.security import mask_apaar_last4, sign_receipt
from sqlalchemy import select
from sqlalchemy.orm import Session

_DEMO_NOTICE = (
    "Synthetic prototype disclosure. APAAR external status, where shown, is "
    "mock/sandbox only and not live government verification."
)


def _request_out(request: VerificationRequest) -> VerificationRequestOut:
    claims = list((request.requested_claims or {}).get("claims", []))
    return VerificationRequestOut(
        id=request.id,
        recipient_name=request.recipient_name,
        recipient_org=request.recipient_org,
        recipient_email=request.recipient_email,
        purpose=request.purpose,
        requested_claims=claims,
        legal_basis=request.legal_basis,
        expires_in_hours=request.expires_in_hours,
        status=request.status,
        single_use=request.single_use,
        issued_at=request.issued_at,
        expires_at=request.expires_at,
        viewed_at=request.viewed_at,
        revoked_at=request.revoked_at,
        revoked_reason=request.revoked_reason,
        created_at=request.created_at,
    )


def _receipt_out(receipt: VerificationReceipt) -> VerificationReceiptOut:
    return VerificationReceiptOut(
        id=receipt.id,
        payload=receipt.payload,
        signature=receipt.signature,
        key_id=receipt.key_id,
        issued_at=receipt.issued_at,
        expires_at=receipt.expires_at,
    )


def _hash_claims(claims: list[dict[str, Any]]) -> str:
    body = json.dumps(claims, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def _receipt(
    db: Session,
    request: VerificationRequest,
    *,
    claims: list[dict[str, Any]],
    expires_at,
) -> VerificationReceipt:
    issued_at = utc_now()
    payload = {
        "requestId": request.id,
        "claimsHash": _hash_claims(claims),
        "issuedAt": issued_at.isoformat(),
        "expiresAt": expires_at.isoformat(),
        "subjectRef": request.student_identity_id,
        "keyId": "primary",
    }
    signature = sign_receipt(payload)["signature"]
    receipt = VerificationReceipt(
        verification_request_id=request.id,
        claims_hash=payload["claimsHash"],
        payload=payload,
        signature=signature,
        key_id="primary",
        issued_at=issued_at,
        expires_at=expires_at,
    )
    db.add(receipt)
    db.flush()
    return receipt


def create_request(
    db: Session, user: UserContext, payload: VerificationRequestCreate
) -> VerificationRequest:
    if "STUDENT" not in user.roles or not user.student_identity_id:
        raise forbidden("Only a student can create a verification request")
    request = VerificationRequest(
        subject_user_id=user.id,
        student_identity_id=user.student_identity_id,
        created_by=user.id,
        recipient_name=payload.recipient_name,
        recipient_org=payload.recipient_org,
        recipient_email=str(payload.recipient_email),
        purpose=payload.purpose,
        requested_claims={"claims": payload.requested_claims},
        legal_basis=payload.legal_basis,
        expires_in_hours=payload.expires_in_hours,
        status=VerificationRequestStatus.PENDING_AUTHORIZATION.value,
        single_use=payload.single_use,
    )
    db.add(request)
    db.flush()
    return request


def _get_request(db: Session, request_id: str) -> VerificationRequest:
    request = db.get(VerificationRequest, request_id)
    if request is None:
        raise not_found("Verification request not found")
    return request


def _assert_subject(request: VerificationRequest, user: UserContext) -> None:
    if request.subject_user_id != user.id:
        raise forbidden()


def authorize_request(
    db: Session, request: VerificationRequest, user: UserContext, base_url: str
) -> AuthorizeResponse:
    _assert_subject(request, user)
    if request.status == VerificationRequestStatus.REVOKED.value:
        raise conflict("A revoked request cannot issue a link")
    if request.status not in {
        VerificationRequestStatus.PENDING_AUTHORIZATION.value,
        VerificationRequestStatus.AUTHORIZED.value,
    }:
        raise conflict("This request cannot issue a link in its current state")
    now = utc_now()
    if (
        request.status == VerificationRequestStatus.AUTHORIZED.value
        and request.expires_at
        and request.expires_at > now
    ):
        token = None
    else:
        token = secrets.token_urlsafe(32)
        request.token_hash = hashlib.sha256(token.encode()).hexdigest()
        request.token_jti = secrets.token_urlsafe(24)
        request.issued_at = now
        request.expires_at = now + timedelta(hours=request.expires_in_hours)
        request.status = VerificationRequestStatus.AUTHORIZED.value
        grant = ConsentGrant(
            subject_user_id=request.subject_user_id,
            student_identity_id=request.student_identity_id,
            verification_request_id=request.id,
            recipient_name=request.recipient_name,
            recipient_org=request.recipient_org,
            recipient_email=request.recipient_email,
            purpose=request.purpose,
            fields_scope=request.requested_claims,
            legal_basis=request.legal_basis,
            notice_version="2026-1",
            single_use=request.single_use,
            status=ConsentStatus.ACTIVE.value,
            granted_at=now,
            expires_at=request.expires_at,
        )
        db.add(grant)
    db.flush()
    # A link is returned only on the authorization call. Re-issuing a link for
    # an already-authorized request requires the explicit issue-link endpoint.
    if token is None:
        raise conflict("This request is already authorized; use issue-link")
    receipt = _receipt(db, request, claims=[], expires_at=request.expires_at)
    return AuthorizeResponse(
        request=_request_out(request),
        token=token,
        verify_url=f"{base_url.rstrip('/')}/api/v1/public/verify/{token}",
        expires_at=request.expires_at,
        receipt=_receipt_out(receipt),
    )


def issue_link(
    db: Session, request: VerificationRequest, user: UserContext, base_url: str
) -> AuthorizeResponse:
    _assert_subject(request, user)
    if request.status == VerificationRequestStatus.REVOKED.value:
        raise conflict("A revoked request cannot issue a link")
    request.status = VerificationRequestStatus.PENDING_AUTHORIZATION.value
    return authorize_request(db, request, user, base_url)


def revoke_request(
    db: Session, request: VerificationRequest, user: UserContext, reason: str
) -> VerificationRequest:
    if request.subject_user_id != user.id and not set(user.roles) & {
        "AICTE_SUPERVISOR",
        "SYSTEM_ADMIN",
    }:
        raise forbidden()
    if request.status == VerificationRequestStatus.REVOKED.value:
        return request
    request.status = VerificationRequestStatus.REVOKED.value
    request.revoked_at = utc_now()
    request.revoked_reason = reason
    grants = db.scalars(
        select(ConsentGrant).where(ConsentGrant.verification_request_id == request.id)
    ).all()
    for grant in grants:
        grant.status = ConsentStatus.REVOKED.value
        grant.revoked_at = request.revoked_at
    db.flush()
    return request


def list_requests(
    db: Session, user: UserContext, scope: str | None, status: str | None
) -> list[VerificationRequest]:
    statement = select(VerificationRequest).order_by(VerificationRequest.created_at.desc())
    if scope == "all" and set(user.roles) & {"AICTE_SUPERVISOR", "SYSTEM_ADMIN", "AUDITOR"}:
        pass
    else:
        statement = statement.where(VerificationRequest.subject_user_id == user.id)
    if status:
        statement = statement.where(VerificationRequest.status == status)
    return list(db.scalars(statement).all())


def _current_enrollment(db: Session, identity_id: str) -> StudentEnrollment | None:
    return db.scalar(
        select(StudentEnrollment)
        .where(
            StudentEnrollment.student_identity_id == identity_id,
            StudentEnrollment.is_current.is_(True),
        )
        .order_by(StudentEnrollment.record_accepted_at.desc().nullslast())
    )


def _build_claims(db: Session, request: VerificationRequest) -> list[dict[str, Any]]:
    identity = db.get(StudentIdentity, request.student_identity_id)
    enrollment = _current_enrollment(db, request.student_identity_id)
    if identity is None or enrollment is None:
        raise conflict("No current record is available for disclosure")
    institution = db.get(Institution, enrollment.institution_id)
    programme = db.get(Programme, enrollment.programme_id)
    as_of = enrollment.updated_at or utc_now()
    claim_map: dict[str, dict[str, Any]] = {
        VerificationClaim.INSTITUTION.value: {
            "key": "INSTITUTION",
            "label": "Institution",
            "value": institution.name if institution else "Institution submitted",
            "source": "Institution-submitted",
            "status": "SUBMITTED",
        },
        VerificationClaim.PROGRAMME.value: {
            "key": "PROGRAMME",
            "label": "Programme",
            "value": programme.programme_name if programme else "Programme submitted",
            "source": "Institution-submitted",
            "status": "SUBMITTED",
        },
        VerificationClaim.ACADEMIC_YEAR.value: {
            "key": "ACADEMIC_YEAR",
            "label": "Academic year",
            "value": enrollment.academic_year,
            "source": "Institution-submitted",
            "status": "SUBMITTED",
        },
        VerificationClaim.ENROLMENT_STATUS.value: {
            "key": "ENROLMENT_STATUS",
            "label": "Enrolment status",
            "value": enrollment.enrollment_status,
            "source": "Institution-submitted",
            "status": "CURRENT",
        },
        VerificationClaim.RECORD_ACCEPTANCE.value: {
            "key": "RECORD_ACCEPTANCE",
            "label": "AICTE acceptance",
            "value": "Accepted" if enrollment.record_accepted_at else "Not accepted",
            "source": "AICTE workflow",
            "status": "ACCEPTED" if enrollment.record_accepted_at else "NOT_ACCEPTED",
        },
        VerificationClaim.APAAR_FORMAT_STATUS.value: {
            "key": "APAAR_FORMAT_STATUS",
            "label": "APAAR format status",
            "value": identity.identifier_status,
            "source": "Format check",
            "status": "FORMAT_CHECK",
        },
        VerificationClaim.APAAR_EXTERNAL_STATUS.value: {
            "key": "APAAR_EXTERNAL_STATUS",
            "label": "APAAR external status",
            "value": identity.identifier_status,
            "source": "MOCK_APAAR",
            "status": "MOCK",
        },
    }
    claims: list[dict[str, Any]] = []
    requested = list((request.requested_claims or {}).get("claims", []))
    for key in requested:
        claim = dict(claim_map[key])
        claim["asOf"] = as_of.isoformat()
        claims.append(claim)
    return claims


def resolve_public(
    db: Session, token: str, *, request_meta: dict[str, str | None]
) -> PublicVerificationResponse:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    request = db.scalar(
        select(VerificationRequest).where(VerificationRequest.token_hash == token_hash)
    )
    if request is None:
        db.add(
            VerificationAttempt(
                verification_request_id=None,
                outcome=AttemptOutcome.DENIED.value,
                denial_reason=AttemptDenialReason.MALFORMED.value,
                ip_address=request_meta.get("ipAddress"),
                user_agent=request_meta.get("userAgent"),
                trace_id=request_meta.get("traceId"),
            )
        )
        record_audit(
            db,
            action="PUBLIC_VERIFICATION_DENIED",
            resource_type="verification_request",
            resource_ref="unresolved",
            reason=AttemptDenialReason.MALFORMED.value,
            metadata={"tokenHashPrefix": token_hash[:12]},
        )
        db.commit()
        raise AppError(410, "VERIFICATION_UNAVAILABLE", "Verification link is unavailable")
    now = utc_now()
    denial: AttemptDenialReason | None = None
    if request.status == VerificationRequestStatus.REVOKED.value:
        denial = AttemptDenialReason.REVOKED
    elif request.expires_at is None or request.expires_at <= now:
        request.status = VerificationRequestStatus.EXPIRED.value
        denial = AttemptDenialReason.EXPIRED
    elif request.single_use and request.status in {
        VerificationRequestStatus.CONSUMED.value,
        VerificationRequestStatus.VIEWED.value,
    }:
        denial = AttemptDenialReason.CONSUMED
    if denial is not None:
        attempt = VerificationAttempt(
            verification_request_id=request.id,
            outcome=AttemptOutcome.DENIED.value,
            denial_reason=denial.value,
            ip_address=request_meta.get("ipAddress"),
            user_agent=request_meta.get("userAgent"),
            trace_id=request_meta.get("traceId"),
        )
        db.add(attempt)
        record_audit(
            db,
            action="PUBLIC_VERIFICATION_DENIED",
            resource_type="verification_request",
            resource_ref=request.id,
            reason=denial.value,
            metadata={"tokenHashPrefix": token_hash[:12]},
        )
        db.commit()
        raise AppError(410, "VERIFICATION_UNAVAILABLE", "Verification link is unavailable")
    claims = _build_claims(db, request)
    expires_at = request.expires_at
    receipt = _receipt(db, request, claims=claims, expires_at=expires_at)
    attempt = VerificationAttempt(
        verification_request_id=request.id,
        outcome=AttemptOutcome.SUCCESS.value,
        claims_disclosed={"keys": [claim["key"] for claim in claims]},
        ip_address=request_meta.get("ipAddress"),
        user_agent=request_meta.get("userAgent"),
        trace_id=request_meta.get("traceId"),
        receipt_id=receipt.id,
    )
    db.add(attempt)
    request.viewed_at = now
    request.status = (
        VerificationRequestStatus.CONSUMED.value
        if request.single_use
        else VerificationRequestStatus.VIEWED.value
    )
    db.commit()
    out_claims = [VerificationClaimOut(**claim) for claim in claims]
    return PublicVerificationResponse(
        valid=True,
        claims=out_claims,
        receipt=_receipt_out(receipt),
        expires_at=expires_at,
        demo_notice=_DEMO_NOTICE,
    )


def student_me(db: Session, user: UserContext) -> StudentMeResponse:
    if "STUDENT" not in user.roles or not user.student_identity_id:
        raise forbidden("Student access is required")
    identity = db.get(StudentIdentity, user.student_identity_id)
    if identity is None:
        raise not_found("Student identity not found")
    enrollments = db.scalars(
        select(StudentEnrollment)
        .where(
            StudentEnrollment.student_identity_id == identity.id,
            StudentEnrollment.is_current.is_(True),
        )
        .order_by(StudentEnrollment.academic_year.desc())
    ).all()
    requests = list_requests(db, user, "mine", None)
    return StudentMeResponse(
        masked_apaar=mask_apaar_last4(identity.apaar_last4),
        identity_status=identity.identifier_status,
        identity_last4=identity.apaar_last4,
        enrollments=[
            {
                "id": enrollment.id,
                "institutionId": enrollment.institution_id,
                "programmeId": enrollment.programme_id,
                "academicYear": enrollment.academic_year,
                "enrollmentStatus": enrollment.enrollment_status,
                "seatClassification": enrollment.seat_classification,
                "recordAccepted": bool(enrollment.record_accepted_at),
            }
            for enrollment in enrollments
        ],
        verification_requests=[_request_out(item) for item in requests],
    )
