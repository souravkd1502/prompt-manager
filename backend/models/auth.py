"""
SQLAlchemy models for authentication and user/tenant management.

This module defines the database schema for handling multi-tenant user management,
authentication, roles, refresh tokens, and API keys.
"""

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.core.database import Base


class Tenant(Base):
    """
    Represents a Tenant in a multi-tenant system.

    Attributes:
        id (str): Unique identifier (UUID stored as string).
        name (str): Unique tenant name.
        settings (str): JSON string for tenant-specific settings.
        created_at (datetime): Timestamp of creation (UTC).
    """

    __tablename__ = "tenants"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    settings = Column(Text, default="{}")  # JSON string for dynamic tenant settings
    created_at = Column(DateTime, default=lambda: datetime.now(tz=timezone.utc))

    # Relationships
    users = relationship(
        "Membership", back_populates="tenant", cascade="all, delete-orphan"
    )
    api_keys = relationship(
        "ApiKey", back_populates="tenant", cascade="all, delete-orphan"
    )


class User(Base):
    """
    Represents an application User.

    Attributes:
        id (str): Unique identifier (UUID stored as string).
        email (str): Unique user email (case-insensitive validation handled at app level).
        password_hash (str): Hashed password.
        name (str): Optional display name.
        status (str): User status (default: active).
        created_at (datetime): Timestamp of creation (UTC).
    """

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(
        String, unique=True, nullable=False, index=True
    )  # Ensure uniqueness at DB level
    password_hash = Column(Text, nullable=False)
    name = Column(String, nullable=True)
    status = Column(String, default="active")  # Can extend for suspended, deleted, etc.
    created_at = Column(DateTime, default=lambda: datetime.now(tz=timezone.utc))

    # Relationships
    memberships = relationship(
        "Membership", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


class Membership(Base):
    """
    Association table mapping Users to Tenants with assigned roles.

    Attributes:
        user_id (str): Foreign key to User.
        tenant_id (str): Foreign key to Tenant.
        role (str): User role within the tenant (admin, editor, viewer).
    """

    __tablename__ = "memberships"

    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    tenant_id = Column(
        String, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    role = Column(String, nullable=False)

    # Constraint ensures role is one of the allowed values
    __table_args__ = (
        CheckConstraint("role IN ('admin','editor','viewer')", name="role_check"),
    )

    # Relationships
    user = relationship("User", back_populates="memberships")
    tenant = relationship("Tenant", back_populates="users")


class RefreshToken(Base):
    """
    Represents a Refresh Token for authentication.

    Attributes:
        id (str): Unique identifier (UUID stored as string).
        user_id (str): Foreign key to User.
        token_hash (str): Hashed refresh token for security.
        expires_at (datetime): Expiration time of the token.
        revoked (bool): Indicates whether the token is revoked.
        created_at (datetime): Timestamp when issued (UTC).
    """

    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(tz=timezone.utc))

    # Relationship back to User
    user = relationship("User", back_populates="refresh_tokens")


class ApiKey(Base):
    """
    Represents an API Key for programmatic access.

    Attributes:
        id (str): Unique identifier (UUID stored as string).
        tenant_id (str): Foreign key to Tenant.
        name (str): Human-readable name for identifying the API key.
        hash (str): Secure hash of the API key (stored instead of raw key).
        prefix (str): Key prefix for easier identification/logging.
        created_at (datetime): Timestamp of creation (UTC).
        last_used_at (datetime): Last time this key was used (nullable).
    """

    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(
        String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    hash = Column(
        Text, unique=True, nullable=False
    )  # Hash ensures security & uniqueness
    prefix = Column(String, nullable=False)  # Prefix aids debugging/logging
    created_at = Column(DateTime, default=lambda: datetime.now(tz=timezone.utc))
    last_used_at = Column(DateTime, nullable=True)

    # Relationship back to Tenant
    tenant = relationship("Tenant", back_populates="api_keys")
