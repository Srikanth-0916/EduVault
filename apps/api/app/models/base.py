"""Declarative base, common column helpers, and mixins.

Conventions (design §5.2):

- UUID string primary keys (36-char ``uuid4`` strings).
- UTC timestamps stored with ``DateTime(timezone=True)``.
- ``created_at`` / ``updated_at`` on every table via :class:`TimestampMixin`.
- Enum columns store canonical string values (see ``app.models.enums``).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, MetaData, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models.enums import sa_enum_values

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def utc_now() -> datetime:
    """Naive UTC timestamp (never server-local time)."""
    return datetime.now(UTC).replace(tzinfo=None)


def as_utc(value: datetime) -> datetime:
    """Normalize a database datetime for comparison.

    PostgreSQL returns timezone-aware values for ``TIMESTAMP WITH TIME ZONE``
    while SQLite returns naive values. Treat naive values as UTC.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class Base(DeclarativeBase):
    """Declarative base for the whole prototype data model."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    type_annotation_map: ClassVar[dict[Any, Any]] = {dict[str, Any]: JSON}


def pk() -> Mapped[str]:
    """36-char UUID string primary key."""
    return mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))


def sa_enum(enum_cls: type, **kwargs: Any) -> Any:
    """String-backed SQLAlchemy enum storing canonical values (design §5.2)."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        values_callable=sa_enum_values,
        length=64,
        **kwargs,
    )


def uuid_fk(target: str, *, nullable: bool = False, index: bool = False) -> Mapped[str]:
    """36-char UUID foreign-key column."""
    return mapped_column(
        String(36),
        ForeignKey(target),
        nullable=nullable,
        index=index,
    )


class TimestampMixin:
    """created_at/updated_at timestamps in UTC."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
