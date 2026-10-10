import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from studio.db.enums import JobStatus
from studio.db.session import get_db
from studio.schemas.common import Page
from studio.schemas.jobs import JobDetail, JobRead
from studio.services import jobs as svc

router = APIRouter(prefix="/jobs", tags=["jobs"])
DB = Annotated[Session, Depends(get_db)]


@router.get("", response_model=Page[JobRead])
def list_jobs(
    db: DB,
    status: JobStatus | None = None,
    project_id: uuid.UUID | None = None,
    type: Annotated[str | None, Query(max_length=64)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = svc.list_jobs(db, status=status, project_id=project_id, job_type=type,
                                 limit=limit, offset=offset)
    return Page(items=[JobRead.model_validate(j) for j in items], total=total, limit=limit, offset=offset)


@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: uuid.UUID, db: DB):
    return svc.get_job(db, job_id, with_events=True)


@router.post("/{job_id}/cancel", response_model=JobRead)
def cancel_job(job_id: uuid.UUID, db: DB):
    return svc.cancel(db, job_id)


@router.post("/{job_id}/retry", response_model=JobRead)
def retry_job(job_id: uuid.UUID, db: DB):
    return svc.retry(db, job_id)
