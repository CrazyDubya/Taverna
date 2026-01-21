"""
Test suite for the Bounty system.

Tests bounty creation, tracking, completion, and rewards.
"""
import unittest
import tempfile
import shutil
from pathlib import Path

from living_rusted_tankard.core.bounties import (
    BountyManager,
    BountyObjective,
    BountyStatus,
)


class TestBountyManager(unittest.TestCase):
    """Test the BountyManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.bounty_manager = BountyManager(data_dir=self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_bounty_manager_initialization(self):
        """Test that BountyManager initializes correctly."""
        self.assertIsNotNone(self.bounty_manager)
        self.assertEqual(self.bounty_manager.data_dir, Path(self.test_dir))

    def test_create_bounty(self):
        """Test creating a new bounty."""
        bounty_id = "test_bounty_001"
        title = "Test Bounty"
        description = "A test bounty for unit testing"
        reward_gold = 100
        objectives = [
            BountyObjective(
                id="obj1",
                description="Test objective",
                target="test_target",
                current=0,
                required=5,
            )
        ]

        bounty = self.bounty_manager.create_bounty(
            bounty_id=bounty_id,
            title=title,
            description=description,
            reward_gold=reward_gold,
            objectives=objectives,
        )

        self.assertEqual(bounty.id, bounty_id)
        self.assertEqual(bounty.title, title)
        self.assertEqual(bounty.description, description)
        self.assertEqual(bounty.reward_gold, reward_gold)
        self.assertEqual(len(bounty.objectives), 1)
        self.assertEqual(bounty.status, BountyStatus.AVAILABLE)

    def test_get_active_bounties(self):
        """Test retrieving active bounties."""
        # Create a test bounty
        self.bounty_manager.create_bounty(
            bounty_id="bounty1",
            title="Active Bounty",
            description="Test",
            reward_gold=50,
            objectives=[],
        )

        active = self.bounty_manager.get_active_bounties()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].id, "bounty1")

    def test_complete_bounty_objective(self):
        """Test completing a bounty objective."""
        objectives = [
            BountyObjective(
                id="obj1",
                description="Collect items",
                target="apple",
                current=0,
                required=3,
            )
        ]

        bounty = self.bounty_manager.create_bounty(
            bounty_id="bounty_obj",
            title="Objective Test",
            description="Test objectives",
            reward_gold=75,
            objectives=objectives,
        )

        # Progress the objective
        self.bounty_manager.update_bounty_progress("bounty_obj", "obj1", 2)
        bounty = self.bounty_manager.get_bounty("bounty_obj")
        self.assertEqual(bounty.objectives[0].current, 2)
        self.assertFalse(bounty.objectives[0].is_completed())

        # Complete the objective
        self.bounty_manager.update_bounty_progress("bounty_obj", "obj1", 1)
        bounty = self.bounty_manager.get_bounty("bounty_obj")
        self.assertEqual(bounty.objectives[0].current, 3)
        self.assertTrue(bounty.objectives[0].is_completed())

    def test_bounty_status_transitions(self):
        """Test bounty status changes."""
        bounty = self.bounty_manager.create_bounty(
            bounty_id="status_test",
            title="Status Test",
            description="Test status transitions",
            reward_gold=100,
            objectives=[],
        )

        self.assertEqual(bounty.status, BountyStatus.AVAILABLE)

        # Accept bounty
        self.bounty_manager.accept_bounty("status_test")
        bounty = self.bounty_manager.get_bounty("status_test")
        self.assertEqual(bounty.status, BountyStatus.ACTIVE)

        # Complete bounty
        self.bounty_manager.complete_bounty("status_test")
        bounty = self.bounty_manager.get_bounty("status_test")
        self.assertEqual(bounty.status, BountyStatus.COMPLETED)

    def test_bounty_rewards(self):
        """Test bounty reward calculation."""
        bounty = self.bounty_manager.create_bounty(
            bounty_id="reward_test",
            title="Reward Test",
            description="Test rewards",
            reward_gold=150,
            objectives=[],
        )

        self.assertEqual(bounty.reward_gold, 150)
        self.bounty_manager.accept_bounty("reward_test")
        self.bounty_manager.complete_bounty("reward_test")

        bounty = self.bounty_manager.get_bounty("reward_test")
        self.assertEqual(bounty.status, BountyStatus.COMPLETED)


class TestBountyObjective(unittest.TestCase):
    """Test the BountyObjective class."""

    def test_objective_creation(self):
        """Test creating a bounty objective."""
        obj = BountyObjective(
            id="test_obj",
            description="Test objective",
            target="wolves",
            current=0,
            required=10,
        )

        self.assertEqual(obj.id, "test_obj")
        self.assertEqual(obj.target, "wolves")
        self.assertEqual(obj.current, 0)
        self.assertEqual(obj.required, 10)
        self.assertFalse(obj.is_completed())

    def test_objective_progress(self):
        """Test objective progress tracking."""
        obj = BountyObjective(
            id="progress_test",
            description="Progress test",
            target="items",
            current=3,
            required=10,
        )

        self.assertEqual(obj.progress_percentage(), 30.0)
        self.assertFalse(obj.is_completed())

        obj.current = 10
        self.assertEqual(obj.progress_percentage(), 100.0)
        self.assertTrue(obj.is_completed())

    def test_objective_completion(self):
        """Test objective completion check."""
        obj = BountyObjective(
            id="complete_test",
            description="Completion test",
            target="quest",
            current=5,
            required=5,
        )

        self.assertTrue(obj.is_completed())
        self.assertEqual(obj.progress_percentage(), 100.0)


if __name__ == "__main__":
    unittest.main()
