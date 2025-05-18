"""API endpoints for session management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from core.models.game_state import GameState, GameStateCreate, GameStateUpdate, GameSession
from core.services.session_service import SessionService
from ..deps import get_session_service

router = APIRouter()

@router.post("/sessions/", response_model=GameSession)
def create_session(
    player_name: str,
    user_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Create a new game session."""
    return session_service.create_session(
        user_id=user_id,
        player_name=player_name
    )

@router.get("/sessions/{session_id}", response_model=GameSession)
def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Get a session by ID."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session

@router.get("/users/{user_id}/sessions/", response_model=list[GameSession])
def list_user_sessions(
    user_id: str,
    active_only: bool = True,
    session_service: SessionService = Depends(get_session_service)
):
    """List all sessions for a user."""
    return session_service.get_user_sessions(
        user_id=user_id,
        active_only=active_only
    )

@router.post("/sessions/{session_id}/end", response_model=GameSession)
def end_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """End a session."""
    session = session_service.end_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session

@router.get("/game-states/{state_id}", response_model=GameState)
def get_game_state(
    state_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Get a game state by ID."""
    game_state = session_service.get_game_state(state_id)
    if not game_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game state not found"
        )
    return game_state

@router.patch("/game-states/{state_id}", response_model=GameState)
def update_game_state(
    state_id: str,
    update_data: GameStateUpdate,
    session_service: SessionService = Depends(get_session_service)
):
    """Update a game state."""
    game_state = session_service.update_game_state(state_id, update_data)
    if not game_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game state not found"
        )
    return game_state
