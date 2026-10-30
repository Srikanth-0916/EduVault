"""Institution dashboard aggregation and access control."""

from __future__ import annotations

from tests.factories import auth_headers


def test_institution_dashboard_has_kpis_and_capacity(client, seeded) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    response = client.get("/api/v1/dashboard/institution", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["institutionId"] == "inst_ait"
    assert len(body["kpis"]) == 6
    assert {item["key"] for item in body["kpis"]} >= {
        "approved_intake",
        "reported_enrollment",
        "apaar_gaps",
        "unresolved_cases",
        "pending_batches",
    }
    assert body["capacity"]
    assert all(item["programmeCode"] for item in body["capacity"])
    assert body["identityDistribution"]
    assert body["enrollmentStatusDistribution"]
    assert "synthetic" in body["dataFreshness"].lower()


def test_dashboard_rejects_non_institution_roles(client, seeded) -> None:
    analyst = auth_headers(client, "analyst@aicte.demo")
    assert client.get("/api/v1/dashboard/institution", headers=analyst).status_code == 403
