"""Inter-NPC relationship and conflict management system."""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import random
from datetime import datetime

from .psychology import Relationship, Secret, Personality, Mood


class RelationshipType(Enum):
    """Types of relationships between NPCs."""

    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    BEST_FRIEND = "best_friend"
    RIVAL = "rival"
    ENEMY = "enemy"
    LOVER = "lover"
    SPOUSE = "spouse"
    FAMILY = "family"
    EMPLOYER = "employer"
    EMPLOYEE = "employee"
    MENTOR = "mentor"
    STUDENT = "student"
    ALLY = "ally"
    BUSINESS_PARTNER = "business_partner"


class ConflictType(Enum):
    """Types of conflicts between NPCs."""

    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    ROMANTIC = "romantic"
    FINANCIAL = "financial"
    TERRITORIAL = "territorial"
    IDEOLOGICAL = "ideological"
    COMPETITION = "competition"
    PAST_GRIEVANCE = "past_grievance"


class AllianceType(Enum):
    """Types of alliances between NPCs."""

    FRIENDSHIP = "friendship"
    BUSINESS = "business"
    PROTECTION = "protection"
    INFORMATION = "information"
    ROMANTIC = "romantic"
    CONSPIRACY = "conspiracy"


@dataclass
class RelationshipModifier:
    """Modifies how NPCs interact based on circumstances."""

    condition: str  # e.g., "drunk", "stressed", "in_public"
    trust_modifier: float = 0.0
    affection_modifier: float = 0.0
    interaction_probability_modifier: float = 0.0
    reveal_secret_modifier: float = 0.0


@dataclass
class Conflict:
    """Represents an ongoing conflict between NPCs."""

    id: str
    type: ConflictType
    participants: Set[str]  # NPC IDs
    description: str
    intensity: float = 0.5  # 0-1, how serious
    started: datetime = field(default_factory=datetime.now)

    # Conflict details
    root_cause: str = ""
    stakes: List[str] = field(default_factory=list)

    # Resolution
    resolution_conditions: List[str] = field(default_factory=list)
    resolved: bool = False
    resolution: Optional[str] = None

    # Escalation
    escalation_triggers: List[str] = field(default_factory=list)
    current_stage: int = 1  # 1-5, higher = worse

    def escalate(self, reason: str) -> None:
        """Escalate the conflict."""
        self.current_stage = min(5, self.current_stage + 1)
        self.intensity = min(1.0, self.intensity + 0.2)

    def deescalate(self, reason: str) -> None:
        """De-escalate the conflict."""
        self.current_stage = max(1, self.current_stage - 1)
        self.intensity = max(0.1, self.intensity - 0.15)

    def check_resolution(self, world_state: Dict[str, Any]) -> bool:
        """Check if conflict can be resolved."""
        # Simplified - in reality would check resolution conditions
        if self.intensity < 0.2:
            self.resolved = True
            self.resolution = "Faded over time"
            return True
        return False


@dataclass
class Alliance:
    """Represents an alliance or positive relationship between NPCs."""

    id: str
    type: AllianceType
    members: Set[str]  # NPC IDs
    description: str
    strength: float = 0.5  # 0-1
    formed: datetime = field(default_factory=datetime.now)

    # Alliance details
    purpose: str = ""
    benefits: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)

    # Secrets shared within alliance
    shared_secrets: List[str] = field(default_factory=list)

    # Stability
    stability: float = 1.0  # 0-1, likelihood to persist
    threat_factors: List[str] = field(default_factory=list)

    def strengthen(self, amount: float = 0.1) -> None:
        """Strengthen the alliance."""
        self.strength = min(1.0, self.strength + amount)
        self.stability = min(1.0, self.stability + amount * 0.5)

    def weaken(self, amount: float = 0.1) -> None:
        """Weaken the alliance."""
        self.strength = max(0.0, self.strength - amount)
        self.stability = max(0.0, self.stability - amount * 0.5)

    def add_member(self, npc_id: str) -> bool:
        """Add a new member to alliance."""
        if npc_id not in self.members:
            self.members.add(npc_id)
            # New members slightly destabilize initially
            self.stability = max(0.3, self.stability - 0.1)
            return True
        return False

    def remove_member(self, npc_id: str) -> bool:
        """Remove a member from alliance."""
        if npc_id in self.members and len(self.members) > 2:
            self.members.remove(npc_id)
            self.weaken(0.2)
            return True
        return False


