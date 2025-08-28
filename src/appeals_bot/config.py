"""Configuration management for the Appeals Bot."""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Configuration settings for the Appeals Bot."""
    
    appeals_bot_token: str = Field(..., env='APPEALS_BOT_TOKEN')
    main_group_id: int = Field(..., env='MAIN_GROUP_ID')
    admin_group_id: int = Field(..., env='ADMIN_GROUP_ID')
    spam_bot_admin_token: str = Field(..., env='SPAM_BOT_ADMIN_TOKEN')
    database_path: str = Field('/data/appeals.db', env='DATABASE_PATH')
    
    # Optional settings
    log_level: str = Field('INFO', env='LOG_LEVEL')
    log_file: Optional[str] = Field(None, env='LOG_FILE')
    api_timeout: int = Field(30, env='API_TIMEOUT')
    
    # tg-spam API settings
    tg_spam_host: str = Field('tg-spam', env='TG_SPAM_HOST')
    tg_spam_port: int = Field(8080, env='TG_SPAM_PORT')
    use_tg_spam_api: bool = Field(True, env='USE_TG_SPAM_API')
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


def get_config() -> Config:
    """Get configuration instance."""
    return Config()


# Global config instance
config = get_config()
