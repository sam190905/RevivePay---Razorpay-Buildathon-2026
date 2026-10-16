"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator


class Settings(BaseSettings):
    """All application settings, loaded from .env or environment."""

    # --- App ---
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)
    app_mode: str = Field(default="developer", env="APP_MODE")
    backend_url: str = Field(default="")
    frontend_url: str = Field(default="http://localhost:3000")

    @field_validator("backend_url", mode="before")
    @classmethod
    def resolve_backend_url(cls, v: str) -> str:
        if isinstance(v, str) and v.strip():
            return v.strip().rstrip("/")
        import os
        return (
            os.getenv("BACKEND_URL")
            or os.getenv("RENDER_EXTERNAL_URL")
            or f"http://localhost:{os.getenv('PORT', '8000')}"
        )

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://revivepay:revivepay_dev@localhost:5433/revivepay"
    )
    database_url_sync: str = Field(
        default="postgresql://revivepay:revivepay_dev@localhost:5433/revivepay"
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("database_url_sync", mode="before")
    @classmethod
    def normalize_database_url_sync(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql://", 1)
            elif v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql+asyncpg://", "postgresql://", 1)
        return v

    @model_validator(mode="after")
    def sync_fallback(self) -> "Settings":
        if "localhost:5433" in self.database_url_sync and "localhost:5433" not in self.database_url:
            self.database_url_sync = self.database_url.replace("+asyncpg", "")
        return self

    # --- Razorpay ---
    razorpay_key_id: str = Field(default="")
    razorpay_key_secret: str = Field(default="")
    razorpay_webhook_secret: str = Field(default="")

    # --- AI / LLM ---
    ai_provider: str = Field(default="gemini")
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-3.6-flash")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
