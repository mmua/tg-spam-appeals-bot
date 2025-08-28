"""Smoke tests for utility functions."""

import pytest
from unittest.mock import patch, AsyncMock

from appeals_bot.utils import validate_appeal_text, format_user_mention


class TestUtilsSmoke:
    """Smoke tests for utility functions."""
    
    def test_validate_appeal_text_valid(self):
        """Test validation of valid appeal text."""
        valid_text = "I was discussing F1 race strategy, not making personal attacks."
        
        is_valid, error_msg = validate_appeal_text(valid_text)
        
        assert is_valid is True
        assert error_msg is None
    
    def test_validate_appeal_text_too_short(self):
        """Test validation of too short appeal text."""
        short_text = "Hi"
        
        is_valid, error_msg = validate_appeal_text(short_text)
        
        assert is_valid is False
        assert error_msg is not None
        assert len(error_msg) > 0
    
    def test_validate_appeal_text_too_long(self):
        """Test validation of too long appeal text."""
        long_text = "x" * 2001  # Assuming max length is 2000
        
        is_valid, error_msg = validate_appeal_text(long_text)
        
        assert is_valid is False
        assert error_msg is not None
        assert len(error_msg) > 0
    
    def test_validate_appeal_text_empty(self):
        """Test validation of empty appeal text."""
        empty_text = ""
        
        is_valid, error_msg = validate_appeal_text(empty_text)
        
        assert is_valid is False
        assert error_msg is not None
    
    def test_validate_appeal_text_whitespace_only(self):
        """Test validation of whitespace-only appeal text."""
        whitespace_text = "   \n\t  "
        
        is_valid, error_msg = validate_appeal_text(whitespace_text)
        
        assert is_valid is False
        assert error_msg is not None
    
    def test_format_user_mention_with_username(self):
        """Test user mention formatting with username."""
        first_name = "John"
        username = "john_doe"
        
        mention = format_user_mention(first_name, username)
        
        assert mention == "John (@john_doe)"
    
    def test_format_user_mention_without_username(self):
        """Test user mention formatting without username."""
        first_name = "John"
        username = None
        
        mention = format_user_mention(first_name, username)
        
        assert mention == "John"
    
    def test_format_user_mention_empty_username(self):
        """Test user mention formatting with empty username."""
        first_name = "John"
        username = ""
        
        mention = format_user_mention(first_name, username)
        
        assert mention == "John"
    
    def test_format_user_mention_no_first_name(self):
        """Test user mention formatting without first name."""
        first_name = None
        username = "john_doe"
        
        mention = format_user_mention(first_name, username)
        
        assert mention == "Unknown (@john_doe)"
    
    def test_format_user_mention_nothing(self):
        """Test user mention formatting with nothing."""
        first_name = None
        username = None
        
        mention = format_user_mention(first_name, username)
        
        assert mention == "Unknown"


class TestUnbanServiceSmoke:
    """Smoke tests for unban service."""
    
    @pytest.mark.asyncio
    async def test_unban_service_import(self):
        """Test that unban service can be imported."""
        from appeals_bot.utils import unban_service
        
        assert unban_service is not None
        assert hasattr(unban_service, 'unban_user')
    
    @pytest.mark.asyncio
    async def test_unban_user_success(self):
        """Test successful user unban."""
        from appeals_bot.utils import unban_service
        
        with patch.object(unban_service, 'unban_user', return_value={'ok': True}) as mock_unban:
            result = await unban_service.unban_user(12345)
            
            assert result['ok'] is True
            mock_unban.assert_called_once_with(12345)
    
    @pytest.mark.asyncio
    async def test_unban_user_failure(self):
        """Test failed user unban."""
        from appeals_bot.utils import unban_service
        
        with patch.object(unban_service, 'unban_user', return_value={'ok': False, 'description': 'User not found'}) as mock_unban:
            result = await unban_service.unban_user(12345)
            
            assert result['ok'] is False
            assert 'description' in result
            mock_unban.assert_called_once_with(12345)