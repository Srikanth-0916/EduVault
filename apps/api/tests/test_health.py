"""Health endpoint contract."""

from __future__ import annotations

API_VERSION = "0.1.0"


def test_health_returns_ok(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_reports_version(client):
    r = client.get("/api/v1/health")
    assert r.json()["version"] == API_VERSION
