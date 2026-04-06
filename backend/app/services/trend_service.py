import asyncio
from datetime import date, timedelta
from typing import Any
import numpy as np
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.trends import TrendsResponse, MetricTrendSeries, TrendDataPoint

# Map allowed metric keys to their SQL representation
# Since some domains (e.g. stride_time_cv) are not physically backed by columns in metrics_snapshots,
# we map them to NULL so the query runs and gracefully returns null data.
METRIC_COLUMN_MAP = {
    "movement_age":        "ms.movement_age",
    "symmetry_score":      "ms.symmetry_score",
    "stability_score":     "ms.stability_score",
    "cadence":             "ms.cadence",
    "stride_time_cv":      "NULL",
    "trunk_sway_rms":      "NULL",
    "hip_rotation_rom":    "NULL",
    "ankle_pushoff_proxy": "NULL",
}

METRIC_LABELS = {
    "movement_age":        ("Movement Age", "years", True),  # lower forms = True
    "symmetry_score":      ("Symmetry", "ratio", False),
    "stability_score":     ("Stability", "score", False),
    "cadence":             ("Basic Cadence", "steps/min", False),
    "stride_time_cv":      ("Stride Consistency", "score", True),
    "trunk_sway_rms":      ("Trunk Sway", "score", True),
    "hip_rotation_rom":    ("Hip Mobility", "deg", False),
    "ankle_pushoff_proxy": ("Ankle Pushoff", "score", False),
}


async def fetch_metric_series(
    db: AsyncSession,
    user_id: UUID,
    metric_column: str,
    days: int,
    from_date: date,
    to_date: date,
) -> list[TrendDataPoint]:
    sql = text("""
        SELECT
            time_bucket('1 day', gs.started_at) AS bucket,
            AVG({metric_column})               AS value,
            COUNT(ms.id)                       AS session_count
        FROM metrics_snapshots ms
        JOIN gait_sessions gs ON gs.id = ms.gait_session_id
        WHERE gs.user_id = :user_id
          AND gs.status = 'done'
          AND gs.started_at >= NOW() - CAST(:days_str AS INTERVAL)
        GROUP BY bucket
        ORDER BY bucket ASC;
    """)

    result = await db.execute(sql, {
        "user_id": str(user_id), 
        "days_str": f"{days} days"
    })
    rows = result.fetchall()

    from app.utils.timeseries import gap_fill_chart
    return gap_fill_chart(rows, from_date, to_date)


async def build_series_stats(
    data: list[TrendDataPoint],
    metric: str,
) -> MetricTrendSeries:
    label, unit, lower_is_better = METRIC_LABELS[metric]

    values = [d.value for d in data if d.value is not None]
    
    first_val = values[0] if values else None
    last_val = values[-1] if values else None
    
    change = None
    change_pct = None
    peak = None
    trough = None

    if values:
        change = last_val - first_val
        if first_val and first_val != 0:
            change_pct = (change / first_val) * 100
        peak = max(values)
        trough = min(values)

    trend_direction = None
    if len(values) >= 2:
        x = np.arange(len(values))
        y = np.array(values)
        slope = np.polyfit(x, y, 1)[0]
        
        # Determine trend direction using basic slope tolerance
        if abs(slope) < 0.05:
            trend_direction = "stable"
        else:
            if lower_is_better:
                trend_direction = "declining" if slope > 0 else "improving"
            else:
                trend_direction = "improving" if slope > 0 else "declining"

    return MetricTrendSeries(
        metric=metric,
        label=label,
        unit=unit,
        data=data,
        first_value=first_val,
        last_value=last_val,
        change=change,
        change_pct=change_pct,
        trend_direction=trend_direction,
        peak=peak,
        trough=trough
    )


async def get_user_trends(
    db: AsyncSession,
    user_id: UUID,
    days: int,
    metrics: list[str],
) -> TrendsResponse:
    from_date = date.today() - timedelta(days=days - 1)
    to_date = date.today()
    
    # Fire all SQL trend queries in parallel
    tasks = []
    for m in metrics:
        metric_column = METRIC_COLUMN_MAP[m]
        tasks.append(fetch_metric_series(db, user_id, metric_column, days, from_date, to_date))
    
    results = await asyncio.gather(*tasks)
    
    # Process sequential Python gap/stats builders
    series_tasks = [build_series_stats(res, m) for res, m in zip(results, metrics)]
    series_list = await asyncio.gather(*series_tasks)

    # Compute sum of unique session hits across entire requested period. 
    # Use any metric dimension since gait_session count relies on the primary timestamp axis grouping.
    total_sessions_in_window = sum(d.session_count for d in results[0]) if results else 0

    return TrendsResponse(
        user_id=user_id,
        days=days,
        from_date=from_date,
        to_date=to_date,
        series=series_list,
        total_sessions_in_window=total_sessions_in_window,
        cached=False
    )
