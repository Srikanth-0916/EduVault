"""Institution-scoped user administration."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.constants import INSTITUTION_STAFF_ROLES
from app.db import get_db
from app.deps import get_institution_scope, require_roles
from app.errors import conflict, validation_error
from app.models.enums import MembershipScope, UserRole, UserStatus
from app.models.master import OrganizationMembership, User
from app.schemas.users import (
    InvitationCreate,
    InvitationResponse,
    UserContext,
    UserListResponse,
    UserSummary,
)
from app.security import hash_password, temporary_password

router = APIRouter(prefix="/institutions/me/users", tags=["institution-users"])

_ADMIN_ONLY = require_roles(UserRole.INSTITUTION_ADMIN.value)


def _summary(user: User, roles: list[str], institution_id: str | None) -> UserSummary:
    return UserSummary(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=roles,
        status=user.status,
        institution_id=institution_id,
        last_login_at=user.last_login_at,
    )


@router.get("", response_model=UserListResponse)
def list_users(
    user: Annotated[UserContext, Depends(_ADMIN_ONLY)],
    db: Annotated[Session, Depends(get_db)],
) -> UserListResponse:
    """List users who belong to the admin's own institution."""
    institution_id = get_institution_scope(user)
    memberships = db.scalars(
        select(OrganizationMembership)
        .where(
            OrganizationMembership.institution_id == institution_id,
            OrganizationMembership.is_active.is_(True),
        )
        .order_by(OrganizationMembership.created_at.asc())
    ).all()

    roles_by_user: dict[str, list[str]] = {}
    for membership in memberships:
        roles_by_user.setdefault(membership.user_id, []).append(membership.role)

    if not roles_by_user:
        return UserListResponse(items=[], total=0)

    users = db.scalars(
        select(User)
        .where(User.id.in_(roles_by_user.keys()))
        .order_by(User.full_name.asc(), User.email.asc())
    ).all()
    items = [
        _summary(item, sorted(set(roles_by_user.get(item.id, []))), institution_id)
        for item in users
    ]
    return UserListResponse(items=items, total=len(items))


@router.post("/invitations", response_model=InvitationResponse, status_code=201)
def invite_user(
    payload: InvitationCreate,
    request: Request,
    user: Annotated[UserContext, Depends(_ADMIN_ONLY)],
    db: Annotated[Session, Depends(get_db)],
) -> InvitationResponse:
    """Create a demo institution membership and return a one-time password.

    There is no real email delivery in the prototype. The response is the only
    place the temporary password is ever exposed; it is excluded from audit
    metadata and logs.
    """
    institution_id = get_institution_scope(user)
    role = payload.role.strip().upper()
    if role not in INSTITUTION_STAFF_ROLES:
        raise validation_error(
            "Only institution administrator, operator, or nodal officer roles can be invited here",
            {"role": role},
        )

    email = str(payload.email).strip().lower()
    existing = db.scalar(select(User).where(func.lower(User.email) == email))
    if existing is not None:
        raise conflict("A user with this email already exists")

    temp_password = temporary_password()
    new_user = User(
        email=email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(temp_password),
        status=UserStatus.ACTIVE.value,
    )
    db.add(new_user)
    db.flush()

    db.add(
        OrganizationMembership(
            user_id=new_user.id,
            institution_id=institution_id,
            role=role,
            scope=MembershipScope.INSTITUTION.value,
            valid_from=date.today(),
            is_active=True,
            assigned_by=user.id,
        )
    )
    record_audit(
        db,
        actor=user,
        action="USER_INVITED",
        resource_type="user",
        resource_ref=new_user.id,
        institution_id=institution_id,
        metadata={"role": role, "email": email},
        request=request,
    )
    db.commit()

    return InvitationResponse(
        user=_summary(new_user, [role], institution_id),
        temp_password=temp_password,
    )
