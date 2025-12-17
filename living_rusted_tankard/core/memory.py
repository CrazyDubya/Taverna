"""
Enhanced Memory Management System for The Living Rusted Tankard.

This module provides intelligent memory management with:
- Conversation summarization to reduce context size
- Importance-based memory retention
- Automatic memory pruning and optimization
- Context-aware memory retrieval for LLM prompts

Integrates with:
- enhanced_llm_game_master.py (existing memory system)
- async_llm_pipeline.py (context optimization)
- time_display.py (time-based memory context)
"""

import logging
import time
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class MemoryImportance(Enum):
    """Importance levels for memories."""

    TRIVIAL = 1  # Small talk, routine interactions
    LOW = 2  # Basic information, common responses
    NORMAL = 3  # Standard interactions, game events
    HIGH = 4  # Significant events, character development
    CRITICAL = 5  # Major decisions, story moments


@dataclass
class Memory:
    """Represents a single memory with metadata."""

    id: str
    content: str
    timestamp: float
    importance: MemoryImportance
    session_id: str
    context: Optional[Dict[str, Any]] = None
    access_count: int = 0
    last_accessed: float = 0.0
    summary: Optional[str] = None

    def __post_init__(self):
        if self.last_accessed == 0.0:
            self.last_accessed = self.timestamp

    def get_age_hours(self) -> float:
        """Get memory age in hours."""
        return (time.time() - self.timestamp) / 3600.0

    def get_relevance_score(self, current_context: str = "") -> float:
        """Calculate relevance score based on importance, age, and context match."""
        # Base score from importance
        base_score = self.importance.value * 0.2

        # Age penalty (memories decay over time)
        age_hours = self.get_age_hours()
        age_penalty = min(0.5, age_hours / 24.0)  # Max 50% penalty after 24 hours

        # Access frequency bonus
        access_bonus = min(0.3, self.access_count * 0.05)  # Max 30% bonus

        # Context relevance bonus
        context_bonus = 0.0
        if current_context and self.content:
            # Simple keyword matching for relevance
            context_words = set(current_context.lower().split())
            memory_words = set(self.content.lower().split())
            overlap = len(context_words.intersection(memory_words))
            if overlap > 0:
                context_bonus = min(0.4, overlap * 0.1)  # Max 40% bonus

        return base_score - age_penalty + access_bonus + context_bonus


