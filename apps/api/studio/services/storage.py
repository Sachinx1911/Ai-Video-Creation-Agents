"""Local filesystem storage. Keys are POSIX-style paths relative to STORAGE_ROOT."""

import hashlib
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from studio.core.config import get_settings
from studio.core.errors import PayloadTooLarge
from studio.core.paths import safe_join

CHUNK = 1024 * 1024


@dataclass
class StoredTemp:
    path: Path
    size_bytes: int
    sha256: str


def root() -> Path:
    r = get_settings().storage_root
    r.mkdir(parents=True, exist_ok=True)
    return r


def resolve(key: str) -> Path:
    return safe_join(root(), key)


def write_temp(src: BinaryIO, max_bytes: int) -> StoredTemp:
    """Stream an upload into a temp file, hashing and enforcing the size limit."""
    tmp_dir = resolve("tmp/uploads")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp = tmp_dir / f"{uuid.uuid4().hex}.part"
    digest = hashlib.sha256()
    size = 0
    try:
        with tmp.open("wb") as out:
            while chunk := src.read(CHUNK):
                size += len(chunk)
                if size > max_bytes:
                    raise PayloadTooLarge(f"file exceeds {max_bytes // (1024 * 1024)} MB limit")
                digest.update(chunk)
                out.write(chunk)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return StoredTemp(tmp, size, digest.hexdigest())


def promote(temp: StoredTemp, key: str) -> Path:
    dest = resolve(key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.replace(temp.path, dest)
    return dest


def remove(key: str) -> None:
    """Best-effort removal used only to roll back a failed registration."""
    resolve(key).unlink(missing_ok=True)


def disk_usage() -> shutil._ntuple_diskusage:  # type: ignore[name-defined]
    return shutil.disk_usage(root())
