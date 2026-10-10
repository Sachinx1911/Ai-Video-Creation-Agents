"""Safe filesystem path handling. All storage access goes through here."""

import re
import unicodedata
from pathlib import Path, PurePosixPath


class UnsafePathError(ValueError):
    pass


_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_WINDOWS_RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def _ascii_component(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return _SAFE_CHARS.sub("_", text).strip("._ ")


def sanitize_filename(name: str, max_len: int = 120) -> str:
    """Reduce an untrusted filename to a safe single path component.

    The extension is kept separately so non-ASCII names (e.g. Marathi) still
    keep their type: "मराठी.mp3" -> "file.mp3".
    """
    # Drop any directory part, using both separators regardless of OS.
    base = re.split(r"[\\/]", name or "")[-1]
    stem, dot, ext = base.rpartition(".")
    if not dot or not stem.strip("."):
        stem, ext = base, ""
    stem = _ascii_component(stem) or "file"
    ext = _ascii_component(ext)[:16]
    if stem.lower() in _WINDOWS_RESERVED:
        stem = f"_{stem}"
    stem = stem[: max(1, max_len - len(ext) - 1)]
    return f"{stem}.{ext}" if ext else stem


def safe_join(root: Path, relative_key: str) -> Path:
    """Resolve `relative_key` under `root`, refusing anything that escapes it."""
    if not relative_key or "\x00" in relative_key:
        raise UnsafePathError("empty or invalid path")
    key = PurePosixPath(relative_key.replace("\\", "/"))
    if key.is_absolute() or ".." in key.parts or re.match(r"^[A-Za-z]:", relative_key):
        raise UnsafePathError(f"unsafe storage key: {relative_key!r}")
    root_resolved = root.resolve()
    candidate = (root_resolved / Path(*key.parts)).resolve()
    if not candidate.is_relative_to(root_resolved):
        raise UnsafePathError(f"path escapes storage root: {relative_key!r}")
    return candidate
