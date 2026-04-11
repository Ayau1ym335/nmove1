"""app/models/profile.py — Patient profile data collected at registration."""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.metrics_snapshot import MetricsSnapshot


class Gender(str, enum.Enum):
    male = "male"
    female = "female"


class Side(str, enum.Enum):
    left = "left"
    right = "right"


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[Gender] = mapped_column(
        SAEnum(Gender, name="profile_gender", create_type=False),
        nullable=False,
    )
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    nationality: Mapped[str] = mapped_column(String(100), nullable=False)
    have_injury: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    have_banomaly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    banomaly: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shoe_size: Mapped[float] = mapped_column(Float, nullable=False)
    leg_length: Mapped[float] = mapped_column(Float, nullable=False)
    dominant_leg: Mapped[Side] = mapped_column(
        SAEnum(Side, name="profile_side", create_type=False),
        nullable=False,
        default=Side.right,
        server_default="right",
    )
    lifestyle: Mapped[str] = mapped_column(String(100), nullable=False)
    smoke: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    alcohol: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    baseline_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metrics_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="profile", lazy="selectin")
    baseline_snapshot: Mapped["MetricsSnapshot | None"] = relationship("MetricsSnapshot", lazy="selectin")
