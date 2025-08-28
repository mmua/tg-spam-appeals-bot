"""Database operations for the Appeals Bot using Peewee ORM."""

import logging
from datetime import datetime
from typing import List, Optional, Dict

from peewee import *

from .config import config

logger = logging.getLogger(__name__)

# Database connection - will be initialized when needed
db = None


class Appeal(Model):
    """Appeal model using Peewee ORM."""
    
    id = AutoField(primary_key=True)
    user_id = IntegerField(index=True)
    username = CharField(null=True)
    first_name = CharField(null=True)
    appeal_text = TextField()
    original_message = TextField(null=True)
    status = CharField(default='pending', index=True)
    admin_decision = TextField(null=True)
    created_at = DateTimeField(default=datetime.utcnow, index=True)
    processed_at = DateTimeField(null=True)
    
    class Meta:
        # Database will be set when initialized
        table_name = 'appeals'


class DatabaseManager:
    """Database manager for appeals using Peewee."""
    
    def __init__(self, database_path: str = None):
        """Initialize database manager with optional custom database path."""
        global db
        
        # Initialize database connection
        db_path = database_path or config.database_path
        db = SqliteDatabase(db_path)
        
        # Set the database for the model
        Appeal._meta.database = db
        
        # Initialize tables
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize the database with required tables."""
        db.connect()
        db.create_tables([Appeal], safe=True)
        logger.info("Database initialized successfully")
    
    def create_appeal(self, appeal_data: dict) -> int:
        """Create a new appeal and return its ID."""
        appeal = Appeal.create(**appeal_data)
        logger.info(f"Created appeal #{appeal.id} for user {appeal.user_id}")
        return appeal.id
    
    def get_appeal(self, appeal_id: int) -> Optional[Appeal]:
        """Get appeal by ID."""
        try:
            return Appeal.get_by_id(appeal_id)
        except Appeal.DoesNotExist:
            return None
    
    def get_pending_appeal(self, user_id: int) -> Optional[Appeal]:
        """Get pending appeal for user."""
        try:
            return (Appeal
                   .select()
                   .where((Appeal.user_id == user_id) & (Appeal.status == 'pending'))
                   .order_by(Appeal.created_at.desc())
                   .get())
        except Appeal.DoesNotExist:
            return None
    
    def get_pending_appeals(self) -> List[Appeal]:
        """Get all pending appeals."""
        return list(Appeal.select().where(Appeal.status == 'pending').order_by(Appeal.created_at.asc()))
    
    def update_appeal_status(self, appeal_id: int, status: str, admin_decision: str) -> bool:
        """Update appeal status and admin decision."""
        query = (Appeal
                .update(status=status, admin_decision=admin_decision, processed_at=datetime.utcnow())
                .where(Appeal.id == appeal_id))
        rows_updated = query.execute()
        success = rows_updated > 0
        if success:
            logger.info(f"Updated appeal #{appeal_id} status to {status}")
        return success
    
    def get_appeals_stats(self) -> Dict[str, int]:
        """Get appeals statistics."""
        stats = {}
        
        # Count by status
        for appeal in Appeal.select(Appeal.status, fn.COUNT(Appeal.id).alias('count')).group_by(Appeal.status):
            stats[appeal.status] = appeal.count
        
        # Total count
        stats['total'] = Appeal.select().count()
        
        return stats
    
    def get_user_appeals(self, user_id: int) -> List[Appeal]:
        """Get all appeals for a user."""
        return list(Appeal.select().where(Appeal.user_id == user_id).order_by(Appeal.created_at.desc()))


# Global database manager instance - tests can replace this directly
db_manager: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager