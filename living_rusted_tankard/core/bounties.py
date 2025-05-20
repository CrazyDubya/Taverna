from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field

class BountyStatus(str, Enum):
    AVAILABLE = "available"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    FAILED = "failed" # Future use

class BountyObjective(BaseModel):
    description: str
    target_id: Optional[str] = None # e.g., item ID to find, NPC ID to talk to, enemy type ID to defeat
    current_progress: int = 0
    required_progress: int = 1
    is_completed: bool = False # Will be updated by BountyManager

    def complete(self):
        self.is_completed = True
        self.current_progress = self.required_progress

class BountyReward(BaseModel):
    gold: Optional[int] = None
    items: Optional[List[str]] = None # List of item IDs
    reputation: Optional[Dict[str, int]] = None # Faction/NPC ID to reputation change
    xp: Optional[int] = None # Experience points

class Bounty(BaseModel):
    id: str = Field(..., description="Unique identifier for the bounty")
    title: str = Field(..., description="Title of the bounty")
    description: str = Field(..., description="Detailed description of the bounty")
    issuer: Optional[str] = "Tavern Staff" # NPC ID or generic issuer
    
    status: BountyStatus = BountyStatus.AVAILABLE
    objectives: List[BountyObjective] = Field(default_factory=list)
    rewards: BountyReward = Field(default_factory=BountyReward)
    
    prerequisites: Optional[List[str]] = Field(default_factory=list, description="List of bounty IDs that must be completed first")
    
    # Fields for tracking who accepted the bounty and when
    accepted_by_player_id: Optional[str] = None
    accepted_timestamp: Optional[float] = None # Game time

    # For serialization, ensure complex objects like BountyObjective and BountyReward are handled.
    # Pydantic does this automatically if they are also Pydantic models.

    def are_all_objectives_completed(self) -> bool:
        if not self.objectives: # No objectives means it's trivially completed once accepted or by other means
            return True 
        return all(obj.is_completed for obj in self.objectives)

# Example of how one might manage active and defined bounties (BountyManager will handle this)
# class BountyManager(BaseModel):
#     bounty_definitions: Dict[str, Bounty] = Field(default_factory=dict) # Loaded from JSON
#     active_bounties: Dict[str, Bounty] = Field(default_factory=dict) # Instances of bounties being pursued or completed
#     # bounty_id -> Bounty instance with current status, progress, etc.

#     def load_definitions(self, path: str):
#         pass # load from json

#     def accept_bounty(self, player_id: str, bounty_def_id: str):
#         pass

#     def complete_objective(self, player_id: str, bounty_id: str, objective_index: int):
#         pass
#     # etc.

# This file will also contain BountyManager later.
import json
from pathlib import Path
from .items import TAVERN_ITEMS # Ensure TAVERN_ITEMS is available for item rewards
from .reputation import update_reputation # Import the reputation utility

# (Bounty, BountyObjective, BountyReward, BountyStatus models remain as previously defined)

