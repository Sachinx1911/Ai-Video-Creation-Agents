import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from studio.core.errors import NotFoundError
from studio.db.enums import AssetKind
from studio.db.models import Asset
from studio.db.session import get_db
from studio.schemas.assets import AssetDetail, AssetRead, AssetVersionRead
from studio.schemas.common import Page
from studio.services import assets as svc
from studio.services import storage

router = APIRouter(tags=["assets"])
DB = Annotated[Session, Depends(get_db)]


def _read(asset: Asset) -> AssetRead:
    out = AssetRead.model_validate(asset)
    latest = svc.latest_version(asset)
    out.latest = AssetVersionRead.model_validate(latest) if latest else None
    return out


def _detail(asset: Asset) -> AssetDetail:
    base = _read(asset)
    return AssetDetail(**base.model_dump(), versions=[AssetVersionRead.model_validate(v) for v in asset.versions])


@router.get("/assets", response_model=Page[AssetRead])
def list_assets(
    db: DB,
    project_id: uuid.UUID | None = None,
    kind: AssetKind | None = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    include_archived: bool = False,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = svc.list_assets(
        db, project_id=project_id, kind=kind, q=q, include_archived=include_archived,
        limit=limit, offset=offset,
    )
    return Page(items=[_read(a) for a in items], total=total, limit=limit, offset=offset)


@router.post("/projects/{project_id}/assets", response_model=AssetDetail, status_code=status.HTTP_201_CREATED)
def upload_asset(
    project_id: uuid.UUID,
    db: DB,
    file: Annotated[UploadFile, File()],
    kind: Annotated[AssetKind, Form()],
    name: Annotated[str | None, Form(max_length=200)] = None,
    license_note: Annotated[str | None, Form(max_length=2000)] = None,
):
    asset = svc.upload_asset(
        db, project_id, kind, file.file, file.filename or "upload", name or None, license_note or None
    )
    return _detail(asset)


@router.get("/assets/{asset_id}", response_model=AssetDetail)
def get_asset(asset_id: uuid.UUID, db: DB):
    return _detail(svc.get_asset(db, asset_id))


@router.post("/assets/{asset_id}/versions", response_model=AssetDetail, status_code=status.HTTP_201_CREATED)
def add_version(asset_id: uuid.UUID, db: DB, file: Annotated[UploadFile, File()]):
    return _detail(svc.add_version(db, asset_id, file.file, file.filename or "upload"))


@router.post("/assets/{asset_id}/archive", response_model=AssetDetail)
def archive_asset(asset_id: uuid.UUID, db: DB):
    return _detail(svc.set_archived(db, asset_id, True))


@router.post("/assets/{asset_id}/restore", response_model=AssetDetail)
def restore_asset(asset_id: uuid.UUID, db: DB):
    return _detail(svc.set_archived(db, asset_id, False))


@router.get("/assets/{asset_id}/versions/{version}/file")
def asset_file(
    asset_id: uuid.UUID,
    version: Annotated[int, Path(ge=1)],
    db: DB,
    download: bool = False,
):
    av = svc.get_version(db, asset_id, version)
    path = storage.resolve(av.storage_key)
    if not path.is_file():
        raise NotFoundError("file is missing from storage")
    return FileResponse(
        path,
        media_type=av.mime_type,
        filename=path.name,
        content_disposition_type="attachment" if download else "inline",
        headers={"X-Content-Type-Options": "nosniff"},
    )
