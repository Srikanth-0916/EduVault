"""Application settings.

Secrets are read from the environment. Safe non-production defaults exist so
local development works without a `.env`; these defaults are refused when
``ENV=production`` (fail closed, design §7).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_VERSION = "0.1.0"

_ENV = Literal["development", "test", "production"]

# Clearly non-production default secrets (demo/dev only).
_DEV_JWT_SECRET = "dev-only-jwt-secret-change-me-please-32-bytes"
_DEV_APAAR_ENCRYPTION_KEY = "dev-only-apaar-encryption-key-change-me"
_DEV_APAAR_LOOKUP_KEY = "dev-only-apaar-lookup-key-change-me"
_DEV_RECEIPT_SIGNING_KEY = "dev-only-receipt-signing-key-change-me"

_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

_DEV_DATABASE_URL = "postgresql+psycopg://apaar:apaar@localhost:5432/apaar_sdmv"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,
        env_ignore_empty=True,
        extra="ignore",
        validate_default=True,
    )

    env: _ENV = Field(default="development", validation_alias="ENV")
    database_url: str = Field(default=_DEV_DATABASE_URL, validation_alias="DATABASE_URL")
    jwt_secret: str = Field(default=_DEV_JWT_SECRET, validation_alias="JWT_SECRET")
    apaar_encryption_key: str = Field(
        default=_DEV_APAAR_ENCRYPTION_KEY, validation_alias="APAAR_ENCRYPTION_KEY"
    )
    apaar_lookup_key: str = Field(
        default=_DEV_APAAR_LOOKUP_KEY, validation_alias="APAAR_LOOKUP_KEY"
    )
    receipt_signing_key: str = Field(
        default=_DEV_RECEIPT_SIGNING_KEY, validation_alias="RECEIPT_SIGNING_KEY"
    )
    cors_origins: list[str] = Field(default=_DEFAULT_CORS_ORIGINS, validation_alias="CORS_ORIGINS")
    access_token_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_MINUTES")
    jwt_issuer: str = Field(default="apaar-sdmv-api", validation_alias="JWT_ISSUER")
    jwt_audience: str = Field(default="apaar-sdmv-web", validation_alias="JWT_AUDIENCE")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept both JSON lists and comma-separated strings."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    def model_post_init(self, __context: object) -> None:
        if self.is_production:
            insecure: list[str] = []
            if not self.database_url.startswith("postgresql+") and not self.database_url.startswith(
                "postgresql"
            ):
                insecure.append("database_url")
            for name, secret in (
                ("jwt_secret", self.jwt_secret),
                ("apaar_encryption_key", self.apaar_encryption_key),
                ("apaar_lookup_key", self.apaar_lookup_key),
                ("receipt_signing_key", self.receipt_signing_key),
            ):
                if not secret or secret.startswith("dev-only-"):
                    insecure.append(name)
            if insecure:
                raise RuntimeError(
                    "Refusing to start with development defaults in production; "
                    f"provide proper values for: {', '.join(insecure)}"
                )


@lru_cache
def get_settings() -> Settings:
    return Settings()
