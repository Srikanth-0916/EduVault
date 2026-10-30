"""Pytest fixtures for the APAAR-SDMV API test suite.

Tests run against SQLite without network access: the environment is configured
*before* the application package is imported so ``app.config.Settings`` and
``app.db`` pick up the test database and the ``test`` environment flag.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./var/test_api.db")

import pytest
from app.db import create_all, drop_all, get_engine, reset_engine
from app.main import create_app
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from collections.abc import Iterator

    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session


@pytest.fixture(autouse=True)
def _test_db_storage_engine(tmp_path: Path) -> Iterator[None]:
    """Point the shared engine at a per-test SQLite file and reset it after."""
    reset_engine()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    yield
    reset_engine()
    os.environ["DATABASE_URL"] = "sqlite:///./var/test_api.db"


@pytest.fixture()
def db() -> Iterator[Session]:
    """Provide a session over a freshly created schema; tables drop after test."""
    create_all()
    engine = get_engine()
    connection = engine.connect()
    session = Session(bind=connection, future=True)
    try:
        yield session
    finally:
        session.close()
        connection.close()
        drop_all()


@pytest.fixture()
def seeded(db: Session) -> Session:
    """Core deterministic seed: institutions, programmes, users, memberships."""
    from app.seed import seed_core

    seed_core(db)
    db.commit()
    return db


@pytest.fixture()
def client(db: Session) -> Iterator[TestClient]:
    """FastAPI test client wired to the per-test SQLite session."""
    from app.db import get_db
    from fastapi.testclient import TestClient

    application = create_app()

    def override_get_db() -> Iterator[Session]:
        yield db

    application.dependency_overrides[get_db] = override_get_db

    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()
