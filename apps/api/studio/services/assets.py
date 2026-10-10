"""Asset registry: files on disk, metadata + provenance in PostgreSQL."""

import uuid
from typing import BinaryIO

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from studio.core.config import get_settings
from studio.core.errors import ConflictError, NotFoundError, ValidationFailed
from studio.core.paths import sanitize_filename
from studio.db.base import utcnow
from studio.db.enums import AssetKind, AssetOrigin
from studio.db.models import Asset, AssetVersion
from studio.media.validation import mime_for
from studio.services import audit, jobs, storage
from studio.services.projects import get_project

PROBE_JOB = "asset.probe"
# Third-party audio must carry its licence / source (REQ-012).
LICENSE_REQUIRED = frozenset({AssetKind.MUSIC, AssetKind.SFX})


def _storage_key(project_id: uuid.UUID, asset_id: uuid.UUID, version: int, filename: str) -> str:
    return f"projects/{project_id}/assets/{asset_id}/v{version}/{filename}"


def _store_version(
    session: Session,
    asset: Asset,
    version: int,
    fileobj: BinaryIO,
    original_filename: str,
    provenance: dict,
) -> AssetVersion:
    """Write the file, register the version and enqueue validation (single commit).

    On any failure the transaction is rolled back and a promoted file is removed.
    """
    key: str | None = None
    try:
        filename = sanitize_filename(original_filename)
        mime = mime_for(AssetKind(asset.kind), filename)
        if mime is None:
            ext = filename.rpartition(".")[2] if "." in filename else "(none)"
            raise ValidationFailed(f"file type {ext!r} is not allowed for kind {asset.kind}")
        temp = storage.write_temp(fileobj, get_settings().max_upload_bytes)
        if temp.size_bytes == 0:
            temp.path.unlink(missing_ok=True)
            raise ValidationFailed("file is empty")
        key = _storage_key(asset.project_id, asset.id, version, filename)
        storage.promote(temp, key)
        av = AssetVersion(
            id=uuid.uuid4(),
            asset_id=asset.id,
            version=version,
            storage_key=key,
            original_filename=original_filename[:255],
            mime_type=mime,
            size_bytes=temp.size_bytes,
            sha256=temp.sha256,
            provenance=provenance,
        )
        session.add(av)
        session.flush()
        jobs.enqueue(
            session,
            PROBE_JOB,
            {"asset_version_id": str(av.id)},
            project_id=asset.project_id,
            idempotency_key=f"{PROBE_JOB}:{av.id}",
            priority=50,
        )
        session.commit()
    except BaseException:
        session.rollback()
        if key:
            storage.remove(key)
        raise
    return av


def upload_asset(
    session: Session,
    project_id: uuid.UUID,
    kind: AssetKind,
    fileobj: BinaryIO,
    original_filename: str,
    name: str | None = None,
    license_note: str | None = None,
) -> Asset:
    project = get_project(session, project_id)
    if project.archived_at is not None:
        raise ConflictError("cannot add assets to an archived project")
    if kind in LICENSE_REQUIRED and not (license_note or "").strip():
        raise ValidationFailed(f"{kind.value} assets require a license / source note")
    asset = Asset(
        id=uuid.uuid4(),
        project_id=project_id,
        kind=kind,
        name=(name or original_filename or "asset")[:200],
        origin=AssetOrigin.UPLOAD,
        license_note=license_note,
        current_version=1,
    )
    session.add(asset)
    session.flush()
    audit.record(session, "asset", asset.id, "upload", {"project_id": str(project_id), "kind": kind.value})
    _store_version(session, asset, 1, fileobj, original_filename, {"source": "user_upload"})
    return get_asset(session, asset.id)


def add_version(
    session: Session, asset_id: uuid.UUID, fileobj: BinaryIO, original_filename: str
) -> Asset:
    asset = session.scalars(select(Asset).where(Asset.id == asset_id).with_for_update()).one_or_none()
    if asset is None:
        raise NotFoundError(f"asset {asset_id} not found")
    if asset.archived_at is not None:
        raise ConflictError("asset is archived")
    asset.current_version += 1
    asset.updated_at = utcnow()
    audit.record(session, "asset", asset.id, "new_version", {"version": asset.current_version})
    _store_version(session, asset, asset.current_version, fileobj, original_filename,
                   {"source": "user_upload"})
    return get_asset(session, asset_id)


def get_asset(session: Session, asset_id: uuid.UUID) -> Asset:
    asset = session.scalars(
        select(Asset).where(Asset.id == asset_id).options(selectinload(Asset.versions))
    ).one_or_none()
    if asset is None:
        raise NotFoundError(f"asset {asset_id} not found")
    return asset


def get_version(session: Session, asset_id: uuid.UUID, version: int) -> AssetVersion:
    av = session.scalars(
        select(AssetVersion).where(AssetVersion.asset_id == asset_id, AssetVersion.version == version)
    ).one_or_none()
    if av is None:
        raise NotFoundError(f"asset {asset_id} version {version} not found")
    return av


def list_assets(
    session: Session,
    *,
    project_id: uuid.UUID | None = None,
    kind: AssetKind | None = None,
    q: str | None = None,
    include_archived: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[Asset], int]:
    stmt = select(Asset)
    if project_id:
        stmt = stmt.where(Asset.project_id == project_id)
    if kind:
        stmt = stmt.where(Asset.kind == kind)
    if q:
        like = f"%{q.replace('%', r'\%').replace('_', r'\_')}%"
        stmt = stmt.where(Asset.name.ilike(like))
    if not include_archived:
        stmt = stmt.where(Asset.archived_at.is_(None))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.scalars(
        stmt.options(selectinload(Asset.versions))
        .order_by(Asset.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(rows), total


def set_archived(session: Session, asset_id: uuid.UUID, archived: bool) -> Asset:
    """Soft archive only; files are never deleted by this call (REQ-003)."""
    asset = get_asset(session, asset_id)
    asset.archived_at = utcnow() if archived else None
    audit.record(session, "asset", asset.id, "archive" if archived else "restore")
    session.commit()
    return asset


def latest_version(asset: Asset) -> AssetVersion | None:
    return next((v for v in asset.versions if v.version == asset.current_version), None)
