"""AICTE review queue and decision contract tests."""

from tests.factories import auth_headers


def test_reviewer_queue_requires_aicte_role(client, seeded) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    reviewer = auth_headers(client, "reviewer@aicte.demo")

    assert client.get("/api/v1/review/queue", headers=operator).status_code == 403
    response = client.get("/api/v1/review/queue", headers=reviewer)
    assert response.status_code == 200, response.text
    assert "items" in response.json()


def test_review_summary_is_available_to_reviewer_and_not_operator(client, seeded) -> None:
    reviewer = auth_headers(client, "reviewer@aicte.demo")
    operator = auth_headers(client, "operator@demo-ait.edu")

    response = client.get("/api/v1/review/summary", headers=reviewer)
    assert response.status_code == 200, response.text
    assert {"underReview", "openCases", "oldestPending"} <= set(response.json())
    assert client.get("/api/v1/review/summary", headers=operator).status_code == 403


def test_illegal_decision_transition_returns_conflict(client, seeded) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    batch = client.post(
        "/api/v1/submission-batches",
        json={"academicYear": "2026-27", "sourceType": "CSV_UPLOAD"},
        headers=operator,
    ).json()
    reviewer = auth_headers(client, "reviewer@aicte.demo")
    response = client.post(
        f"/api/v1/submission-batches/{batch['id']}/decision",
        json={"decision": "ACCEPT", "reason": "Cannot decide a draft"},
        headers=reviewer,
    )
    assert response.status_code == 409


def test_reason_code_is_restricted(client, seeded) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    batch = client.post(
        "/api/v1/submission-batches",
        json={"academicYear": "2026-27", "sourceType": "CSV_UPLOAD"},
        headers=operator,
    ).json()
    reviewer = auth_headers(client, "reviewer@aicte.demo")
    response = client.post(
        f"/api/v1/submission-batches/{batch['id']}/decision",
        json={"decision": "ACCEPT", "reason": "Reason", "reasonCode": "UNSAFE"},
        headers=reviewer,
    )
    assert response.status_code == 422
