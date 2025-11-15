from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .game_state import GameState
    from .npc import NPC
    from .room import RoomManager


@dataclass
class GameSnapshot:
    """A lightweight, serializable snapshot of the game state for the parser."""

    time: float  # Current game time in hours (raw decimal)
    formatted_time: str  # Natural fantasy time display
    present_npcs: List[Dict[str, Any]]  # Currently present NPCs
    board_notes: List[str]  # Currently visible board notes
    player: Dict[str, Any]  # Player state
    location: str  # Current location (always "tavern" for now)


class SnapshotManager:
    """Manages creation of game state snapshots for the parser."""

    def __init__(self, game_state):
        self.game_state = game_state

    def create_snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of the current game state for the parser.

        Returns:
            Dict containing the minimal structured data needed by the parser.
        """
        # Get present NPCs with their basic info
        present_npcs = []
        for npc in self._get_present_npcs():
            present_npcs.append(
                {
                    "id": npc.id,
                    "name": npc.name,
                    "description": npc.description,
                    "mood": npc.mood if hasattr(npc, "mood") else "neutral",
                    "last_interaction_time": npc.last_interaction_time if hasattr(npc, "last_interaction_time") else 0,
                }
            )

        # Get visible board notes (simplified for now)
        board_notes = self._get_visible_board_notes()

        # Create player state snapshot
        player_inventory = []
        if hasattr(self.game_state.player, "inventory"):
            inventory = self.game_state.player.inventory
            if hasattr(inventory, "items") and isinstance(inventory.items, dict):
                for _, inv_item in inventory.items.items():
                    if hasattr(inv_item, "item") and hasattr(inv_item, "quantity"):
                        player_inventory.append({"name": inv_item.item.name, "quantity": inv_item.quantity})

        player_state = {
            "gold": self.game_state.player.gold,
            "has_room": self.game_state.player.has_room,
            "tiredness": getattr(self.game_state.player, "tiredness", 0),
            "inventory": player_inventory,
        }

        # Create and return the snapshot
        try:
            if hasattr(self.game_state.clock, "get_time"):
                time_value = self.game_state.clock.get_time()
            elif hasattr(self.game_state.clock, "get_current_time"):
                time_value = self.game_state.clock.get_current_time().hours
            elif hasattr(self.game_state.clock, "current_time"):
                time_value = self.game_state.clock.current_time.hours
            else:
                time_value = 0.0
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"Failed to parse time value: {e}")
            time_value = 0.0

        # Get formatted natural time
        formatted_time = "Unknown time"
        try:
            from .time_display import format_time_for_display

            formatted_time = format_time_for_display(time_value, "ui_main")
        except Exception:
            # Fallback to clock's formatted time if available
            try:
                if hasattr(self.game_state.clock, "get_formatted_time"):
                    formatted_time = self.game_state.clock.get_formatted_time()
                elif hasattr(self.game_state.clock, "current_time"):
                    formatted_time = self.game_state.clock.current_time.format_time()
            except Exception:
                formatted_time = f"Day {int(time_value // 24) + 1}"

        snapshot = GameSnapshot(
            time=time_value,
            formatted_time=formatted_time,
            present_npcs=present_npcs,
            board_notes=board_notes,
            player=player_state,
            location="tavern",  # Hardcoded for now
        )

        return asdict(snapshot)

    def _get_present_npcs(self) -> List["NPC"]:
        """Get a list of currently present NPCs."""
        from .npc import NPC  # Import here to avoid circular import

        if hasattr(self.game_state, "npc_manager") and hasattr(self.game_state.npc_manager, "npcs"):
            npcs_dict = self.game_state.npc_manager.npcs
            if isinstance(npcs_dict, dict):
                return [npc for npc in npcs_dict.values() if hasattr(npc, "is_present") and npc.is_present]
        return []

    def _get_visible_board_notes(self) -> List[str]:
        """Get currently visible board notes."""
        # This is a stub - implement based on your board/note system
        if hasattr(self.game_state, "bulletin_board"):
            board = getattr(self.game_state, "bulletin_board")
            if hasattr(board, "get_visible_notes"):
                notes = board.get_visible_notes()
                return [getattr(note, "content", str(note)) for note in notes]
        return []
