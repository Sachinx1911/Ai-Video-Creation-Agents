import uuid
from datetime import datetime
from typing import Any

from studio.db.enums import ErrorCategory, JobStatus
from studio.schemas.common import ORMModel


class JobEventRead(ORMModel):
    id: int
    from_status: str | None
    to_status: str
    message: str | None
    data: dict[str, Any]
    created_at: datetime


class JobRead(ORMModel):
    id: uuid.UUID
    type: str
    status: JobStatus
    project_id: uuid.UUID | None
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error_category: ErrorCategory | None
    error_message: str | None
    attempts: int
    max_attempts: int
    priority: int
    run_after: datetime
    locked_by: str | None
    lease_expires_at: datetime | None
    cancel_requested: bool
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    updated_at: datetime


class JobDetail(JobRead):
    events: list[JobEventRead]
