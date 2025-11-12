"""
Fixed NPC presence update logic that ensures NPCs spawn properly on game start
"""
from typing import Optional, Dict, Any
import random


def update_presence_fixed(self, current_time: float, event_bus = None, npc_definitions: Optional[Dict[str, Any]] = None) -> bool:
    """Fixed update_presence that handles initial spawn better."""
    was_present = self.is_present
    current_hour = current_time % 24
    current_day = int(current_time // 24)
    
    # Check if NPC is scheduled for current time
    scheduled_now = any(
        (start <= current_hour < end) if start < end else (current_hour >= start or current_hour < end)
        for start, end in self.schedule
    )
    
    if not scheduled_now:
        # Not scheduled - should not be present
        if self.is_present:
            self.is_present = False
    else:
        # NPC is scheduled for this time
        
        # First time spawn (never visited before)
        if self.last_visit_day == -1:
            # Initial spawn - use visit frequency but be more generous
            # For essential NPCs like bartenders, ensure they spawn
            if self.npc_type.name == "BARKEEP":
                self.is_present = True  # Bartenders always spawn initially
            else:
                self.is_present = random.random() < max(self.visit_frequency, 0.8)
            
            if self.is_present:
                self.last_visit_day = current_day
                self.shared_news_ids = []
                
        # New day
        elif self.last_visit_day < current_day:
            self.last_visit_day = current_day
            self.is_present = random.random() < self.visit_frequency
            if self.is_present:
                self.shared_news_ids = []
                
        # Same day, not present but scheduled - chance to appear
        elif not self.is_present and self.last_visit_day == current_day:
            # Give another chance to appear if scheduled
            spawn_chance = 0.1  # Low chance for random appearance
            if self.npc_type.name == "BARKEEP" and current_hour >= 16:
                spawn_chance = 0.5  # Higher chance for bartender during prime hours
            
            if random.random() < spawn_chance:
                self.is_present = True
                self.shared_news_ids = []
        
        # Check for random departure
        if self.is_present and random.random() < self.departure_chance:
            self.is_present = False
    
    # Handle state change events
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


# Monkey patch to test
def apply_npc_fix():
    """Apply the fixed update_presence method to NPC class."""
    from core.npc import NPC
    import types
    NPC.update_presence = types.MethodType(update_presence_fixed, None, NPC)