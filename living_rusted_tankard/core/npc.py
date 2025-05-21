"""NPC system for The Living Rusted Tankard."""
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable, Set, TYPE_CHECKING
import random
from pydantic import BaseModel, Field

from .items import Item, TAVERN_ITEMS
from .reputation import get_reputation, get_reputation_tier # Import reputation utilities

if TYPE_CHECKING:
    from .player import PlayerState # Corrected import path for PlayerState if it's in core
    from .events import EventBus # Corrected import path for EventBus if it's in core
    from .economy import Economy # Corrected import path for Economy if it's in core
# Note: The TYPE_CHECKING block might need to refer to PlayerState as '.player.PlayerState'
# if PlayerState is in the same directory, or adjust based on actual project structure.
# Assuming PlayerState is in core, so from .player import PlayerState
# from living_rusted_tankard.core.player import PlayerState # Alternative if path issues


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


from .callable_registry import get_interaction # Assuming registry provides get_interaction

class NPCInteraction(BaseModel):
    """Represents a possible interaction with an NPC."""
    id: str
    name: str
    description: str
    condition_name: Optional[str] = None  # Registered name of the condition callable
    action_name: str                   # Registered name of the action callable
    cooldown: float = 0  # Hours before this interaction can be used again
    last_used: float = -1  # Game time when this was last used

    # Helper properties to get the actual callables (runtime only)
    @property
    def condition(self) -> Optional[Callable[['NPC', 'PlayerState'], bool]]:
        if self.condition_name:
            return get_interaction(self.condition_name)
        return None

    @property
    def action(self) -> Callable[['NPC', 'PlayerState', 'Economy'], Dict[str, Any]]:
        return get_interaction(self.action_name)


class NPC(BaseModel):
    """Represents a non-player character in the game."""
    id: str
    definition_id: str # To link back to static definitions from npcs.json
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
    # Consider if is_present should be serialized or always recalculated.
    # If serialized, it represents the state at time of save. Recalculation might be needed post-load.

    class Config:
        arbitrary_types_allowed = True # For runtime properties like condition/action on NPCInteraction

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
        # Default greeting and topics
        greeting = f"{self.name} nods in your direction."
        current_topics = list(self.conversation_topics) # Make a copy to potentially modify

        if self.id == "barkeep": # Specific handling for Old Tom
            player_rep_score = get_reputation(player, self.id)
            rep_tier = get_reputation_tier(player_rep_score)

            if rep_tier == "Friendly":
                greeting = f"{self.name} gives you a slight smile. 'Good to see ya. What can I get for you, or got somethin' on your mind?'"
                if "local_gossip" not in current_topics:
                    current_topics.append("local_gossip")
            elif rep_tier == "Liked" or rep_tier == "Trusted" or rep_tier == "Hero":
                greeting = f"{self.name} grins. 'Well, look who it is! The usual, or are we talkin' business today?'"
                if "local_gossip" not in current_topics:
                    current_topics.append("local_gossip")
                if "barkeep_special" not in current_topics: # A special topic for high rep
                    current_topics.append("barkeep_special")
            elif rep_tier == "Unfriendly":
                greeting = f"{self.name} barely looks at you. 'What do you want?'"
                if "local_gossip" in current_topics:
                    current_topics.remove("local_gossip") # Might not want to share gossip
            elif rep_tier == "Disliked" or rep_tier == "Hated" or rep_tier == "Despised":
                greeting = f"{self.name} scowls. 'Make it quick. I'm busy.'"
                current_topics = [t for t in current_topics if t not in ["local_gossip", "rumors"]] # Very restricted topics
            else: # Neutral
                greeting = f"{self.name} nods. 'What'll it be?'"


        if not topic:
            return {
                "success": True,
                "message": greeting,
                "topics": current_topics
            }
            
        if topic in current_topics:
            # Simple response based on topic
            responses = {
                "tavern": "The Rusted Tankard has seen better days, but it's home.",
                "drinks": "I'll have whatever's on tap. Best ale in town, not that there's much competition.",
                "rumors": "I've heard whispers... but talk is cheap. And sometimes dangerous.",
                "local_gossip": "This town's full of stories. Some even true. Old Man Fitzwilliam thinks he saw a ghost by the well again.",
                "barkeep_special": "Alright, since it's you... I might know a thing or two that ain't common knowledge. What are you interested in?"
            }
            # Specific response if Old Tom and high rep
            if self.id == "barkeep" and topic == "barkeep_special":
                if get_reputation_tier(get_reputation(player, self.id)) in ["Liked", "Trusted", "Hero"]:
                     return {"success": True, "message": responses[topic], "topics": current_topics}
                else: # Shouldn't be offered if rep too low, but as a fallback
                    return {"success": True, "message": "I don't think I have anything special for you right now.", "topics": current_topics}

            return {
                "success": True,
                "message": responses.get(topic, "I don't have much to say about that."),
                "topics": current_topics
            }
            
        return {
            "success": False,
            "message": "I'm not sure what you're talking about, or I'm not inclined to discuss that with you right now.",
            "topics": current_topics
        }


