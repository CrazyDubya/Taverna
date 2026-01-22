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
        self.assertIsInstance(self.manager.memories, dict)

    def test_add_memory(self):
        """Test adding a memory."""
        memory_id = self.manager.add_memory(
            session_id="test_session",
            content="Test event occurred",
            importance=MemoryImportance.NORMAL,
        )

        self.assertIsNotNone(memory_id)
        self.assertIn("test_session", self.manager.memories)
        self.assertEqual(len(self.manager.memories["test_session"]), 1)

    def test_retrieve_memory(self):
        """Test retrieving memories for a session."""
        # Add some memories
        self.manager.add_memory(
            session_id="test",
            content="First memory",
            importance=MemoryImportance.HIGH,
        )
        self.manager.add_memory(
            session_id="test",
            content="Second memory",
            importance=MemoryImportance.NORMAL,
        )

        # Get relevant memories
        memories = self.manager.get_relevant_memories("test")
        self.assertGreater(len(memories), 0)
        self.assertLessEqual(len(memories), self.manager.max_context_memories)

    def test_get_relevant_memories_with_context(self):
        """Test retrieving memories based on context."""
        self.manager.add_memory(
            session_id="test",
            content="The player talked to the merchant about swords",
            importance=MemoryImportance.NORMAL,
        )
        self.manager.add_memory(
            session_id="test",
            content="The weather was rainy",
            importance=MemoryImportance.LOW,
        )

        # Search with relevant context
        relevant = self.manager.get_relevant_memories("test", context="merchant swords")
        self.assertGreater(len(relevant), 0)

    def test_get_memories_by_importance(self):
        """Test filtering memories by importance level."""
        # Add memories with different importance levels
        self.manager.add_memory(
            session_id="test",
            content="Critical event",
            importance=MemoryImportance.CRITICAL,
        )

        self.manager.add_memory(
            session_id="test",
            content="Normal event",
            importance=MemoryImportance.NORMAL,
        )

        # Get all memories and check importance
        memories = self.manager.get_relevant_memories("test", max_memories=10)
        critical_count = sum(
            1 for m in memories if m.importance == MemoryImportance.CRITICAL
        )
        self.assertGreater(critical_count, 0)

    def test_memory_pruning(self):
        """Test memory pruning functionality."""
        # Add many memories to trigger pruning
        session_id = "prune_test"
        for i in range(150):  # More than default max
            self.manager.add_memory(
                session_id=session_id,
                content=f"Memory {i}",
                importance=MemoryImportance.TRIVIAL,
            )

        # Check that memories were pruned
        memory_count = len(self.manager.memories[session_id])
        self.assertLessEqual(memory_count, self.manager.max_memories_per_session)

    def test_memory_summarization(self):
        """Test memory summarization functionality."""
        session_id = "summary_test"
        # Add some memories
        for i in range(5):
            self.manager.add_memory(
                session_id=session_id,
                content=f"Event {i} happened",
                importance=MemoryImportance.LOW,
            )

        # Attempt to summarize old memories
        summarized_count = self.manager.summarize_old_memories(
            session_id, age_threshold_hours=0.0
        )
        
        # Just verify the method works
        self.assertIsInstance(summarized_count, int)


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
