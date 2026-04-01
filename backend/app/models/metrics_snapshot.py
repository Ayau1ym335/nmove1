"""app/models/metrics_snapshot.py — Computed gait metrics per session."""
import enum
import uuid

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey
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
    cadence: Mapped[float] = mapped_column(Float, nullable=False)
    symmetry_score: Mapped[float] = mapped_column(Float, nullable=False)
    stability_score: Mapped[float] = mapped_column(Float, nullable=False)
    movement_age: Mapped[float | None] = mapped_column(Float, nullable=True)
    interpretation_status: Mapped[InterpretationStatus] = mapped_column(
        SAEnum(
            InterpretationStatus,
            name="interpretation_status_enum",
            create_type=True,
        ),
        nullable=False,
        default=InterpretationStatus.normal,
    )
    calculated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    gait_session: Mapped["GaitSession"] = relationship(  # noqa: F821
        "GaitSession", back_populates="metrics_snapshots"
    )
    exercises: Mapped[list["Exercise"]] = relationship(  # noqa: F821
        "Exercise", back_populates="metrics_snapshot", cascade="all, delete-orphan"
    )
