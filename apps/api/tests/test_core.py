"""Unit tests: path safety, secret redaction, probe parsing, schema validation (no DB)."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from studio.core.logging import redact
from studio.core.paths import UnsafePathError, safe_join, sanitize_filename
from studio.media.probe import build_probe_args, parse_probe_output
from studio.media.validation import check_probe
from studio.schemas.projects import ProjectCreate, ProjectUpdate


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("clip.mp4", "clip.mp4"),
        ("../../etc/passwd", "passwd"),
        ("..\\..\\Windows\\win.ini", "win.ini"),
        ("C:\\temp\\x.png", "x.png"),
        ("my video (final).MP4", "my_video_final.MP4"),
        ("CON.wav", "_CON.wav"),
        ("", "file"),
        ("....", "file"),
        ("मराठी.mp3", "file.mp3"),
        (".bashrc", "bashrc"),
    ],
)
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


@pytest.mark.parametrize(
    "key", ["../x", "a/../../x", "/etc/passwd", "C:/Windows/x", "a\\..\\..\\x", "", "a\x00b"]
)
def test_safe_join_rejects_escape(tmp_path: Path, key):
    with pytest.raises(UnsafePathError):
        safe_join(tmp_path, key)


def test_safe_join_accepts_nested(tmp_path: Path):
    p = safe_join(tmp_path, "projects/abc/assets/v1/a.png")
    assert p.is_relative_to(tmp_path.resolve())


def test_redact_secrets():
    s = redact("url=postgresql://studio:hunter2@db/x api_key=sk-123 Authorization: Bearer abc")
    assert "hunter2" not in s and "sk-123" not in s and "Bearer abc" not in s


def test_probe_args_are_a_list_without_shell():
    args = build_probe_args("ffprobe", Path("/tmp/a b.mp4"))
    assert args[0] == "ffprobe" and args[-1].endswith("a b.mp4") and args[-2] == "-i"


def test_parse_probe_output_and_checks():
    raw = json.dumps({
        "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "2.0", "size": "1000"},
        "streams": [
            {"index": 0, "codec_type": "video", "codec_name": "h264", "width": 1080,
             "height": 1920, "avg_frame_rate": "30/1"},
            {"index": 1, "codec_type": "audio", "codec_name": "aac", "sample_rate": "48000",
             "channels": 2},
        ],
    })
    info = parse_probe_output(raw)
    d = info.to_dict()
    assert (d["width"], d["height"], d["fps"], d["duration_sec"]) == (1080, 1920, 30.0, 2.0)
    assert check_probe("video", info) is None
    assert check_probe("audio", info) is None
    assert check_probe("image", info) is not None


def test_project_create_defaults_and_validation():
    p = ProjectCreate(name="  CIDCO  ", topic="CIDCO housing")
    assert p.name == "CIDCO" and p.language == "mr" and p.target_duration_sec == 45
    for bad in (
        {"name": "", "topic": "abc"},
        {"name": "x", "topic": "abc", "target_duration_sec": 500},
        {"name": "x", "topic": "abc", "language": "fr"},
        {"name": "x", "topic": "abc", "unknown_field": 1},
        {"name": "x", "topic": "abc", "branding": {"primary_color": "red"}},
    ):
        with pytest.raises(ValidationError):
            ProjectCreate(**bad)


def test_project_update_rejects_null_required():
    with pytest.raises(ValidationError):
        ProjectUpdate(name=None)
    assert ProjectUpdate().model_dump(exclude_unset=True) == {}
