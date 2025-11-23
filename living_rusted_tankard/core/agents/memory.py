"""
Memory System for Deep Agents.

Implements:
- Episodic memory (specific events and experiences)
- Semantic memory (general knowledge and facts)
- Emotional tagging of memories
- Importance-based retention
- Memory retrieval based on relevance

Integrates with existing memory.py but provides richer structure
for deep agent cognition.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import time
import hashlib


class MemoryType(Enum):
    """Types of memories."""

    EPISODIC = "episodic"  # Specific events ("I talked to Sarah yesterday")
    SEMANTIC = "semantic"  # General knowledge ("Bread costs 2 gold")
    PROCEDURAL = "procedural"  # How to do things ("How to clean tables")


@dataclass
class Memory:
    """
    A single memory with context and emotional tagging.

    Memories have:
    - Content (what happened/was learned)
    - Context (where, when, who was involved)
    - Emotional valence (how it felt)
    - Importance (how significant)
    - Accessibility (how easy to recall)
    """

    memory_id: str
    memory_type: MemoryType
    content: str

    # Context
    timestamp: float = field(default_factory=time.time)
    location: Optional[str] = None
    participants: List[str] = field(default_factory=list)  # Other agents involved

    # Emotional dimension
    emotional_valence: float = 0.0  # -1.0 (negative) to 1.0 (positive)
    emotional_intensity: float = 0.0  # 0.0-1.0, how emotionally charged

    # Significance
    importance: float = 0.5  # 0.0-1.0, how important this memory is
    access_count: int = 0  # How many times recalled
    last_accessed: float = field(default_factory=time.time)

    # Connections to other memories
    related_memories: List[str] = field(default_factory=list)  # IDs of related memories

    def access(self) -> None:
        """Access this memory (affects recall likelihood)."""
        self.access_count += 1
        self.last_accessed = time.time()

        # Accessing a memory slightly increases its importance
        self.importance = min(1.0, self.importance + 0.01)

    def get_age_hours(self) -> float:
        """Get age of memory in hours."""
        return (time.time() - self.timestamp) / 3600.0

    def get_recency_score(self) -> float:
        """
        Calculate recency score (0.0-1.0).

        Recent memories are more accessible.
        """
        hours_since_access = (time.time() - self.last_accessed) / 3600.0

        # Exponential decay with half-life of 24 hours
        half_life = 24.0
        decay_factor = 0.5 ** (hours_since_access / half_life)

        return decay_factor

    def get_accessibility(self) -> float:
        """
        Calculate how easy this memory is to recall.

        Based on:
        - Importance
        - Recency
        - Emotional intensity (emotional memories are more vivid)
        - Access count (frequently accessed memories are more accessible)
        """
        importance_weight = 0.4
        recency_weight = 0.3
        emotion_weight = 0.2
        frequency_weight = 0.1

        recency_score = self.get_recency_score()
        frequency_score = min(1.0, self.access_count / 10.0)  # Caps at 10 accesses

        accessibility = (
            self.importance * importance_weight
            + recency_score * recency_weight
            + self.emotional_intensity * emotion_weight
            + frequency_score * frequency_weight
        )

        return accessibility

    def is_emotionally_significant(self, threshold: float = 0.6) -> bool:
        """Check if this is an emotionally significant memory."""
        return self.emotional_intensity >= threshold

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "location": self.location,
            "participants": self.participants,
            "emotional_valence": self.emotional_valence,
            "emotional_intensity": self.emotional_intensity,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "related_memories": self.related_memories,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Memory":
        """Deserialize from saved data."""
        data["memory_type"] = MemoryType(data["memory_type"])
        return cls(**data)

    def __repr__(self) -> str:
        return (
            f"Memory({self.memory_type.value}, "
            f"'{self.content[:50]}...', "
            f"importance={self.importance:.2f})"
        )


@dataclass
class EpisodicMemory:
    """
    Episodic memory system for personal experiences.

    Stores memories of specific events with rich context.
    Supports retrieval by time, emotional content, participants, etc.
    """

    memories: List[Memory] = field(default_factory=list)
    max_memories: int = 1000  # Limit to prevent unbounded growth

    def add_memory(
        self,
        content: str,
        location: Optional[str] = None,
        participants: Optional[List[str]] = None,
        emotional_valence: float = 0.0,
        emotional_intensity: float = 0.0,
        importance: float = 0.5,
    ) -> Memory:
        """Add a new episodic memory."""
        memory_id = self._generate_memory_id(content)

        memory = Memory(
            memory_id=memory_id,
            memory_type=MemoryType.EPISODIC,
            content=content,
            location=location,
            participants=participants or [],
            emotional_valence=emotional_valence,
            emotional_intensity=emotional_intensity,
            importance=importance,
        )

        self.memories.append(memory)

        # Prune if over limit
        if len(self.memories) > self.max_memories:
            self._prune_memories()

        return memory

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a specific memory by ID."""
        for memory in self.memories:
            if memory.memory_id == memory_id:
                memory.access()
                return memory
        return None

    def recall_recent(self, hours: float = 24.0, limit: int = 10) -> List[Memory]:
        """Recall memories from the last N hours."""
        cutoff_time = time.time() - (hours * 3600)

        recent = [m for m in self.memories if m.timestamp >= cutoff_time]

        # Sort by accessibility
        recent.sort(key=lambda m: m.get_accessibility(), reverse=True)

        # Access the recalled memories
        for memory in recent[:limit]:
            memory.access()

        return recent[:limit]

    def recall_about(self, subject: str, limit: int = 5) -> List[Memory]:
        """Recall memories mentioning a subject (agent, location, topic)."""
        relevant = []

        for memory in self.memories:
            # Check if subject mentioned in content or participants
            if subject.lower() in memory.content.lower():
                relevant.append(memory)
            elif subject in memory.participants:
                relevant.append(memory)
            elif memory.location and subject.lower() in memory.location.lower():
                relevant.append(memory)

        # Sort by accessibility
        relevant.sort(key=lambda m: m.get_accessibility(), reverse=True)

        # Access the recalled memories
        for memory in relevant[:limit]:
            memory.access()

        return relevant[:limit]

    def recall_emotional(
        self, valence: Optional[float] = None, min_intensity: float = 0.5, limit: int = 5
    ) -> List[Memory]:
        """
        Recall emotionally charged memories.

        Args:
            valence: If specified, filter by positive (>0) or negative (<0)
            min_intensity: Minimum emotional intensity
            limit: Maximum number to recall
        """
        emotional = []

        for memory in self.memories:
            if memory.emotional_intensity < min_intensity:
                continue

            if valence is not None:
                if valence > 0 and memory.emotional_valence <= 0:
                    continue
                if valence < 0 and memory.emotional_valence >= 0:
                    continue

            emotional.append(memory)

        # Sort by emotional intensity * accessibility
        emotional.sort(
            key=lambda m: m.emotional_intensity * m.get_accessibility(), reverse=True
        )

        # Access the recalled memories
        for memory in emotional[:limit]:
            memory.access()

        return emotional[:limit]

    def recall_with_agent(self, agent_name: str, limit: int = 5) -> List[Memory]:
        """Recall memories involving a specific agent."""
        return self.recall_about(agent_name, limit)

    def _generate_memory_id(self, content: str) -> str:
        """Generate unique memory ID."""
        combined = f"{content}:{time.time()}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def _prune_memories(self) -> None:
        """Prune least accessible memories when over limit."""
        # Keep most important and accessible memories
        self.memories.sort(key=lambda m: m.get_accessibility(), reverse=True)
        self.memories = self.memories[: self.max_memories]

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary statistics of memory."""
        if not self.memories:
            return {"total": 0, "emotional": 0, "avg_importance": 0.0}

        emotional = sum(1 for m in self.memories if m.is_emotionally_significant())
        avg_importance = sum(m.importance for m in self.memories) / len(self.memories)

        return {
            "total": len(self.memories),
            "emotional": emotional,
            "avg_importance": avg_importance,
            "oldest_memory_hours": max(m.get_age_hours() for m in self.memories),
        }

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "memories": [m.to_dict() for m in self.memories],
            "max_memories": self.max_memories,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "EpisodicMemory":
        """Deserialize from saved data."""
        memories = [Memory.from_dict(m) for m in data.get("memories", [])]
        return cls(memories=memories, max_memories=data.get("max_memories", 1000))


@dataclass
class SemanticMemory:
    """
    Semantic memory system for general knowledge.

    Stores facts, procedures, and general knowledge separate from
    specific experiences.

    Examples:
    - "Bread costs 2 gold"
    - "Gene the bartender owns the tavern"
    - "To clean tables, you need a rag"
    """

    knowledge: Dict[str, Memory] = field(default_factory=dict)  # topic -> memory

    def add_knowledge(
        self, topic: str, content: str, confidence: float = 0.8, source: Optional[str] = None
    ) -> Memory:
        """Add or update general knowledge."""
        memory_id = hashlib.md5(topic.encode()).hexdigest()[:16]

        memory = Memory(
            memory_id=memory_id,
            memory_type=MemoryType.SEMANTIC,
            content=content,
            importance=confidence,  # Confidence maps to importance
        )

        if source:
            memory.participants = [source]  # Track source of knowledge

        self.knowledge[topic] = memory
        return memory

    def get_knowledge(self, topic: str) -> Optional[Memory]:
        """Retrieve knowledge about a topic."""
        memory = self.knowledge.get(topic)
        if memory:
            memory.access()
        return memory

    def knows_about(self, topic: str, min_confidence: float = 0.5) -> bool:
        """Check if agent has knowledge about topic with sufficient confidence."""
        memory = self.knowledge.get(topic)
        return memory is not None and memory.importance >= min_confidence

    def get_all_knowledge(self) -> List[Memory]:
        """Get all semantic knowledge, sorted by importance."""
        return sorted(self.knowledge.values(), key=lambda m: m.importance, reverse=True)

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {"knowledge": {topic: mem.to_dict() for topic, mem in self.knowledge.items()}}

    @classmethod
    def from_dict(cls, data: Dict) -> "SemanticMemory":
        """Deserialize from saved data."""
        knowledge = {
            topic: Memory.from_dict(mem_data)
            for topic, mem_data in data.get("knowledge", {}).items()
        }
        return cls(knowledge=knowledge)
