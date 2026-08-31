"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """All application settings, loaded from .env or environment."""

    # --- App ---
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)
    app_mode: str = Field(default="developer", env="APP_MODE")
    backend_url: str = Field(default="http://localhost:8000")
    frontend_url: str = Field(default="http://localhost:3000")

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://revivepay:revivepay_dev@localhost:5433/revivepay"
    )
    database_url_sync: str = Field(
        default="postgresql://revivepay:revivepay_dev@localhost:5433/revivepay"
    )

    # --- Razorpay ---
    razorpay_key_id: str = Field(default="")
    razorpay_key_secret: str = Field(default="")
    razorpay_webhook_secret: str = Field(default="")

    # --- AI / LLM ---
    ai_provider: str = Field(default="openai")
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.5-flash")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
