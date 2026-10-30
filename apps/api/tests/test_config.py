"""Settings contract, including the production fail-closed guard (design §7)."""

from __future__ import annotations

import pytest
from app.config import Settings


def _prod_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "env": "production",
        "database_url": "postgresql+psycopg://u:p@db:5432/apaar_sdmv",
        "jwt_secret": "strong-random-production-secret",
        "apaar_encryption_key": "strong-random-production-key",
        "apaar_lookup_key": "strong-random-lookup",
        "receipt_signing_key": "strong-random-receipt",
    }
    base.update(overrides)
    return base


def test_development_allows_dev_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENV", "development")
    settings = Settings()
    assert settings.env == "development"
    assert settings.jwt_secret.startswith("dev-only-")


def test_production_refuses_default_secrets():
    with pytest.raises(RuntimeError, match="jwt_secret"):
        Settings(**_prod_kwargs(jwt_secret="dev-only-jwt-secret-change-me"))


def test_production_refuses_compose_placeholder_secrets():
    with pytest.raises(RuntimeError, match="jwt_secret"):
        Settings(**_prod_kwargs(jwt_secret="dev-compose-jwt-secret-change-me"))


def test_production_refuses_non_postgres_database():
    with pytest.raises(RuntimeError, match="database_url"):
        Settings(**_prod_kwargs(database_url="sqlite:///./var/app.db"))


def test_production_accepts_real_secret_values():
    settings = Settings(**_prod_kwargs())
    assert settings.is_production
    assert settings.jwt_secret == "strong-random-production-secret"


def test_cors_origins_accept_comma_separated_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    settings = Settings()
    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
