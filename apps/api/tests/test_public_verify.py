"""Unauthenticated verification disclosure tests."""

from app.models.enums import AttemptDenialReason, AttemptOutcome
from app.models.ops import AuditEvent
from app.models.verification import VerificationAttempt
from sqlalchemy import select
from tests.factories import auth_headers
from tests.test_verification import request_payload


def test_student_authorize_and_public_verify(client, seeded) -> None:
    student = auth_headers(client, "student@demo-ait.edu")
    request = client.post(
        "/api/v1/verification-requests", json=request_payload(), headers=student
    ).json()
    authorized = client.post(
        f"/api/v1/verification-requests/{request['id']}/authorize", headers=student
    ).json()
    public = client.get(f"/api/v1/public/verify/{authorized['token']}")
    assert public.status_code == 200, public.text
    body = public.json()
    assert {claim["key"] for claim in body["claims"]} == {
        "INSTITUTION",
        "PROGRAMME",
        "ENROLMENT_STATUS",
    }
    assert "student_name" not in public.text.lower()
    assert body["receipt"]["signature"]
    assert "mock" in body["demoNotice"].lower()


def test_revoked_token_denies_without_disclosure(client, seeded) -> None:
    student = auth_headers(client, "student@demo-ait.edu")
    request = client.post(
        "/api/v1/verification-requests", json=request_payload(), headers=student
    ).json()
    authorized = client.post(
        f"/api/v1/verification-requests/{request['id']}/authorize", headers=student
    ).json()
    client.post(
        f"/api/v1/verification-requests/{request['id']}/revoke",
        json={"reason": "Synthetic revocation"},
        headers=student,
    )
    denied = client.get(f"/api/v1/public/verify/{authorized['token']}")
    assert denied.status_code == 410
    assert "programme" not in denied.text.lower()


def test_student_me_is_masked_and_scoped(client, seeded) -> None:
    student = auth_headers(client, "student@demo-ait.edu")
    response = client.get("/api/v1/students/me", headers=student)
    assert response.status_code == 200, response.text
    assert response.json()["maskedApaar"].endswith("9012")
    assert "123456789012" not in response.text


def test_unknown_token_denial_is_audited_without_storing_token(client, seeded, db) -> None:
    token = "synthetic-invalid-token"
    response = client.get(f"/api/v1/public/verify/{token}")
    assert response.status_code == 410
    attempt = db.scalar(
        select(VerificationAttempt).where(VerificationAttempt.verification_request_id.is_(None))
    )
    assert attempt is not None
    assert attempt.outcome == AttemptOutcome.DENIED.value
    assert attempt.denial_reason == AttemptDenialReason.MALFORMED.value
    assert token not in str(attempt.__dict__)
    audit = db.scalar(select(AuditEvent).where(AuditEvent.action == "PUBLIC_VERIFICATION_DENIED"))
    assert audit is not None
    assert token not in str(audit.metadata_)
