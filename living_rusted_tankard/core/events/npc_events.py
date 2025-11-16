"""Events related to NPC interactions."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from ..npc import NPC


@dataclass
class NPCEvent:
    """Base class for NPC-related events."""

    npc: NPC
    event_type: str
    data: Dict[str, Any] = None

    def __post_init__(self):
        self.data = self.data or {}


@dataclass
class NPCSpawnEvent(NPCEvent):
    """Event triggered when an NPC spawns or becomes present."""

    def __init__(self, npc: NPC, location: str = None):
        super().__init__(npc, "npc_spawn", {"location": location or "tavern"})


@dataclass
class NPCDepartEvent(NPCEvent):
    """Event triggered when an NPC departs or becomes absent."""

    def __init__(self, npc: NPC, reason: str = "scheduled"):
        super().__init__(npc, "npc_depart", {"reason": reason})


@dataclass
class NPCInteractionEvent(NPCEvent):
    """Event triggered when a player interacts with an NPC."""

    def __init__(self, npc: NPC, player, interaction_type: str, **kwargs):
        data = {
            "interaction_type": interaction_type,
            "player_id": getattr(player, "id", str(player)),
        }
        data.update(kwargs)
        super().__init__(npc, "npc_interaction", data)


@dataclass
class NPCRelationshipChangeEvent(NPCEvent):
    """Event triggered when an NPC's relationship with the player changes."""

    def __init__(self, npc: NPC, player_id: str, change: float, new_value: float):
        super().__init__(
            npc,
            "npc_relationship_change",
            {"player_id": player_id, "change": change, "new_value": new_value},
        )
