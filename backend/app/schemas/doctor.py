from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field

class PatientSummary(BaseModel):
    user_id: UUID
    full_name: str | None
    email: str
    bio_age: int | None

    latest_session_id: UUID | None
    last_seen: datetime | None
    session_status: str | None

    movement_age: int | None
    movement_age_delta: float | None
    overall_status: str | None
    symmetry_score: float | None
    stability_score: float | None
    cadence: float | None

    alert: bool
    days_since_last_session: int | None

class PatientListFilters(BaseModel):
    status: Literal["normal", "attention", "concern"] | None = None
    sort: Literal["last_seen", "movement_age", "movement_age_delta", "name"] = "last_seen"
    order: Literal["asc", "desc"] = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    search: str | None = None

class PatientListResponse(BaseModel):
    doctor_id: UUID
    patients: list[PatientSummary]
    total: int
    page: int
    page_size: int
    has_more: bool
    cached: bool = False

    total_concern: int
    total_attention: int
    total_normal: int
    total_no_data: int

class SessionRow(BaseModel):
    session_id: UUID
    started_at: datetime
    ended_at:   datetime | None
    duration_seconds: float | None
    status:     str
    device_id:  str | None

    movement_age:           int | None
    movement_age_delta:     float | None
    interpretation_status:  str | None
    symmetry_score:         float | None
    stability_score:        float | None
    cadence:                float | None

    status_badge: Literal["normal", "attention", "concern", "no_data"]

class SessionHistory(BaseModel):
    sessions:   list[SessionRow]
    total:      int
    page:       int
    page_size:  int
    has_more:   bool

from datetime import date

class ChartPoint(BaseModel):
    date:          date
    value:         float | None
    session_count: int = 0

class MetricChart(BaseModel):
    metric:    str
    label:     str
    unit:      str
    points:    list[ChartPoint]
    first:     float | None
    last:      float | None
    best:      float | None
    worst:     float | None
    trend:     Literal["improving", "stable", "declining"] | None

class ExerciseAdherenceRow(BaseModel):
    title:             str
    difficulty:        str
    for_metric:        str | None
    times_prescribed:  int
    last_prescribed:   datetime | None

class ExerciseAdherence(BaseModel):
    exercises:        list[ExerciseAdherenceRow]
    total_prescribed: int
    unique_exercises: int
    most_common:      str | None

class MovementAgeSummaryDetail(BaseModel):
    current_movement_age:  int | None
    bio_age:               int | None
    current_delta:         int | None
    best_movement_age:     int | None
    worst_movement_age:    int | None
    first_movement_age:    int | None
    sessions_analyzed:     int
    overall_trend:         Literal["improving", "stable", "declining"] | None

class PatientDetail(BaseModel):
    patient_id:   UUID
    full_name:    str | None
    email:        str
    bio_age:      int | None

    doctor_id:    UUID
    first_assigned:  datetime | None

    movement_age_summary: MovementAgeSummaryDetail
    charts: dict[str, MetricChart]
    trend_days: int

    session_history: SessionHistory
    exercise_adherence: ExerciseAdherence

    has_concern_sessions: bool
    sessions_this_week:   int
    last_seen:            datetime | None
    total_sessions:       int

    cached: bool = False

