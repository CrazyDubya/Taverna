"""
AI Player Manager - Session-based AI player management without global state.

This module provides proper session isolation for AI players, replacing the
problematic global state pattern with a clean session-based approach.
"""

import uuid
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

from .ai_player import AIPlayer, AIPlayerPersonality

logger = logging.getLogger(__name__)


@dataclass
class AIPlayerSession:
    """Container for an AI player session with metadata."""

    session_id: str
    ai_player: AIPlayer
    created_at: datetime
    last_activity: datetime
    is_active: bool = True
    auto_play: bool = False

    def mark_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = datetime.now()

    async def deactivate(self):
        """Deactivate the session and clean up resources."""
        self.is_active = False
        self.auto_play = False
        self.ai_player.is_active = False

        # Clean up HTTP resources
        await self.ai_player.close()


class AIPlayerManager:
    """
    Manages multiple AI player sessions without global state.

    This replaces the problematic global _ai_player pattern with proper
    session isolation and resource management.
    """

    def __init__(self):
        self._sessions: Dict[str, AIPlayerSession] = {}
        self._cleanup_threshold = 3600  # Remove inactive sessions after 1 hour

    def create_session(
        self,
        personality: AIPlayerPersonality,
        name: Optional[str] = None,
        model: str = "gemma2:2b",
        session_id: Optional[str] = None,
    ) -> AIPlayerSession:
        """
        Create a new AI player session.

        Args:
            personality: The AI player personality
            name: Optional name for the AI player
            model: LLM model to use
            session_id: Optional specific session ID (generates UUID if None)

        Returns:
            AIPlayerSession with the created AI player
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        if session_id in self._sessions:
            raise ValueError(f"Session {session_id} already exists")

        # Create AI player instance
        ai_player = AIPlayer(
            name=name or f"AI-{personality.value}", personality=personality, model=model
        )
        ai_player.session_id = session_id

        # Create session
        now = datetime.now()
        session = AIPlayerSession(
            session_id=session_id,
            ai_player=ai_player,
            created_at=now,
            last_activity=now,
            is_active=True,
        )

        self._sessions[session_id] = session
        logger.info(
            f"Created AI player session {session_id} with personality {personality.value}"
        )

        return session

    def get_session(self, session_id: str) -> Optional[AIPlayerSession]:
        """
        Get an AI player session by ID.

        Args:
            session_id: The session identifier

        Returns:
            AIPlayerSession if found, None otherwise
        """
        session = self._sessions.get(session_id)
        if session and session.is_active:
            session.mark_activity()
            return session
        return None

    def get_ai_player(self, session_id: str) -> Optional[AIPlayer]:
        """
        Get an AI player by session ID.

        Args:
            session_id: The session identifier

        Returns:
            AIPlayer if session exists and is active, None otherwise
        """
        session = self.get_session(session_id)
        return session.ai_player if session else None

    def list_active_sessions(self) -> List[AIPlayerSession]:
        """
        Get all active AI player sessions.

        Returns:
            List of active AIPlayerSession objects
        """
        return [session for session in self._sessions.values() if session.is_active]

    async def deactivate_session(self, session_id: str) -> bool:
        """
        Deactivate an AI player session.

        Args:
            session_id: The session identifier

        Returns:
            True if session was deactivated, False if not found
        """
        session = self._sessions.get(session_id)
        if session:
            await session.deactivate()
            logger.info(f"Deactivated AI player session {session_id}")
            return True
        return False

    async def cleanup_inactive_sessions(self) -> int:
        """
        Remove old inactive sessions to prevent memory leaks.

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        to_remove = []

        for session_id, session in self._sessions.items():
            if (
                not session.is_active
                and (now - session.last_activity).total_seconds()
                > self._cleanup_threshold
            ):
                to_remove.append((session_id, session))

        for session_id, session in to_remove:
            # Properly clean up resources
            await session.deactivate()
            del self._sessions[session_id]
            logger.info(f"Cleaned up inactive session {session_id}")

        return len(to_remove)

    def get_session_count(self) -> Dict[str, int]:
        """
        Get count of sessions by status.

        Returns:
            Dictionary with 'active' and 'total' counts
        """
        active_count = sum(1 for s in self._sessions.values() if s.is_active)
        return {"active": active_count, "total": len(self._sessions)}

    async def clear_all_sessions(self):
        """Clear all sessions - primarily for testing."""
        sessions_to_clear = list(self._sessions.values())
        for session in sessions_to_clear:
            await session.deactivate()
        self._sessions.clear()
        logger.info("Cleared all AI player sessions")


# Global manager instance - this is acceptable because it manages sessions
# rather than containing game state
_ai_player_manager = AIPlayerManager()


def get_ai_player_manager() -> AIPlayerManager:
    """
    Get the global AI player manager instance.

    Note: This global is acceptable because it's a manager/factory,
    not game state. Each session is properly isolated.
    """
    return _ai_player_manager


def create_ai_player_session(
    personality: AIPlayerPersonality,
    name: Optional[str] = None,
    model: str = "gemma2:2b",
) -> AIPlayerSession:
    """
    Convenience function to create an AI player session.

    Args:
        personality: The AI player personality
        name: Optional name for the AI player
        model: LLM model to use

    Returns:
        AIPlayerSession with the created AI player
    """
    return get_ai_player_manager().create_ai_player_session(
        personality=personality, name=name, model=model
    )
