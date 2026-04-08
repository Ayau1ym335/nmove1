from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class MetricValue(BaseModel):
    value: float
    unit: str
    label: str
    status: Literal["normal", "attention", "concern"]
    norm_mean: float | None = None
    norm_sd: float | None = None

class DomainScore(BaseModel):
    domain: str
    score: float
    label: str
    status: Literal["normal", "attention", "concern"]

class ExerciseOut(BaseModel):
    id: UUID
    title: str
    description: str
    difficulty: str
    duration_minutes: int | None = None
    for_metric: str | None = None
    model_config = ConfigDict(from_attributes=True)

class MovementAgeSummary(BaseModel):
    movement_age: int
    bio_age: int | None
    delta: int | None
    delta_vs_last_session: int | None
    composite_score: float | None
    trend: Literal["improving", "stable", "declining"] | None

class IssueOut(BaseModel):
    metric: str
    label: str
    value: float
    severity: Literal["attention", "concern"]

STATUS_LABELS = {
    "normal": {
        "label": "Looking good",
        "description": "Your movement patterns are within healthy ranges for your age group. Keep it up.",
    },
    "attention": {
        "label": "Room to improve",
        "description": "Some movement patterns could use attention. The exercises below will help.",
    },
    "concern": {
        "label": "Action recommended",
        "description": "Several movement patterns are outside healthy ranges. Review the recommendations and consider consulting your doctor.",
    },
    "no_data": {
        "label": "No data yet",
        "description": "Complete your first walking session to see your movement analysis.",
    },
}

class DashboardSummary(BaseModel):
    user_id: UUID
    generated_at: datetime
    cached: bool = False
    cache_ttl_seconds: int | None = None

    # Session info
    latest_session_id: UUID | None
    latest_session_date: datetime | None
    latest_session_status: str | None

    # Movement age
    movement_age: MovementAgeSummary | None

    # Overall status
    overall_status: Literal["normal", "attention", "concern", "no_data"]
    status_label: str
    status_description: str

    # Metric breakdown
    key_metrics: list[MetricValue]

    # Domain scores
    domain_scores: list[DomainScore]

    # Issues detected
    issues: list[IssueOut]

    # Recommendations
    exercises: list[ExerciseOut]

    # Session count
    total_sessions: int
    sessions_this_week: int

    # ML / Anomaly detection
    personal_baseline_available: bool = False
    anomaly_score: float | None = None
    is_anomaly: bool | None = None

    # AI commentary (Gemini)
    gemini_insight: str | None = None
    gemini_insight_audience: Literal["patient", "doctor"] | None = None
