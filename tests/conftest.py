"""Test configuration and fixtures."""

import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Generator

from appeals_bot.database import DatabaseManager
from appeals_bot.config import config


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create a temporary database for testing."""
    # Create a temp file but don't open it, just get the path
    fd, tmp_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)  # Close the file descriptor so the database can use it
    
    yield tmp_path
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def db_manager(temp_db: str) -> DatabaseManager:
    """Create a database manager with temporary database for database tests."""
    return DatabaseManager(database_path=temp_db)


@pytest.fixture
def sample_appeal_data() -> dict:
    """Sample appeal data for testing."""
    return {
        'user_id': 12345,
        'username': 'testuser',
        'first_name': 'Test User',
        'appeal_text': 'I was discussing F1 race strategy, not making personal attacks.'
    }


@pytest.fixture
def mock_update():
    """Mock Telegram Update object."""
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.username = 'testuser'
    update.effective_user.first_name = 'Test User'
    update.effective_chat.id = 67890
    # Ensure message exists and has from_user matching effective_user
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.message.from_user = MagicMock()
    update.message.from_user.id = update.effective_user.id
    update.message.from_user.username = update.effective_user.username
    update.message.from_user.first_name = update.effective_user.first_name
    return update


@pytest.fixture
def mock_context():
    """Mock Telegram Context object."""
    context = MagicMock()
    context.args = []
    context.bot.send_message = AsyncMock()
    # Mock get_chat_member to return a kicked user by default
    mock_chat_member = MagicMock()
    mock_chat_member.status = 'kicked'
    context.bot.get_chat_member = AsyncMock(return_value=mock_chat_member)
    return context


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    original_admin_group_id = config.admin_group_id
    config.admin_group_id = 67890
    
    yield config
    
    # Restore original config
    config.admin_group_id = original_admin_group_id


@pytest.fixture
def patched_db_manager(temp_db):
    """Fixture that sets DATABASE_PATH, resets DB manager, and returns it.

    Avoids patching handlers; all code uses get_db_manager() reading fresh config.
    """
    import os
    from appeals_bot import database
    
    # Set environment variable for this test's DB path
    original_db_path = os.environ.get('DATABASE_PATH')
    os.environ['DATABASE_PATH'] = temp_db
    
    try:
        # Reset and re-create the global db manager to pick env change
        database.reset_db_manager()
        mgr = database.get_db_manager()
        yield mgr
    finally:
        # Restore original env and reset
        if original_db_path is not None:
            os.environ['DATABASE_PATH'] = original_db_path
        else:
            os.environ.pop('DATABASE_PATH', None)
        database.reset_db_manager()