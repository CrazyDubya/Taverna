"""
Database-aware GameState that extends the main GameState with persistence capabilities.

This approach preserves the existing GameState implementation while adding 
database persistence features for session management.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON, DateTime
import uuid

from .game_state import GameState as CoreGameState
from .models.game_state import GameStatePersistence

class DatabaseGameState(CoreGameState):
    """
    GameState with database persistence capabilities.
    
    This class extends the core GameState with methods to:
    - Save/load from database via SQLModel
    - Track persistence state
    - Manage session IDs
    """
    
    def __init__(self, data_dir: str = "data", session_id: Optional[str] = None, db_id: Optional[str] = None):
        """Initialize with optional session and database IDs."""
        super().__init__(data_dir)
        self._session_id = session_id or str(uuid.uuid4())
        self._db_id = db_id
        self._needs_save = True
        
    @property
    def session_id(self) -> str:
        """Get the session ID."""
        return self._session_id
    
    @property 
    def db_id(self) -> Optional[str]:
        """Get the database ID if persisted."""
        return self._db_id
        
    def set_db_id(self, db_id: str) -> None:
        """Set the database ID after persistence."""
        self._db_id = db_id
        
    def mark_dirty(self) -> None:
        """Mark state as needing database save."""
        self._needs_save = True
        
    def mark_clean(self) -> None:
        """Mark state as clean (saved to database)."""
        self._needs_save = False
        
    def needs_save(self) -> bool:
        """Check if state needs to be saved to database."""
        return self._needs_save
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary, including session info."""
        data = super().to_dict()
        data.update({
            "session_id": self._session_id,
            "db_id": self._db_id,
            "serialized_at": datetime.utcnow().isoformat()
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], narrator: Optional[Any] = None, command_parser: Optional[Any] = None, data_dir: str = "data") -> 'DatabaseGameState':
        """Deserialize from dictionary with session info."""
        session_id = data.get("session_id")
        db_id = data.get("db_id")
        
        # Create instance using parent's from_dict, then convert to DatabaseGameState
        parent_instance = super().from_dict(data, narrator, command_parser, data_dir)
        
        # Create new DatabaseGameState with same state
        db_instance = cls(data_dir=data_dir, session_id=session_id, db_id=db_id)
        
        # Copy all attributes from parent instance
        for attr_name in dir(parent_instance):
            if not attr_name.startswith('_') and not callable(getattr(parent_instance, attr_name)):
                setattr(db_instance, attr_name, getattr(parent_instance, attr_name))
        
        # Copy private attributes that matter
        db_instance._last_update_time = parent_instance._last_update_time
        db_instance._observers = parent_instance._observers
        db_instance._present_npcs = parent_instance._present_npcs
        db_instance._data_dir = parent_instance._data_dir
        
        db_instance.mark_clean()  # Just loaded, so it's clean
        return db_instance
    
    def to_persistence_model(self) -> 'GameStatePersistence':
        """Convert to database persistence model.""" 
        return GameStatePersistence(
            id=self._db_id,
            session_id=self._session_id,
            player_name=getattr(self.player, 'name', 'Unknown Player'),
            game_data=self.to_dict(),
            updated_at=datetime.utcnow()
        )
    
    @classmethod
    def from_persistence_model(cls, model: 'GameStatePersistence', data_dir: str = "data") -> 'DatabaseGameState':
        """Create from database persistence model."""
        instance = cls.from_dict(model.game_data, data_dir=data_dir)
        instance.set_db_id(model.id)
        instance.mark_clean()
        return instance
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """Process command and mark state as dirty."""
        result = super().process_command(command)
        self.mark_dirty()  # Any command changes state
        return result
    
    def update(self, delta_override: Optional[float] = None) -> None:
        """Update game state and mark as dirty."""
        super().update(delta_override)
        self.mark_dirty()  # Updates change state

# For backwards compatibility and easy importing
GameState = DatabaseGameState