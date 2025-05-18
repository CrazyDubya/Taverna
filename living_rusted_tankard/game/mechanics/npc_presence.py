"""NPC presence and scheduling system."""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from datetime import time

@dataclass
class TimeWindow:
    """Represents a time window when an NPC is present."""
    start_hour: int
    end_hour: int
    days: Set[int] = field(default_factory=lambda: set(range(7)))  # 0=Monday to 6=Sunday
    
    def is_active(self, current_time: float, day_of_week: int) -> bool:
        """Check if this time window is currently active."""
        current_hour = int(current_time) % 24
        return (
            day_of_week in self.days
            and self.start_hour <= current_hour < self.end_hour
        )

@dataclass
class NPCPresence:
    """Tracks an NPC's presence state and schedule."""
    npc_id: str
    is_present: bool = False
    time_windows: List[TimeWindow] = field(default_factory=list)
    is_indefinite: bool = False
    departure_roll_made: bool = False
    current_room: Optional[str] = None
    
    def update_presence(self, game_clock) -> Tuple[bool, Optional[str]]:
        """
        Update NPC's presence based on current time.
        
        Returns:
            Tuple of (presence_changed, message)
        """
        current_time = game_clock.current_time
        day_of_week = (game_clock.days_elapsed + 1) % 7  # 0=Monday to 6=Sunday
        
        # Check if NPC should be present based on schedule
        should_be_present = any(
            window.is_active(current_time, day_of_week)
            for window in self.time_windows
        )
        
        # Handle indefinite guests (like the player)
        if self.is_indefinite and not self.departure_roll_made:
            # 20% chance to decide to leave each day
            if random.random() < 0.2:
                self.departure_roll_made = True
                should_be_present = False
                self.is_indefinite = False
                
        # Check for state change
        if should_be_present and not self.is_present:
            self.is_present = True
            return True, f"{self.npc_id} has arrived."
            
        if not should_be_present and self.is_present:
            self.is_present = False
            self.current_room = None
            return True, f"{self.npc_id} has left the tavern."
            
        return False, None

class PresenceManager:
    """Manages NPC presence states and schedules."""
    
    def __init__(self, game_clock):
        self.game_clock = game_clock
        self.npcs: Dict[str, NPCPresence] = {}
        self.last_update_day = -1
        self.initialized = False
    
    def add_npc(self, npc_id: str, time_windows: List[Dict], is_indefinite: bool = False) -> None:
        """Add an NPC with their schedule."""
        windows = [
            TimeWindow(
                start_hour=w['start_hour'],
                end_hour=w['end_hour'],
                days=set(w.get('days', range(7)))
            )
            for w in time_windows
        ]
        self.npcs[npc_id] = NPCPresence(
            npc_id=npc_id,
            time_windows=windows,
            is_indefinite=is_indefinite
        )
    
    def update_all(self) -> List[str]:
        """Update all NPCs' presence states."""
        messages = []
        current_day = self.game_clock.days_elapsed
        current_time = self.game_clock.current_time
        day_of_week = current_day % 7  # 0=Monday to 6=Sunday
        
        # On first run, initialize all NPCs based on their schedule
        if not self.initialized:
            for npc in self.npcs.values():
                # Check if NPC should be present based on schedule
                should_be_present = any(
                    window.is_active(current_time, day_of_week)
                    for window in npc.time_windows
                )
                npc.is_present = should_be_present
            self.initialized = True
            return []
            
        # Only update on day change
        if current_day == self.last_update_day:
            return messages
            
        self.last_update_day = current_day
        
        # Update all NPCs
        for npc in self.npcs.values():
            changed, message = npc.update_presence(self.game_clock)
            if changed and message:
                messages.append(message)
                
        return messages
    
    def get_present_npcs(self, room: Optional[str] = None) -> List[str]:
        """Get list of NPCs currently present, optionally filtered by room."""
        return [
            npc.npc_id 
            for npc in self.npcs.values() 
            if npc.is_present and (room is None or npc.current_room == room)
        ]
    
    def move_npc(self, npc_id: str, room: str) -> bool:
        """Move an NPC to a different room."""
        if npc_id not in self.npcs or not self.npcs[npc_id].is_present:
            return False
        self.npcs[npc_id].current_room = room
        return True
