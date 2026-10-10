import uuid
from datetime import datetime
from typing import Any

from studio.db.enums import AssetKind, AssetOrigin, ValidationStatus
from studio.schemas.common import ORMModel


class AssetVersionRead(ORMModel):
    id: uuid.UUID
    version: int
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    validation_status: ValidationStatus
    validation_error: str | None
    media_info: dict[str, Any]
    provenance: dict[str, Any]
    created_at: datetime


class AssetRead(ORMModel):
    id: uuid.UUID
    project_id: uuid.UUID
    kind: AssetKind
    name: str
    origin: AssetOrigin
    license_note: str | None
    scene_id: uuid.UUID | None
    current_version: int
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    latest: AssetVersionRead | None = None


class AssetDetail(AssetRead):
    versions: list[AssetVersionRead]
