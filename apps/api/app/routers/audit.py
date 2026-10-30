"""Read-only audit trail endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import sanitize_metadata
from app.db import get_db
from app.deps import CurrentUser, Pagination
from app.errors import forbidden
from app.models.ops import AuditEvent
from app.schemas.ops import AuditEventListResponse, AuditEventOut

router = APIRouter(prefix="/audit-events", tags=["audit"])
_READ = {"AUDITOR", "AICTE_SUPERVISOR", "SYSTEM_ADMIN"}


def _out(event: AuditEvent) -> AuditEventOut:
    return AuditEventOut(
        id=event.id,
        actor_id=event.actor_id,
        actor_email=event.actor_email,
        actor_role=event.actor_role,
        action=event.action,
        outcome=event.outcome,
        resource_type=event.resource_type,
        resource_ref=event.resource_ref,
        institution_id=event.institution_id,
        reason=event.reason,
        metadata=sanitize_metadata(event.metadata_ or {}),
        timestamp=event.timestamp,
    )


@router.get("", response_model=AuditEventListResponse)
def list_audit_events(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    pagination: Pagination,
    action: Annotated[str | None, Query()] = None,
    actor_id: Annotated[str | None, Query(alias="actorId")] = None,
    resource_type: Annotated[str | None, Query(alias="resourceType")] = None,
    resource_ref: Annotated[str | None, Query(alias="resourceRef")] = None,
    institution_id: Annotated[str | None, Query(alias="institutionId")] = None,
    from_at: Annotated[datetime | None, Query(alias="from")] = None,
    to_at: Annotated[datetime | None, Query(alias="to")] = None,
) -> AuditEventListResponse:
    if not set(user.roles) & _READ:
        raise forbidden("Audit access is restricted to oversight roles")
    statement = select(AuditEvent)
    count_statement = select(func.count(AuditEvent.id))
    filters = []
    for column, value in (
        (AuditEvent.action, action),
        (AuditEvent.actor_id, actor_id),
        (AuditEvent.resource_type, resource_type),
        (AuditEvent.resource_ref, resource_ref),
        (AuditEvent.institution_id, institution_id),
    ):
        if value:
            filters.append(column == value)
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    if from_at:
        statement = statement.where(AuditEvent.timestamp >= from_at)
        count_statement = count_statement.where(AuditEvent.timestamp >= from_at)
    if to_at:
        statement = statement.where(AuditEvent.timestamp <= to_at)
        count_statement = count_statement.where(AuditEvent.timestamp <= to_at)
    page, page_size = pagination
    total = int(db.scalar(count_statement) or 0)
    events = db.scalars(
        statement.order_by(AuditEvent.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return AuditEventListResponse(
        items=[_out(event) for event in events],
        page=page,
        page_size=page_size,
        total=total,
    )
