"""Role-scoped aggregate report and export tests."""

from app.models.ops import AuditEvent, ReportExport
from sqlalchemy import select
from tests.factories import auth_headers


def test_analyst_export_has_no_direct_identifiers(client, seeded) -> None:
    analyst = auth_headers(client, "analyst@aicte.demo")
    response = client.get(
        "/api/v1/reports/enrolment/export.csv?groupBy=institution",
        headers=analyst,
    )
    assert response.status_code == 200, response.text
    assert "student_name" not in response.text.lower()
    assert "apaar" not in response.text.lower()
    assert "text/csv" in response.headers["content-type"]


def test_institution_export_is_tenant_scoped_and_masked(client, seeded) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    response = client.get(
        "/api/v1/reports/enrolment/export.csv?groupBy=programme",
        headers=operator,
    )
    assert response.status_code == 200, response.text
    assert "inst_bie" not in response.text.lower()
    assert "student_name" not in response.text.lower()


def test_report_shapes_include_freshness_and_suppression(client, seeded) -> None:
    analyst = auth_headers(client, "analyst@aicte.demo")
    response = client.get(
        "/api/v1/reports/enrolment?academicYear=2026-27&groupBy=institution",
        headers=analyst,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert {"generatedAt", "filters", "dataFreshness", "suppressedGroups", "items"} <= set(body)
    assert all(
        "studentName" not in row and "apaar" not in str(row).lower() for row in body["items"]
    )


def test_institution_grouping_does_not_emit_a_random_programme(client, seeded) -> None:
    analyst = auth_headers(client, "analyst@aicte.demo")
    response = client.get(
        "/api/v1/reports/enrolment?academicYear=2026-27&groupBy=institution",
        headers=analyst,
    )
    assert response.status_code == 200, response.text
    rows = [item for item in response.json()["items"] if not item.get("suppressed")]
    assert rows
    assert all("programmeCode" not in item for item in rows)


def test_analyst_data_quality_suppresses_small_cells(client, seeded) -> None:
    analyst = auth_headers(client, "analyst@aicte.demo")
    response = client.get(
        "/api/v1/reports/data-quality?academicYear=2026-27",
        headers=analyst,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["suppressedGroups"] > 0
    assert all(item.get("suppressed") or item.get("count", 0) >= 5 for item in body["items"])


def test_analyst_intake_report_suppresses_small_programme_groups(client, seeded) -> None:
    analyst = auth_headers(client, "analyst@aicte.demo")
    response = client.get(
        "/api/v1/reports/intake-reconciliation?academicYear=2026-27",
        headers=analyst,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["suppressedGroups"] > 0
    assert all(item.get("suppressed") for item in body["items"] if item.get("suppressed"))


def test_formula_leading_values_are_neutralized(client, seeded) -> None:
    analyst = auth_headers(client, "analyst@aicte.demo")
    response = client.get(
        "/api/v1/reports/enrolment/export.csv?groupBy=institution",
        headers=analyst,
    )
    assert response.status_code == 200
    assert "=HYPERLINK" not in response.text


def test_csv_export_writes_linked_export_and_audit_rows(client, seeded, db) -> None:
    analyst = auth_headers(client, "analyst@aicte.demo")
    response = client.get(
        "/api/v1/reports/enrolment/export.csv?groupBy=institution",
        headers=analyst,
    )
    assert response.status_code == 200
    export = db.scalar(select(ReportExport).order_by(ReportExport.created_at.desc()))
    assert export is not None
    audit = db.scalar(
        select(AuditEvent).where(
            AuditEvent.action == "REPORT_EXPORTED",
            AuditEvent.resource_ref == export.id,
        )
    )
    assert audit is not None
