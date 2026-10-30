"""Validation rules, duplicate cases, capacity warnings, and idempotency."""

from __future__ import annotations

import csv
import io

from app.models.review import DuplicateCase
from app.services.csv_import import parse_csv
from sqlalchemy import func, select
from tests.factories import auth_headers
from tests.helpers import create_batch, upload, upload_and_validate


def test_mixed_batch_creates_expected_findings_and_cases(
    client, seeded, sample_csv
) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    detail = upload_and_validate(
        client, headers, sample_csv("batch_mixed.csv"), "mixed.csv"
    )
    assert detail["status"] == "VALIDATION_FAILED"
    rules = {finding["ruleId"] for finding in detail["findings"]}
    expected = {
        "BR-001",
        "BR-002",
        "BR-003",
        "BR-004",
        "BR-005",
        "BR-006",
        "BR-007",
        "BR-009",
        "BR-010",
    }
    assert expected <= rules

    reviewer = auth_headers(client, "reviewer@aicte.demo")
    cases = client.get("/api/v1/duplicate-cases", headers=reviewer)
    assert cases.status_code == 200
    assert cases.json()["total"] == 5
    evidence_text = str(cases.json())
    assert "••••••••" in evidence_text
    assert "920000000003" not in evidence_text


def test_capacity_warning_is_explanatory_and_non_blocking(
    client, seeded, sample_csv
) -> None:
    supervisor = auth_headers(client, "supervisor@aicte.demo")
    patched = client.patch(
        "/api/v1/intake-allocations/alloc_ait_ece_regular",
        json={"approvedCount": 17, "reason": "Demo capacity adjustment"},
        headers=supervisor,
    )
    assert patched.status_code == 200, patched.text

    operator = auth_headers(client, "operator@demo-ait.edu")
    detail = upload_and_validate(
        client, operator, sample_csv("batch_valid.csv"), "valid.csv"
    )
    assert detail["status"] == "READY_FOR_ATTESTATION"
    capacity_findings = [
        item for item in detail["findings"] if item["ruleId"] == "BR-008"
    ]
    assert capacity_findings
    evidence = capacity_findings[0]["evidence"]
    assert evidence["projected"] > evidence["approved"]
    assert capacity_findings[0]["blocking"] is False


def test_supernumerary_without_reference_blocks(client, seeded, sample_csv) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    detail = upload_and_validate(
        client, headers, sample_csv("batch_mixed.csv"), "mixed.csv"
    )
    finding = next(item for item in detail["findings"] if item["ruleId"] == "BR-009")
    assert finding["code"] == "SUPERNUMERARY_REFERENCE_REQUIRED"
    assert finding["blocking"] is True


def test_revalidation_does_not_duplicate_cases(client, seeded, db, sample_csv) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    batch = create_batch(client, headers)
    upload(client, headers, batch["id"], sample_csv("batch_mixed.csv"))
    for _ in range(2):
        response = client.post(
            f"/api/v1/submission-batches/{batch['id']}/validate", headers=headers
        )
        assert response.status_code == 200, response.text
    count = db.scalar(select(func.count(DuplicateCase.id)))
    assert count == 5


def test_parser_rejects_more_than_ten_thousand_rows() -> None:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "institution_student_id",
            "apaar_id",
            "student_name",
            "programme_code",
            "campus_code",
            "academic_year",
            "admission_date",
            "exit_date",
            "enrollment_status",
            "seat_classification",
            "admission_category",
            "nri_status",
            "oci_status",
            "foreign_national_status",
            "approval_reference",
        ]
    )
    for index in range(10_001):
        writer.writerow(
            [
                f"S{index}",
                f"{700000000000 + index:012d}",
                "Student",
                "CSE",
                "AIT-MAIN",
                "2026-27",
                "2026-07-01",
                "",
                "ACTIVE",
                "APPROVED_REGULAR",
                "GENERAL",
                "NO",
                "NO",
                "NO",
                "",
            ]
        )
    parsed = parse_csv(output.getvalue().encode("utf-8"))
    assert any(error["code"] == "TOO_MANY_ROWS" for error in parsed.errors)
    assert len(parsed.rows) == 10_000
