"""Attestation, submission, decisions, receipts, and resubmission."""

from __future__ import annotations

from app.models.enrollment import StudentEnrollment
from sqlalchemy import func, select
from tests.factories import auth_headers
from tests.helpers import create_batch, upload


def _ready_batch(client, sample_csv) -> tuple[str, dict, dict]:
    operator = auth_headers(client, "operator@demo-ait.edu")
    batch = create_batch(client, operator)
    uploaded = upload(client, operator, batch["id"], sample_csv("batch_valid.csv"))
    assert uploaded.status_code == 200, uploaded.text
    validated = client.post(
        f"/api/v1/submission-batches/{batch['id']}/validate", headers=operator
    )
    assert validated.status_code == 200, validated.text
    assert validated.json()["status"] == "READY_FOR_ATTESTATION"
    return batch["id"], operator, validated.json()


def test_submission_requires_attestation_and_records_receipt(client, seeded, sample_csv) -> None:
    batch_id, operator, _ = _ready_batch(client, sample_csv)
    nodal = auth_headers(client, "nodal@demo-ait.edu")

    premature = client.post(
        f"/api/v1/submission-batches/{batch_id}/submit", headers=nodal
    )
    assert premature.status_code == 409

    attested = client.post(
        f"/api/v1/submission-batches/{batch_id}/attest",
        json={"declaration": True, "attestationName": "Nisha Kulkarni"},
        headers=nodal,
    )
    assert attested.status_code == 200, attested.text
    assert attested.json()["attestedAt"]

    submitted = client.post(
        f"/api/v1/submission-batches/{batch_id}/submit", headers=nodal
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["status"] == "UNDER_AICTE_REVIEW"

    receipt = client.get(
        f"/api/v1/submission-batches/{batch_id}/receipt", headers=operator
    )
    assert receipt.status_code == 200, receipt.text
    body = receipt.json()
    assert body["checksum"]
    assert body["signature"]["algorithm"] == "HMAC-SHA256"
    assert body["signature"]["signature"]


def test_reviewer_accepts_and_enrollments_are_acknowledged(client, seeded, db, sample_csv) -> None:
    batch_id, _, _ = _ready_batch(client, sample_csv)
    nodal = auth_headers(client, "nodal@demo-ait.edu")
    client.post(
        f"/api/v1/submission-batches/{batch_id}/attest",
        json={"declaration": True, "attestationName": "Nisha Kulkarni"},
        headers=nodal,
    )
    submitted = client.post(
        f"/api/v1/submission-batches/{batch_id}/submit", headers=nodal
    )
    assert submitted.status_code == 200

    reviewer = auth_headers(client, "reviewer@aicte.demo")
    decided = client.post(
        f"/api/v1/submission-batches/{batch_id}/decision",
        json={"decision": "ACCEPT", "reason": "Synthetic review complete"},
        headers=reviewer,
    )
    assert decided.status_code == 200, decided.text
    assert decided.json()["status"] == "ACCEPTED"
    accepted = db.scalar(
        select(func.count(StudentEnrollment.id)).where(
            StudentEnrollment.source_batch_id == batch_id,
            StudentEnrollment.record_accepted_at.is_not(None),
        )
    )
    assert accepted == 4


def test_reviewer_return_then_resubmission_does_not_double_count(
    client, seeded, db, sample_csv
) -> None:
    batch_id, operator, _ = _ready_batch(client, sample_csv)
    nodal = auth_headers(client, "nodal@demo-ait.edu")
    client.post(
        f"/api/v1/submission-batches/{batch_id}/attest",
        json={"declaration": True, "attestationName": "Nisha Kulkarni"},
        headers=nodal,
    )
    client.post(f"/api/v1/submission-batches/{batch_id}/submit", headers=nodal)

    reviewer = auth_headers(client, "reviewer@aicte.demo")
    returned = client.post(
        f"/api/v1/submission-batches/{batch_id}/decision",
        json={"decision": "RETURN", "reason": "Please correct a synthetic field"},
        headers=reviewer,
    )
    assert returned.status_code == 200
    assert returned.json()["status"] == "RETURNED_FOR_CORRECTION"

    revalidated = client.post(
        f"/api/v1/submission-batches/{batch_id}/validate", headers=operator
    )
    assert revalidated.status_code == 200, revalidated.text
    assert revalidated.json()["status"] == "READY_FOR_ATTESTATION"
    client.post(
        f"/api/v1/submission-batches/{batch_id}/attest",
        json={"declaration": True, "attestationName": "Nisha Kulkarni"},
        headers=nodal,
    )
    resubmitted = client.post(
        f"/api/v1/submission-batches/{batch_id}/submit", headers=nodal
    )
    assert resubmitted.status_code == 200, resubmitted.text
    assert resubmitted.json()["version"] == 2

    current = db.scalar(
        select(func.count(StudentEnrollment.id)).where(
            StudentEnrollment.source_batch_id == batch_id,
            StudentEnrollment.is_current.is_(True),
        )
    )
    assert current == 4


def test_row_edit_resets_to_draft_then_revalidates(client, seeded, sample_csv) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    batch = create_batch(client, operator)
    uploaded = upload(client, operator, batch["id"], sample_csv("batch_valid.csv"))
    assert uploaded.status_code == 200
    row = uploaded.json()["rows"][0]
    edited = client.patch(
        f"/api/v1/submission-batches/{batch['id']}/rows/{row['id']}",
        json={"studentName": "Edited Synthetic Student"},
        headers=operator,
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["status"] == "DRAFT"
    assert edited.json()["rows"][0]["studentName"] == "Edited Synthetic Student"

    revalidated = client.post(
        f"/api/v1/submission-batches/{batch['id']}/validate", headers=operator
    )
    assert revalidated.status_code == 200
    assert revalidated.json()["status"] == "READY_FOR_ATTESTATION"


def test_nodal_cannot_decide_and_operator_cannot_attest(client, seeded, sample_csv) -> None:
    batch_id, _, _ = _ready_batch(client, sample_csv)
    operator = auth_headers(client, "operator@demo-ait.edu")
    denied_attest = client.post(
        f"/api/v1/submission-batches/{batch_id}/attest",
        json={"declaration": True, "attestationName": "Arjun Nair"},
        headers=operator,
    )
    assert denied_attest.status_code == 403

    nodal = auth_headers(client, "nodal@demo-ait.edu")
    denied_decision = client.post(
        f"/api/v1/submission-batches/{batch_id}/decision",
        json={"decision": "ACCEPT", "reason": "Institution cannot decide"},
        headers=nodal,
    )
    assert denied_decision.status_code == 403
