"""Authentication endpoints: login and current user."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.db import get_db
from app.deps import CurrentUser, active_memberships, build_user_context
from app.errors import AppError
from app.models.base import utc_now
from app.models.enums import AuditOutcome, UserStatus
from app.models.master import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.users import UserContext
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    """Email/password login. Failures are generic and audited."""
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(func.lower(User.email) == email))

    if (
        user is None
        or user.status != UserStatus.ACTIVE.value
        or not verify_password(payload.password, user.hashed_password)
    ):
        record_audit(
            db,
            actor_email=email,
            action="AUTH_LOGIN_FAILED",
            outcome=AuditOutcome.DENIED,
            resource_type="auth",
            resource_ref="login",
            reason="Invalid credentials",
            request=request,
            commit=True,
        )
        raise AppError(401, "INVALID_CREDENTIALS", "Invalid credentials")

    memberships = active_memberships(db, user.id)
    if not memberships:
        record_audit(
            db,
            actor=user,
            action="AUTH_LOGIN_FAILED",
            outcome=AuditOutcome.DENIED,
            resource_type="auth",
            resource_ref="login",
            reason="No active role",
            request=request,
            commit=True,
        )
        raise AppError(403, "NO_ACTIVE_ROLE", "Your account has no active role")

    context = build_user_context(db, user, memberships)
    token, expires_in = create_access_token(
        user, roles=context.roles, institution_id=context.institution_id
    )
    user.last_login_at = utc_now()
    record_audit(
        db,
        actor=context,
        action="AUTH_LOGIN_SUCCESS",
        resource_type="auth",
        resource_ref="login",
        request=request,
    )
    db.commit()

    return LoginResponse(access_token=token, expires_in=expires_in, user=context)


@router.get("/me", response_model=UserContext)
def me(user: CurrentUser) -> UserContext:
    """Return the authenticated user's live role context."""
    return user
