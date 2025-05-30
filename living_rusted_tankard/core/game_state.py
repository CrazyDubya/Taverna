from typing import Dict, Optional, Callable, Any, List, TYPE_CHECKING, Union, Deque, Set
from collections import deque 
from datetime import datetime
from pydantic import BaseModel, Field
import uuid
import time
import logging
from sqlmodel import SQLModel, Field as SQLField, Column, JSON, DateTime
from core.player import PlayerState

logger = logging.getLogger(__name__)
from .clock import GameClock, GameTime
from .room import RoomManager
from .npc import NPCManager, NPC 
from .economy import Economy, TransactionResult
from .items import Item, Inventory 
from .items import ITEM_DEFINITIONS, load_item_definitions 
from pathlib import Path 
from .news_manager import NewsManager 
from .bounties import BountyManager, BountyStatus, BountyObjective 
from .event_bus import EventBus, EventType, Event

from games.gambling_manager import GamblingManager
from .events import (
    NPCSpawnEvent,
    NPCDepartEvent,
    NPCInteractionEvent,
    NPCRelationshipChangeEvent
)
from .event_formatter import EventFormatter
from game.commands.bounty_commands import BOUNTY_COMMAND_HANDLERS 
from game.commands.reputation_commands import REPUTATION_COMMAND_HANDLERS 

# Phase 2: World System imports
try:
    from .world.atmosphere import AtmosphereManager
    from .world.area_manager import AreaManager
    from .world.floor_manager import FloorManager
    PHASE2_AVAILABLE = True
except ImportError:
    PHASE2_AVAILABLE = False

# Phase 3: NPC System imports  
try:
    from .npc_systems.psychology import NPCPsychologyManager
    from .npc_systems.secrets import SecretsManager
    from .npc_systems.dialogue import DialogueGenerator, DialogueContext
    from .npc_systems.gossip import GossipNetwork
    from .npc_systems.goals import GoalManager
    from .npc_systems.interactions import InteractionManager
    PHASE3_AVAILABLE = True
except ImportError as e:
    print(f"Phase 3 import error: {e}")
    PHASE3_AVAILABLE = False

# Phase 4: Narrative Engine imports
try:
    from .narrative import (
        ThreadManager, NarrativeRulesEngine, NarrativeOrchestrator,
        StoryThread, ThreadType
    )
    from .narrative.event_integration import NarrativeEventHandler
    PHASE4_AVAILABLE = True
except ImportError as e:
    print(f"Phase 4 import error: {e}")
    PHASE4_AVAILABLE = False

if TYPE_CHECKING:
    from .snapshot import SnapshotManager
    from .reputation import get_reputation, get_reputation_tier 

class GameEvent(BaseModel):
    timestamp: float
    message: str
    event_type: str = "info" 
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True

