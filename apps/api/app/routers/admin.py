"""System administrator user directory endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.db import get_db
from app.deps import CurrentUser, Pagination
from app.errors import forbidden, not_found, validation_error
from app.models.enums import UserRole, UserStatus
from app.models.master import Institution, OrganizationMembership, User
from app.schemas.ops import UserRoleUpdate, UserStatusUpdate
from app.schemas.users import UserListResponse, UserSummary

router = APIRouter(prefix="/admin/users", tags=["admin"])


def _assert_admin(user: CurrentUser) -> None:
    if "SYSTEM_ADMIN" not in user.roles:
        raise forbidden("System administrator access is required")


def _summary(db: Session, user: User) -> UserSummary:
    memberships = db.scalars(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.is_active.is_(True),
        )
    ).all()
    return UserSummary(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[item.role for item in memberships],
        status=user.status,
        institution_id=next(
            (item.institution_id for item in memberships if item.institution_id), None
        ),
        last_login_at=user.last_login_at,
    )


@router.get("", response_model=UserListResponse)
def list_admin_users(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    pagination: Pagination,
) -> UserListResponse:
    _assert_admin(user)
    page, page_size = pagination
    total = int(db.scalar(select(func.count(User.id))) or 0)
    users = db.scalars(
        select(User).order_by(User.email.asc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return UserListResponse(items=[_summary(db, item) for item in users], total=total)


@router.patch("/{user_id}/status", response_model=UserSummary)
def update_user_status(
    user_id: str,
    payload: UserStatusUpdate,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> UserSummary:
    _assert_admin(user)
    target = db.get(User, user_id)
    if target is None:
        raise not_found("User not found")
    if target.id == user.id and payload.status == UserStatus.SUSPENDED.value:
        raise validation_error("You cannot suspend your own active session")
    target.status = payload.status
    record_audit(
        db,
        actor=user,
        action="ADMIN_USER_STATUS_CHANGED",
        resource_type="user",
        resource_ref=target.id,
        reason=payload.reason,
        metadata={"status": payload.status},
        request=request,
    )
    db.commit()
    return _summary(db, target)


@router.post("/{user_id}/roles", response_model=UserSummary)
def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> UserSummary:
    _assert_admin(user)
    if payload.role not in {item.value for item in UserRole}:
        raise validation_error("Unknown user role")
    institution_roles = {
        UserRole.INSTITUTION_ADMIN.value,
        UserRole.INSTITUTION_OPERATOR.value,
        UserRole.INSTITUTION_NODAL_OFFICER.value,
        UserRole.STUDENT.value,
    }
    if payload.role in institution_roles:
        if not payload.institution_id or db.get(Institution, payload.institution_id) is None:
            raise validation_error("An existing institutionId is required for this role")
    elif payload.institution_id is not None:
        raise validation_error("National roles cannot be assigned an institution scope")
    target = db.get(User, user_id)
    if target is None:
        raise not_found("User not found")
    membership = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == target.id,
            OrganizationMembership.role == payload.role,
            OrganizationMembership.institution_id == payload.institution_id,
            OrganizationMembership.is_active.is_(True),
        )
    )
    if payload.action == "ADD" and membership is None:
        membership = OrganizationMembership(
            user_id=target.id,
            role=payload.role,
            scope="INSTITUTION" if payload.role in institution_roles else "NATIONAL",
            institution_id=payload.institution_id,
            valid_from=__import__("datetime", fromlist=["date"]).date.today(),
            is_active=True,
            assigned_by=user.id,
        )
        db.add(membership)
    elif payload.action == "REMOVE" and membership is not None:
        membership.is_active = False
    record_audit(
        db,
        actor=user,
        action="ADMIN_USER_ROLE_CHANGED",
        resource_type="user",
        resource_ref=target.id,
        reason=payload.reason,
        metadata={"role": payload.role, "action": payload.action},
        request=request,
    )
    db.commit()
    return _summary(db, target)
