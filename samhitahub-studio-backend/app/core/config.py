"""
Application configuration.

All configuration is sourced from environment variables (optionally loaded
from a `.env` file in local development) via `pydantic-settings`. This is
the ONLY place in the codebase that should read `os.environ` directly —
every other module must receive configuration through the `Settings`
object (via dependency injection), never by reading the environment
itself. Centralizing this:

- Makes configuration typed, validated, and discoverable in one file.
- Makes the app trivially testable (override `Settings` in tests/DI).
- Prevents "mystery env vars" scattered across the codebase.

Usage
-----
    from app.core.config import get_settings

    settings = get_settings()
    print(settings.app_name)

`get_settings` is wrapped in `functools.lru_cache` so the environment is
parsed once per process and reused everywhere (cheap, and avoids subtly
different config objects floating around).
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment discriminator.

    Used to toggle behaviors such as debug mode, docs exposure, and log
    formatting without scattering `if env == "prod"` string checks
    throughout the codebase.
    """

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class LogLevel(str, Enum):
    """Supported logging levels, mirroring the stdlib `logging` levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """
    Strongly-typed application settings.

    Every field maps to an environment variable of the same name
    (case-insensitive). See `.env.example` for the full list with
    descriptions and example values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- General application metadata -----------------------------------
    app_name: str = Field(default="SamhitaHub Studio Backend")
    app_version: str = Field(default="0.1.0")
    environment: Environment = Field(default=Environment.LOCAL)
    debug: bool = Field(default=False)

    # --- API configuration -------------------------------------------------
    api_v1_prefix: str = Field(default="/api/v1")
    docs_enabled: bool = Field(
        default=True,
        description="Whether to expose /docs, /redoc, and /openapi.json.",
    )

    # --- Server ---------------------------------------------------------
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # --- CORS -------------------------------------------------------------
    cors_allow_origins: List[str] = Field(default_factory=lambda: ["*"])

    # --- Logging ------------------------------------------------------------
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_json: bool = Field(
        default=False,
        description="Emit logs as structured JSON (recommended for prod).",
    )

    # --- Security (placeholders for future auth work) ----------------------
    secret_key: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="Used later for signing tokens once auth is implemented.",
    )
    access_token_expire_minutes: int = Field(default=60)

    # --- Google Drive integration (placeholders) ---------------------------
    google_service_account_json_path: str | None = Field(default=None)
    google_drive_root_folder_id: str | None = Field(default=None)

    # --- Firestore integration (placeholders) -------------------------------
    firestore_project_id: str | None = Field(default=None)
    firestore_credentials_path: str | None = Field(default=None)

    # --- AI provider integration (placeholders) -----------------------------
    ai_provider_api_key: str | None = Field(default=None)
    ai_provider_model: str = Field(default="claude-sonnet-5")

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_comma_separated_origins(cls, value: object) -> object:
        """Allow CORS origins to be provided as a comma-separated string
        in the environment (e.g. `CORS_ALLOW_ORIGINS=https://a.com,https://b.com`)
        while still supporting a native list when set programmatically.
        """
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        """Convenience flag used by startup code to gate prod-only behavior."""
        return self.environment == Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """Return a cached, process-wide `Settings` instance.

    FastAPI routes/services should depend on this via
    `Depends(get_settings)` rather than instantiating `Settings()`
    directly, so tests can override it cleanly with
    `app.dependency_overrides[get_settings] = lambda: TestSettings()`.
    """
    return Settings()
