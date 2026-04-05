"""app/models/gait_session.py — Gait recording sessions (TimescaleDB hypertable)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class GaitSession(Base):
    __tablename__ = "gait_sessions"

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
    device_id: Mapped[str | None] = mapped_column(
        String(100),    # ESP32 device identifier
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="TimescaleDB partition key",
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Computed on session close",
    )
    raw_data_path: Mapped[str | None] = mapped_column(
        String(500),   # MinIO object path
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships — lazy="selectin" for async safety
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="gait_sessions",
        lazy="selectin",
    )
    metrics_snapshots: Mapped[list["MetricsSnapshot"]] = relationship(  # noqa: F821
        "MetricsSnapshot",
        back_populates="gait_session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
