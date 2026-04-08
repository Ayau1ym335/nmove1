"""app/models/user_model.py — Per-user ML model metadata stored after training."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserModel(Base):
    __tablename__ = "user_models"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="autoencoder"
    )
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    n_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    minio_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO object path for autoencoder .pkl",
    )
    scaler_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO object path for per-user MinMaxScaler .pkl",
    )

    # Relationships
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        lazy="selectin",
    )
