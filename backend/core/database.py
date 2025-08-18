"""
Database initialization and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# SQLAlchemy Base
Base = declarative_base()

# Engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite only
    if settings.DATABASE_URL.startswith("sqlite") else {}
)

# SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database models and create tables if not exist.
    """
    from backend.models import prompt  # Import models so they register with Base
    Base.metadata.create_all(bind=engine)


# Dependency (for FastAPI endpoints)
def get_db():
    """
    Provides a transactional scope around a series of operations.
    Yields a SQLAlchemy session for request handling.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
