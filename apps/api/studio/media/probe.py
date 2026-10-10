"""FFprobe wrapper. Arguments are built as a list; never via a shell."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ProbeError(Exception):
    """FFprobe could not read the file (corrupt / unsupported)."""


class ProbeUnavailable(Exception):
    """FFprobe binary missing or timed out (environment problem, retryable)."""


@dataclass
class StreamInfo:
    index: int
    codec_type: str
    codec_name: str | None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    sample_rate: int | None = None
    channels: int | None = None
    duration_sec: float | None = None


@dataclass
class MediaInfo:
    format_name: str | None
    duration_sec: float | None
    size_bytes: int | None
    bit_rate: int | None
    streams: list[StreamInfo]

    def first(self, codec_type: str) -> StreamInfo | None:
        return next((s for s in self.streams if s.codec_type == codec_type), None)

    def to_dict(self) -> dict[str, Any]:
        v, a = self.first("video"), self.first("audio")
        return {
            "format_name": self.format_name,
            "duration_sec": self.duration_sec,
            "size_bytes": self.size_bytes,
            "bit_rate": self.bit_rate,
            "width": v.width if v else None,
            "height": v.height if v else None,
            "fps": v.fps if v else None,
            "video_codec": v.codec_name if v else None,
            "audio_codec": a.codec_name if a else None,
            "sample_rate": a.sample_rate if a else None,
            "channels": a.channels if a else None,
            "streams": [s.__dict__ for s in self.streams],
        }


def _float(v: Any) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f and f >= 0 else None  # drop NaN / negatives


def _int(v: Any) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _rate(v: str | None) -> float | None:
    if not v or "/" not in v:
        return _float(v)
    num, den = v.split("/", 1)
    n, d = _float(num), _float(den)
    return round(n / d, 3) if n is not None and d else None


def build_probe_args(ffprobe_bin: str, path: Path) -> list[str]:
    return [
        ffprobe_bin, "-v", "error", "-hide_banner",
        "-print_format", "json", "-show_format", "-show_streams",
        # Paths are absolute (resolved by safe_join), so they never look like options.
        "-i", str(path),
    ]


def parse_probe_output(raw: str) -> MediaInfo:
    data = json.loads(raw)
    fmt = data.get("format") or {}
    streams = []
    for s in data.get("streams") or []:
        streams.append(
            StreamInfo(
                index=_int(s.get("index")) or 0,
                codec_type=s.get("codec_type") or "unknown",
                codec_name=s.get("codec_name"),
                width=_int(s.get("width")),
                height=_int(s.get("height")),
                fps=_rate(s.get("avg_frame_rate")) or _rate(s.get("r_frame_rate")),
                sample_rate=_int(s.get("sample_rate")),
                channels=_int(s.get("channels")),
                duration_sec=_float(s.get("duration")),
            )
        )
    return MediaInfo(
        format_name=fmt.get("format_name"),
        duration_sec=_float(fmt.get("duration")),
        size_bytes=_int(fmt.get("size")),
        bit_rate=_int(fmt.get("bit_rate")),
        streams=streams,
    )


def probe(path: Path, ffprobe_bin: str = "ffprobe", timeout_sec: int = 60) -> MediaInfo:
    try:
        proc = subprocess.run(
            build_probe_args(ffprobe_bin, path),
            capture_output=True, text=True, timeout=timeout_sec, shell=False, check=False,
            encoding="utf-8", errors="replace",
        )
    except FileNotFoundError as e:
        raise ProbeUnavailable(f"ffprobe not found: {ffprobe_bin}") from e
    except subprocess.TimeoutExpired as e:
        raise ProbeUnavailable(f"ffprobe timed out after {timeout_sec}s") from e
    if proc.returncode != 0:
        raise ProbeError((proc.stderr or "ffprobe failed").strip()[:1000])
    try:
        return parse_probe_output(proc.stdout)
    except (json.JSONDecodeError, AttributeError) as e:
        raise ProbeError(f"unparseable ffprobe output: {e}") from e


def tool_version(binary: str, timeout_sec: int = 10) -> str | None:
    """First line of `<binary> -version`, or None if unavailable."""
    try:
        proc = subprocess.run(
            [binary, "-version"], capture_output=True, text=True,
            timeout=timeout_sec, shell=False, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout.splitlines() or [""])[0].strip() or None
