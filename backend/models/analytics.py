"""
SQLAlchemy models for audit logging.

This module defines the `AuditLog` model, which records prompt-related
actions for analytics, compliance, and historical tracking.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint
from backend.core.database import Base


class AuditLog(Base):
    """
    Audit log entry for prompt actions.

    Captures an immutable record of operations performed on prompts,
    including the user, action type, version changes, and timestamp.

    Attributes:
        id (str): Unique identifier (UUID stored as string).
        prompt_id (str): Reference to the modified prompt.
        user_id (str): Reference to the user who performed the action.
        action (str): Type of action ('create', 'update', 'rollback', 'delete').
        old_version (str): Reference to the previous prompt version.
        new_version (str): Reference to the new prompt version.
        timestamp (datetime): Time of action in UTC.
    """

    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, index=True)
    prompt_id = Column(String, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    old_version = Column(String, ForeignKey("prompt_versions.id"), nullable=True)
    new_version = Column(String, ForeignKey("prompt_versions.id"), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(tz=timezone.utc))

    __table_args__ = (
        CheckConstraint(
            "action IN ('create','update','rollback','delete')",
            name="audit_log_action_check"
        ),
    )
