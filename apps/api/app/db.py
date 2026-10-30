"""Database engine, session factory, and prototype schema bootstrap.

The engine is created lazily from the ``DATABASE_URL`` environment variable
(falling back to ``Settings.database_url``) so that tests can point it at
SQLite before the first use. ``create_all`` is used for prototype bootstrapping
and migrations are documented as a production follow-on.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _database_url() -> str:
    url = get_settings().database_url
    # Test fixtures (and deployments) may override the URL via the environment
    # after import time, so the env var is consulted at engine-creation time.
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        url = env_url
    return url


def _sqlite_connect_args() -> dict[str, bool]:
    return {"check_same_thread": False}


def _create_engine(url: str) -> Engine:
    connect_args = _sqlite_connect_args() if url.startswith("sqlite") else {}
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def get_engine() -> Engine:
    """Return the process-wide engine, creating it on first use."""
    global _engine
    if _engine is None:
        _engine = _create_engine(_database_url())
        _session_factory = sessionmaker(
            bind=_engine,
            autoflush=False,
            expire_on_commit=False,
            future=True,
        )
    return _engine


def reset_engine() -> None:
    """Dispose and clear the cached engine (used between tests)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_session_factory() -> sessionmaker[Session]:
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    return _session_factory


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def create_all(engine: Engine | None = None) -> None:
    """Create the prototype schema (idempotent). Tests call this per test."""
    from app import models

    models.Base.metadata.create_all(engine or get_engine())


def drop_all(engine: Engine | None = None) -> None:
    """Drop the prototype schema (used between tests)."""
    from app import models

    models.Base.metadata.drop_all(engine or get_engine())
