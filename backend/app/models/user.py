"""app/models/user.py — Users table (new schema, UUID PKs)."""
import enum
import uuid

from sqlalchemy import Boolean, Enum as SAEnum, String
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
        SAEnum(UserRole, name="user_role_enum", create_type=True),
        nullable=False,
        default=UserRole.patient,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    auth_sessions: Mapped[list["AuthSession"]] = relationship(  # noqa: F821
        "AuthSession", back_populates="user", cascade="all, delete-orphan"
    )
    gait_sessions: Mapped[list["GaitSession"]] = relationship(  # noqa: F821
        "GaitSession", back_populates="user", cascade="all, delete-orphan"
    )
