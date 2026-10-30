"""User context and institution user administration schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common import CamelModel


class UserContext(CamelModel):
    id: str
    email: str
    full_name: str
    roles: list[str]
    primary_role: str
    institution_id: str | None = None
    institution_name: str | None = None
    student_identity_id: str | None = None
    mfa_enabled: bool = False


class UserSummary(CamelModel):
    id: str
    email: str
    full_name: str
    roles: list[str]
    status: str
    institution_id: str | None = None
    last_login_at: datetime | None = None


class UserListResponse(CamelModel):
    items: list[UserSummary]
    total: int


class InvitationCreate(CamelModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    role: str = Field(min_length=1, max_length=64)


class InvitationResponse(CamelModel):
    user: UserSummary
    temp_password: str
    note: str = (
        "This demo invitation password is shown once. In production, invitation "
        "delivery must use an approved channel and force a password change."
    )
