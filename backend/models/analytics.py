"""
SQLAlchemy models for logs and analytics.

This module defines models for auditing prompt-related actions,
enabling tracking of changes and user activity for compliance
and historical reference.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint
from datetime import datetime, timezone
from backend.core.database import Base


class AuditLog(Base):
    """
    Represents an audit log entry for tracking changes to Prompts.

    This model helps maintain an immutable history of operations
    performed on prompts, including who performed the action,
    what action was performed, and version changes.

    Attributes:
        id (str): Unique identifier for the log entry (UUID stored as string).
        prompt_id (str): Foreign key referencing the Prompt being modified.
        user_id (str): Optional foreign key referencing the User who performed the action.
        action (str): The action performed (create, update, rollback, delete).
        old_version (str): Optional foreign key referencing the previous version (if applicable).
        new_version (str): Optional foreign key referencing the new version (if applicable).
        timestamp (datetime): When the action was logged (UTC).
    """

    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, index=True)
    prompt_id = Column(
        String, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # Action performed on the prompt
    old_version = Column(
        String, ForeignKey("prompt_versions.id"), nullable=True
    )  # Previous version ID
    new_version = Column(
        String, ForeignKey("prompt_versions.id"), nullable=True
    )  # New version ID
    timestamp = Column(DateTime, default=lambda: datetime.now(tz=timezone.utc))

    # Constraint to ensure only valid actions are logged
    __table_args__ = (
        CheckConstraint(
            "action IN ('create','update','rollback','delete')", name="action_check"
        ),
    )
