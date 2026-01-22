"""
Test suite for the Reputation Network system.

Tests reputation tracking, relationship management, and reputation effects.
"""
import unittest

from living_rusted_tankard.core.narrative.reputation_network import (
    ReputationNetwork,
    ReputationLevel,
    ReputationModifier,
)


class TestReputationNetwork(unittest.TestCase):
    """Test the ReputationNetwork class."""

    def setUp(self):
        """Set up test fixtures."""
        self.network = ReputationNetwork()

    def test_network_initialization(self):
        """Test that ReputationNetwork initializes correctly."""
        self.assertIsNotNone(self.network)

    def test_get_reputation(self):
        """Test getting reputation for an entity."""
        entity_id = "npc_merchant"
        player_id = "player_001"

        reputation = self.network.get_reputation(player_id, entity_id)
        self.assertIsNotNone(reputation)
        self.assertIsInstance(reputation, (int, float))

    def test_modify_reputation(self):
        """Test modifying reputation."""
        player_id = "player_test"
        entity_id = "npc_guard"
        
        initial = self.network.get_reputation(player_id, entity_id)
        
        self.network.modify_reputation(player_id, entity_id, amount=10)
        
        after = self.network.get_reputation(player_id, entity_id)
        self.assertGreater(after, initial)

    def test_reputation_boundaries(self):
        """Test that reputation respects min/max boundaries."""
        player_id = "player_boundary"
        entity_id = "npc_test"

        # Try to set very high reputation
        self.network.modify_reputation(player_id, entity_id, amount=10000)
        rep_high = self.network.get_reputation(player_id, entity_id)
        
        # Try to set very low reputation
        self.network.modify_reputation(player_id, entity_id, amount=-20000)
        rep_low = self.network.get_reputation(player_id, entity_id)

        # Should be within reasonable bounds
        self.assertLessEqual(rep_high, 100)
        self.assertGreaterEqual(rep_low, -100)

    def test_get_reputation_level(self):
        """Test getting reputation level (friendly, neutral, hostile, etc.)."""
        player_id = "player_level"
        entity_id = "npc_level"

        # Set high reputation
        self.network.modify_reputation(player_id, entity_id, amount=50)
        
        level = self.network.get_reputation_level(player_id, entity_id)
        self.assertIsNotNone(level)

    def test_get_all_reputations(self):
        """Test getting all reputations for a player."""
        player_id = "player_all"
        
        # Set reputation with multiple entities
        self.network.modify_reputation(player_id, "entity_1", 10)
        self.network.modify_reputation(player_id, "entity_2", -10)
        self.network.modify_reputation(player_id, "entity_3", 25)

        all_reps = self.network.get_all_reputations(player_id)
        self.assertIsInstance(all_reps, dict)
        self.assertGreaterEqual(len(all_reps), 3)

    def test_reputation_decay(self):
        """Test reputation decay over time."""
        player_id = "player_decay"
        entity_id = "npc_decay"

        # Set initial reputation
        self.network.modify_reputation(player_id, entity_id, 50)
        initial = self.network.get_reputation(player_id, entity_id)

        # Apply decay
        self.network.apply_reputation_decay(player_id, entity_id, decay_factor=0.1)
        
        after_decay = self.network.get_reputation(player_id, entity_id)
        self.assertLessEqual(after_decay, initial)


class TestReputationLevel(unittest.TestCase):
    """Test reputation level enumeration."""

    def test_reputation_levels_exist(self):
        """Test that reputation levels are defined."""
        levels = [
            ReputationLevel.HATED,
            ReputationLevel.HOSTILE,
            ReputationLevel.UNFRIENDLY,
            ReputationLevel.NEUTRAL,
            ReputationLevel.FRIENDLY,
            ReputationLevel.HONORED,
            ReputationLevel.EXALTED,
        ]

        for level in levels:
            self.assertIsNotNone(level)

    def test_reputation_level_ordering(self):
        """Test that reputation levels are properly ordered."""
        self.assertLess(
            ReputationLevel.HOSTILE.value,
            ReputationLevel.NEUTRAL.value
        )
        self.assertLess(
            ReputationLevel.NEUTRAL.value,
            ReputationLevel.FRIENDLY.value
        )


class TestReputationModifier(unittest.TestCase):
    """Test reputation modifier system."""

    def test_modifier_creation(self):
        """Test creating a reputation modifier."""
        modifier = ReputationModifier(
            source="quest_completion",
            amount=25,
            reason="Helped save the village",
        )

        self.assertEqual(modifier.source, "quest_completion")
        self.assertEqual(modifier.amount, 25)

    def test_positive_modifier(self):
        """Test positive reputation modifier."""
        modifier = ReputationModifier(
            source="good_deed",
            amount=10,
        )

        self.assertGreater(modifier.amount, 0)

    def test_negative_modifier(self):
        """Test negative reputation modifier."""
        modifier = ReputationModifier(
            source="bad_action",
            amount=-15,
        )

        self.assertLess(modifier.amount, 0)


class TestReputationEffects(unittest.TestCase):
    """Test reputation effects on gameplay."""

    def setUp(self):
        """Set up test fixtures."""
        self.network = ReputationNetwork()

    def test_check_reputation_threshold(self):
        """Test checking if reputation meets a threshold."""
        player_id = "player_threshold"
        entity_id = "npc_threshold"

        self.network.modify_reputation(player_id, entity_id, 30)

        # Check if reputation is above threshold
        meets_threshold = self.network.check_reputation_threshold(
            player_id, entity_id, threshold=20
        )
        
        self.assertTrue(meets_threshold)

    def test_get_reputation_multiplier(self):
        """Test getting reputation-based multipliers."""
        player_id = "player_multiplier"
        merchant_id = "npc_merchant"

        # High reputation should give better prices
        self.network.modify_reputation(player_id, merchant_id, 50)

        multiplier = self.network.get_price_multiplier(player_id, merchant_id)
        self.assertIsInstance(multiplier, float)
        self.assertLessEqual(multiplier, 1.0)  # Discount for high reputation


if __name__ == "__main__":
    unittest.main()
