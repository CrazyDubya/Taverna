from typing import List, Dict, Any, Optional, TYPE_CHECKING, Type, TypeVar, Tuple
from pydantic import BaseModel, Field
import uuid
import sys
import os

# Add the parent directory to the path to allow import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if TYPE_CHECKING:
    from ..core.clock import GameClock
    from .npc_state import NPCState

# Import configuration
try:
    from core.config import CONFIG
except ImportError:
    # Fallback if config not available
    class FallbackConfig:
        STARTING_GOLD = 40
        MAX_TIREDNESS = 100

    CONFIG = FallbackConfig()

T = TypeVar("T")


class Inventory(BaseModel):
    """Tracks the player's items."""

    items: Dict[str, int] = Field(default_factory=dict)  # item_name: quantity

    def add_item(self, item_name: str, quantity: int = 1) -> None:
        """Add items to inventory."""
        self.items[item_name] = self.items.get(item_name, 0) + quantity

    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """Remove items from inventory. Returns True if successful."""
        if self.items.get(item_name, 0) < quantity:
            return False
        self.items[item_name] -= quantity
        if self.items[item_name] <= 0:
            del self.items[item_name]
        return True

    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Check if player has at least quantity of item."""
        return self.items.get(item_name, 0) >= quantity


class PlayerState(BaseModel):
    """Tracks all player-specific state."""

    player_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Traveler"
    gold: int = Field(default_factory=lambda: CONFIG.STARTING_GOLD)
    inventory: Inventory = Field(default_factory=Inventory)
    has_room: bool = False
    room_number: Optional[str] = None
    tiredness: float = 0.0  # 0-CONFIG.MAX_TIREDNESS scale
    rest_immune: bool = False  # For the no-sleep meta-quest
    flags: Dict[str, Any] = Field(
        default_factory=dict
    )  # For tracking quest states, etc.
    energy: float = 1.0  # 0.0 to 1.0 scale
    last_ate: float = 0.0  # Game time when player last ate
    last_drank: float = 0.0  # Game time when player last drank

    # Properties
    @property
    def id(self) -> str:
        """Get the player's unique ID."""
        return self.player_id

    # Private attributes
    no_sleep_quest_unlocked_internal: bool = Field(default=False)
    npc_state_internal: Optional[Any] = Field(default=None, exclude=True)
    npc_state_internal_cls: Optional[Type] = Field(default=None, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize NPC state class
        if "npc_state_internal_cls" not in self.__dict__:
            from .npc_state import NPCState

            self.npc_state_internal_cls = NPCState

    # Removed __post_init__ since we're using Pydantic's __init__

    @property
    def no_sleep_quest_unlocked(self) -> bool:
        """Get whether the no-sleep quest is unlocked.

        Once unlocked, the quest remains unlocked even if the player gets a room.
        """
        return self.no_sleep_quest_unlocked_internal

    @no_sleep_quest_unlocked.setter
    def no_sleep_quest_unlocked(self, value: bool) -> None:
        """Set whether the no-sleep quest is unlocked.

        Once unlocked, the quest remains unlocked even if the player gets a room.
        """
        # Once unlocked, it stays unlocked
        if value or self.no_sleep_quest_unlocked_internal:
            self.no_sleep_quest_unlocked_internal = True
        else:
            self.no_sleep_quest_unlocked_internal = value

    def model_dump(self) -> Dict[str, Any]:
        """Convert model to dictionary, including private attributes."""
        data = super().model_dump()
        data["no_sleep_quest_unlocked_internal"] = self.no_sleep_quest_unlocked_internal
        return data

    @classmethod
    def model_validate(cls, data: Dict[str, Any]) -> "PlayerState":
        """Create model from dictionary, handling private attributes."""
        no_sleep_quest = data.pop("no_sleep_quest_unlocked_internal", False)
        instance = super().model_validate(data)
        instance.no_sleep_quest_unlocked_internal = no_sleep_quest
        return instance

    @property
    def npc_state(self) -> "NPCState":
        if self.npc_state_internal is None:
            self.npc_state_internal = self.npc_state_internal_cls()
        return self.npc_state_internal

    def add_gold(self, amount: int) -> bool:
        """Add gold to player's purse. Returns True if successful."""
        if amount < 0 and self.gold < abs(amount):
            return False
        self.gold += amount
        return True

    def spend_gold(self, amount: int) -> Tuple[bool, str]:
        """Attempt to spend gold from the player's purse.

        Args:
            amount: Amount of gold to spend

        Returns:
            Tuple of (success: bool, message: str)
        """
        if amount < 0:
            return False, "Cannot spend a negative amount of gold."

        if self.gold < amount:
            return False, "Not enough gold."

        self.gold -= amount
        return True, f"Spent {amount} gold."

    def update_tiredness(self, delta: float, game_clock: "GameClock") -> None:
        """Update tiredness based on time passed and game state."""
        # Store current game time for quest tracking
        self.current_game_time_internal = game_clock.time.hours

        # Track when player was last awake for the no-sleep quest
        if not hasattr(self, "last_awake_time_internal"):
            self.last_awake_time_internal = self.current_game_time_internal

        # Base tiredness increase
        self.tiredness = min(CONFIG.MAX_TIREDNESS, self.tiredness + delta * 0.5)

        # If player has a room, they can rest and recover
        if self.has_room and not self.rest_immune:
            self.tiredness = max(0, self.tiredness - delta * 0.2)
            # Reset awake time when player rests in a room
            self.last_awake_time_internal = self.current_game_time_internal

        # Check for exhaustion effects
        if self.tiredness >= CONFIG.MAX_TIREDNESS and not self.rest_immune:
            self._handle_exhaustion(game_clock)

    def _handle_exhaustion(self, game_clock: "GameClock") -> None:
        """Handle effects of extreme tiredness.

        Exhaustion effects:
        - Reduced energy (affects combat and task effectiveness)
        - Slowed movement and actions
        - Risk of collapsing if tiredness gets too high
        """
        # Calculate exhaustion severity (0.0 to 1.0)
        exhaustion_severity = min(1.0, (self.tiredness - CONFIG.MAX_TIREDNESS) / (CONFIG.MAX_TIREDNESS * 0.5))

        # Reduce energy based on exhaustion severity
        # Energy drains faster the more exhausted you are
        energy_drain = exhaustion_severity * 0.1
        self.energy = max(0.0, self.energy - energy_drain)

        # Set exhaustion flag for other systems to check
        self.flags["exhausted"] = True
        self.flags["exhaustion_severity"] = exhaustion_severity

        # If severely exhausted (tiredness > 150% of max), apply additional penalties
        if exhaustion_severity > 0.5:
            self.flags["severely_exhausted"] = True

        # If critically exhausted (tiredness > 200% of max), risk of collapse
        if exhaustion_severity >= 1.0:
            self.flags["critically_exhausted"] = True
            # Force minimal energy to prevent any actions
            self.energy = min(self.energy, 0.1)

    def _clear_exhaustion_if_recovered(self) -> None:
        """Clear exhaustion flags if tiredness is back to normal levels."""
        if self.tiredness < CONFIG.MAX_TIREDNESS:
            self.flags.pop("exhausted", None)
            self.flags.pop("exhaustion_severity", None)
            self.flags.pop("severely_exhausted", None)
            self.flags.pop("critically_exhausted", None)

    def rest(self, hours: float) -> None:
        """Rest for a number of hours, reducing tiredness."""
        if not self.has_room:
            return

        # Resting reduces tiredness more effectively than just waiting
        self.tiredness = max(0, self.tiredness - hours * 2)

        # Clear exhaustion flags if tiredness is back to normal
        self._clear_exhaustion_if_recovered()
        
        # Restore some energy when resting
        if self.tiredness < CONFIG.MAX_TIREDNESS:
            self.energy = min(1.0, self.energy + hours * 0.1)

    def sleep(self, hours: float) -> float:
        """Sleep for a number of hours, reducing tiredness and advancing time.

        Args:
            hours: Number of hours to sleep

        Returns:
            float: Number of hours actually slept (0 if couldn't sleep)
        """
        if not self.has_room:
            return 0.0

        # Reduce tiredness by hours slept (capped at 0)
        self.tiredness = max(0, self.tiredness - hours)

        # Clear exhaustion flags if tiredness is back to normal
        self._clear_exhaustion_if_recovered()

        # Restore energy significantly when sleeping
        self.energy = min(1.0, self.energy + hours * 0.15)

        return hours

    def ask_about_sleep(self) -> str:
        """Player asks about sleep, potentially unlocking the no-sleep quest.

        Returns:
            str: Response to the player's question
        """
        # Check if player has been awake for 48+ hours and doesn't have a room
        if not self.has_room and not self.no_sleep_quest_unlocked_internal:
            # Check if 48 hours have passed in game time
            if hasattr(self, "current_game_time_internal") and hasattr(
                self, "last_awake_time_internal"
            ):
                time_awake = (
                    self.current_game_time_internal - self.last_awake_time_internal
                )
                if time_awake >= 48:
                    self.no_sleep_quest_unlocked_internal = True
                    return (
                        "You feel a strange energy coursing through you. "
                        "You no longer feel the need for sleep..."
                    )
                else:
                    return f"You've been awake for {time_awake:.1f} hours. Keep going!"
            return "You're feeling tired and could use some rest."

        if self.has_room:
            return "You have a comfortable room to sleep in."
        return "You're feeling tired and could use some rest."

    def to_dict(self) -> Dict[str, Any]:
        """Serialize player state to a dictionary."""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "gold": self.gold,
            "inventory": self.inventory.items,
            "has_room": self.has_room,
            "room_number": self.room_number,
            "tiredness": self.tiredness,
            "rest_immune": self.rest_immune,
            "no_sleep_quest_unlocked": self.no_sleep_quest_unlocked,
            "flags": self.flags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerState":
        """Deserialize player state from a dictionary."""
        player = cls(
            player_id=data.get("player_id", str(uuid.uuid4())),
            name=data.get("name", "Traveler"),
            gold=data.get("gold", CONFIG.STARTING_GOLD),
            has_room=data.get("has_room", False),
            room_number=data.get("room_number"),
            tiredness=data.get("tiredness", 0.0),
            rest_immune=data.get("rest_immune", False),
            no_sleep_quest_unlocked=data.get("no_sleep_quest_unlocked", False),
            flags=data.get("flags", {}),
        )
        player.inventory = Inventory(data.get("inventory", {}))
        return player


# Alias for backward compatibility
Player = PlayerState
