import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.gait_session import GaitSession
from app.models.metrics_snapshot import MetricsSnapshot
from app.models.profile import Profile
from app.models.user import User

router = APIRouter(prefix="/api/baseline", tags=["Baseline"])


class BaselineRecordRequest(BaseModel):
    user_id: uuid.UUID
    gait_session_id: uuid.UUID | None = None


@router.post("/record")
async def record_baseline(
    body: BaselineRecordRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(select(User).where(User.id == body.user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    profile = await db.scalar(select(Profile).where(Profile.user_id == body.user_id))
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    if body.gait_session_id is not None:
        snapshot = await db.scalar(
            select(MetricsSnapshot)
            .where(MetricsSnapshot.gait_session_id == body.gait_session_id)
            .order_by(desc(MetricsSnapshot.calculated_at))
            .limit(1)
        )
    else:
        snapshot = await db.scalar(
            select(MetricsSnapshot)
            .join(GaitSession, GaitSession.id == MetricsSnapshot.gait_session_id)
            .where(GaitSession.user_id == body.user_id)
            .order_by(desc(MetricsSnapshot.calculated_at))
            .limit(1)
        )

    if snapshot is None:
        raise HTTPException(status_code=404, detail="No processed metrics snapshot found")

    profile.baseline_snapshot_id = snapshot.id
    await db.flush()

    return {
        "status": "success",
        "message": "Baseline snapshot recorded",
        "baseline_snapshot_id": str(snapshot.id),
        "user_id": str(body.user_id),
        "recorded_at": datetime.now(UTC).isoformat(),
    }


@router.get("/{user_id}")
async def get_user_baseline(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    profile = await db.scalar(select(Profile).where(Profile.user_id == user_id))
    if not profile or profile.baseline_snapshot_id is None:
        return {
            "has_baseline": False,
            "message": "Baseline not recorded yet. Please use /api/baseline/record first.",
        }

    baseline = await db.scalar(
        select(MetricsSnapshot).where(MetricsSnapshot.id == profile.baseline_snapshot_id)
    )
    if baseline is None:
        return {"has_baseline": False, "message": "Baseline snapshot reference is invalid."}

    return {
        "has_baseline": True,
        "baseline_info": {
            "snapshot_id": str(baseline.id),
            "recorded_at": baseline.calculated_at.isoformat() if baseline.calculated_at else None,
        },
        "metrics": {
            "rhythm_pace": {
                "cadence": baseline.cadence,
                "avg_speed": baseline.avg_speed,
                "step_count": baseline.step_count,
                "stride_length": baseline.stride_length,
            },
            "joint_mechanics": {
                "hip_rotation_rom": baseline.hip_rotation_rom,
                "ankle_pushoff_proxy": baseline.ankle_pushoff_proxy,
                "vertical_oscillation": baseline.vertical_oscillation,
            },
            "variability": {
                "stride_time_cv": baseline.stride_time_cv,
                "trunk_sway_rms": baseline.trunk_sway_rms,
            },
            "symmetry_phases": {
                "symmetry_score": baseline.symmetry_score,
                "stance_phase_pct": baseline.stance_phase_pct,
                "double_support_pct": baseline.double_support_pct,
            },
        },
        "clinical_context": {
            "interpretation_status": baseline.interpretation_status.value,
            "movement_age": baseline.movement_age,
            "bio_age": baseline.bio_age,
            "movement_age_delta": baseline.movement_age_delta,
            "stability_score": baseline.stability_score,
        },
    }