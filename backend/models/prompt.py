"""
SQLAlchemy models for Prompt management.

This module defines the database schema for:
- Prompt (base entity)
- PromptVersion (version history of each prompt)
- Users (system users)
- Tenants (tenant accounts)
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


#######################################
# Prompt Management Models
#######################################

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
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    prompt_text = Column(Text, nullable=False)
    is_archived = Column(Boolean, default=False)
    tags = Column(Text, nullable=True)  # Comma-separated list of tags
    current_version_id = Column(
        Integer, ForeignKey("prompt_versions.id"), nullable=True
    )

    created_at = Column(DateTime, default=datetime.now(tz=timezone.utc))
    updated_at = Column(
        DateTime, default=datetime.now(tz=timezone.utc), onupdate=datetime.now(tz=timezone.utc)
    )

    # Relationships
    versions = relationship(
        "PromptVersion",
        back_populates="prompt",
        cascade="all, delete-orphan",
        foreign_keys="PromptVersion.prompt_id",
    )

    # User who created this prompt
    creator = relationship("Users", back_populates="prompts", foreign_keys=[created_by])

    # Owning tenant
    tenant = relationship("Tenants", back_populates="prompts", foreign_keys=[tenant_id])


class PromptVersion(Base):
    """
    Represents a specific version of a Prompt.

    Attributes:
        id (int): Auto-increment primary key.
        prompt_id (int): Foreign key to parent Prompt.
        version_number (int): Incremental version number (unique per prompt).
        prompt_text (str): Versioned content of the prompt.
        created_by (int): Foreign key to user who created this version.
        created_at (datetime): Creation timestamp.
    """

    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(
        Integer, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False
    )
    version_number = Column(Integer, nullable=False)
    prompt_text = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now(tz=timezone.utc))

    __table_args__ = (
        UniqueConstraint("prompt_id", "version_number", name="uq_prompt_version"),
    )

    # Relationships
    prompt = relationship("Prompt", back_populates="versions", foreign_keys=[prompt_id])
    creator = relationship("Users", back_populates="prompt_versions", foreign_keys=[created_by])


#######################################
# User Management Models
#######################################

class Users(Base):
    """
    Represents a User entity.

    Attributes:
        id (int): Auto-increment primary key.
        username (str): Unique username for the user.
        email (str): Email address of the user.
        created_at (datetime): Account creation timestamp.
        updated_at (datetime): Last update timestamp.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    status = Column(String, default="active")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(tz=timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(tz=timezone.utc))

    # Relationships
    prompts = relationship("Prompt", back_populates="creator", foreign_keys="[Prompt.created_by]")
    prompt_versions = relationship("PromptVersion", back_populates="creator", foreign_keys="[PromptVersion.created_by]")
    tenants = relationship("Tenants", back_populates="users", foreign_keys="[Users.tenant_id]")


class Tenants(Base):
    """
    Represents a Tenant entity.

    Attributes:
        id (int): Auto-increment primary key.
        name (str): Name of the tenant.
        created_at (datetime): Account creation timestamp.
        updated_at (datetime): Last update timestamp.
    """

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(tz=timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(tz=timezone.utc))

    # Relationships
    users = relationship("Users", back_populates="tenants", foreign_keys="[Users.tenant_id]")
    prompts = relationship("Prompt", back_populates="tenant", foreign_keys="[Prompt.tenant_id]")
