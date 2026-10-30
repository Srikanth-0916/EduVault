"""Manual enrollment creation, versioning, identity checks, and tenancy."""

from __future__ import annotations

from app.constants import STUDENT_IDENTITY_ID
from app.models.enrollment import StudentEnrollment
from sqlalchemy import select
from tests.factories import auth_headers


def _manual_payload(**overrides) -> dict:
    payload = {
        "studentLocalId": "MANUAL-2026-001",
        "studentFullName": "Manual Synthetic Student",
        "apaarId": "555555555555",
        "programmeId": "prog_ait_cse",
        "campusId": "camp_ait_main",
        "academicYear": "2026-27",
        "admissionDate": "2026-08-01",
        "enrollmentStatus": "ACTIVE",
        "seatClassification": "APPROVED_REGULAR",
        "admissionCategory": "GENERAL",
        "nriStatus": "NO",
        "ociStatus": "NO",
        "foreignNationalStatus": "NO",
    }
    payload.update(overrides)
    return payload


def test_manual_enrollment_is_masked_and_versioned(client, seeded) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    created = client.post("/api/v1/enrollments", json=_manual_payload(), headers=headers)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["version"] == 1
    assert body["maskedApaar"].endswith("5555")
    assert "555555555555" not in str(body)
    assert body["identityStatus"] in {
        "FORMAT_VALID",
        "EXTERNALLY_CONFIRMED",
        "EXTERNAL_UNAVAILABLE",
        "MANUAL_REVIEW",
    }

    duplicate = client.post("/api/v1/enrollments", json=_manual_payload(), headers=headers)
    assert duplicate.status_code == 409

    patched = client.patch(
        f"/api/v1/enrollments/{body['id']}",
        json={"studentFullName": "Corrected Synthetic Student", "reason": "Name correction"},
        headers=headers,
    )
    assert patched.status_code == 200, patched.text
    updated = patched.json()
    assert updated["id"] != body["id"]
    assert updated["version"] == 2
    assert updated["isCurrent"] is True
    assert updated["studentFullName"] == "Corrected Synthetic Student"

    current = client.get(
        "/api/v1/enrollments",
        params={"search": "MANUAL-2026-001"},
        headers=headers,
    )
    assert current.status_code == 200
    assert current.json()["total"] == 1
    assert current.json()["items"][0]["id"] == updated["id"]


def test_patch_requires_a_reason(client, seeded) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    created = client.post("/api/v1/enrollments", json=_manual_payload(), headers=headers).json()
    response = client.patch(
        f"/api/v1/enrollments/{created['id']}",
        json={"studentFullName": "No Reason"},
        headers=headers,
    )
    assert response.status_code == 422


def test_manual_create_rejects_programme_from_another_institution(client, seeded) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    response = client.post(
        "/api/v1/enrollments",
        json=_manual_payload(programmeId="prog_bie_mech", campusId="camp_bie_main"),
        headers=headers,
    )
    assert response.status_code == 404


def test_identity_verification_is_explicitly_mock(client, seeded) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    created = client.post("/api/v1/enrollments", json=_manual_payload(), headers=headers).json()
    response = client.post(f"/api/v1/enrollments/{created['id']}/verify-identity", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["verification"]["isMock"] is True
    assert body["verification"]["provider"] == "MOCK_APAAR"
    assert body["verification"]["result"] == "SUCCESS"
    assert body["identityStatus"] == "EXTERNALLY_CONFIRMED"


def test_institution_list_is_scoped_and_analyst_is_denied(client, seeded) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    response = client.get("/api/v1/enrollments", headers=operator)
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["institutionId"] == "inst_ait" for item in items)

    analyst = auth_headers(client, "analyst@aicte.demo")
    denied = client.get("/api/v1/enrollments", headers=analyst)
    assert denied.status_code == 403


def test_student_can_read_own_record_only(client, seeded, db) -> None:
    own = db.scalar(
        select(StudentEnrollment).where(
            StudentEnrollment.student_identity_id == STUDENT_IDENTITY_ID
        )
    )
    assert own is not None
    student = auth_headers(client, "student@demo-ait.edu")
    response = client.get(f"/api/v1/enrollments/{own.id}", headers=student)
    assert response.status_code == 200

    other = db.scalar(
        select(StudentEnrollment).where(
            StudentEnrollment.student_identity_id != STUDENT_IDENTITY_ID
        )
    )
    assert other is not None
    denied = client.get(f"/api/v1/enrollments/{other.id}", headers=student)
    assert denied.status_code == 403
