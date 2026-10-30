"""Recipient-scoped in-app notification endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import CurrentUser, Pagination
from app.errors import forbidden, not_found
from app.models.base import utc_now
from app.models.ops import Notification
from app.schemas.ops import NotificationListResponse, NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _out(item: Notification) -> NotificationOut:
    return NotificationOut(
        id=item.id,
        event_type=item.event_type,
        title=item.title,
        body=item.body,
        channel=item.channel,
        delivery_status=item.delivery_status,
        resource_type=item.resource_type,
        resource_ref=item.resource_ref,
        read_at=item.read_at,
        created_at=item.created_at,
    )


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    pagination: Pagination,
) -> NotificationListResponse:
    page, page_size = pagination
    predicate = Notification.recipient_user_id == user.id
    total = int(db.scalar(select(func.count(Notification.id)).where(predicate)) or 0)
    unread = int(
        db.scalar(
            select(func.count(Notification.id)).where(
                predicate,
                Notification.read_at.is_(None),
                Notification.channel == "IN_APP",
            )
        )
        or 0
    )
    items = db.scalars(
        select(Notification)
        .where(predicate)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return NotificationListResponse(
        items=[_out(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
        unread=unread,
    )


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> NotificationOut:
    item = db.get(Notification, notification_id)
    if item is None:
        raise not_found("Notification not found")
    if item.recipient_user_id != user.id:
        raise forbidden()
    item.read_at = utc_now()
    db.commit()
    return _out(item)


@router.post("/read-all")
def mark_all_notifications_read(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, int]:
    items = db.scalars(
        select(Notification).where(
            Notification.recipient_user_id == user.id,
            Notification.read_at.is_(None),
            Notification.channel == "IN_APP",
        )
    ).all()
    now = utc_now()
    for item in items:
        item.read_at = now
    db.commit()
    return {"updated": len(items)}
