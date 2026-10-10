"""Domain enums. Stored as VARCHAR + CHECK constraints (ADR-0004)."""

from enum import StrEnum


class Language(StrEnum):
    MARATHI = "mr"
    HINDI = "hi"
    ENGLISH = "en"


class Platform(StrEnum):
    INSTAGRAM_REELS = "instagram_reels"
    YOUTUBE_SHORTS = "youtube_shorts"


class VideoStyle(StrEnum):
    CINEMATIC_DOCUMENTARY = "cinematic_documentary"
    PHOTOREALISTIC_COMMERCIAL = "photorealistic_commercial"
    EDUCATIONAL_EXPLAINER = "educational_explainer"
    ANIMATION_3D = "animation_3d"


class VisualMethod(StrEnum):
    AI_IMAGES = "ai_images"
    AI_VIDEO = "ai_video"
    AI_IMAGES_AND_VIDEO = "ai_images_and_video"


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    PLANNING = "planning"
    GENERATING = "generating"
    RENDERING = "rendering"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"


class AssetKind(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    MUSIC = "music"
    SFX = "sfx"
    LOGO = "logo"
    FONT = "font"
    REFERENCE_IMAGE = "reference_image"
    SUBTITLE = "subtitle"
    FINAL_EXPORT = "final_export"
    OTHER = "other"


class AssetOrigin(StrEnum):
    UPLOAD = "upload"
    GENERATED = "generated"
    RENDERED = "rendered"


class ValidationStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_RETRY = "awaiting_retry"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_JOB_STATUSES = frozenset(
    {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}
)


class ErrorCategory(StrEnum):
    TRANSIENT = "transient"
    RATE_LIMITED = "rate_limited"
    PROVIDER_OUTAGE = "provider_outage"
    INVALID_REQUEST = "invalid_request"
    AUTH = "auth"
    INVALID_OUTPUT = "invalid_output"
    INTERNAL = "internal"
    CANCELLED = "cancelled"
    LEASE_EXPIRED = "lease_expired"


RETRYABLE_ERROR_CATEGORIES = frozenset(
    {
        ErrorCategory.TRANSIENT,
        ErrorCategory.RATE_LIMITED,
        ErrorCategory.PROVIDER_OUTAGE,
        ErrorCategory.LEASE_EXPIRED,
    }
)
