from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.gait_session import GaitSession
from app.core.dependencies import require_any_role
from app.core.cache import cache_get, cache_set, redis_client
from app.schemas.trends import TrendsResponse
from app.services.trend_service import get_user_trends, METRIC_COLUMN_MAP

router = APIRouter(prefix="/trends", tags=["trends"])

def trends_cache_key(user_id: str, days: int, sorted_metrics_joined: str) -> str:
    return f"trends:{user_id}:{days}:{sorted_metrics_joined}"

@router.get(
    "/{user_id}",
    response_model=TrendsResponse,
    status_code=200,
    summary="Get aggregated trend data for a specified timeframe",
)
async def get_trends(
    user_id: UUID,
    days: Literal[7, 30, 90] = Query(30, description="Time bucket window in days"),
    metrics: list[str] = Query(["movement_age", "symmetry_score", "stability_score"]),
    current_user: User = Depends(require_any_role),
    db: AsyncSession = Depends(get_db)
) -> TrendsResponse:
    
    # Validation against whitelist
    for m in metrics:
        if m not in METRIC_COLUMN_MAP:
            raise HTTPException(status_code=422, detail=f"Invalid metric requested: {m}")
            
    sorted_metrics_joined = ",".join(sorted(metrics))

    # Authorization rules
    if current_user.role == UserRole.patient and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Patients can only view their own trends")

    if current_user.role == UserRole.doctor:
        assigned = await db.execute(
            select(GaitSession)
            .where(GaitSession.user_id == user_id)
            .where(GaitSession.doctor_id == current_user.id)
            .limit(1)
        )
        if assigned.scalar_one_or_none() is None:
            raise HTTPException(status_code=403, detail="You are not assigned to any of this patient's sessions")

    # Cache execution
    cache_key = trends_cache_key(str(user_id), days, sorted_metrics_joined)
    cached_data = await cache_get(cache_key)
    
    if cached_data:
        response = TrendsResponse(**cached_data)
        response.cached = True
        return response

    # Cache missed
    result = await get_user_trends(db, user_id, days, metrics)
    
    CACHE_WINDOWS = {
        7: 10 * 60,
        30: 30 * 60,
        90: 60 * 60,
    }
    await cache_set(cache_key, result.model_dump(), ttl=CACHE_WINDOWS[days])
    
    return result
