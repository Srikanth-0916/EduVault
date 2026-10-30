"""Operations, notification, audit, and admin schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from app.schemas.common import CamelModel


class NotificationOut(CamelModel):
    id: str
    event_type: str
    title: str
    body: str
    channel: str
    delivery_status: str
    resource_type: str | None = None
    resource_ref: str | None = None
    read_at: datetime | None = None
    created_at: datetime | None = None


class NotificationListResponse(CamelModel):
    items: list[NotificationOut]
    page: int
    page_size: int
    total: int
    unread: int


class AuditEventOut(CamelModel):
    id: str
    actor_id: str | None = None
    actor_email: str | None = None
    actor_role: str | None = None
    action: str
    outcome: str
    resource_type: str
    resource_ref: str | None = None
    institution_id: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] | None = None
    timestamp: datetime


class AuditEventListResponse(CamelModel):
    items: list[AuditEventOut]
    page: int
    page_size: int
    total: int


class UserStatusUpdate(CamelModel):
    status: Literal["ACTIVE", "SUSPENDED", "PENDING_INVITATION"]
    reason: str = Field(min_length=3, max_length=512)


class UserRoleUpdate(CamelModel):
    role: str
    action: Literal["ADD", "REMOVE"]
    reason: str = Field(min_length=3, max_length=512)
    institution_id: str | None = None
