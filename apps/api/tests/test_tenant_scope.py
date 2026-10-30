"""Tenant isolation, role guards, and institution user administration."""

from __future__ import annotations

import pytest
from app.deps import (
    active_memberships,
    assert_institution_access,
    build_user_context,
    get_institution_scope,
)
from app.errors import AppError
from app.models.master import User
from app.models.ops import AuditEvent
from sqlalchemy import select
from sqlalchemy.orm import Session
from tests.factories import auth_headers, make_user


def _context(db: Session, email: str):
    user = db.scalar(select(User).where(User.email == email))
    assert user is not None
    return build_user_context(db, user, active_memberships(db, user.id))


def test_operator_cannot_list_institution_users(client, seeded, db: Session):
    headers = auth_headers(client, "operator@demo-ait.edu")
    response = client.get("/api/v1/institutions/me/users", headers=headers)
    assert response.status_code == 403
    event = db.scalar(
        select(AuditEvent)
        .where(AuditEvent.action == "SECURITY_ACCESS_DENIED")
        .order_by(AuditEvent.timestamp.desc())
    )
    assert event is not None
    assert event.metadata_ == {"requiredRoles": ["INSTITUTION_ADMIN"]}


def test_admin_sees_only_own_institution_users(client, seeded):
    headers = auth_headers(client, "admin@demo-ait.edu")
    response = client.get("/api/v1/institutions/me/users", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 4
    assert all(item["institutionId"] == "inst_ait" for item in body["items"])
    emails = {item["email"] for item in body["items"]}
    assert "admin@demo-ait.edu" in emails
    assert "reviewer@aicte.demo" not in emails


def test_admin_of_other_institution_cannot_see_ait_users(client, seeded, db: Session):
    make_user(
        db,
        "INSTITUTION_ADMIN",
        institution_id="inst_bie",
        email="bie-admin@demo-bie.edu",
    )
    headers = auth_headers(client, "bie-admin@demo-bie.edu")
    response = client.get("/api/v1/institutions/me/users", headers=headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["email"] for item in items] == ["bie-admin@demo-bie.edu"]


def test_admin_can_invite_and_new_user_can_login(client, seeded, db: Session):
    headers = auth_headers(client, "admin@demo-ait.edu")
    response = client.post(
        "/api/v1/institutions/me/users/invitations",
        headers=headers,
        json={
            "email": "new.operator@demo-ait.edu",
            "fullName": "New Operator",
            "role": "INSTITUTION_OPERATOR",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["tempPassword"].startswith("Tmp-")
    assert body["user"]["institutionId"] == "inst_ait"
    assert body["user"]["roles"] == ["INSTITUTION_OPERATOR"]

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "new.operator@demo-ait.edu", "password": body["tempPassword"]},
    )
    assert login.status_code == 200
    assert login.json()["user"]["primaryRole"] == "INSTITUTION_OPERATOR"

    audit = db.scalar(select(AuditEvent).where(AuditEvent.action == "USER_INVITED"))
    assert audit is not None
    assert body["tempPassword"] not in str(audit.metadata_)


def test_invitation_cannot_grant_aicte_role(client, seeded):
    headers = auth_headers(client, "admin@demo-ait.edu")
    response = client.post(
        "/api/v1/institutions/me/users/invitations",
        headers=headers,
        json={
            "email": "sneaky@demo-ait.edu",
            "fullName": "Sneaky User",
            "role": "AICTE_REVIEWER",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_duplicate_invitation_is_conflict(client, seeded):
    headers = auth_headers(client, "admin@demo-ait.edu")
    payload = {
        "email": "duplicate@demo-ait.edu",
        "fullName": "Duplicate User",
        "role": "INSTITUTION_OPERATOR",
    }
    assert (
        client.post(
            "/api/v1/institutions/me/users/invitations", headers=headers, json=payload
        ).status_code
        == 201
    )
    second = client.post("/api/v1/institutions/me/users/invitations", headers=headers, json=payload)
    assert second.status_code == 409


def test_cross_tenant_access_is_denied_and_audited(client, seeded, db: Session):
    context = _context(db, "admin@demo-ait.edu")
    assert context.institution_id == "inst_ait"

    assert_institution_access(db, context, "inst_ait")
    with pytest.raises(AppError) as exc:
        assert_institution_access(db, context, "inst_bie")
    assert exc.value.status_code == 403

    event = db.scalar(
        select(AuditEvent)
        .where(AuditEvent.action == "SECURITY_ACCESS_DENIED")
        .order_by(AuditEvent.timestamp.desc())
    )
    assert event is not None
    assert event.resource_ref == "inst_bie"
    assert event.actor_email == "admin@demo-ait.edu"


def test_national_roles_can_traverse_but_analyst_cannot(seeded, db: Session):
    reviewer = _context(db, "reviewer@aicte.demo")
    assert_institution_access(db, reviewer, "inst_bie")

    analyst = _context(db, "analyst@aicte.demo")
    with pytest.raises(AppError):
        assert_institution_access(db, analyst, "inst_bie")


def test_institution_scope_required_for_national_user(seeded, db: Session):
    reviewer = _context(db, "reviewer@aicte.demo")
    with pytest.raises(AppError) as exc:
        get_institution_scope(reviewer)
    assert exc.value.code == "FORBIDDEN"
