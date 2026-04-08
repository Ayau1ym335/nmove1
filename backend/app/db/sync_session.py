# backend/app/db/sync_session.py
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# Replace async driver with sync driver (psycopg2) for Celery
DATABASE_URL_SYNC = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")

sync_engine = create_engine(
    DATABASE_URL_SYNC,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)

@contextmanager
def get_sync_db() -> Generator[Session, None, None]:
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
