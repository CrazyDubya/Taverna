from typing import Dict, Optional, Callable, Any, List, TYPE_CHECKING, Union, Deque
from collections import deque # Added deque
from datetime import datetime
from pydantic import BaseModel
from core.player import PlayerState
from .clock import GameClock, GameTime
from .room import RoomManager
from .npc import NPCManager, NPC
from .economy import Economy, TransactionResult
from .items import Item, TAVERN_ITEMS, Inventory
from games.gambling_manager import GamblingManager
from .events import (
    NPCSpawnEvent,
    NPCDepartEvent,
    NPCInteractionEvent,
    NPCRelationshipChangeEvent
)
from .event_formatter import EventFormatter
from .bounties import BountyManager # Import BountyManager
from living_rusted_tankard.game.commands.bounty_commands import BOUNTY_COMMAND_HANDLERS # Import bounty commands
from living_rusted_tankard.game.commands.reputation_commands import REPUTATION_COMMAND_HANDLERS # Import reputation commands

if TYPE_CHECKING:
    from .snapshot import SnapshotManager

class GameEvent(BaseModel):
    """Represents a game event or notification."""
    timestamp: float
    message: str
    event_type: str = "info"  # info, warning, success, error
    data: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True

class GameState:
    """Main game state manager that ties all systems together."""
    def __init__(self, data_dir: str = "data"):
        """Initialize the game state.
        
        Args:
            data_dir: Directory containing game data files
        """
        # Initialize core components
        self.clock = GameClock()
        self.player = PlayerState()
        self.room_manager = RoomManager()  # Initialize room manager
        self.npc_manager = NPCManager(data_dir, self)  # Initialize NPC manager
        self.economy = Economy()
        self.gambling_manager = GamblingManager()
        self.bounty_manager = BountyManager(data_dir=data_dir) # Initialize BountyManager
        
        # Travelling Merchant Event State
        self.travelling_merchant_active: bool = False
        self.travelling_merchant_npc_id: Optional[str] = "travelling_merchant_elara"
        self.travelling_merchant_arrival_time: Optional[float] = None
        self.travelling_merchant_departure_time: Optional[float] = None
        self.travelling_merchant_temporary_items: List[str] = Field(default_factory=list)

        self.events: Deque[GameEvent] = deque(maxlen=100) # Changed to deque
        self._last_update_time = 0.0

        # Initialize event handling system
        self._observers: Dict[str, Callable[[Any], None]] = {}
        self._setup_event_handlers()
        
        # Track which NPCs are currently present
        self._present_npcs: Dict[str, NPC] = {}
        
        # Setup NPC event handlers
        self._setup_npc_event_handlers()
        
        # Initialize snapshot manager (will be set up on first access via property)
        self._snapshot_manager = None
        
        # Initialize event formatter
        self.event_formatter = EventFormatter()
        
        # Store data_dir for potential use during deserialization of NPCManager
        self._data_dir = data_dir 

        self._initialize_game()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the game state to a dictionary."""
        # Assuming components will have model_dump or to_dict
        # For Pydantic models, model_dump(mode='json') is good for complex types
        # If they are not Pydantic but have to_dict, call that.
        
        serialized_events = [event.model_dump(mode='json') for event in self.events]

        return {
            "clock": self.clock.to_dict() if hasattr(self.clock, 'to_dict') else self.clock.model_dump(mode='json') if isinstance(self.clock, BaseModel) else vars(self.clock),
            "player": self.player.model_dump(mode='json'), # PlayerState is Pydantic
            "room_manager": self.room_manager.to_dict() if hasattr(self.room_manager, 'to_dict') else self.room_manager.model_dump(mode='json') if isinstance(self.room_manager, BaseModel) else vars(self.room_manager),
            "npc_manager": self.npc_manager.to_dict() if hasattr(self.npc_manager, 'to_dict') else self.npc_manager.model_dump(mode='json') if isinstance(self.npc_manager, BaseModel) else vars(self.npc_manager),
            "economy": self.economy.model_dump(mode='json') if isinstance(self.economy, BaseModel) else self.economy.to_dict(), # Assume Pydantic or has to_dict
            "gambling_manager": self.gambling_manager.model_dump(mode='json') if isinstance(self.gambling_manager, BaseModel) else self.gambling_manager.to_dict(), # Assume Pydantic or has to_dict
            "bounty_manager": self.bounty_manager.model_dump(mode='json'), # BountyManager is Pydantic
            "events": serialized_events,
            "_last_update_time": self._last_update_time,
            # Travelling Merchant State
            "travelling_merchant_active": self.travelling_merchant_active,
            "travelling_merchant_npc_id": self.travelling_merchant_npc_id,
            "travelling_merchant_arrival_time": self.travelling_merchant_arrival_time,
            "travelling_merchant_departure_time": self.travelling_merchant_departure_time,
            "travelling_merchant_temporary_items": self.travelling_merchant_temporary_items,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], narrator: Optional[Any] = None, command_parser: Optional[Any] = None, data_dir: str = "data") -> 'GameState':
        """Deserialize the game state from a dictionary."""
        
        # Create a new GameState instance. data_dir is crucial for NPCManager.
        game_state = cls(data_dir=data_dir)

        # Deserialize components
        # For Pydantic models, model_validate is used.
        # If not Pydantic, they need their own from_dict or manual reconstruction.
        
        if 'clock' in data:
            if hasattr(GameClock, 'from_dict'):
                game_state.clock = GameClock.from_dict(data['clock'])
            elif isinstance(game_state.clock, BaseModel): # Check if it's a Pydantic model
                 game_state.clock = GameClock.model_validate(data['clock'])
            else: # Fallback for simple dicts if not Pydantic and no from_dict
                game_state.clock.__dict__.update(data['clock'])


        if 'player' in data:
            game_state.player = PlayerState.model_validate(data['player'])

        if 'room_manager' in data:
            if hasattr(RoomManager, 'from_dict'):
                game_state.room_manager = RoomManager.from_dict(data['room_manager'])
            elif isinstance(game_state.room_manager, BaseModel):
                 game_state.room_manager = RoomManager.model_validate(data['room_manager'])
            else:
                game_state.room_manager.__dict__.update(data['room_manager'])
        
        # NPCManager needs data_dir for its definitions, it's already passed to __init__
        # Its from_dict should handle loading NPCs using that data_dir
        if 'npc_manager' in data:
            if hasattr(NPCManager, 'from_dict'):
                # Pass self (GameState instance) if NPCManager.from_dict expects it
                game_state.npc_manager = NPCManager.from_dict(data['npc_manager'], game_state=game_state, data_dir=data_dir)
            elif isinstance(game_state.npc_manager, BaseModel):
                # This path might be problematic if NPCManager isn't just data but needs re-initialization logic
                # For Pydantic, model_validate is fine for data fields, but complex objects might need more.
                # The NPCManager __init__ takes data_dir and game_state, so simple model_validate might not be enough.
                # We might need to re-initialize it or ensure its from_dict is robust.
                # For now, assume its from_dict or Pydantic nature handles this.
                # Let's assume NPCManager.from_dict will be implemented and is preferred.
                # If it's Pydantic and needs data_dir/game_state, its model_validate might need a context.
                # This is a placeholder, NPCManager will require careful handling.
                 game_state.npc_manager = NPCManager.model_validate(data['npc_manager'], context={'game_state': game_state, 'data_dir': data_dir})
            else:
                 game_state.npc_manager.__dict__.update(data['npc_manager'])


        if 'economy' in data:
            if hasattr(Economy, 'from_dict'):
                game_state.economy = Economy.from_dict(data['economy'])
            elif isinstance(game_state.economy, BaseModel):
                 game_state.economy = Economy.model_validate(data['economy'])
            else:
                game_state.economy.__dict__.update(data['economy'])

        if 'gambling_manager' in data:
            if hasattr(GamblingManager, 'from_dict'):
                game_state.gambling_manager = GamblingManager.from_dict(data['gambling_manager'])
            elif isinstance(game_state.gambling_manager, BaseModel):
                 game_state.gambling_manager = GamblingManager.model_validate(data['gambling_manager'])
            else: # Fallback, though GamblingManager is now Pydantic
                game_state.gambling_manager.__dict__.update(data['gambling_manager'])

        if 'bounty_manager' in data:
            # BountyManager's __init__ takes data_dir, Pydantic's model_validate will pass it if it's part of the model's fields
            # Or, we ensure data_dir is correctly passed when BountyManager instance is created by GameState.from_dict
            # Since BountyManager's __init__ calls _load_bounty_definitions using its _data_dir,
            # and GameState's from_dict passes data_dir to its own __init__ which then passes to BountyManager's __init__,
            # this should be fine.
            game_state.bounty_manager = BountyManager.model_validate(data['bounty_manager'], context={'data_dir': data_dir})
            # If BountyManager needs game_state access during its own from_dict/validate, context can be used.
            # For now, direct model_validate should work for its fields like 'managed_bounties_state'.
            # The _bounty_definitions are reloaded in BountyManager's __init__ based on its own _data_dir.

        if 'events' in data:
            # Recreate as a deque with maxlen
            game_state.events = deque(
                (GameEvent.model_validate(event_data) for event_data in data.get('events', [])), 
                maxlen=100
            )
        
        # Travelling Merchant State
        game_state.travelling_merchant_active = data.get("travelling_merchant_active", False)
        game_state.travelling_merchant_npc_id = data.get("travelling_merchant_npc_id", "travelling_merchant_elara")
        game_state.travelling_merchant_arrival_time = data.get("travelling_merchant_arrival_time")
        game_state.travelling_merchant_departure_time = data.get("travelling_merchant_departure_time")
        game_state.travelling_merchant_temporary_items = data.get("travelling_merchant_temporary_items", [])

        if '_last_update_time' in data:
            game_state._last_update_time = data['_last_update_time']

        # Re-initialize transient states or handlers
        # _observers is for runtime, typically not serialized/deserialized directly.
        # It's re-populated by systems that add observers.
        game_state._observers = {} 
        game_state._setup_event_handlers()  # Re-link clock events, etc.
        game_state._setup_npc_event_handlers() # Re-link NPC events if needed

        # Refresh runtime states based on loaded data
        # Ensure NPCs are correctly placed based on loaded time and their schedules
        if game_state.clock.current_time is not None :
             game_state.npc_manager.update_all_npcs(game_state.clock.current_time)
        game_state._update_present_npcs() # Populate _present_npcs based on current state

        # _snapshot_manager and event_formatter are typically re-created on demand or in __init__
        # and don't need to be part of from_dict data restoration unless they hold serializable state.

        return game_state

    def _initialize_game(self) -> None:
        """Initialize the game with starting state."""
        # Add some starting items to player's inventory
        starting_items = ["bread", "ale"]
        for item_id in starting_items:
            if item_id in TAVERN_ITEMS:
                self.player.inventory.add_item(TAVERN_ITEMS[item_id])
        
        # Log game start
        self._add_event("Welcome to The Rusted Tankard!", "info")

    def _add_event(self, message: str, event_type: str = "info", data: Optional[Dict] = None) -> None:
        """Add a new game event for internal logging."""
        current_time = getattr(self.clock, 'current_time', None)
        if hasattr(current_time, 'hours'): # GameTime object
            timestamp = float(current_time.hours)
        elif isinstance(current_time, float): # Raw float time
            timestamp = current_time
        else: # Fallback if time is not available or in unexpected format
            timestamp = self.clock.get_current_time().total_hours if hasattr(self.clock, 'get_current_time') else 0.0
            
        self.events.append(GameEvent(
            timestamp=timestamp,
            message=message,
            event_type=event_type,
            data=data or {}
        ))
        # The deque with maxlen automatically handles eviction of old events.
        # Manual slicing is no longer needed.
        # if len(self.events) > 100:
        #     self.events = self.events[-100:]

    def _setup_event_handlers(self) -> None:
        """Set up event handlers for time-based events."""
        def on_time_advanced(old_time: float, new_time: float, delta: float) -> None:
            self.player.update_tiredness(delta, self.clock)
            
            # Update NPC presence based on the new time
            self.npc_manager.update_all_npcs(new_time) # Already called in self.update(), consider if needed here
            
            # Update economic events
            event_update = self.economy.update_economic_events(delta)
            if event_update:
                self._add_event(event_update["message"], "info") # Use internal _add_event
            
            # Handle specific time-based events (like dawn/dusk)
            self._handle_time_based_events(old_time, new_time, delta)

            self._notify_observers('time_advanced', {
                'old_time': old_time,
                'new_time': new_time,
                'delta': delta
            })
        
        # Schedule the first time update
        self.clock.on_time_advanced = on_time_advanced

    def _handle_time_based_events(self, old_time: float, new_time: float, delta: float) -> None:
        """Handle events that should occur at specific times."""
        old_hour = int(old_time % 24)
        new_hour = int(new_time % 24)
        
        if old_hour != new_hour:
            # Hour changed
            if new_hour == 6:
                self._add_event("Dawn breaks over the tavern.", "info")
            elif new_hour == 18:
                self._add_event("The sun begins to set outside.", "info")
            
            # Check for rest opportunities
            if new_hour in [22, 23, 0, 1, 2, 3, 4, 5]:
                if not self.player.has_room and not self.player.rest_immune:
                    self._add_event(
                        "The common room is getting uncomfortable. Consider renting a room for the night.",
                        "warning"
                    )

    def add_observer(self, event_type: str, callback: Callable[[Any], None]) -> Callable[[], None]:
        """Add an observer for game events. Returns a function to remove the observer."""
        observer_id = str(id(callback))
        self._observers[observer_id] = callback
        
        def remove():
            self._observers.pop(observer_id, None)
            
        return remove
    
    def _notify_observers(self, event_type: str, data: Any = None) -> None:
        """Notify all observers of an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type in self._observers:
            self._observers[event_type](data)
    
    def dispatch(self, event):
        """Dispatch an event to the event bus if available.
        
        Args:
            event: The event to dispatch
        """
        if hasattr(self.clock, 'event_bus') and hasattr(self.clock.event_bus, 'publish'):
            self.clock.event_bus.publish(event)
        elif hasattr(self, '_notify_observers'):
            # Fall back to notifying observers if event bus is not available
            self._notify_observers(event.__class__.__name__.lower(), event)
                
        # Also forward to the event bus if it's an NPC event
        if hasattr(self, 'clock') and hasattr(self.clock, 'event_bus'):
            self.clock.event_bus.dispatch(event)
    
    def update(self, delta_override: Optional[float] = None) -> None:
        """Update game state. Should be called every frame.
        
        Args:
            delta_override: Optional time in hours to advance, useful for specific updates.
                           If None, uses time since last internal clock update.
        """
        if delta_override is not None:
            # Advance time by a specific delta, then update clock's internal state
            self.clock.advance_time(delta_override) 
            self.clock.update() # Ensure GameTime object is synchronized
            current_time_val = self.clock.current_time
            # delta for event handlers should reflect the override
            actual_delta = delta_override
            # self._last_update_time should be updated based on current_time_val after processing
        else:
            # Standard update based on clock's internal progression
            self.clock.update()
            current_time_val = self.clock.current_time
            actual_delta = current_time_val - self._last_update_time
        
        # The on_time_advanced handler will be called by clock.advance_time or clock.update
        # if time actually changes. We need to ensure it gets the correct delta.
        # If clock.on_time_advanced is the primary mechanism, ensure it's called correctly.
        # The current GameClock.update() calls on_time_advanced.
        # We need to ensure _last_update_time is correctly managed.
        
        # If delta_override was used, the event handlers (on_time_advanced)
        # would have already been triggered by advance_time with delta_override.
        # If not, clock.update() triggers them with its internal delta.

        # Update NPC states based on current time (already done by on_time_advanced if new_time is used)
        # current_game_time_obj = self.clock.get_current_time() # GameTime object
        # self.npc_manager.update_all_npcs(current_game_time_obj.total_hours) # Redundant if on_time_advanced handles it
        
        # Update present NPCs list
        self._update_present_npcs()

        # Update player status effects
        self._update_player_status()
        
        # Update last update time to the new current time from the clock
        current_time_val_float = 0.0
        # In GameClock, current_time is a GameTime object, current_time_hours is the float
        if hasattr(self.clock, 'current_time_hours'): 
            current_time_val_float = float(self.clock.current_time_hours)
        elif hasattr(self.clock, 'current_time') and isinstance(self.clock.current_time, float): # Fallback if it's a direct float
             current_time_val_float = self.clock.current_time
        elif hasattr(self.clock, 'get_current_time'): # Fallback if it's a method returning GameTime
             current_time_val_float = self.clock.get_current_time().total_hours
        
        self._last_update_time = current_time_val_float
        
        # Handle Travelling Merchant Event Logic
        self._update_travelling_merchant_event(current_time_val_float)


    def _update_travelling_merchant_event(self, current_game_hours: float):
        """Manages the appearance and departure of the travelling merchant."""
        import random # Ensure random is imported

        merchant_duration_hours = 24.0 
        merchant_cooldown_hours = 48.0
        merchant_arrival_chance_per_hour_after_cooldown = 0.02 

        merchant_npc = self.npc_manager.get_npc(self.travelling_merchant_npc_id)
        if not merchant_npc:
            # Log this issue, as the merchant NPC ID is expected to be valid
            # self._add_event(f"Travelling merchant NPC '{self.travelling_merchant_npc_id}' not found.", "error")
            return

        if self.travelling_merchant_active:
            if self.travelling_merchant_departure_time is not None and current_game_hours >= self.travelling_merchant_departure_time:
                self._add_event(f"{merchant_npc.name} has packed up their wares and departed.", "event")
                merchant_npc.is_present = False
                merchant_npc.current_room = None 
                # NPCManager's update_all_npcs is called in GameState.update, which will handle _present_npc_ids.

                self.travelling_merchant_active = False
                # self.travelling_merchant_arrival_time = None # Keep for history if needed, not strictly necessary for next arrival logic
                # self.travelling_merchant_departure_time is now the "last departure time"
                self.travelling_merchant_temporary_items.clear()
        else:
            last_departure = self.travelling_merchant_departure_time if self.travelling_merchant_departure_time is not None else -float('inf')
            
            if current_game_hours > (last_departure + merchant_cooldown_hours):
                # This chance is evaluated each time GameState.update is called.
                # If update is called very frequently (e.g. many times per in-game hour),
                # this random chance needs to be scaled by the actual delta time of the update.
                # For now, assuming update() might be called representing ~1 hour chunks for this probability.
                if random.random() < merchant_arrival_chance_per_hour_after_cooldown:
                    self.travelling_merchant_active = True
                    self.travelling_merchant_arrival_time = current_game_hours
                    self.travelling_merchant_departure_time = current_game_hours + merchant_duration_hours
                    
                    merchant_npc.is_present = True
                    merchant_npc.current_room = "tavern_main" # Ensure this room ID exists
                    # NPCManager's update_all_npcs will handle _present_npc_ids.

                    self.travelling_merchant_temporary_items.clear()
                    for item_instance in merchant_npc.inventory:
                        self.travelling_merchant_temporary_items.append(item_instance.id)
                    
                    self._add_event(f"A travelling merchant, {merchant_npc.name}, has arrived in the tavern!", "event")
                    
                    # To get item names for the message, we need to access TAVERN_ITEMS or similar definitions
                    # This assumes merchant_npc.inventory contains Item objects with a 'name' attribute.
                    item_names_for_sale = [item.name for item in merchant_npc.inventory if hasattr(item, 'name')]
                    if not item_names_for_sale: # Fallback if inventory items don't have names directly (e.g. just IDs)
                        item_names_for_sale = [TAVERN_ITEMS.get(item_id).name if TAVERN_ITEMS.get(item_id) else item_id for item_id in self.travelling_merchant_temporary_items]

                    if item_names_for_sale:
                        self._add_event(f"{merchant_npc.name} is offering some unique items: {', '.join(item_names_for_sale)}", "info")


    def _update_player_status(self) -> None:
        """Update player's status effects and conditions."""
        # Check for exhaustion
        if self.player.tiredness >= 0.9 and not self.player.rest_immune:
            self._add_event("You're feeling extremely tired. Find a place to rest soon!", "warning")
        
        # Check for hunger/thirst
        if self.player.energy < 0.3:
            self._add_event("You're feeling weak from hunger or thirst.", "warning")

    def _update_present_npcs(self) -> None:
        """Update the list of currently present NPCs."""
        present_npcs = {}
        for npc in self.npc_manager.get_present_npcs():
            present_npcs[npc.id] = npc
            # If this NPC is newly present, ensure they're in the current room
            if npc.id not in self._present_npcs:
                self._add_npc_to_room(npc)
        
        # Handle NPCs that have left
        for npc_id in set(self._present_npcs) - set(present_npcs):
            self._remove_npc_from_room(npc_id)
            
        self._present_npcs = present_npcs
    
    def _add_npc_to_room(self, npc: NPC) -> None:
        """Add an NPC to their current room."""
        # By default, NPCs are added to the tavern main room
        room = self.room_manager.get_room("tavern_main")
        if room:
            if not room.is_occupied:
                # If room is unoccupied, set as main occupant
                room.occupant_id = npc.id
                room.is_occupied = True
            elif npc.id not in room.npcs:
                # Otherwise add to NPCs list
                room.npcs.append(npc.id)
    
    def _remove_npc_from_room(self, npc_id: str) -> None:
        """Remove an NPC from their current room."""
        for room in self.room_manager.get_all_rooms().values():
            if room.is_occupant(npc_id):
                if npc_id == room.occupant_id:
                    room.occupant_id = None
                    room.is_occupied = False
                elif npc_id in room.npcs:
                    room.npcs.remove(npc_id)
                break
    
    @property
    def snapshot_manager(self):
        """Lazy-load the snapshot manager to avoid circular imports."""
        if self._snapshot_manager is None:
            from .snapshot import SnapshotManager  # Import here to avoid circular import
            self._snapshot_manager = SnapshotManager(self)
        return self._snapshot_manager
    
    def _setup_npc_event_handlers(self):
        """Set up event handlers for NPC-related events."""
        def handle_npc_spawn(event: NPCSpawnEvent):
            npc = self.npc_manager.get_npc(event.npc_id)
            if npc:
                self._present_npcs[npc.id] = npc
                self._add_npc_to_room(npc)
                # Add to recent events
                self.event_formatter.add_event(
                    'npc_spawn',
                    npc_name=npc.name,
                    npc_id=npc.id,
                    location=event.data.get('location', 'tavern')
                )
                # Also notify observers
                self._notify_observers('npc_spawn', {
                    'npc_id': npc.id,
                    'room_id': npc.current_room,
                    'npc_name': npc.name
                })
        
        def handle_npc_depart(event: NPCDepartEvent):
            npc = self._present_npcs.pop(event.npc_id, None)
            if npc:
                reason = event.data.get('reason', 'unknown')
                self._remove_npc_from_room(npc.id)
                # Add to recent events
                self.event_formatter.add_event(
                    'npc_depart',
                    npc_name=npc.name,
                    npc_id=npc.id,
                    reason=reason
                )
                # Also notify observers
                self._notify_observers('npc_depart', {
                    'npc_id': npc.id,
                    'room_id': npc.current_room,
                    'npc_name': npc.name,
                    'reason': reason
                })
        
        def handle_npc_interaction(event: NPCInteractionEvent):
            # Forward interaction events to observers
            self._notify_observers('npc_interaction', {
                'npc_id': event.npc_id,
                'player_id': event.player_id,
                'interaction_type': event.interaction_type,
                'data': event.data
            })
        
        def handle_relationship_change(event: NPCRelationshipChangeEvent):
            # Forward relationship change events to observers
            self._notify_observers('npc_relationship_change', {
                'npc_id': event.npc_id,
                'player_id': event.player_id,
                'change': event.change,
                'new_value': event.new_value
            })
        
        # Subscribe all handlers to the event bus if available
        if hasattr(self.clock, 'event_bus') and hasattr(self.clock.event_bus, 'subscribe'):
            self.clock.event_bus.subscribe('npc_spawn', handle_npc_spawn)
            self.clock.event_bus.subscribe('npc_depart', handle_npc_depart)
            self.clock.event_bus.subscribe('npc_interaction', handle_npc_interaction)
            self.clock.event_bus.subscribe('npc_relationship_change', handle_relationship_change)
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of the current game state."""
        # Get basic NPC info for the current room
        current_room = self.room_manager.current_room
        room_occupants = []
        
        if current_room:
            for occupant_id, occupant_type in current_room.occupants.items():
                if occupant_type == 'player' and occupant_id == self.player.id:
                    # Player
                    room_occupants.append({
                        'id': occupant_id,
                        'type': 'player',
                        'name': self.player.name,
                        'is_player': True
                    })
                elif occupant_type == 'npc':
                    # NPC
                    npc = self.npc_manager.get_npc(occupant_id)
                    if npc:
                        room_occupants.append({
                            'id': npc.id,
                            'type': 'npc',
                            'name': npc.name,
                            'description': npc.description,
                            'is_player': False,
                            'disposition': npc.disposition.name.lower(),
                            'relationship': npc.relationships.get(self.player.id, 0)
                        })
        
        return {
            'time': self.clock.get_current_time().to_dict(),
            'player': self.player.to_dict(),
            'current_room': current_room.id if current_room else None,
            'room_occupants': room_occupants,
            'present_npcs': [
                {
                    'id': npc.id,
                    'name': npc.name,
                    'description': npc.description,
                    'type': npc.npc_type.name.lower(),
                    'disposition': npc.disposition.name.lower(),
                    'relationship': npc.relationships.get(self.player.id, 0)
                }
                for npc in self.npc_manager.get_present_npcs()
            ]
        }
    
    def interact_with_npc(self, npc_id: str, interaction_type: str = "talk", **kwargs) -> Dict[str, Any]:
        """Interact with an NPC.
        
        Args:
            npc_id: ID of the NPC to interact with
            interaction_type: Type of interaction (talk, trade, etc.)
            **kwargs: Additional interaction data
            
        Returns:
            Dict with interaction results
        """
        return self.npc_manager.interact_with_npc(
            npc_id, self.player, interaction_type, **kwargs)
    
    def get_interactive_npcs(self) -> List[Dict[str, Any]]:
        """Get a list of interactive NPCs in the current room.
        
        Returns:
            List of NPCs with their available interactions
        """
        if not self.room_manager.current_room:
            return []
            
        # Only return NPCs that are in the current room
        current_room_npcs = [
            occupant_id for occupant_id, occupant_type 
            in self.room_manager.current_room.occupants.items()
            if occupant_type == 'npc' and self.npc_manager.get_npc(occupant_id)
        ]
        
        # Get interactive info for NPCs in the current room
        return [
            npc for npc in self.npc_manager.get_interactive_npcs(self.player)
            if npc['id'] in current_room_npcs
        ]
        
    def get_available_games(self) -> List[Dict[str, Any]]:
        """Get a list of available gambling games.
        
        Returns:
            List of game descriptions with rules and bet limits
        """
        return self.gambling_manager.get_available_games()
        
    def play_gambling_game(self, game_type: str, bet: int, **kwargs) -> Dict[str, Any]:
        """Play a gambling game.
        
        Args:
            game_type: Type of game to play
            bet: Amount of gold to bet
            **kwargs: Game-specific arguments
            
        Returns:
            Dict with game results and updated player state
        """
        # Check if player is in the tavern (where gambling is allowed)
        if not self.room_manager.current_room or 'tavern' not in self.room_manager.current_room.id.lower():
            return {
                'success': False,
                'message': "You can only gamble in the tavern!"
            }
            
        # Play the game and get results
        result = self.gambling_manager.play_game(self.player, game_type, bet, **kwargs)
        
        # Notify observers of the gambling result
        self._notify_observers('gambling_result', {
            'game_type': game_type,
            'bet': bet,
            'result': result,
            'player_id': self.player.id,
            'new_balance': self.player.gold
        })
        
        return result
        
    def get_gambling_stats(self) -> Dict[str, Any]:
        """Get gambling statistics for the current player.
        
        Returns:
            Dict with gambling statistics
        """
        return self.gambling_manager.get_player_stats(self.player.id)
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """Process a player command and return the result.
        
        Returns:
            Dict containing:
            - success: Whether the command was successful
            - message: The main response message
            - recent_events: List of formatted event strings that occurred during this command
            - time_advanced: Optional float of hours advanced (for time-based commands)
        """
        command = command.lower().strip()
        result = {
            'success': False, 
            'message': "I don't understand that command.",
            'recent_events': []
        }
        
        # Clear previous events at the start of each command
        self.event_formatter.clear_events()
        
        # Clear previous events at the start of each command
        self.event_formatter.clear_events()
        
        # Command routing
        parts = command.split()
        main_command = parts[0] if parts else ""
        args = parts[1:]

        # Construct potential full command key for bounty commands (e.g., "bounty list")
        full_command_key = f"{main_command} {args[0]}" if args else main_command
        
        if full_command_key in BOUNTY_COMMAND_HANDLERS:
            # For commands like "bounty list", "bounty view <ID>", etc.
            # The args for the handler would be parts after the matched key.
            # e.g., for "bounty view id123", key is "bounty view", args for handler is ["id123"]
            # For "bounty list", key is "bounty list", args for handler is []
            # Need to adjust how args are passed based on how BOUNTY_COMMAND_HANDLERS is structured.
            # Current bounty_commands.py expects (game_state, args_list)
            # If key is "bounty view", args for handler should be parts[2:]
            # If key is "bounties", args for handler should be parts[1:] (empty in this case)

            # Simpler approach: if main_command is "bounty" and there's a subcommand
            if main_command == "bounty" and args:
                sub_command = args[0]
                handler_key = f"bounty {sub_command}"
                if handler_key in BOUNTY_COMMAND_HANDLERS:
                    result = BOUNTY_COMMAND_HANDLERS[handler_key](self, args[1:]) # Pass args after subcommand
                else: # Fallback for single "bounty" command if it exists, or error
                    if "bounties" in BOUNTY_COMMAND_HANDLERS and sub_command == "list": # alias "bounty list" to "bounties"
                         result = BOUNTY_COMMAND_HANDLERS["bounties"](self, [])
                    elif main_command in BOUNTY_COMMAND_HANDLERS: # e.g. if "bounties" is aliased to "bounty"
                         result = BOUNTY_COMMAND_HANDLERS[main_command](self, args)
                    else:
                        result = {'success': False, 'message': f"Unknown bounty command: {sub_command}"}

            elif main_command in BOUNTY_COMMAND_HANDLERS : # For single-word bounty commands like "bounties"
                result = BOUNTY_COMMAND_HANDLERS[main_command](self, args)
            # else, it will fall through to other command handlers
        
        # Reputation Command Handling
        elif f"{main_command} {args[0]}" if args and f"{main_command} {args[0]}" in REPUTATION_COMMAND_HANDLERS else main_command in REPUTATION_COMMAND_HANDLERS:
            # Handles "rep status" or "reputation" or "rep"
            handler_key_long = f"{main_command} {args[0]}" if args else "" # e.g. "rep status"
            actual_args_for_handler = args[1:] if args and handler_key_long in REPUTATION_COMMAND_HANDLERS else args
            
            if handler_key_long in REPUTATION_COMMAND_HANDLERS:
                result = REPUTATION_COMMAND_HANDLERS[handler_key_long](self, actual_args_for_handler)
            elif main_command in REPUTATION_COMMAND_HANDLERS:
                 result = REPUTATION_COMMAND_HANDLERS[main_command](self, args)
            # No explicit else needed, will fall to unknown command if not matched
            
        elif main_command == "status":
            result = self._handle_status()
        elif main_command == "inventory":
            result = self._handle_inventory()
        elif main_command == "buy" and args:
            result = self._handle_buy(args[0])
        elif main_command == "use" and args:
            result = self._handle_use(args[0])
        elif main_command == "jobs":
            result = self._handle_available_jobs()
        elif main_command == "work" and args:
            result = self._handle_work(args[0])
        elif main_command == 'look':
            result = self._handle_look()
        elif main_command == 'wait':
            if args:
                try:
                    hours = float(args[0])
                    result = self._handle_wait(hours)
                except ValueError:
                    result = {'success': False, 'message': "Please specify a valid number of hours to wait."}
            else:
                result = self._handle_wait() # Default 1 hour
        elif main_command == 'sleep':
            if args:
                try:
                    hours = float(args[0])
                    result = self._handle_sleep(hours)
                except ValueError:
                    result = {'success': False, 'message': "Please specify a valid number of hours to sleep."}
            else:
                result = self._handle_sleep() # Default 8 hours
        elif main_command in ('quit', 'exit'):
            result = {'success': True, 'message': "Goodbye!", 'should_quit': True}
        elif command == 'ask about sleep': # Keeping original for now
            result = {'success': True, 'message': self.player.ask_about_sleep()}
        elif command in ('rent room', 'rent a room'): # Keeping original
            if self.room_manager.rent_room(self.player):
                result = {'success': True, 'message': "You rent a room for the night."} # This message might be simplified vs _handle_rent
            else:
                result = {'success': False, 'message': "You don't have enough gold to rent a room."} # ditto
        elif main_command == 'games':
            games = self.get_available_games()
            if games:
                game_list = '\n'.join([
                    f"{i+1}. {game['name']}: {game['description']} (Bet: {game['min_bet']}-{game['max_bet']} gold, Payout: {game['payout']})"
                    for i, game in enumerate(games)
                ])
                result = {'success': True, 'message': f"Available games:\n{game_list}"}
            else:
                result = {'success': False, 'message': "No games available right now."}
        elif main_command == "play" and args:
            game_type_arg = args[0] if args else ""
            try:
                bet_amount = int(args[1]) if len(args) > 1 else 0
                if bet_amount <= 0:
                    raise ValueError("Bet must be a positive number!")

                game_kwargs = {}
                # Example for dice: play dice <bet> low/high or play dice <bet> 1/2
                if game_type_arg == 'dice':
                    if len(args) > 2:
                        guess_arg = args[2].lower()
                        if guess_arg in ('low', '1'): game_kwargs['guess'] = 1
                        elif guess_arg in ('high', '2'): game_kwargs['guess'] = 2
                        else: raise ValueError("For dice, specify 'low' or 'high' (or 1/2) after the bet.")
                    else: raise ValueError("For dice, specify 'low' or 'high' (or 1/2) after the bet.")
                elif game_type_arg == 'coin':
                     if len(args) > 2:
                        guess_arg = args[2].lower()
                        if guess_arg in ('heads', 'tails'): game_kwargs['guess'] = guess_arg
                        else: raise ValueError("For coin flip, specify 'heads' or 'tails' after the bet.")
                     else: raise ValueError("For coin flip, specify 'heads' or 'tails' after the bet.")
                
                game_type_map = { 'dice': 'dice', 'coin': 'coin_flip', 'high': 'high_card'}
                actual_game_type = game_type_map.get(game_type_arg)

                if actual_game_type:
                    result = self.play_gambling_game(actual_game_type, bet_amount, **game_kwargs)
                else:
                    result = {'success': False, 'message': f"Unknown game: {game_type_arg}"}

            except ValueError as e:
                result = {'success': False, 'message': str(e)}
            except IndexError:
                 result = {'success': False, 'message': "Invalid 'play' command format."}

        elif command == 'gambling stats': # Kept original command structure
            stats = self.get_gambling_stats()
            if stats['total_games_played'] > 0:
                stats_msg = [
                    f"Games Played: {stats['total_games_played']}",
                    f"Total Won: {stats['total_won']} gold",
                    f"Total Lost: {stats['total_lost']} gold",
                    f"Net Profit: {stats['net_profit']} gold"
                ]
                
                for game_type, game_stats in stats['games'].items():
                    stats_msg.extend([
                        f"\n{game_type.title()}:",
                        f"  Games: {game_stats['games_played']}",
                        f"  Biggest Win: {game_stats['biggest_win']} gold",
                        f"  Biggest Loss: {game_stats['biggest_loss']} gold"
                    ])
                
                result = {'success': True, 'message': '\n'.join(stats_msg)}
            else:
                result = {'success': False, 'message': "You haven't played any gambling games yet!"}
        
        
        # Update the game state - use default delta logic by not passing arg
        self.update() 
        
        # Add any formatted events from this command processing to the result
        result['recent_events'] = self.event_formatter.get_formatted_events()
        return result

    def _handle_status(self) -> Dict[str, Any]:
        """Handle status command."""
        status_data = {
            "time": self.clock.get_formatted_time(),
            "gold": self.player.gold,
            "has_room": self.player.has_room,
            "tiredness": f"{self.player.tiredness*100:.0f}%",
            "energy": f"{self.player.energy*100:.0f}%",
            "status_effects": ", ".join(self.player.get_status_effects()),
        }
        if self.economy.current_event:
            status_data["current_event"] = self.economy.current_event["name"]
            status_data["event_description"] = self.economy.current_event["description"]
        
        return {"success": True, "message": "Player status:", "data": status_data}

    def _handle_inventory(self) -> Dict[str, Any]:
        """Handle inventory command."""
        items_data = [{"name": item.name, "description": item.description} 
                      for item in self.player.inventory.list_items()]
        inventory_info = {
            "items": items_data,
            "count": len(items_data),
            "gold": self.player.gold
        }
        return {
            "success": True,
            "message": "Your inventory:",
            "data": inventory_info
        }

    def _handle_buy(self, item_id: str) -> Dict[str, Any]:
        """Handle buy command, considering travelling merchant stock."""
        item_id_lower = item_id.lower()
        item_to_buy: Optional[Item] = None

        # Check if the item is offered by an active travelling merchant
        if self.travelling_merchant_active and item_id_lower in self.travelling_merchant_temporary_items:
            merchant_npc = self.npc_manager.get_npc(self.travelling_merchant_npc_id)
            if merchant_npc:
                for item_in_merchant_inventory in merchant_npc.inventory:
                    if item_in_merchant_inventory.id == item_id_lower:
                        item_to_buy = item_in_merchant_inventory
                        break
        
        # If not found with merchant (or merchant not active/item not in their list), check standard tavern items
        if not item_to_buy:
            item_to_buy = TAVERN_ITEMS.get(item_id_lower)

        if not item_to_buy:
            return {"success": False, "message": f"Item '{item_id}' is not available for purchase."}
        
        # Pass self (GameState instance) to get_item_price for context
        price = self.economy.get_item_price(item_id_lower, game_state=self)
        
        if price is None: 
            return {"success": False, "message": f"Cannot determine price for {item_to_buy.name}."}
        
        if not self.player.spend_gold(price):
            return {
                "success": False,
                "message": f"Not enough gold. You need {price} gold for {item_to_buy.name}."
            }
        
        self.player.inventory.add_item(item_to_buy)
        self._add_event(f"Bought {item_to_buy.name} for {price} gold.", "success") # Internal log
        self.event_formatter.add_event('item_bought', item_name=item_to_buy.name, price=price) # Formatted event
        
        return {
            "success": True,
            "message": f"You bought {item_to_buy.name} for {price} gold.",
            "data": {"gold": self.player.gold}
        }

    def _handle_use(self, item_id: str) -> Dict[str, Any]:
        """Handle use item command."""
        item_id_lower = item_id.lower()
        if not self.player.inventory.get_item(item_id_lower): # Assumes get_item takes id
            return {"success": False, "message": f"You don't have {item_id} in your inventory."}
        
        # Try to consume the item
        if self.player.consume_item(item_id_lower): # Assumes consume_item takes id
            self.event_formatter.add_event('item_used', item_name=item_id)
            return {"success": True, "message": f"Used {item_id}."}
        else:
            return {"success": False, "message": f"Could not use {item_id}."}

    def _handle_available_jobs(self) -> Dict[str, Any]:
        """Handle jobs command."""
        jobs = self.economy.get_available_jobs(self.player.energy)
        jobs_data = [{
            "id": job_id, "name": job["name"], "description": job["description"],
            "reward": f"{job['base_reward']} gold", "tiredness": f"+{job['tiredness_cost']*100:.0f}%"
        } for job_id, job in jobs.items()]
        
        if not jobs_data:
            return {"success": True, "message": "No jobs available at the moment."}
            
        return {"success": True, "message": "Available jobs:", "data": jobs_data}

    def _handle_work(self, job_id: str) -> Dict[str, Any]:
        """Handle work command."""
        result = self.economy.perform_job(job_id, self.player.energy)
        if not result["success"]:
            return {"success": False, "message": result["message"]}
        
        self.player.add_gold(result["reward"])
        self.player.tiredness = min(1.0, self.player.tiredness + result["tiredness"])
        
        for item in result.get("items", []):
            self.player.inventory.add_item(item)
        
        self.event_formatter.add_event('job_completed', job_name=job_id, reward=result["reward"])
        response_data = {
            "reward": result["reward"],
            "tiredness_increase": result["tiredness"]
        }
        if "items" in result and result["items"]:
            response_data["items_received"] = [item.name for item in result["items"]]

        return {
            "success": True,
            "message": result["message"],
            "data": response_data
        }

    def _handle_look(self) -> Dict[str, Any]:
        """Handle the 'look' command."""
        time_desc = self.clock.time.format_time()
        room_desc = "a small, dimly lit room" if self.player.has_room else "the common area of the tavern"
        
        return {
            'success': True,
            'message': f"It is {time_desc}. You are in {room_desc}.\n"
                     f"Your gold: {self.player.gold} | Tiredness: {int(self.player.tiredness)}%"
        }
    
    def _handle_wait(self, hours: float = 1.0) -> Dict[str, Any]:
        """Handle the 'wait' command."""
        if hours <= 0:
            return {'success': False, 'message': "Time only moves forward in The Rusted Tankard."}
            
        self.clock.advance_time(hours)
        return {
            'success': True,
            'message': f"You wait for {hours:.1f} hours. {self.clock.time.format_time()}",
            'time_advanced': hours
        }
        
    def _handle_sleep(self, hours: float = 8.0) -> Dict[str, Any]:
        """Handle the 'sleep' command."""
        if hours <= 0:
            return {'success': False, 'message': "You can't sleep for negative time!"}
            
        if not self.player.has_room:
            self.event_formatter.add_event('sleep_failure')
            return {'success': False, 'message': "You need to rent a room before you can sleep."}
            
        # Cap sleep at 24 hours
        sleep_hours = min(hours, 24.0)
        
        # Use the room manager to handle sleeping
        success = self.room_manager.sleep(self.player, self.clock)
        
        if success:
            self.event_formatter.add_event(
                'sleep_success',
                hours=sleep_hours,
                room_id=self.player.room_id
            )
            return {
                'success': True,
                'message': f"You sleep for {sleep_hours:.1f} hours. You feel refreshed! {self.clock.time.format_time()}",
                'time_advanced': sleep_hours
            }
        else:
            return {'success': False, 'message': "You can't sleep right now."}
            
    def _handle_rent(self, room_id: str) -> Dict[str, Any]:
        """Handle the 'rent' command."""
        if not room_id.isdigit():
            return {'success': False, 'message': 'Please specify a valid room number.'}
            
        room_to_rent = self.room_manager.get_room(room_id) # Renamed variable for clarity
        if not room_to_rent:
            return {'success': False, 'message': f'Room {room_id} does not exist.'}
            
        if room_to_rent.is_occupied and room_to_rent.occupant_id != self.player.id:
            return {'success': False, 'message': f'Room {room_id} is already occupied.'}
            
        if self.player.gold < room_to_rent.price_per_night:
            short_amount = room_to_rent.price_per_night - self.player.gold
            self.event_formatter.add_event(
                'rent_failure',
                amount=room_to_rent.price_per_night,
                short_amount=short_amount,
                room_id=room_id
            )
            return {
                'success': False, 
                'message': f'You need {room_to_rent.price_per_night} gold to rent this room.'
            }
            
        # If player already has a room, vacate it first
        if self.player.has_room and self.player.room_id: # Ensure room_id is set
            old_room = self.room_manager.get_room(self.player.room_id)
            if old_room:
                old_room.vacate()
        
        # Rent the new room
        rent_successful = room_to_rent.rent(self.player) # Renamed variable
        if rent_successful:
            self.player.spend_gold(room_to_rent.price_per_night) # Use spend_gold for consistency
            self.player.has_room = True
            self.player.room_id = room_id # room_id is string, ensure consistency if Room expects int
            
            self.event_formatter.add_event(
                'rent_success',
                amount=room_to_rent.price_per_night,
                room_id=room_id
            )
            
            return { # result variable was missing before
                'success': True,
                'message': f'You have rented room {room_id} for {room_to_rent.price_per_night} gold.'
            }
        return {'success': False, 'message': 'Failed to rent the room.'}

    def save_game(self, filename: str) -> bool:
        """Save the current game state to a file."""
        try:
            import json # Keep import local to method for now
            
            save_data = {
                "timestamp": datetime.now().isoformat(),
                "game_time": self.clock.current_time, # Assuming current_time is float
                "player": {
                    "gold": self.player.gold,
                    "has_room": self.player.has_room,
                    "tiredness": self.player.tiredness,
                    "energy": self.player.energy,
                    "inventory": [item.id for item in self.player.inventory.list_items()],
                    "flags": self.player.flags,
                    "room_id": self.player.room_id
                },
                "current_event": self.economy.current_event["name"] if self.economy.current_event else None,
                "event_duration": self.economy.event_duration,
                "events_log": [event.model_dump() for event in self.events] # Save internal events
            }
            
            with open(filename, 'w') as f:
                json.dump(save_data, f, indent=2)
                
            self._add_event(f"Game saved to {filename}", "success") # Use internal event log
            return True
            
        except Exception as e:
            self._add_event(f"Failed to save game: {str(e)}", "error")
            return False
    
    def load_game(self, filename: str) -> bool:
        """Load a game state from a file. (Legacy, to be replaced by from_dict via utility)"""
        try:
            import json 
            
            with open(filename, 'r') as f:
                save_data_dict = json.load(f)
            
            # This is where we would use the new from_dict logic
            # For now, this method will become a wrapper or be deprecated.
            # We need a data_dir for this. Assuming "data" for now.
            # Also, narrator and command_parser are not available here.
            
            # This is a conceptual sketch of how it *would* integrate:
            # new_game_state = GameState.from_dict(save_data_dict, data_dir="data") 
            # self.__dict__.update(new_game_state.__dict__) # Risky, better to replace instance or copy specific attrs

            # For now, retain old logic but acknowledge it's superseded.
            # The OPTIMIZATIONS.MD suggests replacing save/load in utils.serialization
            # So, this GameState.load_game might be removed entirely later.

            if "player" not in save_data_dict or "game_time" not in save_data_dict:
                raise ValueError("Invalid save file format (legacy check)")

            self.clock.current_time = save_data_dict["game_time"]
            self._last_update_time = self.clock.current_time 

            player_data = save_data_dict["player"]
            self.player = PlayerState.model_validate(player_data) # Assuming PlayerState is Pydantic

            # Inventory needs to be handled carefully, PlayerState.model_validate should cover it if structured correctly
            # If inventory is separate in save_data_dict or needs special handling:
            # self.player.inventory = Inventory.from_dict(player_data.get("inventory")) or similar

            if save_data_dict.get("current_event") and save_data_dict["current_event"] in self.economy.economic_events:
                self.economy.current_event = self.economy.economic_events[save_data_dict["current_event"]]
                self.economy.event_duration = save_data_dict.get("event_duration", 0)
            else:
                self.economy.current_event = None
                self.economy.event_duration = 0
            
            self.events = [GameEvent.model_validate(event_data) for event_data in save_data_dict.get("events_log", [])]

            self._add_event("Game loaded successfully (legacy method)!", "success")
            self.npc_manager.update_all_npcs(self.clock.current_time)
            self._update_present_npcs()
            return True
            
        except Exception as e:
            self._add_event(f"Failed to load game (legacy method): {str(e)}", "error")
            return False

    def get_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of the current game state for the parser.
        
        Returns:
            Dict containing the minimal structured data needed by the parser.
        """
        return self.snapshot_manager.create_snapshot()
