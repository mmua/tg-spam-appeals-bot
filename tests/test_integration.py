"""Integration smoke tests for the entire bot workflow."""

import pytest
from unittest.mock import patch, AsyncMock

from appeals_bot import handlers


class TestIntegrationSmoke:
    """Integration smoke tests for complete workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_appeal_workflow_approved(self, mock_update, mock_context, mock_config, patched_db_manager):
        """Test complete workflow: submit -> admin approve -> user notification."""
        # Step 1: User submits appeal
        mock_context.args = ['I was discussing F1 strategy, not making personal attacks']
        
        with patch('appeals_bot.handlers.validate_appeal_text', return_value=(True, None)), \
             patch('appeals_bot.handlers._format_admin_notification', return_value='Admin notification'), \
             patch('appeals_bot.handlers.unban_service') as mock_unban, \
             patch('appeals_bot.handlers._notify_user_decision') as mock_notify:
            
            mock_unban.unban_user = AsyncMock(return_value={'ok': True})
            mock_notify.return_value = None
            
            # Submit appeal
            await handlers.appeal_command(mock_update, mock_context)
            
            # Verify appeal was created
            appeals = patched_db_manager.get_user_appeals(mock_update.effective_user.id)
            assert len(appeals) == 1
            appeal = appeals[0]
            assert appeal.status == 'pending'
            
            # Step 2: Admin approves appeal
            mock_update.effective_chat.id = mock_config.admin_group_id
            mock_context.args = [str(appeal.id)]
            
            await handlers.approve_command(mock_update, mock_context)
            
            # Verify appeal was approved
            updated_appeal = patched_db_manager.get_appeal(appeal.id)
            assert updated_appeal.status == 'approved'
            assert updated_appeal.processed_at is not None
            assert 'Одобрена' in updated_appeal.admin_decision
            
            # Verify unban service was called
            mock_unban.unban_user.assert_called_once_with(appeal.user_id)
            
            # Verify user was notified
            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_appeal_workflow_rejected(self, mock_update, mock_context, mock_config, patched_db_manager):
        """Test complete workflow: submit -> admin reject -> user notification."""
        # Step 1: User submits appeal
        mock_context.args = ['Test appeal text']
        
        with patch('appeals_bot.handlers.validate_appeal_text', return_value=(True, None)), \
             patch('appeals_bot.handlers._format_admin_notification', return_value='Admin notification'), \
             patch('appeals_bot.handlers._notify_user_decision') as mock_notify:
            
            mock_notify.return_value = None
            
            # Submit appeal
            await handlers.appeal_command(mock_update, mock_context)
            
            # Verify appeal was created
            appeals = patched_db_manager.get_user_appeals(mock_update.effective_user.id)
            assert len(appeals) == 1
            appeal = appeals[0]
            
            # Step 2: Admin rejects appeal
            mock_update.effective_chat.id = mock_config.admin_group_id
            mock_context.args = [str(appeal.id), 'Spam', 'message']
            
            await handlers.reject_command(mock_update, mock_context)
            
            # Verify appeal was rejected
            updated_appeal = patched_db_manager.get_appeal(appeal.id)
            assert updated_appeal.status == 'rejected'
            assert updated_appeal.processed_at is not None
            assert 'Spam message' in updated_appeal.admin_decision
            
            # Verify user was notified
            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_user_cannot_submit_multiple_pending_appeals(self, mock_update, mock_context, patched_db_manager):
        """Test that user cannot submit multiple pending appeals."""
        mock_context.args = ['First appeal']
        
        with patch('appeals_bot.handlers.validate_appeal_text', return_value=(True, None)), \
             patch('appeals_bot.handlers._format_admin_notification', return_value='Admin notification'):
            
            # Submit first appeal
            await handlers.appeal_command(mock_update, mock_context)
            
            # Verify first appeal was created
            appeals = patched_db_manager.get_user_appeals(mock_update.effective_user.id)
            assert len(appeals) == 1
            
            # Reset mock calls
            mock_update.message.reply_text.reset_mock()
            
            # Try to submit second appeal
            mock_context.args = ['Second appeal']
            await handlers.appeal_command(mock_update, mock_context)
            
            # Should get error message
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]
            assert "незавершенная апелляция" in message_text
            
            # Still only one appeal
            appeals = patched_db_manager.get_user_appeals(mock_update.effective_user.id)
            assert len(appeals) == 1
    
    @pytest.mark.asyncio
    async def test_error_handling_in_appeal_creation(self, mock_update, mock_context, patched_db_manager):
        """Test error handling during appeal creation."""
        mock_context.args = ['Test appeal']
        
        with patch('appeals_bot.handlers.validate_appeal_text', return_value=(True, None)), \
             patch.object(patched_db_manager, 'create_appeal', side_effect=Exception('Database error')):
            
            await handlers.appeal_command(mock_update, mock_context)
            
            # Should get error message
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]
            
            assert "❌" in message_text
            assert "Не удалось подать апелляцию" in message_text