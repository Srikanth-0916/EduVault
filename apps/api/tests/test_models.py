"""Data model contract: every table in design doc §5.2 must exist."""

from __future__ import annotations

from sqlalchemy import inspect


def test_all_core_tables_create(db):
    inspector = inspect(db.get_bind())
    expected = {"institutions","campuses","programmes","approval_snapshots","intake_allocations",
      "users","organization_memberships","student_identities","student_enrollments","enrollment_versions",
      "submission_batches","submission_rows","validation_runs","validation_findings","duplicate_cases",
      "identity_verifications","consent_grants","verification_requests","verification_receipts",
      "verification_attempts","audit_events","notifications","report_exports","integration_clients"}
    assert expected <= set(inspector.get_table_names())
