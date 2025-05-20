from typing import Dict, Any, Optional, List, Union, Tuple, TYPE_CHECKING
from enum import Enum
from pydantic import BaseModel, Field, PrivateAttr
import json
from pathlib import Path

if TYPE_CHECKING:
    from .player import PlayerState 
    from .reputation import get_reputation, get_reputation_tier, REPUTATION_TIERS 

class BountyStatus(str, Enum):
    AVAILABLE = "available"
    ACCEPTED = "accepted" 
    COMPLETED = "completed"
    FAILED = "failed" 

class BountyObjective(BaseModel):
    id: str # Added ID for easier reference
    description: str
    type: str # e.g., "kill_target", "collect_item", "discover_location", "report_to_npc"
    target_id: Optional[str] = None 
    required_progress: int = 1
    current_progress: int = 0 
    is_completed: bool = False 
    is_active: bool = False # New field to mark the currently active objective

class ReputationRequirement(BaseModel):
    npc_id: str
    min_tier: str 

class BountyReward(BaseModel):
    gold: Optional[int] = None
    items: Optional[List[Dict[str, Any]]] = Field(default_factory=list) 
    reputation: Optional[Dict[str, int]] = None 
    xp: Optional[int] = None 

class Bounty(BaseModel):
    id: str = Field(..., description="Unique identifier for the bounty")
    title: str = Field(..., description="Title of the bounty")
    description: str = Field(..., description="Detailed description of the bounty")
    issuer: Optional[str] = "Tavern Staff" 
    
    status: BountyStatus = BountyStatus.AVAILABLE 
    objectives: List[BountyObjective] = Field(default_factory=list)
    rewards: BountyReward = Field(default_factory=BountyReward)
    
    prerequisites: Optional[List[str]] = Field(default_factory=list)
    is_posted: bool = False 
    reputation_requirement: Optional[ReputationRequirement] = None 
    
    current_objective_index: int = 0 # New field for multi-stage bounties
    
    accepted_by_player_id: Optional[str] = None # For active bounty instances
    accepted_timestamp: Optional[float] = None  # For active bounty instances

    def get_active_objective(self) -> Optional[BountyObjective]:
        if 0 <= self.current_objective_index < len(self.objectives):
            return self.objectives[self.current_objective_index]
        return None

    def are_all_objectives_completed(self) -> bool:
        if not self.objectives: return True 
        return all(obj.is_completed for obj in self.objectives)

