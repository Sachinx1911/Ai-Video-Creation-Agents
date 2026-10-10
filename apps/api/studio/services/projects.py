import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from studio.core.errors import ConflictError, NotFoundError, ValidationFailed
from studio.core.presets import DEFAULT_PRESET_BY_PLATFORM, EXPORT_PRESETS
from studio.db.base import utcnow
from studio.db.enums import Platform, ProjectStatus
from studio.db.models import Project, ProjectRevision
from studio.schemas.projects import ProjectCreate, ProjectUpdate
from studio.services import audit

# Fields copied by duplicate() and captured in revision snapshots.
SETTINGS_FIELDS = (
    "name", "description", "topic", "target_audience", "language", "platform",
    "target_duration_sec", "style", "visual_method", "aspect_ratio", "export_preset",
    "width", "height", "fps", "voiceover_enabled", "captions_enabled", "voice_settings",
    "caption_settings", "branding", "provider_preferences",
)
_JSON_FIELDS = {"voice_settings", "caption_settings", "branding", "provider_preferences"}


def _snapshot(project: Project) -> dict[str, Any]:
    snap: dict[str, Any] = {}
    for f in SETTINGS_FIELDS:
        v = getattr(project, f)
        snap[f] = v.value if hasattr(v, "value") else v
    return snap


def _apply_preset(project: Project, preset_key: str | None, platform: Platform, fps: int | None) -> None:
    key = preset_key or DEFAULT_PRESET_BY_PLATFORM[platform]
    preset = EXPORT_PRESETS.get(key)
    if preset is None:
        raise ValidationFailed(
            f"unknown export_preset {key!r}; valid: {sorted(EXPORT_PRESETS)}"
        )
    project.export_preset = preset.key
    project.aspect_ratio = preset.aspect_ratio
    project.width = preset.width
    project.height = preset.height
    project.fps = fps or preset.fps


def _add_revision(session: Session, project: Project, summary: str) -> None:
    session.add(
        ProjectRevision(
            project_id=project.id,
            revision=project.current_revision,
            snapshot=_snapshot(project),
            change_summary=summary,
        )
    )


def create_project(session: Session, data: ProjectCreate) -> Project:
    fields = data.model_dump(exclude={"export_preset", "fps"}, mode="json")
    project = Project(id=uuid.uuid4(), status=ProjectStatus.DRAFT, current_revision=1, **fields)
    _apply_preset(project, data.export_preset, data.platform, data.fps)
    session.add(project)
    session.flush()
    _add_revision(session, project, "created")
    audit.record(session, "project", project.id, "create", {"name": project.name})
    session.commit()
    return project


def get_project(session: Session, project_id: uuid.UUID) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise NotFoundError(f"project {project_id} not found")
    return project


def list_projects(
    session: Session,
    *,
    archived: bool = False,
    status: ProjectStatus | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Project], int]:
    stmt = select(Project).where(
        Project.archived_at.is_not(None) if archived else Project.archived_at.is_(None)
    )
    if status:
        stmt = stmt.where(Project.status == status)
    if q:
        like = f"%{q.replace('%', r'\%').replace('_', r'\_')}%"
        stmt = stmt.where(or_(Project.name.ilike(like), Project.topic.ilike(like)))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.scalars(stmt.order_by(Project.updated_at.desc()).limit(limit).offset(offset)).all()
    return list(rows), total


def update_project(session: Session, project_id: uuid.UUID, data: ProjectUpdate) -> Project:
    project = session.scalars(
        select(Project).where(Project.id == project_id).with_for_update()
    ).one_or_none()
    if project is None:
        raise NotFoundError(f"project {project_id} not found")
    if project.archived_at is not None:
        raise ConflictError("archived projects are read-only; restore it first")

    changes = data.model_dump(exclude_unset=True, mode="json")
    summary = changes.pop("change_summary", None)
    preset_key = changes.pop("export_preset", None)
    fps = changes.pop("fps", None)

    before = _snapshot(project)
    for field, value in changes.items():
        setattr(project, field, value)
    if preset_key is not None or fps is not None:
        # A new preset resets fps to the preset default unless fps is also given.
        keep_fps = project.fps if preset_key is None else None
        _apply_preset(project, preset_key or project.export_preset, project.platform, fps or keep_fps)

    after = _snapshot(project)
    changed = sorted(k for k in after if after[k] != before[k])
    if not changed:
        session.rollback()
        return get_project(session, project_id)

    project.current_revision += 1
    project.updated_at = utcnow()
    _add_revision(session, project, summary or f"updated: {', '.join(changed)}")
    audit.record(session, "project", project.id, "update", {"fields": changed})
    session.commit()
    return project


def duplicate_project(session: Session, project_id: uuid.UUID, name: str | None) -> Project:
    src = get_project(session, project_id)
    copy = Project(id=uuid.uuid4(), status=ProjectStatus.DRAFT, current_revision=1)
    for f in SETTINGS_FIELDS:
        v = getattr(src, f)
        setattr(copy, f, dict(v) if f in _JSON_FIELDS else v)
    copy.name = name or f"{src.name} (copy)"[:200]
    session.add(copy)
    session.flush()
    _add_revision(session, copy, f"duplicated from {src.id}")
    audit.record(session, "project", copy.id, "duplicate", {"source_project_id": str(src.id)})
    session.commit()
    return copy


def set_archived(session: Session, project_id: uuid.UUID, archived: bool) -> Project:
    project = get_project(session, project_id)
    if archived and project.archived_at is None:
        project.archived_at = utcnow()
        audit.record(session, "project", project.id, "archive")
    elif not archived and project.archived_at is not None:
        project.archived_at = None
        audit.record(session, "project", project.id, "restore")
    session.commit()
    return project


def list_revisions(session: Session, project_id: uuid.UUID) -> list[ProjectRevision]:
    get_project(session, project_id)
    return list(
        session.scalars(
            select(ProjectRevision)
            .where(ProjectRevision.project_id == project_id)
            .order_by(ProjectRevision.revision.desc())
        )
    )
