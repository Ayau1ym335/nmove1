"""app/models/user.py — Users table (UUID PK, role enum, timezone-aware timestamps)."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class UserRole(str, enum.Enum):
    patient = "patient"
    doctor = "doctor"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        # create_type=False: the ENUM type is managed by the Alembic migration,
        # not by SQLAlchemy at ORM level. Prevents "type already exists" errors.
        SAEnum(UserRole, name="user_role", create_type=False),
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        # onupdate=func.now() is a Python-side default (sets value in ORM before INSERT/UPDATE).
        # The DB-side trigger in the migration handles it for direct SQL updates.
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships — lazy="selectin" is required for async-safe eager loading
    auth_sessions: Mapped[list["AuthSession"]] = relationship(  # noqa: F821
        "AuthSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    gait_sessions: Mapped[list["GaitSession"]] = relationship(  # noqa: F821
        "GaitSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
