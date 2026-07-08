"""
Database Connection - SQLite with SQLAlchemy

Uses SQLite for simplicity (no Docker/PostgreSQL setup needed).
To switch to PostgreSQL, just change DATABASE_URL to:
  postgresql://user:password@localhost:5432/codecarbonops
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database file location (project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATABASE_PATH = PROJECT_ROOT / "codecarbonops.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def init_db():
    """Create all database tables if they don't exist."""
    from backend.database.models import InferenceRun, OffsetPurchase, CarbonCache  # noqa
    Base.metadata.create_all(bind=engine)
    print(f"[OK] Database initialized at: {DATABASE_PATH}")


def get_db():
    """Get a database session (for use as dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
