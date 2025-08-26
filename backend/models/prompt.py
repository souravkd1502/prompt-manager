"""
SQLAlchemy models for Prompt management.

This module defines the database schema for:
- Prompt (base entity)
- PromptVersion (version history of each prompt)
- Tag (categorization labels)
- PromptTag (many-to-many bridge between Prompts and Tags)
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
from datetime import datetime
from backend.core.database import Base


class Prompt(Base):
    """
    Represents a Prompt entity.

    Attributes:
        id (int): Auto-increment primary key.
        tenant_id (int): Foreign key to tenant that owns this prompt.
        created_by (int): Foreign key to the user who created this prompt.
        title (str): Prompt title.
        description (str): Optional description.
        prompt_text (str): Latest active text for this prompt.
        is_archived (bool): Whether the prompt is archived.
        current_version_id (int): Foreign key to the active prompt version.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
    """

    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    prompt_text = Column(Text, nullable=False)
    is_archived = Column(Boolean, default=False)
    current_version_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    versions = relationship("PromptVersion", back_populates="prompt", cascade="all, delete-orphan")
    tags = relationship("PromptTag", back_populates="prompt", cascade="all, delete-orphan")


class PromptVersion(Base):
    """
    Represents a specific version of a Prompt.

    Attributes:
        id (int): Auto-increment primary key.
        prompt_id (int): Foreign key to parent Prompt.
        version_number (int): Incremental version number (unique per prompt).
        prompt_text (str): Versioned content of the prompt.
        style (str): Optional style.
        created_by (int): Foreign key to user who created this version.
        created_at (datetime): Creation timestamp.
    """

    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    prompt_text = Column(Text, nullable=False)
    style = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("prompt_id", "version_number", name="uq_prompt_version"),
    )

    # Relationships
    prompt = relationship("Prompt", back_populates="versions")


class Tag(Base):
    """
    Represents a Tag entity.

    Attributes:
        id (int): Auto-increment primary key.
        name (str): Unique tag name.
        created_at (datetime): Timestamp when created.
    """

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prompt_tags = relationship("PromptTag", back_populates="tag", cascade="all, delete-orphan")


class PromptTag(Base):
    """
    Bridge table for many-to-many relationship between Prompts and Tags.

    Attributes:
        prompt_id (int): Foreign key to Prompt.
        tag_id (int): Foreign key to Tag.
        assigned_at (datetime): Timestamp of assignment.
    """

    __tablename__ = "prompt_tags"

    prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prompt = relationship("Prompt", back_populates="tags")
    tag = relationship("Tag", back_populates="prompt_tags")
