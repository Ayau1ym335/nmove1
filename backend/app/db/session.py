"""app/db/session.py — Async engine, session factory, and FastAPI get_db dependency."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.db.base import Base  # noqa: F401 — ensure Base is importable from this module

# ---------------------------------------------------------------------------
# Engine — reads DATABASE_URL from settings; never hardcode credentials.
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,           # flip to True to log all SQL in development
    pool_pre_ping=True,   # recycles stale connections gracefully
    pool_size=10,
    max_overflow=20,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # safe for async: avoids lazy-load after commit
    autoflush=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a database session for a single request.

    - Commits automatically on clean exit.
    - Rolls back automatically on any exception.
    - Always closes the session at the end of the request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