class NPCManager(BaseModel):
    """Manages all NPCs in the game."""
    
    npcs: Dict[str, NPC] = Field(default_factory=dict)
    
    # Runtime attributes, not part of serialized state, but needed for initialization and operation
    _data_dir: Path = PrivateAttr()
    _event_bus: Optional[Any] = PrivateAttr(default=None) # Define type more accurately if possible, e.g. EventBus
    _npc_definitions: Dict[str, Any] = PrivateAttr(default_factory=dict) # Loaded from JSON
    _present_npc_ids: Set[str] = PrivateAttr(default_factory=set) # For optimization

    def __init__(self, data_dir: str = "data", event_bus: Optional[Any] = None, **data: Any):
        """Initialize the NPC manager.
        
        Args:
            data_dir: Directory containing NPC data files.
            event_bus: Optional event bus to dispatch events to.
            **data: Pydantic model data, typically 'npcs' dictionary if loading from serialized state.
        """
        # Initialize PrivateAttrs before super().__init__ if they are used by validators/etc.
        # However, Pydantic generally expects private attrs to be set after super call if not defaults.
        self._data_dir = Path(data_dir)
        self._event_bus = event_bus
        
        super().__init__(**data) # This will populate self.npcs if 'npcs' is in data

        # Load definitions regardless of whether we are loading saved NPCs or initializing fresh
        self._load_npc_definitions()

        if not self.npcs: # If not loading a saved state (i.e., npcs dict is empty)
            self._initialize_npcs_from_definitions()
        else:
            # If loading saved state, NPCs are already created by Pydantic.
            # We might need to re-link transient data or call update methods.
            # For example, re-linking to their definitions if that's not fully handled by NPC.model_validate
            for npc_id, npc_instance in self.npcs.items():
                if npc_instance.definition_id in self._npc_definitions:
                    # Potentially re-apply static data if needed, or ensure NPC's model_validate did this.
                    # For now, assume NPC's deserialization is sufficient.
                    pass
                if npc_instance.is_present: # Populate _present_npc_ids from loaded state
                    self._present_npc_ids.add(npc_instance.id)
                
                if npc_instance.is_present and self._event_bus: # Existing event dispatch
                    from .events.npc_events import NPCSpawnEvent
                    if hasattr(self._event_bus, 'dispatch'):
                        self._event_bus.dispatch(NPCSpawnEvent(npc_instance))


    def _load_npc_definitions(self) -> None:
        """Load NPC definitions from the JSON file."""
        npc_file = self._data_dir / "npcs.json"
        if not npc_file.exists():
            print(f"Warning: NPC definition file not found at {npc_file}. No NPC definitions loaded.")
            return
        try:
            import json
            with open(npc_file, 'r') as f:
                definitions_data = json.load(f)
            for npc_def_data in definitions_data.get("npc_definitions", []):
                def_id = npc_def_data.get("id")
                if def_id:
                    self._npc_definitions[def_id] = npc_def_data
                else:
                    print("Warning: Found an NPC definition without an ID. It will be ignored.")
        except Exception as e:
            print(f"Error loading NPC definitions from {npc_file}: {e}")

    def _initialize_npcs_from_definitions(self) -> None:
        """Initialize NPCs from loaded definitions. Called when not loading from a saved state."""
        if not self._npc_definitions:
            print("No NPC definitions loaded. Creating default NPCs as fallback.")
            self._create_default_npcs() # Fallback to hardcoded defaults
            return

        for def_id, npc_def_data in self._npc_definitions.items():
            try:
                # Create a mutable copy for processing
                processed_data = npc_def_data.copy()
                processed_data["definition_id"] = def_id # Ensure definition_id is set from the key

                # Convert string enums to their enum values
                processed_data["npc_type"] = NPCType[processed_data["npc_type"]]
                processed_data["disposition"] = NPCDisposition[processed_data.get("disposition", "NEUTRAL")]
                
                if "schedule" in processed_data:
                    processed_data["schedule"] = [tuple(period) for period in processed_data["schedule"]]
                
                # Process inventory: convert item IDs/data to Item instances
                # This assumes Item is Pydantic and TAVERN_ITEMS maps ids to Item models or dicts
                full_inventory = []
                if "inventory" in processed_data:
                    for item_ref in processed_data["inventory"]:
                        item_id = item_ref.get("id") if isinstance(item_ref, dict) else str(item_ref)
                        if item_id in TAVERN_ITEMS:
                             # Assuming TAVERN_ITEMS contains Item instances or valid dicts for Item model
                            item_obj = TAVERN_ITEMS[item_id]
                            if isinstance(item_obj, dict): # If it's a dict, validate into Item model
                                full_inventory.append(Item(**item_obj))
                            elif isinstance(item_obj, Item): # If it's already an Item instance
                                full_inventory.append(item_obj)
                        else:
                            print(f"Warning: Unknown item ID '{item_id}' in definition for NPC '{def_id}'.")
                processed_data["inventory"] = full_inventory

                # Process interactions: convert dicts to NPCInteraction models
                # This assumes NPCInteraction's from_dict/model_validate handles callback_names
                interactions_map = {}
                if "interactions" in processed_data:
                    for key, interact_data in processed_data["interactions"].items():
                        interactions_map[key] = NPCInteraction(**interact_data)
                processed_data["interactions"] = interactions_map
                
                npc = NPC(**processed_data)
                self.add_npc(npc) # Adds to self.npcs
                
                if npc.is_present: # Populate _present_npc_ids for newly defined NPCs
                    self._present_npc_ids.add(npc.id)

                if npc.is_present and self._event_bus: # Existing event dispatch
                    from .events.npc_events import NPCSpawnEvent
                    if hasattr(self._event_bus, 'dispatch'):
                         self._event_bus.dispatch(NPCSpawnEvent(npc))
            except (KeyError, ValueError) as e:
                print(f"Error creating NPC from definition '{def_id}': {e}")
            except Exception as e: # Catch broader errors during NPC creation
                print(f"Unexpected error creating NPC from definition '{def_id}': {e}")


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
        merchant_data = {
            "id":"merchant", "definition_id": "merchant_def", # merchant_def should exist in a hypothetical json
            "name":"Garrick", "description":"A traveling merchant with exotic wares.",
            "npc_type":NPCType.MERCHANT, "disposition":NPCDisposition.FRIENDLY,
            "schedule":[(10, 18)], "visit_frequency":0.6, "gold":200,
            "conversation_topics":["merchandise", "travel", "rumors"],
            "inventory":[TAVERN_ITEMS["stew"], TAVERN_ITEMS["bread"]]
        }
        # This default creation would also need to handle interaction_names if they have default interactions
        self.add_npc(NPC(**merchant_data))
    
    def add_npc(self, npc: NPC) -> None:
        """Add an NPC to the manager's runtime dictionary."""
        self.npcs[npc.id] = npc # This now updates the Pydantic model's field
    
    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC by ID, if present."""
        return self.npcs.get(npc_id)
    
    def update_all_npcs(self, game_time: float) -> None:
        """Update presence for all NPCs based on current game time."""
        for npc_id, npc in self.npcs.items():
            presence_changed = npc.update_presence(game_time, self._event_bus) # Use the private attribute
            if npc.is_present:
                self._present_npc_ids.add(npc_id)
            else:
                self._present_npc_ids.discard(npc_id)
    
    def get_present_npcs(self) -> List[NPC]:
        """Get a list of all currently present NPCs using the optimized set."""
        return [self.npcs[npc_id] for npc_id in self._present_npc_ids if npc_id in self.npcs]
    
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
        interactive_npcs_data = []
        for npc_instance in self.get_present_npcs(): # Use renamed variable
            # Basic interaction is always available
            npc_interactions_data = [{ # Use renamed variable
                'id': 'talk', # Default talk interaction ID
                'name': 'Talk',
                'description': f'Strike up a conversation with {npc_instance.name}'
            }]
            
            # Add any additional interactions
            if npc_instance.interactions: # Check if the NPC has specific interactions defined
                for interaction_id, interaction_obj in npc_instance.interactions.items():
                    # Use the helper property to get the condition callable
                    condition_callable = interaction_obj.condition 
                    if condition_callable is None or (player and condition_callable(npc_instance, player)):
                        npc_interactions_data.append({
                            'id': interaction_obj.id,
                            'name': interaction_obj.name,
                            'description': interaction_obj.description
                        })
            
            relationship_score = None # Use renamed variable
            if player:
                relationship_score = npc_instance.relationships.get(player.id, 0) # Make sure player has an id attribute
            
            interactive_npcs_data.append({
                'id': npc_instance.id,
                'name': npc_instance.name,
                'description': npc_instance.description,
                'relationship': relationship_score,
                'interactions': npc_interactions_data
            })
                
        return interactive_npcs_data
