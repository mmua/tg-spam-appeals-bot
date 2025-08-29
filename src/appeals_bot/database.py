"""Database operations for the Appeals Bot using Peewee ORM."""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict

from peewee import (
    Model,
    AutoField,
    IntegerField,
    CharField,
    TextField,
    DateTimeField,
    SqliteDatabase,
    fn,
)

from .config import get_config

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class Appeal(Model):
    """Appeal model using Peewee ORM."""

    id = AutoField(primary_key=True)
    user_id = IntegerField(index=True)
    username = CharField(null=True)
    first_name = CharField(null=True)
    appeal_text = TextField()
    original_message = TextField(null=True)
    status = CharField(default="pending", index=True)
    admin_decision = TextField(null=True)
    created_at = DateTimeField(default=utcnow, index=True)
    processed_at = DateTimeField(null=True)

    class Meta:
        # Database will be set when initialized
        table_name = "appeals"


class DatabaseManager:
    """Database manager for appeals using Peewee."""

    def __init__(self, database_path: Optional[str] = None) -> None:
        """Initialize database manager with optional custom database path.

        Args:
            database_path: Optional path to SQLite file. Defaults to configured path.
        """
        # Initialize database connection (use fresh config to respect env)
        db_path = database_path or get_config().database_path
        self.db = SqliteDatabase(db_path)  # Store as instance attribute

        # Set the database for the model
        Appeal._meta.database = self.db

        # Initialize tables
        self.init_database()

    def init_database(self) -> None:
        """Initialize the database with required tables."""
        if self.db:
            self.db.connect()
            self.db.create_tables([Appeal], safe=True)
            logger.info("Database initialized successfully")

    def create_appeal(self, appeal_data: dict) -> int:
        """Create a new appeal and return its ID."""
        appeal: Appeal = Appeal.create(**appeal_data)
        logger.info(f"Created appeal #{appeal.id} for user {appeal.user_id}")
        appeal_id: int = int(appeal.id)
        return appeal_id

    def get_appeal(self, appeal_id: int) -> Optional["Appeal"]:
        """Get appeal by ID."""
        try:
            appeal: Appeal = Appeal.get_by_id(appeal_id)
            return appeal
        except Appeal.DoesNotExist:
            return None

    def get_pending_appeal(self, user_id: int) -> Optional["Appeal"]:
        """Get pending appeal for user."""
        try:
            appeal: Appeal = (
                Appeal.select()
                .where((Appeal.user_id == user_id) & (Appeal.status == "pending"))
                .order_by(Appeal.created_at.desc())
                .get()
            )
            return appeal
        except Appeal.DoesNotExist:
            return None

    def get_pending_appeals(self) -> List["Appeal"]:
        """Get all pending appeals."""
        return list(
            Appeal.select()
            .where(Appeal.status == "pending")
            .order_by(Appeal.created_at.asc())
        )

    def update_appeal_status(
        self, appeal_id: int, status: str, admin_decision: str
    ) -> bool:
        """Update appeal status and admin decision."""
        query = Appeal.update(
            status=status, admin_decision=admin_decision, processed_at=utcnow()
        ).where(Appeal.id == appeal_id)
        rows_updated: int = query.execute()
        success = rows_updated > 0
        if success:
            logger.info(f"Updated appeal #{appeal_id} status to {status}")
        return success

    def get_appeals_stats(self) -> Dict[str, int]:
        """Get appeals statistics."""
        stats = {}

        # Count by status
        for appeal in Appeal.select(
            Appeal.status, fn.COUNT(Appeal.id).alias("count")
        ).group_by(Appeal.status):
            stats[appeal.status] = appeal.count

        # Total count
        stats["total"] = Appeal.select().count()

        return stats

    def get_user_appeals(self, user_id: int) -> List["Appeal"]:
        """Get all appeals for a user."""
        return list(
            Appeal.select()
            .where(Appeal.user_id == user_id)
            .order_by(Appeal.created_at.desc())
        )


# Global database manager instance - tests can replace this directly
db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager


def reset_db_manager() -> None:
    """Reset the global database manager and close existing DB connection."""
    global db_manager
    if db_manager is not None and getattr(db_manager, "db", None):
        try:
            db_manager.db.close()
        except Exception:
            pass
    db_manager = None
