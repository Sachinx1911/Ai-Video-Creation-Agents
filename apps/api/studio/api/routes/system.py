from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from studio.core.presets import DEFAULT_PRESET_BY_PLATFORM, EXPORT_PRESETS
from studio.db.enums import (
    AssetKind,
    JobStatus,
    Language,
    Platform,
    ProjectStatus,
    VideoStyle,
    VisualMethod,
)
from studio.db.session import get_db
from studio.media.validation import ALLOWED_EXTENSIONS
from studio.services import health

router = APIRouter(tags=["system"])
DB = Annotated[Session, Depends(get_db)]


@router.get("/health")
def liveness():
    """Process is up. Does not touch dependencies."""
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: DB):
    result = health.readiness(db)
    return JSONResponse(result, status_code=200 if result["ready"] else 503)


@router.get("/system/overview")
def overview(db: DB):
    return health.overview(db)


@router.get("/meta/options")
def options():
    """Enum values and presets for building forms (single source of truth)."""
    return {
        "languages": [{"value": v.value, "label": {"mr": "Marathi", "hi": "Hindi", "en": "English"}[v.value]}
                      for v in Language],
        "platforms": [p.value for p in Platform],
        "styles": [s.value for s in VideoStyle],
        "visual_methods": [m.value for m in VisualMethod],
        "project_statuses": [s.value for s in ProjectStatus],
        "job_statuses": [s.value for s in JobStatus],
        "asset_kinds": [k.value for k in AssetKind],
        "asset_extensions": {k.value: sorted(v) for k, v in ALLOWED_EXTENSIONS.items()},
        "export_presets": [p.to_dict() for p in EXPORT_PRESETS.values()],
        "default_preset_by_platform": {k.value: v for k, v in DEFAULT_PRESET_BY_PLATFORM.items()},
    }
