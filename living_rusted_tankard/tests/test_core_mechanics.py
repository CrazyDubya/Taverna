"""Tests for core game mechanics in The Living Rusted Tankard."""

import unittest
from unittest.mock import patch, MagicMock
from datetime import timedelta

from core.game_state import GameState
from core.player import PlayerState as Player
from core.clock import GameClock
from core.room import RoomManager


class TestGoldAndRoomMechanics(unittest.TestCase):
    """Test gold transactions and room rental mechanics."""

    def setUp(self):
        """Set up test environment."""
        self.player = Player()
        self.room_manager = RoomManager()

    def test_room_rental_cost(self):
        """Test that renting a room deducts gold correctly."""
        initial_gold = self.player.gold
        room_cost = 10  # Example cost

        with patch("core.room.ROOM_COST", room_cost):
            success, _ = self.room_manager.rent_room(self.player)

        self.assertTrue(success)
        self.assertEqual(self.player.gold, initial_gold - room_cost)
        self.assertTrue(self.player.has_room)

    def test_insufficient_funds_for_room(self):
        """Test that room rental fails with insufficient funds."""
        self.player.gold = 5
        room_cost = 10

        with patch("core.room.ROOM_COST", room_cost):
            success, _ = self.room_manager.rent_room(self.player)

        self.assertFalse(success)
        self.assertEqual(self.player.gold, 5)
        self.assertFalse(self.player.has_room)

    def test_double_room_rental(self):
        """Test that renting a room twice only charges once."""
        self.player.gold = 20
        room_cost = 10

        with patch("core.room.ROOM_COST", room_cost):
            # First rental should succeed
            success1, _ = self.room_manager.rent_room(self.player)
            gold_after_first = self.player.gold

            # Second rental should fail (already has room)
            success2, _ = self.room_manager.rent_room(self.player)

        self.assertTrue(success1)
        self.assertFalse(success2)
        self.assertEqual(self.player.gold, gold_after_first)  # No additional charge


class TestGameStateIntegration(unittest.TestCase):
    """Integration tests for game state and mechanics."""

    def test_complete_game_flow(self):
        """Test a complete game flow with multiple systems interacting."""
        # Initialize game state
        game = GameState()

        # Player starts with no room
        self.assertFalse(game.player.has_room)

        # Try to sleep - should fail with correct message
        result = game.process_command("sleep 8")
        self.assertIn("you need to rent a room", result["message"].lower())

        # Rent a room
        game.player.gold = 20  # Ensure enough gold
        result = game.process_command("rent room")
        self.assertTrue(game.player.has_room)

        # Sleep should now work
        initial_time = game.clock.current_time
        result = game.process_command("sleep 8")
        self.assertGreater(game.clock.current_time, initial_time)

        # Meta-quest should be blocked
        game.clock.advance(50)  # Fast forward past 48h
        result = game.process_command("ask about sleep")
        self.assertFalse(game.player.no_sleep_quest_unlocked)


if __name__ == "__main__":
    unittest.main()
