from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from .items import Item, TAVERN_ITEMS, Inventory

class PlayerState(BaseModel):
    """Represents the player's current state in the game."""
    player_id: str = "default_player"
    name: str = "Player"
    gold: int = 40
    has_room: bool = False
    room_number: Optional[int] = None
    tiredness: float = 0.0
    energy: float = 1.0  # 0.0 to 1.0, affects what jobs can be done
    rest_immune: bool = False
    _no_sleep_quest_unlocked: bool = False
    _no_sleep_quest_locked: bool = False
    inventory: Inventory = Field(default_factory=Inventory)
    flags: Dict[str, Any] = Field(default_factory=dict)  # For tracking quest states and other flags
    last_ate: float = 0.0  # Game time when player last ate
    last_drank: float = 0.0  # Game time when player last drank
    
    @property
    def id(self) -> str:
        """Alias for player_id for backward compatibility."""
        return self.player_id
        
    @property
    def no_sleep_quest_unlocked(self) -> bool:
        """Get whether the no-sleep quest is unlocked.
        
        Returns:
            bool: True if the quest is unlocked and not locked, False otherwise
        """
        return self._no_sleep_quest_unlocked and not self._no_sleep_quest_locked
        
    @no_sleep_quest_unlocked.setter
    def no_sleep_quest_unlocked(self, value: bool) -> None:
        """Set whether the no-sleep quest is unlocked.
        
        Args:
            value: Whether the quest should be unlocked
            
        Note:
            Has no effect if the quest has been locked
        """
        if not self._no_sleep_quest_locked:
            self._no_sleep_quest_unlocked = bool(value)
            
    def lock_no_sleep_quest(self) -> None:
        """Lock the no-sleep quest, preventing further changes to its state."""
        self._no_sleep_quest_locked = True
        self._no_sleep_quest_unlocked = False
    
    class Config:
        arbitrary_types_allowed = True
    
    def can_afford(self, amount: int) -> bool:
        """Check if player has enough gold.
        
        Args:
            amount: Amount of gold to check
            
        Returns:
            bool: True if player can afford the amount, False otherwise
            
        Note:
            Returns False for zero or negative amounts as they are not valid transactions
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            return False
        return self.gold >= amount
    
    def add_gold(self, amount: int) -> tuple[bool, str]:
        """Add gold to player's inventory.
        
        Args:
            amount: Amount of gold to add (must be positive)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            return False, "Amount must be a positive number"
            
        try:
            self.gold += amount
            return True, f"Added {amount} gold. New total: {self.gold}"
        except Exception as e:
            return False, f"Failed to add gold: {str(e)}"
            
    def spend_gold(self, amount: int) -> tuple[bool, str]:
        """Spend gold from player's inventory.
        
        Args:
            amount: Amount of gold to spend (must be positive)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            return False, "Amount must be a positive number"
            
        if self.gold < amount:
            return False, f"Not enough gold. Needed: {amount}, Have: {self.gold}"
            
        remaining = self.gold - amount
        self.gold = remaining
        return True, f"Spent {amount} gold. Remaining: {remaining}"
        
    def update_tiredness(self, amount: float, clock) -> None:
        """Update the player's tiredness level.
        
        Args:
            amount: Amount to add to tiredness (can be negative)
            clock: The game clock to track time
        """
        self.tiredness = max(0, min(1.0, self.tiredness + amount))
        self.energy = 1.0 - self.tiredness
        
    def sleep(self, hours: float = 8.0) -> str:
        """Player sleeps to reduce tiredness.
        
        Args:
            hours: Number of hours to sleep
            
        Returns:
            str: Message describing the sleep action
        """
        if not self.has_room:
            return "You need to rent a room to sleep!"
            
        # Reduce tiredness based on sleep duration
        recovery = min(0.1 * hours, 1.0 - self.tiredness)
        self.tiredness = max(0, self.tiredness - recovery)
        self.energy = 1.0 - self.tiredness
        
        return f"You sleep for {hours} hours and feel more rested."
        
    def check_no_sleep_quest(self) -> bool:
        """Check if the no-sleep quest is unlocked.
        
        Returns:
            bool: True if the no-sleep quest is unlocked, False otherwise
        """
        return self.no_sleep_quest_unlocked
        
    def ask_about_sleep(self) -> str:
        """Handle player asking about sleep.
        
        Returns:
            str: Response to the player's question about sleep
        """
        if self.no_sleep_quest_unlocked:
            return "You've already unlocked the no-sleep quest!"
            
        # Check if player qualifies for the no-sleep quest
        if self.tiredness >= 0.8:  # Very tired
            self.no_sleep_quest_unlocked = True
            return ("You feel an unusual energy despite your exhaustion. "
                   "You've unlocked the No-Sleep Challenge quest!")
        else:
            return "You're feeling a bit tired, but nothing unusual."
        
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
