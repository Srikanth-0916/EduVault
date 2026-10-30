"""APAAR protection and mock adapter contract tests."""

from __future__ import annotations

from app.adapters.apaar import MockApaarProvider
from app.models.identity import StudentIdentity
from app.security import apaar_lookup_token, mask_apaar
from app.services.apaar import upsert_student_identity, validate_apaar_format
from sqlalchemy import select
from sqlalchemy.orm import Session


def test_masking_and_encryption_roundtrip(db: Session) -> None:
    raw = "123456789012"
    ident = upsert_student_identity(db, raw, "FORMAT_VALID")
    assert ident.apaar_ciphertext != raw
    assert raw not in (ident.apaar_ciphertext or "")
    assert ident.apaar_lookup_token == apaar_lookup_token(raw)
    assert ident.apaar_last4 == "9012"
    assert mask_apaar(raw) == "••••••••9012"


def test_identity_is_deduplicated_by_lookup_token(db: Session) -> None:
    first = upsert_student_identity(db, "111111111111")
    second = upsert_student_identity(db, "111111111111")
    assert first.id == second.id
    assert db.scalar(
        select(StudentIdentity).where(
            StudentIdentity.apaar_lookup_token == apaar_lookup_token("111111111111")
        )
    ) is not None


def test_malformed_and_missing_never_store_ciphertext(db: Session) -> None:
    malformed = upsert_student_identity(db, "ABC123")
    missing = upsert_student_identity(db, "")
    for ident in (malformed, missing):
        assert ident.apaar_ciphertext is None
        assert ident.apaar_lookup_token is None
        assert ident.apaar_last4 is None
    assert malformed.identifier_status == "MALFORMED"
    assert missing.identifier_status == "MISSING"


def test_format_validation_is_separate_from_external_checks() -> None:
    assert validate_apaar_format("123456789012")["status"] == "FORMAT_VALID"
    assert validate_apaar_format("12345678901")["status"] == "MALFORMED"
    assert validate_apaar_format("1234 5678 9012")["status"] == "MALFORMED"
    assert validate_apaar_format("")["status"] == "MISSING"


def test_mock_provider_outcomes_are_deterministic_and_labelled() -> None:
    provider = MockApaarProvider()
    success = provider.verify("111111111111", "enrolment", {})
    assert success.outcome == "SUCCESS"
    assert success.mock is True
    assert success.adapter_version == "mock-1.0"

    assert provider.verify("111111111199", "enrolment", {}).outcome == "MISMATCH"
    assert provider.verify("111111111188", "enrolment", {}).outcome == "UNAVAILABLE"
    assert provider.verify("not-an-apaar", "enrolment", {}).outcome == "NOT_FOUND"


def test_no_raw_apaar_in_seeded_key_or_verification_fields(seeded: Session) -> None:
    identities = seeded.scalars(select(StudentIdentity)).all()
    assert identities
    for identity in identities:
        assert identity.apaar_ciphertext is None or not identity.apaar_ciphertext.isdigit()
        assert identity.key_id in (None, "primary")
