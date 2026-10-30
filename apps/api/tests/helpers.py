"""Shared API helpers for batch workflow tests."""

from __future__ import annotations


def create_batch(client, headers, year: str = "2026-27") -> dict:
    response = client.post(
        "/api/v1/submission-batches",
        json={"academicYear": year, "sourceType": "CSV_UPLOAD"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def upload(client, headers, batch_id: str, content: bytes, name: str = "upload.csv"):
    return client.post(
        f"/api/v1/submission-batches/{batch_id}/file",
        files={"file": (name, content, "text/csv")},
        headers=headers,
    )


def upload_and_validate(
    client, headers, content: bytes, name: str = "upload.csv"
) -> dict:
    batch = create_batch(client, headers)
    uploaded = upload(client, headers, batch["id"], content, name)
    assert uploaded.status_code == 200, uploaded.text
    validated = client.post(
        f"/api/v1/submission-batches/{batch['id']}/validate", headers=headers
    )
    assert validated.status_code == 200, validated.text
    detail = client.get(
        f"/api/v1/submission-batches/{batch['id']}", headers=headers
    )
    assert detail.status_code == 200, detail.text
    return detail.json()
