"""NPC system for The Living Rusted Tankard."""
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable, Set, TYPE_CHECKING
import random
from pydantic import BaseModel, Field

from .items import Item, TAVERN_ITEMS

if TYPE_CHECKING:
    from ..models.player import PlayerState
    from ..core.events import EventBus
    from ..core.economy import Economy


class NPCType(Enum):
    """Types of NPCs in the game."""
    BARKEEP = auto()
    PATRON = auto()
    MERCHANT = auto()
    GUARD = auto()
    BARD = auto()
    THIEF = auto()
    ADVENTURER = auto()
    NOBLE = auto()
    SERVANT = auto()
    COOK = auto()


class NPCDisposition(Enum):
    """Possible dispositions of NPCs."""
    FRIENDLY = auto()
    NEUTRAL = auto()
    UNFRIENDLY = auto()
    HOSTILE = auto()


class NPCSkill(BaseModel):
    """Represents a skill that an NPC has."""
    name: str
    level: float  # 0.0 to 1.0


class NPCInteraction(BaseModel):
    """Represents a possible interaction with an NPC."""
    id: str
    name: str
    description: str
    condition: Optional[Callable[['NPC', 'PlayerState'], bool]] = None
    action: Callable[['NPC', 'PlayerState', 'Economy'], Dict[str, Any]]
    cooldown: float = 0  # Hours before this interaction can be used again
    last_used: float = -1  # Game time when this was last used


