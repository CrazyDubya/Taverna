"""NPC state management for The Living Rusted Tankard."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import time as time_type


@dataclass
class NPCSchedule:
    """Defines when an NPC is present in the tavern."""
    start_hour: int  # 0-23
    end_hour: int  # 0-23
    days: Set[int] = field(default_factory=lambda: set(range(7)))  # 0=Monday
    probability: float = 1.0  # Chance of appearing during scheduled time


@dataclass
class NPCState:
    """Tracks the state of NPCs in the game."""
    # NPC presence and relationships
    present_npcs: Set[str] = field(default_factory=set)
    known_npcs: Dict[str, int] = field(default_factory=dict)  # NPC ID -> relationship score
    scheduled_npcs: Dict[str, NPCSchedule] = field(default_factory=dict)
    
    # Conversation state
    active_conversations: Dict[str, str] = field(default_factory=dict)  # NPC ID -> conversation state
    
    def add_npc_schedule(self, npc_id: str, schedule: NPCSchedule) -> None:
        """Add or update an NPC's schedule.
        
        Args:
            npc_id: Unique identifier for the NPC
            schedule: The NPC's schedule
        """
        self.scheduled_npcs[npc_id] = schedule
    
    def update_npc_presence(self, current_hour: int, current_weekday: int) -> None:
        """Update which NPCs are present based on the current time.
        
        Args:
            current_hour: Current hour of the day (0-23)
            current_weekday: Current day of the week (0=Monday, 6=Sunday)
        """
        for npc_id, schedule in self.scheduled_npcs.items():
            # Check if NPC should be present at this time
            is_scheduled = (
                schedule.start_hour <= current_hour < schedule.end_hour and
                current_weekday in schedule.days
            )
            
            if is_scheduled and npc_id not in self.present_npcs:
                # NPC should be present
                self.present_npcs.add(npc_id)
                # Initialize relationship if new NPC
                if npc_id not in self.known_npcs:
                    self.known_npcs[npc_id] = 0
            elif not is_scheduled and npc_id in self.present_npcs:
                # NPC should leave
                self.present_npcs.remove(npc_id)
    
    def get_available_npcs(self) -> List[str]:
        """Get a list of NPCs currently present in the tavern.
        
        Returns:
            List of NPC IDs that are currently present
        """
        return list(self.present_npcs)
    
    def get_relationship(self, npc_id: str) -> int:
        """Get the relationship score with an NPC.
        
        Args:
            npc_id: The ID of the NPC
            
        Returns:
            Relationship score (higher is better)
        """
        return self.known_npcs.get(npc_id, 0)
    
    def modify_relationship(self, npc_id: str, delta: int) -> None:
        """Modify the relationship with an NPC.
        
        Args:
            npc_id: The ID of the NPC
            delta: Amount to change the relationship by (can be negative)
        """
        # Initialize relationship if this is the first interaction
        if npc_id not in self.known_npcs:
            self.known_npcs[npc_id] = 0
        
        # Update relationship, keeping it within -100 to 100
        self.known_npcs[npc_id] = max(-100, min(100, self.known_npcs[npc_id] + delta))
    
    def start_conversation(self, npc_id: str, state: str = "greeting") -> None:
        """Start or update a conversation with an NPC.
        
        Args:
            npc_id: The ID of the NPC
            state: The current conversation state
        """
        self.active_conversations[npc_id] = state
    
    def end_conversation(self, npc_id: str) -> None:
        """End a conversation with an NPC.
        
        Args:
            npc_id: The ID of the NPC
        """
        self.active_conversations.pop(npc_id, None)
