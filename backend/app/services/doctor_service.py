import json
from datetime import datetime
from typing import Any, Literal, cast
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.doctor import PatientSummary, PatientListFilters, PatientListResponse
from app.core.cache import cache_get, cache_set

async def get_assigned_patients_raw(db: AsyncSession, doctor_id: UUID) -> list[dict]:
    query = text("""
        SELECT DISTINCT ON (u.id)
            u.id as user_id,
            u.email,
            u.full_name,
            u.bio_age,
            gs.id              AS latest_session_id,
            gs.started_at      AS last_seen,
            gs.status          AS session_status,
            ms.movement_age,
            ms.movement_age_delta,
            ms.interpretation_status as overall_status,
            ms.symmetry_score,
            ms.stability_score,
            ms.cadence
        FROM users u
        JOIN gait_sessions gs
            ON gs.user_id = u.id
            AND gs.doctor_id = :doctor_id
            AND gs.status    = 'done'
        LEFT JOIN metrics_snapshots ms
            ON ms.gait_session_id = gs.id
        WHERE u.role = 'patient'
        ORDER BY u.id, gs.started_at DESC;
    """)

    result = await db.execute(query, {"doctor_id": str(doctor_id)})
    rows = result.mappings().all()
    return [dict(row) for row in rows]

async def apply_filters_and_paginate(
    rows: list[dict],
    filters: PatientListFilters,
) -> tuple[list[PatientSummary], int, dict]:
    summaries = []
    
    total_concern = 0
    total_attention = 0
    total_normal = 0
    total_no_data = 0

    for r in rows:
        status_val = r.get("overall_status")
        if status_val is not None and hasattr(status_val, "value"):
            status_val = getattr(status_val, "value")
        
        if status_val == "concern": total_concern += 1
        elif status_val == "attention": total_attention += 1
        elif status_val == "normal": total_normal += 1
        
        if r.get("movement_age") is None:
            total_no_data += 1

        if filters.search:
            s = filters.search.lower()
            name = (r.get("full_name") or "").lower()
            email = (r.get("email") or "").lower()
            if s not in name and s not in email:
                continue

        if filters.status and status_val != filters.status:
            continue

        days_since = None
        last_seen = r.get("last_seen")
        if last_seen:
            if last_seen.tzinfo is not None:
                delta = datetime.now(last_seen.tzinfo) - last_seen
            else:
                delta = datetime.utcnow() - last_seen
            days_since = delta.days

        summaries.append(PatientSummary(
            **r,
            overall_status=status_val,
            alert=(status_val == "concern"),
            days_since_last_session=days_since
        ))

    def get_sort_key(s: PatientSummary):
        if filters.sort == "last_seen": val = s.last_seen
        elif filters.sort == "movement_age": val = s.movement_age
        elif filters.sort == "movement_age_delta": val = s.movement_age_delta
        else: val = s.full_name.lower() if s.full_name else "~"
        
        return (val is None, val)

    summaries.sort(key=get_sort_key, reverse=(filters.order == "desc"))

    total = len(summaries)
    stats = {
        "total_concern": total_concern,
        "total_attention": total_attention,
        "total_normal": total_normal,
        "total_no_data": total_no_data,
    }

    start = (filters.page - 1) * filters.page_size
    end = start + filters.page_size
    
    return summaries[start:end], total, stats

async def get_patient_list(
    db: AsyncSession,
    doctor_id: UUID,
    filters: PatientListFilters,
) -> PatientListResponse:
    cache_key = f"doctor:patients:{doctor_id}"
    cached_raw = await cache_get(cache_key)
    
    is_cached = True
    if cached_raw is None:
        raw_rows = await get_assigned_patients_raw(db, doctor_id)
        
        def default_serialize(obj):
            if isinstance(obj, UUID): return str(obj)
            if isinstance(obj, datetime): return obj.isoformat()
            if hasattr(obj, 'value'): return obj.value
            return str(obj)
        
        await cache_set(cache_key, [
            {k: default_serialize(v) if not isinstance(v, (int, float, str, bool, type(None))) else v 
             for k, v in r.items()} for r in raw_rows
        ], ttl=120)
        
        cached_raw = raw_rows
        is_cached = False
    else:
        for r in cached_raw:
            if "last_seen" in r and r["last_seen"] and isinstance(r["last_seen"], str):
                r["last_seen"] = datetime.fromisoformat(r["last_seen"])
            if "user_id" in r and r["user_id"] and isinstance(r["user_id"], str):
                r["user_id"] = UUID(r["user_id"])
            if "latest_session_id" in r and r["latest_session_id"] and isinstance(r["latest_session_id"], str):
                r["latest_session_id"] = UUID(r["latest_session_id"])

    page_data, total, stats = await apply_filters_and_paginate(cached_raw, filters)

    return PatientListResponse(
        doctor_id=doctor_id,
        patients=page_data,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        has_more=(filters.page * filters.page_size) < total,
        cached=is_cached,
        **stats
    )

