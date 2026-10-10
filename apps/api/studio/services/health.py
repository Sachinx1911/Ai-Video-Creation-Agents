"""Readiness checks and system overview. Every value comes from a real probe/query."""

from datetime import timedelta
from functools import lru_cache
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from studio.core.config import API_DIR, get_settings
from studio.db.base import utcnow
from studio.db.enums import JobStatus, ValidationStatus
from studio.db.models import Asset, AssetVersion, AuditLog, Job, Project, WorkerHeartbeat
from studio.media.probe import tool_version
from studio.services import storage


@lru_cache
def _migration_head() -> str | None:
    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_DIR / "migrations"))
    return ScriptDirectory.from_config(cfg).get_current_head()


def _tool_versions() -> dict[str, str | None]:
    s = get_settings()
    return {"ffmpeg": tool_version(s.ffmpeg_bin), "ffprobe": tool_version(s.ffprobe_bin)}


def _check(ok: bool, detail: Any, severity: str = "error") -> dict[str, Any]:
    return {"ok": ok, "detail": detail, "severity": "ok" if ok else severity}


def readiness(session: Session) -> dict[str, Any]:
    s = get_settings()
    checks: dict[str, dict[str, Any]] = {}

    try:
        session.execute(text("SELECT 1"))
        checks["database"] = _check(True, "connected")
        current = session.execute(text("SELECT version_num FROM alembic_version")).scalar()
        head = _migration_head()
        checks["migrations"] = _check(
            current == head, {"current": current, "head": head}
        )
    except Exception as e:  # report, do not crash the health endpoint
        session.rollback()
        checks["database"] = _check(False, f"{type(e).__name__}: {str(e)[:200]}")
        checks["migrations"] = _check(False, "database unavailable")

    versions = _tool_versions()
    for tool, v in versions.items():
        checks[tool] = _check(v is not None, v or f"{tool} not found or not executable")

    try:
        root = storage.root()
        probe_file = root / ".write-test"
        probe_file.write_text("ok")
        probe_file.unlink()
        usage = storage.disk_usage()
        free_gb = round(usage.free / 1024**3, 2)
        checks["storage"] = _check(True, {"root": str(root), "free_gb": free_gb,
                                          "total_gb": round(usage.total / 1024**3, 2)})
        checks["disk_space"] = _check(free_gb >= s.min_free_disk_gb,
                                      {"free_gb": free_gb, "min_free_gb": s.min_free_disk_gb},
                                      severity="warning")
    except OSError as e:
        checks["storage"] = _check(False, f"storage not writable: {e}")

    if checks["database"]["ok"]:
        cutoff = utcnow() - timedelta(seconds=s.worker_heartbeat_stale_sec)
        workers = session.scalars(
            select(WorkerHeartbeat).where(WorkerHeartbeat.last_seen_at >= cutoff)
        ).all()
        checks["worker"] = _check(
            bool(workers),
            [{"worker_id": w.worker_id, "job_types": w.job_types,
              "last_seen_at": w.last_seen_at.isoformat()} for w in workers]
            or "no worker heartbeat in the last "
               f"{s.worker_heartbeat_stale_sec}s - queued jobs will not run",
        )

    ready = all(c["ok"] for c in checks.values() if c["severity"] != "warning")
    return {"ready": ready, "checks": checks}


def overview(session: Session) -> dict[str, Any]:
    jobs_by_status = dict(
        session.execute(select(Job.status, func.count()).group_by(Job.status)).all()
    )
    active_projects = session.scalar(
        select(func.count()).select_from(Project).where(Project.archived_at.is_(None))
    ) or 0
    archived_projects = session.scalar(
        select(func.count()).select_from(Project).where(Project.archived_at.is_not(None))
    ) or 0
    asset_count = session.scalar(
        select(func.count()).select_from(Asset).where(Asset.archived_at.is_(None))
    ) or 0
    invalid_versions = session.scalar(
        select(func.count()).select_from(AssetVersion)
        .where(AssetVersion.validation_status == ValidationStatus.INVALID)
    ) or 0
    storage_bytes = session.scalar(select(func.coalesce(func.sum(AssetVersion.size_bytes), 0))) or 0
    recent = session.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(15)).all()
    return {
        "projects": {"active": active_projects, "archived": archived_projects},
        "assets": {"active": asset_count, "invalid_versions": invalid_versions,
                   "stored_bytes": int(storage_bytes)},
        "jobs": {st.value: int(jobs_by_status.get(st, 0)) for st in JobStatus},
        "recent_activity": [
            {"id": a.id, "entity_type": a.entity_type, "entity_id": a.entity_id,
             "action": a.action, "details": a.details, "created_at": a.created_at.isoformat()}
            for a in recent
        ],
    }
