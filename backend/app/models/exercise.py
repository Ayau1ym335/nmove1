"""app/models/exercise.py — Prescribed exercises linked to metrics snapshots."""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.metrics_snapshot import MetricsSnapshot


class ExerciseDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    metrics_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("metrics_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[ExerciseDifficulty | None] = mapped_column(
        SAEnum(
            ExerciseDifficulty,
            name="exercise_difficulty",
            # create_type=False: ENUM type is managed by Alembic migration,
            # not by SQLAlchemy ORM. Prevents "type already exists" on startup.
            create_type=False,
        ),
        nullable=True,
    )
    video_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship — lazy="selectin" for async safety
    metrics_snapshot: Mapped["MetricsSnapshot"] = relationship(  # noqa: F821
        "MetricsSnapshot",
        back_populates="exercises",
        lazy="selectin",
    )
