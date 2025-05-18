"""Dependencies for FastAPI routes."""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from core.db.session import SessionLocal, get_session
from core.services.session_service import SessionService

def get_db() -> Generator[Session, None, None]:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_session_service(
    db: Session = Depends(get_db)
) -> SessionService:
    """Get a session service instance."""
    return SessionService(db)

def get_current_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
) -> dict:
    """Get the current game session or raise 404 if not found."""
    session = session_service.get_session(session_id)
    if not session or not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or inactive"
        )
    return session
