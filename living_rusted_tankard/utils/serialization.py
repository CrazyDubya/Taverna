"""
Serialization utilities for The Living Rusted Tankard game.
Handles saving/loading game state to/from JSON.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Type, TypeVar, Generic
from dataclasses import asdict, is_dataclass

T = TypeVar('T')

class Serializable:
    """Base class for serializable objects."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert object to a dictionary."""
        if is_dataclass(self):
            return asdict(self)
        return {}

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create object from dictionary."""
        return cls(**data)  # type: ignore


def save_game_state(state: Dict[str, Any], save_dir: str = 'saves') -> str:
    """
    Save game state to a JSON file.

    Args:
        state: Game state dictionary to save
        save_dir: Directory to save the game state

    Returns:
        Path to the saved file
    """
    # Ensure save directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Create a timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'save_{timestamp}.json'
    filepath = Path(save_dir) / filename

    try:
        # Convert any Serializable objects to dicts
        def serialize(obj):
            if isinstance(obj, Serializable):
                return obj.to_dict()
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [serialize(item) for item in obj]
            return obj

        serialized_state = serialize(state)

        # Save to file
        with open(filepath, 'w') as f:
            json.dump(serialized_state, f, indent=2)

        return str(filepath)
    except Exception as e:
        raise RuntimeError(f"Failed to save game state: {str(e)}")


def load_game_state(filepath: str) -> Dict[str, Any]:
    """
    Load game state from a JSON file.

    Args:
        filepath: Path to the save file

    Returns:
        Deserialized game state
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load game state: {str(e)}")


def get_latest_save(save_dir: str = 'saves') -> Optional[str]:
    """
    Get the most recent save file.

    Args:
        save_dir: Directory containing save files

    Returns:
        Path to the most recent save file, or None if no saves exist
    """
    try:
        save_dir = Path(save_dir)
        if not save_dir.exists():
            return None

        save_files = list(save_dir.glob('save_*.json'))
        if not save_files:
            return None

        latest_save = max(save_files, key=os.path.getmtime)
        return str(latest_save)
    except Exception as e:
        print(f"Warning: Failed to find latest save: {str(e)}")
        return None

