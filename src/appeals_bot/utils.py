"""Utility functions for the Appeals Bot."""

import logging
import requests
from typing import Dict, Optional, Any

from .config import config

logger = logging.getLogger(__name__)


class TelegramAPI:
    """Telegram API helper class."""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    async def unban_chat_member(
        self, 
        chat_id: int, 
        user_id: int, 
        only_if_banned: bool = True
    ) -> Dict[str, Any]:
        """Unban a chat member via Telegram API."""
        url = f"{self.base_url}/unbanChatMember"
        payload = {
            'chat_id': chat_id,
            'user_id': user_id,
            'only_if_banned': only_if_banned
        }
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                timeout=config.api_timeout
            )
            result = response.json()
            logger.info(f"Unban API response: {result}")
            return result
        except requests.RequestException as e:
            logger.error(f"Telegram API error: {e}")
            return {'ok': False, 'error': str(e)}


class TgSpamAPI:
    """tg-spam API helper class."""
    
    def __init__(self):
        self.base_url = f"http://{config.tg_spam_host}:{config.tg_spam_port}"
    
    async def unban_user(self, user_id: int, group_id: int) -> Dict[str, Any]:
        """Unban user via tg-spam API."""
        url = f"{self.base_url}/unban"
        payload = {
            'user_id': user_id,
            'group_id': group_id
        }
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                timeout=config.api_timeout
            )
            result = response.json()
            logger.info(f"tg-spam API response: {result}")
            return result
        except requests.RequestException as e:
            logger.error(f"tg-spam API error: {e}")
            return {'ok': False, 'error': str(e)}


class UnbanService:
    """Service to handle user unbanning with fallback mechanisms."""
    
    def __init__(self):
        self.telegram_api = TelegramAPI(config.spam_bot_admin_token)
        self.tg_spam_api = TgSpamAPI() if config.use_tg_spam_api else None
    
    async def unban_user(self, user_id: int) -> Dict[str, Any]:
        """
        Unban user with fallback from tg-spam API to direct Telegram API.
        """
        # Try tg-spam API first if enabled
        if self.tg_spam_api:
            try:
                result = await self.tg_spam_api.unban_user(user_id, config.main_group_id)
                if result.get('ok'):
                    logger.info(f"User {user_id} unbanned via tg-spam API")
                    return result
                else:
                    logger.warning(f"tg-spam API failed: {result}")
            except Exception as e:
                logger.error(f"tg-spam API exception: {e}")
        
        else:
          # Fallback to direct Telegram API
          try:
              result = await self.telegram_api.unban_chat_member(
                  config.main_group_id, 
                  user_id
              )
              if result.get('ok'):
                  logger.info(f"User {user_id} unbanned via Telegram API")
              else:
                  logger.warning(f"Telegram API failed: {result}")
              return result
          except Exception as e:
              logger.error(f"Telegram API exception: {e}")
              return {'ok': False, 'error': str(e)}


def format_user_mention(first_name: Optional[str], username: Optional[str] = None) -> str:
    """Format user mention string."""
    name = first_name or "Unknown"
    if username:
        return f"{name} (@{username})"
    return name


def escape_markdown(text: str) -> str:
    """Escape markdown special characters."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def validate_appeal_text(text: str) -> tuple[bool, Optional[str]]:
    """Validate appeal text."""
    if not text or not text.strip():
        return False, "Appeal text cannot be empty"
    
    if len(text.strip()) < 10:
        return False, "Appeal text must be at least 10 characters long"
    
    if len(text) > 1000:
        return False, "Appeal text must be less than 1000 characters"
    
    return True, None


# Global instances
unban_service = UnbanService()
