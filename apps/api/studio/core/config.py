"""Application settings, loaded from environment variables / `.env`.

Secrets use `SecretStr` so they are never printed by repr() or logs.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = API_DIR.parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=API_DIR / ".env", env_prefix="STUDIO_", extra="ignore"
    )

    env: str = "development"
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://studio:studio@127.0.0.1:5433/studio"
    )
    storage_root: Path = REPO_ROOT / "storage"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"
    ffprobe_timeout_sec: int = Field(default=60, ge=1, le=600)

    max_upload_mb: int = Field(default=1024, ge=1, le=10240)
    min_free_disk_gb: float = Field(default=5.0, ge=0)

    worker_poll_interval_sec: float = Field(default=1.0, gt=0)
    worker_lease_sec: int = Field(default=120, ge=10)
    worker_heartbeat_stale_sec: int = Field(default=60, ge=5)
    job_default_max_attempts: int = Field(default=3, ge=1, le=20)
    job_backoff_base_sec: float = Field(default=5.0, gt=0)
    job_backoff_max_sec: float = Field(default=600.0, gt=0)

    log_level: str = "INFO"

    @field_validator("storage_root")
    @classmethod
    def _resolve_storage(cls, v: Path) -> Path:
        return v.expanduser().resolve()

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
