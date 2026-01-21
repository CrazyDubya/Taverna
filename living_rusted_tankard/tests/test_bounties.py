"""
Test suite for the Bounty system.

Tests bounty loading, retrieval, and objective structure.
"""
import unittest
import tempfile
import shutil
import json
from pathlib import Path

from living_rusted_tankard.core.bounties import (
    BountyManager,
    Bounty,
    BountyObjective,
    BountyStatus,
    BountyReward,
)


class TestBountyObjective(unittest.TestCase):
    """Test the BountyObjective class."""

    def test_objective_creation(self):
        """Test creating a bounty objective."""
        obj = BountyObjective(
            id="test_obj",
            description="Test objective",
            type="kill_target",
            target_id="wolves",
            current_progress=0,
            required_progress=10,
            is_completed=False,
            is_active=True,
        )

        self.assertEqual(obj.id, "test_obj")
        self.assertEqual(obj.type, "kill_target")
        self.assertEqual(obj.target_id, "wolves")
        self.assertEqual(obj.current_progress, 0)
        self.assertEqual(obj.required_progress, 10)
        self.assertFalse(obj.is_completed)
        self.assertTrue(obj.is_active)

    def test_objective_types(self):
        """Test different objective types."""
        types = ["kill_target", "collect_item", "discover_location", "report_to_npc"]

        for obj_type in types:
            obj = BountyObjective(
                id=f"obj_{obj_type}",
                description=f"Test {obj_type}",
                type=obj_type,
                target_id="test_target",
                required_progress=1,
            )
            self.assertEqual(obj.type, obj_type)


class TestBountyReward(unittest.TestCase):
    """Test the BountyReward class."""

    def test_reward_with_gold(self):
        """Test reward with gold."""
        reward = BountyReward(gold=100)
        self.assertEqual(reward.gold, 100)

    def test_reward_with_items(self):
        """Test reward with items."""
        reward = BountyReward(
            gold=50,
            items=[{"id": "potion", "quantity": 2}],
        )
        self.assertEqual(len(reward.items), 1)
        self.assertEqual(reward.items[0]["id"], "potion")

    def test_reward_with_reputation(self):
        """Test reward with reputation."""
        reward = BountyReward(
            gold=75,
            reputation={"merchant": 10},
        )
        self.assertIn("merchant", reward.reputation)
        self.assertEqual(reward.reputation["merchant"], 10)


class TestBounty(unittest.TestCase):
    """Test the Bounty class."""

    def test_bounty_creation(self):
        """Test creating a bounty."""
        bounty = Bounty(
            id="test_bounty",
            title="Test Bounty",
            description="A test bounty",
            objectives=[],
            rewards=BountyReward(gold=100),
        )

        self.assertEqual(bounty.id, "test_bounty")
        self.assertEqual(bounty.title, "Test Bounty")
        self.assertEqual(bounty.status, BountyStatus.AVAILABLE)

    def test_bounty_with_objectives(self):
        """Test bounty with objectives."""
        objectives = [
            BountyObjective(
                id="obj1",
                description="Objective 1",
                type="kill_target",
                target_id="enemy",
                required_progress=5,
            )
        ]

        bounty = Bounty(
            id="multi_objective",
            title="Multi Objective",
            description="Test",
            objectives=objectives,
            rewards=BountyReward(gold=150),
        )

        self.assertEqual(len(bounty.objectives), 1)
        self.assertEqual(bounty.objectives[0].id, "obj1")

    def test_get_active_objective(self):
        """Test getting the active objective."""
        objectives = [
            BountyObjective(
                id="obj1",
                description="First",
                type="generic",
                required_progress=1,
                is_active=True,
            ),
            BountyObjective(
                id="obj2",
                description="Second",
                type="generic",
                required_progress=1,
                is_active=False,
            ),
        ]

        bounty = Bounty(
            id="test",
            title="Test",
            description="Test",
            objectives=objectives,
            rewards=BountyReward(gold=50),
        )

        active = bounty.get_active_objective()
        self.assertIsNotNone(active)
        self.assertEqual(active.id, "obj1")

    def test_are_all_objectives_completed(self):
        """Test checking if all objectives are completed."""
        objectives = [
            BountyObjective(
                id="obj1",
                description="First",
                type="generic",
                required_progress=1,
                current_progress=1,
                is_completed=True,
            ),
            BountyObjective(
                id="obj2",
                description="Second",
                type="generic",
                required_progress=1,
                current_progress=1,
                is_completed=True,
            ),
        ]

        bounty = Bounty(
            id="test",
            title="Test",
            description="Test",
            objectives=objectives,
            rewards=BountyReward(gold=100),
        )

        self.assertTrue(bounty.are_all_objectives_completed())


class TestBountyManager(unittest.TestCase):
    """Test the BountyManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.create_test_bounties_file()
        self.bounty_manager = BountyManager(data_dir=self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_bounties_file(self):
        """Create a test bounties.json file."""
        bounties_data = {
            "bounties": [
                {
                    "id": "test_bounty_001",
                    "title": "Test Bounty",
                    "description": "A test bounty",
                    "objectives": [
                        {
                            "id": "obj1",
                            "description": "Test objective",
                            "type": "kill_target",
                            "target_id": "wolf",
                            "required_progress": 5,
                        }
                    ],
                    "rewards": {"gold": 100},
                }
            ]
        }

        bounties_file = Path(self.test_dir) / "bounties.json"
        with open(bounties_file, "w") as f:
            json.dump(bounties_data, f)

    def test_bounty_manager_initialization(self):
        """Test that BountyManager initializes correctly."""
        self.assertIsNotNone(self.bounty_manager)

    def test_get_bounty(self):
        """Test retrieving a bounty by ID."""
        bounty = self.bounty_manager.get_bounty("test_bounty_001")
        self.assertIsNotNone(bounty)
        self.assertEqual(bounty.id, "test_bounty_001")
        self.assertEqual(bounty.title, "Test Bounty")

    def test_get_nonexistent_bounty(self):
        """Test retrieving a bounty that doesn't exist."""
        bounty = self.bounty_manager.get_bounty("nonexistent")
        self.assertIsNone(bounty)

    def test_bounty_loaded_objectives(self):
        """Test that bounty objectives are loaded correctly."""
        bounty = self.bounty_manager.get_bounty("test_bounty_001")
        self.assertIsNotNone(bounty)
        self.assertEqual(len(bounty.objectives), 1)
        self.assertEqual(bounty.objectives[0].type, "kill_target")


class TestBountyStatus(unittest.TestCase):
    """Test bounty status enum."""

    def test_status_values(self):
        """Test that all status values exist."""
        statuses = [
            BountyStatus.AVAILABLE,
            BountyStatus.ACCEPTED,
            BountyStatus.COMPLETED,
            BountyStatus.FAILED,
        ]

        for status in statuses:
            self.assertIsNotNone(status)
            self.assertIsInstance(status, BountyStatus)


if __name__ == "__main__":
    unittest.main()
