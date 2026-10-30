"""Test factories for auth and tenant-scope tests."""

from __future__ import annotations

import secrets
from datetime import date

from app.constants import DEMO_PASSWORD, INSTITUTION_TRAVERSAL_ROLES
from app.models.enums import (
    InstitutionStatus,
    InstitutionType,
    MembershipScope,
    UserStatus,
)
from app.models.master import Institution, OrganizationMembership, User
from app.security import hash_password
from sqlalchemy.orm import Session


def make_institution(
    db: Session,
    *,
    name: str = "Test Institute (Demo)",
    code: str | None = None,
) -> Institution:
    suffix = secrets.token_hex(4).upper()
    institution = Institution(
        aicte_institution_code=code or f"TEST-{suffix}",
        name=name,
        institution_type=InstitutionType.PRIVATE_SELF_FINANCED.value,
        status=InstitutionStatus.ACTIVE.value,
        state="Maharashtra",
        city="Pune",
    )
    db.add(institution)
    db.commit()
    return institution


def make_user(
    db: Session,
    role: str,
    *,
    institution_id: str | None = None,
    email: str | None = None,
    full_name: str = "Test User",
    password: str = DEMO_PASSWORD,
    status: str = UserStatus.ACTIVE.value,
    membership_active: bool = True,
) -> User:
    suffix = secrets.token_hex(4)
    user = User(
        email=email or f"user-{suffix}@example.com",
        full_name=full_name,
        hashed_password=hash_password(password),
        status=status,
    )
    db.add(user)
    db.flush()

    scope = (
        MembershipScope.INSTITUTION.value
        if institution_id
        else MembershipScope.NATIONAL.value
    )
    db.add(
        OrganizationMembership(
            user_id=user.id,
            institution_id=institution_id,
            role=role,
            scope=scope,
            valid_from=date(2025, 1, 1),
            is_active=membership_active,
        )
    )
    db.commit()
    return user


def auth_headers(client, email: str, password: str = DEMO_PASSWORD) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


def is_national_role(role: str) -> bool:
    return role in INSTITUTION_TRAVERSAL_ROLES
