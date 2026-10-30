"""Security primitive tests: hashing, JWT, APAAR crypto, tokens, receipts."""

from __future__ import annotations

from app.security import (
    apaar_lookup_token,
    create_access_token,
    decode_token,
    decrypt_apaar,
    encrypt_apaar,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    is_valid_apaar,
    mask_apaar,
    sign_receipt,
    verify_password,
    verify_receipt,
)


def test_password_hash_roundtrip():
    hashed = hash_password("Demo@1234")
    assert hashed != "Demo@1234"
    assert verify_password("Demo@1234", hashed)
    assert not verify_password("wrong", hashed)
    assert not verify_password("Demo@1234", None)


def test_jwt_roundtrip_and_tamper_rejected():
    token, expires_in = create_access_token(
        "usr_test", roles=["INSTITUTION_OPERATOR"], institution_id="inst_ait"
    )
    assert expires_in == 1800
    claims = decode_token(token)
    assert claims["sub"] == "usr_test"
    assert claims["institutionId"] == "inst_ait"
    assert claims["roles"] == ["INSTITUTION_OPERATOR"]
    assert claims["jti"]

    try:
        decode_token(token + "x")
    except Exception as exc:  # AppError
        assert getattr(exc, "status_code", None) == 401
    else:  # pragma: no cover
        raise AssertionError("tampered token was accepted")


def test_apaar_format_and_masking():
    assert is_valid_apaar("123456789012")
    assert is_valid_apaar(" 123456789012 ")
    assert not is_valid_apaar("12345678901")
    assert not is_valid_apaar("12345678901A")
    assert not is_valid_apaar("१२३४५६७८९०१२")
    assert mask_apaar("123456789012") == "••••••••9012"
    assert mask_apaar(None) == "••••••••••••"


def test_apaar_encryption_and_lookup():
    ciphertext = encrypt_apaar("123456789012")
    assert ciphertext != "123456789012"
    assert "123456789012" not in ciphertext
    assert decrypt_apaar(ciphertext) == "123456789012"
    assert decrypt_apaar(None) is None

    first = apaar_lookup_token("123456789012")
    second = apaar_lookup_token("123456789012")
    assert first == second
    assert first != apaar_lookup_token("123456789013")
    assert len(first) == 64


def test_opaque_token_is_hashed():
    raw, digest = generate_opaque_token()
    assert len(raw) >= 32
    assert digest == hash_opaque_token(raw)
    assert raw not in digest
    raw2, digest2 = generate_opaque_token()
    assert raw != raw2
    assert digest != digest2


def test_receipt_signature():
    payload = {
        "claims": [{"key": "INSTITUTION", "value": "Aarav (Demo)"}],
        "expiresAt": "2026-10-31T00:00:00Z",
    }
    receipt = sign_receipt(payload)
    assert receipt["algorithm"] == "HMAC-SHA256"
    assert receipt["keyId"] == "primary"
    assert len(receipt["signature"]) == 64
    assert verify_receipt(payload, receipt["signature"])
    tampered = {**payload, "expiresAt": "2027-01-01T00:00:00Z"}
    assert not verify_receipt(tampered, receipt["signature"])
