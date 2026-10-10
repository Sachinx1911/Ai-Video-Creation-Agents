"""Export presets (Phase 1: defined in code; moved to a table in Phase 4)."""

from dataclasses import asdict, dataclass

from studio.db.enums import Platform


@dataclass(frozen=True)
class ExportPreset:
    key: str
    label: str
    aspect_ratio: str
    width: int
    height: int
    fps: int
    video_codec: str
    audio_codec: str
    container: str

    def to_dict(self) -> dict:
        return asdict(self)


EXPORT_PRESETS: dict[str, ExportPreset] = {
    p.key: p
    for p in [
        ExportPreset("vertical_1080p30", "Vertical 1080×1920 · 30 fps", "9:16", 1080, 1920, 30, "h264", "aac", "mp4"),
        ExportPreset("vertical_1080p60", "Vertical 1080×1920 · 60 fps", "9:16", 1080, 1920, 60, "h264", "aac", "mp4"),
        ExportPreset("vertical_720p30", "Vertical 720×1280 · 30 fps (draft)", "9:16", 720, 1280, 30, "h264", "aac", "mp4"),
        ExportPreset("square_1080p30", "Square 1080×1080 · 30 fps", "1:1", 1080, 1080, 30, "h264", "aac", "mp4"),
        ExportPreset("landscape_1080p30", "Landscape 1920×1080 · 30 fps", "16:9", 1920, 1080, 30, "h264", "aac", "mp4"),
    ]
}

DEFAULT_PRESET_BY_PLATFORM: dict[Platform, str] = {
    Platform.INSTAGRAM_REELS: "vertical_1080p30",
    Platform.YOUTUBE_SHORTS: "vertical_1080p30",
}
