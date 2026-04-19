"""app/routers/patient.py — Patient-facing endpoints."""

from typing import Any, cast, Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.dependencies import require_patient
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import ReportRequest, ReportTaskResponse, ReportStatusResponse, ReportListItem
from app.tasks.generate_report import generate_report as generate_report_task
from app.services.minio_service import list_patient_reports
from celery.result import AsyncResult

router = APIRouter(prefix="/patient", tags=["patient"])


@router.post(
    "/report",
    response_model=ReportTaskResponse,
    status_code=202,
    summary="Patient: generate a PDF report for own gait data",
)
async def create_own_report(
    request: ReportRequest,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> ReportTaskResponse:
    """Generate a PDF report for the authenticated patient.

    Looks up the doctor assigned to the patient's most recent session and
    delegates to the same Celery task used by the doctor endpoint
    (``POST /doctor/patients/{id}/report``).

    Returns 404 if the patient has no sessions with an assigned doctor yet.
    """
    # Find the doctor assigned to this patient's most-recent session
    row = await db.execute(
        text(
            """
            SELECT doctor_id
            FROM gait_sessions
            WHERE user_id = :patient_id AND doctor_id IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"patient_id": str(current_user.id)},
    )
    doctor_id = row.scalar_one_or_none()
    if not doctor_id:
        raise HTTPException(
            status_code=404,
            detail="No sessions with an assigned doctor found. "
                   "A doctor must be linked to at least one of your sessions before a report can be generated.",
        )

    task = cast(Any, generate_report_task).delay(
        str(current_user.id), str(doctor_id), request.days
    )

    return ReportTaskResponse(
        task_id=task.id,
        patient_id=current_user.id,
        status="queued",
        message="Report generation started. Poll task_id for completion.",
        estimated_seconds=45,
    )


@router.get(
    "/report/status/{task_id}",
    response_model=ReportStatusResponse,
    status_code=200,
    summary="Patient: poll report generation status",
)
async def get_own_report_status(
    task_id: str,
    current_user: User = Depends(require_patient),
) -> ReportStatusResponse:
    """Poll the Celery task status for a previously queued report."""
    task_result = AsyncResult(task_id)
    state = task_result.state

    status_map = {
        "PENDING": "queued",
        "STARTED": "processing",
        "SUCCESS": "done",
        "FAILURE": "failed",
    }
    status = cast(
        Literal["queued", "processing", "done", "failed"],
        status_map.get(state, "queued"),
    )

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
    "/report/history",
    response_model=list[ReportListItem],
    status_code=200,
    summary="Patient: list previously generated reports",
)
async def get_own_report_history(
    current_user: User = Depends(require_patient),
) -> list[ReportListItem]:
    """Return all PDF reports stored in MinIO for the authenticated patient."""
    import asyncio
    return await asyncio.to_thread(list_patient_reports, current_user.id)