import asyncio
from datetime import timedelta
from typing import Literal
import numpy as np
from app.schemas.doctor import (
    PatientDetail, SessionHistory, SessionRow, MovementAgeSummaryDetail,
    MetricChart, ChartPoint, ExerciseAdherence, ExerciseAdherenceRow
)
from app.utils.timeseries import gap_fill_chart

def resolve_status_badge(
    interpretation_status: str | None,
) -> Literal["normal", "attention", "concern", "no_data"]:
    if interpretation_status is None:
        return "no_data"
    if interpretation_status in {"normal", "attention", "concern", "no_data"}:
        return cast(Literal["normal", "attention", "concern", "no_data"], interpretation_status)
    return "no_data"

def _build_movement_age_summary(session_rows: list, bio_age: int | None) -> MovementAgeSummaryDetail:
    vals = [r["movement_age"] for r in session_rows if r.get("movement_age") is not None]
    
    current_movement_age = vals[0] if vals else None
    
    best_movement_age = min(vals) if vals else None
    worst_movement_age = max(vals) if vals else None
    first_movement_age = vals[-1] if vals else None
    
    current_delta = None
    if current_movement_age is not None and bio_age is not None:
        current_delta = current_movement_age - bio_age
        
    overall_trend = None
    if len(vals) >= 2:
        # Array was sorted DESC by date in SQL. Reverse for historical time-based slope (oldest = index 0)
        temporal_vals = list(reversed(vals))
        x = np.arange(len(temporal_vals))
        y = np.array(temporal_vals)
        slope = np.polyfit(x, y, 1)[0]
        
        if abs(slope) < 0.05:
            overall_trend = "stable"
        else:
            overall_trend = "declining" if slope > 0 else "improving"

    return MovementAgeSummaryDetail(
        current_movement_age=current_movement_age,
        bio_age=bio_age,
        current_delta=current_delta,
        best_movement_age=best_movement_age,
        worst_movement_age=worst_movement_age,
        first_movement_age=first_movement_age,
        sessions_analyzed=len(vals),
        overall_trend=overall_trend
    )

async def _query_user(db: AsyncSession, patient_id: UUID) -> dict | None:
    res = await db.execute(text("SELECT * FROM users WHERE id = :patient_id"), {"patient_id": str(patient_id)})
    row = res.mappings().first()
    return dict(row) if row else None

async def _query_session_history(db: AsyncSession, patient_id: UUID, doctor_id: UUID, page: int, limit: int) -> tuple[list[dict], int]:
    offset = (page - 1) * limit
    
    q_data = text("""
        SELECT gs.id as session_id, gs.started_at, gs.ended_at, gs.duration_seconds, gs.status, gs.device_id,
               ms.movement_age, ms.interpretation_status, ms.symmetry_score, ms.stability_score, ms.cadence, ms.movement_age_delta
        FROM gait_sessions gs
        LEFT JOIN metrics_snapshots ms ON ms.gait_session_id = gs.id
        WHERE gs.user_id = :patient_id AND gs.doctor_id = :doctor_id
        ORDER BY gs.started_at DESC
        LIMIT :limit OFFSET :offset
    """)
    q_count = text("""
        SELECT COUNT(*)
        FROM gait_sessions
        WHERE user_id = :patient_id AND doctor_id = :doctor_id
    """)
    res_data, res_count = await asyncio.gather(
        db.execute(q_data, {"patient_id": str(patient_id), "doctor_id": str(doctor_id), "limit": limit, "offset": offset}),
        db.execute(q_count, {"patient_id": str(patient_id), "doctor_id": str(doctor_id)})
    )
    raw_count = res_count.scalar()
    return [dict(r) for r in res_data.mappings().all()], int(raw_count or 0)

