"""app/models/metrics_snapshot.py — Computed gait metrics per session."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class InterpretationStatus(str, enum.Enum):
    normal = "normal"
    needs_attention = "needs_attention"
    improving = "improving"


class MetricsSnapshot(Base):
    __tablename__ = "metrics_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    gait_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gait_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cadence: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Steps per minute"
    )
    symmetry_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="0.0–1.0, 1.0 = perfect symmetry"
    )
    stability_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="0.0–1.0"
    )
    movement_age: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Calculated movement age in years"
    )
    bio_age: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="User's biological age at time of session"
    )
    movement_age_delta: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="movement_age - bio_age"
    )
    interpretation_status: Mapped[InterpretationStatus] = mapped_column(
        SAEnum(
            InterpretationStatus,
            name="interpretation_status",
            # create_type=False: ENUM type is managed by Alembic migration,
            # not by SQLAlchemy ORM. Prevents "type already exists" on startup.
            create_type=False,
        ),
        nullable=False,
        default=InterpretationStatus.normal,
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships — lazy="selectin" for async safety
    gait_session: Mapped["GaitSession"] = relationship(  # noqa: F821
        "GaitSession",
        back_populates="metrics_snapshots",
        lazy="selectin",
    )
    exercises: Mapped[list["Exercise"]] = relationship(  # noqa: F821
        "Exercise",
        back_populates="metrics_snapshot",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
