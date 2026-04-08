# backend/app/models/gait_reading.py
"""app/models/gait_reading.py — Raw IMU readings from ESP32 devices.

Each row is one sensor sample (accelerometer + gyroscope) from a single leg.
The table is a TimescaleDB hypertable partitioned on the ``time`` column with
1-hour chunks.

Composite primary key (time, id):
    TimescaleDB requires the partition key (time) to appear first in any
    unique constraint.  The secondary column (id) ensures uniqueness within
    a chunk without scanning the entire chunk for a random UUID.

Relationship to GaitSession uses lazy="selectin" for async-safe eager loading.
Do NOT use lazy="joined" or any sync-loading strategy in this codebase.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.gait_session import GaitSession


class GaitReading(Base):
    """One sample of raw IMU data from an ESP32 wearable.

    Columns
    -------
    time            — UTC timestamp of the sensor sample; TimescaleDB partition key.
    id              — Random UUID, second part of composite PK.
    gait_session_id — Owning session (FK → gait_sessions.id, CASCADE DELETE).
    device_id       — ESP32 chip identifier (optional; max 100 chars).
    leg_side        — "left" or "right".
    ax / ay / az    — Accelerometer readings in m/s².
    gx / gy / gz    — Gyroscope readings in deg/s.
    temperature     — Optional onboard chip temperature in °C.
    sequence_number — Uint16 packet counter from device; used for gap detection.
    created_at      — DB insertion timestamp (server-side default).
    """

    __tablename__ = "gait_readings"

    # ------------------------------------------------------------------ #
    # Primary key columns                                                  #
    # ------------------------------------------------------------------ #
    # We declare them as regular columns and set the composite PK via
    # __table_args__ so Alembic and TimescaleDB see the exact constraint.

    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="TimescaleDB partition key — UTC sensor timestamp",
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
        nullable=False,
    )

    # ------------------------------------------------------------------ #
    # FK + device metadata                                                 #
    # ------------------------------------------------------------------ #

    gait_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gait_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="ESP32 chip ID",
    )
    leg_side: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment='"left" or "right"',
    )

    # ------------------------------------------------------------------ #
    # Accelerometer (m/s²)                                                 #
    # ------------------------------------------------------------------ #

    ax: Mapped[float] = mapped_column(Float, nullable=False, comment="Accel X (m/s²)")
    ay: Mapped[float] = mapped_column(Float, nullable=False, comment="Accel Y (m/s²)")
    az: Mapped[float] = mapped_column(Float, nullable=False, comment="Accel Z (m/s²)")

    # ------------------------------------------------------------------ #
    # Gyroscope (deg/s)                                                    #
    # ------------------------------------------------------------------ #

    gx: Mapped[float] = mapped_column(Float, nullable=False, comment="Gyro X (deg/s)")
    gy: Mapped[float] = mapped_column(Float, nullable=False, comment="Gyro Y (deg/s)")
    gz: Mapped[float] = mapped_column(Float, nullable=False, comment="Gyro Z (deg/s)")

    # ------------------------------------------------------------------ #
    # Optional sensors                                                     #
    # ------------------------------------------------------------------ #

    temperature: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="ESP32 onboard temperature (°C)",
    )
    sequence_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Uint16 packet counter from device; rolls over at 65535",
    )

    # ------------------------------------------------------------------ #
    # Audit                                                                #
    # ------------------------------------------------------------------ #

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ------------------------------------------------------------------ #
    # Table-level constraints                                              #
    # ------------------------------------------------------------------ #

    __table_args__ = (
        # Composite PK: time MUST be first (TimescaleDB partitioning requirement).
        PrimaryKeyConstraint("time", "id", name="pk_gait_readings"),
    )

    # ------------------------------------------------------------------ #
    # Relationships                                                        #
    # ------------------------------------------------------------------ #

    gait_session: Mapped["GaitSession"] = relationship(  # noqa: F821
        "GaitSession",
        back_populates="gait_readings",
        lazy="selectin",
    )
