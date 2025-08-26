"""
SQLAlchemy models for authentication and user/tenant management.

This module defines the database schema for:
- Tenant (multi-tenant ownership)
- User (application users)
- Membership (role-based tenant membership)
- RefreshToken (authentication refresh tokens)
- ApiKey (programmatic access keys)
"""

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Integer,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.core.database import Base


class Tenant(Base):
    """
    Represents a Tenant in a multi-tenant system.
    """

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    settings = Column(Text, default="{}")  # JSON string for tenant-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("Membership", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """
    Represents an application User.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    name = Column(String, nullable=True)
    status = Column(String, default="active")  # Possible values: active, suspended, deleted
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class Membership(Base):
    """
    Association table mapping Users to Tenants with assigned roles.
    """

    __tablename__ = "memberships"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String, nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('admin','editor','viewer')", name="role_check"),
    )

    # Relationships
    user = relationship("User", back_populates="memberships")
    tenant = relationship("Tenant", back_populates="users")


class RefreshToken(Base):
    """
    Represents a Refresh Token for authentication.
    """

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to User
    user = relationship("User", back_populates="refresh_tokens")


class ApiKey(Base):
    """
    Represents an API Key for programmatic access.
    """

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    hash = Column(Text, unique=True, nullable=False)  # Stored as secure hash
    prefix = Column(String, nullable=False)          # Useful for logging/debugging
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationship back to Tenant
    tenant = relationship("Tenant", back_populates="api_keys")
