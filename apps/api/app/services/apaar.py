"""APAAR identity helpers: protected upsert plus format state.

Raw APAAR values enter this module once (from a CSV row or portal form) and are
immediately encrypted + tokenized. Callers receive the identity row and must
never persist the raw value themselves.
"""

from __future__ import annotations

from app.models.enums import IdentityStatus
from app.models.identity import StudentIdentity
from app.security import (
    apaar_key_id,
    apaar_lookup_token,
    encrypt_apaar,
    is_valid_apaar,
    mask_apaar,
    mask_apaar_last4,
    normalize_apaar,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

_STATUS_RANK = {
    IdentityStatus.MISSING.value: 0,
    IdentityStatus.MALFORMED.value: 0,
    IdentityStatus.FORMAT_VALID.value: 1,
    IdentityStatus.PENDING_EXTERNAL_CHECK.value: 2,
    IdentityStatus.EXTERNAL_UNAVAILABLE.value: 3,
    IdentityStatus.EXTERNAL_MISMATCH.value: 4,
    IdentityStatus.MANUAL_REVIEW.value: 4,
    IdentityStatus.EXTERNALLY_CONFIRMED.value: 5,
    IdentityStatus.CORRECTED.value: 2,
}


def validate_apaar_format(value: str | None) -> dict[str, str]:
    """Return the format-only state for a CSV/portal value.

    This is intentionally *not* an external verification result.
    """
    normalized = normalize_apaar(value)
    if not normalized:
        return {
            "status": IdentityStatus.MISSING.value,
            "message": "APAAR ID is required for this record",
        }
    if not is_valid_apaar(normalized):
        return {
            "status": IdentityStatus.MALFORMED.value,
            "message": "APAAR ID must be exactly 12 digits",
        }
    return {
        "status": IdentityStatus.FORMAT_VALID.value,
        "message": "APAAR format is valid; external checks are separate",
    }


def _upgrade_status(current: str | None, requested: str) -> str:
    """Never downgrade an external outcome during a re-import."""
    current = current or IdentityStatus.MISSING.value
    return (
        requested
        if _STATUS_RANK.get(requested, 0) >= _STATUS_RANK.get(current, 0)
        else current
    )


def upsert_student_identity(
    db: Session,
    raw_apaar: str | None,
    status: str | IdentityStatus = IdentityStatus.FORMAT_VALID,
) -> StudentIdentity:
    """Create or reuse the protected identity for a raw APAAR value.

    Valid values are deduplicated by keyed lookup token. Missing/malformed
    values deliberately have no ciphertext, token or last-four fragment, so no
    unsupported fragment can be mistaken for a real identifier.
    """
    requested = status.value if isinstance(status, IdentityStatus) else str(status)
    normalized = normalize_apaar(raw_apaar)

    if not is_valid_apaar(normalized):
        derived = (
            IdentityStatus.MISSING.value
            if not normalized
            else IdentityStatus.MALFORMED.value
        )
        identity = StudentIdentity(
            identifier_status=derived,
            apaar_ciphertext=None,
            apaar_lookup_token=None,
            apaar_last4=None,
            key_id=None,
        )
        db.add(identity)
        db.flush()
        return identity

    assert normalized is not None
    token = apaar_lookup_token(normalized)
    existing = db.scalar(
        select(StudentIdentity).where(StudentIdentity.apaar_lookup_token == token)
    )
    if existing is not None:
        existing.identifier_status = _upgrade_status(existing.identifier_status, requested)
        return existing

    identity = StudentIdentity(
        apaar_ciphertext=encrypt_apaar(normalized),
        apaar_lookup_token=token,
        apaar_last4=normalized[-4:],
        identifier_status=requested
        if requested in {member.value for member in IdentityStatus}
        else IdentityStatus.FORMAT_VALID.value,
        key_id=apaar_key_id(),
    )
    db.add(identity)
    db.flush()
    return identity


def masked_identity(identity: StudentIdentity | None) -> str:
    """Display helper for an identity row; never decrypts for display."""
    if identity is None:
        return mask_apaar(None)
    return mask_apaar_last4(identity.apaar_last4)
