"""Authentication request/response schemas."""

from __future__ import annotations

from pydantic import EmailStr, Field

from app.schemas.common import CamelModel
from app.schemas.users import UserContext


class LoginRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=512)


class LoginResponse(CamelModel):
    access_token: str
    expires_in: int
    user: UserContext
