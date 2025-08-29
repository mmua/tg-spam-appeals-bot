"""Unit tests for services module to improve coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from appeals_bot.services import UnbanService


class TestUnbanService:
    """Tests for UnbanService.unban_user outcomes."""

    @pytest.mark.asyncio
    async def test_unban_user_success(self):
        service = UnbanService()
        bot = MagicMock()
        bot.unban_chat_member = AsyncMock(return_value=True)

        result = await service.unban_user(bot, 123)

        assert result["ok"] is True
        bot.unban_chat_member.assert_called_once()

    @pytest.mark.asyncio
    async def test_unban_user_false(self):
        service = UnbanService()
        bot = MagicMock()
        bot.unban_chat_member = AsyncMock(return_value=False)

        result = await service.unban_user(bot, 123)

        assert result["ok"] is False
        assert "description" in result

    @pytest.mark.asyncio
    async def test_unban_user_exception(self):
        service = UnbanService()
        bot = MagicMock()
        bot.unban_chat_member = AsyncMock(side_effect=RuntimeError("boom"))

        result = await service.unban_user(bot, 123)

        assert result["ok"] is False
        assert "error" in result


