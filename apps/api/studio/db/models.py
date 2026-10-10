"""ORM models for the Phase 1 foundation schema. See docs/DATABASE_SCHEMA.md."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from studio.db.base import Base, TimestampMixin, str_enum, utcnow
from studio.db.enums import (
    AssetKind,
    AssetOrigin,
    ErrorCategory,
    JobStatus,
    Language,
    Platform,
    ProjectStatus,
    ValidationStatus,
    VideoStyle,
    VisualMethod,
)


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str | None] = mapped_column(String(300))
    language: Mapped[Language] = mapped_column(str_enum(Language, "language"), nullable=False)
    platform: Mapped[Platform] = mapped_column(str_enum(Platform, "platform"), nullable=False)
    target_duration_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    style: Mapped[VideoStyle] = mapped_column(str_enum(VideoStyle, "video_style"), nullable=False)
    visual_method: Mapped[VisualMethod] = mapped_column(
        str_enum(VisualMethod, "visual_method"), nullable=False
    )
    aspect_ratio: Mapped[str] = mapped_column(String(8), nullable=False)
    export_preset: Mapped[str] = mapped_column(String(64), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    fps: Mapped[int] = mapped_column(Integer, nullable=False)
    voiceover_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    captions_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    voice_settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    caption_settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    branding: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    provider_preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    status: Mapped[ProjectStatus] = mapped_column(
        str_enum(ProjectStatus, "project_status"), nullable=False, default=ProjectStatus.DRAFT
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    revisions: Mapped[list["ProjectRevision"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ProjectRevision.revision"
    )
    assets: Mapped[list["Asset"]] = relationship(back_populates="project")

    __table_args__ = (
        CheckConstraint("target_duration_sec BETWEEN 5 AND 180", name="duration_range"),
        CheckConstraint("width > 0 AND height > 0 AND fps BETWEEN 1 AND 120", name="video_dims"),
        Index("ix_projects_archived_updated", "archived_at", "updated_at"),
        Index("ix_projects_status", "status"),
    )


class ProjectRevision(Base):
    __tablename__ = "project_revisions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="revisions")

    __table_args__ = (UniqueConstraint("project_id", "revision", name="uq_project_revision"),)


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = _uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[AssetKind] = mapped_column(str_enum(AssetKind, "asset_kind"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    origin: Mapped[AssetOrigin] = mapped_column(
        str_enum(AssetOrigin, "asset_origin"), nullable=False, default=AssetOrigin.UPLOAD
    )
    license_note: Mapped[str | None] = mapped_column(Text)
    scene_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship(back_populates="assets")
    versions: Mapped[list["AssetVersion"]] = relationship(
        back_populates="asset", order_by="AssetVersion.version"
    )

    __table_args__ = (Index("ix_assets_project_kind", "project_id", "kind"),)


class AssetVersion(Base):
    __tablename__ = "asset_versions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    validation_status: Mapped[ValidationStatus] = mapped_column(
        str_enum(ValidationStatus, "validation_status"),
        nullable=False,
        default=ValidationStatus.PENDING,
    )
    validation_error: Mapped[str | None] = mapped_column(Text)
    media_info: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    asset: Mapped[Asset] = relationship(back_populates="versions")

    __table_args__ = (
        UniqueConstraint("asset_id", "version", name="uq_asset_version"),
        Index("ix_asset_versions_sha256", "sha256"),
    )


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        str_enum(JobStatus, "job_status"), nullable=False, default=JobStatus.QUEUED
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL")
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_category: Mapped[ErrorCategory | None] = mapped_column(
        str_enum(ErrorCategory, "error_category")
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    run_after: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    locked_by: Mapped[str | None] = mapped_column(String(200))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(200), unique=True)
    provider_job_id: Mapped[str | None] = mapped_column(String(200))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    events: Mapped[list["JobEvent"]] = relationship(
        back_populates="job", order_by="JobEvent.id", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("attempts >= 0 AND max_attempts >= 1", name="attempts_range"),
        Index("ix_jobs_claim", "status", "run_after", "priority", "created_at"),
        Index("ix_jobs_project", "project_id"),
        Index("ix_jobs_type", "type"),
    )


class JobEvent(Base):
    __tablename__ = "job_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(32))
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    job: Mapped[Job] = relationship(back_populates="events")

    __table_args__ = (Index("ix_job_events_job", "job_id", "id"),)


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"

    worker_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    hostname: Mapped[str] = mapped_column(String(200), nullable=False)
    pid: Mapped[int] = mapped_column(Integer, nullable=False)
    job_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (Index("ix_audit_entity", "entity_type", "entity_id"),)