class ConversationSummarizer:
    """Summarizes conversation history to reduce memory usage."""

    def __init__(self):
        self.summary_templates = {
            "quest_interaction": "Player discussed quest '{quest}' with {npc}. Outcome: {outcome}",
            "purchase": "Player bought {item} for {price} gold from {npc}",
            "social": "Player had {type} conversation with {npc} about {topic}",
            "exploration": "Player explored {location} and discovered {discovery}",
            "general": "Player interacted with {npc}. Key points: {points}",
        }

    def summarize_conversation_batch(self, messages: List[str], context: Dict[str, Any] = None) -> str:
        """Summarize a batch of conversation messages."""
        if not messages:
            return ""

        if len(messages) == 1:
            return self._create_single_message_summary(messages[0], context)

        # Extract key information from the conversation
        key_info = self._extract_key_information(messages, context)

        # Generate summary based on conversation type
        conversation_type = self._classify_conversation(messages)
        template = self.summary_templates.get(conversation_type, self.summary_templates["general"])

        try:
            summary = template.format(**key_info)
        except KeyError:
            # Fallback to generic summary
            summary = (
                f"Conversation involving {key_info.get('npc', 'unknown')}. "
                + f"Topics: {', '.join(key_info.get('topics', ['general discussion']))}"
            )

        return summary

    def _create_single_message_summary(self, message: str, context: Dict[str, Any] = None) -> str:
        """Create summary for a single message."""
        # Truncate very long messages
        if len(message) > 200:
            return message[:197] + "..."
        return message

    def _extract_key_information(self, messages: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract key information from conversation messages."""
        combined_text = " ".join(messages).lower()

        # Extract NPCs mentioned
        npcs = []
        if context and "npcs" in context:
            npcs = [npc for npc in context["npcs"] if npc.lower() in combined_text]

        # Extract items mentioned
        items = []
        item_patterns = [r"\b(ale|wine|bread|sword|shield|potion|coin|gold)\b"]
        for pattern in item_patterns:
            items.extend(re.findall(pattern, combined_text))

        # Extract topics
        topics = []
        topic_patterns = [
            r"\b(quest|mission|task|job|work)\b",
            r"\b(weather|time|day|night)\b",
            r"\b(trade|buy|sell|purchase)\b",
            r"\b(rumor|news|gossip|story)\b",
        ]
        for pattern in topic_patterns:
            matches = re.findall(pattern, combined_text)
            topics.extend(matches)

        return {
            "npc": npcs[0] if npcs else "someone",
            "npcs": npcs,
            "items": list(set(items)),
            "topics": list(set(topics)),
            "points": "; ".join(messages[-2:]) if len(messages) > 1 else messages[0],
        }

    def _classify_conversation(self, messages: List[str]) -> str:
        """Classify the type of conversation."""
        combined_text = " ".join(messages).lower()

        if any(word in combined_text for word in ["quest", "mission", "task", "job"]):
            return "quest_interaction"
        elif any(word in combined_text for word in ["buy", "purchase", "sell", "trade", "gold", "coin"]):
            return "purchase"
        elif any(word in combined_text for word in ["explore", "look", "examine", "search"]):
            return "exploration"
        elif any(word in combined_text for word in ["hello", "greet", "chat", "talk", "gossip"]):
            return "social"
        else:
            return "general"


class MemoryManager:
    """Enhanced memory management system."""

    def __init__(self, max_memories_per_session: int = 100, max_context_memories: int = 5):
        self.max_memories_per_session = max_memories_per_session
        self.max_context_memories = max_context_memories

        # Memory storage: session_id -> List[Memory]
        self.memories: Dict[str, List[Memory]] = {}

        # Conversation summarizer
        self.summarizer = ConversationSummarizer()

        # Statistics
        self.stats = {
            "total_memories": 0,
            "memories_created": 0,
            "memories_pruned": 0,
            "summaries_created": 0,
            "context_retrievals": 0,
        }

    def add_memory(
        self,
        session_id: str,
        content: str,
        importance: MemoryImportance = MemoryImportance.NORMAL,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a new memory."""
        memory_id = self._generate_memory_id(session_id, content)

        memory = Memory(
            id=memory_id,
            content=content,
            timestamp=time.time(),
            importance=importance,
            session_id=session_id,
            context=context or {},
        )

        if session_id not in self.memories:
            self.memories[session_id] = []

        self.memories[session_id].append(memory)
        self.stats["total_memories"] += 1
        self.stats["memories_created"] += 1

        # Prune memories if we're over the limit
        self._prune_memories_if_needed(session_id)

        logger.debug(f"Added memory for session {session_id}: {content[:50]}...")
        return memory_id

    def get_relevant_memories(
        self, session_id: str, context: str = "", max_memories: Optional[int] = None
    ) -> List[Memory]:
        """Get the most relevant memories for current context."""
        if session_id not in self.memories:
            return []

        max_memories = max_memories or self.max_context_memories
        session_memories = self.memories[session_id]

        # Score all memories by relevance
        scored_memories = []
        for memory in session_memories:
            relevance_score = memory.get_relevance_score(context)
            scored_memories.append((relevance_score, memory))

        # Sort by relevance score (descending)
        scored_memories.sort(key=lambda x: x[0], reverse=True)

        # Update access count for retrieved memories
        relevant_memories = []
        for score, memory in scored_memories[:max_memories]:
            memory.access_count += 1
            memory.last_accessed = time.time()
            relevant_memories.append(memory)

        self.stats["context_retrievals"] += 1

        logger.debug(f"Retrieved {len(relevant_memories)} relevant memories for session {session_id}")
        return relevant_memories

    def summarize_old_memories(self, session_id: str, age_threshold_hours: float = 24.0) -> int:
        """Summarize old memories to reduce storage space."""
        if session_id not in self.memories:
            return 0

        current_time = time.time()
        old_memories = []
        keep_memories = []

        for memory in self.memories[session_id]:
            age_hours = (current_time - memory.timestamp) / 3600.0

            # Keep critical memories and recent memories
            if memory.importance == MemoryImportance.CRITICAL or age_hours < age_threshold_hours:
                keep_memories.append(memory)
            else:
                old_memories.append(memory)

        if not old_memories:
            return 0

        # Group old memories by time period and summarize
        summarized_count = 0
        time_groups = self._group_memories_by_time(old_memories)

        for time_period, memories in time_groups.items():
            if len(memories) > 1:
                # Create summary
                memory_contents = [mem.content for mem in memories]
                summary_content = self.summarizer.summarize_conversation_batch(
                    memory_contents, {"session_id": session_id}
                )

                # Create summary memory with averaged importance
                avg_importance = sum(mem.importance.value for mem in memories) // len(memories)
                summary_importance = MemoryImportance(max(1, min(5, avg_importance)))

                summary_memory = Memory(
                    id=self._generate_memory_id(session_id, f"summary_{time_period}"),
                    content=f"[Summary] {summary_content}",
                    timestamp=memories[0].timestamp,  # Use earliest timestamp
                    importance=summary_importance,
                    session_id=session_id,
                    summary=f"Summary of {len(memories)} memories",
                )

                keep_memories.append(summary_memory)
                summarized_count += len(memories)
                self.stats["summaries_created"] += 1
            else:
                # Keep single memories as-is
                keep_memories.extend(memories)

        # Update memory list
        self.memories[session_id] = keep_memories
        self.stats["total_memories"] = sum(len(mems) for mems in self.memories.values())

        logger.info(f"Summarized {summarized_count} old memories for session {session_id}")
        return summarized_count

    def _prune_memories_if_needed(self, session_id: str) -> None:
        """Prune memories if session has too many."""
        if session_id not in self.memories:
            return

        session_memories = self.memories[session_id]
        if len(session_memories) <= self.max_memories_per_session:
            return

        # First try summarizing old memories
        self.summarize_old_memories(session_id)

        # If still too many, remove least relevant memories
        if len(self.memories[session_id]) > self.max_memories_per_session:
            memories_to_remove = len(self.memories[session_id]) - self.max_memories_per_session

            # Sort by relevance (keeping most relevant)
            scored_memories = []
            for memory in self.memories[session_id]:
                relevance_score = memory.get_relevance_score()
                scored_memories.append((relevance_score, memory))

            scored_memories.sort(key=lambda x: x[0], reverse=True)

            # Keep the most relevant memories
            self.memories[session_id] = [memory for score, memory in scored_memories[:-memories_to_remove]]

            self.stats["memories_pruned"] += memories_to_remove

            logger.info(f"Pruned {memories_to_remove} memories for session {session_id}")

    def _group_memories_by_time(self, memories: List[Memory]) -> Dict[str, List[Memory]]:
        """Group memories by time periods for summarization."""
        groups = {}

        for memory in memories:
            # Group by day
            memory_day = int(memory.timestamp // 86400)  # 86400 seconds in a day
            day_key = f"day_{memory_day}"

            if day_key not in groups:
                groups[day_key] = []
            groups[day_key].append(memory)

        return groups

    def _generate_memory_id(self, session_id: str, content: str) -> str:
        """Generate unique memory ID."""
        combined = f"{session_id}:{content}:{time.time()}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def get_memory_context_for_llm(self, session_id: str, current_input: str = "") -> str:
        """Get formatted memory context for LLM prompts."""
        relevant_memories = self.get_relevant_memories(session_id, current_input)

        if not relevant_memories:
            return ""

        # Format memories for LLM context
        memory_texts = []
        for memory in relevant_memories:
            # Add time context using natural time display
            age_hours = memory.get_age_hours()
            if age_hours < 1:
                time_ref = "recently"
            elif age_hours < 24:
                time_ref = f"{int(age_hours)} hours ago"
            else:
                time_ref = f"{int(age_hours // 24)} days ago"

            memory_text = f"{memory.content} ({time_ref})"
            memory_texts.append(memory_text)

        return " | ".join(memory_texts)

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session."""
        if session_id not in self.memories:
            return {"total_memories": 0, "importance_breakdown": {}}

        session_memories = self.memories[session_id]
        importance_counts = {}

        for memory in session_memories:
            importance = memory.importance.name
            importance_counts[importance] = importance_counts.get(importance, 0) + 1

        return {
            "total_memories": len(session_memories),
            "importance_breakdown": importance_counts,
            "oldest_memory_age_hours": max(mem.get_age_hours() for mem in session_memories) if session_memories else 0,
            "newest_memory_age_hours": min(mem.get_age_hours() for mem in session_memories) if session_memories else 0,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics."""
        stats = self.stats.copy()
        stats["active_sessions"] = len(self.memories)
        stats["average_memories_per_session"] = stats["total_memories"] / max(1, stats["active_sessions"])
        return stats


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def add_session_memory(
    session_id: str,
    content: str,
    importance: MemoryImportance = MemoryImportance.NORMAL,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """Convenience function to add a memory."""
    manager = get_memory_manager()
    return manager.add_memory(session_id, content, importance, context)


def get_memory_context_for_llm(session_id: str, current_input: str = "") -> str:
    """Convenience function to get memory context for LLM."""
    manager = get_memory_manager()
    return manager.get_memory_context_for_llm(session_id, current_input)


def cleanup_old_memories(age_threshold_hours: float = 48.0) -> int:
    """Cleanup old memories across all sessions."""
    manager = get_memory_manager()
    total_summarized = 0

    for session_id in manager.memories.keys():
        summarized = manager.summarize_old_memories(session_id, age_threshold_hours)
        total_summarized += summarized

    return total_summarized


if __name__ == "__main__":
    # Test the memory system
    print("=== Memory Management System Test ===")

    manager = MemoryManager()
    session_id = "test-session"

    # Add some test memories
    manager.add_memory(session_id, "Player talked to Gene the bartender", MemoryImportance.NORMAL)
    manager.add_memory(session_id, "Player bought ale for 2 gold", MemoryImportance.LOW)
    manager.add_memory(session_id, "Player discovered secret quest about missing kegs", MemoryImportance.HIGH)
    manager.add_memory(session_id, "Player said hello", MemoryImportance.TRIVIAL)

    print(f"Added 4 memories. Total: {len(manager.memories[session_id])}")

    # Test retrieval
    relevant = manager.get_relevant_memories(session_id, "bartender ale")
    print(f"Relevant memories for 'bartender ale': {len(relevant)}")
    for memory in relevant:
        print(f"  - {memory.content} (score: {memory.get_relevance_score('bartender ale'):.2f})")

    # Test LLM context
    context = manager.get_memory_context_for_llm(session_id, "talk to bartender")
    print(f"LLM context: {context}")

    print("✅ Memory system test completed")
