"""Smoke tests for bot handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from appeals_bot import handlers
from appeals_bot.database import DatabaseManager


class TestHandlersSmoke:
    """Smoke tests for bot handlers."""
    
    @pytest.mark.asyncio
    async def test_start_command(self, mock_update, mock_context):
        """Test /start command returns welcome message."""
        await handlers.start_command(mock_update, mock_context)
        
        # Verify reply_text was called with English welcome message
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]  # First positional argument
        
        assert "F1News.ru для подачи апелляций" in message_text
        assert "/appeal" in message_text
        assert "/status" in message_text
        assert "/help" in message_text
    
    @pytest.mark.asyncio
    async def test_help_command(self, mock_update, mock_context):
        """Test /help command calls start_command."""
        with patch('appeals_bot.handlers.start_command') as mock_start:
            mock_start.return_value = None
            await handlers.help_command(mock_update, mock_context)
            mock_start.assert_called_once_with(mock_update, mock_context)
    
    @pytest.mark.asyncio
    async def test_appeal_command_no_args(self, mock_update, mock_context):
        """Test /appeal command without arguments shows error."""
        mock_context.args = []
        
        await handlers.appeal_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        
        assert "❌" in message_text
        assert "объяснение для апелляции" in message_text
    
    @pytest.mark.asyncio
    async def test_appeal_command_with_pending_appeal(self, mock_update, mock_context, patched_db_manager, sample_appeal_data):
        """Test /appeal command when user already has pending appeal.
        
        Note: Due to database isolation issues, this test currently validates
        that the handler runs successfully rather than checking the exact logic.
        TODO: Fix database isolation for proper testing.
        """
        mock_context.args = ['Test appeal text']
        
        # Create a pending appeal for the user
        appeal_id = patched_db_manager.create_appeal(sample_appeal_data)
        existing_appeal = patched_db_manager.get_pending_appeal(sample_appeal_data['user_id'])
        assert existing_appeal is not None
        
        await handlers.appeal_command(mock_update, mock_context)
        
        # Verify the handler responded with pending message (user already has pending)
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        
        # Should show pending appeal message since user already has one
        assert "⏳" in message_text, f"Expected pending appeal message, got: {message_text}"
        assert "незавершенная апелляция" in message_text
    
    @pytest.mark.asyncio 
    async def test_appeal_command_success(self, mock_update, mock_context, patched_db_manager):
        """Test successful appeal submission."""
        mock_context.args = ['I was discussing F1 strategy, not making personal attacks']
        
        await handlers.appeal_command(mock_update, mock_context)
        
        # Should have called reply_text at least once
        assert mock_update.message.reply_text.call_count >= 1
        
        # Check success message
        success_call = mock_update.message.reply_text.call_args_list[0]
        success_message = success_call[0][0]
        assert "✅" in success_message
        assert "подана успешно" in success_message
    
    @pytest.mark.asyncio
    async def test_status_command_no_appeals(self, mock_update, mock_context, patched_db_manager):
        """Test /status command when user has no appeals."""
        await handlers.status_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        
        assert "зарегистрированных апелляций" in message_text
    
    @pytest.mark.asyncio
    async def test_status_command_with_appeals(self, mock_update, mock_context, patched_db_manager, sample_appeal_data):
        """Test /status command when user has appeals."""
        # Create an appeal
        appeal_id = patched_db_manager.create_appeal(sample_appeal_data)
            
        await handlers.status_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        
        assert "Ваши апелляции" in message_text
        assert str(appeal_id) in message_text
        assert "Pending" in message_text
    
    @pytest.mark.asyncio
    async def test_approve_command_wrong_chat(self, mock_update, mock_context, mock_config):
        """Test /approve command in wrong chat does nothing."""
        mock_update.effective_chat.id = 99999  # Different from admin group
        
        await handlers.approve_command(mock_update, mock_context)
        
        # Should not call reply_text at all
        mock_update.message.reply_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_approve_command_no_args(self, mock_update, mock_context, mock_config):
        """Test /approve command without arguments."""
        mock_update.effective_chat.id = mock_config.admin_group_id
        mock_context.args = []
        
        await handlers.approve_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        
        assert "❌" in message_text
        assert "ID апелляции" in message_text
    
    @pytest.mark.asyncio
    async def test_approve_command_invalid_id(self, mock_update, mock_context, mock_config):
        """Test /approve command with invalid appeal ID."""
        mock_update.effective_chat.id = mock_config.admin_group_id
        mock_context.args = ['not_a_number']
        
        await handlers.approve_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        
        assert "❌" in message_text
        assert "Неверный ID" in message_text
    
    @pytest.mark.asyncio
    async def test_approve_command_appeal_not_found(self, mock_update, mock_context, mock_config, patched_db_manager):
        """Test /approve command with non-existent appeal."""
        mock_update.effective_chat.id = mock_config.admin_group_id
        mock_context.args = ['99999']
        
        await handlers.approve_command(mock_update, mock_context)
            
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        
        assert "❌" in message_text
        assert "не найдена" in message_text
    
    @pytest.mark.asyncio
    async def test_reject_command_wrong_chat(self, mock_update, mock_context, mock_config):
        """Test /reject command in wrong chat does nothing."""
        mock_update.effective_chat.id = 99999  # Different from admin group
        
        await handlers.reject_command(mock_update, mock_context)
        
        # Should not call reply_text at all
        mock_update.message.reply_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_reject_command_no_args(self, mock_update, mock_context, mock_config):
        """Test /reject command without arguments."""
        mock_update.effective_chat.id = mock_config.admin_group_id
        mock_context.args = []
        
        await handlers.reject_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        
        assert "❌" in message_text
        assert "ID апелляции" in message_text
    
    @pytest.mark.asyncio
    async def test_reject_command_success(self, mock_update, mock_context, mock_config, patched_db_manager, sample_appeal_data):
        """Test successful appeal rejection."""
        mock_update.effective_chat.id = mock_config.admin_group_id
        mock_context.args = ['123', 'Test rejection reason']
        
        with patch('appeals_bot.handlers._notify_user_decision') as mock_notify:
            # Create an appeal
            appeal_id = patched_db_manager.create_appeal(sample_appeal_data)
            mock_context.args[0] = str(appeal_id)  # Use real ID
            
            mock_notify.return_value = None
            
            await handlers.reject_command(mock_update, mock_context)
            
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]
            
            assert "❌" in message_text
            assert "отклонена" in message_text
    
    @pytest.mark.asyncio
    async def test_info_command_wrong_chat(self, mock_update, mock_context, mock_config):
        """Test /info command in wrong chat does nothing."""
        mock_update.effective_chat.id = 99999  # Different from admin group
        
        await handlers.info_command(mock_update, mock_context)
        
        # Should not call reply_text at all
        mock_update.message.reply_text.assert_not_called()
    
    def test_format_admin_notification(self, sample_appeal_data, patched_db_manager):
        """Test admin notification formatting."""
        appeal_id = patched_db_manager.create_appeal(sample_appeal_data)
        appeal = patched_db_manager.get_appeal(appeal_id)
            
        notification = handlers._format_admin_notification(appeal_id, appeal)
        
        assert "Новая апелляция" in notification
        assert str(appeal_id) in notification
        assert str(appeal.user_id) in notification
        assert appeal.first_name in notification
        assert appeal.appeal_text in notification
        assert "/approve" in notification
        assert "/reject" in notification

    @pytest.mark.asyncio
    async def test_edited_message_handler_ignores_non_appeal(self, mock_context):
        """Edited messages not starting with /appeal should be ignored."""
        update = MagicMock()
        update.edited_message = MagicMock()
        update.edited_message.text = "Some random edit"
        update.edited_message.reply_text = AsyncMock()

        await handlers.edited_message_handler(update, mock_context)

        update.edited_message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_edited_message_handler_processes_appeal(self, mock_context, patched_db_manager):
        """Edited /appeal message should be processed and succeed."""
        update = MagicMock()
        edited = MagicMock()
        edited.text = "/appeal Это новая апелляция с достаточной длиной текста"
        edited.reply_text = AsyncMock()
        # from_user fields used by handler
        edited.from_user.id = 12345
        edited.from_user.username = "testuser"
        edited.from_user.first_name = "Test User"
        update.edited_message = edited

        # Mock ban status check to 'kicked'
        mock_context.bot.get_chat_member = AsyncMock(return_value=MagicMock(status='kicked'))

        await handlers.edited_message_handler(update, mock_context)

        # Should acknowledge successful submission
        edited.reply_text.assert_called()
        success_calls = [c for c in edited.reply_text.call_args_list if "✅" in c[0][0]]
        assert success_calls, "Expected a success reply with a checkmark"
    
    @pytest.mark.asyncio
    async def test_notify_user_decision_approved(self, mock_context, patched_db_manager, sample_appeal_data):
        """Test user notification for approved appeal."""
        appeal_id = patched_db_manager.create_appeal(sample_appeal_data)
        appeal = patched_db_manager.get_appeal(appeal_id)
        
        await handlers._notify_user_decision(
            mock_context, 
            appeal, 
            'approved', 
            'Одобрена админом'
        )
        
        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        
        assert call_args[1]['chat_id'] == appeal.user_id
        message_text = call_args[1]['text']
        assert "✅" in message_text
        assert "одобрена" in message_text
        assert "F1News.ru" in message_text
    
    @pytest.mark.asyncio
    async def test_notify_user_decision_rejected(self, mock_context, patched_db_manager, sample_appeal_data):
        """Test user notification for rejected appeal."""
        appeal_id = patched_db_manager.create_appeal(sample_appeal_data)
        appeal = patched_db_manager.get_appeal(appeal_id)
        
        await handlers._notify_user_decision(
            mock_context, 
            appeal, 
            'rejected', 
            'Отклонена админом: нарушение правил'
        )
        
        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        
        assert call_args[1]['chat_id'] == appeal.user_id
        message_text = call_args[1]['text']
        assert "❌" in message_text
        assert "отклонена" in message_text
        assert "нарушение правил" in message_text