class NPC(BaseModel):
    """Represents a non-player character in the game."""
    id: str
    name: str
    description: str
    npc_type: NPCType
    disposition: NPCDisposition = NPCDisposition.NEUTRAL
    schedule: List[Tuple[float, float]] = Field(default_factory=list)  # (start_hour, end_hour)
    departure_chance: float = 0.1  # 0.0 to 1.0
    visit_frequency: float = 0.8  # 0.0 to 1.0, chance to visit when scheduled
    gold: int = 0
    inventory: List[Item] = Field(default_factory=list)
    relationships: Dict[str, float] = Field(default_factory=dict)  # NPC/player ID -> relationship score
    conversation_topics: List[str] = Field(default_factory=list)
    current_topic: Optional[str] = None
    last_visit_day: int = -1
    is_present: bool = False
    skills: Dict[str, NPCSkill] = Field(default_factory=dict)
    interactions: Dict[str, NPCInteraction] = Field(default_factory=dict)
    current_room: Optional[str] = Field(default=None, description="ID of the room the NPC is currently in")

    def update_presence(self, current_time: float, event_bus = None) -> bool:
        """Update the NPC's presence based on the current time.

        Args:
            current_time: Current game time in hours
            event_bus: Optional event bus or game state to dispatch events to

        Returns:
            bool: True if presence state changed, False otherwise
        """
        was_present = self.is_present
        current_hour = current_time % 24
        current_day = int(current_time // 24)

        # Check if NPC is scheduled to be here now
        scheduled = False
        for start, end in self.schedule:
            if start < end:
                # Normal case: schedule within the same day (e.g., 9-17)
                if start <= current_hour < end:
                    scheduled = True
                    break
            else:
                # Special case: schedule spans midnight (e.g., 20-4)
                if current_hour >= start or current_hour < end:
                    scheduled = True
                    break

        # If not scheduled, NPC should not be present
        if not scheduled:
            if self.is_present:
                self.is_present = False
                if event_bus:
                    from .events.npc_events import NPCDepartEvent
                    if hasattr(event_bus, 'event_bus') and hasattr(event_bus.event_bus, 'dispatch'):
                        # If event_bus is GameState with an event_bus attribute
                        event_bus.event_bus.dispatch(NPCDepartEvent(self, "not_scheduled"))
                    elif hasattr(event_bus, 'dispatch'):
                        # If event_bus is an event bus directly
                        event_bus.dispatch(NPCDepartEvent(self, "not_scheduled"))
                return True
            return False

        # If this is a new day, update the last visit day and check if NPC visits
        if self.last_visit_day < current_day:
            self.last_visit_day = current_day
            will_visit = random.random() <= self.visit_frequency

            if will_visit != self.is_present:
                self.is_present = will_visit
                if event_bus:
                    from .events.npc_events import NPCSpawnEvent, NPCDepartEvent
                    if will_visit:
                        if hasattr(event_bus, 'event_bus') and hasattr(event_bus.event_bus, 'dispatch'):
                            event_bus.event_bus.dispatch(NPCSpawnEvent(self))
                        elif hasattr(event_bus, 'dispatch'):
                            event_bus.dispatch(NPCSpawnEvent(self))
                    else:
                        if hasattr(event_bus, 'event_bus') and hasattr(event_bus.event_bus, 'dispatch'):
                            event_bus.event_bus.dispatch(NPCDepartEvent(self, "visit_ended"))
                        elif hasattr(event_bus, 'dispatch'):
                            event_bus.dispatch(NPCDepartEvent(self, "visit_ended"))
                return True

        # If it's the same day and NPC is not present but should be, make them present
        if self.last_visit_day == current_day and not self.is_present and scheduled:
            self.is_present = True
            if event_bus:
                from .events.npc_events import NPCSpawnEvent
                if hasattr(event_bus, 'event_bus') and hasattr(event_bus.event_bus, 'dispatch'):
                    event_bus.event_bus.dispatch(NPCSpawnEvent(self))
                elif hasattr(event_bus, 'dispatch'):
                    event_bus.dispatch(NPCSpawnEvent(self))
            return True
        
        # If NPC is present, check for random departure
        if self.is_present and random.random() < self.departure_chance:
            self.is_present = False
            if event_bus:
                from .events.npc_events import NPCDepartEvent
                event_bus.dispatch(NPCDepartEvent(self, "random_departure"))
            return True
            
        return was_present != self.is_present
        
    def modify_relationship(self, player_id: str, change: float, 
                           event_bus: Optional['EventBus'] = None) -> float:
        """Modify this NPC's relationship with a player.
        
        Args:
            player_id: ID of the player
            change: Amount to change the relationship by
            event_bus: Optional event bus to dispatch events to
            
        Returns:
            float: New relationship value
        """
        old_value = self.relationships.get(player_id, 0)
        new_value = max(-1.0, min(1.0, old_value + change))
        self.relationships[player_id] = new_value
        
        if event_bus and abs(change) > 0.01:  # Only dispatch if meaningful change
            from .events.npc_events import NPCRelationshipChangeEvent
            event_bus.dispatch(NPCRelationshipChangeEvent(
                self, player_id, change, new_value))
                
        return new_value
        
    def interact(self, player: 'PlayerState', interaction_type: str = "talk", 
                 event_bus: Optional['EventBus'] = None, **kwargs) -> Dict[str, Any]:
        """Handle an interaction with this NPC.
        
        Args:
            player: The player interacting with the NPC
            interaction_type: Type of interaction (talk, trade, etc.)
            event_bus: Optional event bus to dispatch events to
            **kwargs: Additional interaction data
            
        Returns:
            Dict with interaction results
        """
        if not self.is_present:
            return {"success": False, "message": f"{self.name} is not available right now."}
            
        # Default interaction logic can be overridden by specific NPCs
        if interaction_type == "talk":
            response = self._handle_conversation(player, **kwargs)
        else:
            response = {"success": False, "message": "I'm not sure what you want from me."}
            
        # Dispatch interaction event if event bus is available
        if event_bus is not None:
            from .events.npc_events import NPCInteractionEvent
            try:
                # Try dispatching the event
                if hasattr(event_bus, 'dispatch'):
                    event_bus.dispatch(NPCInteractionEvent(
                        self, player, interaction_type, **kwargs))
                # Also try notifying observers if the event bus is a GameState
                elif hasattr(event_bus, '_notify_observers'):
                    event_bus._notify_observers('npc_interaction', {
                        'npc_id': self.id,
                        'player_id': player.player_id,
                        'interaction_type': interaction_type,
                        'data': kwargs
                    })
            except Exception as e:
                # Log the error but don't fail the interaction
                print(f"Error dispatching NPC interaction event: {e}")
                
        return response
        
    def _handle_conversation(self, player: 'PlayerState', topic: str = None, **kwargs) -> Dict[str, Any]:
        """Handle conversation with this NPC.
        
        Args:
            player: The player conversing with the NPC
            topic: Optional topic of conversation
            
        Returns:
            Dict with conversation response
        """
        if not topic:
            # Default greeting
            return {
                "success": True,
                "message": f"{self.name} nods in your direction.",
                "topics": self.conversation_topics
            }
            
        if topic in self.conversation_topics:
            # Simple response based on topic
            responses = {
                "tavern": "The Rusted Tankard has seen better days, but it's home.",
                "drinks": "I'll have whatever's on tap.",
                "rumors": "I've heard whispers in the dark... but that's all I'll say.",
            }
            return {
                "success": True,
                "message": responses.get(topic, "I don't have much to say about that."),
                "topics": self.conversation_topics
            }
            
        return {
            "success": False,
            "message": "I'm not sure what you're talking about.",
            "topics": self.conversation_topics
        }


class NPCManager:
    """Manages all NPCs in the game."""
    
    def __init__(self, data_dir: str = "data", event_bus = None):
        """Initialize the NPC manager.
        
        Args:
            data_dir: Directory containing NPC data files
            event_bus: Optional event bus to dispatch events to
        """
        self.npcs: Dict[str, NPC] = {}
        self.data_dir = Path(data_dir)
        self.event_bus = event_bus
        self._initialize_npcs()
    
    def _initialize_npcs(self) -> None:
        """Initialize the NPCs by loading them from JSON files."""
        npc_file = self.data_dir / "npcs.json"
        
        if not npc_file.exists():
            print(f"Warning: NPC data file not found at {npc_file}")
            self._create_default_npcs()
            return
            
        try:
            import json
            with open(npc_file, 'r') as f:
                data = json.load(f)
                
            for npc_data in data.get("npc_definitions", []):
                try:
                    # Convert string enums to their enum values
                    npc_data["npc_type"] = NPCType[npc_data["npc_type"]]
                    npc_data["disposition"] = NPCDisposition[npc_data.get("disposition", "NEUTRAL")]
                    
                    # Convert schedule to list of tuples
                    if "schedule" in npc_data:
                        npc_data["schedule"] = [tuple(period) for period in npc_data["schedule"]]
                    
                    # Process inventory items - look up full item definitions
                    if "inventory" in npc_data:
                        full_inventory = []
                        for item_data in npc_data["inventory"]:
                            item_id = item_data.get("id")
                            if item_id in TAVERN_ITEMS:
                                full_inventory.append(TAVERN_ITEMS[item_id])
                            else:
                                print(f"Warning: Unknown item {item_id} in {npc_data.get('id', 'unknown')}'s inventory")
                        npc_data["inventory"] = full_inventory
                    
                    # Create the NPC
                    npc = NPC(**npc_data)
                    self.add_npc(npc)
                    
                    # Dispatch spawn event for initially present NPCs
                    if npc.is_present and self.event_bus:
                        from .events.npc_events import NPCSpawnEvent
                        self.event_bus.dispatch(NPCSpawnEvent(npc))
                    
                except (KeyError, ValueError) as e:
                    print(f"Error loading NPC {npc_data.get('id', 'unknown')}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error loading NPCs from {npc_file}: {e}")
            self._create_default_npcs()
            
    def _create_default_npcs(self) -> None:
        """Create default NPCs if loading from file fails."""
        print("Creating default NPCs...")
        
        # Create a basic barkeeper NPC
        barkeep = NPC(
            id="barkeep",
            name="Old Tom",
            description="The grizzled barkeep of The Rusted Tankard.",
            npc_type=NPCType.BARKEEP,
            disposition=NPCDisposition.FRIENDLY,
            schedule=[(8, 24)],  # 8 AM to midnight
            visit_frequency=1.0,  # Always present during schedule
            departure_chance=0.0,  # Never leaves early
            gold=100,
            conversation_topics=["tavern", "drinks", "rumors"],
            inventory=[TAVERN_ITEMS["ale"], TAVERN_ITEMS["stew"]]
        )
        self.add_npc(barkeep)
        
        # Create a regular patron
        patron = NPC(
            id="patron_regular",
            name="Marlin",
            description="A regular patron nursing a drink in the corner.",
            npc_type=NPCType.PATRON,
            disposition=NPCDisposition.NEUTRAL,
            schedule=[(12, 20)],  # Noon to 8 PM
            visit_frequency=0.8,
            gold=25,
            conversation_topics=["tavern", "drinks"],
            inventory=[TAVERN_ITEMS["ale"], TAVERN_ITEMS["bread"]]
        )
        self.add_npc(patron)
        
        # Create a merchant
        merchant = NPC(
            id="merchant",
            name="Garrick",
            description="A traveling merchant with exotic wares.",
            npc_type=NPCType.MERCHANT,
            disposition=NPCDisposition.FRIENDLY,
            schedule=[(10, 18)],  # 10 AM to 6 PM
            visit_frequency=0.6,
            gold=200,
            conversation_topics=["merchandise", "travel", "rumors"],
            inventory=[TAVERN_ITEMS["stew"], TAVERN_ITEMS["bread"]]
        )
        self.add_npc(merchant)
    
    def add_npc(self, npc: NPC) -> None:
        """Add an NPC to the manager."""
        self.npcs[npc.id] = npc
    
    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC by ID, if present."""
        return self.npcs.get(npc_id)
    
    def update_all_npcs(self, game_time: float) -> None:
        """Update presence for all NPCs based on current game time."""
        for npc in self.npcs.values():
            npc.update_presence(game_time, self.event_bus)
    
    def get_present_npcs(self) -> List[NPC]:
        """Get a list of all currently present NPCs."""
        return [npc for npc in self.npcs.values() if npc.is_present]
    
    def find_npc_by_name(self, name: str) -> Optional[NPC]:
        """Find an NPC by name (case-insensitive)."""
        name_lower = name.lower()
        for npc in self.npcs.values():
            if npc.name.lower() == name_lower:
                return npc
        return None
    
    def get_npcs_by_type(self, npc_type: NPCType) -> List[NPC]:
        """Get all NPCs of a specific type."""
        return [npc for npc in self.npcs.values() if npc.npc_type == npc_type]
    
    def interact_with_npc(self, npc_id: str, player: 'PlayerState', 
                         interaction_type: str = "talk", **kwargs) -> Dict[str, Any]:
        """Handle interaction with an NPC.
        
        Args:
            npc_id: ID of the NPC to interact with
            player: The player initiating the interaction
            interaction_type: Type of interaction (talk, trade, etc.)
            **kwargs: Additional interaction data
            
        Returns:
            Dict with interaction results
        """
        npc = self.get_npc(npc_id)
        if not npc:
            return {"success": False, "message": "NPC not found."}
            
        return npc.interact(player, interaction_type, self.event_bus, **kwargs)

    def get_interactive_npcs(self, player: 'PlayerState' = None) -> List[Dict[str, Any]]:
        """Get a list of present NPCs with their available interactions.
        
        Args:
            player: Optional player to check interactions against
            
        Returns:
            List of NPCs with their available interactions
        """
        interactive = []
        for npc in self.get_present_npcs():
            # Basic interaction is always available
            interactions = [{
                'id': 'talk',
                'name': 'Talk',
                'description': f'Strike up a conversation with {npc.name}'
            }]
            
            # Add any additional interactions based on relationship, etc.
            if npc.interactions:
                for interaction in npc.interactions.values():
                    if (interaction.condition is None or 
                        (player and interaction.condition(npc, player))):
                        interactions.append({
                            'id': interaction.id,
                            'name': interaction.name,
                            'description': interaction.description
                        })
            
            # Get relationship with player if available
            relationship = None
            if player:
                relationship = npc.relationships.get(player.id, 0)
            
            interactive.append({
                'id': npc.id,
                'name': npc.name,
                'description': npc.description,
                'relationship': relationship,
                'interactions': interactions
            })
                
        return interactive
