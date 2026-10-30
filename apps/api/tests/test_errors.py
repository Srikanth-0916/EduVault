"""Canonical error payload shape: {error:{code,message,details},traceId}."""

from __future__ import annotations


def test_unknown_route_uses_error_envelope(client):
    r = client.get("/api/v1/definitely-not-a-route")
    assert r.status_code == 404
    body = r.json()
    assert set(body.keys()) == {"error", "traceId"}
    assert set(body["error"].keys()) == {"code", "message", "details"}
    assert body["traceId"]


def test_validation_error_uses_error_envelope(client):
    # An invalid JSON POST against a GET-only route flows through the shared
    # envelope (405) or validation envelope (422).
    r = client.post(
        "/api/v1/health",
        content=b"[]",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 405 or r.status_code == 422
    body = r.json()
    assert set(body.keys()) == {"error", "traceId"}


def test_trace_id_echoed_on_response_header(client):
    r = client.get("/api/v1/health", headers={"X-Request-Id": "trc_fixed_123"})
    assert r.headers["X-Request-Id"] == "trc_fixed_123"
