"""app/models/metrics_snapshot.py — Computed gait metrics per session.

Columns are grouped by biomechanical domain to mirror the ML feature vector:
  · Rhythm & Pace     — cadence, stride_length, step_count, avg_speed
  · Joint Mechanics   — hip_rotation_rom, ankle_pushoff_proxy, vertical_oscillation
  · Variability       — stride_time_cv, trunk_sway_rms
  · Symmetry & Phases — symmetry_score, stance_phase_pct, double_support_pct
"""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID

if TYPE_CHECKING:
    from app.models.gait_session import GaitSession  # noqa: F401
    from app.models.exercise import Exercise         # noqa: F401

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class InterpretationStatus(str, enum.Enum):
    normal    = "normal"
    attention = "attention"
    concern   = "concern"


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
    # ── Rhythm & Pace ─────────────────────────────────────────────────────────
    cadence: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Steps per minute"
    )
    stride_length: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Estimated stride length (m)"
    )
    step_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Total steps detected in the session"
    )
    avg_speed: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Average walking speed (m/s)"
    )

    # ── Joint Mechanics ───────────────────────────────────────────────────────
    hip_rotation_rom: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Hip rotation ROM (deg) from gyroscope"
    )
    ankle_pushoff_proxy: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Ankle push-off proxy (m/s²)"
    )
    vertical_oscillation: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Vertical oscillation peak-to-peak (m/s²)"
    )

    # ── Variability ───────────────────────────────────────────────────────────
    stride_time_cv: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Stride time coefficient of variation (%)"
    )
    trunk_sway_rms: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Trunk sway RMS lateral acceleration (m/s²)"
    )

    # ── Symmetry & Phases ─────────────────────────────────────────────────────
    symmetry_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="0.0–1.0, 1.0 = perfect symmetry"
    )
    stance_phase_pct: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Stance phase percentage (%)"
    )
    double_support_pct: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Double-support phase percentage (%)"
    )

    # ── ML Anomaly Scoring ───────────────────────────────────────────────────────
    anomaly_score: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Autoencoder reconstruction error, normalised 0–1 (0=normal, 1=very abnormal)"
    )
    is_anomaly: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True,
        comment="True when anomaly_score > 0.65"
    )

    # ── Movement Age & Composite ──────────────────────────────────────────────

    stability_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Composite stability 0.0–1.0"
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
