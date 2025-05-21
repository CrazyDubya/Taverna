"""NPC system for The Living Rusted Tankard."""
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable, Set, TYPE_CHECKING, Union
import random
import json
from pydantic import BaseModel, Field as PydanticField

if TYPE_CHECKING:
    from .player import PlayerState 
    from .economy import Economy 
    from .reputation import get_reputation, get_reputation_tier, REPUTATION_TIERS
    from .news_manager import NewsManager # For news sharing
    from .game_state import GameState # To pass to _handle_conversation for context

from .callable_registry import get_interaction 

class NPCType(Enum):
    BARKEEP = auto(); PATRON = auto(); MERCHANT = auto(); GUARD = auto()
    BARD = auto(); THIEF = auto(); ADVENTURER = auto(); NOBLE = auto()
    SERVANT = auto(); COOK = auto()

class NPCDisposition(Enum):
    FRIENDLY = auto(); NEUTRAL = auto(); UNFRIENDLY = auto(); HOSTILE = auto()

class NPCSkill(BaseModel):
    name: str
    level: float

class ReputationRequirement(BaseModel): 
    min_tier: str

class NPCInteraction(BaseModel):
    id: str
    name: str
    description: str
    condition_name: Optional[str] = None  
    action_name: str                   
    cooldown: float = 0  
    last_used: float = -1  
    reputation_requirement: Optional[ReputationRequirement] = None

    @property
    def condition(self) -> Optional[Callable[['NPC', 'PlayerState'], bool]]:
        if self.condition_name:
            return get_interaction(self.condition_name)
        return None

    @property
    def action(self) -> Callable[['NPC', 'PlayerState', 'Economy'], Dict[str, Any]]:
        return get_interaction(self.action_name)

