"""app/routers/sessions.py — Gait session lifecycle + IMU ingest endpoints."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import require_patient, require_doctor, require_any_role
from ..db.session import get_db
from ..models.gait_session import GaitSession
from ..models.user import User, UserRole
from ..schemas.ingest import IngestRequest, IngestResponse
from ..schemas.session import (
    PatchSessionStatusRequest, SessionSummary, SessionDetail, 
    PatientSessionListResponse, SessionStatusUpdateResponse, SessionStatusEnum
)
from ..services import ingest_service, session_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get(
    "/me",
    response_model=PatientSessionListResponse,
    status_code=200,
    summary="Patient: list own sessions",
)
async def list_my_sessions(
    status_filter: SessionStatusEnum | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> PatientSessionListResponse:
    from sqlalchemy import func
    
    query = select(GaitSession).where(GaitSession.user_id == current_user.id)
    if status_filter:
        query = query.where(GaitSession.status == status_filter.value)
    query = query.order_by(GaitSession.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    sessions = result.scalars().all()

    return PatientSessionListResponse(
        patient_id=current_user.id,
        sessions=[SessionSummary.model_validate(s) for s in sessions],
        total=total if total is not None else 0,
        page=page,
        page_size=page_size,
        has_more=(offset + len(sessions)) < (total if total is not None else 0),
    )


@router.get(
    "/doctor/patients/{patient_id}",
    response_model=PatientSessionListResponse,
    status_code=200,
    summary="Doctor: list all sessions for a patient",
)
async def list_sessions_for_patient(
    patient_id: uuid.UUID,
    status_filter: SessionStatusEnum | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> PatientSessionListResponse:
    return await session_service.list_patient_sessions(db, patient_id, current_user.id, status_filter, page, page_size)


@router.get(
    "/{session_id}",
    response_model=SessionDetail,
    status_code=200,
    summary="Get session detail with metrics",
)
async def get_session_detail(
    session_id: uuid.UUID,
    current_user: User = Depends(require_any_role),
    db: AsyncSession = Depends(get_db),
) -> SessionDetail:
    session = await session_service.get_session_or_404(db, session_id)
    
    if current_user.role == UserRole.patient:
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this session")
    else:
        if session.doctor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this session")
            
    return SessionDetail.model_validate(session)


@router.patch(
    "/{session_id}/status",
    response_model=SessionStatusUpdateResponse,
    status_code=200,
    summary="Update session processing status",
)
async def patch_session_status(
    session_id: uuid.UUID,
    body: PatchSessionStatusRequest,
    current_user: User = Depends(require_any_role),
    db: AsyncSession = Depends(get_db),
) -> SessionStatusUpdateResponse:
    session = await session_service.get_session_or_404(db, session_id)
    
    if current_user.role == UserRole.patient and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == UserRole.doctor and session.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    session, previous = await session_service.update_session_status(db, session_id, body.status, body.error_message)
    
    return SessionStatusUpdateResponse(
        session_id=session.id,
        previous_status=previous,
        new_status=body.status,
        updated_at=session.status_updated_at,
        message=f"Session status updated to {body.status}",
    )


@router.post(
    "/{session_id}/assign-doctor",
    response_model=SessionSummary,
    status_code=200,
    summary="Doctor: assign themselves to a session",
)
async def assign_doctor(
    session_id: uuid.UUID,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db),
) -> SessionSummary:
    session = await session_service.assign_doctor_to_session(db, session_id, current_user.id, current_user.id)
    return SessionSummary.model_validate(session)

# ---------------------------------------------------------------------------
# POST /sessions/start
# ---------------------------------------------------------------------------

@router.post(
    "/start",
    status_code=status.HTTP_201_CREATED,
    summary="Open a new gait session",
)
async def start_session(
    device_id: str | None = None,
    leg_side: Literal["left", "right"] = "left",
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> dict:
    now = datetime.now(timezone.utc)
    session = GaitSession(
        user_id=current_user.id,
        device_id=device_id.strip() if device_id else None,
        leg_side=leg_side,
        started_at=now,
        ended_at=None,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {
        "session_id": str(session.id),
        "started_at": session.started_at.isoformat(),
    }

# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/close
# ---------------------------------------------------------------------------

@router.post(
    "/{session_id}/close",
    status_code=status.HTTP_200_OK,
    summary="Close an open gait session",
)
async def close_session(
    session_id: uuid.UUID,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> dict:
    session = await session_service.get_session_or_404(db, session_id, current_user.id)
        
    if session.ended_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session already closed")

    now = datetime.now(timezone.utc)
    session.ended_at = now
    started = session.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    session.duration_seconds = (now - started).total_seconds()

    await db.commit()
    await db.refresh(session)

    return {
        "session_id": str(session.id),
        "ended_at": (session.ended_at or now).isoformat(),
        "duration_seconds": session.duration_seconds,
    }


# ---------------------------------------------------------------------------
# POST /sessions/ingest
# ---------------------------------------------------------------------------

@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest raw IMU readings from ESP32",
)
async def ingest_readings(
    data: IngestRequest,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    gait_session = await ingest_service.validate_session_ownership(db, data.session_id, current_user.id)
    return await ingest_service.write_readings(db, gait_session, data)


@router.post(
    "/ingest/bin",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest IMU binary .bin payload",
)
async def ingest_readings_bin(
    session_id: uuid.UUID = Form(...),
    leg_side: Literal["left", "right"] = Form(...),
    sensor_slot: Literal[1, 2] = Form(1),
    device_id: str | None = Form(None),
    imu_file: UploadFile = File(...),
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    filename = imu_file.filename or ""
    if not filename.lower().endswith(".bin"):
        raise HTTPException(status_code=400, detail="imu_file must be a .bin file")

    raw_bytes = await imu_file.read()
    gait_session = await ingest_service.validate_session_ownership(db, session_id, current_user.id)
    ingest_request = ingest_service.build_ingest_request_from_bin(
        raw_bytes=raw_bytes,
        session_id=session_id,
        leg_side=leg_side,
        device_id=device_id,
        sensor_slot=sensor_slot,
    )
    return await ingest_service.write_readings(db, gait_session, ingest_request)