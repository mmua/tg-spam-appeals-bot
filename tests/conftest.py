"""Test configuration and fixtures."""

import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Generator

from appeals_bot.database import DatabaseManager, Appeal
from appeals_bot.config import config


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def db_manager(temp_db: str) -> DatabaseManager:
    """Create a database manager with temporary database."""
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
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Mock Telegram Context object."""
    context = MagicMock()
    context.args = []
    context.bot.send_message = AsyncMock()
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
def patched_db_manager(db_manager):
    """Fixture that patches get_db_manager to return test db_manager."""
    with patch('appeals_bot.handlers.get_db_manager', return_value=db_manager):
        yield db_manager