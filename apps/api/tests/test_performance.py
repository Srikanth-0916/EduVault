"""Validation performance smoke: 2,000 rows must stay well under the NFR."""

from __future__ import annotations

import time

from app.services.csv_import import ALL_HEADERS
from tests.factories import auth_headers
from tests.helpers import create_batch, upload


def _csv(row_count: int) -> bytes:
    values = {
        "institution_student_id": "",
        "apaar_id": "",
        "student_name": "",
        "programme_code": "CSE",
        "campus_code": "AIT-MAIN",
        "academic_year": "2026-27",
        "admission_date": "2026-07-20",
        "exit_date": "",
        "enrollment_status": "ACTIVE",
        "seat_classification": "APPROVED_REGULAR",
        "admission_category": "GENERAL",
        "nri_status": "NO",
        "oci_status": "NO",
        "foreign_national_status": "NO",
        "approval_reference": "",
        "date_of_birth": "2007-01-01",
        "gender": "FEMALE",
    }
    lines = [",".join(ALL_HEADERS)]
    for index in range(1, row_count + 1):
        values["institution_student_id"] = f"PERF{index:06d}"
        values["apaar_id"] = f"8{index:011d}"
        values["student_name"] = f"Performance Student {index}"
        lines.append(",".join(values[header] for header in ALL_HEADERS))
    return ("\n".join(lines) + "\n").encode()


def test_validation_of_two_thousand_rows_is_under_sixty_seconds(client, seeded) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    batch = create_batch(client, operator)
    content = _csv(2_000)
    uploaded = upload(client, operator, batch["id"], content)
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["rowCount"] == 2_000

    started = time.perf_counter()
    validated = client.post(f"/api/v1/submission-batches/{batch['id']}/validate", headers=operator)
    duration = time.perf_counter() - started
    assert validated.status_code == 200, validated.text
    print(f"validated 2,000 rows in {duration:.2f}s")
    assert duration < 60
