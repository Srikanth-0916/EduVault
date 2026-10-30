"""Authentication, token revalidation, and audit tests."""

from __future__ import annotations

from app.models.enums import AuditOutcome, UserStatus
from app.models.master import OrganizationMembership, User
from app.models.ops import AuditEvent
from app.security import decode_token
from sqlalchemy import select
from sqlalchemy.orm import Session
from tests.factories import auth_headers


def test_login_and_me(client, seeded):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@demo-ait.edu", "password": "Demo@1234"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["accessToken"]
    assert body["expiresIn"] == 1800
    assert body["user"]["institutionId"] == "inst_ait"
    assert body["user"]["primaryRole"] == "INSTITUTION_OPERATOR"

    claims = decode_token(body["accessToken"])
    assert claims["sub"] == body["user"]["id"]
    assert claims["jti"].startswith("jti_")

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['accessToken']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "operator@demo-ait.edu"
    assert "INSTITUTION_OPERATOR" in me.json()["roles"]


def test_bad_password_is_generic(client, seeded, db: Session):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@demo-ait.edu", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert "password" not in response.json()["error"]["message"].lower()

    event = db.scalar(
        select(AuditEvent)
        .where(AuditEvent.action == "AUTH_LOGIN_FAILED")
        .order_by(AuditEvent.timestamp.desc())
    )
    assert event is not None
    assert event.outcome == AuditOutcome.DENIED.value
    assert event.metadata_ is None


def test_unknown_email_same_generic_error(client, seeded):
    known = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@demo-ait.edu", "password": "wrong"},
    )
    unknown = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrong"},
    )
    assert known.status_code == unknown.status_code == 401
    assert known.json()["error"]["message"] == unknown.json()["error"]["message"]


def test_me_requires_bearer(client, seeded):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"}).status_code
        == 401
    )


def test_suspended_user_cannot_login(client, seeded, db: Session):
    user = db.scalar(select(User).where(User.email == "operator@demo-ait.edu"))
    assert user is not None
    user.status = UserStatus.SUSPENDED.value
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@demo-ait.edu", "password": "Demo@1234"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_token_is_revalidated_after_suspension(client, seeded, db: Session):
    headers = auth_headers(client, "operator@demo-ait.edu")
    user = db.scalar(select(User).where(User.email == "operator@demo-ait.edu"))
    assert user is not None
    user.status = UserStatus.SUSPENDED.value
    db.commit()

    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_token_is_revalidated_after_role_removal(client, seeded, db: Session):
    headers = auth_headers(client, "operator@demo-ait.edu")
    membership = db.scalar(
        select(OrganizationMembership).where(OrganizationMembership.user_id == "usr_ait_operator")
    )
    assert membership is not None
    membership.is_active = False
    db.commit()

    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "NO_ACTIVE_ROLE"


def test_aicte_and_student_contexts(client, seeded):
    reviewer = client.post(
        "/api/v1/auth/login",
        json={"email": "reviewer@aicte.demo", "password": "Demo@1234"},
    )
    assert reviewer.status_code == 200
    assert reviewer.json()["user"]["institutionId"] is None
    assert reviewer.json()["user"]["roles"] == ["AICTE_REVIEWER"]

    student = client.post(
        "/api/v1/auth/login",
        json={"email": "student@demo-ait.edu", "password": "Demo@1234"},
    )
    assert student.status_code == 200
    assert student.json()["user"]["studentIdentityId"] == "sid_demo_student_1"
    assert student.json()["user"]["roles"] == ["STUDENT"]


def test_successful_login_is_audited(client, seeded, db: Session):
    auth_headers(client, "admin@demo-ait.edu")
    event = db.scalar(
        select(AuditEvent)
        .where(AuditEvent.action == "AUTH_LOGIN_SUCCESS")
        .order_by(AuditEvent.timestamp.desc())
    )
    assert event is not None
    assert event.actor_email == "admin@demo-ait.edu"
    assert event.actor_id == "usr_ait_admin"
    assert event.trace_id
