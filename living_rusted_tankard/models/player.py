from dataclasses import dataclass, field, InitVar
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Type, TypeVar
import uuid
import importlib

if TYPE_CHECKING:
    from ..core.clock import GameClock
    from .npc_state import NPCState

T = TypeVar('T')

@dataclass
class Inventory:
    """Tracks the player's items."""
    items: Dict[str, int] = field(default_factory=dict)  # item_name: quantity
    
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

@dataclass
class PlayerState:
    """Tracks all player-specific state."""
    player_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Traveler"
    gold: int = 40
    inventory: Inventory = field(default_factory=Inventory)
    has_room: bool = False
    room_number: Optional[str] = None
    tiredness: float = 0.0  # 0-100 scale
    rest_immune: bool = False  # For the no-sleep meta-quest
    no_sleep_quest_unlocked: bool = False
    flags: Dict[str, Any] = field(default_factory=dict)  # For tracking quest states, etc.
    _npc_state: Optional['NPCState'] = field(default=None, init=False)
    _npc_state_cls: Type['NPCState'] = field(init=False)
    
    def __post_init__(self):
        # Lazy import to avoid circular imports
        if '_npc_state' not in self.__dict__:
            from .npc_state import NPCState
            self._npc_state_cls = NPCState
    
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
    
    def update_tiredness(self, delta: float, game_clock: 'GameClock') -> None:
        """Update tiredness based on time passed and game state."""
        if self.rest_immune:
            return
            
        # Tiredness increases over time when awake
        self.tiredness = max(0, min(100, self.tiredness + delta * 0.5))
        
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
