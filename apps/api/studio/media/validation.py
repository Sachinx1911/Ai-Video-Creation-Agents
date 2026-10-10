"""Per-kind asset validation rules (upload allow-lists + probe checks)."""

from pathlib import Path

from studio.db.enums import AssetKind
from studio.media.probe import MediaInfo

IMAGE_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
VIDEO_EXT = {".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm", ".mkv": "video/x-matroska"}
AUDIO_EXT = {
    ".wav": "audio/wav", ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".aac": "audio/aac",
    ".flac": "audio/flac", ".ogg": "audio/ogg",
}
FONT_EXT = {".ttf": "font/ttf", ".otf": "font/otf", ".woff": "font/woff", ".woff2": "font/woff2"}
SUBTITLE_EXT = {".srt": "application/x-subrip", ".vtt": "text/vtt", ".ass": "text/x-ssa"}

ALLOWED_EXTENSIONS: dict[AssetKind, dict[str, str]] = {
    AssetKind.IMAGE: IMAGE_EXT,
    AssetKind.REFERENCE_IMAGE: IMAGE_EXT,
    AssetKind.LOGO: IMAGE_EXT,
    AssetKind.VIDEO: VIDEO_EXT,
    AssetKind.FINAL_EXPORT: VIDEO_EXT,
    AssetKind.VOICE: AUDIO_EXT,
    AssetKind.MUSIC: AUDIO_EXT,
    AssetKind.SFX: AUDIO_EXT,
    AssetKind.FONT: FONT_EXT,
    AssetKind.SUBTITLE: SUBTITLE_EXT,
    AssetKind.OTHER: {**IMAGE_EXT, **VIDEO_EXT, **AUDIO_EXT, **FONT_EXT, **SUBTITLE_EXT},
}

IMAGE_CODECS = {"png", "mjpeg", "webp"}
IMAGE_FORMATS = {"png_pipe", "jpeg_pipe", "webp_pipe", "image2"}
SUBTITLE_CODECS = {"subrip", "webvtt", "ass", "ssa"}
FONT_MAGIC = (b"\x00\x01\x00\x00", b"OTTO", b"true", b"wOFF", b"wOF2")


def mime_for(kind: AssetKind, filename: str) -> str | None:
    """MIME type from the extension if allowed for this kind; None if not allowed."""
    return ALLOWED_EXTENSIONS[kind].get(Path(filename).suffix.lower())


def media_family(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    for family, table in (
        ("image", IMAGE_EXT), ("video", VIDEO_EXT), ("audio", AUDIO_EXT),
        ("font", FONT_EXT), ("subtitle", SUBTITLE_EXT),
    ):
        if ext in table:
            return family
    return "unknown"


def check_font(path: Path) -> str | None:
    """Return an error string, or None if the header looks like a font."""
    with path.open("rb") as f:
        head = f.read(4)
    return None if head in FONT_MAGIC else "file header is not a TrueType/OpenType/WOFF font"


def check_probe(family: str, info: MediaInfo) -> str | None:
    """Return an error string if probed media does not match the expected family."""
    v, a, s = info.first("video"), info.first("audio"), info.first("subtitle")
    if family == "image":
        if not v or v.codec_name not in IMAGE_CODECS or info.format_name not in IMAGE_FORMATS:
            return f"not a supported still image (format={info.format_name})"
        if not v.width or not v.height:
            return "image has no dimensions"
    elif family == "video":
        if not v or info.format_name in IMAGE_FORMATS:
            return "no video stream"
        if not v.width or not v.height:
            return "video stream has no dimensions"
        if not info.duration_sec or info.duration_sec <= 0:
            return "video has no measurable duration"
    elif family == "audio":
        if not a:
            return "no audio stream"
        if not info.duration_sec or info.duration_sec <= 0:
            return "audio has no measurable duration"
    elif family == "subtitle":
        if not s or s.codec_name not in SUBTITLE_CODECS:
            return "not a readable subtitle file"
    else:
        return f"unsupported media family {family!r}"
    return None
