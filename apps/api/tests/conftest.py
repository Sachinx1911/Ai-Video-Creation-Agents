"""Test fixtures.

DB tests run against a REAL PostgreSQL database (TEST_DATABASE_URL, default: the
`studio_test` database on 127.0.0.1:5433). Migrations are applied from scratch at
session start, and every table is truncated between tests. Nothing is mocked.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://studio:studio@127.0.0.1:5433/studio_test"
)
if "studio_test" not in TEST_DB_URL and not os.environ.get("ALLOW_NON_TEST_DB"):
    raise RuntimeError("refusing to run tests against a database not named *studio_test*")


@pytest.fixture(scope="session", autouse=True)
def _env(tmp_path_factory):
    storage = tmp_path_factory.mktemp("storage")
    os.environ["STUDIO_DATABASE_URL"] = TEST_DB_URL
    os.environ["STUDIO_STORAGE_ROOT"] = str(storage)
    os.environ["STUDIO_WORKER_LEASE_SEC"] = "30"
    os.environ["STUDIO_JOB_BACKOFF_BASE_SEC"] = "1"
    from studio.core.config import get_settings
    from studio.db.session import get_engine, get_sessionmaker

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    yield storage


@pytest.fixture(scope="session")
def migrated(_env):
    """Apply migrations from an empty schema (also exercises downgrade)."""
    from alembic import command
    from alembic.config import Config

    from studio.core.config import API_DIR

    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.attributes["url"] = TEST_DB_URL
    try:
        command.downgrade(cfg, "base")
    except Exception:
        pass  # empty database (no alembic_version yet)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    return cfg


@pytest.fixture
def db(migrated):
    from sqlalchemy import text

    from studio.db.base import Base
    from studio.db.session import get_sessionmaker

    sf = get_sessionmaker()
    with sf() as s:
        names = ", ".join(t.name for t in Base.metadata.sorted_tables)
        s.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
        s.commit()
    with sf() as s:
        yield s


@pytest.fixture
def client(db):
    from fastapi.testclient import TestClient

    from studio.main import create_app

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def worker(db):
    from studio.workers.runner import Worker

    return Worker(worker_id="test-worker")


# ------------------------------------------------------------- synthetic media

FFMPEG = shutil.which("ffmpeg")
requires_ffmpeg = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg not on PATH")


def _ffmpeg(*args: str) -> None:
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


@pytest.fixture(scope="session")
def media_dir(tmp_path_factory) -> Path:
    """Small synthetic media generated locally with FFmpeg (no copyrighted content)."""
    if FFMPEG is None:
        pytest.skip("ffmpeg not on PATH")
    d = tmp_path_factory.mktemp("media")
    _ffmpeg("-f", "lavfi", "-i", "testsrc=size=270x480:rate=30:duration=2",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(d / "clip.mp4"))
    _ffmpeg("-f", "lavfi", "-i", "testsrc=size=540x960", "-frames:v", "1", str(d / "frame.png"))
    _ffmpeg("-f", "lavfi", "-i", "sine=frequency=220:duration=1.5", str(d / "voice.wav"))
    (d / "broken.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42" + os.urandom(2048))
    (d / "subs.srt").write_text("1\n00:00:00,000 --> 00:00:01,500\nनमस्कार\n", encoding="utf-8")
    return d
