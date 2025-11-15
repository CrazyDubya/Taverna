"""Area system for multi-room tavern layout."""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from .atmosphere import AtmosphereState


class AreaType(Enum):
    """Types of areas in the tavern."""

    COMMON = "common"
    PRIVATE = "private"
    SERVICE = "service"
    STORAGE = "storage"
    SECRET = "secret"
    OUTDOOR = "outdoor"


class AccessLevel(Enum):
    """Access permissions for areas."""

    PUBLIC = 0
    PATRON = 1
    GUEST = 2
    STAFF = 3
    OWNER = 4
    SECRET = 5


@dataclass
class Feature:
    """An interactive feature within an area."""

    id: str
    name: str
    description: str
    interaction_verb: str = "examine"
    requires_item: Optional[str] = None
    hidden: bool = False
    discovered: bool = False
    one_time_use: bool = False
    used: bool = False

    def can_interact(self, has_item: bool = False) -> bool:
        """Check if feature can be interacted with."""
        if self.used and self.one_time_use:
            return False
        if self.hidden and not self.discovered:
            return False
        if self.requires_item and not has_item:
            return False
        return True

    def interact(self) -> str:
        """Perform interaction with the feature."""
        if self.one_time_use:
            self.used = True
        return f"You {self.interaction_verb} the {self.name}."


@dataclass
class Connection:
    """A connection between two areas."""

    from_area: str
    to_area: str
    direction: str  # "north", "south", "up", "down", etc.
    reverse_direction: str
    description: str = "A passage leads {direction}"
    requires_key: Optional[str] = None
    is_locked: bool = False
    is_hidden: bool = False
    discovered: bool = False
    access_level: AccessLevel = AccessLevel.PUBLIC

    def can_traverse(self, has_key: bool = False, access: AccessLevel = AccessLevel.PUBLIC) -> bool:
        """Check if connection can be traversed."""
        if self.is_hidden and not self.discovered:
            return False
        if self.is_locked and not has_key:
            return False
        if access.value < self.access_level.value:
            return False
        return True

    def get_description(self) -> str:
        """Get connection description."""
        desc = self.description.format(direction=self.direction)
        if self.is_locked:
            desc += " (locked)"
        return desc


@dataclass
class TavernArea:
    """Represents a distinct area within the tavern."""

    id: str
    name: str
    description: str
    floor: int = 0  # -1 for cellar, 0 for ground, 1+ for upper floors
    area_type: AreaType = AreaType.COMMON
    access_level: AccessLevel = AccessLevel.PUBLIC

    # Spatial properties
    size: str = "medium"  # "tiny", "small", "medium", "large", "huge"
    max_occupancy: int = 10

    # Features and objects
    features: List[Feature] = field(default_factory=list)
    items: List[str] = field(default_factory=list)

    # Current state
    npcs: Set[str] = field(default_factory=set)
    players: Set[str] = field(default_factory=set)

    # Atmosphere
    base_atmosphere: Optional[AtmosphereState] = None
    atmosphere_modifiers: Dict[str, float] = field(default_factory=dict)

    # Special properties
    allows_rest: bool = True
    allows_combat: bool = False
    is_safe_zone: bool = True
    visibility: float = 1.0  # 0.0 = pitch black, 1.0 = fully visible

    # Connections are managed by AreaManager

    @property
    def current_occupancy(self) -> int:
        """Get current number of occupants."""
        return len(self.npcs) + len(self.players)

    @property
    def is_full(self) -> bool:
        """Check if area is at capacity."""
        return self.current_occupancy >= self.max_occupancy

    @property
    def is_empty(self) -> bool:
        """Check if area has no occupants."""
        return self.current_occupancy == 0

    def add_npc(self, npc_id: str) -> bool:
        """Add an NPC to the area."""
        if self.is_full:
            return False
        self.npcs.add(npc_id)
        return True

    def remove_npc(self, npc_id: str) -> bool:
        """Remove an NPC from the area."""
        if npc_id in self.npcs:
            self.npcs.remove(npc_id)
            return True
        return False

    def add_player(self, player_id: str) -> bool:
        """Add a player to the area."""
        if self.is_full:
            return False
        self.players.add(player_id)
        return True

    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the area."""
        if player_id in self.players:
            self.players.remove(player_id)
            return True
        return False

    def get_feature(self, feature_id: str) -> Optional[Feature]:
        """Get a feature by ID."""
        for feature in self.features:
            if feature.id == feature_id:
                return feature
        return None

    def discover_feature(self, feature_id: str) -> bool:
        """Discover a hidden feature."""
        feature = self.get_feature(feature_id)
        if feature and feature.hidden and not feature.discovered:
            feature.discovered = True
            return True
        return False

    def add_item(self, item_id: str) -> None:
        """Add an item to the area."""
        self.items.append(item_id)

    def remove_item(self, item_id: str) -> bool:
        """Remove an item from the area."""
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False

    def get_description_with_contents(self) -> str:
        """Get area description including visible contents."""
        desc = [self.description]

        # Add visible features
        visible_features = [f for f in self.features if not f.hidden or f.discovered]
        if visible_features:
            feature_list = ", ".join(f.name for f in visible_features)
            desc.append(f"You notice: {feature_list}")

        # Add items
        if self.items:
            desc.append(f"On the ground: {', '.join(self.items)}")

        # Add occupants
        if self.npcs:
            desc.append(f"Present here: {', '.join(self.npcs)}")

        return "\n".join(desc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert area to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "floor": self.floor,
            "area_type": self.area_type.value,
            "access_level": self.access_level.value,
            "size": self.size,
            "max_occupancy": self.max_occupancy,
            "features": [
                {
                    "id": f.id,
                    "name": f.name,
                    "description": f.description,
                    "interaction_verb": f.interaction_verb,
                    "requires_item": f.requires_item,
                    "hidden": f.hidden,
                    "discovered": f.discovered,
                    "one_time_use": f.one_time_use,
                    "used": f.used,
                }
                for f in self.features
            ],
            "items": list(self.items),
            "npcs": list(self.npcs),
            "players": list(self.players),
            "atmosphere_modifiers": self.atmosphere_modifiers,
            "allows_rest": self.allows_rest,
            "allows_combat": self.allows_combat,
            "is_safe_zone": self.is_safe_zone,
            "visibility": self.visibility,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TavernArea":
        """Create area from dictionary."""
        area = cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            floor=data.get("floor", 0),
            area_type=AreaType(data.get("area_type", "common")),
            access_level=AccessLevel(data.get("access_level", 0)),
            size=data.get("size", "medium"),
            max_occupancy=data.get("max_occupancy", 10),
        )

        # Load features
        for f_data in data.get("features", []):
            feature = Feature(
                id=f_data["id"],
                name=f_data["name"],
                description=f_data["description"],
                interaction_verb=f_data.get("interaction_verb", "examine"),
                requires_item=f_data.get("requires_item"),
                hidden=f_data.get("hidden", False),
                discovered=f_data.get("discovered", False),
                one_time_use=f_data.get("one_time_use", False),
                used=f_data.get("used", False),
            )
            area.features.append(feature)

        # Load other properties
        area.items = data.get("items", [])
        area.npcs = set(data.get("npcs", []))
        area.players = set(data.get("players", []))
        area.atmosphere_modifiers = data.get("atmosphere_modifiers", {})
        area.allows_rest = data.get("allows_rest", True)
        area.allows_combat = data.get("allows_combat", False)
        area.is_safe_zone = data.get("is_safe_zone", True)
        area.visibility = data.get("visibility", 1.0)

        return area
