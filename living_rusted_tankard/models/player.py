from typing import List, Dict, Any, Optional, TYPE_CHECKING, Type, TypeVar
from pydantic import BaseModel, Field
import uuid

if TYPE_CHECKING:
    from ..core.clock import GameClock
    from .npc_state import NPCState

T = TypeVar('T')

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
    gold: int = 40
    inventory: Inventory = Field(default_factory=Inventory)
    has_room: bool = False
    room_number: Optional[str] = None
    tiredness: float = 0.0  # 0-100 scale
    rest_immune: bool = False  # For the no-sleep meta-quest
    flags: Dict[str, Any] = Field(default_factory=dict)  # For tracking quest states, etc.
    energy: float = 1.0  # 0.0 to 1.0 scale
    last_ate: float = 0.0  # Game time when player last ate
    last_drank: float = 0.0  # Game time when player last drank
    
    # Properties
    @property
    def id(self) -> str:
        """Get the player's unique ID."""
        return self.player_id
        
    # Private attributes
    _no_sleep_quest_unlocked: bool = Field(default=False, exclude=True)
    _npc_state: Optional['NPCState'] = Field(default=None, exclude=True)
    _npc_state_cls: Optional[Type['NPCState']] = Field(default=None, exclude=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Initialize NPC state class
        if '_npc_state_cls' not in self.__dict__:
            from .npc_state import NPCState
            self._npc_state_cls = NPCState
    
    # Removed __post_init__ since we're using Pydantic's __init__
    
    @property
    def no_sleep_quest_unlocked(self) -> bool:
        """Get whether the no-sleep quest is unlocked.
        
        Once unlocked, the quest remains unlocked even if the player gets a room.
        """
        return self._no_sleep_quest_unlocked
    
    @no_sleep_quest_unlocked.setter
    def no_sleep_quest_unlocked(self, value: bool) -> None:
        """Set whether the no-sleep quest is unlocked.
        
        Once unlocked, the quest remains unlocked even if the player gets a room.
        """
        # Once unlocked, it stays unlocked
        if value or self._no_sleep_quest_unlocked:
            self._no_sleep_quest_unlocked = True
        else:
            self._no_sleep_quest_unlocked = value
        
    def model_dump(self) -> Dict[str, Any]:
        """Convert model to dictionary, including private attributes."""
        data = super().model_dump()
        data['_no_sleep_quest_unlocked'] = self._no_sleep_quest_unlocked
        return data
    
    @classmethod
    def model_validate(cls, data: Dict[str, Any]) -> 'PlayerState':
        """Create model from dictionary, handling private attributes."""
        no_sleep_quest = data.pop('_no_sleep_quest_unlocked', False)
        instance = super().model_validate(data)
        instance._no_sleep_quest_unlocked = no_sleep_quest
        return instance
    
    @property
    def npc_state(self) -> 'NPCState':
        if self._npc_state is None:
            self._npc_state = self._npc_state_cls()
        return self._npc_state
    
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
    
    def update_tiredness(self, delta: float, game_clock: 'GameClock') -> None:
        """Update tiredness based on time passed and game state."""
        # Store current game time for quest tracking
        self._current_game_time = game_clock.time.hours
        
        # Track when player was last awake for the no-sleep quest
        if not hasattr(self, '_last_awake_time'):
            self._last_awake_time = self._current_game_time
            
        # Base tiredness increase
        self.tiredness = min(100, self.tiredness + delta * 0.5)
        
        # If player has a room, they can rest and recover
        if self.has_room and not self.rest_immune:
            self.tiredness = max(0, self.tiredness - delta * 0.2)
            # Reset awake time when player rests in a room
            self._last_awake_time = self._current_game_time
        
        # Check for exhaustion effects
        if self.tiredness >= 100 and not self.rest_immune:
            self._handle_exhaustion(game_clock)
    
    def _handle_exhaustion(self, game_clock: 'GameClock') -> None:
        """Handle effects of extreme tiredness."""
        # TODO: Implement exhaustion effects
        pass
    
    def rest(self, hours: float) -> None:
        """Rest for a number of hours, reducing tiredness."""
        if not self.has_room:
            return
            
        # Resting reduces tiredness more effectively than just waiting
        self.tiredness = max(0, self.tiredness - hours * 2)
    
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
        return hours
    
    def ask_about_sleep(self) -> str:
        """Player asks about sleep, potentially unlocking the no-sleep quest.
        
        Returns:
            str: Response to the player's question
        """
        # Check if player has been awake for 48+ hours and doesn't have a room
        if not self.has_room and not self._no_sleep_quest_unlocked:
            # Check if 48 hours have passed in game time
            if hasattr(self, '_current_game_time') and hasattr(self, '_last_awake_time'):
                time_awake = self._current_game_time - self._last_awake_time
                if time_awake >= 48:
                    self._no_sleep_quest_unlocked = True
                    return ("You feel a strange energy coursing through you. "
                           "You no longer feel the need for sleep...")
                else:
                    return f"You've been awake for {time_awake:.1f} hours. Keep going!"
            return "You're feeling tired and could use some rest."
        
        if self.has_room:
            return "You have a comfortable room to sleep in."
        return "You're feeling tired and could use some rest."
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize player state to a dictionary."""
        return {
            'player_id': self.player_id,
            'name': self.name,
            'gold': self.gold,
            'inventory': self.inventory.items,
            'has_room': self.has_room,
            'room_number': self.room_number,
            'tiredness': self.tiredness,
            'rest_immune': self.rest_immune,
            'no_sleep_quest_unlocked': self.no_sleep_quest_unlocked,
            'flags': self.flags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerState':
        """Deserialize player state from a dictionary."""
        player = cls(
            player_id=data.get('player_id', str(uuid.uuid4())),
            name=data.get('name', 'Traveler'),
            gold=data.get('gold', 40),
            has_room=data.get('has_room', False),
            room_number=data.get('room_number'),
            tiredness=data.get('tiredness', 0.0),
            rest_immune=data.get('rest_immune', False),
            no_sleep_quest_unlocked=data.get('no_sleep_quest_unlocked', False),
            flags=data.get('flags', {})
        )
        player.inventory = Inventory(data.get('inventory', {}))
        return player
