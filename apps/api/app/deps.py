"""Authentication and authorization dependencies.

Authorization is always resolved from current, active organization memberships
in the database — never from role claims alone. This makes role removal and
institution changes take effect immediately.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date
from typing import Annotated

from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.constants import INSTITUTION_TRAVERSAL_ROLES
from app.db import get_db
from app.errors import AppError, forbidden
from app.models.enums import AuditOutcome, MembershipScope, UserStatus
from app.models.master import Institution, OrganizationMembership, User
from app.schemas.users import UserContext
from app.security import decode_token

_bearer = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


def active_memberships(db: Session, user_id: str) -> list[OrganizationMembership]:
    """Memberships that are active today, not merely rows that exist."""
    today = date.today()
    rows = db.scalars(
        select(OrganizationMembership)
        .where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.is_active.is_(True),
            OrganizationMembership.valid_from <= today,
        )
        .order_by(OrganizationMembership.created_at.asc())
    ).all()
    return [row for row in rows if row.valid_to is None or row.valid_to >= today]


def _role_priority(role: str) -> int:
    order = {
        "INSTITUTION_ADMIN": 0,
        "INSTITUTION_NODAL_OFFICER": 1,
        "INSTITUTION_OPERATOR": 2,
        "STUDENT": 3,
        "AICTE_SUPERVISOR": 10,
        "AICTE_REVIEWER": 11,
        "AICTE_ANALYST": 12,
        "AUDITOR": 13,
        "SYSTEM_ADMIN": 14,
        "EXTERNAL_VERIFIER": 15,
    }
    return order.get(role, 99)


def build_user_context(
    db: Session,
    user: User,
    memberships: Sequence[OrganizationMembership],
    *,
    token_institution_id: str | None = None,
) -> UserContext:
    """Build the public user context from live memberships."""
    if not memberships:
        raise AppError(403, "NO_ACTIVE_ROLE", "Your account has no active role")

    primary = None
    if token_institution_id:
        primary = next(
            (
                m
                for m in memberships
                if m.institution_id == token_institution_id
                and m.scope == MembershipScope.INSTITUTION.value
            ),
            None,
        )
    if primary is None:
        primary = sorted(memberships, key=lambda m: _role_priority(m.role))[0]

    institution_name = None
    if primary.institution_id:
        institution = db.get(Institution, primary.institution_id)
        institution_name = institution.name if institution else None

    roles = sorted({m.role for m in memberships}, key=_role_priority)
    return UserContext(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=roles,
        primary_role=primary.role,
        institution_id=primary.institution_id,
        institution_name=institution_name,
        student_identity_id=user.student_identity_id,
        mfa_enabled=bool(user.mfa_enabled),
    )


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> UserContext:
    """Resolve the bearer token to a live user context."""
    if credentials is None or not credentials.credentials:
        raise AppError(401, "UNAUTHENTICATED", "Authentication required")
    if credentials.scheme.lower() != "bearer":
        raise AppError(401, "UNAUTHENTICATED", "Authentication required")

    claims = decode_token(credentials.credentials)
    user = db.get(User, claims["sub"])
    if user is None or user.status != UserStatus.ACTIVE.value:
        raise AppError(401, "UNAUTHENTICATED", "Authentication required")

    memberships = active_memberships(db, user.id)
    if not memberships:
        record_audit(
            db,
            actor=None,
            actor_email=user.email,
            action="SECURITY_ACCESS_DENIED",
            outcome=AuditOutcome.DENIED,
            resource_type="auth",
            resource_ref="no_active_membership",
            reason="Authenticated account has no active role",
            request=request,
            commit=True,
        )
        raise AppError(403, "NO_ACTIVE_ROLE", "Your account has no active role")

    token_institution = claims.get("institutionId")
    return build_user_context(
        db,
        user,
        memberships,
        token_institution_id=token_institution if isinstance(token_institution, str) else None,
    )


def get_institution_scope(user: UserContext) -> str:
    """Require an institution-scoped context."""
    if not user.institution_id:
        raise forbidden("This action requires an institution account")
    return user.institution_id


def assert_institution_access(
    db: Session,
    user: UserContext,
    institution_id: str,
    request: Request | None = None,
) -> None:
    """Allow own-institution access or an authorized national traversal role."""
    if institution_id == user.institution_id:
        return
    if set(user.roles) & set(INSTITUTION_TRAVERSAL_ROLES):
        return

    record_audit(
        db,
        actor=user,
        action="SECURITY_ACCESS_DENIED",
        outcome=AuditOutcome.DENIED,
        resource_type="institution",
        resource_ref=institution_id,
        reason="Cross-tenant access attempt",
        metadata={"path": request.url.path if request else None},
        request=request,
        commit=True,
    )
    raise forbidden()


def require_roles(*required: str) -> Callable[..., UserContext]:
    """Dependency factory: allow any one of the listed canonical roles."""
    if not required:
        raise ValueError("require_roles needs at least one role")

    def dependency(
        request: Request,
        user: Annotated[UserContext, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> UserContext:
        if set(user.roles) & set(required):
            return user
        record_audit(
            db,
            actor=user,
            action="SECURITY_ACCESS_DENIED",
            outcome=AuditOutcome.DENIED,
            resource_type="route",
            resource_ref=request.url.path[:128],
            reason="Role not permitted for this action",
            metadata={"requiredRoles": list(required)},
            request=request,
            commit=True,
        )
        raise forbidden()

    return dependency


def pagination(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, alias="pageSize")] = 20,
) -> tuple[int, int]:
    return page, page_size


CurrentUser = Annotated[UserContext, Depends(get_current_user)]
Pagination = Annotated[tuple[int, int], Depends(pagination)]

__all__ = [
    "CurrentUser",
    "Pagination",
    "active_memberships",
    "assert_institution_access",
    "build_user_context",
    "get_current_user",
    "get_institution_scope",
    "pagination",
    "require_roles",
]
