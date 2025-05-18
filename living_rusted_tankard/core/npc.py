from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import random

@dataclass
class NPC:
    """Represents a non-player character in the game."""
    id: str
    name: str
    description: str
    schedule: List[Tuple[float, float]]  # List of (start_hour, end_hour) tuples
    departure_chance: float = 0.1  # Daily chance to leave (0.0 to 1.0)
    present: bool = False
    last_seen_day: int = -1  # Last day this NPC was seen
    
    def update_presence(self, game_time: float) -> None:
        """Update NPC's presence based on current game time."""
        current_day = int(game_time // 24)
        current_hour = game_time % 24
        
        # Only update once per game day
        if current_day == self.last_seen_day:
            return
            
        self.last_seen_day = current_day
        
        # Check if NPC should be present based on schedule
        should_be_present = any(
            start <= current_hour < end 
            for start, end in self.schedule
        )
        
        if should_be_present:
            # If NPC is scheduled to be present, check if they decide to leave
            if random.random() < self.departure_chance:
                self.present = False
            else:
                self.present = True
        else:
            self.present = False

@dataclass
class NPCManager:
    """Manages all NPCs in the game."""
    npcs: Dict[str, NPC] = field(default_factory=dict)
    
    def add_npc(self, npc: NPC) -> None:
        """Add an NPC to the manager."""
        self.npcs[npc.id] = npc
    
    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC by ID, if present."""
        return self.npcs.get(npc_id)
    
    def update_all_npcs(self, game_time: float) -> None:
        """Update presence for all NPCs based on current game time."""
        for npc in self.npcs.values():
            npc.update_presence(game_time)
    
    def get_present_npcs(self) -> List[NPC]:
        """Get a list of all currently present NPCs."""
        return [npc for npc in self.npcs.values() if npc.present]
    
    def find_npc_by_name(self, name: str) -> Optional[NPC]:
        """Find an NPC by name (case-insensitive)."""
        name_lower = name.lower()
        for npc in self.npcs.values():
            if npc.name.lower() == name_lower:
                return npc
        return None
