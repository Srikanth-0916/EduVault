"""Duplicate case access, resolution, and information requests."""

from __future__ import annotations

from tests.factories import auth_headers
from tests.helpers import upload_and_validate


def _cases(client, headers) -> list[dict]:
    response = client.get("/api/v1/duplicate-cases", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["items"]


def test_cases_are_tenant_scoped_and_analyst_cannot_read_evidence(
    client, seeded, sample_csv
) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    upload_and_validate(client, operator, sample_csv("batch_mixed.csv"))
    cases = _cases(client, operator)
    assert len(cases) == 5

    analyst = auth_headers(client, "analyst@aicte.demo")
    denied = client.get("/api/v1/duplicate-cases", headers=analyst)
    assert denied.status_code == 403


def test_only_supervisor_resolves_case_and_institution_cannot(client, seeded, sample_csv) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    upload_and_validate(client, operator, sample_csv("batch_mixed.csv"))
    cases = _cases(client, operator)
    target = cases[0]

    denied = client.post(
        f"/api/v1/duplicate-cases/{target['id']}/resolve",
        json={"resolutionCode": "DATA_ERROR", "reason": "Institution cannot decide"},
        headers=operator,
    )
    assert denied.status_code == 403

    reviewer = auth_headers(client, "reviewer@aicte.demo")
    reviewer_denied = client.post(
        f"/api/v1/duplicate-cases/{target['id']}/resolve",
        json={
            "resolutionCode": "VALID_TRANSFER",
            "reason": "Reviewer cannot finalize resolution",
        },
        headers=reviewer,
    )
    assert reviewer_denied.status_code == 403

    supervisor = auth_headers(client, "supervisor@aicte.demo")
    resolved = client.post(
        f"/api/v1/duplicate-cases/{target['id']}/resolve",
        json={
            "resolutionCode": "VALID_TRANSFER",
            "reason": "Synthetic transfer evidence reviewed",
        },
        headers=supervisor,
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["status"] == "RESOLVED"
    assert resolved.json()["resolutionCode"] == "VALID_TRANSFER"

    listed = _cases(client, operator)
    assert next(item for item in listed if item["id"] == target["id"])["status"] == "RESOLVED"


def test_information_request_sets_in_review(client, seeded, sample_csv) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    upload_and_validate(client, operator, sample_csv("batch_mixed.csv"))
    target = _cases(client, operator)[0]
    reviewer = auth_headers(client, "reviewer@aicte.demo")
    response = client.post(
        f"/api/v1/duplicate-cases/{target['id']}/request-information",
        json={"reason": "Please provide the transfer certificate"},
        headers=reviewer,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "IN_REVIEW"
    assert "transfer certificate" in response.json()["resolutionReason"]


def test_case_detail_has_masked_evidence_only(client, seeded, sample_csv) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    upload_and_validate(client, operator, sample_csv("batch_mixed.csv"))
    target = _cases(client, operator)[0]
    detail = client.get(f"/api/v1/duplicate-cases/{target['id']}", headers=operator)
    assert detail.status_code == 200
    assert "••••••••" in str(detail.json()["evidence"])
    assert "920000000003" not in str(detail.json())
