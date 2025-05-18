from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from .items import Item, TAVERN_ITEMS, Inventory

class PlayerState(BaseModel):
    """Represents the player's current state in the game."""
    gold: int = 40
    has_room: bool = False
    tiredness: float = 0.0
    energy: float = 1.0  # 0.0 to 1.0, affects what jobs can be done
    rest_immune: bool = False
    no_sleep_quest_unlocked: bool = False
    inventory: Inventory = Field(default_factory=Inventory)
    flags: Dict[str, Any] = Field(default_factory=dict)  # For tracking quest states and other flags
    last_ate: float = 0.0  # Game time when player last ate
    last_drank: float = 0.0  # Game time when player last drank
    
    class Config:
        arbitrary_types_allowed = True
    
    def can_afford(self, amount: int) -> bool:
        """Check if player has enough gold."""
        return self.gold >= amount
    
    def add_gold(self, amount: int) -> bool:
        """Add gold to player's inventory. Returns True if successful."""
        if amount < 0:
            return False
        self.gold += amount
        return True
    
    def spend_gold(self, amount: int) -> bool:
        """Attempt to spend gold. Returns True if successful."""
        if amount < 0 or not self.can_afford(amount):
            return False
        self.gold -= amount
        return True
    
    def update_tiredness(self, hours: float) -> None:
        """Update tiredness based on time passed and other factors."""
        if self.rest_immune:
            return
            
        # Base tiredness increase
        self.tiredness = min(1.0, self.tiredness + hours * 0.1)
        
        # Adjust energy based on tiredness and time since last meal/drink
        self.energy = max(0.0, 1.0 - (self.tiredness * 0.9))
        
        # Penalize for not eating/drinking
        # (These would be updated by the game loop with current time)
        # self._update_hunger_thirst(game_time)
    
    def _update_hunger_thirst(self, game_time: float) -> None:
        """Update hunger and thirst status based on time."""
        hours_since_ate = game_time - self.last_ate
        hours_since_drank = game_time - self.last_drank
        
        # Get hungry after 6 hours
        if hours_since_ate > 6:
            self.energy = max(0.0, self.energy - 0.05)
            
        # Get thirsty after 4 hours
        if hours_since_drank > 4:
            self.energy = max(0.0, self.energy - 0.1)
    
    def consume_item(self, item_id: str) -> bool:
        """Consume an item from inventory and apply its effects."""
        item = self.inventory.get_item(item_id)
        if not item:
            return False
            
        # Apply item effects
        if "tiredness" in item.effects:
            self.tiredness = max(0.0, self.tiredness + item.effects["tiredness"])
            
        if "energy" in item.effects:
            self.energy = min(1.0, self.energy + item.effects["energy"])
        
        # Update last ate/drank times based on item type
        # (This would be called with current game time from game loop)
        # if item.item_type == "food":
        #     self.last_ate = current_time
        # elif item.item_type == "drink":
        #     self.last_drank = current_time
            
        # Remove the item (if it's consumable)
        if item_id in TAVERN_ITEMS:
            self.inventory.remove_item(item_id)
            
        return True
    
    def rest(self, hours: float) -> bool:
        """Attempt to rest. Returns True if successful."""
        if not self.has_room:
            return False
            
        # Resting reduces tiredness and restores some energy
        self.tiredness = max(0, self.tiredness - (hours * 0.2))
        self.energy = min(1.0, self.energy + (hours * 0.15))
        return True
    
    def check_no_sleep_quest_condition(self, game_time: float, last_action: str) -> bool:
        """Check if the no-sleep meta quest should be unlocked."""
        if (game_time >= 48 and 
            not self.has_room and 
            last_action == "inquire_sleep" and 
            not self.no_sleep_quest_unlocked):
            self.no_sleep_quest_unlocked = True
            self.rest_immune = True
            return True
        return False
    
    def get_status_effects(self) -> List[str]:
        """Get a list of current status effects."""
        effects = []
        
        if self.tiredness > 0.8:
            effects.append("Exhausted")
        elif self.tiredness > 0.5:
            effects.append("Tired")
            
        if self.energy < 0.3:
            effects.append("Drained")
        elif self.energy < 0.6:
            effects.append("Fatigued")
            
        if self.rest_immune:
            effects.append("Sleepless")
            
        return effects if effects else ["Well-rested"]
