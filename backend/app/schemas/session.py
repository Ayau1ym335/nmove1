from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

class SessionStatusEnum(str, Enum):
    ingested = "ingested"
    processing = "processing"
    done = "done"
    error = "error"

class PatchSessionStatusRequest(BaseModel):
    status: SessionStatusEnum
    error_message: Optional[str] = Field(None, max_length=1000)

    @model_validator(mode="after")
    def validate_status_transition(self) -> "PatchSessionStatusRequest":
        if self.status == SessionStatusEnum.error and not self.error_message:
            raise ValueError("error_message is required when status is error")
        return self

class MetricsSnapshotOut(BaseModel):
    id: UUID
    cadence: float
    symmetry_score: float
    stability_score: float
    movement_age: float | None = None
    bio_age: int | None = None
    movement_age_delta: float | None = None
    interpretation_status: str
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SessionSummary(BaseModel):
    id: UUID
    user_id: UUID
    doctor_id: UUID | None = None
    device_id: str | None = None
    leg_side: str | None = None
    status: SessionStatusEnum
    status_updated_at: datetime | None = None
    started_at: datetime
    ended_at: datetime | None = None
    duration_seconds: float | None = None
    reading_count: int | None = None
    task_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SessionDetail(SessionSummary):
    error_message: str | None = None
    metrics_snapshots: list[MetricsSnapshotOut] = []
    notes: str | None = None

class PatientSessionListResponse(BaseModel):
    patient_id: UUID
    sessions: list[SessionSummary]
    total: int
    page: int
    page_size: int
    has_more: bool

class SessionStatusUpdateResponse(BaseModel):
    session_id: UUID
    previous_status: SessionStatusEnum
    new_status: SessionStatusEnum
    updated_at: datetime | None
    message: str
