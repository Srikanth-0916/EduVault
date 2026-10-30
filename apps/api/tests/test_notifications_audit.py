"""Notification and append-only audit access tests."""

from tests.factories import auth_headers


def test_notifications_are_recipient_scoped_and_readable(client, seeded) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    response = client.get("/api/v1/notifications", headers=operator)
    assert response.status_code == 200, response.text
    assert "items" in response.json()

    other = auth_headers(client, "reviewer@aicte.demo")
    assert client.get("/api/v1/notifications", headers=other).status_code == 200
    if response.json()["items"]:
        item_id = response.json()["items"][0]["id"]
        marked = client.post(f"/api/v1/notifications/{item_id}/read", headers=operator)
        assert marked.status_code == 200, marked.text
        assert marked.json()["readAt"]


def test_audit_requires_auditor_and_filters_without_raw_identifiers(client, seeded) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    auditor = auth_headers(client, "auditor@aicte.demo")
    assert client.get("/api/v1/audit-events", headers=operator).status_code == 403
    response = client.get(
        "/api/v1/audit-events?resourceType=submission_batch",
        headers=auditor,
    )
    assert response.status_code == 200, response.text
    assert "items" in response.json()
    assert "123456789012" not in response.text

    filtered = client.get(
        "/api/v1/audit-events?from=2099-01-01T00:00:00&to=2099-01-02T00:00:00",
        headers=auditor,
    )
    assert filtered.status_code == 200, filtered.text
    assert filtered.json()["total"] == 0


def test_system_admin_user_directory_can_change_status_but_auditor_cannot(client, seeded) -> None:
    sysadmin = auth_headers(client, "sysadmin@aicte.demo")
    auditor = auth_headers(client, "auditor@aicte.demo")
    response = client.patch(
        "/api/v1/admin/users/usr_ait_operator/status",
        json={"status": "SUSPENDED", "reason": "Synthetic access test"},
        headers=auditor,
    )
    assert response.status_code == 403
    changed = client.patch(
        "/api/v1/admin/users/usr_ait_operator/status",
        json={"status": "SUSPENDED", "reason": "Synthetic access test"},
        headers=sysadmin,
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["status"] == "SUSPENDED"
