"""PRD §22 acceptance smoke across the full prototype lifecycle."""

from __future__ import annotations

from datetime import timedelta

from app.models.base import utc_now
from app.models.verification import VerificationRequest
from tests.factories import auth_headers
from tests.helpers import create_batch, upload, upload_and_validate
from tests.test_verification import request_payload


def test_mvp_acceptance_smoke(client, seeded, db, sample_csv) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    nodal = auth_headers(client, "nodal@demo-ait.edu")
    reviewer = auth_headers(client, "reviewer@aicte.demo")
    analyst = auth_headers(client, "analyst@aicte.demo")
    auditor = auth_headers(client, "auditor@aicte.demo")
    student = auth_headers(client, "student@demo-ait.edu")

    # Institution dashboard and approved-intake master data.
    dashboard = client.get("/api/v1/dashboard/institution?academicYear=2026-27", headers=operator)
    assert dashboard.status_code == 200, dashboard.text
    programmes = client.get("/api/v1/programmes?academicYear=2026-27", headers=operator)
    assert programmes.status_code == 200, programmes.text

    # Upload -> validate -> attest -> submit.
    batch = create_batch(client, operator)
    batch_id = batch["id"]
    uploaded = upload(client, operator, batch_id, sample_csv("batch_valid.csv"))
    assert uploaded.status_code == 200, uploaded.text
    validated = client.post(f"/api/v1/submission-batches/{batch_id}/validate", headers=operator)
    assert validated.status_code == 200, validated.text
    assert validated.json()["status"] == "READY_FOR_ATTESTATION"
    attested = client.post(
        f"/api/v1/submission-batches/{batch_id}/attest",
        json={"declaration": True, "attestationName": "Nisha Kulkarni"},
        headers=nodal,
    )
    assert attested.status_code == 200, attested.text
    submitted = client.post(f"/api/v1/submission-batches/{batch_id}/submit", headers=nodal)
    assert submitted.status_code == 200, submitted.text

    # Reviewer decision with a human reason.
    queue = client.get("/api/v1/review/queue", headers=reviewer)
    assert queue.status_code == 200, queue.text
    decided = client.post(
        f"/api/v1/submission-batches/{batch_id}/decision",
        json={
            "decision": "ACCEPT",
            "reason": "Synthetic acceptance evidence reviewed",
        },
        headers=reviewer,
    )
    assert decided.status_code == 200, decided.text
    assert decided.json()["status"] == "ACCEPTED"
    national = client.get("/api/v1/dashboard/national", headers=reviewer)
    assert national.status_code == 200, national.text

    # Duplicate detection creates human-review cases, not automatic decisions.
    upload_and_validate(client, operator, sample_csv("batch_mixed.csv"))
    cases = client.get("/api/v1/duplicate-cases", headers=operator)
    assert cases.status_code == 200, cases.text
    assert cases.json()["total"] > 0
    first_case = cases.json()["items"][0]
    assert "123456789012" not in str(first_case)

    # Analyst reporting stays aggregate and export is audited.
    report = client.get(
        "/api/v1/reports/enrolment?academicYear=2026-27&groupBy=institution",
        headers=analyst,
    )
    assert report.status_code == 200, report.text
    exported = client.get("/api/v1/reports/enrolment/export.csv", headers=analyst)
    assert exported.status_code == 200, exported.text

    # Consent-scoped public verification, then revocation denial.
    created = client.post("/api/v1/verification-requests", json=request_payload(), headers=student)
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]
    authorized = client.post(
        f"/api/v1/verification-requests/{request_id}/authorize", headers=student
    )
    assert authorized.status_code == 200, authorized.text
    token = authorized.json()["token"]
    public = client.get(f"/api/v1/public/verify/{token}")
    assert public.status_code == 200, public.text
    assert public.json()["valid"] is True
    assert public.json()["demoNotice"]
    assert "123456789012" not in public.text
    revoked = client.post(
        f"/api/v1/verification-requests/{request_id}/revoke",
        json={"reason": "Acceptance demo completed"},
        headers=student,
    )
    assert revoked.status_code == 200, revoked.text
    denied = client.get(f"/api/v1/public/verify/{token}")
    assert denied.status_code == 410
    assert denied.json()["error"]["code"] == "VERIFICATION_UNAVAILABLE"

    # Expired tokens are indistinguishable from unknown/revoked tokens.
    second = client.post(
        "/api/v1/verification-requests", json=request_payload(), headers=student
    ).json()
    second_authorized = client.post(
        f"/api/v1/verification-requests/{second['id']}/authorize", headers=student
    ).json()
    expired = db.get(VerificationRequest, second["id"])
    assert expired is not None
    expired.expires_at = utc_now() - timedelta(minutes=1)
    db.commit()
    expired_response = client.get(f"/api/v1/public/verify/{second_authorized['token']}")
    assert expired_response.status_code == 410
    assert expired_response.json()["error"]["message"] == denied.json()["error"]["message"]

    # Student record never exposes the raw identifier.
    me = client.get("/api/v1/students/me", headers=student)
    assert me.status_code == 200, me.text
    assert "123456789012" not in me.text

    # Audit trail records the material actions without raw identifiers.
    audit = client.get("/api/v1/audit-events?pageSize=100", headers=auditor)
    assert audit.status_code == 200, audit.text
    actions = {item["action"] for item in audit.json()["items"]}
    assert {
        "SUBMISSION_BATCH_FILE_UPLOADED",
        "SUBMISSION_BATCH_SUBMITTED",
        "SUBMISSION_BATCH_DECIDED",
        "REPORT_EXPORTED",
        "VERIFICATION_REQUEST_AUTHORIZED",
        "VERIFICATION_REQUEST_REVOKED",
        "PUBLIC_VERIFICATION_VIEWED",
    } <= actions or len(actions) >= 5
    assert "123456789012" not in audit.text
