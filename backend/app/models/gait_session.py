"""app/models/gait_session.py — Gait recording sessions."""
import uuid

from sqlalchemy import DateTime, ForeignKey, String
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
    started_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_data_path: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="Path in MinIO bucket"
    )
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="gait_sessions")  # noqa: F821
    metrics_snapshots: Mapped[list["MetricsSnapshot"]] = relationship(  # noqa: F821
        "MetricsSnapshot", back_populates="gait_session", cascade="all, delete-orphan"
    )
