import asyncio
from datetime import date, timedelta
from typing import Any, cast
import numpy as np
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.trends import TrendsResponse, MetricTrendSeries, TrendDataPoint

# Map allowed metric keys to their SQL column in metrics_snapshots (aliased as ms)
# NOTE: This is a server-side allowlist. metric_column values are NEVER derived
# from user input, so formatting them into SQL is safe.
METRIC_COLUMN_MAP = {
    "movement_age":        "ms.movement_age",
    "symmetry_score":      "ms.symmetry_score",
    "stability_score":     "ms.stability_score",
    "cadence":             "ms.cadence",
    "stride_time_cv":      "ms.stride_time_cv",
    "trunk_sway_rms":      "ms.trunk_sway_rms",
    "hip_rotation_rom":    "ms.hip_rotation_rom",
    "ankle_pushoff_proxy": "ms.ankle_pushoff_proxy",
    "anomaly_score":       "ms.anomaly_score",
    "avg_speed":           "ms.avg_speed",
    "stride_length":       "ms.stride_length",
}

METRIC_LABELS = {
    "movement_age":        ("Movement Age",       "years",    True),
    "symmetry_score":      ("Symmetry",           "ratio",    False),
    "stability_score":     ("Stability",          "score",    False),
    "cadence":             ("Cadence",            "steps/min",False),
    "stride_time_cv":      ("Stride Consistency", "CV%",      True),
    "trunk_sway_rms":      ("Trunk Sway",         "m/s²",     True),
    "hip_rotation_rom":    ("Hip Mobility",       "deg",      False),
    "ankle_pushoff_proxy": ("Ankle Pushoff",      "m/s²",     False),
    "anomaly_score":       ("Anomaly Score",      "0–1",      True),
    "avg_speed":           ("Avg Speed",          "m/s",      False),
    "stride_length":       ("Stride Length",      "m",        False),
}


async def fetch_metric_series(
    db: AsyncSession,
    user_id: UUID,
    metric_column: str,
    days: int,
    from_date: date,
    to_date: date,
) -> list[TrendDataPoint]:
    # metric_column is ALWAYS sourced from METRIC_COLUMN_MAP (server-side
    # allowlist), never from user input — safe to format into the SQL string.
    sql = text(f"""
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
    return gap_fill_chart(list[Any](rows), from_date, to_date)


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
        first_num = cast(float, first_val)
        last_num = cast(float, last_val)
        change = last_num - first_num
        if first_num != 0:
            change_pct = (change / first_num) * 100
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
