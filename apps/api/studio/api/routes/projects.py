import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from studio.db.enums import ProjectStatus
from studio.db.session import get_db
from studio.schemas.common import Page
from studio.schemas.projects import (
    ProjectCreate,
    ProjectDuplicate,
    ProjectRead,
    ProjectRevisionRead,
    ProjectSummary,
    ProjectUpdate,
)
from studio.services import projects as svc

router = APIRouter(prefix="/projects", tags=["projects"])
DB = Annotated[Session, Depends(get_db)]


@router.get("", response_model=Page[ProjectSummary])
def list_projects(
    db: DB,
    archived: bool = False,
    status_: Annotated[ProjectStatus | None, Query(alias="status")] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = svc.list_projects(db, archived=archived, status=status_, q=q, limit=limit, offset=offset)
    return Page(items=[ProjectSummary.model_validate(p) for p in items], total=total, limit=limit, offset=offset)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(body: ProjectCreate, db: DB):
    return svc.create_project(db, body)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: uuid.UUID, db: DB):
    return svc.get_project(db, project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: uuid.UUID, body: ProjectUpdate, db: DB):
    return svc.update_project(db, project_id, body)


@router.post("/{project_id}/duplicate", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def duplicate_project(project_id: uuid.UUID, body: ProjectDuplicate, db: DB):
    return svc.duplicate_project(db, project_id, body.name)


@router.post("/{project_id}/archive", response_model=ProjectRead)
def archive_project(project_id: uuid.UUID, db: DB):
    return svc.set_archived(db, project_id, True)


@router.post("/{project_id}/restore", response_model=ProjectRead)
def restore_project(project_id: uuid.UUID, db: DB):
    return svc.set_archived(db, project_id, False)


@router.get("/{project_id}/revisions", response_model=list[ProjectRevisionRead])
def list_revisions(project_id: uuid.UUID, db: DB):
    return svc.list_revisions(db, project_id)
