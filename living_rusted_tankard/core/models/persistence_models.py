"""Persistence models for database storage using SQLModel."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON, String, DateTime
import uuid


class GameStateBase(SQLModel):
    """Base model for game state."""

    player_name: str = Field(index=True)
    current_room: str = Field(default="tavern_main")
    inventory: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    flags: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, onupdate=datetime.utcnow))


class GameStatePersistence(GameStateBase, table=True):
    """Game state persistence model for the database."""

    __tablename__ = "game_states"

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    session_id: str = Field(index=True)
    game_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


# Backwards compatibility
GameState = GameStatePersistence


class GameStateCreate(GameStateBase):
    """Model for creating a new game state."""

    pass


class GameStateUpdate(SQLModel):
    """Model for updating an existing game state."""

    current_room: Optional[str] = None
    inventory: Optional[List[str]] = None
    flags: Optional[Dict[str, Any]] = None


class GameSession(SQLModel, table=True):
    """Game session model."""

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    user_id: str = Field(index=True)
    game_state_id: str = Field(foreign_key="gamestate.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata_: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
