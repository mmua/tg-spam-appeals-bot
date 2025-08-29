"""Configuration management for the Appeals Bot."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Configuration settings for the Appeals Bot."""

    appeals_bot_token: str = Field(alias="APPEALS_BOT_TOKEN")
    main_group_id: int = Field(alias="MAIN_GROUP_ID")
    admin_group_id: int = Field(alias="ADMIN_GROUP_ID")
    database_path: str = Field(default="/data/appeals.db", alias="DATABASE_PATH")

    # Optional settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, alias="LOG_FILE")
    api_timeout: int = Field(default=30, alias="API_TIMEOUT")

    # tg-spam API settings
    tg_spam_host: str = Field(default="tg-spam", alias="TG_SPAM_HOST")
    tg_spam_port: int = Field(default=8080, alias="TG_SPAM_PORT")
    use_tg_spam_api: bool = Field(default=True, alias="USE_TG_SPAM_API")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


def get_config() -> Config:
    """Get configuration instance.

    Note: Required fields are loaded from environment at runtime; mypy doesn't
    know that, so we ignore the call-arg check here.
    """
    return Config()  # type: ignore[call-arg]


# Global config instance
config = get_config()
