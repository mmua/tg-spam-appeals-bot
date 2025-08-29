"""F1 Appeals Bot - Telegram bot for handling community moderation appeals."""

__version__ = "1.0.0"
__author__ = "F1news.ru"
__email__ = "maxim.moroz@f1news.ru"

from .config import config
from .database import get_db_manager, db_manager, Appeal
from .services import unban_service

__all__ = ["config", "get_db_manager", "db_manager", "Appeal", "unban_service"]
