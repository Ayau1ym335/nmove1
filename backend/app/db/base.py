"""app/db/base.py — Shared declarative Base with constraint naming convention."""
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------------------------
# Naming convention — keeps generated constraint names predictable and
# consistent across all databases and Alembic revisions.
# ---------------------------------------------------------------------------
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Single declarative base for all ORM models in the new schema.

    All models that inherit from this Base will have their tables tracked by
    Alembic via ``Base.metadata``.  The naming convention above ensures that
    auto-generated constraint names are deterministic and human-readable.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
