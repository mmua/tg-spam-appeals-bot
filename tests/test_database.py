"""Smoke tests for database operations."""

import pytest
from datetime import datetime

from appeals_bot.database import DatabaseManager, Appeal


class TestDatabaseSmoke:
    """Smoke tests for database functionality."""
    
    def test_database_initialization(self, db_manager: DatabaseManager):
        """Test that database initializes correctly."""
        assert db_manager is not None
        assert Appeal.table_exists()
    
    def test_create_appeal(self, db_manager: DatabaseManager, sample_appeal_data: dict):
        """Test creating a new appeal."""
        appeal_id = db_manager.create_appeal(sample_appeal_data)
        
        assert appeal_id is not None
        assert appeal_id > 0
        
        # Verify the appeal was created
        appeal = db_manager.get_appeal(appeal_id)
        assert appeal is not None
        assert appeal.user_id == sample_appeal_data['user_id']
        assert appeal.username == sample_appeal_data['username']
        assert appeal.first_name == sample_appeal_data['first_name']
        assert appeal.appeal_text == sample_appeal_data['appeal_text']
        assert appeal.status == 'pending'
        assert appeal.created_at is not None
    
    def test_get_nonexistent_appeal(self, db_manager: DatabaseManager):
        """Test getting a non-existent appeal returns None."""
        appeal = db_manager.get_appeal(99999)
        assert appeal is None
    
    def test_get_pending_appeal(self, db_manager: DatabaseManager, sample_appeal_data: dict):
        """Test getting pending appeal for user."""
        # Create an appeal
        appeal_id = db_manager.create_appeal(sample_appeal_data)
        
        # Should find the pending appeal
        pending_appeal = db_manager.get_pending_appeal(sample_appeal_data['user_id'])
        assert pending_appeal is not None
        assert pending_appeal.id == appeal_id
        assert pending_appeal.status == 'pending'
        
        # Should not find pending appeal for different user
        no_appeal = db_manager.get_pending_appeal(99999)
        assert no_appeal is None
    
    def test_get_pending_appeals(self, db_manager: DatabaseManager, sample_appeal_data: dict):
        """Test getting all pending appeals."""
        # Initially should be empty
        pending = db_manager.get_pending_appeals()
        initial_count = len(pending)
        
        # Create an appeal
        appeal_id = db_manager.create_appeal(sample_appeal_data)
        
        # Should now have one more pending appeal
        pending = db_manager.get_pending_appeals()
        assert len(pending) == initial_count + 1
        assert any(appeal.id == appeal_id for appeal in pending)
    
    def test_update_appeal_status(self, db_manager: DatabaseManager, sample_appeal_data: dict):
        """Test updating appeal status."""
        # Create an appeal
        appeal_id = db_manager.create_appeal(sample_appeal_data)
        
        # Update status to approved
        success = db_manager.update_appeal_status(
            appeal_id, 
            'approved', 
            'Approved by test admin'
        )
        assert success is True
        
        # Verify the update
        appeal = db_manager.get_appeal(appeal_id)
        assert appeal.status == 'approved'
        assert appeal.admin_decision == 'Approved by test admin'
        assert appeal.processed_at is not None
        
        # Should no longer be in pending appeals
        pending_appeal = db_manager.get_pending_appeal(sample_appeal_data['user_id'])
        assert pending_appeal is None
    
    def test_update_nonexistent_appeal(self, db_manager: DatabaseManager):
        """Test updating non-existent appeal returns False."""
        success = db_manager.update_appeal_status(
            99999, 
            'approved', 
            'Test decision'
        )
        assert success is False
    
    def test_get_appeals_stats(self, db_manager: DatabaseManager, sample_appeal_data: dict):
        """Test getting appeals statistics."""
        # Get initial stats
        initial_stats = db_manager.get_appeals_stats()
        initial_total = initial_stats.get('total', 0)
        initial_pending = initial_stats.get('pending', 0)
        
        # Create an appeal
        appeal_id = db_manager.create_appeal(sample_appeal_data)
        
        # Check stats after creation
        stats = db_manager.get_appeals_stats()
        assert stats['total'] == initial_total + 1
        assert stats.get('pending', 0) == initial_pending + 1
        
        # Approve the appeal
        db_manager.update_appeal_status(appeal_id, 'approved', 'Test approval')
        
        # Check stats after approval
        stats = db_manager.get_appeals_stats()
        assert stats['total'] == initial_total + 1
        assert stats.get('pending', 0) == initial_pending  # Should be back to initial
        assert stats.get('approved', 0) >= 1
    
    def test_get_user_appeals(self, db_manager: DatabaseManager, sample_appeal_data: dict):
        """Test getting all appeals for a user."""
        user_id = sample_appeal_data['user_id']
        
        # Initially no appeals for user
        appeals = db_manager.get_user_appeals(user_id)
        initial_count = len(appeals)
        
        # Create first appeal
        appeal_id_1 = db_manager.create_appeal(sample_appeal_data)
        
        # Create second appeal with different text
        sample_appeal_data['appeal_text'] = 'Second appeal text'
        appeal_id_2 = db_manager.create_appeal(sample_appeal_data)
        
        # Should now have two appeals
        appeals = db_manager.get_user_appeals(user_id)
        assert len(appeals) == initial_count + 2
        
        appeal_ids = [appeal.id for appeal in appeals]
        assert appeal_id_1 in appeal_ids
        assert appeal_id_2 in appeal_ids
        
        # Should be ordered by created_at DESC (newest first)
        if len(appeals) >= 2:
            assert appeals[0].created_at >= appeals[1].created_at
    
    def test_multiple_users_isolation(self, db_manager: DatabaseManager):
        """Test that appeals are properly isolated between users."""
        user1_data = {
            'user_id': 11111,
            'username': 'user1',
            'first_name': 'User One',
            'appeal_text': 'User 1 appeal'
        }
        
        user2_data = {
            'user_id': 22222,
            'username': 'user2', 
            'first_name': 'User Two',
            'appeal_text': 'User 2 appeal'
        }
        
        # Create appeals for both users
        appeal_id_1 = db_manager.create_appeal(user1_data)
        appeal_id_2 = db_manager.create_appeal(user2_data)
        
        # Each user should only see their own appeals
        user1_appeals = db_manager.get_user_appeals(11111)
        user2_appeals = db_manager.get_user_appeals(22222)
        
        user1_ids = [appeal.id for appeal in user1_appeals]
        user2_ids = [appeal.id for appeal in user2_appeals]
        
        assert appeal_id_1 in user1_ids
        assert appeal_id_1 not in user2_ids
        assert appeal_id_2 in user2_ids
        assert appeal_id_2 not in user1_ids
    
    def test_appeal_model_fields(self, db_manager: DatabaseManager, sample_appeal_data: dict):
        """Test that all Appeal model fields work correctly."""
        appeal_id = db_manager.create_appeal(sample_appeal_data)
        appeal = db_manager.get_appeal(appeal_id)
        
        # Test all fields are accessible
        assert hasattr(appeal, 'id')
        assert hasattr(appeal, 'user_id')
        assert hasattr(appeal, 'username')
        assert hasattr(appeal, 'first_name')
        assert hasattr(appeal, 'appeal_text')
        assert hasattr(appeal, 'original_message')
        assert hasattr(appeal, 'status')
        assert hasattr(appeal, 'admin_decision')
        assert hasattr(appeal, 'created_at')
        assert hasattr(appeal, 'processed_at')
        
        # Test field types
        assert isinstance(appeal.id, int)
        assert isinstance(appeal.user_id, int)
        assert isinstance(appeal.created_at, datetime)
        assert appeal.original_message is None  # Not set in sample data
        assert appeal.admin_decision is None    # Not set initially
        assert appeal.processed_at is None      # Not processed yet