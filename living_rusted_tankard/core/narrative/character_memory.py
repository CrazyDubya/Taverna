"""
Character Memory System - The foundation of making NPCs feel like real people.
Each character remembers their interactions with the player and builds relationships over time.
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RelationshipLevel(Enum):
    """Defines the depth of relationship between NPC and player."""

    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIENDLY = "friendly"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    TRUSTED = "trusted"
    HOSTILE = "hostile"

    @property
    def trust_threshold(self) -> float:
        """Trust level needed to reach this relationship."""
        thresholds = {
            self.STRANGER: 0.0,
            self.ACQUAINTANCE: 0.1,
            self.FRIENDLY: 0.3,
            self.FRIEND: 0.5,
            self.CLOSE_FRIEND: 0.7,
            self.TRUSTED: 0.9,
            self.HOSTILE: -0.3,
        }
        return thresholds.get(self, 0.0)


@dataclass
class Memory:
    """A single memory of an interaction with the player."""

    timestamp: float
    interaction_type: str  # 'conversation', 'help', 'transaction', 'conflict'
    player_action: str
    npc_response: str
    emotional_impact: float  # -1.0 to 1.0
    context: Dict[str, any] = field(default_factory=dict)
    referenced_count: int = 0  # How often this memory has been referenced

    def age_in_hours(self, current_time: float) -> float:
        """How old is this memory in game hours."""
        return (current_time - self.timestamp) / 3600.0

    def to_narrative(self) -> str:
        """Convert memory to narrative text for dialogue."""
        time_desc = self._get_time_description()
        if self.interaction_type == "help":
            return f"when you helped me {self.player_action} {time_desc}"
        elif self.interaction_type == "conversation":
            return f"our conversation about {self.context.get('topic', 'various things')} {time_desc}"
        elif self.interaction_type == "transaction":
            return f"when you {self.player_action} {time_desc}"
        else:
            return f"when {self.player_action} {time_desc}"

    def _get_time_description(self) -> str:
        """Generate natural time description."""
        age_hours = self.age_in_hours(time.time())
        if age_hours < 1:
            return "just now"
        elif age_hours < 24:
            return "earlier today"
        elif age_hours < 48:
            return "yesterday"
        elif age_hours < 168:
            return "a few days ago"
        else:
            return "some time ago"


class CharacterMemory:
    """Manages all memories and relationships for a single NPC."""

    def __init__(self, npc_id: str, npc_name: str):
        self.npc_id = npc_id
        self.npc_name = npc_name
        self.memories: List[Memory] = []
        self.relationship_score: float = 0.0  # -1.0 to 1.0
        self.trust_level: float = 0.0  # 0.0 to 1.0
        self.last_interaction: Optional[float] = None
        self.interaction_count: int = 0
        self.mood_modifiers: Dict[str, float] = {}
        self.personal_facts: Dict[str, any] = {}  # Things NPC has learned about player

    @property
    def relationship_level(self) -> RelationshipLevel:
        """Current relationship level based on score."""
        if self.relationship_score < -0.3:
            return RelationshipLevel.HOSTILE
        elif self.trust_level >= 0.9:
            return RelationshipLevel.TRUSTED
        elif self.trust_level >= 0.7:
            return RelationshipLevel.CLOSE_FRIEND
        elif self.trust_level >= 0.5:
            return RelationshipLevel.FRIEND
        elif self.trust_level >= 0.3:
            return RelationshipLevel.FRIENDLY
        elif self.trust_level >= 0.1:
            return RelationshipLevel.ACQUAINTANCE
        else:
            return RelationshipLevel.STRANGER

    def add_memory(
        self,
        interaction_type: str,
        player_action: str,
        npc_response: str,
        emotional_impact: float,
        context: Optional[Dict] = None,
    ) -> None:
        """Add a new memory of interaction with the player."""
        memory = Memory(
            timestamp=time.time(),
            interaction_type=interaction_type,
            player_action=player_action,
            npc_response=npc_response,
            emotional_impact=emotional_impact,
            context=context or {},
        )

        self.memories.append(memory)
        self.interaction_count += 1
        self.last_interaction = memory.timestamp

        # Update relationship based on emotional impact
        self._update_relationship(emotional_impact)

        # Update trust based on positive interactions
        if emotional_impact > 0.2:
            self._update_trust(0.05)  # Small trust gain for positive interactions
        elif emotional_impact < -0.5:
            self._update_trust(-0.1)  # Larger trust loss for very negative interactions

        logger.info(f"{self.npc_name} formed memory: {memory.to_narrative()}")

    def _update_relationship(self, impact: float) -> None:
        """Update relationship score based on interaction impact."""
        # Recent interactions have more weight
        weight = 1.0
        self.relationship_score = max(-1.0, min(1.0, self.relationship_score * 0.9 + impact * weight * 0.1))

    def _update_trust(self, delta: float) -> None:
        """Update trust level, which changes slowly over time."""
        self.trust_level = max(0.0, min(1.0, self.trust_level + delta))

    def improve_relationship(self, amount: float = 0.1) -> None:
        """Improve relationship score."""
        self.relationship_score = min(1.0, self.relationship_score + amount)

    def damage_relationship(self, amount: float = 0.1) -> None:
        """Damage relationship score."""
        self.relationship_score = max(-1.0, self.relationship_score - amount)

    def get_relationship_level(self) -> RelationshipLevel:
        """Get current relationship level based on score."""
        return self.relationship_level

    def add_interaction_memory(self, description: str, details: Dict[str, any]) -> None:
        """Add a memory of interaction with player."""
        self.add_memory(
            interaction_type=details.get("type", "conversation"),
            player_action=description,
            npc_response="",  # Will be filled by dialogue system
            emotional_impact=details.get("emotional_impact", 0.1),
            context=details,
        )

    def add_personal_fact(self, category: str, fact: str) -> None:
        """Add a personal fact learned about the player."""
        if category not in self.personal_facts:
            self.personal_facts[category] = []
        if fact not in self.personal_facts[category]:
            self.personal_facts[category].append(fact)

    def get_relevant_memories(self, topic: str, limit: int = 3) -> List[Memory]:
        """Get memories relevant to a topic."""
        return self.recall_relevant_memories(topic, limit)

    def get_greeting(self) -> str:
        """Generate contextually appropriate greeting based on relationship."""
        level = self.relationship_level
        time_since_last = self._time_since_last_interaction()

        if level == RelationshipLevel.STRANGER:
            return f"{self.npc_name} looks at you with polite curiosity."

        elif level == RelationshipLevel.ACQUAINTANCE:
            if time_since_last and time_since_last < 24:
                return f'{self.npc_name} nods in recognition. "Back again, I see."'
            else:
                return f"{self.npc_name} gives you a slight nod of recognition."

        elif level == RelationshipLevel.FRIENDLY:
            recent_memory = self._get_most_relevant_memory()
            if recent_memory and recent_memory.emotional_impact > 0:
                return f'{self.npc_name} smiles warmly. "Good to see you again! I remember {recent_memory.to_narrative()}."'
            else:
                return f'{self.npc_name} greets you with a friendly smile. "Welcome back!"'

        elif level == RelationshipLevel.FRIEND:
            if time_since_last and time_since_last > 72:
                return f"{self.npc_name}'s face lights up. \"My friend! It's been too long. How have you been?\""
            else:
                return f'{self.npc_name} greets you warmly. "Always good to see you, friend."'

        elif level == RelationshipLevel.CLOSE_FRIEND:
            personal_touch = self._get_personal_greeting()
            return f'{self.npc_name} beams at you. "There you are! {personal_touch}"'

        elif level == RelationshipLevel.TRUSTED:
            return f'{self.npc_name} greets you with deep warmth and trust. "My dear friend, welcome."'

        else:  # HOSTILE
            return f"{self.npc_name} eyes you warily, clearly not pleased to see you."

    def get_contextual_greeting(self) -> str:
        """Alias for get_greeting() for compatibility."""
        return self.get_greeting()

    def _time_since_last_interaction(self) -> Optional[float]:
        """Hours since last interaction."""
        if self.last_interaction:
            return (time.time() - self.last_interaction) / 3600.0
        return None

    def _get_most_relevant_memory(self, context: Optional[str] = None) -> Optional[Memory]:
        """Get most relevant recent memory, optionally filtered by context."""
        if not self.memories:
            return None

        # Get recent positive memories
        recent_memories = [m for m in self.memories[-10:] if m.emotional_impact > 0]

        if context and recent_memories:
            # Try to find memory matching context
            for memory in reversed(recent_memories):
                if context.lower() in memory.player_action.lower():
                    return memory

        # Return most recent positive memory
        return recent_memories[-1] if recent_memories else None

    def _get_personal_greeting(self) -> str:
        """Generate personalized greeting for close friends."""
        if self.personal_facts.get("helped_with_business"):
            return "Business has been so much better since your help!"
        elif self.personal_facts.get("shared_secrets"):
            return "I knew I could trust you to keep our conversation private."
        elif self.interaction_count > 20:
            return "Feels like you're becoming a regular here!"
        else:
            return "I was just thinking about you!"

    def recall_relevant_memories(self, current_topic: str, limit: int = 3) -> List[Memory]:
        """Recall memories relevant to current conversation topic."""
        relevant_memories = []

        for memory in reversed(self.memories):  # Most recent first
            relevance_score = self._calculate_relevance(memory, current_topic)
            if relevance_score > 0.3:
                relevant_memories.append((relevance_score, memory))
                memory.referenced_count += 1

        # Sort by relevance and return top memories
        relevant_memories.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in relevant_memories[:limit]]

    def _calculate_relevance(self, memory: Memory, topic: str) -> float:
        """Calculate how relevant a memory is to current topic."""
        relevance = 0.0
        topic_lower = topic.lower()

        # Direct topic match
        if topic_lower in memory.player_action.lower():
            relevance += 0.5
        if topic_lower in memory.context.get("topic", "").lower():
            relevance += 0.5

        # Similar interaction type
        if memory.interaction_type == self._guess_interaction_type(topic):
            relevance += 0.3

        # Recency bonus (memories fade)
        age_penalty = min(memory.age_in_hours(time.time()) / 168.0, 1.0)  # Max penalty after a week
        relevance *= 1.0 - age_penalty * 0.5

        # Emotional significance bonus
        relevance += abs(memory.emotional_impact) * 0.2

        return min(relevance, 1.0)

    def _guess_interaction_type(self, topic: str) -> str:
        """Guess interaction type from topic keywords."""
        topic_lower = topic.lower()
        if any(word in topic_lower for word in ["help", "assist", "aid"]):
            return "help"
        elif any(word in topic_lower for word in ["buy", "sell", "trade", "gold"]):
            return "transaction"
        elif any(word in topic_lower for word in ["fight", "conflict", "angry"]):
            return "conflict"
        else:
            return "conversation"

    def update_personal_fact(self, fact_key: str, fact_value: any) -> None:
        """Update something the NPC has learned about the player."""
        self.personal_facts[fact_key] = fact_value
        logger.info(f"{self.npc_name} learned: {fact_key} = {fact_value}")

    def generate_dialogue_context(self) -> Dict[str, any]:
        """Generate context for dialogue system based on memories."""
        recent_memories = self.memories[-5:] if self.memories else []

        return {
            "relationship_level": self.relationship_level.value,
            "trust_level": self.trust_level,
            "interaction_count": self.interaction_count,
            "recent_memories": [m.to_narrative() for m in recent_memories],
            "mood_modifiers": self.mood_modifiers,
            "personal_facts": self.personal_facts,
            "time_since_last": self._time_since_last_interaction(),
        }

    def to_dict(self) -> Dict[str, any]:
        """Serialize memory for persistence."""
        return {
            "npc_id": self.npc_id,
            "npc_name": self.npc_name,
            "memories": [
                {
                    "timestamp": m.timestamp,
                    "interaction_type": m.interaction_type,
                    "player_action": m.player_action,
                    "npc_response": m.npc_response,
                    "emotional_impact": m.emotional_impact,
                    "context": m.context,
                    "referenced_count": m.referenced_count,
                }
                for m in self.memories
            ],
            "relationship_score": self.relationship_score,
            "trust_level": self.trust_level,
            "last_interaction": self.last_interaction,
            "interaction_count": self.interaction_count,
            "mood_modifiers": self.mood_modifiers,
            "personal_facts": self.personal_facts,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> "CharacterMemory":
        """Deserialize memory from persistence."""
        memory = cls(data["npc_id"], data["npc_name"])
        memory.relationship_score = data["relationship_score"]
        memory.trust_level = data["trust_level"]
        memory.last_interaction = data["last_interaction"]
        memory.interaction_count = data["interaction_count"]
        memory.mood_modifiers = data["mood_modifiers"]
        memory.personal_facts = data["personal_facts"]

        for m_data in data["memories"]:
            memory.memories.append(
                Memory(
                    timestamp=m_data["timestamp"],
                    interaction_type=m_data["interaction_type"],
                    player_action=m_data["player_action"],
                    npc_response=m_data["npc_response"],
                    emotional_impact=m_data["emotional_impact"],
                    context=m_data["context"],
                    referenced_count=m_data["referenced_count"],
                )
            )

        return memory


class CharacterMemoryManager:
    """Manages character memories for all NPCs in the game."""

    def __init__(self):
        self.character_memories: Dict[str, CharacterMemory] = {}

    def get_or_create_memory(self, npc_id: str, npc_name: str) -> CharacterMemory:
        """Get existing memory or create new one."""
        if npc_id not in self.character_memories:
            self.character_memories[npc_id] = CharacterMemory(npc_id, npc_name)
            logger.info(f"Created new character memory for {npc_name} ({npc_id})")

        return self.character_memories[npc_id]

    def get_memory(self, npc_id: str) -> Optional[CharacterMemory]:
        """Get character memory if it exists."""
        return self.character_memories.get(npc_id)

    def save_all(self, filepath: str) -> None:
        """Save all character memories to file."""
        data = {npc_id: memory.to_dict() for npc_id, memory in self.character_memories.items()}

        import json

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(data)} character memories to {filepath}")

    def load_all(self, filepath: str) -> None:
        """Load character memories from file."""
        import json
        import os

        if not os.path.exists(filepath):
            logger.warning(f"Memory file not found: {filepath}")
            return

        with open(filepath, "r") as f:
            data = json.load(f)

        self.character_memories.clear()
        for npc_id, memory_data in data.items():
            self.character_memories[npc_id] = CharacterMemory.from_dict(memory_data)

        logger.info(f"Loaded {len(self.character_memories)} character memories from {filepath}")

    def cleanup_old_memories(self, max_age_days: int = 30) -> None:
        """Remove very old memories to prevent unbounded growth."""
        current_time = time.time()
        max_age_hours = max_age_days * 24

        for memory in self.character_memories.values():
            # Keep only memories younger than max age or frequently referenced
            memory.memories = [
                m for m in memory.memories if m.age_in_hours(current_time) < max_age_hours or m.referenced_count > 5
            ]

    def get_relationship_summary(self) -> Dict[str, Dict[str, any]]:
        """Get summary of all NPC relationships."""
        return {
            npc_id: {
                "name": memory.npc_name,
                "relationship": memory.get_relationship_level().value,
                "trust": memory.trust_level,
                "interactions": memory.interaction_count,
                "last_seen": memory._time_since_last_interaction(),
            }
            for npc_id, memory in self.character_memories.items()
        }
