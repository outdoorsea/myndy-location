"""
Database Connection Management
File: database/connection.py

Handles PostgreSQL connections and session management.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://location_user:password@localhost:5435/location_intelligence",
)

# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Session:
    """
    Get database session (dependency injection for FastAPI)

    Usage:
        from fastapi import Depends
        def my_endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create tables if needed)"""
    try:
        # Import all models to register them
        from database import models  # noqa: F401

        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


def get_db_session() -> Session:
    """Get a new database session (for direct use outside FastAPI)"""
    return SessionLocal()