async def _query_chart_data(db: AsyncSession, patient_id: UUID, doctor_id: UUID, trend_days: int) -> list[dict]:
    q = text("""
        SELECT
            time_bucket('1 day', gs.started_at) AS bucket,
            AVG(ms.movement_age)                AS movement_age,
            AVG(ms.symmetry_score)              AS symmetry_score,
            AVG(ms.stability_score)             AS stability_score,
            AVG(ms.cadence)                     AS cadence,
            COUNT(*)                            AS session_count
        FROM gait_sessions gs
        JOIN metrics_snapshots ms ON ms.gait_session_id = gs.id
        WHERE gs.user_id = :patient_id
          AND gs.doctor_id = :doctor_id
          AND gs.status = 'done'
          AND gs.started_at >= NOW() - CAST(:days_str AS INTERVAL)
        GROUP BY bucket
        ORDER BY bucket ASC
    """)
    res = await db.execute(q, {
        "patient_id": str(patient_id),
        "doctor_id": str(doctor_id),
        "days_str": f"{trend_days} days"
    })
    return [dict(r) for r in res.mappings().all()]


async def _query_exercise_adherence(db: AsyncSession, patient_id: UUID, doctor_id: UUID) -> list[dict]:
    q = text("""
        SELECT
            e.title,
            e.difficulty,
            NULL as for_metric,
            COUNT(e.id) AS times_prescribed,
            MAX(gs.started_at) AS last_prescribed
        FROM exercises e
        JOIN metrics_snapshots ms ON ms.id = e.metrics_snapshot_id
        JOIN gait_sessions gs ON gs.id = ms.gait_session_id
        WHERE gs.user_id = :patient_id AND gs.doctor_id = :doctor_id
        GROUP BY e.title, e.difficulty
        ORDER BY times_prescribed DESC
        LIMIT 20
    """)
    res = await db.execute(q, {"patient_id": str(patient_id), "doctor_id": str(doctor_id)})
    return [dict(r) for r in res.mappings().all()]

