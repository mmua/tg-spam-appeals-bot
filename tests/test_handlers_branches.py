"""Targeted branch tests for handlers to raise coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from appeals_bot import handlers


@pytest.mark.asyncio
async def test_appeal_command_user_not_kicked(mock_update, mock_context):
    mock_context.args = ["Valid appeal text with enough length"]
    # Simulate user not banned
    mock_context.bot.get_chat_member = AsyncMock(return_value=MagicMock(status="member"))

    await handlers.appeal_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    assert "не заблокированы" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_appeal_command_get_chat_member_exception(mock_update, mock_context):
    mock_context.args = ["Another valid appeal text long enough"]
    # Simulate API error
    mock_context.bot.get_chat_member = AsyncMock(side_effect=RuntimeError("api error"))

    await handlers.appeal_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    assert "Не удалось проверить ваш статус" in mock_update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_pending_and_stats_empty(mock_update, mock_context, mock_config, patched_db_manager):
    # Wrong chat first
    mock_update.effective_chat.id = 999
    await handlers.pending_command(mock_update, mock_context)
    await handlers.stats_command(mock_update, mock_context)
    # Now correct chat
    mock_update.effective_chat.id = mock_config.admin_group_id
    await handlers.pending_command(mock_update, mock_context)
    await handlers.stats_command(mock_update, mock_context)
    # Should have at least one call from pending with 'No pending appeals.' or stats header
    texts = [c[0][0] for c in mock_update.message.reply_text.call_args_list]
    assert any("No pending appeals" in t or "Appeals Statistics" in t for t in texts)


