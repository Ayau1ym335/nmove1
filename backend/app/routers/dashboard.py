import logging
from datetime import datetime, timedelta
from typing import Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_any_role
from app.db.session import get_db
from app.models.user import User
from app.models.gait_session import GaitSession
from app.models.metrics_snapshot import MetricsSnapshot
from app.models.exercise import Exercise
from app.models.user_model import UserModel

from app.core.cache import dashboard_cache_key, cache_get, cache_set, redis_client
from app.schemas.dashboard import (
    DashboardSummary, MovementAgeSummary, MetricValue, DomainScore, 
    ExerciseOut, IssueOut, STATUS_LABELS
)
from app.norms.norms_loader import get_norm, get_age_group, METRIC_DOMAIN_MAP

logger = logging.getLogger("nmove.routers.dashboard")
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

def get_status_from_issue(metric: str, value: float, issues: list) -> Literal["normal", "attention", "concern"]:
    for issue in issues:
        if issue["metric"] == metric:
            return issue["severity"]
    return "normal"

@router.get(
    "/{user_id}/summary",
    response_model=DashboardSummary,
    status_code=200,
    summary="Get movement summary dashboard for a user",
)
async def get_dashboard_summary(
    user_id: UUID,
    current_user: User = Depends(require_any_role),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummary:
    
    # -----------------------------------------------------
    # Authorization
    # -----------------------------------------------------
    if current_user.role == "patient" and current_user.id != user_id:
        raise HTTPException(403, "Patients can only view their own dashboard")

    if current_user.role == "doctor":
        assigned = await db.execute(
            select(GaitSession)
            .where(GaitSession.user_id == user_id)
            .where(GaitSession.doctor_id == current_user.id)
            .limit(1)
        )
        if assigned.scalar_one_or_none() is None:
            raise HTTPException(
                403, "You are not assigned to any of this patient's sessions"
            )

    # -----------------------------------------------------
    # Cache Check
    # -----------------------------------------------------
    cache_key = dashboard_cache_key(str(user_id))
    try:
        cached_data = await cache_get(cache_key)
        if cached_data:
            logger.info(f"Dashboard cache HIT for user={user_id}")
            summary = DashboardSummary(**cached_data)
            summary.cached = True
            
            ttl = await redis_client.ttl(cache_key)
            summary.cache_ttl_seconds = ttl if ttl > 0 else None
            return summary
    except Exception as e:
        logger.error(f"Redis cache resolution failed: {e}")

    logger.info(f"Dashboard cache MISS for user={user_id}")

    # -----------------------------------------------------
    # Build Dashboard from Database
    # -----------------------------------------------------
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    latest_session_result = await db.execute(
        select(GaitSession)
        .where(GaitSession.user_id == user_id)
        .where(GaitSession.status == "done")
        .order_by(GaitSession.created_at.desc())
        .limit(1)
    )
    latest_session = latest_session_result.scalar_one_or_none()

    if not latest_session:
        # Check whether a trained model exists for this user
        user_model_result = await db.execute(
            select(UserModel)
            .where(UserModel.user_id == user_id)
            .order_by(UserModel.trained_at.desc())
            .limit(1)
        )
        baseline_available = user_model_result.scalar_one_or_none() is not None

        summary = DashboardSummary(
            user_id=user_id,
            generated_at=datetime.utcnow(),
            overall_status="no_data",
            status_label=STATUS_LABELS["no_data"]["label"],
            status_description=STATUS_LABELS["no_data"]["description"],
            key_metrics=[],
            domain_scores=[],
            issues=[],
            exercises=[],
            movement_age=None,
            latest_session_id=None,
            latest_session_date=None,
            latest_session_status=None,
            total_sessions=0,
            sessions_this_week=0,
            personal_baseline_available=baseline_available,
        )
        await cache_set(cache_key, summary.model_dump(), ttl=60)
        return summary

    snapshot_result = await db.execute(
        select(MetricsSnapshot)
        .where(MetricsSnapshot.gait_session_id == latest_session.id)
        .order_by(MetricsSnapshot.calculated_at.desc())
        .limit(1)
    )
    snapshot = snapshot_result.scalar_one_or_none()

    exercises_db = []
    if snapshot:
        exercises_result = await db.execute(
            select(Exercise)
            .where(Exercise.metrics_snapshot_id == snapshot.id)
            .limit(5)
        )
        exercises_db = exercises_result.scalars().all()

    prev_session_result = await db.execute(
        select(GaitSession)
        .where(GaitSession.user_id == user_id)
        .where(GaitSession.status == "done")
        .where(GaitSession.id != latest_session.id)
        .order_by(GaitSession.created_at.desc())
        .limit(1)
    )
    prev_session = prev_session_result.scalar_one_or_none()

    prev_snapshot = None
    if prev_session:
        prev_snap_result = await db.execute(
            select(MetricsSnapshot)
            .where(MetricsSnapshot.gait_session_id == prev_session.id)
            .order_by(MetricsSnapshot.calculated_at.desc())
            .limit(1)
        )
        prev_snapshot = prev_snap_result.scalar_one_or_none()

    total_count = await db.scalar(
        select(func.count(GaitSession.id))
        .where(GaitSession.user_id == user_id)
        .where(GaitSession.status == "done")
    )

    week_ago = datetime.utcnow() - timedelta(days=7)
    week_count = await db.scalar(
        select(func.count(GaitSession.id))
        .where(GaitSession.user_id == user_id)
        .where(GaitSession.status == "done")
        .where(GaitSession.created_at >= week_ago)
    )

    # Re-run rule engine inline / retrieve pre-computed outputs
    # Because interpretation_service isn't mapped specifically to a persistent issues array
    # we reconstruct it by calling the interpretation service logic or using the snapshot fields.
    from app.services.interpretation_service import compute_interpretation
    metrics_mock = {
        "cadence": getattr(snapshot, "cadence", None) if snapshot else None,
        "step_symmetry_ratio": getattr(snapshot, "symmetry_score", None) if snapshot else None,
        "stability_score": getattr(snapshot, "stability_score", None) if snapshot else None
    }
    mov_age_mock = {"delta": getattr(snapshot, "movement_age_delta", None) if snapshot else None}

    interpretation = compute_interpretation(
        {k: v for k, v in metrics_mock.items() if v is not None}, 
        mov_age_mock
    )
    issues_out = [IssueOut(**iss) for iss in interpretation.get("issues", [])]

    # Assembly MovementAgeSummary
    movement_age_summary = None
    if snapshot and snapshot.movement_age is not None:
        delta_vs_last = None
        trend = None

        if prev_snapshot and prev_snapshot.movement_age is not None:
            delta_vs_last = int(snapshot.movement_age) - int(prev_snapshot.movement_age)
            if delta_vs_last <= -1:
                trend = "improving"
            elif delta_vs_last >= 2:
                trend = "declining"
            else:
                trend = "stable"

        movement_age_summary = MovementAgeSummary(
            movement_age=int(snapshot.movement_age),
            bio_age=snapshot.bio_age,
            delta=int(snapshot.movement_age_delta) if snapshot.movement_age_delta is not None else None,
            delta_vs_last_session=delta_vs_last,
            composite_score=snapshot.stability_score, # Because we map composite_score to stability_score previously in DB
            trend=trend,
        )

    # Assembly key metrics
    key_metrics = []
    if snapshot:
        bio_age_for_norm = snapshot.bio_age if snapshot.bio_age else 35
        age_group = get_age_group(bio_age_for_norm)
        
        SNAPSHOT_METRIC_MAP = {
            "cadence":             ("steps/min", "Walking pace"),
            "symmetry_score":      ("ratio",     "Step symmetry"),
            "stability_score":     ("score",     "Stability"),
            "movement_age":        ("years",     "Movement age"),
        }
        
        for attr_name, (unit, label) in SNAPSHOT_METRIC_MAP.items():
            val = getattr(snapshot, attr_name, None)
            if val is not None:
                # Check for issues array match
                pseudo_metric = attr_name
                if attr_name == "symmetry_score": pseudo_metric = "step_symmetry_ratio"
                
                status_metric = get_status_from_issue(pseudo_metric, val, interpretation.get("issues", []))
                
                mean_v = None
                sd_v = None
                try:
                    norm = get_norm(pseudo_metric, age_group)
                    mean_v = norm["mean"]
                    sd_v = norm["sd"]
                except ValueError:
                    pass
                except Exception as e:
                    logger.warning(f"Norm lookup failed: {e}")

                key_metrics.append(MetricValue(
                    value=val,
                    unit=unit,
                    label=label,
                    status=status_metric,
                    norm_mean=mean_v,
                    norm_sd=sd_v
                ))

    # Using dummy mapping since domain metrics aren't populated directly to snapshot columns
    domain_scores = []
    
    # Finalize
    overall_status = snapshot.interpretation_status if snapshot else "no_data"
    
    # In case overall_status resolves strictly to the Enum object in SQLAlchemy
    if not isinstance(overall_status, str):
        overall_status = cast(str, getattr(overall_status, "value", "no_data"))
    overall_status = cast(Literal["normal", "attention", "concern", "no_data"], overall_status)

    # ── ML / Anomaly fields ──────────────────────────────────────────────────
    user_model_result = await db.execute(
        select(UserModel)
        .where(UserModel.user_id == user_id)
        .order_by(UserModel.trained_at.desc())
        .limit(1)
    )
    baseline_available = user_model_result.scalar_one_or_none() is not None

    a_score   = getattr(snapshot, "anomaly_score", None) if snapshot else None
    a_flag    = getattr(snapshot, "is_anomaly",    None) if snapshot else None

    # ── Gemini insight (patient audience; doctor portal fetches separately) ──
    gemini_text: str | None = None
    if snapshot and baseline_available:
        try:
            from app.ml.gemini import get_gait_insight
            from app.services.trend_service import get_user_trends
            trend_result = await get_user_trends(db, user_id, 30, ["movement_age"])
            trend_dir = (
                trend_result.series[0].trend_direction
                if trend_result.series else None
            )
            gemini_text = await get_gait_insight(
                user_id, snapshot, trend_dir, audience="patient"
            )
        except Exception:
            logger.warning("Gemini insight failed for user=%s (non-fatal)", user_id)

    summary = DashboardSummary(
        user_id=user_id,
        generated_at=datetime.utcnow(),
        cached=False,
        overall_status=overall_status,
        status_label=STATUS_LABELS.get(overall_status, {}).get("label", "Unknown"),
        status_description=STATUS_LABELS.get(overall_status, {}).get("description", "Unknown"),
        latest_session_id=latest_session.id,
        latest_session_date=latest_session.started_at,
        latest_session_status=latest_session.status,
        movement_age=movement_age_summary,
        key_metrics=key_metrics,
        domain_scores=domain_scores,
        issues=issues_out,
        exercises=[ExerciseOut.model_validate(e) for e in exercises_db],
        total_sessions=total_count or 0,
        sessions_this_week=week_count or 0,
        personal_baseline_available=baseline_available,
        anomaly_score=a_score,
        is_anomaly=a_flag,
        gemini_insight=gemini_text,
        gemini_insight_audience="patient" if gemini_text else None,
    )

    await cache_set(cache_key, summary.model_dump(), ttl=300)
    logger.info(f"Dashboard built and cached for user={user_id} status={overall_status}")
    
    return summary
