"""Application services for the Appeals Bot."""

import logging
from typing import Dict, Any

from .config import config
from telegram import Bot

logger = logging.getLogger(__name__)


class UnbanService:
    """Service to handle user unbanning using PTB async API."""

    def __init__(self) -> None:
        """Initialize unban service."""
        pass

    async def unban_user(self, bot: Bot, user_id: int) -> Dict[str, Any]:
        """Unban a user via python-telegram-bot's Bot API.

        Args:
            bot: PTB Bot instance (e.g., from context.bot).
            user_id: Telegram user ID to unban.
        """
        try:
            ok: bool = await bot.unban_chat_member(
                chat_id=config.main_group_id,
                user_id=user_id,
                only_if_banned=True,
            )
            if ok:
                logger.info(f"User {user_id} unbanned via PTB unban_chat_member")
                return {"ok": True}
            logger.warning(f"PTB unban_chat_member returned False: user_id={user_id}")
            return {"ok": False, "description": "unban_chat_member returned False"}
        except Exception as e:
            logger.error(f"PTB unban_chat_member exception: {e}")
            return {"ok": False, "error": str(e)}


# Global instance for convenience
unban_service = UnbanService()

__all__ = ["UnbanService", "unban_service"]
