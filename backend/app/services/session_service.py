import logging
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gait_session import GaitSession, SessionStatus
from app.models.user import User
from app.schemas.session import PatientSessionListResponse, SessionSummary, SessionStatusEnum

logger = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    SessionStatus.ingested: [SessionStatus.processing],
    SessionStatus.processing: [SessionStatus.done, SessionStatus.error],
    SessionStatus.done: [],
    SessionStatus.error: [SessionStatus.ingested],
}

async def get_session_or_404(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID | None = None
) -> GaitSession:
    query = select(GaitSession).where(GaitSession.id == session_id)
    if user_id is not None:
        query = query.where(GaitSession.user_id == user_id)
        
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session

async def update_session_status(
    db: AsyncSession,
    session_id: UUID,
    new_status: SessionStatusEnum,
    error_message: str | None = None,
    task_id: str | None = None,
    reading_count: int | None = None,
) -> tuple[GaitSession, SessionStatusEnum]:
    result = await db.execute(
        select(GaitSession).where(GaitSession.id == session_id).with_for_update()
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
        
    previous_status = session.status

    if new_status not in VALID_TRANSITIONS.get(previous_status, []):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition from {previous_status} to {new_status}. Allowed: {VALID_TRANSITIONS.get(previous_status, [])}"
        )

    session.status = new_status
    session.status_updated_at = datetime.utcnow()
    
    if error_message: 
        session.error_message = error_message
    else: 
        session.error_message = None
        
    if task_id: 
        session.task_id = task_id
    if reading_count is not None: 
        session.reading_count = reading_count

    await db.commit()
    await db.refresh(session)
    logger.info(f"Session {session_id} status: {previous_status} → {new_status}")
    
    return session, previous_status

async def list_patient_sessions(
    db: AsyncSession,
    patient_id: UUID,
    doctor_id: UUID,
    status_filter: SessionStatusEnum | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PatientSessionListResponse:
    # 1. Verify doctor has access
    patient_result = await db.execute(select(User).where(User.id == patient_id, User.role == 'patient'))
    if patient_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    access_result = await db.execute(
        select(GaitSession).where(GaitSession.user_id == patient_id, GaitSession.doctor_id == doctor_id).limit(1)
    )
    if access_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="You do not have access to this patient's sessions")

    # 2. Build query
    query = select(GaitSession).where(GaitSession.user_id == patient_id)
    if status_filter:
        query = query.where(GaitSession.status == status_filter.value)
    query = query.order_by(GaitSession.created_at.desc())

    # 3. Count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # 4. Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    sessions = result.scalars().all()

    return PatientSessionListResponse(
        patient_id=patient_id,
        sessions=[SessionSummary.model_validate(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(sessions)) < total,
    )

async def assign_doctor_to_session(
    db: AsyncSession,
    session_id: UUID,
    doctor_id: UUID,
    requesting_doctor_id: UUID,
) -> GaitSession:
    if doctor_id != requesting_doctor_id:
        raise HTTPException(status_code=403, detail="Can only assign self")
    
    session = await get_session_or_404(db, session_id)
    if session.doctor_id is not None and session.doctor_id != requesting_doctor_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session already assigned to another doctor")
        
    session.doctor_id = doctor_id
    await db.commit()
    await db.refresh(session)
    
    from app.core.cache import cache_delete, cache_delete_pattern
    await cache_delete(f"doctor:patients:{doctor_id}")
    await cache_delete_pattern(f"doctor:patient_detail:{doctor_id}:{session.user_id}:*")
    
    return session

def sync_update_session_status(
    session_id: str,
    new_status: str,
    error_message: str | None = None,
    reading_count: int | None = None,
) -> None:
    from datetime import timezone
    from app.db.sync_session import get_sync_db
    try:
        with get_sync_db() as db:
            update_data: dict = {
                "status": new_status,
                "status_updated_at": datetime.now(timezone.utc),
            }
            if error_message is not None:
                update_data["error_message"] = error_message
            if reading_count is not None:
                update_data["reading_count"] = reading_count

            db.query(GaitSession).filter(GaitSession.id == UUID(session_id)).update(update_data)
            db.commit()
            logger.info(f"Sync update session {session_id} to {new_status}")
    except Exception as e:
        logger.error(f"Failed to sync_update_session_status for {session_id}: {e}")

