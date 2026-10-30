"""Rate limiting, security headers, and log-redaction contracts."""

from __future__ import annotations

import logging

from app.middleware import RedactSensitiveFilter, redact_text
from tests.factories import auth_headers


def test_login_rate_limit_returns_retry_after(client) -> None:
    payload = {"email": "nobody@example.com", "password": "wrong-password"}
    for _ in range(10):
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 401

    blocked = client.post("/api/v1/auth/login", json=payload)
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "RATE_LIMITED"
    assert int(blocked.headers["Retry-After"]) >= 1
    # The trace/security middleware stays outside the limiter.
    assert blocked.headers["X-Request-Id"].startswith("trc_")
    assert blocked.headers["X-Content-Type-Options"] == "nosniff"


def test_public_verify_rate_limit_is_per_ip_and_route(client, seeded) -> None:
    for _ in range(30):
        response = client.get("/api/v1/public/verify/not-a-real-token")
        assert response.status_code == 410

    blocked = client.get("/api/v1/public/verify/not-a-real-token")
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "RATE_LIMITED"
    assert "Retry-After" in blocked.headers

    # Authentication endpoints have an independent bucket.
    operator = auth_headers(client, "operator@demo-ait.edu")
    assert operator["Authorization"].startswith("Bearer ")


def test_api_responses_carry_security_headers_and_no_banner(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Content-Security-Policy"].startswith("default-src 'none'")
    assert "server" not in {key.lower() for key in response.headers}


def test_redact_text_scrubs_identifiers_and_tokens() -> None:
    text = (
        "student apaar_id=123456789012 and Authorization: Bearer eyJhbGciOi.secret.sig "
        'payload {"password": "Demo@1234", "access_token": "raw-token"}'
    )
    redacted = redact_text(text)
    assert "123456789012" not in redacted
    assert "eyJhbGciOi.secret.sig" not in redacted
    assert "Demo@1234" not in redacted
    assert "raw-token" not in redacted
    assert "[APAAR_REDACTED]" in redact_text("identifier 123456789012")


def test_log_filter_redacts_message_and_arguments() -> None:
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="APAAR %s for token %s",
        args=("123456789012", "Bearer abc.def.ghi"),
        exc_info=None,
    )
    assert RedactSensitiveFilter().filter(record)
    rendered = record.getMessage()
    assert "123456789012" not in rendered
    assert "abc.def.ghi" not in rendered