@dataclass
class SocialEvent:
    """A social event that affects relationships."""

    timestamp: datetime
    event_type: str
    participants: List[str]
    location: str
    description: str

    # Effects on relationships
    relationship_changes: Dict[Tuple[str, str], Dict[str, float]] = field(
        default_factory=dict
    )

    # Witnesses
    witnesses: List[str] = field(default_factory=list)
    public: bool = False


class RelationshipWeb:
    """Manages the complex web of NPC relationships."""

    def __init__(self):
        # Core relationship data
        self.relationships: Dict[Tuple[str, str], Relationship] = {}
        self.relationship_types: Dict[Tuple[str, str], RelationshipType] = {}

        # Conflicts and alliances
        self.conflicts: Dict[str, Conflict] = {}
        self.alliances: Dict[str, Alliance] = {}

        # Social groups
        self.social_groups: Dict[str, Set[str]] = {
            "staf": set(),
            "regulars": set(),
            "merchants": set(),
            "guards": set(),
            "troublemakers": set(),
            "nobility": set(),
        }

        # Social dynamics
        self.gossip_network: Dict[str, Set[str]] = {}  # Who shares gossip with whom
        self.influence_map: Dict[str, float] = {}  # Social influence scores

        # History
        self.social_events: List[SocialEvent] = []

        # Modifiers
        self.global_modifiers: List[RelationshipModifier] = []

    def _get_relationship_key(self, npc1: str, npc2: str) -> Tuple[str, str]:
        """Get consistent key for relationship lookup."""
        return tuple(sorted([npc1, npc2]))

    def get_relationship(self, npc1: str, npc2: str) -> Optional[Relationship]:
        """Get relationship between two NPCs."""
        key = self._get_relationship_key(npc1, npc2)
        return self.relationships.get(key)

    def set_relationship(
        self,
        npc1: str,
        npc2: str,
        relationship: Relationship,
        rel_type: RelationshipType = RelationshipType.ACQUAINTANCE,
    ) -> None:
        """Set relationship between NPCs."""
        key = self._get_relationship_key(npc1, npc2)
        self.relationships[key] = relationship
        self.relationship_types[key] = rel_type

    def create_relationship(
        self,
        npc1: str,
        npc2: str,
        rel_type: RelationshipType,
        trust: float = 0.5,
        affection: float = 0.5,
        respect: float = 0.5,
    ) -> Relationship:
        """Create a new relationship between NPCs."""
        relationship = Relationship(
            character_id=npc2 if npc1 < npc2 else npc1,
            trust=trust,
            affection=affection,
            respect=respect,
        )

        self.set_relationship(npc1, npc2, relationship, rel_type)

        # Add to gossip network if friends
        if rel_type in [RelationshipType.FRIEND, RelationshipType.BEST_FRIEND]:
            self.add_to_gossip_network(npc1, npc2)

        return relationship

    def add_to_social_group(self, npc_id: str, group: str) -> None:
        """Add NPC to a social group."""
        if group in self.social_groups:
            self.social_groups[group].add(npc_id)

    def get_social_groups(self, npc_id: str) -> List[str]:
        """Get all social groups an NPC belongs to."""
        groups = []
        for group_name, members in self.social_groups.items():
            if npc_id in members:
                groups.append(group_name)
        return groups

    def create_conflict(
        self,
        conflict_type: ConflictType,
        participants: List[str],
        description: str,
        root_cause: str,
        intensity: float = 0.5,
    ) -> Conflict:
        """Create a new conflict."""
        conflict_id = f"conflict_{len(self.conflicts)}_{conflict_type.value}"

        conflict = Conflict(
            id=conflict_id,
            type=conflict_type,
            participants=set(participants),
            description=description,
            root_cause=root_cause,
            intensity=intensity,
        )

        self.conflicts[conflict_id] = conflict

        # Affect relationships
        for i, npc1 in enumerate(participants):
            for npc2 in participants[i + 1 :]:
                rel = self.get_relationship(npc1, npc2)
                if rel:
                    # Conflicts reduce trust and affection
                    rel.modify_relationship(
                        trust_delta=-0.2 * intensity,
                        affection_delta=-0.15 * intensity,
                        fear_delta=0.1 * intensity
                        if conflict_type == ConflictType.PERSONAL
                        else 0,
                    )

        return conflict

    def create_alliance(
        self,
        alliance_type: AllianceType,
        members: List[str],
        description: str,
        purpose: str,
        strength: float = 0.5,
    ) -> Alliance:
        """Create a new alliance."""
        alliance_id = f"alliance_{len(self.alliances)}_{alliance_type.value}"

        alliance = Alliance(
            id=alliance_id,
            type=alliance_type,
            members=set(members),
            description=description,
            purpose=purpose,
            strength=strength,
        )

        self.alliances[alliance_id] = alliance

        # Strengthen relationships between members
        for i, npc1 in enumerate(members):
            for npc2 in members[i + 1 :]:
                rel = self.get_relationship(npc1, npc2)
                if not rel:
                    rel = self.create_relationship(npc1, npc2, RelationshipType.ALLY)

                # Alliances increase trust and affection
                rel.modify_relationship(
                    trust_delta=0.2 * strength,
                    affection_delta=0.1 * strength,
                    respect_delta=0.15 * strength,
                )

        return alliance

    def add_to_gossip_network(self, npc1: str, npc2: str) -> None:
        """Add gossip connection between NPCs."""
        if npc1 not in self.gossip_network:
            self.gossip_network[npc1] = set()
        if npc2 not in self.gossip_network:
            self.gossip_network[npc2] = set()

        self.gossip_network[npc1].add(npc2)
        self.gossip_network[npc2].add(npc1)

    def spread_gossip(
        self, source_npc: str, secret: Secret, reliability: float = 0.8
    ) -> Set[str]:
        """Spread gossip through the network."""
        informed = {source_npc}
        to_process = [source_npc]

        while to_process:
            current = to_process.pop(0)

            # Get gossip connections
            connections = self.gossip_network.get(current, set())

            for connection in connections:
                if connection in informed:
                    continue

                # Check if gossip spreads
                rel = self.get_relationship(current, connection)
                if rel and rel.trust > 0.4:
                    spread_chance = rel.trust * reliability

                    if random.random() < spread_chance:
                        informed.add(connection)
                        secret.suspected_by.add(connection)

                        # Continue spreading with reduced reliability
                        if reliability > 0.3:
                            to_process.append(connection)
                            reliability *= 0.8

        return informed

    def calculate_social_influence(self, npc_id: str) -> float:
        """Calculate an NPC's social influence score."""
        influence = 0.0

        # Base influence from social groups
        groups = self.get_social_groups(npc_id)
        group_influence = {
            "nobility": 0.3,
            "staf": 0.2,
            "merchants": 0.15,
            "guards": 0.2,
            "regulars": 0.1,
            "troublemakers": -0.1,
        }

        for group in groups:
            influence += group_influence.get(group, 0)

        # Influence from relationships
        relationship_count = 0
        total_disposition = 0.0

        for (npc1, npc2), rel in self.relationships.items():
            if npc1 == npc_id or npc2 == npc_id:
                relationship_count += 1
                total_disposition += rel.get_overall_disposition()

        if relationship_count > 0:
            avg_disposition = total_disposition / relationship_count
            influence += avg_disposition * 0.3

        # Influence from alliances
        for alliance in self.alliances.values():
            if npc_id in alliance.members:
                influence += alliance.strength * 0.2

        # Negative influence from conflicts
        for conflict in self.conflicts.values():
            if npc_id in conflict.participants:
                influence -= conflict.intensity * 0.1

        # Store calculated influence
        self.influence_map[npc_id] = max(0.0, min(1.0, influence))

        return self.influence_map[npc_id]

    def get_faction_members(self, npc_id: str) -> Set[str]:
        """Get all NPCs in the same factions as the given NPC."""
        faction_members = set()

        # Check alliances
        for alliance in self.alliances.values():
            if npc_id in alliance.members:
                faction_members.update(alliance.members)

        # Check social groups
        for group_name, members in self.social_groups.items():
            if npc_id in members:
                faction_members.update(members)

        faction_members.discard(npc_id)  # Remove self
        return faction_members

    def get_enemies(self, npc_id: str) -> Set[str]:
        """Get all NPCs in conflict with the given NPC."""
        enemies = set()

        for conflict in self.conflicts.values():
            if npc_id in conflict.participants and not conflict.resolved:
                enemies.update(conflict.participants)

        # Check for enemy relationships
        for (npc1, npc2), rel_type in self.relationship_types.items():
            if rel_type in [RelationshipType.ENEMY, RelationshipType.RIVAL]:
                if npc1 == npc_id:
                    enemies.add(npc2)
                elif npc2 == npc_id:
                    enemies.add(npc1)

        enemies.discard(npc_id)  # Remove self
        return enemies

    def record_social_event(
        self,
        event_type: str,
        participants: List[str],
        location: str,
        description: str,
        public: bool = False,
    ) -> SocialEvent:
        """Record a social event that affects relationships."""
        event = SocialEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            participants=participants,
            location=location,
            description=description,
            public=public,
        )

        self.social_events.append(event)

        # Process event effects
        self._process_social_event(event)

        return event

    def _process_social_event(self, event: SocialEvent) -> None:
        """Process the effects of a social event."""
        if event.event_type == "public_argument":
            # Arguments damage relationships
            for i, npc1 in enumerate(event.participants):
                for npc2 in event.participants[i + 1 :]:
                    rel = self.get_relationship(npc1, npc2)
                    if rel:
                        rel.modify_relationship(
                            trust_delta=-0.1, affection_delta=-0.15, respect_delta=-0.05
                        )
                        event.relationship_changes[(npc1, npc2)] = {
                            "trust": -0.1,
                            "affection": -0.15,
                            "respect": -0.05,
                        }

        elif event.event_type == "shared_celebration":
            # Celebrations strengthen bonds
            for i, npc1 in enumerate(event.participants):
                for npc2 in event.participants[i + 1 :]:
                    rel = self.get_relationship(npc1, npc2)
                    if rel:
                        rel.modify_relationship(
                            trust_delta=0.05, affection_delta=0.1, respect_delta=0.05
                        )
                        event.relationship_changes[(npc1, npc2)] = {
                            "trust": 0.05,
                            "affection": 0.1,
                            "respect": 0.05,
                        }

        elif event.event_type == "betrayal":
            # Betrayals severely damage trust
            if len(event.participants) >= 2:
                betrayer = event.participants[0]
                betrayed = event.participants[1]

                rel = self.get_relationship(betrayer, betrayed)
                if rel:
                    rel.modify_relationship(
                        trust_delta=-0.5,
                        affection_delta=-0.3,
                        respect_delta=-0.4,
                        fear_delta=0.2,
                    )

                    # May create conflict
                    if rel.trust < 0.3:
                        self.create_conflict(
                            ConflictType.PERSONAL,
                            [betrayer, betrayed],
                            "Conflict arising from betrayal",
                            "Betrayal of trust",
                            intensity=0.7,
                        )

    def get_relationship_summary(self, npc_id: str) -> Dict[str, Any]:
        """Get a summary of an NPC's relationships."""
        summary = {
            "allies": [],
            "friends": [],
            "enemies": [],
            "rivals": [],
            "romantic": [],
            "neutral": [],
            "conflicts": [],
            "alliances": [],
            "social_groups": self.get_social_groups(npc_id),
            "influence": self.calculate_social_influence(npc_id),
        }

        # Categorize relationships
        for (npc1, npc2), rel_type in self.relationship_types.items():
            other_npc = npc2 if npc1 == npc_id else npc1 if npc2 == npc_id else None

            if other_npc:
                rel = self.get_relationship(npc_id, other_npc)
                if not rel:
                    continue

                rel_info = {
                    "npc": other_npc,
                    "type": rel_type.value,
                    "disposition": rel.get_overall_disposition(),
                }

                if rel_type == RelationshipType.ENEMY:
                    summary["enemies"].append(rel_info)
                elif rel_type == RelationshipType.RIVAL:
                    summary["rivals"].append(rel_info)
                elif rel_type in [RelationshipType.LOVER, RelationshipType.SPOUSE]:
                    summary["romantic"].append(rel_info)
                elif rel_type in [
                    RelationshipType.FRIEND,
                    RelationshipType.BEST_FRIEND,
                ]:
                    summary["friends"].append(rel_info)
                elif rel_type == RelationshipType.ALLY:
                    summary["allies"].append(rel_info)
                else:
                    summary["neutral"].append(rel_info)

        # Add conflicts
        for conflict in self.conflicts.values():
            if npc_id in conflict.participants and not conflict.resolved:
                summary["conflicts"].append(
                    {
                        "id": conflict.id,
                        "type": conflict.type.value,
                        "intensity": conflict.intensity,
                        "participants": list(conflict.participants),
                    }
                )

        # Add alliances
        for alliance in self.alliances.values():
            if npc_id in alliance.members:
                summary["alliances"].append(
                    {
                        "id": alliance.id,
                        "type": alliance.type.value,
                        "strength": alliance.strength,
                        "members": list(alliance.members),
                    }
                )

        return summary