class BountyManager(BaseModel):
    # Stores the original definitions from bounties.json
    # This is loaded once and is static during a game session.
    # It's not part of the saved game state directly, but used to instantiate active bounties.
    _bounty_definitions: Dict[str, Bounty] = PrivateAttr(default_factory=dict)

    # Stores the state of bounties that are not in their initial 'available' state,
    # e.g., accepted, progress made, completed by a player.
    # Key: bounty_id, Value: Bounty instance with its current state.
    # This is the part that needs to be serialized with the game state.
    managed_bounties_state: Dict[str, Bounty] = Field(default_factory=dict)
    
    _data_dir: Path = PrivateAttr(default=Path("data")) # Default data directory

    def __init__(self, data_dir: Union[str, Path] = "data", **data: Any):
        super().__init__(**data) # Pydantic specific data for managed_bounties_state
        self._data_dir = Path(data_dir)
        self._load_bounty_definitions()

    def _load_bounty_definitions(self) -> None:
        """Load bounty definitions from the JSON file."""
        bounties_file = self._data_dir / "bounties.json"
        if not bounties_file.exists():
            # In a real game, you might raise an error or log this more critically
            print(f"Warning: Bounties data file not found at {bounties_file}")
            return
        try:
            with open(bounties_file, 'r') as f:
                data = json.load(f)
            for bounty_data in data.get("bounties", []):
                bounty = Bounty(**bounty_data)
                self._bounty_definitions[bounty.id] = bounty
        except Exception as e:
            print(f"Error loading bounty definitions from {bounties_file}: {e}")

    def list_available_bounties(self, player: Optional[Any] = None) -> List[Bounty]: # PlayerState type hint
        """Returns bounties that are 'available' or match player-specific conditions."""
        available = []
        for def_id, definition in self._bounty_definitions.items():
            # If this bounty is already in managed_bounties_state, use that version.
            managed_bounty = self.managed_bounties_state.get(def_id)
            
            bounty_to_check = managed_bounty if managed_bounty else definition
            
            if bounty_to_check.status == BountyStatus.AVAILABLE:
                # TODO: Check prerequisites against player's completed bounties if player is provided
                # if player and bounty_to_check.prerequisites:
                #     if not all(p_id in player.completed_bounty_ids for p_id in bounty_to_check.prerequisites):
                #         continue
                available.append(bounty_to_check)
        return available

    def view_bounty(self, bounty_id: str) -> Optional[Bounty]:
        """Returns details of a specific bounty (either its current state or definition)."""
        if bounty_id in self.managed_bounties_state:
            return self.managed_bounties_state[bounty_id]
        return self._bounty_definitions.get(bounty_id)

    def accept_bounty(self, player_id: str, bounty_id: str, current_game_time: float) -> Tuple[bool, str]:
        """Allows a player to accept a bounty."""
        if bounty_id not in self._bounty_definitions:
            return False, "Bounty not found."

        # Check if bounty is already managed (e.g. accepted by this or another player, or completed)
        if bounty_id in self.managed_bounties_state:
            managed_bounty = self.managed_bounties_state[bounty_id]
            if managed_bounty.status == BountyStatus.ACCEPTED and managed_bounty.accepted_by_player_id == player_id:
                return False, "You have already accepted this bounty."
            elif managed_bounty.status != BountyStatus.AVAILABLE: # e.g. completed, or accepted by someone else
                return False, f"This bounty is currently {managed_bounty.status.value}."
        
        # Use the definition as a base
        bounty_def = self._bounty_definitions[bounty_id]
        
        # TODO: Check prerequisites
        # if bounty_def.prerequisites and player: # Assuming player object is passed
        #     if not all(p_id in player.completed_bounty_ids for p_id in bounty_def.prerequisites):
        #         return False, "You do not meet the prerequisites for this bounty."

        # Create a new instance for the player to manage or update existing if it was available
        active_bounty = bounty_def.model_copy(deep=True) # Create a copy to modify state
        active_bounty.status = BountyStatus.ACCEPTED
        active_bounty.accepted_by_player_id = player_id
        active_bounty.accepted_timestamp = current_game_time
        
        # Reset objectives progress for this instance
        for obj in active_bounty.objectives:
            obj.current_progress = 0
            obj.is_completed = False
            
        self.managed_bounties_state[bounty_id] = active_bounty
        # The calling code (e.g. GameState or command handler) should update PlayerState.active_bounty_ids
        return True, f"Bounty '{active_bounty.title}' accepted."

    def update_objective_progress(self, player_id: str, bounty_id: str, objective_index: int, progress_made: int = 1) -> Tuple[bool, str]:
        """Update progress for a specific objective of an active bounty."""
        active_bounty = self.managed_bounties_state.get(bounty_id)
        if not active_bounty or active_bounty.accepted_by_player_id != player_id or active_bounty.status != BountyStatus.ACCEPTED:
            return False, "Bounty not active for you or not found."

        if not (0 <= objective_index < len(active_bounty.objectives)):
            return False, "Invalid objective."

        objective = active_bounty.objectives[objective_index]
        if objective.is_completed:
            return False, "Objective already completed."

        objective.current_progress += progress_made
        objective.current_progress = min(objective.current_progress, objective.required_progress)

        if objective.current_progress >= objective.required_progress:
            objective.is_completed = True
            # Check if all objectives are now complete
            if active_bounty.are_all_objectives_completed():
                return True, f"Objective '{objective.description}' completed. All objectives for '{active_bounty.title}' are now complete!"
            return True, f"Objective '{objective.description}' completed."
        
        return True, f"Progress made on objective: '{objective.description}' ({objective.current_progress}/{objective.required_progress})."


    def complete_bounty(self, player_id: str, bounty_id: str, game_state: Any) -> Tuple[bool, str]: # GameState for rewards
        """Allows a player to complete a bounty if all objectives are met."""
        active_bounty = self.managed_bounties_state.get(bounty_id)
        if not active_bounty or active_bounty.accepted_by_player_id != player_id:
            return False, "Bounty not accepted by you or not found."
        
        if active_bounty.status != BountyStatus.ACCEPTED:
            return False, f"Bounty is not active; current status: {active_bounty.status.value}."

        if not active_bounty.are_all_objectives_completed():
            return False, "Not all objectives for this bounty are completed."

        # Grant rewards
        player = game_state.player # Assuming GameState is passed and has player
        rewards = active_bounty.rewards
        reward_messages = []

        if rewards.gold:
            player.add_gold(rewards.gold)
            reward_messages.append(f"{rewards.gold} gold")
        if rewards.items:
            for item_id_reward in rewards.items:
                # This assumes TAVERN_ITEMS holds Item Pydantic models or dicts that can be converted
                item_to_add = TAVERN_ITEMS.get(item_id_reward) # Need actual Item objects
                if item_to_add:
                    player.inventory.add_item(item_to_add) # Assuming Item object
                    reward_messages.append(f"item: {item_to_add.name}")
                else:
                    print(f"Warning: Bounty reward item ID '{item_id_reward}' not found in TAVERN_ITEMS.")
        if rewards.reputation:
            for entity_id, rep_change in rewards.reputation.items():
                new_rep_score = update_reputation(player, entity_id, rep_change)
                reward_messages.append(f"{rep_change} reputation with {entity_id} (New score: {new_rep_score})")
        if rewards.xp:
            # player.add_xp(rewards.xp) # Assuming player has add_xp method
            reward_messages.append(f"{rewards.xp} XP")
            
        active_bounty.status = BountyStatus.COMPLETED
        # The calling code should update PlayerState: remove from active, add to completed
        
        reward_summary = ", ".join(reward_messages) if reward_messages else "No direct rewards."
        return True, f"Bounty '{active_bounty.title}' completed! Rewards: {reward_summary}"
