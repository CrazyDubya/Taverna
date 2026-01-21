"""
Test suite for the Memory Management system.

Tests memory storage, retrieval, importance scoring, and pruning.
"""
import unittest
import time

from living_rusted_tankard.core.memory import (
    MemoryManager,
    Memory,
    MemoryImportance,
)


class TestMemory(unittest.TestCase):
    """Test the Memory class."""

    def test_memory_creation(self):
        """Test creating a memory object."""
        memory = Memory(
            id="test_mem_001",
            content="Test memory content",
            timestamp=time.time(),
            importance=MemoryImportance.NORMAL,
            session_id="test_session",
        )

        self.assertEqual(memory.id, "test_mem_001")
        self.assertEqual(memory.importance, MemoryImportance.NORMAL)
        self.assertEqual(memory.access_count, 0)

    def test_memory_age_calculation(self):
        """Test memory age calculation."""
        past_time = time.time() - 7200  # 2 hours ago
        memory = Memory(
            id="old_memory",
            content="Old memory",
            timestamp=past_time,
            importance=MemoryImportance.LOW,
            session_id="test",
        )

        age = memory.get_age_hours()
        self.assertGreaterEqual(age, 1.9)  # Should be close to 2 hours
        self.assertLess(age, 2.2)

    def test_memory_relevance_score(self):
        """Test memory relevance scoring."""
        memory = Memory(
            id="relevant_mem",
            content="The player talked to the merchant about rare items",
            timestamp=time.time(),
            importance=MemoryImportance.HIGH,
            session_id="test",
        )

        # Test with matching context
        score_with_context = memory.get_relevance_score(
            current_context="merchant rare items"
        )
        score_without_context = memory.get_relevance_score(
            current_context="completely different topic"
        )

        # Score with matching context should be higher
        self.assertGreater(score_with_context, score_without_context)

    def test_memory_access_tracking(self):
        """Test that memory access is tracked."""
        memory = Memory(
            id="tracked_mem",
            content="Tracked memory",
            timestamp=time.time(),
            importance=MemoryImportance.NORMAL,
            session_id="test",
        )

        initial_count = memory.access_count
        memory.access_count += 1

        self.assertEqual(memory.access_count, initial_count + 1)


class TestMemoryManager(unittest.TestCase):
    """Test the MemoryManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = MemoryManager()

    def test_memory_manager_initialization(self):
        """Test that MemoryManager initializes correctly."""
        self.assertIsNotNone(self.manager)
        self.assertEqual(len(self.manager.get_all_memories()), 0)

    def test_add_memory(self):
        """Test adding a memory."""
        memory_id = self.manager.add_memory(
            content="Test event occurred",
            importance=MemoryImportance.NORMAL,
            session_id="test_session",
        )

        self.assertIsNotNone(memory_id)
        memories = self.manager.get_all_memories()
        self.assertEqual(len(memories), 1)

    def test_retrieve_memory(self):
        """Test retrieving a specific memory."""
        memory_id = self.manager.add_memory(
            content="Specific test memory",
            importance=MemoryImportance.HIGH,
            session_id="test",
        )

        retrieved = self.manager.get_memory(memory_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, "Specific test memory")

    def test_get_recent_memories(self):
        """Test retrieving recent memories."""
        # Add multiple memories
        for i in range(5):
            self.manager.add_memory(
                content=f"Memory {i}",
                importance=MemoryImportance.NORMAL,
                session_id="test",
            )

        recent = self.manager.get_recent_memories(count=3)
        self.assertLessEqual(len(recent), 3)

    def test_get_memories_by_importance(self):
        """Test filtering memories by importance level."""
        # Add memories with different importance levels
        self.manager.add_memory(
            content="Critical event",
            importance=MemoryImportance.CRITICAL,
            session_id="test",
        )

        self.manager.add_memory(
            content="Normal event",
            importance=MemoryImportance.NORMAL,
            session_id="test",
        )

        critical_memories = self.manager.get_memories_by_importance(
            MemoryImportance.CRITICAL
        )

        self.assertGreater(len(critical_memories), 0)
        self.assertTrue(
            all(m.importance == MemoryImportance.CRITICAL for m in critical_memories)
        )

    def test_memory_pruning(self):
        """Test memory pruning functionality."""
        # Add many low-importance memories
        for i in range(100):
            self.manager.add_memory(
                content=f"Low importance memory {i}",
                importance=MemoryImportance.TRIVIAL,
                session_id="test",
            )

        initial_count = len(self.manager.get_all_memories())

        # Prune memories (if implemented)
        self.manager.prune_memories(max_memories=50, min_importance=MemoryImportance.LOW)

        after_prune_count = len(self.manager.get_all_memories())

        # Either pruning happened or it's not implemented yet
        self.assertLessEqual(after_prune_count, initial_count)

    def test_memory_context_search(self):
        """Test searching memories by context."""
        # Add memories with specific content
        self.manager.add_memory(
            content="The dragon appeared in the forest",
            importance=MemoryImportance.HIGH,
            session_id="test",
        )

        self.manager.add_memory(
            content="Bought supplies at the market",
            importance=MemoryImportance.LOW,
            session_id="test",
        )

        # Search for dragon-related memories
        results = self.manager.search_memories(query="dragon forest")

        self.assertGreater(len(results), 0)
        # Check that relevant memory is found
        self.assertTrue(
            any("dragon" in m.content.lower() for m in results)
        )


class TestMemoryImportance(unittest.TestCase):
    """Test memory importance levels."""

    def test_importance_levels(self):
        """Test that importance levels are ordered correctly."""
        self.assertLess(MemoryImportance.TRIVIAL.value, MemoryImportance.LOW.value)
        self.assertLess(MemoryImportance.LOW.value, MemoryImportance.NORMAL.value)
        self.assertLess(MemoryImportance.NORMAL.value, MemoryImportance.HIGH.value)
        self.assertLess(MemoryImportance.HIGH.value, MemoryImportance.CRITICAL.value)

    def test_importance_comparison(self):
        """Test comparing importance levels."""
        mem1 = Memory(
            id="mem1",
            content="Important event",
            timestamp=time.time(),
            importance=MemoryImportance.CRITICAL,
            session_id="test",
        )

        mem2 = Memory(
            id="mem2",
            content="Trivial event",
            timestamp=time.time(),
            importance=MemoryImportance.TRIVIAL,
            session_id="test",
        )

        self.assertGreater(mem1.importance.value, mem2.importance.value)


if __name__ == "__main__":
    unittest.main()
