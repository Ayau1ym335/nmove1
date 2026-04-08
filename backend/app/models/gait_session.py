import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    Integer,
    Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.metrics_snapshot import MetricsSnapshot
    from app.models.gait_reading import GaitReading

class SessionStatus(str, enum.Enum):
    ingested = "ingested"
    processing = "processing"
    done = "done"
    error = "error"

class GaitSession(Base):
    __tablename__ = "gait_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    leg_side: Mapped[str | None] = mapped_column(String(10), nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    raw_data_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status", create_type=False),
        nullable=False,
        default=SessionStatus.ingested
    )
    status_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reading_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[user_id], 
        lazy="selectin"
    )
    doctor: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[doctor_id], 
        lazy="selectin"
    )
    metrics_snapshots: Mapped[list["MetricsSnapshot"]] = relationship(
        "MetricsSnapshot", back_populates="gait_session", cascade="all, delete-orphan", lazy="selectin"
    )
    gait_readings: Mapped[list["GaitReading"]] = relationship(
        "GaitReading", back_populates="gait_session", cascade="all, delete-orphan", lazy="selectin"
    )
