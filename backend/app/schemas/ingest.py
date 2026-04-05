# backend/app/schemas/ingest.py
"""app/schemas/ingest.py — Pydantic v2 schemas for the ESP32 IMU ingest pipeline.

Schema hierarchy:
    IMUReading       — one sensor frame from the ESP32
    IngestRequest    — batch payload (1–500 IMUReadings for one session)
    IngestResponse   — server acknowledgment (202 Accepted)
    IngestError      — structured validation error response

Validator behaviour summary:
    - Naive timestamps → assume UTC, attach tzinfo, emit WARNING log
    - Future timestamps > 60 s → reject (422)
    - Stale timestamps > 24 h → reject (422)
    - Accel values outside ±156.9 m/s² → reject
    - Gyro values outside ±2000 deg/s → reject
    - Temperature outside -40..125 °C → reject (when provided)
    - sequence_number outside 0..65535 → reject (when provided)
    - Unsorted readings → sort automatically, add warning string
    - Mixed leg_side in one batch → reject (422)
    - Sequence gaps > 10 → accept, add warning string (not rejected)
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ACCEL_MAX: float = 156.9         # ±16g in m/s²
_GYRO_MAX: float  = 2000.0        # deg/s, max gyro range
_TEMP_MIN: float  = -40.0         # °C, ESP32 operating floor
_TEMP_MAX: float  = 125.0         # °C, ESP32 operating ceiling
_SEQ_MAX:  int    = 65535         # uint16 rollover
_MAX_FUTURE_SEC:  int = 60        # reject if > 60 s ahead of server time
_MAX_AGE_HOURS:   int = 24        # reject if older than 24 h


# ---------------------------------------------------------------------------
# IMUReading — single sensor frame
# ---------------------------------------------------------------------------

class IMUReading(BaseModel):
    """One sample of raw IMU data from the ESP32.

    All six sensor axes are required.  ``temperature`` and
    ``sequence_number`` are optional (not all firmware versions expose them).
    """

    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    """UTC sensor timestamp.  Naive datetimes are accepted and treated as UTC
    (ESP32 firmware often omits timezone info even though it uses NTP-synced UTC).
    Timestamps > 60 s in the future or > 24 h in the past are rejected."""

    # --- Accelerometer ---
    ax: float = Field(..., description="Accelerometer X axis (m/s²)")
    ay: float = Field(..., description="Accelerometer Y axis (m/s²)")
    az: float = Field(..., description="Accelerometer Z axis (m/s²)")

    # --- Gyroscope ---
    gx: float = Field(..., description="Gyroscope X axis (deg/s)")
    gy: float = Field(..., description="Gyroscope Y axis (deg/s)")
    gz: float = Field(..., description="Gyroscope Z axis (deg/s)")

    # --- Metadata ---
    leg_side: Literal["left", "right"]
    temperature: float | None = None
    sequence_number: int | None = None

    # ------------------------------------------------------------------ #
    # Field validators                                                     #
    # ------------------------------------------------------------------ #

    @field_validator("timestamp", mode="before")
    @classmethod
    def normalise_timestamp(cls, v: object) -> datetime:
        """Parse and normalise ``timestamp``.

        - If a ``str`` is received, parse it as ISO 8601.
        - If the resulting datetime is naive (no tzinfo), attach UTC and emit
          a WARNING — do NOT reject (ESP32 firmware commonly sends naive UTC).
        - Reject timestamps more than 60 s in the future.
        - Reject timestamps older than 24 h.
        """
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))

        if not isinstance(v, datetime):
            raise ValueError("timestamp must be a datetime or ISO 8601 string")

        if v.tzinfo is None:
            logger.warning(
                "Naive timestamp received from device — assuming UTC. "
                "Update firmware to send timezone-aware timestamps."
            )
            v = v.replace(tzinfo=timezone.utc)

        now_utc = datetime.now(timezone.utc)

        if v > now_utc + timedelta(seconds=_MAX_FUTURE_SEC):
            raise ValueError(
                f"Timestamp is {(v - now_utc).total_seconds():.0f} s in the future "
                f"(max allowed: {_MAX_FUTURE_SEC} s). Check device clock."
            )

        if v < now_utc - timedelta(hours=_MAX_AGE_HOURS):
            raise ValueError(
                f"Timestamp is older than {_MAX_AGE_HOURS} h. "
                "Re-sync device clock or start a new session."
            )

        return v

    @field_validator("ax", "ay", "az")
    @classmethod
    def validate_accel(cls, v: float, info: object) -> float:
        """Reject accelerometer readings outside ±156.9 m/s² (±16g range)."""
        if not (-_ACCEL_MAX <= v <= _ACCEL_MAX):
            field_name = getattr(info, "field_name", "accel")
            raise ValueError(
                f"{field_name}={v} out of valid range "
                f"[{-_ACCEL_MAX}, {_ACCEL_MAX}] m/s²"
            )
        return v

    @field_validator("gx", "gy", "gz")
    @classmethod
    def validate_gyro(cls, v: float, info: object) -> float:
        """Reject gyroscope readings outside ±2000 deg/s."""
        if not (-_GYRO_MAX <= v <= _GYRO_MAX):
            field_name = getattr(info, "field_name", "gyro")
            raise ValueError(
                f"{field_name}={v} out of valid range "
                f"[{-_GYRO_MAX}, {_GYRO_MAX}] deg/s"
            )
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float | None) -> float | None:
        """Reject temperature readings outside ESP32 operating range."""
        if v is not None and not (_TEMP_MIN <= v <= _TEMP_MAX):
            raise ValueError(
                f"temperature={v} out of valid range "
                f"[{_TEMP_MIN}, {_TEMP_MAX}] °C"
            )
        return v

    @field_validator("sequence_number")
    @classmethod
    def validate_sequence_number(cls, v: int | None) -> int | None:
        """Reject sequence numbers outside uint16 range (0–65535)."""
        if v is not None and not (0 <= v <= _SEQ_MAX):
            raise ValueError(
                f"sequence_number={v} out of valid uint16 range [0, {_SEQ_MAX}]"
            )
        return v


# ---------------------------------------------------------------------------
# IngestRequest — batch payload from ESP32
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    """Batch of IMU readings from a single ESP32 device for one gait session.

    Constraints enforced at validation time:
    - 1 ≤ len(readings) ≤ 500
    - All readings share the same leg_side
    - Readings are sorted by timestamp ascending (auto-fixed with warning)
    - Sequence gaps > 10 are flagged but not rejected
    """

    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    """Must match an open gait_session owned by the authenticated patient."""

    device_id: str | None = None

    readings: list[IMUReading] = Field(..., min_length=1, max_length=500)
    """Between 1 and 500 IMUReading objects per HTTP request."""

    # Mutable default: store whether the list was reordered so the service
    # layer can attach a warning without running its own sort check.
    _was_reordered: bool = False

    @field_validator("device_id")
    @classmethod
    def normalise_device_id(cls, v: str | None) -> str | None:
        """Strip whitespace; enforce max 100 chars."""
        if v is None:
            return v
        stripped = v.strip()
        if len(stripped) > 100:
            raise ValueError("device_id must be at most 100 characters")
        return stripped or None  # treat blank string as None

    @model_validator(mode="after")
    def validate_readings_batch(self) -> "IngestRequest":
        """Cross-field validation on the readings list.

        1. Enforce uniform leg_side.
        2. Sort by timestamp if not already sorted (with warning flag).
        """
        readings = self.readings

        # 1. Uniform leg_side
        sides = {r.leg_side for r in readings}
        if len(sides) > 1:
            raise ValueError(
                f"All readings in one batch must share the same leg_side. "
                f"Found: {sorted(sides)}"
            )

        # 2. Sort by timestamp — auto-fix unsorted batches
        timestamps = [r.timestamp for r in readings]
        if timestamps != sorted(timestamps):
            logger.warning(
                "IngestRequest received with unsorted timestamps — "
                "reordering on server. Device firmware should sort before sending."
            )
            object.__setattr__(
                self,
                "readings",
                sorted(readings, key=lambda r: r.timestamp),
            )
            object.__setattr__(self, "_was_reordered", True)

        return self


# ---------------------------------------------------------------------------
# IngestResponse — server acknowledgment (HTTP 202)
# ---------------------------------------------------------------------------

class IngestResponse(BaseModel):
    """Returned after a successful ingest.  HTTP status 202 Accepted."""

    accepted: int
    """Number of rows written to the database."""

    session_id: UUID

    first_timestamp: datetime
    """Timestamp of the earliest reading in the batch (after sorting)."""

    last_timestamp: datetime
    """Timestamp of the latest reading in the batch (after sorting)."""

    warnings: list[str] = []
    """Non-fatal warnings: sequence gaps, auto-sort, naive timestamps, etc."""

    ingested_at: datetime
    """Server-side UTC timestamp of the ingest operation."""

    task_id: str | None = None
    """Celery task ID for status polling"""


# ---------------------------------------------------------------------------
# IngestError — structured error response for validation failures
# ---------------------------------------------------------------------------

class IngestError(BaseModel):
    """Returned when the batch is rejected at validation time."""

    detail: str
    """Human-readable explanation of the rejection reason."""

    field: str | None = None
    """Which field caused the error, if applicable."""

    rejected_count: int
    """Number of readings that were rejected (usually the full batch size)."""
