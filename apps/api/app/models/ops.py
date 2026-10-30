"""Operational tables: audit trail, notifications, exports, integrations.

Tables: ``audit_events``, ``notifications``, ``report_exports``,
``integration_clients``.

The audit table is append-only through the API: no update/delete routes exist.
Audit metadata must never contain raw APAAR values, passwords, or tokens.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pk, sa_enum, utc_now
from app.models.enums import (
    AuditOutcome,
    IntegrationClientStatus,
    NotificationChannel,
    NotificationDeliveryStatus,
)


class AuditEvent(Base):
    """Append-only audit evidence for every material action.

    ``metadata`` is a free-form JSON blob constrained by the audit helper:
    masked identifiers only, plus request context (IP, agent, trace id).
    """

    __tablename__ = "audit_events"

    id: Mapped[str] = pk()
    actor_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), default=None)
    actor_role: Mapped[str | None] = mapped_column(String(64), default=None)
    action: Mapped[str] = mapped_column(String(96), index=True)
    outcome: Mapped[str] = mapped_column(sa_enum(AuditOutcome), default=AuditOutcome.SUCCESS.value)
    resource_type: Mapped[str] = mapped_column(String(64), index=True)
    resource_ref: Mapped[str | None] = mapped_column(String(128), default=None, index=True)
    institution_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("institutions.id"), default=None, index=True
    )
    reason: Mapped[str | None] = mapped_column(String(1024), default=None)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    ip_address: Mapped[str | None] = mapped_column(String(64), default=None)
    user_agent: Mapped[str | None] = mapped_column(String(512), default=None)
    trace_id: Mapped[str | None] = mapped_column(String(64), default=None)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )


class Notification(TimestampMixin, Base):
    """In-app (and mock email) notification delivered to one recipient."""

    __tablename__ = "notifications"

    id: Mapped[str] = pk()
    recipient_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), default=None, index=True
    )
    institution_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("institutions.id"), default=None, index=True
    )
    event_type: Mapped[str] = mapped_column(String(96))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(String(2048))
    channel: Mapped[str] = mapped_column(
        sa_enum(NotificationChannel), default=NotificationChannel.IN_APP.value
    )
    delivery_status: Mapped[str] = mapped_column(
        sa_enum(NotificationDeliveryStatus), default=NotificationDeliveryStatus.QUEUED.value
    )
    resource_type: Mapped[str | None] = mapped_column(String(64), default=None)
    resource_ref: Mapped[str | None] = mapped_column(String(128), default=None)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class ReportExport(TimestampMixin, Base):
    """Record of one generated export (audited, scoped, aggregate-first)."""

    __tablename__ = "report_exports"

    id: Mapped[str] = pk()
    report_type: Mapped[str] = mapped_column(String(64), index=True)
    requested_by: Mapped[str | None] = mapped_column(String(36), default=None)
    requested_role: Mapped[str | None] = mapped_column(String(64), default=None)
    institution_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("institutions.id"), default=None, index=True
    )
    filters: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    format: Mapped[str] = mapped_column(String(16), default="CSV")
    file_storage_key: Mapped[str | None] = mapped_column(String(512), default=None)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    contains_direct_identifiers: Mapped[bool] = mapped_column(Boolean, default=False)


class IntegrationClient(TimestampMixin, Base):
    """Machine-to-machine integration identity (seeded/read-only for MVP)."""

    __tablename__ = "integration_clients"

    id: Mapped[str] = pk()
    organization_name: Mapped[str] = mapped_column(String(255))
    contact_email: Mapped[str | None] = mapped_column(String(255), default=None)
    scopes: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)  # list of scope keys
    credential_ref: Mapped[str | None] = mapped_column(String(255), default=None)
    status: Mapped[str] = mapped_column(
        sa_enum(IntegrationClientStatus), default=IntegrationClientStatus.ACTIVE.value
    )
    read_only: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
