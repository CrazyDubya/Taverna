"""Service for managing game sessions and states."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlmodel import select, or_
from sqlalchemy.orm import Session
import uuid

from core.models.persistence_models import GameStatePersistence, GameStateCreate, GameStateUpdate, GameSession
from core.db.session import get_session


class SessionService:
    """Service for managing game sessions and states."""

    def __init__(self, session: Session):
        """Initialize with a database session."""
        self.session = session

    # Game State Methods

    def create_game_state(
        self, player_name: str, session_id: str, game_data: Optional[Dict[str, Any]] = None
    ) -> GameStatePersistence:
        """Create a new game state."""
        game_state = GameStatePersistence(
            player_name=player_name, session_id=session_id, game_data=game_data or {}, inventory=[], flags={}
        )
        self.session.add(game_state)
        self.session.commit()
        self.session.refresh(game_state)
        return game_state

    def get_game_state(self, state_id: str) -> Optional[GameStatePersistence]:
        """Get a game state by ID."""
        return self.session.get(GameStatePersistence, state_id)

    def update_game_state(self, state_id: str, game_data: Dict[str, Any]) -> Optional[GameStatePersistence]:
        """Update a game state with full game data."""
        game_state = self.get_game_state(state_id)
        if not game_state:
            return None

        game_state.game_data = game_data
        game_state.updated_at = datetime.utcnow()
        self.session.add(game_state)
        self.session.commit()
        self.session.refresh(game_state)
        return game_state

    def save_game_state_data(
        self, session_id: str, game_data: Dict[str, Any], player_name: str = "Unknown"
    ) -> Optional[GameStatePersistence]:
        """Save or update game state data for a session."""
        # Try to find existing state by session_id
        existing_state = self.session.exec(
            select(GameStatePersistence).where(GameStatePersistence.session_id == session_id)
        ).first()

        if existing_state:
            return self.update_game_state(existing_state.id, game_data)
        else:
            return self.create_game_state(player_name, session_id, game_data)

    # Session Management

    def create_session(self, user_id: str, player_name: str, metadata: Optional[Dict[str, Any]] = None) -> GameSession:
        """Create a new game session."""
        # Create game state first
        session_id = str(uuid.uuid4())
        game_state = self.create_game_state(player_name, session_id)

        # Create session
        session = GameSession(user_id=user_id, game_state_id=game_state.id, metadata_=metadata or {})
        self.session.add(session)
        self.session.commit()
        self.session.refresh(session)
        return session

    def get_session(self, session_id: str) -> Optional[GameSession]:
        """Get a session by ID."""
        return self.session.get(GameSession, session_id)

    def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[GameSession]:
        """Get all sessions for a user."""
        query = select(GameSession).where(GameSession.user_id == user_id)
        if active_only:
            query = query.where(GameSession.is_active == True)
        return self.session.exec(query).all()

    def update_session_activity(self, session_id: str) -> Optional[GameSession]:
        """Update the last activity timestamp for a session."""
        session = self.get_session(session_id)
        if not session:
            return None

        session.last_activity = datetime.utcnow()
        self.session.add(session)
        self.session.commit()
        self.session.refresh(session)
        return session

    def end_session(self, session_id: str) -> Optional[GameSession]:
        """Mark a session as inactive."""
        session = self.get_session(session_id)
        if not session:
            return None

        session.is_active = False
        self.session.add(session)
        self.session.commit()
        self.session.refresh(session)
        return session

    def cleanup_inactive_sessions(self, days_inactive: int = 30) -> int:
        """Clean up sessions inactive for more than X days."""
        cutoff = datetime.utcnow() - timedelta(days=days_inactive)
        result = self.session.execute(
            select(GameSession).where(GameSession.is_active == False, GameSession.last_activity < cutoff)  # noqa: E712
        )

        count = 0
        for session in result.scalars():
            self.session.delete(session)
            count += 1

        if count > 0:
            self.session.commit()

        return count
