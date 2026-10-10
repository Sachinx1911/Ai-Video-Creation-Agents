"""`asset.probe`: validate an uploaded asset version with FFprobe / header checks."""

import uuid
from typing import Any

from studio.core.config import get_settings
from studio.core.paths import UnsafePathError
from studio.db.enums import ErrorCategory, ValidationStatus
from studio.db.models import AssetVersion
from studio.media import probe as ffprobe
from studio.media.validation import check_font, check_probe, media_family
from studio.services import storage
from studio.services.assets import PROBE_JOB
from studio.workers.base import JobContext, JobError, register


def _validate(av: AssetVersion) -> tuple[ValidationStatus, str | None, dict[str, Any]]:
    try:
        path = storage.resolve(av.storage_key)
    except UnsafePathError as e:
        return ValidationStatus.INVALID, str(e), {}
    if not path.is_file():
        return ValidationStatus.INVALID, "file is missing from storage", {}
    if path.stat().st_size != av.size_bytes:
        return ValidationStatus.INVALID, "file size differs from registered size", {}

    family = media_family(av.storage_key)
    if family == "font":
        err = check_font(path)
        return (ValidationStatus.INVALID if err else ValidationStatus.VALID), err, {"family": family}

    s = get_settings()
    try:
        info = ffprobe.probe(path, s.ffprobe_bin, s.ffprobe_timeout_sec)
    except ffprobe.ProbeUnavailable as e:
        # Environment problem, not a bad file: let the queue retry.
        raise JobError(ErrorCategory.TRANSIENT, str(e)) from e
    except ffprobe.ProbeError as e:
        return ValidationStatus.INVALID, f"unreadable media: {e}", {"family": family}

    media = {"family": family, **info.to_dict()}
    err = check_probe(family, info)
    return (ValidationStatus.INVALID if err else ValidationStatus.VALID), err, media


@register(PROBE_JOB)
def handle(ctx: JobContext) -> dict[str, Any]:
    try:
        av_id = uuid.UUID(str(ctx.payload["asset_version_id"]))
    except (KeyError, ValueError) as e:
        raise JobError(ErrorCategory.INVALID_REQUEST, f"bad payload: {e}") from e

    with ctx.session_factory() as session:
        av = session.get(AssetVersion, av_id)
        if av is None:
            raise JobError(ErrorCategory.INVALID_REQUEST, f"asset version {av_id} not found")
        ctx.check_cancelled()
        status, error, media = _validate(av)
        av.validation_status = status
        av.validation_error = error
        av.media_info = media
        session.commit()
        return {"asset_version_id": str(av_id), "validation_status": status.value, "error": error}
