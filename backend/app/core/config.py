"""app/core/config.py — Application settings loaded from environment variables."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.db_url import quote_sqlalchemy_postgres_userinfo


def _decode_env_file_bytes(raw: bytes) -> str:
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def _read_database_url_from_backend_env_file() -> str | None:
    """Return DATABASE_URL from backend/.env if that file defines it."""
    backend_dir = Path(__file__).resolve().parents[2]
    env_path = backend_dir / ".env"
    if not env_path.is_file():
        return None
    try:
        raw = env_path.read_bytes()
    except OSError:
        return None
    text = _decode_env_file_bytes(raw)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key == "DATABASE_URL" and val:
            return val
    return None


def _in_docker() -> bool:
    try:
        return Path("/.dockerenv").is_file()
    except OSError:
        return False


class Settings(BaseSettings):
    # -------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------
    APP_NAME: str = "NMove"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    APP_ENV: str = "development"

    # -------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------
    # Default matches docker-compose published Postgres port for host-side uvicorn.
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5433/nmove"
    )

    # -------------------------------------------------------------------
    # Redis
    # -------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # -------------------------------------------------------------------
    # JWT / Auth
    # -------------------------------------------------------------------
    # No default — must be provided in .env or environment.
    # Generate: python -c "import secrets; print(secrets.token_hex(32))"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # -------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------
    CORS_ORIGINS: List[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: object) -> List[str]:
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            return [item.strip() for item in v.split(",")]
        return v  # type: ignore[return-value]

    # -------------------------------------------------------------------
    # MinIO
    # -------------------------------------------------------------------
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = "nmove_admin"
    MINIO_ROOT_PASSWORD: str = "nmove_minio_secret"
    MINIO_SECURE: bool = False

    # -------------------------------------------------------------------
    # External APIs
    # -------------------------------------------------------------------
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        return quote_sqlalchemy_postgres_userinfo(v)

    @model_validator(mode="after")
    def _prefer_backend_env_file_database_url_on_host(self) -> Self:
        """Use backend/.env for DATABASE_URL when running outside Docker.

        Shell-exported DATABASE_URL (often ``...@db:5432`` for Compose) overrides
        pydantic's ``env_file`` and breaks host ``uvicorn`` because hostname
        ``db`` only resolves on the Compose network.
        """
        if _in_docker():
            return self
        from_file = _read_database_url_from_backend_env_file()
        if from_file:
            object.__setattr__(
                self,
                "DATABASE_URL",
                quote_sqlalchemy_postgres_userinfo(from_file),
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    # Only inject JWT from the process environment when it is actually set.
    # ``Settings(JWT_SECRET_KEY="" )`` would override a valid ``JWT_SECRET_KEY``
    # loaded from ``backend/.env`` whenever the shell does not export the variable
    # (typical for local ``uvicorn``), yielding an empty signing key.
    env_jwt = os.getenv("JWT_SECRET_KEY")
    if env_jwt:
        return Settings(JWT_SECRET_KEY=env_jwt)
    return Settings(JWT_SECRET_KEY="")


# Module-level singleton — importable as `from app.core.config import settings`
settings: Settings = get_settings()
