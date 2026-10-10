import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from studio.db.enums import (
    Language,
    Platform,
    ProjectStatus,
    VideoStyle,
    VisualMethod,
)
from studio.schemas.common import ORMModel


class VoiceSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    voice_id: str | None = Field(default=None, max_length=200)
    gender: str | None = Field(default=None, max_length=30)
    speaking_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    tone: str | None = Field(default=None, max_length=100)
    accent: str | None = Field(default=None, max_length=100)
    pronunciation_notes: str | None = Field(default=None, max_length=2000)


class CaptionSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    burn_in: bool = True
    export_srt: bool = True
    max_chars_per_line: int = Field(default=32, ge=10, le=80)
    position: str = Field(default="bottom", pattern="^(top|center|bottom)$")


class Branding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    brand_name: str | None = Field(default=None, max_length=200)
    primary_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    logo_asset_id: uuid.UUID | None = None
    cta_text: str | None = Field(default=None, max_length=300)


class ProviderPreferences(BaseModel):
    """Preferred provider keys per capability. Validated against real adapters in Phase 3."""

    model_config = ConfigDict(extra="forbid")
    llm: str | None = Field(default=None, max_length=100)
    image: str | None = Field(default=None, max_length=100)
    video: str | None = Field(default=None, max_length=100)
    tts: str | None = Field(default=None, max_length=100)
    prefer_local: bool = False


class ProjectBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    topic: str = Field(min_length=3, max_length=5000)
    target_audience: str | None = Field(default=None, max_length=300)
    language: Language = Language.MARATHI
    platform: Platform = Platform.INSTAGRAM_REELS
    target_duration_sec: int = Field(default=45, ge=5, le=180)
    style: VideoStyle = VideoStyle.CINEMATIC_DOCUMENTARY
    visual_method: VisualMethod = VisualMethod.AI_IMAGES_AND_VIDEO
    export_preset: str | None = Field(default=None, max_length=64)
    fps: int | None = Field(default=None, ge=1, le=120)
    voiceover_enabled: bool = True
    captions_enabled: bool = True
    voice_settings: VoiceSettings = Field(default_factory=VoiceSettings)
    caption_settings: CaptionSettings = Field(default_factory=CaptionSettings)
    branding: Branding = Field(default_factory=Branding)
    provider_preferences: ProviderPreferences = Field(default_factory=ProviderPreferences)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    """Partial update; omitted fields are unchanged."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    topic: str | None = Field(default=None, min_length=3, max_length=5000)
    target_audience: str | None = Field(default=None, max_length=300)
    language: Language | None = None
    platform: Platform | None = None
    target_duration_sec: int | None = Field(default=None, ge=5, le=180)
    style: VideoStyle | None = None
    visual_method: VisualMethod | None = None
    export_preset: str | None = Field(default=None, max_length=64)
    fps: int | None = Field(default=None, ge=1, le=120)
    voiceover_enabled: bool | None = None
    captions_enabled: bool | None = None
    voice_settings: VoiceSettings | None = None
    caption_settings: CaptionSettings | None = None
    branding: Branding | None = None
    provider_preferences: ProviderPreferences | None = None
    change_summary: str | None = Field(default=None, max_length=500)

    @field_validator("name", "topic")
    @classmethod
    def _not_null(cls, v: str | None) -> str | None:
        # Explicit null is not allowed for required columns.
        if v is None:
            raise ValueError("may not be null")
        return v


class ProjectDuplicate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)


class ProjectRead(ORMModel):
    id: uuid.UUID
    name: str
    description: str | None
    topic: str
    target_audience: str | None
    language: Language
    platform: Platform
    target_duration_sec: int
    style: VideoStyle
    visual_method: VisualMethod
    aspect_ratio: str
    export_preset: str
    width: int
    height: int
    fps: int
    voiceover_enabled: bool
    captions_enabled: bool
    voice_settings: dict[str, Any]
    caption_settings: dict[str, Any]
    branding: dict[str, Any]
    provider_preferences: dict[str, Any]
    status: ProjectStatus
    archived_at: datetime | None
    current_revision: int
    created_at: datetime
    updated_at: datetime


class ProjectSummary(ORMModel):
    id: uuid.UUID
    name: str
    topic: str
    language: Language
    platform: Platform
    target_duration_sec: int
    style: VideoStyle
    status: ProjectStatus
    archived_at: datetime | None
    current_revision: int
    created_at: datetime
    updated_at: datetime


class ProjectRevisionRead(ORMModel):
    id: uuid.UUID
    revision: int
    snapshot: dict[str, Any]
    change_summary: str | None
    created_at: datetime
