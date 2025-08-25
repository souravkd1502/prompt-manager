"""
Database initialization and synchronous session management.
===========================================================

Summary
-----------
This module provides synchronous database engine initialization, session
management, and dependency injection for FastAPI routes.

Functionality
----------------
- Defines SQLAlchemy synchronous engine and base declarative class.
- Provides `init_db` to initialize tables.
- Provides `get_db` as a dependency for request-scoped DB sessions.

Usage
---------
1. Import `get_db` in FastAPI routes to use as a dependency.
2. Call `init_db` on application startup for table creation.
3. Extend `Base` for all ORM models.

Requirements
-----------------
- SQLAlchemy >= 2.0
- Databases supported: SQLite, PostgreSQL, MySQL
    * SQLite: sqlite3
    * PostgreSQL: psycopg2
    * MySQL: pymysql

TODO
--------
- Add connection pooling configuration for production.
- Implement Alembic migrations instead of direct `create_all`.

FIXME
--------
- None for synchronous implementation.

Created By
-------------
Sourav Das

Date
--------
2025-08-19
"""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import SQLAlchemyError

from .config import settings

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# SQLAlchemy Declarative Base
Base = declarative_base()

# Convert async URL to sync URL
database_url = settings.DATABASE_URL
if database_url.startswith("sqlite+aiosqlite"):
    database_url = database_url.replace("sqlite+aiosqlite", "sqlite")
elif database_url.startswith("postgresql+asyncpg"):
    database_url = database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
elif database_url.startswith("mysql+aiomysql"):
    database_url = database_url.replace("mysql+aiomysql", "mysql+pymysql")

# Synchronous Engine
try:
    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}
        if database_url.startswith("sqlite")
        else {},
    )
    logger.info("Database engine initialized successfully.")
except SQLAlchemyError as e:
    logger.exception("Failed to initialize database engine: %s", e)
    raise

# Synchronous SessionLocal factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    autocommit=False,
)


def init_db() -> None:
    """
    Initialize database models and create tables if they do not exist.

    Raises
    -------
    SQLAlchemyError
        If table creation fails.
    """
    try:
        from backend.models import prompt  

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except SQLAlchemyError as e:
        logger.exception("Database initialization failed: %s", e)
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Provides a synchronous transactional session for request handling.

    Yields
    -------
    Session
        Database session to be used inside FastAPI endpoints.

    Ensures
    -------
    - Session is properly closed after request.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.exception("Database session error: %s", e)
        db.rollback()
        raise
    finally:
        db.close()
