import logging
from datetime import datetime, timezone
from uuid import UUID
from typing import Any, Literal, cast
import numpy as np

from fastapi import HTTPException, status
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gait_reading import GaitReading
from app.models.gait_session import GaitSession
from app.schemas.ingest import IMUReading, IngestRequest, IngestResponse

logger = logging.getLogger(__name__)

_BIN_DTYPE = np.dtype([
    ("header", "u1"),
    ("timestamp", "f8"),
    ("acc1", "f4", (3,)),
    ("gyro1", "f4", (3,)),
    ("acc2", "f4", (3,)),
    ("gyro2", "f4", (3,)),
])


async def validate_session_ownership(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID,
) -> GaitSession:
    result = await db.execute(
        select(GaitSession).where(
            GaitSession.id == session_id,
            GaitSession.user_id == user_id,
        )
    )
    gait_session = result.scalar_one_or_none()

    if gait_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gait session not found or does not belong to this user",
        )

    if gait_session.ended_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot ingest into a closed session. Start a new gait session first.",
        )
    return gait_session


def detect_sequence_gaps(readings: list[IMUReading]) -> list[str]:
    seq_nums = [
        r.sequence_number
        for r in readings
        if r.sequence_number is not None
    ]

    if len(seq_nums) < 2:
        return []

    warnings: list[str] = []
    _GAP_THRESHOLD = 10
    _ROLLOVER = 65536  

    for current, nxt in zip(seq_nums, seq_nums[1:]):
        raw_diff = nxt - current
        forward_diff = raw_diff % _ROLLOVER
        if forward_diff == 0:
            continue
        if forward_diff > _GAP_THRESHOLD:
            warnings.append(
                f"Sequence gap detected: {forward_diff - 1} packets missing between seq {current} and seq {nxt}"
            )
            logger.warning(
                "Sequence gap in ingest: %d packets missing between %d and %d",
                forward_diff - 1, current, nxt
            )
    return warnings


async def write_readings(
    db: AsyncSession,
    gait_session: GaitSession,
    data: IngestRequest,
) -> IngestResponse:
    readings = data.readings

    warnings: list[str] = []
    warnings.extend(detect_sequence_gaps(readings))
    if getattr(data, "_was_reordered", False):
        warnings.append("Readings reordered by timestamp on server")
        logger.warning(
            "Readings were reordered during ingest for session=%s device=%s",
            gait_session.id, data.device_id
        )

    rows: list[dict] = [
        {
            "time":             reading.timestamp,
            "gait_session_id":  gait_session.id,
            "device_id":        data.device_id,
            "leg_side":         reading.leg_side,
            "ax":               reading.ax,
            "ay":               reading.ay,
            "az":               reading.az,
            "gx":               reading.gx,
            "gy":               reading.gy,
            "gz":               reading.gz,
            "temperature":      reading.temperature,
            "sequence_number":  reading.sequence_number,
        }
        for reading in readings
    ]

    await db.execute(insert(GaitReading), rows)
    await db.commit()

    logger.info(
        "Ingested %d readings — session=%s device=%s leg=%s",
        len(rows), gait_session.id, data.device_id, readings[0].leg_side
    )

    from app.tasks.process_session import process_session
    from app.core.cache import invalidate_user_dashboard, cache_delete_pattern, cache_delete

    task_result = cast(Any, process_session).delay(str(gait_session.id))
    logger.info(f"Enqueued process_session task: task_id={task_result.id} session={gait_session.id}")
    
    await invalidate_user_dashboard(str(gait_session.user_id))
    await cache_delete_pattern(f"trends:{gait_session.user_id}:*")
    if gait_session.doctor_id is not None:
        await cache_delete(f"doctor:patients:{gait_session.doctor_id}")
        await cache_delete_pattern(f"doctor:patient_detail:{gait_session.doctor_id}:{gait_session.user_id}:*")


    # Store task_id on the session row for polling
    await db.execute(
        update(GaitSession)
        .where(GaitSession.id == gait_session.id)
        .values(task_id=task_result.id)
    )
    await db.commit()

    return IngestResponse(
        accepted=len(rows),
        session_id=gait_session.id,
        first_timestamp=readings[0].timestamp,
        last_timestamp=readings[-1].timestamp,
        warnings=warnings,
        ingested_at=datetime.now(timezone.utc),
        task_id=task_result.id,
    )


def build_ingest_request_from_bin(
    *,
    raw_bytes: bytes,
    session_id: UUID,
    leg_side: Literal["left", "right"],
    device_id: str | None,
    sensor_slot: int = 1,
) -> IngestRequest:
    if not raw_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty .bin file")

    if sensor_slot not in (1, 2):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="sensor_slot must be 1 or 2",
        )

    record_size = _BIN_DTYPE.itemsize
    if len(raw_bytes) % record_size != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid .bin size: not aligned to record size ({record_size} bytes)",
        )

    try:
        arr = np.frombuffer(raw_bytes, dtype=_BIN_DTYPE)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode .bin payload: {exc}",
        ) from exc

    if arr.size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No IMU frames found in .bin file")

    acc_key = "acc1" if sensor_slot == 1 else "acc2"
    gyro_key = "gyro1" if sensor_slot == 1 else "gyro2"

    readings: list[IMUReading] = []
    for i, row in enumerate(arr):
        try:
            ts = datetime.fromtimestamp(float(row["timestamp"]), tz=timezone.utc)
            acc = row[acc_key]
            gyro = row[gyro_key]
            readings.append(
                IMUReading(
                    timestamp=ts,
                    ax=float(acc[0]),
                    ay=float(acc[1]),
                    az=float(acc[2]),
                    gx=float(gyro[0]),
                    gy=float(gyro[1]),
                    gz=float(gyro[2]),
                    leg_side=leg_side,
                    sequence_number=i,
                )
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid frame at index {i}: {exc}",
            ) from exc

    return IngestRequest(
        session_id=session_id,
        device_id=device_id,
        readings=readings,
    )
