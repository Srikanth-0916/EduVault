"""Security primitives: passwords, JWT, APAAR crypto, tokens and receipts.

The implementation is deliberately small and explicit so that the prototype's
security claims can be reviewed. Production still requires managed keys, an
external identity provider, and key rotation; see ``docs/security.md``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.fernet import Fernet, InvalidToken
from pwdlib import PasswordHash

from app.config import get_settings
from app.errors import AppError

JWT_ALGORITHM = "HS256"
_TOKEN_ISSUER = "apaar-sdmv-api"
_TOKEN_AUDIENCE = "apaar-sdmv-web"
_APAAR_PATTERN = re.compile(r"^[0-9]{12}$")
_KEY_ID = "primary"

_password_hash = PasswordHash.recommended()


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Argon2id hash (pwdlib's recommended configuration)."""
    if not password:
        raise ValueError("password must not be empty")
    return _password_hash.hash(password)


def verify_password(password: str, hashed_password: str | None) -> bool:
    """Constant-time password check that never reveals why it failed."""
    if not password or not hashed_password:
        return False
    try:
        return bool(_password_hash.verify(password, hashed_password))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


def _jwt_settings() -> tuple[str, str, str, int]:
    settings = get_settings()
    issuer = settings.jwt_issuer or _TOKEN_ISSUER
    audience = settings.jwt_audience or _TOKEN_AUDIENCE
    return settings.jwt_secret, issuer, audience, settings.access_token_minutes


def create_access_token(
    user: Any,
    *,
    roles: Sequence[str] = (),
    institution_id: str | None = None,
) -> tuple[str, int]:
    """Create a short-lived HS256 access token.

    Returns ``(token, expires_in_seconds)``. Role and institution claims are
    informational; authorization always reloads memberships from the database
    so a stale token cannot retain revoked access.
    """
    secret, issuer, audience, minutes = _jwt_settings()
    user_id = getattr(user, "id", None) or str(user)
    now = datetime.now(UTC)
    expires_in = max(1, int(minutes)) * 60
    payload = {
        "sub": str(user_id),
        "roles": list(roles),
        "institutionId": institution_id,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(seconds=expires_in),
        "jti": f"jti_{secrets.token_urlsafe(16)}",
    }
    token = jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)
    return token, expires_in


def decode_token(token: str) -> dict[str, Any]:
    """Validate signature/issuer/audience/expiry and return the claims."""
    secret, issuer, audience, _ = _jwt_settings()
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            audience=audience,
            issuer=issuer,
            options={"require": ["sub", "iat", "exp", "jti"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AppError(401, "UNAUTHENTICATED", "Your session has expired") from exc
    except jwt.PyJWTError as exc:
        raise AppError(401, "UNAUTHENTICATED", "Authentication required") from exc
    if not isinstance(claims.get("sub"), str) or not claims["sub"]:
        raise AppError(401, "UNAUTHENTICATED", "Authentication required")
    return claims


# ---------------------------------------------------------------------------
# APAAR protection
# ---------------------------------------------------------------------------


def normalize_apaar(value: str | None) -> str | None:
    """Trim separators while keeping format errors visible to the caller.

    Only surrounding whitespace is removed. Internal spaces/hyphens remain and
    therefore fail the strict 12-ASCII-digit check.
    """
    if value is None:
        return None
    return value.strip()


def is_valid_apaar(value: str | None) -> bool:
    """True only for exactly 12 ASCII digits. This is a *format* check."""
    normalized = normalize_apaar(value)
    return bool(normalized and _APAAR_PATTERN.fullmatch(normalized))


def mask_apaar(value: str | None) -> str:
    """Display fragment: last four digits only."""
    normalized = normalize_apaar(value)
    if not normalized:
        return "••••••••••••"
    digits = re.sub(r"\D", "", normalized)
    if len(digits) >= 4:
        return f"••••••••{digits[-4:]}"
    return "••••••••••••"


def mask_apaar_last4(last4: str | None) -> str:
    if not last4:
        return "••••••••••••"
    return f"••••••••{last4[-4:]}"


def _fernet() -> Fernet:
    settings = get_settings()
    # Derive a valid Fernet key from arbitrary deployment secret material. In
    # production the configured value should already come from a KMS.
    digest = hashlib.sha256(settings.apaar_encryption_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_apaar(value: str) -> str:
    if not is_valid_apaar(value):
        raise ValueError("APAAR must be exactly 12 ASCII digits")
    return _fernet().encrypt(value.strip().encode("utf-8")).decode("ascii")


def decrypt_apaar(ciphertext: str | None) -> str | None:
    if not ciphertext:
        return None
    try:
        return _fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise AppError(500, "INTERNAL_ERROR", "Protected identifier could not be read") from exc


def apaar_lookup_token(value: str) -> str:
    """Keyed HMAC used for exact matching; never display or export this value."""
    settings = get_settings()
    normalized = normalize_apaar(value) or ""
    return hmac.new(
        settings.apaar_lookup_key.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def apaar_key_id() -> str:
    return _KEY_ID


# ---------------------------------------------------------------------------
# Opaque verification tokens and signed receipts
# ---------------------------------------------------------------------------


def generate_opaque_token() -> tuple[str, str]:
    """Return ``(raw_token, sha256_hex_digest)``.

    Only the digest is stored at rest. The raw token is shown once to the
    student and placed in the verification URL.
    """
    raw = secrets.token_urlsafe(32)
    return raw, hash_opaque_token(raw)


def hash_opaque_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sign_receipt(payload: Mapping[str, Any]) -> dict[str, str]:
    """HMAC-SHA256 over canonical JSON. Prototype key id is ``primary``."""
    settings = get_settings()
    body = _canonical_json(payload)
    signature = hmac.new(
        settings.receipt_signing_key.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    return {
        "algorithm": "HMAC-SHA256",
        "keyId": _KEY_ID,
        "signature": signature,
        "payloadHash": hashlib.sha256(body).hexdigest(),
    }


def verify_receipt(payload: Mapping[str, Any], signature: str) -> bool:
    expected = sign_receipt(payload)["signature"]
    return hmac.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# Miscellaneous
# ---------------------------------------------------------------------------


def redact_secret(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) <= 6:
        return "***"
    return f"{value[:3]}***{value[-2:]}"


def temporary_password() -> str:
    """One-time invitation password for the demo (not emailed in the prototype)."""
    return f"Tmp-{secrets.token_urlsafe(9)}"