class BountyManager(BaseModel):
    _bounty_definitions: Dict[str, Bounty] = PrivateAttr(default_factory=dict)
    # managed_bounties_state will store instances of Bounty which now include current_objective_index
    # and the full state of objectives (current_progress, is_completed, is_active)
    managed_bounties_state: Dict[str, Bounty] = Field(default_factory=dict)
    _data_dir: Path = PrivateAttr(default=Path("data"))

    def __init__(self, data_dir: Union[str, Path] = "data", **data: Any):
        super().__init__(**data) 
        self._data_dir = Path(data_dir)
        self._load_bounties()

    def _load_bounties(self) -> None:
        bounties_file = self._data_dir / "bounties.json"
        if not bounties_file.exists():
            print(f"Warning: Bounties data file not found at {bounties_file}")
            return
        try:
            with open(bounties_file, 'r') as f:
                data = json.load(f)
            for bounty_data in data.get("bounties", []):
                loaded_objectives = []
                for i, obj_data in enumerate(bounty_data.get("objectives", [])):
                    # For definitions, is_active is based on being the first objective,
                    # unless specified otherwise (though typically only first is active initially).
                    is_active_from_json = obj_data.get("is_active", i == 0)
                    loaded_objectives.append(BountyObjective(
                        id=obj_data.get("id", f"obj_{bounty_data['id']}_{i+1}"), # Ensure objective ID
                        description=obj_data["description"],
                        type=obj_data.get("type", "generic"),
                        target_id=obj_data.get("target_id"),
                        required_progress=obj_data.get("required_progress", 1),
                        current_progress=obj_data.get("current_progress", 0), # Usually 0 for definition
                        is_completed=obj_data.get("is_completed", False),   # Usually False for definition
                        is_active=is_active_from_json
                    ))
                bounty_data["objectives"] = loaded_objectives
                
                if "reputation_requirement" in bounty_data and bounty_data["reputation_requirement"]:
                    bounty_data["reputation_requirement"] = ReputationRequirement(**bounty_data["reputation_requirement"])
                else:
                    bounty_data["reputation_requirement"] = None

                bounty = Bounty(**bounty_data)
                # Ensure the first objective is marked active if none are explicitly set
                if bounty.objectives and not any(obj.is_active for obj in bounty.objectives):
                    bounty.objectives[0].is_active = True
                
                self._bounty_definitions[bounty.id] = bounty
        except Exception as e:
            print(f"Error loading bounty definitions from {bounties_file}: {e}")

    def get_bounty(self, bounty_id: str) -> Optional[Bounty]:
        if bounty_id in self.managed_bounties_state:
            return self.managed_bounties_state[bounty_id]
        return self._bounty_definitions.get(bounty_id)

    def _check_reputation_requirement(self, player_state: 'PlayerState', requirement: Optional[ReputationRequirement]) -> bool:
        if not requirement: return True 
        from .reputation import get_reputation, get_reputation_tier, REPUTATION_TIERS 
        player_score = get_reputation(player_state, requirement.npc_id)
        player_tier_str = get_reputation_tier(player_score)
        tier_values = {tier_name: i for i, (_, tier_name) in enumerate(REPUTATION_TIERS)}
        required_tier_value = tier_values.get(requirement.min_tier.upper()) # Ensure tier name matches enum/key
        player_tier_value = tier_values.get(player_tier_str)
        if required_tier_value is None or player_tier_value is None: return False
        return player_tier_value >= required_tier_value

    def get_available_bounties_on_notice_board(self, player_state: 'PlayerState') -> List[Bounty]:
        notice_board_bounties = []
        for def_id, definition_bounty in self._bounty_definitions.items():
            managed_bounty = self.managed_bounties_state.get(def_id)
            if managed_bounty and managed_bounty.status != BountyStatus.AVAILABLE: continue 
            bounty_to_display = managed_bounty if managed_bounty else definition_bounty
            if bounty_to_display.status == BountyStatus.AVAILABLE and bounty_to_display.is_posted:
                if self._check_reputation_requirement(player_state, bounty_to_display.reputation_requirement):
                    # Make sure we return a copy of the definition if it's not already managed
                    # so that any UI display of objectives doesn't reflect another player's potential state
                    # (though for notice board, it should always be pristine)
                    notice_board_bounties.append(definition_bounty.model_copy(deep=True))
        return notice_board_bounties

    def post_bounty(self, bounty_id: str) -> bool:
        bounty_def = self._bounty_definitions.get(bounty_id)
        if bounty_def:
            bounty_def.is_posted = True
            managed_bounty = self.managed_bounties_state.get(bounty_id)
            if managed_bounty and managed_bounty.status == BountyStatus.AVAILABLE:
                managed_bounty.is_posted = True
            return True
        return False
    
    def accept_bounty(self, bounty_id: str, player_state: 'PlayerState', current_game_time: float) -> Tuple[bool, str]:
        bounty_def = self._bounty_definitions.get(bounty_id)
        if not bounty_def: return False, "Bounty not found."
        if not bounty_def.is_posted and bounty_def.status == BountyStatus.AVAILABLE : # Check if it's available but just not posted
             return False, "Bounty is not currently posted on the notice board."
        if bounty_def.status != BountyStatus.AVAILABLE:
             return False, f"This bounty is currently {bounty_def.status.value}."
        if not self._check_reputation_requirement(player_state, bounty_def.reputation_requirement):
            req = bounty_def.reputation_requirement
            return False, f"You do not meet the reputation requirement ({req.min_tier} with {req.npc_id}) for this bounty." # type: ignore
        if bounty_id in self.managed_bounties_state:
            existing_bounty_instance = self.managed_bounties_state[bounty_id]
            if existing_bounty_instance.accepted_by_player_id == player_state.id and \
               existing_bounty_instance.status == BountyStatus.ACCEPTED:
                return False, "You have already accepted this bounty."
        
        active_bounty = bounty_def.model_copy(deep=True) 
        active_bounty.status = BountyStatus.ACCEPTED
        active_bounty.accepted_by_player_id = player_state.id
        active_bounty.accepted_timestamp = current_game_time
        active_bounty.is_posted = False 
        active_bounty.current_objective_index = 0 # Start at the first objective
        
        for i, obj in enumerate(active_bounty.objectives):
            obj.current_progress = 0
            obj.is_completed = False
            obj.is_active = (i == 0) # Only the first objective is active initially
            
        self.managed_bounties_state[bounty_id] = active_bounty
        # PlayerState active_bounties should store the bounty_id or a lightweight reference.
        # The full PlayerBountyState is now effectively the Bounty instance in managed_bounties_state.
        if not hasattr(player_state, 'active_bounty_ids'): player_state.active_bounty_ids = set()
        player_state.active_bounty_ids.add(bounty_id) # type: ignore
        return True, f"Bounty '{active_bounty.title}' accepted."

    def update_bounty_progress(self, player_id: str, bounty_id: str, objective_id: str, progress_amount: int = 1) -> Tuple[bool, str]:
        active_bounty = self.managed_bounties_state.get(bounty_id)
        if not active_bounty or active_bounty.accepted_by_player_id != player_id or active_bounty.status != BountyStatus.ACCEPTED:
            return False, "Bounty not active for you or not found."

        current_obj_index = active_bounty.current_objective_index
        if not (0 <= current_obj_index < len(active_bounty.objectives)):
            return False, "Invalid bounty state: current objective index out of bounds."

        objective = active_bounty.objectives[current_obj_index]
        if objective.id != objective_id: # Ensure we're updating the correct, active objective
            return False, f"Objective {objective_id} is not the current active objective for this bounty."
        if not objective.is_active:
            return False, f"Objective {objective.description} is not active."
        if objective.is_completed:
            return False, "Objective already completed."

        objective.current_progress = min(objective.current_progress + progress_amount, objective.required_progress)
        message = f"Progress on '{objective.description}': {objective.current_progress}/{objective.required_progress}."

        if objective.current_progress >= objective.required_progress:
            objective.is_completed = True
            objective.is_active = False
            message = f"Objective '{objective.description}' completed."
            
            active_bounty.current_objective_index += 1
            if active_bounty.current_objective_index < len(active_bounty.objectives):
                next_objective = active_bounty.objectives[active_bounty.current_objective_index]
                next_objective.is_active = True
                message += f" Next objective: '{next_objective.description}'."
            else: # All objectives completed
                # Bounty status change to COMPLETED should happen in complete_bounty/turn_in_bounty
                message += " All objectives for this bounty are now complete! Ready to turn in."
        
        return True, message

    def get_active_objective_description(self, player_id: str, bounty_id: str) -> Optional[str]:
        active_bounty = self.managed_bounties_state.get(bounty_id)
        if active_bounty and active_bounty.accepted_by_player_id == player_id and active_bounty.status == BountyStatus.ACCEPTED:
            active_obj = active_bounty.get_active_objective()
            if active_obj:
                return active_obj.description
        return None

    def is_bounty_objective_complete(self, player_id: str, bounty_id: str, objective_id: str) -> bool:
        active_bounty = self.managed_bounties_state.get(bounty_id)
        if active_bounty and active_bounty.accepted_by_player_id == player_id:
            for obj in active_bounty.objectives:
                if obj.id == objective_id:
                    return obj.is_completed
        return False

    def are_all_objectives_complete(self, player_id: str, bounty_id: str) -> bool:
        active_bounty = self.managed_bounties_state.get(bounty_id)
        if active_bounty and active_bounty.accepted_by_player_id == player_id:
            return active_bounty.are_all_objectives_completed()
        return False

    def complete_bounty(self, player_id: str, bounty_id: str, game_state_interface: Any) -> Tuple[bool, str]:
        active_bounty = self.managed_bounties_state.get(bounty_id)
        if not active_bounty or active_bounty.accepted_by_player_id != player_id:
            return False, "Bounty not accepted by you or not found."
        if active_bounty.status != BountyStatus.ACCEPTED: # Should be ACCEPTED to be turn-in-able
            return False, f"Bounty cannot be completed. Current status: {active_bounty.status.value}."
        if not active_bounty.are_all_objectives_completed():
            return False, "Not all objectives for this bounty are completed."
        
        # Grant rewards (assuming game_state_interface is GameState which has player and item definitions)
        player = game_state_interface.player 
        from .items import ITEM_DEFINITIONS # Ensure item defs are available

        rewards = active_bounty.rewards; reward_messages = []
        if rewards.gold:
            player.add_gold(rewards.gold); reward_messages.append(f"{rewards.gold} gold")
        if rewards.items:
            for item_reward_dict in rewards.items:
                item_id = item_reward_dict.get("item_id")
                quantity = item_reward_dict.get("quantity", 1)
                item_def = ITEM_DEFINITIONS.get(item_id) if item_id else None
                if item_def:
                    # Player inventory add_item takes item_id and quantity
                    success, msg = player.inventory.add_item(item_id_to_add=item_id, quantity=quantity)
                    if success: reward_messages.append(f"{quantity} x {item_def.name}")
                    else: print(f"Warning: Failed to add reward item {item_id}: {msg}")
                else: print(f"Warning: Reward item ID '{item_id}' not found.")
        if rewards.reputation and hasattr(player, 'reputation'): # Assuming PlayerState has reputation dict
             from .reputation import update_reputation # Local import to avoid circularity at top level
             for entity_id, rep_change in rewards.reputation.items():
                update_reputation(player, entity_id, rep_change) # This updates player.reputation
                reward_messages.append(f"{rep_change} rep with {entity_id}")
        if rewards.xp and hasattr(player, 'add_xp'): # Assuming PlayerState has add_xp method
            player.add_xp(rewards.xp); reward_messages.append(f"{rewards.xp} XP")
            
        active_bounty.status = BountyStatus.COMPLETED
        if hasattr(player, 'active_bounty_ids') and bounty_id in player.active_bounty_ids: # type: ignore
            player.active_bounty_ids.remove(bounty_id) # type: ignore
        if hasattr(player, 'completed_bounty_ids'):
            player.completed_bounty_ids.add(bounty_id) # type: ignore
        
        reward_summary = ", ".join(reward_messages) if reward_messages else "No direct rewards."
        return True, f"Bounty '{active_bounty.title}' completed! Rewards: {reward_summary}"