class GameState:
    """
    Main GameState with integrated database persistence and performance optimizations.
    
    This class combines:
    - Core game logic and state management
    - Database persistence capabilities  
    - Performance optimizations with caching
    - Memory management and optimization
    """
    
    def __init__(self, data_dir: str = "data", session_id: Optional[str] = None, db_id: Optional[str] = None):
        self._data_dir = Path(data_dir) 
        if not ITEM_DEFINITIONS: 
            load_item_definitions(self._data_dir)

        self.clock = GameClock()
        self.player = PlayerState()
        self.room_manager = RoomManager()
        self.event_bus = EventBus()  # Create proper event bus
        self.npc_manager = NPCManager(data_dir=str(self._data_dir), event_bus=self.event_bus) 
        self.economy = Economy()
        self.gambling_manager = GamblingManager()
        self.bounty_manager = BountyManager(data_dir=str(self._data_dir)) 
        self.news_manager = NewsManager(data_dir=str(self._data_dir)) 
        
        self.active_global_events: List[str] = [] 
        
        self.travelling_merchant_active: bool = False
        self.travelling_merchant_npc_id: Optional[str] = "travelling_merchant_elara"
        self.travelling_merchant_arrival_time: Optional[float] = None
        self.travelling_merchant_departure_time: Optional[float] = None
        self.travelling_merchant_temporary_items: List[str] = []

        self.events: Deque[GameEvent] = deque(maxlen=100) 
        self._last_update_time = 0.0
        self._observers: Dict[str, Callable[[Any], None]] = {}
        self._setup_event_handlers()
        self._present_npcs: Dict[str, NPC] = {}
        self._setup_npc_event_handlers()
        self._snapshot_manager = None
        self.event_formatter = EventFormatter()
        
        # Player state for two-step commands (e.g. rent confirmation)
        self.pending_command: Optional[Dict[str, Any]] = None
        
        # Database persistence features
        self._session_id = session_id or str(uuid.uuid4())
        self._db_id = db_id
        self._needs_save = True
        
        # Performance optimization features
        self._present_npcs_cache: Dict[str, Any] = {}
        self._present_npcs_set: Set[str] = set()
        self._npc_cache_timestamp: float = 0.0
        self._npc_cache_ttl: float = 0.5  # 0.5 second cache
        
        # Snapshot optimization
        self._snapshot_cache: Optional[Dict[str, Any]] = None
        self._snapshot_timestamp: float = 0.0
        self._snapshot_ttl: float = 1.0  # 1 second cache
        self._snapshot_dirty: bool = True
        
        # Event batch processing
        self._event_batch: List[Dict[str, Any]] = []
        self._event_batch_size: int = 5
        self._last_event_process: float = 0.0
        
        # Initialize Phase 2: World System
        if PHASE2_AVAILABLE:
            self.atmosphere_manager = AtmosphereManager()
            self.area_manager = AreaManager()
            self.floor_manager = FloorManager(self.area_manager)
            self.area_manager._initialize_default_areas()
            self.floor_manager._initialize_floors()
            logger.info("Phase 2: World System initialized")
        
        # Initialize Phase 3: NPC Systems
        if PHASE3_AVAILABLE:
            self.npc_psychology = NPCPsychologyManager()
            self.secrets_manager = SecretsManager()
            self.dialogue_generator = DialogueGenerator()
            # Create a basic relationship web for gossip network
            from .npc_systems.relationships import RelationshipWeb
            self.relationship_web = RelationshipWeb()
            self.gossip_network = GossipNetwork(self.relationship_web)
            self.goal_manager = GoalManager()
            self.interaction_manager = InteractionManager(self.relationship_web, self.gossip_network)
            logger.info("Phase 3: NPC Systems initialized")
        
        # Initialize Phase 4: Narrative Engine
        if PHASE4_AVAILABLE:
            self.thread_manager = ThreadManager()
            self.rules_engine = NarrativeRulesEngine()
            self.narrative_orchestrator = NarrativeOrchestrator(
                self.thread_manager,
                self.rules_engine
            )
            # Event handler will be initialized after event_bus is set up
            self._narrative_handler_pending = True
            logger.info("Phase 4: Narrative Engine initialized")
        else:
            self._narrative_handler_pending = False
        
        self._initialize_game()

    def to_dict(self) -> Dict[str, Any]:
        serialized_events = [event.model_dump(mode='json') for event in self.events]
        return {
            "clock": self.clock.model_dump(mode='json'),
            "player": self.player.model_dump(mode='json'), 
            "room_manager": self.room_manager.model_dump(mode='json'),
            "npc_manager": self.npc_manager.model_dump(mode='json'),
            "economy": self.economy.model_dump(mode='json'), 
            "gambling_manager": self.gambling_manager.model_dump(mode='json'), 
            "bounty_manager": self.bounty_manager.model_dump(mode='json'), 
            "news_manager": self.news_manager.model_dump(mode='json'), 
            "active_global_events": self.active_global_events, 
            "events": serialized_events,
            "_last_update_time": self._last_update_time,
            "travelling_merchant_active": self.travelling_merchant_active,
            "travelling_merchant_npc_id": self.travelling_merchant_npc_id,
            "travelling_merchant_arrival_time": self.travelling_merchant_arrival_time,
            "travelling_merchant_departure_time": self.travelling_merchant_departure_time,
            "travelling_merchant_temporary_items": self.travelling_merchant_temporary_items,
            "_data_dir": str(self._data_dir),
            "pending_command": self.pending_command,
            "session_id": self._session_id,
            "db_id": self._db_id,
            "serialized_at": datetime.utcnow().isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], narrator: Optional[Any] = None, command_parser: Optional[Any] = None, data_dir: str = "data", session_id: Optional[str] = None, db_id: Optional[str] = None) -> 'GameState':
        game_state_data_dir = Path(data.get("_data_dir", data_dir)) 
        
        if not ITEM_DEFINITIONS:
            load_item_definitions(game_state_data_dir)

        # Extract session info from data if not provided
        session_id = session_id or data.get("session_id")
        db_id = db_id or data.get("db_id")
        
        game_state = cls(data_dir=str(game_state_data_dir), session_id=session_id, db_id=db_id)
        
        game_state.clock = GameClock.model_validate(data['clock'])
        game_state.player = PlayerState.model_validate(data['player'])
        game_state.room_manager = RoomManager.model_validate(data['room_manager'])
        game_state.npc_manager = NPCManager.model_validate(data.get('npc_manager',{}), context={'event_bus': game_state, 'data_dir': str(game_state_data_dir)})
        game_state.economy = Economy.model_validate(data['economy'])
        game_state.gambling_manager = GamblingManager.model_validate(data['gambling_manager'])
        game_state.bounty_manager = BountyManager.model_validate(data['bounty_manager'], context={'data_dir': str(game_state_data_dir)})
        game_state.news_manager = NewsManager.model_validate(data.get('news_manager', {}), context={'data_dir': str(game_state_data_dir)}) 
        game_state.active_global_events = data.get('active_global_events', []) 
        game_state.pending_command = data.get('pending_command')


        game_state.events = deque(
            (GameEvent.model_validate(event_data) for event_data in data.get('events', [])), 
            maxlen=100
        )
        
        game_state.travelling_merchant_active = data.get("travelling_merchant_active", False)
        game_state.travelling_merchant_npc_id = data.get("travelling_merchant_npc_id", "travelling_merchant_elara")
        game_state.travelling_merchant_arrival_time = data.get("travelling_merchant_arrival_time")
        game_state.travelling_merchant_departure_time = data.get("travelling_merchant_departure_time")
        game_state.travelling_merchant_temporary_items = data.get("travelling_merchant_temporary_items", [])
        game_state._last_update_time = data.get('_last_update_time', 0.0)

        game_state._observers = {} 
        game_state._setup_event_handlers()
        game_state._setup_npc_event_handlers() 

        current_time_float = game_state.clock.current_time_hours if hasattr(game_state.clock, 'current_time_hours') else \
                             (game_state.clock.current_time.total_hours if hasattr(game_state.clock.current_time, 'total_hours') else float(game_state.clock.current_time))
        if current_time_float is not None:
             game_state.npc_manager.update_all_npcs(current_time_float)
        game_state._update_present_npcs() 

        return game_state

    def _initialize_game(self) -> None:
        if not ITEM_DEFINITIONS: 
            load_item_definitions(self._data_dir)

        # Add starting items
        starting_item_ids = ["bread", "ale"]
        for item_id in starting_item_ids:
            if item_id in ITEM_DEFINITIONS: 
                success = self.player.inventory.add_item(item_id, quantity=1)
                if not success:
                    print(f"Warning: Failed to add starting item '{item_id}'")
            else:
                print(f"Warning: Starting item ID '{item_id}' not found in ITEM_DEFINITIONS.")
        
        # Initialize player attributes
        if not hasattr(self.player, 'active_bounty_ids'): 
            self.player.active_bounty_ids = set() 
        if not hasattr(self.player, 'completed_bounty_ids'):
            self.player.completed_bounty_ids = set()
        if not hasattr(self.player, 'active_effects'): 
            self.player.active_effects = [] 
        if not hasattr(self.player, 'storage_inventory'): # Ensure storage_inventory is initialized
            self.player.storage_inventory = Inventory()
            
        # Give player some starting gold
        self.player.gold = 20
            
        # Complete Phase 4 setup now that event_bus exists
        if PHASE4_AVAILABLE and hasattr(self, '_narrative_handler_pending') and self._narrative_handler_pending:
            self.narrative_handler = NarrativeEventHandler(self, self.narrative_orchestrator)
            self._narrative_handler_pending = False
            
            # Create initial narrative threads
            self._create_initial_narrative_threads()
        
        # Initialize NPC psychology for existing NPCs
        if PHASE3_AVAILABLE:
            for npc_id, npc in self.npc_manager.npcs.items():
                self.npc_psychology.initialize_npc(npc_id, npc)
                if hasattr(npc, 'has_secret') and npc.has_secret:
                    self.secrets_manager.initialize_npc_secrets(npc_id)
                self.goal_manager.initialize_npc_goals(npc_id, npc)
        
        # Add a single, immersive welcome message
        welcome_message = """
The heavy wooden door of The Living Rusted Tankard creaks open, and warm lamplight spills out to greet you. The scent of roasted meat, fresh ale, and old wood fills your nostrils as you step inside. Flickering candles cast dancing shadows on weathered walls adorned with tavern keepsakes.

A burly barkeeper with a magnificent mustache polishes glasses behind the sturdy oak bar, occasionally glancing up at the patrons scattered throughout the common room. The hearth crackles invitingly, its orange glow painting the faces of weary travelers sharing tales over their drinks.

What tale will you weave in this living tapestry of stories?
"""
        self._add_event(welcome_message, "welcome")


    def _add_event(self, message: str, event_type: str = "info", data: Optional[Dict] = None) -> None:
        current_time = getattr(self.clock, 'current_time_hours', None) 
        if current_time is None: 
             current_time_obj = getattr(self.clock, 'current_time', None)
             if hasattr(current_time_obj, 'total_hours'): 
                 current_time = current_time_obj.total_hours
             elif isinstance(current_time_obj, float):
                 current_time = current_time_obj
             else:
                 current_time = 0.0
            
        self.events.append(GameEvent(
            timestamp=float(current_time),
            message=message,
            event_type=event_type,
            data=data or {}
        ))

    def _setup_event_handlers(self) -> None:
        def on_time_advanced(old_time: float, new_time: float, delta: float) -> None:
            self.player.update_tiredness(delta, self.clock) 
            self.player.update_effects(new_time) 
            self.npc_manager.update_all_npcs(new_time) 
            event_update = self.economy.update_economic_events(delta)
            if event_update:
                self._add_event(event_update["message"], "info")
            self._handle_time_based_events(old_time, new_time, delta)
            self._notify_observers('time_advanced', {'old_time': old_time, 'new_time': new_time, 'delta': delta})
        self.clock.on_time_advanced = on_time_advanced

    def _handle_time_based_events(self, old_time: float, new_time: float, delta: float) -> None:
        old_hour = int(old_time % 24)
        new_hour = int(new_time % 24)
        if old_hour != new_hour:
            if new_hour == 6: self._add_event("Dawn breaks over the tavern.", "info")
            elif new_hour == 18: self._add_event("The sun begins to set outside.", "info")
            if new_hour in [22, 23, 0, 1, 2, 3, 4, 5] and not self.player.has_room and not self.player.rest_immune:
                self._add_event("The common room is getting uncomfortable. Consider renting a room for the night.", "warning")

    def add_observer(self, event_type: str, callback: Callable[[Any], None]) -> Callable[[], None]:
        observer_id = str(id(callback))
        self._observers[observer_id] = callback
        def remove(): self._observers.pop(observer_id, None)
        return remove
    
    def _notify_observers(self, event_type: str, data: Any = None) -> None:
        if event_type in self._observers: self._observers[event_type](data)
    
    def dispatch(self, event):
        event_bus = getattr(self.clock, 'event_bus', None)
        if event_bus and hasattr(event_bus, 'publish'): event_bus.publish(event)
        elif hasattr(self, '_notify_observers'): self._notify_observers(event.__class__.__name__.lower(), event)
        if event_bus and hasattr(event_bus, 'dispatch'): event_bus.dispatch(event) 
    
    def update(self, delta_override: Optional[float] = None) -> None:
        if delta_override is not None:
            self.clock.advance_time(delta_override) 
        self.clock.update() 
        
        current_time_val_float = self.clock.current_time_hours if hasattr(self.clock, 'current_time_hours') else \
                                 (self.clock.current_time.total_hours if hasattr(self.clock.current_time, 'total_hours') else float(self.clock.current_time))
        
        self.player.update_effects(current_time_val_float) 
        self._update_present_npcs()
        self._update_player_status()
        self._check_bounty_objective_triggers() 
        
        # Update phase systems
        elapsed_minutes = delta_override if delta_override else 1
        self._update_phase_systems(elapsed_minutes)
        
        self._last_update_time = current_time_val_float
        self._update_travelling_merchant_event(current_time_val_float)
    
    def _update_phase_systems(self, elapsed_minutes: float):
        """Update all phase systems with time progression"""
        # Update Phase 2: Atmosphere
        if PHASE2_AVAILABLE and hasattr(self, 'atmosphere_manager'):
            self.atmosphere_manager.update(elapsed_minutes * 60)  # Convert to seconds
        
        # Update Phase 3: NPC Systems
        if PHASE3_AVAILABLE:
            # Update NPC psychology
            for npc_id in self.npc_manager.npcs:
                self.npc_psychology.update_npc_state(npc_id, elapsed_minutes * 60)
            
            # Process NPC goals
            self.goal_manager.update_all_goals(elapsed_minutes * 60)
            
            # Update gossip network
            self.gossip_network.propagate_rumors(elapsed_minutes * 60)
        
        # Phase 4 narrative updates happen via events, not time

    def _update_travelling_merchant_event(self, current_game_hours: float):
        import random 
        merchant_duration_hours = 24.0 
        merchant_cooldown_hours = 48.0
        merchant_arrival_chance_per_hour_after_cooldown = 0.02 
        merchant_npc = self.npc_manager.get_npc(self.travelling_merchant_npc_id)
        if not merchant_npc: return

        if self.travelling_merchant_active:
            if self.travelling_merchant_departure_time is not None and current_game_hours >= self.travelling_merchant_departure_time:
                self._add_event(f"{merchant_npc.name} has packed up their wares and departed.", "event")
                merchant_npc.is_present = False
                merchant_npc.current_room = None 
                self.travelling_merchant_active = False
                self.travelling_merchant_temporary_items.clear()
        else:
            last_departure = self.travelling_merchant_departure_time if self.travelling_merchant_departure_time is not None else -float('inf')
            if current_game_hours > (last_departure + merchant_cooldown_hours):
                if random.random() < merchant_arrival_chance_per_hour_after_cooldown:
                    self.travelling_merchant_active = True
                    self.travelling_merchant_arrival_time = current_game_hours
                    self.travelling_merchant_departure_time = current_game_hours + merchant_duration_hours
                    merchant_npc.is_present = True
                    merchant_npc.current_room = "tavern_main" 
                    self.travelling_merchant_temporary_items.clear()
                    if not ITEM_DEFINITIONS: load_item_definitions(self._data_dir)
                    for item_instance in merchant_npc.inventory: 
                        self.travelling_merchant_temporary_items.append(item_instance.id)
                    self._add_event(f"A travelling merchant, {merchant_npc.name}, has arrived in the tavern!", "event")
                    item_names_for_sale = [item.name for item in merchant_npc.inventory if hasattr(item, 'name')]
                    if not item_names_for_sale:
                         item_names_for_sale = [ITEM_DEFINITIONS.get(item_id).name if ITEM_DEFINITIONS.get(item_id) else item_id for item_id in self.travelling_merchant_temporary_items]
                    if item_names_for_sale:
                        self._add_event(f"{merchant_npc.name} is offering some unique items: {', '.join(item_names_for_sale)}", "info")

    def _update_player_status(self) -> None:
        if self.player.tiredness >= 0.9 and not self.player.rest_immune:
            self._add_event("You're feeling extremely tired. Find a place to rest soon!", "warning")
        if self.player.energy < 0.3:
            self._add_event("You're feeling weak from hunger or thirst.", "warning")

    def _update_present_npcs(self) -> None:
        present_npcs_now = {}
        for npc in self.npc_manager.get_present_npcs():
            present_npcs_now[npc.id] = npc
            if npc.id not in self._present_npcs: self._add_npc_to_room(npc)
        for npc_id in set(self._present_npcs) - set(present_npcs_now): self._remove_npc_from_room(npc_id)
        self._present_npcs = present_npcs_now
    
    def _add_npc_to_room(self, npc: NPC) -> None:
        room = self.room_manager.get_room("tavern_main")
        if room:
            if not room.is_occupied: room.occupant_id = npc.id; room.is_occupied = True
            elif npc.id not in room.npcs: room.npcs.append(npc.id)
    
    def _remove_npc_from_room(self, npc_id: str) -> None:
        for room in self.room_manager.get_all_rooms().values():
            if room.is_occupant(npc_id):
                if npc_id == room.occupant_id: room.occupant_id = None; room.is_occupied = False
                elif npc_id in room.npcs: room.npcs.remove(npc_id)
                break
    
    @property
    def snapshot_manager(self):
        if self._snapshot_manager is None:
            from .snapshot import SnapshotManager
            self._snapshot_manager = SnapshotManager(self)
        return self._snapshot_manager
    
    def _setup_npc_event_handlers(self):
        def handle_npc_spawn(event: NPCSpawnEvent):
            npc = self.npc_manager.get_npc(event.npc_id)
            if npc:
                self._present_npcs[npc.id] = npc; self._add_npc_to_room(npc)
                self.event_formatter.add_event('npc_spawn', npc_name=npc.name, npc_id=npc.id, location=event.data.get('location', 'tavern'))
                self._notify_observers('npc_spawn', {'npc_id': npc.id, 'room_id': npc.current_room, 'npc_name': npc.name})
        
        def handle_npc_depart(event: NPCDepartEvent):
            npc = self._present_npcs.pop(event.npc_id, None)
            if npc:
                reason = event.data.get('reason', 'unknown')
                self._remove_npc_from_room(npc.id)
                self.event_formatter.add_event('npc_depart', npc_name=npc.name, npc_id=npc.id, reason=reason)
                self._notify_observers('npc_depart', {'npc_id': npc.id, 'room_id': npc.current_room, 'npc_name': npc.name, 'reason': reason})
        
        def handle_npc_interaction(event: NPCInteractionEvent): self._notify_observers('npc_interaction', event.model_dump())
        def handle_relationship_change(event: NPCRelationshipChangeEvent): self._notify_observers('npc_relationship_change', event.model_dump())
        
        event_bus = getattr(self.clock, 'event_bus', None)
        if event_bus and hasattr(event_bus, 'subscribe'):
            event_bus.subscribe('npc_spawn', handle_npc_spawn)
            event_bus.subscribe('npc_depart', handle_npc_depart)
            event_bus.subscribe('npc_interaction', handle_npc_interaction)
            event_bus.subscribe('npc_relationship_change', handle_relationship_change)
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        current_room = self.room_manager.current_room
        room_occupants_data = []
        if current_room and hasattr(current_room, 'occupants') and isinstance(current_room.occupants, list): 
            for occupant_id_str in current_room.occupants:
                if occupant_id_str == self.player.id:
                     room_occupants_data.append({'id': occupant_id_str, 'type': 'player', 'name': self.player.name, 'is_player': True})
                else:
                    npc = self.npc_manager.get_npc(occupant_id_str)
                    if npc:
                        room_occupants_data.append({'id': npc.id, 'type': 'npc', 'name': npc.name, 'description': npc.description, 
                                                     'is_player': False, 'disposition': npc.disposition.name.lower(), 
                                                     'relationship': npc.relationships.get(self.player.id, 0)})
        elif current_room and hasattr(current_room, 'occupants') and isinstance(current_room.occupants, dict): 
             for occupant_id, occupant_type in current_room.occupants.items(): # type: ignore
                if occupant_type == 'player' and occupant_id == self.player.id:
                    room_occupants_data.append({'id': occupant_id, 'type': 'player', 'name': self.player.name, 'is_player': True})
                elif occupant_type == 'npc':
                    npc = self.npc_manager.get_npc(occupant_id)
                    if npc: room_occupants_data.append({'id': npc.id, 'type': 'npc', 'name': npc.name, 'description': npc.description, 
                                                     'is_player': False, 'disposition': npc.disposition.name.lower(), 
                                                     'relationship': npc.relationships.get(self.player.id, 0)})
        return {
            'time': self.clock.get_current_time().to_dict(),
            'player': self.player.to_dict(), 
            'current_room': current_room.id if current_room else None,
            'room_occupants': room_occupants_data, 
            'present_npcs': [{'id': npc.id, 'name': npc.name, 'description': npc.description,
                              'type': npc.npc_type.name.lower(), 'disposition': npc.disposition.name.lower(),
                              'relationship': npc.relationships.get(self.player.id, 0)}
                             for npc in self.npc_manager.get_present_npcs()]
        }
    
    def interact_with_npc(self, npc_id: str, interaction_id: str, **kwargs) -> Dict[str, Any]:
        # Get base response from NPC manager
        response = self.npc_manager.interact_with_npc(npc_id, self.player, interaction_id, self, **kwargs)
        
        # Enhance with Phase 3 systems if available
        if PHASE3_AVAILABLE and response.get("success", False) and interaction_id == "talk":
            npc = self.npc_manager.get_npc(npc_id)
            if npc:
                # Get psychological state
                psychology = self.npc_psychology.get_npc_state(npc_id)
                
                # Get narrative context if Phase 4 is available
                narrative_context = None
                if PHASE4_AVAILABLE and hasattr(self, 'narrative_handler'):
                    narrative_context = self.narrative_handler.get_narrative_context_for_npc(npc_id)
                
                # Create dialogue context
                dialogue_context = DialogueContext(
                    npc_name=npc_id,
                    player_name="player",
                    location=self.player.current_room,
                    time_of_day=self.clock.get_time_period(),
                    relationship_level=self.reputation.get_npc_relationship(npc_id),
                    current_mood=psychology.get('mood', 'neutral'),
                    active_threads=narrative_context.get('active_threads', []) if narrative_context else [],
                    recent_events=self.get_recent_events(limit=5)
                )
                
                # Generate enhanced dialogue
                base_message = response.get('message', '')
                enhanced_message = self.dialogue_generator.generate_dialogue(
                    npc_id,
                    dialogue_context,
                    base_prompt=base_message
                )
                
                # Add gossip if available
                gossip = self.gossip_network.get_npc_gossip(npc_id)
                if gossip:
                    enhanced_message += f"\n\n{npc.name} leans in and whispers: '{gossip}'"
                
                # Add goal-driven dialogue
                current_goal = self.goal_manager.get_current_goal(npc_id)
                if current_goal and hasattr(current_goal, 'involves_player') and current_goal.involves_player:
                    goal_dialogue = self.goal_manager.get_goal_dialogue(npc_id, current_goal)
                    if goal_dialogue:
                        enhanced_message += f"\n\n{goal_dialogue}"
                
                response['message'] = enhanced_message
        
        # Check bounty objectives
        if response.get("success", False) and interaction_id == "talk": 
            self._check_bounty_objective_report_to_npc(npc_id)
        
        return response
    
    def get_interactive_npcs(self) -> List[Dict[str, Any]]:
        return self.npc_manager.get_interactive_npcs(self.player) 
        
    def get_available_games(self) -> List[Dict[str, Any]]: return self.gambling_manager.get_available_games()
        
    def play_gambling_game(self, game_type: str, bet: int, **kwargs) -> Dict[str, Any]:
        if not self.room_manager.current_room or 'tavern' not in self.room_manager.current_room.id.lower():
            return {'success': False, 'message': "You can only gamble in the tavern!"}
        result = self.gambling_manager.play_game(self.player, game_type, bet, **kwargs)
        self._notify_observers('gambling_result', {'game_type': game_type, 'bet': bet, 'result': result, 'player_id': self.player.id, 'new_balance': self.player.gold})
        return result
        
    def get_gambling_stats(self) -> Dict[str, Any]: return self.gambling_manager.get_player_stats(self.player.id)
    
    def process_command(self, command: str) -> Dict[str, Any]:
        command = command.lower().strip()
        
        # Default result for unknown commands
        result = {'success': False, 'message': "I don't understand that command.", 'recent_events': []}
        
        # Clear any previous events
        self.event_formatter.clear_events()
        
        # Handle empty command specially at the beginning
        if not command:
            help_text = self._generate_help_text()
            return {'success': True, 'message': "What would you like to do? Type 'help' for a list of commands.", 'recent_events': []}
        
        parts = command.split()
        main_command = parts[0] if parts else ""
        args = parts[1:]

        # Handle two-step rent confirmation
        if self.pending_command and self.pending_command.get("type") == "confirm_rent":
            if main_command == "yes":
                # Retrieve stored parameters and execute the rent
                params = self.pending_command["params"]
                result = self._execute_rent_room(**params) # type: ignore
                self.pending_command = None
            elif main_command == "no":
                result = {'success': True, 'message': "You decided not to rent the new room. Your current room and storage are safe."}
                self.pending_command = None
            else:
                result = {'success': False, 'message': "Please answer 'yes' or 'no'."}
            # Update and return immediately after handling pending command
            self.update()
            result['recent_events'] = self.event_formatter.get_formatted_events()
            return result

        if main_command == "rent" and "room" in args:
            # Determine if "with chest" is specified
            with_chest = "with chest" in command # Simple check
            result = self._handle_rent_room_command(with_chest=with_chest)
        elif main_command == "store" and len(args) >= 2:
            item_id_to_store = args[0]
            try: quantity_to_store = int(args[1])
            except ValueError: result = {'success': False, 'message': "Invalid quantity."}; quantity_to_store = 0
            if quantity_to_store > 0: result = self._handle_store_item(item_id_to_store, quantity_to_store)
        elif main_command == "retrieve" and len(args) >= 2:
            item_id_to_retrieve = args[0]
            try: quantity_to_retrieve = int(args[1])
            except ValueError: result = {'success': False, 'message': "Invalid quantity."}; quantity_to_retrieve = 0
            if quantity_to_retrieve > 0: result = self._handle_retrieve_item(item_id_to_retrieve, quantity_to_retrieve)
        elif main_command == "check" and "storage" in args:
            result = self._handle_check_storage()
        elif main_command == "read" and " ".join(args) == "notice board":
            result = self._handle_read_notice_board()
        elif main_command == "accept" and args and args[0] == "bounty" and len(args) > 1:
            bounty_id_to_accept = args[1]
            result = self._handle_accept_bounty(bounty_id_to_accept)
        elif main_command == "interact" and len(args) >= 2:
            npc_id_arg = args[0]
            interaction_id_arg = args[1]
            interaction_kwargs = {}
            if interaction_id_arg == "talk" and len(args) > 2:
                interaction_kwargs["topic"] = " ".join(args[2:])
            result = self.interact_with_npc(npc_id_arg, interaction_id_arg, **interaction_kwargs)
        elif main_command == "progress_bounty" and len(args) >= 2: 
            b_id, obj_id_param = args[0], args[1] 
            bounty_instance = self.bounty_manager.get_bounty(b_id)
            active_obj_id_to_progress = obj_id_param 
            if bounty_instance and bounty_instance.accepted_by_player_id == self.player.id:
                active_obj = bounty_instance.get_active_objective()
                if active_obj and obj_id_param == "active": 
                    active_obj_id_to_progress = active_obj.id
            
            prog_amt = int(args[2]) if len(args) > 2 else 1
            success, msg = self.bounty_manager.update_bounty_progress(self.player.id, b_id, active_obj_id_to_progress, prog_amt)
            result = {"success": success, "message": msg}
        elif main_command == "complete_bounty" and args: 
            b_id = args[0]
            success, msg = self.bounty_manager.complete_bounty(self.player.id, b_id, self) 
            if success: self.player.active_bounty_ids.discard(b_id); self.player.completed_bounty_ids.add(b_id)
            result = {"success": success, "message": msg}
        elif main_command == "move" and args: 
            room_id_target = args[0]
            if self.room_manager.move_to_room(room_id_target):
                result = {"success": True, "message": f"You moved to {room_id_target}."}
            else:
                result = {"success": False, "message": f"Cannot move to {room_id_target}."}
        else: 
            full_command_key = f"{main_command} {args[0]}" if args else main_command
            if full_command_key in BOUNTY_COMMAND_HANDLERS:
                handler_args = args[1:] if (main_command == "bounty" and args) else args
                result = BOUNTY_COMMAND_HANDLERS[full_command_key](self, handler_args)
            elif main_command in BOUNTY_COMMAND_HANDLERS and not args:
                 result = BOUNTY_COMMAND_HANDLERS[main_command](self, [])
            elif f"{main_command} {args[0]}" if args and f"{main_command} {args[0]}" in REPUTATION_COMMAND_HANDLERS else main_command in REPUTATION_COMMAND_HANDLERS:
                handler_key_long = f"{main_command} {args[0]}" if args else "" 
                actual_args_for_handler = args[1:] if args and handler_key_long in REPUTATION_COMMAND_HANDLERS else args
                if handler_key_long in REPUTATION_COMMAND_HANDLERS: result = REPUTATION_COMMAND_HANDLERS[handler_key_long](self, actual_args_for_handler)
                elif main_command in REPUTATION_COMMAND_HANDLERS: result = REPUTATION_COMMAND_HANDLERS[main_command](self, args)
            elif main_command == "status": result = self._handle_status()
            elif main_command == "inventory": result = self._handle_inventory()
            elif main_command == "buy" and args: result = self._handle_buy(args[0])
            elif main_command == "use" and args: result = self._handle_use(args[0])
            elif main_command == "jobs": result = self._handle_available_jobs()
            elif main_command == "work" and args: result = self._handle_work(args[0])
            elif main_command == 'look': result = self._handle_look()
            elif main_command == 'wait':
                if args:
                    try: hours = float(args[0]); result = self._handle_wait(hours)
                    except ValueError: result = {'success': False, 'message': "Please specify a valid number of hours to wait."}
                else: result = self._handle_wait() 
            elif main_command == 'sleep':
                if args:
                    try: hours = float(args[0]); result = self._handle_sleep(hours)
                    except ValueError: result = {'success': False, 'message': "Please specify a valid number of hours to sleep."}
                else: result = self._handle_sleep() 
            elif main_command in ('quit', 'exit'): result = {'success': True, 'message': "Goodbye!", 'should_quit': True}
            elif command == 'ask about sleep': result = {'success': True, 'message': self.player.ask_about_sleep()}
            # Removed old 'rent room' command from here as it's now handled by _handle_rent_room_command
            elif main_command == 'help':
                result = {'success': True, 'message': self._generate_help_text()}
            elif main_command == 'games':
                games = self.get_available_games()
                if games:
                    game_list = '\n'.join([f"{i+1}. {g['name']}: {g['description']} (Bet: {g['min_bet']}-{g['max_bet']} gold, Payout: {g['payout']})" for i, g in enumerate(games)])
                    result = {'success': True, 'message': f"Available games:\n{game_list}"}
                else: result = {'success': False, 'message': "No games available right now."}
            elif main_command == "play" and args:
                game_type_arg = args[0]; bet_amount_str = args[1] if len(args) > 1 else "0"
                try:
                    bet_amount = int(bet_amount_str)
                    if bet_amount <= 0: raise ValueError("Bet must be a positive number!")
                    game_kwargs = {}; game_type_map = { 'dice': 'dice', 'coin': 'coin_flip', 'high': 'high_card'}
                    actual_game_type = game_type_map.get(game_type_arg)
                    if actual_game_type == 'dice':
                        if len(args) > 2: guess_arg = args[2].lower(); game_kwargs['guess'] = 1 if guess_arg in ('low', '1') else (2 if guess_arg in ('high', '2') else None)
                        if game_kwargs.get('guess') is None: raise ValueError("For dice, specify 'low'/'high' or '1'/'2'.")
                    elif actual_game_type == 'coin_flip':
                        if len(args) > 2: guess_arg = args[2].lower(); game_kwargs['guess'] = guess_arg if guess_arg in ('heads', 'tails') else None
                        if game_kwargs.get('guess') is None: raise ValueError("For coin flip, specify 'heads' or 'tails'.")
                    if actual_game_type: result = self.play_gambling_game(actual_game_type, bet_amount, **game_kwargs)
                    else: result = {'success': False, 'message': f"Unknown game: {game_type_arg}"}
                except ValueError as e: result = {'success': False, 'message': str(e)}
                except IndexError: result = {'success': False, 'message': "Invalid 'play' command format."}
            elif command == 'gambling stats': 
                stats = self.get_gambling_stats()
                if stats['total_games_played'] > 0:
                    stats_msg = [f"Games: {s['total_games_played']}, Won: {s['total_won']}, Lost: {s['total_lost']}, Net: {s['net_profit']}" for s_type, s in stats['games'].items()] # Simplified
                    result = {'success': True, 'message': f"Overall: {stats['total_games_played']} played, Net: {stats['net_profit']}\n" + "\n".join(stats_msg)}
                else: result = {'success': False, 'message': "No gambling stats yet."}
        
        # Only update if not awaiting confirmation
        if not self.pending_command:
            self.update() 
        
        result['recent_events'] = self.event_formatter.get_formatted_events()
        return result

    def _check_bounty_objective_triggers(self):
        player_id = self.player.id
        active_bounty_ids_copy = list(self.player.active_bounty_ids) 

        for bounty_id in active_bounty_ids_copy:
            bounty = self.bounty_manager.get_bounty(bounty_id)
            if not bounty or bounty.status != BountyStatus.ACCEPTED or bounty.accepted_by_player_id != player_id:
                continue

            active_objective = bounty.get_active_objective()
            if not active_objective or active_objective.is_completed or not active_objective.is_active:
                continue

            if active_objective.type == "discover_location":
                if self.room_manager.current_room_id == active_objective.target_id:
                    success, msg = self.bounty_manager.update_bounty_progress(player_id, bounty_id, active_objective.id)
                    if success: self._add_event(msg, "bounty")
            
    def _check_bounty_objective_report_to_npc(self, interacted_npc_id: str):
        player_id = self.player.id
        active_bounty_ids_copy = list(self.player.active_bounty_ids)

        for bounty_id in active_bounty_ids_copy:
            bounty = self.bounty_manager.get_bounty(bounty_id)
            if not bounty or bounty.status != BountyStatus.ACCEPTED or bounty.accepted_by_player_id != player_id:
                continue
            
            active_objective = bounty.get_active_objective()
            if not active_objective or active_objective.is_completed or not active_objective.is_active:
                continue

            if active_objective.type == "report_to_npc" and active_objective.target_id == interacted_npc_id:
                success, msg = self.bounty_manager.update_bounty_progress(player_id, bounty_id, active_objective.id)
                if success: self._add_event(msg, "bounty")


    def _handle_read_notice_board(self) -> Dict[str, Any]:
        if self.room_manager.current_room_id != "tavern_main":
            return {"success": False, "message": "You need to be in the Tavern Common Area to read the notice board."}
        current_room = self.room_manager.current_room
        if not current_room or not any(feature["id"] == "notice_board" for feature in current_room.features):
            return {"success": False, "message": "There is no notice board here."}
        available_bounties = self.bounty_manager.get_available_bounties_on_notice_board(self.player) 
        if not available_bounties: return {"success": True, "message": "The notice board is empty."}
        bounty_listings = []
        for bounty in available_bounties:
            listing = f"- {bounty.title} (ID: {bounty.id})\n  Description: {bounty.description}\n  Issued by: {bounty.issuer}\n  Reward: {bounty.rewards.gold or 0} gold"
            if bounty.reputation_requirement:
                listing += f"\n  (Requires: {bounty.reputation_requirement.min_tier} with {bounty.reputation_requirement.npc_id})"
            if bounty.rewards.items: 
                item_names = []
                for item_reward_dict in bounty.rewards.items: 
                    item_id = item_reward_dict.get("item_id")
                    item_def = ITEM_DEFINITIONS.get(item_id) if item_id else None
                    item_names.append(item_def.name if item_def else str(item_id)) 
                if item_names: listing += f", Items: {', '.join(item_names)}"
            bounty_listings.append(listing)
        return {"success": True, "message": "Available Bounties:\n" + "\n\n".join(bounty_listings), "data": {"bounties": [b.model_dump() for b in available_bounties]}}

    def _handle_accept_bounty(self, bounty_id: str) -> Dict[str, Any]:
        if self.room_manager.current_room_id != "tavern_main":
             return {"success": False, "message": "You must be at the notice board in the Tavern Common Area to accept a bounty."}
        current_room = self.room_manager.current_room
        if not current_room or not any(feature["id"] == "notice_board" for feature in current_room.features):
            return {"success": False, "message": "There is no notice board here to accept bounties from."}
        
        current_time_float = self.clock.current_time_hours if hasattr(self.clock, 'current_time_hours') else float(self.clock.current_time)
        success, message = self.bounty_manager.accept_bounty(bounty_id=bounty_id, player_state=self.player, current_game_time=current_time_float)
        
        if success:
            bounty_accepted_obj = self.bounty_manager.get_bounty(bounty_id) 
            if not hasattr(self.player, 'active_bounty_ids'): self.player.active_bounty_ids = set() 
            self.player.active_bounty_ids.add(bounty_id) 
            self.event_formatter.add_event('bounty_accepted', bounty_title=bounty_accepted_obj.title if bounty_accepted_obj else bounty_id) # type: ignore
            return {"success": True, "message": message}
        return {"success": False, "message": message}

    def _handle_status(self) -> Dict[str, Any]:
        status_data = {
            "time": self.clock.get_formatted_time(), "gold": self.player.gold, "has_room": self.player.has_room,
            "tiredness": f"{self.player.tiredness*100:.0f}%", "energy": f"{self.player.energy*100:.0f}%",
            "status_effects": ", ".join(self.player.get_status_effects()), 
            "resolve": self.player.get_stat("resolve"), 
            "stamina": f"{self.player.get_stat('current_stamina')}/{self.player.get_stat('max_stamina')}" 
        }
        if self.player.has_room and self.player.room_id:
            room = self.room_manager.get_room(self.player.room_id)
            if room and room.has_storage_chest:
                status_data["storage_chest"] = "Available in your room"

        if self.economy.current_event: 
            status_data["current_event"] = self.economy.current_event["name"]
            status_data["event_description"] = self.economy.current_event["description"]
        active_bounties_info = []
        player_active_bounties = getattr(self.player, 'active_bounty_ids', set())
        if player_active_bounties:
            for b_id in player_active_bounties: 
                bounty = self.bounty_manager.get_bounty(b_id) 
                if bounty and bounty.status == BountyStatus.ACCEPTED: 
                    active_obj_desc = self.bounty_manager.get_active_objective_description(self.player.id, b_id) or "N/A"
                    active_bounties_info.append(f"{bounty.title} (ID: {b_id}) - Current Objective: {active_obj_desc}")
        status_data["active_bounties"] = active_bounties_info if active_bounties_info else "None"
        return {"success": True, "message": "Player status:", "data": status_data}

    def _handle_inventory(self) -> Dict[str, Any]:
        items_data = self.player.inventory.list_items_for_display()
        inventory_info = {"items": items_data, "count": self.player.inventory.get_total_items(), 
                          "total_quantity": self.player.inventory.get_total_quantity(), "gold": self.player.gold}
        return {"success": True, "message": "Your inventory:", "data": inventory_info}

    def _handle_buy(self, item_id: str) -> Dict[str, Any]:
        item_id_lower = item_id.lower()
        item_to_buy: Optional[Item] = None
        if self.travelling_merchant_active and item_id_lower in self.travelling_merchant_temporary_items:
            merchant_npc = self.npc_manager.get_npc(self.travelling_merchant_npc_id)
            if merchant_npc:
                for item_in_merchant_inventory in merchant_npc.inventory:
                    if item_in_merchant_inventory.id == item_id_lower: item_to_buy = item_in_merchant_inventory; break
        if not item_to_buy: item_to_buy = ITEM_DEFINITIONS.get(item_id_lower) 
        if not item_to_buy: return {"success": False, "message": f"Item '{item_id}' is not available."}
        price = self.economy.get_item_price(item_id_lower, game_state=self) 
        if price is None: return {"success": False, "message": f"Cannot price {item_to_buy.name}."}
        if not self.player.spend_gold(price): return {"success": False, "message": f"Not enough gold for {item_to_buy.name}."}
        success, add_msg = self.player.inventory.add_item(item_id_to_add=item_to_buy.id, quantity=1)
        if not success: self.player.add_gold(price); return {"success": False, "message": f"Failed to add: {add_msg}"}
        self._add_event(f"Bought {item_to_buy.name} for {price} gold.", "success") 
        self.event_formatter.add_event('item_bought', item_name=item_to_buy.name, price=price) 
        return {"success": True, "message": f"Bought {item_to_buy.name} for {price} gold.", "data": {"gold": self.player.gold}}

    def _handle_use(self, item_id: str) -> Dict[str, Any]:
        item_id_lower = item_id.lower()
        if not self.player.inventory.has_item(item_id_lower, quantity=1):
            return {"success": False, "message": f"You don't have {item_id}."}
        
        item_def = ITEM_DEFINITIONS.get(item_id_lower) 
        if not item_def: return {"success": False, "message": "Error finding item definition."}

        current_time_float = self.clock.current_time_hours if hasattr(self.clock, 'current_time_hours') else float(self.clock.current_time)
        consume_success = self.player.consume_item_and_apply_effects(item_def, current_time_float)

        if consume_success:
            self.event_formatter.add_event('item_used', item_name=item_def.name)
            return {"success": True, "message": f"Used {item_def.name}."} 
        return {"success": False, "message": f"Could not use {item_def.name}."}


    def _handle_available_jobs(self) -> Dict[str, Any]:
        jobs = self.economy.get_available_jobs(self.player.energy)
        if not jobs: 
            return {"success": True, "message": "No jobs available."}
        
        # Format jobs list for display
        job_descriptions = []
        for i, job in enumerate(jobs):
            job_desc = f"{i+1}. {job['name']}: {job['description']} (Reward: {job['base_reward']} gold, Tiredness: +{job['tiredness_cost']*100:.0f}%)"
            job_descriptions.append(job_desc)
        
        message = "Available jobs:\n" + "\n".join(job_descriptions)
        return {"success": True, "message": message}

    def _handle_work(self, job_id: str) -> Dict[str, Any]:
        result = self.economy.perform_job(job_id, self.player.energy)
        if not result["success"]: return {"success": False, "message": result["message"]}
        self.player.add_gold(result["reward"])
        self.player.tiredness = min(1.0, self.player.tiredness + result["tiredness"])
        for item_data in result.get("items", []): 
            self.player.inventory.add_item(item_id_to_add=item_data["id"], quantity=item_data.get("quantity",1))
        self.event_formatter.add_event('job_completed', job_name=job_id, reward=result["reward"])
        response_data = {"reward": result["reward"], "tiredness_increase": result["tiredness"]}
        if "items" in result and result["items"]: response_data["items_received"] = [item_data["id"] for item_data in result["items"]]
        return {"success": True, "message": result["message"], "data": response_data}

    def _handle_look(self) -> Dict[str, Any]:
        time_desc = self.clock.time.format_time()
        
        if self.player.has_room:
            room_desc = "You are in your rented room upstairs. It's small but comfortable, with a bed, a small table, and a window overlooking the street."
        else:
            room_desc = """
You are in the common area of the Rusted Tankard tavern. 
The room is dimly lit by lanterns and a fire crackling in a stone hearth. 
Wooden tables and chairs are scattered around, some occupied by patrons.
A long bar runs along one wall, where the barkeeper serves drinks.
A staircase leads up to the rooms for rent.
            """
            
        # Get information about present NPCs
        npc_descriptions = []
        for npc in self.npc_manager.get_present_npcs():
            npc_descriptions.append(f"{npc.name} is here. {npc.description}")
            
        npc_text = "\n".join(npc_descriptions) if npc_descriptions else "There's no one of interest here at the moment."
        
        # Add atmosphere description if Phase 2 is available
        atmosphere_desc = ""
        if PHASE2_AVAILABLE and hasattr(self, 'atmosphere_manager'):
            current_atmosphere = self.atmosphere_manager.get_current_atmosphere()
            if current_atmosphere.get('tension', 0) > 0.7:
                atmosphere_desc = "\nThe atmosphere is tense - you can feel it in the air."
            elif current_atmosphere.get('comfort', 0) > 0.8:
                atmosphere_desc = "\nThe atmosphere is warm and inviting."
            elif current_atmosphere.get('mystery', 0) > 0.6:
                atmosphere_desc = "\nThere's something mysterious in the air..."
        
        # Add narrative context if Phase 4 is available
        narrative_hint = ""
        if PHASE4_AVAILABLE and hasattr(self, 'thread_manager'):
            active_threads = self.thread_manager.get_active_threads()
            if active_threads:
                high_tension_threads = [t for t in active_threads if t.tension_level > 0.6]
                if high_tension_threads:
                    narrative_hint = f"\n\n[Something important seems to be happening: {high_tension_threads[0].title}]"
        
        full_description = f"It is {time_desc}.\n\n{room_desc.strip()}{atmosphere_desc}\n\n{npc_text}\n\nYou have {self.player.gold} gold. Tiredness: {int(self.player.tiredness*100)}%{narrative_hint}"
        return {'success': True, 'message': full_description}
    
    def _handle_wait(self, hours: float = 1.0) -> Dict[str, Any]:
        if hours <= 0: return {'success': False, 'message': "Time only moves forward."}
        self.clock.advance_time(hours) 
        return {'success': True, 'message': f"You wait for {hours:.1f} hours. {self.clock.time.format_time()}", 'time_advanced': hours}
        
    def _handle_sleep(self, hours: float = 8.0) -> Dict[str, Any]:
        if hours <= 0: return {'success': False, 'message': "Can't sleep for negative time!"}
        if not self.player.has_room: self.event_formatter.add_event('sleep_failure'); return {'success': False, 'message': "Need a room to sleep."}
        sleep_hours = min(hours, 24.0)
        self.clock.advance_time(sleep_hours)
        self.player.tiredness = 0.0 
        self.event_formatter.add_event('sleep_success', hours=sleep_hours, room_id=self.player.room_id)
        return {'success': True, 'message': f"Slept {sleep_hours:.1f} hours. Refreshed! {self.clock.time.format_time()}", 'time_advanced': sleep_hours}
            
    def _handle_rent_room_command(self, with_chest: bool) -> Dict[str, Any]:
        # If player already has a room and items in storage, and is trying to rent a *different* room
        if self.player.has_room and self.player.room_id and not self.player.storage_inventory.is_empty():
            # Find any available new room to check if it's different
            new_available_room_id = None
            for r_id, r_obj in self.room_manager.rooms.items():
                 if r_id != "tavern_main" and r_id != "deep_cellar" and not r_obj.is_occupied and r_id != self.player.room_id:
                     new_available_room_id = r_id
                     break
            
            if new_available_room_id: # If they are trying to rent a new, different room
                self.pending_command = {"type": "confirm_rent", "params": {"with_chest": with_chest}}
                return {"success": True, 
                        "message": "Warning: You have items in your current room's storage. Renting a new room will empty this storage. Proceed? (yes/no)"}
        
        # If no items in storage, or renting the same room again (e.g. to add a chest), proceed directly
        return self._execute_rent_room(with_chest=with_chest)

    def _execute_rent_room(self, with_chest: bool) -> Dict[str, Any]:
        # Clear storage if player had a room and is now renting (implies new room or re-renting old one after expiry)
        if self.player.has_room and self.player.room_id and not self.player.storage_inventory.is_empty():
            self.player.storage_inventory.items.clear() # Clear the storage
            self._add_event("Your previous room storage has been cleared.", "info")

        success, rented_room_id_or_msg, message = self.room_manager.rent_room(self.player, with_storage_chest=with_chest)
        
        if success and rented_room_id_or_msg:
            self.event_formatter.add_event('rent_success', amount=self.room_manager.get_room(rented_room_id_or_msg).price_per_night, room_id=rented_room_id_or_msg) # type: ignore
            return {'success': True, 'message': message}
        return {'success': False, 'message': rented_room_id_or_msg} # This will be the failure message from RoomManager

    def _handle_store_item(self, item_id: str, quantity: int) -> Dict[str, Any]:
        if not self.player.has_room or not self.player.room_id:
            return {"success": False, "message": "You need to rent a room with a storage chest first."}
        room = self.room_manager.get_room(self.player.room_id)
        if not room or not room.has_storage_chest:
            return {"success": False, "message": "Your current room doesn't have a storage chest."}

        if not self.player.inventory.has_item(item_id, quantity):
            return {"success": False, "message": f"You don't have {quantity} of {item_id}."}

        item_def = ITEM_DEFINITIONS.get(item_id)
        if not item_def: return {"success": False, "message": "Item definition not found."} # Should not happen if has_item passed

        remove_success, remove_msg = self.player.inventory.remove_item(item_id, quantity)
        if not remove_success:
            return {"success": False, "message": remove_msg}
        
        # Add to storage_inventory (which uses Item object, not just item_id)
        add_success, add_msg = self.player.storage_inventory.add_item(item_def, quantity)
        if not add_success:
            # Rollback: add back to player inventory
            self.player.inventory.add_item(item_def, quantity)
            return {"success": False, "message": f"Failed to store item in chest: {add_msg}"}
        
        return {"success": True, "message": f"Stored {quantity} x {item_def.name} in your room's chest."}

    def _handle_retrieve_item(self, item_id: str, quantity: int) -> Dict[str, Any]:
        if not self.player.has_room or not self.player.room_id:
            return {"success": False, "message": "You need to be in your rented room to access storage."}
        room = self.room_manager.get_room(self.player.room_id)
        if not room or not room.has_storage_chest:
            return {"success": False, "message": "Your current room doesn't have a storage chest."}

        if not self.player.storage_inventory.has_item(item_id, quantity):
            return {"success": False, "message": f"Cannot retrieve {quantity} of {item_id}. Not that many in storage."}

        item_def = ITEM_DEFINITIONS.get(item_id)
        if not item_def: return {"success": False, "message": "Item definition not found."}

        remove_success, remove_msg = self.player.storage_inventory.remove_item(item_id, quantity)
        if not remove_success:
            return {"success": False, "message": remove_msg}

        add_success, add_msg = self.player.inventory.add_item(item_def, quantity)
        if not add_success:
            # Rollback: add back to storage
            self.player.storage_inventory.add_item(item_def, quantity)
            return {"success": False, "message": f"Failed to add item to inventory: {add_msg}"}
            
        return {"success": True, "message": f"Retrieved {quantity} x {item_def.name} from your chest."}

    def _handle_check_storage(self) -> Dict[str, Any]:
        if not self.player.has_room or not self.player.room_id:
            return {"success": False, "message": "You need to be in your rented room to access storage."}
        room = self.room_manager.get_room(self.player.room_id)
        if not room or not room.has_storage_chest:
            return {"success": False, "message": "Your current room doesn't have a storage chest."}

        if self.player.storage_inventory.is_empty():
            return {"success": True, "message": "Your storage chest is empty."}

        items_in_storage = self.player.storage_inventory.list_items_for_display()
        storage_list = [f"{item_data['name']} (x{item_data['quantity']})" for item_data in items_in_storage]
        return {"success": True, "message": "Items in your storage chest:\n" + "\n".join(storage_list)}
    
    def _create_initial_narrative_threads(self):
        """Create initial narrative threads based on game state"""
        if not PHASE4_AVAILABLE or not hasattr(self, 'thread_manager'):
            return
        
        # Create main tavern thread
        tavern_thread = StoryThread(
            id="tavern_main_thread",
            title="The Living Rusted Tankard",
            type=ThreadType.MAIN,
            description="The ongoing story of the tavern and its patrons",
            primary_participants=["player", "bartender"],
            tension_level=0.2
        )
        self.thread_manager.add_thread(tavern_thread)
        
        # Create threads for NPCs with secrets
        if PHASE3_AVAILABLE:
            for npc_id, npc in self.npc_manager.npcs.items():
                if hasattr(npc, 'has_secret') and npc.has_secret:
                    secret_thread = StoryThread(
                        id=f"secret_{npc_id}",
                        title=f"{npc.name}'s Secret",
                        type=ThreadType.MYSTERY,
                        description=f"Uncover the truth about {npc.name}",
                        primary_participants=["player", npc_id],
                        tension_level=0.4
                    )
                    self.thread_manager.add_thread(secret_thread)


    def save_game(self, filename: str) -> bool:
        try: 
            import json 
            save_data = self.to_dict() 
            save_data["save_timestamp"] = datetime.now().isoformat() 
            with open(filename, 'w') as f: 
                json.dump(save_data, f, indent=2)
            self._add_event(f"Game saved to {filename}", "success")
            return True
        except Exception as e: self._add_event(f"Failed to save game: {str(e)}", "error"); return False
    
    def load_game(self, filename: str) -> bool:
        try: 
            import json 
            with open(filename, 'r') as f: 
                save_data_dict = json.load(f)
            temp_gs = GameState.from_dict(save_data_dict, data_dir=str(self._data_dir))
            self.clock = temp_gs.clock
            self.player = temp_gs.player
            self.room_manager = temp_gs.room_manager
            self.npc_manager = temp_gs.npc_manager
            self.economy = temp_gs.economy
            self.gambling_manager = temp_gs.gambling_manager
            self.bounty_manager = temp_gs.bounty_manager
            self.news_manager = temp_gs.news_manager 
            self.active_global_events = temp_gs.active_global_events 
            self.events = temp_gs.events
            self._last_update_time = temp_gs._last_update_time
            self.travelling_merchant_active = temp_gs.travelling_merchant_active
            self.travelling_merchant_npc_id = temp_gs.travelling_merchant_npc_id
            self.travelling_merchant_arrival_time = temp_gs.travelling_merchant_arrival_time
            self.travelling_merchant_departure_time = temp_gs.travelling_merchant_departure_time
            self.travelling_merchant_temporary_items = temp_gs.travelling_merchant_temporary_items
            self._data_dir = temp_gs._data_dir 
            self.pending_command = temp_gs.pending_command
            
            self._add_event("Game loaded successfully!", "success")
            return True
        except Exception as e: 
            self._add_event(f"Failed to load game: {str(e)}", "error")
            return False

    def get_snapshot(self) -> Dict[str, Any]: return self.snapshot_manager.create_snapshot()
    
    # ==================== DATABASE PERSISTENCE METHODS ====================
    
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
    
    def to_persistence_model(self) -> Dict[str, Any]:
        """Convert to database persistence format."""
        return {
            "id": self._db_id,
            "session_id": self._session_id,
            "player_name": getattr(self.player, 'name', 'Unknown Player'),
            "game_data": self.to_dict(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    @classmethod
    def from_persistence_data(cls, data: Dict[str, Any], data_dir: str = "data") -> 'GameState':
        """Create from database persistence data."""
        session_id = data.get("session_id")
        db_id = data.get("id")
        game_data = data.get("game_data", {})
        
        # Create instance using from_dict with session info
        instance = cls.from_dict(game_data, data_dir=data_dir, session_id=session_id, db_id=db_id)
        instance.set_db_id(db_id)
        instance.mark_clean()
        return instance
    
    # ==================== PERFORMANCE OPTIMIZATION METHODS ====================
    
    def get_present_npcs_optimized(self) -> List[Any]:
        """Get present NPCs with caching optimization."""
        current_time = time.time()
        
        # Check cache validity
        if (self._present_npcs_cache and 
            current_time - self._npc_cache_timestamp < self._npc_cache_ttl):
            return list(self._present_npcs_cache.values())
        
        # Cache miss - rebuild cache
        present_npcs = self.npc_manager.get_present_npcs()
        self._present_npcs_cache = {npc.id: npc for npc in present_npcs}
        self._present_npcs_set = {npc.id for npc in present_npcs}
        self._npc_cache_timestamp = current_time
        
        return present_npcs
    
    def _invalidate_npc_cache(self) -> None:
        """Invalidate the NPC cache."""
        self._npc_cache_timestamp = 0.0
        self._present_npcs_cache.clear()
        self._present_npcs_set.clear()
    
    def get_snapshot_optimized(self) -> Dict[str, Any]:
        """Get game state snapshot with caching."""
        current_time = time.time()
        
        # Check cache validity
        if (self._snapshot_cache and not self._snapshot_dirty and
            current_time - self._snapshot_timestamp < self._snapshot_ttl):
            return self._snapshot_cache.copy()
        
        # Generate fresh snapshot
        snapshot = self.get_snapshot()
        
        # Cache the snapshot
        self._snapshot_cache = snapshot.copy()
        self._snapshot_timestamp = current_time
        self._snapshot_dirty = False
        
        return snapshot
    
    def _process_event_batch(self) -> None:
        """Process batched events for better performance."""
        if not self._event_batch:
            return
        
        current_time = time.time()
        if (len(self._event_batch) >= self._event_batch_size or
            current_time - self._last_event_process > 1.0):  # Process every second at least
            
            # Process all batched events
            for event_data in self._event_batch:
                # Could add batch event processing logic here
                pass
            
            self._event_batch.clear()
            self._last_event_process = current_time
    
    def _add_event_optimized(self, message: str, event_type: str = "info", data: Optional[Dict[str, Any]] = None) -> None:
        """Add event with batching optimization."""
        # Add to batch instead of immediate processing
        self._event_batch.append({
            "message": message,
            "event_type": event_type,
            "data": data or {},
            "timestamp": time.time()
        })
        
        # Also add to immediate events for backward compatibility
        self._add_event(message, event_type, data)
        
        # Mark snapshot as dirty
        self._snapshot_dirty = True
    
    # ==================== ENHANCED UPDATE METHODS ====================
    
    def update_optimized(self, delta_override: Optional[float] = None) -> None:
        """Optimized update method with performance tracking."""
        start_time = time.time()
        
        # Call standard update
        self.update(delta_override)
        
        # Process any pending events in batch
        self._process_event_batch()
        
        # Mark snapshot as dirty
        self._snapshot_dirty = True
        
        # Invalidate NPC cache
        self._invalidate_npc_cache()
        
        # Mark for database save
        self.mark_dirty()
    
    def process_command_enhanced(self, command: str) -> Dict[str, Any]:
        """Process command with database marking and optimization."""
        result = self.process_command(command)
        self.mark_dirty()  # Any command changes state
        self._snapshot_dirty = True  # Invalidate snapshot cache
        return result
    
    # ==================== HELPER METHODS ====================

    def _generate_help_text(self) -> str:
        """Generate help text showing available commands."""
        help_text = """
Available Commands:
------------------
status    - Check your current status (health, gold, etc.)
inventory - View your inventory and gold
look      - Look around and examine your surroundings
talk [person] - Talk to someone nearby (or list available people)
buy [item] - Buy an item (or list items for sale)
use [item] - Use an item from your inventory
time      - Check the current time
rest      - Rest to recover energy
work      - List available jobs
rent room - Rent a room at the tavern
help      - Display this help message

Advanced Commands:
----------------
gamble [amount] - Try your luck with gambling
store/retrieve - Store or retrieve items (if you have a room with storage)
bounty/quests  - Check available bounties and quests

Type 'quit' to exit the game.
"""
        return help_text