class NPC(BaseModel):
    id: str
    definition_id: str 
    name: str
    description: str
    npc_type: NPCType
    disposition: NPCDisposition = NPCDisposition.NEUTRAL
    schedule: List[Tuple[float, float]] = PydanticField(default_factory=list)
    departure_chance: float = 0.1  
    visit_frequency: float = 0.8  
    gold: int = 0
    inventory: List[Any] = PydanticField(default_factory=list) 
    base_inventory_ids: List[str] = PydanticField(default_factory=list) 

    relationships: Dict[str, float] = PydanticField(default_factory=dict) 
    conversation_topics: List[str] = PydanticField(default_factory=list)
    shared_news_ids: List[str] = PydanticField(default_factory=list, description="Track news shared by this NPC to avoid repetition with the same player recently.")
    current_topic: Optional[str] = None
    last_visit_day: int = -1
    is_present: bool = False
    skills: Dict[str, NPCSkill] = PydanticField(default_factory=dict)
    interactions: Dict[str, NPCInteraction] = PydanticField(default_factory=dict)
    current_room: Optional[str] = PydanticField(default=None)
    current_event_modifier: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True 

    def update_presence(self, current_time: float, event_bus = None, npc_definitions: Optional[Dict[str, Any]] = None) -> bool:
        was_present = self.is_present
        current_hour = current_time % 24
        current_day = int(current_time // 24)
        scheduled_now = any(
            (start <= current_hour < end) if start < end else (current_hour >= start or current_hour < end)
            for start, end in self.schedule
        )

        if not scheduled_now:
            if self.is_present: self.is_present = False
        else:
            if self.last_visit_day < current_day:
                self.last_visit_day = current_day
                self.is_present = random.random() < self.visit_frequency
                if self.is_present: # Reset shared news for a new visit day
                    self.shared_news_ids = [] 
            elif not self.is_present and self.last_visit_day == current_day and random.random() < self.visit_frequency:
                # If it's the same day, but they weren't present (e.g. game load), give a chance to appear if scheduled
                self.is_present = True
                if self.is_present: self.shared_news_ids = []


            if self.is_present and random.random() < self.departure_chance:
                self.is_present = False
        
        state_changed = was_present != self.is_present
        if state_changed and event_bus:
            from .events.npc_events import NPCSpawnEvent, NPCDepartEvent 
            if self.is_present:
                if self.id == "travelling_merchant_elara": 
                    self._update_elara_inventory(npc_definitions)
                event_bus.dispatch(NPCSpawnEvent(npc_id=self.id, data={'location': self.current_room or 'unknown'}))
            else:
                event_bus.dispatch(NPCDepartEvent(npc_id=self.id, data={'reason': 'schedule_change'}))
        return state_changed

    def _update_elara_inventory(self, npc_definitions: Optional[Dict[str, Any]] = None):
        from .items import Item, ITEM_DEFINITIONS 
        self.inventory = [] 
        item_ids_to_choose_from = list(self.base_inventory_ids)
        if not item_ids_to_choose_from and npc_definitions and self.definition_id in npc_definitions:
            item_ids_to_choose_from = list(npc_definitions[self.definition_id].get("base_inventory_ids", []))
        if not item_ids_to_choose_from: return

        num_items = random.randint(min(3, len(item_ids_to_choose_from)), min(5, len(item_ids_to_choose_from)))
        selected_ids = random.sample(item_ids_to_choose_from, num_items)
        
        for item_id in selected_ids:
            item_def = ITEM_DEFINITIONS.get(item_id)
            if not item_def: continue
            quantity = 1
            if item_id in ["elixir_luck", "exotic_spices", "bread", "healing_potion_minor", "arrows"]:
                quantity = random.randint(1, 5)
            # Create inventory item in the proper format
            from .items import InventoryItem
            inventory_item = InventoryItem(item=item_def.model_copy(deep=True), quantity=quantity)
            self.inventory.append(inventory_item)

        if self.current_event_modifier == "war_in_north":
            if not any(item.item.id == "dagger" for item in self.inventory): # Now inventory holds InventoryItem objects
                dagger_def = ITEM_DEFINITIONS.get("dagger")
                if dagger_def: 
                    # Create inventory item in the proper format
                    from .items import InventoryItem
                    dagger_item = InventoryItem(
                        item=dagger_def.model_copy(deep=True),
                        quantity=random.randint(1,2)
                    )
                    self.inventory.append(dagger_item)

    def modify_relationship(self, player_id: str, change: float, event_bus=None) -> float:
        old_value = self.relationships.get(player_id, 0.0)
        new_value = max(-1.0, min(1.0, old_value + change)) 
        self.relationships[player_id] = new_value
        if event_bus and abs(change) > 0.01:
            from .events.npc_events import NPCRelationshipChangeEvent 
            event_bus.dispatch(NPCRelationshipChangeEvent(npc_id=self.id, player_id=player_id, change=change, new_value=new_value))
        return new_value
        
    def _handle_conversation(self, game_state: 'GameState', topic: Optional[str] = None) -> Dict[str, Any]:
        from .reputation import get_reputation, get_reputation_tier 
        
        player_state = game_state.player
        player_rep_score = get_reputation(player_state, self.id)
        rep_tier_str = get_reputation_tier(player_rep_score)

        greeting = f"{self.name} nods at you. (Rep: {rep_tier_str})"
        available_topics = list(self.conversation_topics)
        response_message = greeting

        if topic and topic in available_topics:
            # Simple response for now, can be expanded
            responses = {
                "The old days": f"{self.name} chuckles. 'Ah, the old days... seen a fair bit, I have.'",
                "Rumors in town": f"{self.name} leans in. 'This town's always buzzing with something. What have you heard?'",
                "The mysterious locked door": f"{self.name} glances towards the back. 'Best not to meddle with things best left alone, eh?'",
                "Local gossip": f"{self.name} shrugs. 'Always something being said. Can't believe half of it.'",
                "rare_goods": f"{self.name} eyes you appraisingly. 'Perhaps I have something that might interest a discerning customer like yourself.'",
                "distant_lands": f"{self.name} sighs. 'Aye, seen many a road. Each with its own dust and dangers.'",
                "trade_secrets": f"{self.name} winks. 'Now, that'd be telling, wouldn't it?'"
            }
            response_message = responses.get(topic, f"{self.name} considers {topic} for a moment.")

        # News Sharing Logic
        news_manager = game_state.news_manager
        current_day = game_state.clock.get_current_day() 
        # Assuming active_global_events is a list of strings on GameState
        active_events = getattr(game_state, 'active_global_events', []) 
        
        # Get recently shared news by this NPC (could be from player state if global)
        # For now, using NPC's own list. A more robust system might involve PlayerState.
        recently_shared_to_player = self.shared_news_ids 

        # Only share news if no specific topic was discussed or as an addition
        if random.random() < 0.3: # 30% chance to share news in a general conversation
            news_snippet = news_manager.get_random_news_snippet(
                npc_type_str=self.npc_type.name, # Pass NPCType as string
                current_day=current_day,
                active_events=active_events,
                recently_shared_ids=recently_shared_to_player
            )
            if news_snippet:
                response_message += f"\n\nBy the way, {news_snippet.text}"
                if news_snippet.id not in self.shared_news_ids:
                    self.shared_news_ids.append(news_snippet.id)
                    if len(self.shared_news_ids) > 5: # Keep list from growing too large
                        self.shared_news_ids.pop(0)

        return {"success": True, "message": response_message, "topics": available_topics}


class NPCManager:
    """Manages NPCs in the game world. Not a Pydantic model for compatibility."""
    
    def __init__(self, data_dir: Union[str, Path], event_bus: Optional[Any] = None):
        self._data_dir = Path(data_dir)
        self._event_bus = event_bus
        self._npc_definitions = {}  # Initialize as empty dict
        self.npcs = {}  # Dictionary of active NPCs
        
        # Load NPC definitions from JSON
        self._load_npc_definitions()
        
        # Initialize NPCs from definitions if none exist yet
        if not self.npcs:
            self._initialize_npcs_from_definitions()

    def _load_npc_definitions(self) -> None:
        npc_file = self._data_dir / "npcs.json"
        if not npc_file.exists(): print(f"Warning: NPC file {npc_file} not found."); return
        try:
            with open(npc_file, 'r') as f: data = json.load(f)
            for npc_def_data in data.get("npc_definitions", []):
                def_id = npc_def_data.get("id")
                if def_id: self._npc_definitions[def_id] = npc_def_data
        except Exception as e: print(f"Error loading NPC definitions: {e}")

    def _initialize_npcs_from_definitions(self) -> None:
        if not self._npc_definitions: return
        from .items import ITEM_DEFINITIONS, Item # Ensure Item is imported here

        for def_id, npc_def_data in self._npc_definitions.items():
            try:
                processed_data = npc_def_data.copy()
                processed_data["definition_id"] = def_id
                processed_data["npc_type"] = NPCType[processed_data["npc_type"].upper()]
                processed_data["disposition"] = NPCDisposition[processed_data.get("disposition", "NEUTRAL").upper()]
                processed_data["schedule"] = [tuple(p) for p in processed_data.get("schedule", [])]
                
                inventory_objects = []
                for item_data in processed_data.get("inventory", []):
                    item_def = ITEM_DEFINITIONS.get(item_data["id"])
                    if item_def:
                        # Create inventory item in the proper format
                        from .items import InventoryItem
                        inv_item = InventoryItem(
                            item=item_def.model_copy(deep=True),
                            quantity=item_data.get("quantity", 1)
                        )
                        inventory_objects.append(inv_item)
                processed_data["inventory"] = inventory_objects

                interactions_map = {}
                for key, interact_data in processed_data.get("interactions", {}).items():
                    if "reputation_requirement" in interact_data and interact_data["reputation_requirement"]:
                        interact_data["reputation_requirement"] = ReputationRequirement(**interact_data["reputation_requirement"])
                    interactions_map[key] = NPCInteraction(**interact_data)
                processed_data["interactions"] = interactions_map
                
                npc = NPC(**processed_data)
                self.npcs[npc.id] = npc
            except Exception as e: print(f"Error creating NPC '{def_id}': {e}")

    def get_npc(self, npc_id: str) -> Optional[NPC]: return self.npcs.get(npc_id)

    def update_all_npcs(self, game_time: float) -> None:
        for npc in self.npcs.values():
            npc.update_presence(game_time, self._event_bus, self._npc_definitions)

    def get_present_npcs(self) -> List[NPC]:
        return [npc for npc in self.npcs.values() if npc.is_present]

    def get_interactive_npcs(self, player_state: 'PlayerState') -> List[Dict[str, Any]]:
        from .reputation import get_reputation, get_reputation_tier, REPUTATION_TIERS 
        interactive_list = []
        for npc in self.get_present_npcs():
            npc_data = {"id": npc.id, "name": npc.name, "description": npc.description, "interactions": []}
            npc_data["interactions"].append({"id": "talk", "name": "Talk", "description": f"Talk to {npc.name}."})

            player_rep_score = get_reputation(player_state, npc.id)
            player_tier_str = get_reputation_tier(player_rep_score)
            tier_values = {tier_name: i for i, (_, tier_name) in enumerate(REPUTATION_TIERS)} 
            player_tier_value = tier_values.get(player_tier_str)

            for interact_id, interaction_obj in npc.interactions.items():
                passes_rep_check = True
                if interaction_obj.reputation_requirement:
                    req_tier_value = tier_values.get(interaction_obj.reputation_requirement.min_tier)
                    if req_tier_value is None or player_tier_value is None or player_tier_value < req_tier_value:
                        passes_rep_check = False
                
                if passes_rep_check:
                    condition_met = True
                    if interaction_obj.condition:
                         condition_met = interaction_obj.condition(npc, player_state) 
                    if condition_met:
                        npc_data["interactions"].append({"id": interaction_obj.id, "name": interaction_obj.name, "description": interaction_obj.description})
            interactive_list.append(npc_data)
        return interactive_list

    def interact_with_npc(self, npc_id: str, player_state: 'PlayerState', interaction_id: str, game_state: 'GameState', **kwargs) -> Dict[str, Any]:
        # Changed economy to game_state for broader context access
        npc = self.get_npc(npc_id)
        if not npc or not npc.is_present: return {"success": False, "message": "NPC not available."}

        if interaction_id == "talk": 
            # Pass GameState to _handle_conversation
            return npc._handle_conversation(game_state, topic=kwargs.get("topic"))

        interaction = npc.interactions.get(interaction_id)
        if not interaction: return {"success": False, "message": "Unknown interaction."}

        from .reputation import get_reputation, get_reputation_tier, REPUTATION_TIERS 
        if interaction.reputation_requirement:
            player_rep_score = get_reputation(player_state, npc.id)
            player_tier_str = get_reputation_tier(player_rep_score)
            tier_values = {tier_name: i for i, (_, tier_name) in enumerate(REPUTATION_TIERS)}
            player_tier_value = tier_values.get(player_tier_str)
            req_tier_value = tier_values.get(interaction.reputation_requirement.min_tier)
            if req_tier_value is None or player_tier_value is None or player_tier_value < req_tier_value:
                return {"success": False, "message": f"You are not trusted enough by {npc.name} for that."}
        
        if interaction.condition and not interaction.condition(npc, player_state):
            return {"success": False, "message": "Conditions not met for this interaction."}
            
        action_result = interaction.action(npc, player_state, game_state.economy, **kwargs) # Pass economy from game_state
        if self._event_bus:
            from .events.npc_events import NPCInteractionEvent 
            self._event_bus.dispatch(NPCInteractionEvent(npc_id=npc.id, player_id=player_state.id, interaction_type=interaction_id, data=action_result))
        return action_result

    def add_npc(self, npc: NPC) -> None:
        """Add an NPC to the game world."""
        self.npcs[npc.id] = npc
        
    def set_global_event_modifier(self, event_name: Optional[str]) -> None:
        for npc in self.npcs.values():
            if npc.id == "travelling_merchant_elara": 
                npc.current_event_modifier = event_name
                
    def to_dict(self) -> Dict[str, Any]:
        """Serialize NPCManager state to a dictionary."""
        return {
            "npcs": {npc_id: npc.model_dump() for npc_id, npc in self.npcs.items()}
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any], data_dir: str = "data", event_bus: Optional[Any] = None) -> 'NPCManager':
        """Create an NPCManager from serialized data."""
        manager = cls(data_dir=data_dir, event_bus=event_bus)
        
        # Load NPCs from serialized data
        if "npcs" in data and isinstance(data["npcs"], dict):
            for npc_id, npc_data in data["npcs"].items():
                manager.npcs[npc_id] = NPC.model_validate(npc_data)
                
        return manager
