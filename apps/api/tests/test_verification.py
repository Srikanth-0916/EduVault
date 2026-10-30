"""Student consent and purpose-bound verification tests."""

from tests.factories import auth_headers


def request_payload() -> dict:
    return {
        "recipientName": "Acme HR",
        "recipientOrg": "Acme Demo",
        "recipientEmail": "hr@acme-demo.example",
        "purpose": "Employment screening",
        "requestedClaims": ["INSTITUTION", "PROGRAMME", "ENROLMENT_STATUS"],
        "legalBasis": "CONSENT",
        "expiresInHours": 24,
    }


def test_student_can_create_authorize_and_list_request(client, seeded) -> None:
    student = auth_headers(client, "student@demo-ait.edu")
    created = client.post("/api/v1/verification-requests", json=request_payload(), headers=student)
    assert created.status_code == 201, created.text
    request = created.json()
    assert request["status"] == "PENDING_AUTHORIZATION"
    assert "token" not in created.text

    authorized = client.post(
        f"/api/v1/verification-requests/{request['id']}/authorize",
        headers=student,
    )
    assert authorized.status_code == 200, authorized.text
    body = authorized.json()
    assert body["token"]
    assert body["verifyUrl"].endswith(body["token"])
    assert body["receipt"]["signature"]

    listed = client.get("/api/v1/verification-requests?scope=mine", headers=student)
    assert listed.status_code == 200
    assert listed.json()["items"][0]["status"] == "AUTHORIZED"


def test_claim_allow_list_and_permissions(client, seeded) -> None:
    student = auth_headers(client, "student@demo-ait.edu")
    invalid = {**request_payload(), "requestedClaims": ["STUDENT_NAME"]}
    response = client.post("/api/v1/verification-requests", json=invalid, headers=student)
    assert response.status_code == 422

    operator = auth_headers(client, "operator@demo-ait.edu")
    denied = client.post("/api/v1/verification-requests", json=request_payload(), headers=operator)
    assert denied.status_code == 403


def test_revocation_denies_future_issue_link(client, seeded) -> None:
    student = auth_headers(client, "student@demo-ait.edu")
    created = client.post(
        "/api/v1/verification-requests", json=request_payload(), headers=student
    ).json()
    authorized = client.post(
        f"/api/v1/verification-requests/{created['id']}/authorize", headers=student
    ).json()
    revoked = client.post(
        f"/api/v1/verification-requests/{created['id']}/revoke",
        json={"reason": "Recipient no longer needs access"},
        headers=student,
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "REVOKED"
    issue = client.post(
        f"/api/v1/verification-requests/{created['id']}/issue-link", headers=student
    )
    assert issue.status_code == 409
    assert authorized["token"]
