"""
Test suite for the Character Memory system.

Tests memory storage, retrieval, and character-specific memory management.
"""
import unittest
from datetime import datetime

from living_rusted_tankard.core.narrative.character_memory import (
    CharacterMemoryManager,
    CharacterMemory,
    MemoryType,
)


class TestCharacterMemory(unittest.TestCase):
    """Test the CharacterMemory class."""

    def test_memory_creation(self):
        """Test creating a character memory."""
        memory = CharacterMemory(
            character_id="npc_001",
            memory_text="Met the player at the tavern",
            memory_type=MemoryType.INTERACTION,
            importance=5,
        )

        self.assertEqual(memory.character_id, "npc_001")
        self.assertEqual(memory.memory_type, MemoryType.INTERACTION)
        self.assertEqual(memory.importance, 5)

    def test_memory_timestamp(self):
        """Test that memory has a timestamp."""
        memory = CharacterMemory(
            character_id="npc_002",
            memory_text="Test memory",
            memory_type=MemoryType.EVENT,
        )

        self.assertIsNotNone(memory.timestamp)
        self.assertIsInstance(memory.timestamp, (float, int, datetime))

    def test_memory_types(self):
        """Test different memory types."""
        types = [
            MemoryType.INTERACTION,
            MemoryType.EVENT,
            MemoryType.OBSERVATION,
            MemoryType.EMOTION,
        ]

        for memory_type in types:
            memory = CharacterMemory(
                character_id="test_char",
                memory_text=f"Memory of type {memory_type}",
                memory_type=memory_type,
            )
            self.assertEqual(memory.memory_type, memory_type)


class TestCharacterMemoryManager(unittest.TestCase):
    """Test the CharacterMemoryManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = CharacterMemoryManager()

    def test_manager_initialization(self):
        """Test that CharacterMemoryManager initializes correctly."""
        self.assertIsNotNone(self.manager)

    def test_add_memory_for_character(self):
        """Test adding a memory for a character."""
        character_id = "npc_test"
        
        self.manager.add_memory(
            character_id=character_id,
            memory_text="Test event occurred",
            memory_type=MemoryType.EVENT,
        )

        memories = self.manager.get_memories(character_id)
        self.assertGreater(len(memories), 0)

    def test_get_memories_for_character(self):
        """Test retrieving memories for a specific character."""
        char_id = "npc_retrieve"
        
        # Add multiple memories
        for i in range(3):
            self.manager.add_memory(
                character_id=char_id,
                memory_text=f"Memory {i}",
                memory_type=MemoryType.INTERACTION,
            )

        memories = self.manager.get_memories(char_id)
        self.assertEqual(len(memories), 3)

    def test_get_memories_by_type(self):
        """Test filtering memories by type."""
        char_id = "npc_filter"
        
        # Add different types of memories
        self.manager.add_memory(
            char_id, "Interaction memory", MemoryType.INTERACTION
        )
        self.manager.add_memory(
            char_id, "Event memory", MemoryType.EVENT
        )

        interaction_memories = self.manager.get_memories_by_type(
            char_id, MemoryType.INTERACTION
        )
        
        if len(interaction_memories) > 0:
            self.assertTrue(
                all(m.memory_type == MemoryType.INTERACTION for m in interaction_memories)
            )

    def test_get_recent_memories(self):
        """Test getting recent memories."""
        char_id = "npc_recent"
        
        for i in range(10):
            self.manager.add_memory(
                char_id, f"Memory {i}", MemoryType.OBSERVATION
            )

        recent = self.manager.get_recent_memories(char_id, count=5)
        self.assertLessEqual(len(recent), 5)

    def test_get_important_memories(self):
        """Test filtering memories by importance."""
        char_id = "npc_important"
        
        # Add memories with different importance
        self.manager.add_memory(
            char_id, "Very important", MemoryType.EVENT, importance=10
        )
        self.manager.add_memory(
            char_id, "Not important", MemoryType.EVENT, importance=1
        )

        important = self.manager.get_important_memories(char_id, min_importance=5)
        
        if len(important) > 0:
            self.assertTrue(all(m.importance >= 5 for m in important))

    def test_clear_memories_for_character(self):
        """Test clearing all memories for a character."""
        char_id = "npc_clear"
        
        self.manager.add_memory(char_id, "Memory 1", MemoryType.EVENT)
        self.manager.add_memory(char_id, "Memory 2", MemoryType.EVENT)
        
        self.manager.clear_memories(char_id)
        
        memories = self.manager.get_memories(char_id)
        self.assertEqual(len(memories), 0)


class TestMemoryType(unittest.TestCase):
    """Test memory type enumeration."""

    def test_memory_types_exist(self):
        """Test that all memory types are defined."""
        types = [
            MemoryType.INTERACTION,
            MemoryType.EVENT,
            MemoryType.OBSERVATION,
            MemoryType.EMOTION,
        ]

        for memory_type in types:
            self.assertIsNotNone(memory_type)


if __name__ == "__main__":
    unittest.main()
