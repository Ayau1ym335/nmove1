from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_doctor
from app.db.session import get_db
from app.models.user import User

from app.schemas.doctor import PatientListFilters, PatientListResponse
from app.services.doctor_service import get_patient_list
from app.services.session_service import get_session_or_404
from app.services.trend_service import get_user_trends
from app.schemas.trends import TrendsResponse
from fastapi import Query
from typing import Literal
from app.routers.dashboard import get_dashboard_summary

router = APIRouter(prefix="/doctor", tags=["doctor"])

@router.get(
    "/patients",
    response_model=PatientListResponse,
    status_code=200,
)
async def list_patients(
    filters: PatientListFilters = Depends(),
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
) -> PatientListResponse:
    return await get_patient_list(db, current_user.id, filters)

from pydantic import BaseModel, Field, ConfigDict

class PatientDetailParams(BaseModel):
    trend_days:     Literal[7, 30, 90] = 30
    sessions_page:  int = Field(1, ge=1)
    sessions_limit: int = Field(10, ge=1, le=50)
    model_config = ConfigDict(extra="ignore")

from app.schemas.doctor import PatientDetail
from app.services.doctor_service import get_patient_detail

@router.get(
    "/patients/{patient_id}",
    response_model=PatientDetail,
    status_code=200,
)
async def get_patient_detail_api(
    patient_id: UUID,
    params: PatientDetailParams = Depends(),
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
) -> PatientDetail:
    return await get_patient_detail(
        db=db,
        patient_id=patient_id,
        doctor_id=current_user.id,
        trend_days=params.trend_days,
        sessions_page=params.sessions_page,
        sessions_limit=params.sessions_limit
    )


@router.get(
    "/patients/{patient_id}/trends",
    response_model=TrendsResponse,
    status_code=200,
)
async def get_patient_trends(
    patient_id: UUID,
    days: Literal[7, 30, 90] = Query(30),
    metrics: list[str] = Query(["movement_age", "symmetry_score", "stability_score"]),
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
) -> TrendsResponse:
    # Router logic from trends checks authorization internally for doctors accessing patients trends
    # Just pass the proxy params forwards 
    from app.routers.trends import get_trends
    return await get_trends(patient_id, days, metrics, current_user, db)

from app.schemas.report import ReportRequest, ReportTaskResponse, ReportStatusResponse, ReportListItem
from app.tasks.generate_report import generate_report as generate_report_task
from app.services.minio_service import list_patient_reports
from celery.result import AsyncResult
from sqlalchemy import text

@router.post(
    "/patients/{patient_id}/report",
    response_model=ReportTaskResponse,
    status_code=202,
)
async def create_patient_report(
    patient_id: UUID,
    request: ReportRequest,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
) -> ReportTaskResponse:
    valid_res = await db.execute(
        text("SELECT 1 FROM gait_sessions WHERE user_id = :p AND doctor_id = :d LIMIT 1"),
        {"p": str(patient_id), "d": str(current_user.id)}
    )
    if not valid_res.scalar():
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not assigned to this patient")

    task = generate_report_task.delay(str(patient_id), str(current_user.id), request.days)
    
    return ReportTaskResponse(
        task_id=task.id,
        patient_id=patient_id,
        status="queued",
        message="Report generation started. Poll task_id for completion.",
        estimated_seconds=45,
    )

@router.get(
    "/patients/{patient_id}/report/status/{task_id}",
    response_model=ReportStatusResponse,
    status_code=200,
)
async def get_report_status(
    patient_id: UUID,
    task_id: str,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
) -> ReportStatusResponse:
    valid_res = await db.execute(
        text("SELECT 1 FROM gait_sessions WHERE user_id = :p AND doctor_id = :d LIMIT 1"),
        {"p": str(patient_id), "d": str(current_user.id)}
    )
    if not valid_res.scalar():
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not assigned to this patient")

    task_result = AsyncResult(task_id)
    state = task_result.state
    
    status_map = {
        "PENDING": "queued",
        "STARTED": "processing",
        "SUCCESS": "done",
        "FAILURE": "failed"
    }
    status = status_map.get(state, "queued")
    
    url = None
    expires_at = None
    error = None
    
    if status == "done":
        res_data = task_result.result
        if isinstance(res_data, dict):
            url = res_data.get("url")
            exp_str = res_data.get("expires_at")
            if exp_str:
                from datetime import datetime
                expires_at = datetime.fromisoformat(exp_str)
    elif status == "failed":
        error = str(task_result.result)
        
    return ReportStatusResponse(
        task_id=task_id,
        status=status,
        url=url,
        expires_at=expires_at,
        error=error,
    )

@router.get(
    "/patients/{patient_id}/report/history",
    response_model=list[ReportListItem],
    status_code=200,
)
async def get_report_history(
    patient_id: UUID,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
) -> list[ReportListItem]:
    valid_res = await db.execute(
        text("SELECT 1 FROM gait_sessions WHERE user_id = :p AND doctor_id = :d LIMIT 1"),
        {"p": str(patient_id), "d": str(current_user.id)}
    )
    if not valid_res.scalar():
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not assigned to this patient")

    import asyncio
    return await asyncio.to_thread(list_patient_reports, patient_id)

