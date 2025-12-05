from functools import lru_cache

from pydantic import AnyUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    app_name: str = "HelpDeskAI"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite:///./helpdesk.db"

    # DeepSeek
    deepseek_api_key: str | None = None
    deepseek_base_url: AnyUrl | None = None
    deepseek_model: str = "deepseek-chat"

    # Telegram
    telegram_bot_token: str | None = None

    # CORS
    allowed_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
