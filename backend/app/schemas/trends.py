from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field

class TrendDataPoint(BaseModel):
    date: date
    value: float | None
    session_count: int

class MetricTrendSeries(BaseModel):
    metric: str
    label: str
    unit: str
    data: list[TrendDataPoint]
    first_value: float | None
    last_value: float | None
    change: float | None
    change_pct: float | None
    trend_direction: Literal["improving", "stable", "declining"] | None
    peak: float | None
    trough: float | None

class TrendsResponse(BaseModel):
    user_id: UUID
    days: int
    from_date: date
    to_date: date
    series: list[MetricTrendSeries]
    total_sessions_in_window: int
    cached: bool = False
