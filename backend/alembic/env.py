"""alembic/env.py — Synchronous Alembic environment for SQLAlchemy 2.0.

Alembic's internal DDL runner is synchronous — it calls run_sync() under the
hood even when using an async engine pattern.  We therefore use a plain
synchronous psycopg2 engine here (NOT asyncpg) and override the URL from the
DATABASE_URL environment variable so no credentials are baked into alembic.ini.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path
from sqlalchemy import create_engine, pool

from alembic import context

# ---------------------------------------------------------------------------
# Load backend/.env before anything else (UTF-8 / UTF-16 safe).
# Fixes Windows UnicodeDecodeError in psycopg2 when .env was saved as UTF-16
# or when DATABASE_URL contained bytes mojibake.
# ---------------------------------------------------------------------------


def _decode_env_file(raw: bytes) -> str:
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8")


def _load_backend_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return
    try:
        raw = env_path.read_bytes()
    except OSError:
        return
    try:
        text = _decode_env_file(raw)
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    parsed: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            parsed[key] = val

    # Always take DATABASE_URL from backend/.env when present. A stale or
    # mis-encoded DATABASE_URL exported in the shell (common on Windows)
    # overrides .env with setdefault() and breaks psycopg2 with UnicodeDecodeError.
    if "DATABASE_URL" in parsed:
        os.environ["DATABASE_URL"] = parsed["DATABASE_URL"]
    for key, val in parsed.items():
        if key == "DATABASE_URL":
            continue
        os.environ.setdefault(key, val)


_load_backend_dotenv()

# ---------------------------------------------------------------------------
# Make sure the backend/ directory is on sys.path so app.* imports resolve.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.db_url import quote_sqlalchemy_postgres_userinfo  # noqa: E402

# Import Base — this populates Base.metadata with all table definitions.
from app.db.base import Base  # noqa: E402, F401

# Import every model so SQLAlchemy registers their Table objects on metadata.
# This single import runs app/models/__init__.py which re-exports all models.
import app.models  # noqa: E402, F401

# ---------------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_sync_url() -> str:
    """Return a *synchronous* psycopg2 URL for Alembic's DDL runner.

    Reads DATABASE_URL from the environment (set by Docker / .env) and swaps
    out the async asyncpg driver for the synchronous psycopg2 driver.

    Alembic cannot use asyncpg directly because its internal migration runner
    is synchronous.  The async SQLAlchemy engine (used by FastAPI) is separate.
    """
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5433/nmove",
    )
    url = quote_sqlalchemy_postgres_userinfo(url)
    # Swap async driver → sync driver for Alembic
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — no live DB connection required.

    Useful for generating SQL scripts without a database.
    """
    url = get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connects to the live database.

    Uses a synchronous psycopg2 engine so Alembic's DDL runner works
    without an asyncio event loop.
    """
    # libpq on Windows may return non-UTF-8 error text; psycopg2 then raises
    # UnicodeDecodeError. Prefer UTF-8 on the client side.
    os.environ.setdefault("PGCLIENTENCODING", "UTF8")

    url = get_sync_url()
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
        connect_args={"client_encoding": "UTF8"},
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
