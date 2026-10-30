"""Notification fan-out for in-app and mock email channels."""

from __future__ import annotations

from collections.abc import Iterable

from app.adapters.notifications import get_notification_adapter
from app.models.enums import (
    NotificationChannel,
    NotificationDeliveryStatus,
    UserStatus,
)
from app.models.master import OrganizationMembership, User
from app.models.ops import Notification
from sqlalchemy import select
from sqlalchemy.orm import Session


def _recipients_for_roles(
    db: Session, roles: Iterable[str], institution_id: str | None = None
) -> list[User]:
    statement = (
        select(User)
        .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
        .where(
            OrganizationMembership.role.in_(list(roles)),
            OrganizationMembership.is_active.is_(True),
            User.status == UserStatus.ACTIVE.value,
        )
        .distinct()
    )
    if institution_id is not None:
        statement = statement.where(OrganizationMembership.institution_id == institution_id)
    return list(db.scalars(statement).all())


def notify_users(
    db: Session,
    *,
    recipients: Iterable[str | None],
    event_type: str,
    title: str,
    body: str,
    institution_id: str | None = None,
    resource_type: str | None = None,
    resource_ref: str | None = None,
) -> list[Notification]:
    created: list[Notification] = []
    adapter = get_notification_adapter()
    for recipient in sorted({item for item in recipients if item}):
        created.append(
            Notification(
                recipient_user_id=recipient,
                institution_id=institution_id,
                event_type=event_type,
                title=title,
                body=body,
                channel=NotificationChannel.IN_APP.value,
                delivery_status=NotificationDeliveryStatus.DELIVERED.value,
                resource_type=resource_type,
                resource_ref=resource_ref,
            )
        )
        delivery = adapter.send_email(recipient, title, body)
        created.append(
            Notification(
                recipient_user_id=recipient,
                institution_id=institution_id,
                event_type=event_type,
                title=title,
                body=body,
                channel=NotificationChannel.EMAIL.value,
                delivery_status=delivery.status,
                resource_type=resource_type,
                resource_ref=resource_ref,
            )
        )
    for notification in created:
        db.add(notification)
    if created:
        db.flush()
    return created


def notify_institution_roles(
    db: Session,
    *,
    institution_id: str,
    roles: Iterable[str],
    event_type: str,
    title: str,
    body: str,
    resource_type: str | None = None,
    resource_ref: str | None = None,
    extra_recipients: Iterable[str | None] = (),
) -> list[Notification]:
    users = _recipients_for_roles(db, roles, institution_id)
    recipients = [user.id for user in users]
    recipients.extend(extra_recipients)
    return notify_users(
        db,
        recipients=recipients,
        event_type=event_type,
        title=title,
        body=body,
        institution_id=institution_id,
        resource_type=resource_type,
        resource_ref=resource_ref,
    )


def notify_national_roles(
    db: Session,
    *,
    roles: Iterable[str],
    event_type: str,
    title: str,
    body: str,
    resource_type: str | None = None,
    resource_ref: str | None = None,
) -> list[Notification]:
    users = _recipients_for_roles(db, roles)
    return notify_users(
        db,
        recipients=[user.id for user in users],
        event_type=event_type,
        title=title,
        body=body,
        resource_type=resource_type,
        resource_ref=resource_ref,
    )
