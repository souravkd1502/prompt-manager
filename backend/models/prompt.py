"""
SQLAlchemy models for Prompt operations.

This module defines the database schema for managing Prompts, including:
- Prompt (base entity)
- PromptVersion (version history of each prompt)
- PromptMetadata (key-value metadata for prompts)
- PromptTag (tags for categorization and search)
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.core.database import Base


class Prompt(Base):
    """
    Represents a Prompt entity.

    A Prompt is the main object that stores details such as title, description,
    tenant ownership, and links to its versions, metadata, and tags.

    Attributes:
        id (str): Unique identifier (UUID stored as string).
        tenant_id (str): ID of the tenant that owns this prompt.
        created_by (str): ID of the user who created this prompt.
        title (str): Title of the prompt.
        description (str): Optional description of the prompt.
        is_archived (bool): Whether the prompt is archived.
        current_version_id (str): ID of the currently active prompt version.
        created_at (datetime): Timestamp when the prompt was created (UTC).
        updated_at (datetime): Timestamp when the prompt was last updated (UTC).
    """

    __tablename__ = "prompts"

    id = Column(String, primary_key=True, index=True)  # UUID stored as string
    tenant_id = Column(
        String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False)
    current_version_id = Column(String, ForeignKey("prompt_versions.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(tz=timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(tz=timezone.utc))

    # Relationships
    versions = relationship(
        "PromptVersion", back_populates="prompt", cascade="all, delete-orphan"
    )
    metadata = relationship(
        "PromptMetadata", back_populates="prompt", cascade="all, delete-orphan"
    )
    tags = relationship(
        "PromptTag", back_populates="prompt", cascade="all, delete-orphan"
    )


class PromptVersion(Base):
    """
    Represents a version of a Prompt.

    Each Prompt can have multiple versions, with unique version numbers.
    This allows version tracking and rollback functionality.

    Attributes:
        id (str): Unique identifier for the version (UUID stored as string).
        prompt_id (str): Foreign key to the parent Prompt.
        version_number (int): Version number of the prompt.
        body (str): The actual prompt content.
        style (str): Optional style or formatting instructions.
        created_by (str): ID of the user who created this version.
        created_at (datetime): Timestamp when the version was created (UTC).
    """

    __tablename__ = "prompt_versions"

    id = Column(String, primary_key=True, index=True)
    prompt_id = Column(
        String, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False
    )
    version_number = Column(Integer, nullable=False)
    body = Column(Text, nullable=False)
    style = Column(Text, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(tz=timezone.utc))

    # Ensure each prompt version number is unique for a given prompt
    __table_args__ = (
        UniqueConstraint("prompt_id", "version_number", name="unique_prompt_version"),
    )

    # Relationship back to Prompt
    prompt = relationship("Prompt", back_populates="versions")


class PromptMetadata(Base):
    """
    Represents metadata for a Prompt.

    Metadata is stored as key-value pairs to allow additional
    contextual information to be stored alongside a prompt.

    Attributes:
        id (int): Auto-incrementing unique identifier.
        prompt_id (str): Foreign key to the associated Prompt.
        key (str): Metadata key (e.g., "language", "category").
        value (str): Metadata value.
    """

    __tablename__ = "prompt_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(
        String, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False
    )
    key = Column(String, nullable=False)
    value = Column(String, nullable=True)

    # Ensure a prompt cannot have duplicate metadata keys
    __table_args__ = (
        UniqueConstraint("prompt_id", "key", name="unique_prompt_metadata"),
    )

    # Relationship back to Prompt
    prompt = relationship("Prompt", back_populates="metadata")


class PromptTag(Base):
    """
    Represents a tag associated with a Prompt.

    Tags provide a simple way to categorize and filter prompts.

    Attributes:
        id (int): Auto-incrementing unique identifier.
        prompt_id (str): Foreign key to the associated Prompt.
        tag (str): The tag text (e.g., "support", "finance").
    """

    __tablename__ = "prompt_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(
        String, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False
    )
    tag = Column(String, nullable=False, index=True)

    # Relationship back to Prompt
    prompt = relationship("Prompt", back_populates="tags")
