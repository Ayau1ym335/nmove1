import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gait_reading import GaitReading
from app.models.gait_session import GaitSession
from app.schemas.ingest import IMUReading, IngestRequest, IngestResponse

logger = logging.getLogger(__name__)


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

    task_result = process_session.delay(str(gait_session.id))
    logger.info(f"Enqueued process_session task: task_id={task_result.id} session={gait_session.id}")

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
