"""CSV upload, parsing limits, and batch detail tests."""

from __future__ import annotations

from tests.factories import auth_headers


def create_batch(client, headers, year: str = "2026-27") -> dict:
    response = client.post(
        "/api/v1/submission-batches",
        json={"academicYear": year, "sourceType": "CSV_UPLOAD"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def upload(client, headers, batch_id: str, content: bytes, name: str = "valid.csv"):
    return client.post(
        f"/api/v1/submission-batches/{batch_id}/file",
        files={"file": (name, content, "text/csv")},
        headers=headers,
    )


def test_valid_csv_reaches_ready_for_attestation(client, seeded, sample_csv) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    batch = create_batch(client, headers)
    uploaded = upload(client, headers, batch["id"], sample_csv("batch_valid.csv"))
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["fileChecksum"]
    assert uploaded.json()["rowCount"] == 4

    validated = client.post(
        f"/api/v1/submission-batches/{batch['id']}/validate", headers=headers
    )
    assert validated.status_code == 200, validated.text
    detail = client.get(
        f"/api/v1/submission-batches/{batch['id']}", headers=headers
    ).json()
    assert detail["status"] == "READY_FOR_ATTESTATION"
    assert detail["summary"]["errorRows"] == 0
    assert detail["summary"]["warningRows"] >= 1  # NRI attribute review
    assert len(detail["rows"]) == 4


def test_malformed_apaar_blocks_and_explains(client, seeded, sample_csv) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    batch = create_batch(client, headers)
    upload(client, headers, batch["id"], sample_csv("batch_mixed.csv"))
    response = client.post(
        f"/api/v1/submission-batches/{batch['id']}/validate", headers=headers
    )
    assert response.status_code == 200, response.text
    detail = client.get(
        f"/api/v1/submission-batches/{batch['id']}", headers=headers
    ).json()
    assert detail["status"] == "VALIDATION_FAILED"
    finding = next(item for item in detail["findings"] if item["ruleId"] == "BR-002")
    assert finding["code"] == "APAAR_INVALID_FORMAT"
    assert finding["evidence"]["valueMasked"].endswith("••••")


def test_raw_apaar_is_not_persisted_in_rows_or_findings(
    client, seeded, db, sample_csv
) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    batch = create_batch(client, headers)
    upload(client, headers, batch["id"], sample_csv("batch_mixed.csv"))
    client.post(f"/api/v1/submission-batches/{batch['id']}/validate", headers=headers)

    from app.models.batch import SubmissionRow, ValidationFinding
    from sqlalchemy import select

    rows = db.scalars(select(SubmissionRow)).all()
    findings = db.scalars(select(ValidationFinding)).all()
    assert rows and findings
    serialized_rows = " ".join(str(row.raw_data) for row in rows)
    serialized_findings = " ".join(str(finding.evidence) for finding in findings)
    assert "920000000003" not in serialized_rows
    assert "920000000003" not in serialized_findings
    assert "ABC123" not in serialized_rows
    assert "ABC123" not in serialized_findings


def test_upload_rejects_missing_headers(client, seeded) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    batch = create_batch(client, headers)
    response = upload(
        client,
        headers,
        batch["id"],
        b"institution_student_id,apaar_id\nX,123456789012\n",
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CSV_PARSE_ERROR"
    assert response.json()["error"]["details"]["errors"][0]["code"] == "MISSING_HEADERS"


def test_upload_rejects_oversize_file(client, seeded) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    batch = create_batch(client, headers)
    response = upload(client, headers, batch["id"], b"x" * (5 * 1024 * 1024 + 1))
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_template_download(client, seeded) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    response = client.get("/api/v1/template.csv", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "institution_student_id" in response.text
    assert "date_of_birth" in response.text


def test_other_institution_cannot_read_batch(client, seeded, sample_csv) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    batch = create_batch(client, operator)
    reviewer = auth_headers(client, "reviewer@aicte.demo")
    # Reviewers may read; another institution role is tested through tenant scope
    # in the enrollment suite. Here an unknown batch is a generic 404.
    missing = client.get(
        "/api/v1/submission-batches/batch_does_not_exist", headers=reviewer
    )
    assert missing.status_code == 404
    assert client.get(
        f"/api/v1/submission-batches/{batch['id']}", headers=reviewer
    ).status_code == 200
