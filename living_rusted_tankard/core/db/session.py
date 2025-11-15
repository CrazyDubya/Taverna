"""Database session management."""

from typing import Generator, Optional
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Database URL - using SQLite for simplicity
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taverna.db")

# Create engine
engine = create_engine(
    DATABASE_URL, echo=True, connect_args={"check_same_thread": False}  # Set to False in production  # SQLite specific
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def init_db():
    """Initialize the database."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseSession:
    """Database session manager class."""

    def __init__(self):
        self.session_factory = SessionLocal

    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session."""
        return get_session()

    def create_all(self):
        """Create all database tables."""
        SQLModel.metadata.create_all(engine)
