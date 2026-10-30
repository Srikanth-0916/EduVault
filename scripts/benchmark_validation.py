#!/usr/bin/env python3
"""Benchmark CSV upload + validation with 10,000 synthetic rows.

Usage (from the repository root)::

    cd apps/api && uv run python ../../scripts/benchmark_validation.py

The script uses a throwaway SQLite database and the deterministic synthetic
seed. It prints row count and elapsed time; the PRD target is under 300 seconds
for 10,000 rows. All data is fictional.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"

_temp = tempfile.TemporaryDirectory(prefix="apaar-benchmark-")
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_temp.name) / 'benchmark.db'}"

sys.path.insert(0, str(API_ROOT))

from app.db import create_all, drop_all, get_session_factory  # noqa: E402
from app.main import create_app  # noqa: E402
from app.seed import seed  # noqa: E402
from app.services.csv_import import ALL_HEADERS  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

ROW_COUNT = 10_000


def build_csv(row_count: int = ROW_COUNT) -> bytes:
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
        values["institution_student_id"] = f"BENCH{index:07d}"
        values["apaar_id"] = f"6{index:011d}"
        values["student_name"] = f"Benchmark Student {index}"
        lines.append(",".join(values[header] for header in ALL_HEADERS))
    return ("\n".join(lines) + "\n").encode()


def main() -> int:
    create_all()
    with get_session_factory()() as session:
        seed(session=session)
        session.commit()

    application = create_app()
    with TestClient(application) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "operator@demo-ait.edu", "password": "Demo@1234"},
        )
        login.raise_for_status()
        headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
        batch = client.post(
            "/api/v1/submission-batches",
            json={"academicYear": "2026-27", "sourceType": "CSV_UPLOAD"},
            headers=headers,
        )
        batch.raise_for_status()
        batch_id = batch.json()["id"]

        content = build_csv()
        started = time.perf_counter()
        uploaded = client.post(
            f"/api/v1/submission-batches/{batch_id}/file",
            files={"file": ("benchmark.csv", content, "text/csv")},
            headers=headers,
        )
        upload_seconds = time.perf_counter() - started
        uploaded.raise_for_status()

        started = time.perf_counter()
        validated = client.post(
            f"/api/v1/submission-batches/{batch_id}/validate", headers=headers
        )
        validation_seconds = time.perf_counter() - started
        validated.raise_for_status()

    body = validated.json()
    summary = body.get("validationSummary") or {}
    print(f"rows: {ROW_COUNT:,}")
    print(f"upload_seconds: {upload_seconds:.2f}")
    print(f"validation_seconds: {validation_seconds:.2f}")
    print(f"total_seconds: {upload_seconds + validation_seconds:.2f}")
    print(f"status: {body['status']}")
    print(f"blocking_findings: {summary.get('blockingFindings', 0)}")
    print(f"findings_by_rule: {summary.get('byRule', {})}")
    for finding in (body.get("findings") or [])[:5]:
        print(
            "first_finding:",
            finding.get("code"),
            finding.get("message"),
        )
    under_target = validation_seconds < 300
    print("target_under_300_seconds:", "PASS" if under_target else "FAIL")
    drop_all()
    _temp.cleanup()
    return 0 if under_target else 1


if __name__ == "__main__":
    raise SystemExit(main())
