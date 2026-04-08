"""alembic/env.py — Synchronous Alembic environment for SQLAlchemy 2.0.

Alembic's internal DDL runner is synchronous — it calls run_sync() under the
hood even when using an async engine pattern.  We therefore use a plain
synchronous psycopg2 engine here (NOT asyncpg) and override the URL from the
DATABASE_URL environment variable so no credentials are baked into alembic.ini.
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ---------------------------------------------------------------------------
# Make sure the backend/ directory is on sys.path so app.* imports resolve.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
        # Fallback for local dev outside Docker — uses host port 5433
        "postgresql+asyncpg://postgres:password@localhost:5433/nmove",
    )
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
    # Build config section with the overridden (sync) URL
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_sync_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
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