async def get_patient_detail(
    db: AsyncSession,
    patient_id: UUID,
    doctor_id: UUID,
    trend_days: Literal[7, 30, 90],
    sessions_page: int,
    sessions_limit: int,
) -> PatientDetail:
    from app.core.cache import cache_get, cache_set
    from datetime import date
    
    cache_key = f"doctor:patient_detail:{doctor_id}:{patient_id}:{trend_days}:{sessions_page}:{sessions_limit}"
    cached_payload = await cache_get(cache_key)
    if cached_payload:
        pd = PatientDetail(**cached_payload)
        pd.cached = True
        return pd

    user_row, (session_rows, session_count), chart_rows, exercise_rows = await asyncio.gather(
        _query_user(db, patient_id),
        _query_session_history(db, patient_id, doctor_id, sessions_page, sessions_limit),
        _query_chart_data(db, patient_id, doctor_id, trend_days),
        _query_exercise_adherence(db, patient_id, doctor_id),
    )

    if not user_row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Patient not found or unauthorized")
        
    if session_count == 0:
        # Check explicit assignment independently if 0 logs returned 
        # Actually session_count implicitly validates because 'doctor_id' must exist on at least 1 session to pass strict assignment auth as requested:
        # "at least one gait_session WHERE user_id=patient_id AND doctor_id=doctor_id. If none: raise 403"
        valid_res = await db.execute(text("SELECT 1 FROM gait_sessions WHERE user_id = :p AND doctor_id = :d LIMIT 1"), {"p": str(patient_id), "d": str(doctor_id)})
        if not valid_res.scalar():
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Not assigned to this patient")

    # Mapped SessionRows
    mapped_sessions = []
    for r in session_rows:
        mapped_sessions.append(SessionRow(
            session_id=r["session_id"],
            started_at=r["started_at"],
            ended_at=r["ended_at"],
            duration_seconds=r["duration_seconds"],
            status=r["status"],
            device_id=r["device_id"],
            movement_age=r["movement_age"],
            movement_age_delta=r["movement_age_delta"],
            interpretation_status=r["interpretation_status"],
            symmetry_score=r["symmetry_score"],
            stability_score=r["stability_score"],
            cadence=r["cadence"],
            status_badge=resolve_status_badge(r["interpretation_status"])
        ))
        
    s_hist = SessionHistory(
        sessions=mapped_sessions,
        total=session_count,
        page=sessions_page,
        page_size=sessions_limit,
        has_more=(sessions_page * sessions_limit) < session_count
    )

    mag_summary = _build_movement_age_summary(session_rows, user_row.get("bio_age"))

    # Trend map resolution
    METRIC_LABEL_MAP = {
        "movement_age": ("Movement Age", "years", True),
        "symmetry_score": ("Step Symmetry", "ratio", False),
        "stability_score": ("Stability Score", "score", False),
        "cadence": ("Cadence", "steps/min", False)
    }
    
    from_date = date.today() - timedelta(days=trend_days - 1)
    to_date = date.today()
    
    charts = {}
    for metric_key, (lbl, unit, lower_is_better) in METRIC_LABEL_MAP.items():
        # Inject explicit 'value' bindings so gap_fill sees standard property
        remapped_charts = []
        for cr in chart_rows:
            obj = dict(cr)
            obj["value"] = cr.get(metric_key)
            remapped_charts.append(obj)
            
        gaps_filled = gap_fill_chart(remapped_charts, from_date, to_date)
        
        # Calculate stats explicitly for Chart Metric schema
        vals = [g.value for g in gaps_filled if g.value is not None]
        
        first_val = vals[0] if vals else None
        last_val = vals[-1] if vals else None
        best = min(vals) if lower_is_better and vals else (max(vals) if vals else None)
        worst = max(vals) if lower_is_better and vals else (min(vals) if vals else None)
        
        trend_direction = None
        if len(vals) >= 2:
            x = np.arange(len(vals))
            y = np.array(vals)
            slope = np.polyfit(x, y, 1)[0]
            if abs(slope) < 0.05: trend_direction = "stable"
            else:
                if lower_is_better: trend_direction = "declining" if slope > 0 else "improving"
                else: trend_direction = "improving" if slope > 0 else "declining"
        
        points = [ChartPoint(date=g.date, value=g.value, session_count=g.session_count) for g in gaps_filled]
        
        charts[metric_key] = MetricChart(
            metric=metric_key,
            label=lbl,
            unit=unit,
            points=points,
            first=first_val,
            last=last_val,
            best=best,
            worst=worst,
            trend=trend_direction
        )

    # Adherence
    adherence_rows = []
    total_p = 0
    max_p = -1
    mc = None
    
    for e in exercise_rows:
        rcount = min(e["times_prescribed"], e["times_prescribed"]) # ensure int conversion just in case BigInt
        total_p += rcount
        if rcount > max_p:
            max_p = rcount
            mc = e["title"]
            
        adherence_rows.append(ExerciseAdherenceRow(
            title=e["title"],
            difficulty=e["difficulty"],
            for_metric=e["for_metric"],
            times_prescribed=rcount,
            last_prescribed=e["last_prescribed"]
        ))
        
    adherence = ExerciseAdherence(
        exercises=adherence_rows,
        total_prescribed=total_p,
        unique_exercises=len(adherence_rows),
        most_common=mc
    )
    
    # Flags computation
    has_concern = any(s.status_badge == "concern" for s in mapped_sessions)
    last_seen = mapped_sessions[0].started_at if mapped_sessions else None
    
    t0 = datetime.now()
    if last_seen and last_seen.tzinfo is not None:
        t0 = datetime.now(last_seen.tzinfo)
    week_ago = t0 - timedelta(days=7)
    
    s_this_week = sum(1 for s in mapped_sessions if s.started_at >= week_ago)
    
    first_assigned = mapped_sessions[-1].started_at if mapped_sessions else None

    # Produce output model
    output = PatientDetail(
        patient_id=patient_id,
        full_name=user_row.get("full_name"),
        email=str(user_row.get("email") or ""),
        bio_age=user_row.get("bio_age"),
        doctor_id=doctor_id,
        first_assigned=first_assigned,
        movement_age_summary=mag_summary,
        charts=charts,
        trend_days=trend_days,
        session_history=s_hist,
        exercise_adherence=adherence,
        has_concern_sessions=has_concern,
        sessions_this_week=s_this_week,
        last_seen=last_seen,
        total_sessions=session_count,
        cached=False
    )
    
    # Date serialization parsing before Redis hook
    def recursive_date_serialization(o):
        import copy
        co = copy.deepcopy(o)
        from datetime import datetime, date
        def traverse(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, (datetime, date)): obj[k] = v.isoformat()
                    else: traverse(v)
            elif isinstance(obj, list):
                for idx, v in enumerate(obj):
                    if isinstance(v, (datetime, date)): obj[idx] = v.isoformat()
                    else: traverse(v)
        traverse(co)
        return co
    
    serialized_model_cache = json.loads(output.model_dump_json())
    await cache_set(cache_key, serialized_model_cache, ttl=300)
    
    return output

