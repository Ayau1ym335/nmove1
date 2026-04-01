"""app/db/base.py — Shared declarative base for new SQLAlchemy 2.0 models."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Single source of truth for all new ORM models.

    Kept separate from ``app.data.tables.Base`` (legacy models) to allow
    independent Alembic management. Will be merged in a future migration.
    """
    pass
