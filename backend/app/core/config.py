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

    # Email (Outlook)
    email_enabled: bool = False
    email_imap_host: str = "outlook.office365.com"
    email_imap_port: int = 993
    email_smtp_host: str = "smtp.office365.com"
    email_smtp_port: int = 587
    email_username: str | None = None
    email_password: str | None = None
    email_from_name: str = "Kazakhtelecom HelpDesk"

    # CORS
    allowed_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
