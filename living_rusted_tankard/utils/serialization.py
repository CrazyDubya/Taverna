"""
Serialization utilities for The Living Rusted Tankard game.
Handles saving/loading game state to/from JSON.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.game_state import GameState

    # Assuming Narrator and CommandParser types would be imported if they were actual classes
    # from core.llm.narrator import Narrator
    # from core.llm.parser import CommandParser


# The Serializable class and its direct usage can be phased out
# as Pydantic models have their own to_dict (model_dump) and from_dict (model_validate).


def save_game_state(
    game_state_instance: "GameState",
    save_dir: str = "saves",
    filename_base: Optional[str] = None,
) -> str:
    """
    Save game state to a JSON file using GameState.to_dict().

    Args:
        game_state_instance: The GameState object to save.
        save_dir: Directory to save the game state.
        filename_base: Optional base for the filename. If None, a timestamp is used.
                       .json extension will be added.

    Returns:
        Path to the saved file.
    """
    os.makedirs(save_dir, exist_ok=True)

    if filename_base:
        # Ensure it ends with .json, but first remove if it's already there to avoid .json.json
        if filename_base.endswith(".json"):
            filename_base = filename_base[:-5]
        filename = f"{filename_base}.json"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"save_{timestamp}.json"

    filepath = Path(save_dir) / filename

    try:
        # GameState.to_dict() should produce a JSON-serializable dictionary
        # Pydantic's model_dump(mode='json') handles complex types like datetime, enums.
        state_dict = game_state_instance.to_dict()

        with open(filepath, "w") as f:
            json.dump(state_dict, f, indent=2)

        return str(filepath)
    except Exception as e:
        # Log the exception for better debugging
        print(f"Error during save_game_state: {type(e).__name__} - {e}")
        raise RuntimeError(f"Failed to save game state: {str(e)}")


def load_game_state(
    filepath: str,
    narrator: Any,  # Replace Any with actual Narrator type hint
    command_parser: Any,  # Replace Any with actual CommandParser type hint
    data_dir: str = "data",  # data_dir needed for GameState.from_dict
) -> "GameState":
    """
    Load game state from a JSON file using GameState.from_dict().

    Args:
        filepath: Path to the save file.
        narrator: Initialized Narrator instance.
        command_parser: Initialized CommandParser instance.
        data_dir: Path to the game's data directory.

    Returns:
        Deserialized GameState object.
    """
    try:
        with open(filepath, "r") as f:
            data_dict = json.load(f)

        # Need to import GameState here to avoid circular imports at module level
        from core.game_state import GameState

        # GameState.from_dict will handle reconstruction
        game_state_instance = GameState.from_dict(
            data_dict,
            narrator=narrator,
            command_parser=command_parser,
            data_dir=data_dir,
        )
        return game_state_instance
    except Exception as e:
        # Log the exception for better debugging
        print(f"Error during load_game_state: {type(e).__name__} - {e}")
        raise RuntimeError(f"Failed to load game state: {str(e)}")


def get_latest_save(save_dir: str = "saves") -> Optional[str]:
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

        save_files = list(save_dir.glob("save_*.json"))
        if not save_files:
            return None

        latest_save = max(save_files, key=os.path.getmtime)
        return str(latest_save)
    except Exception as e:
        print(f"Warning: Failed to find latest save: {str(e)}")
        return None
