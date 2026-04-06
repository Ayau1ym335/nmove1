from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel

class ReportRequest(BaseModel):
    days:           Literal[7, 30, 90] = 30
    include_charts: bool = True

class ReportTaskResponse(BaseModel):
    task_id:    str
    patient_id: UUID
    status:     str = "queued"
    message:    str = "Report generation started. Poll task_id for completion."
    estimated_seconds: int = 30

class ReportStatusResponse(BaseModel):
    task_id:     str
    status:      Literal["queued", "processing", "done", "failed"]
    url:         str | None         # presigned MinIO URL when done
    expires_at:  datetime | None    # when URL expires
    error:       str | None

class ReportListItem(BaseModel):
    object_name:  str
    generated_at: datetime
    size_bytes:   int
    url:          str               # fresh presigned URL
    expires_at:   datetime
    days_window:  int | None
