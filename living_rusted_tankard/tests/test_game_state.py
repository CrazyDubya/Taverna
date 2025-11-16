"""Tests for the GameState class and time advancement."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from core.game_state import GameState, GameEvent
from core.clock import GameClock, GameTime
from core.player import PlayerState


class TestGameState:
    """Test suite for the GameState class."""

    @pytest.fixture
    def game_state(self):
        """Create a fresh GameState instance for each test."""
        return GameState()

    def test_initialization(self, game_state):
        """Test that GameState initializes with correct default values."""
        assert isinstance(game_state.clock, GameClock)
        assert isinstance(game_state.player, PlayerState)
        assert len(game_state.events) > 0  # Should have welcome message
        assert not game_state.running

    def test_time_advancement(self, game_state):
        """Test that time advances correctly in the game state."""
        initial_time = game_state.clock.time.hours

        # Update the game state (time will advance based on real time)
        game_state.update()

        # Time should have advanced (not by a specific amount since it's real-time based)
        assert game_state.clock.time.hours > initial_time

    def test_event_handling(self, game_state):
        """Test that game events are properly handled and stored."""
        initial_event_count = len(game_state.events)

        # Add a test event
        test_msg = "Test event"
        game_state._add_event(test_msg, "test")

        assert len(game_state.events) == initial_event_count + 1
        assert game_state.events[-1].message == test_msg
        assert game_state.events[-1].event_type == "test"

    def test_event_limit(self, game_state):
        """Test that the event list doesn't exceed the maximum limit."""
        # Add more events than the limit
        for i in range(150):
            game_state._add_event(f"Event {i}", "test")

        # Should only keep the last 100 events
        assert len(game_state.events) == 100
        assert (
            game_state.events[0].message == "Event 50"
        )  # First 50 should be discarded

    @patch("core.clock.GameClock.update")
    def test_update_calls_advance_time(self, mock_update, game_state):
        """Test that update() calls the clock's update method."""
        game_state.update()
        mock_update.assert_called_once()

    def test_initial_events(self, game_state):
        """Test that initial game events are created on startup."""
        # Should have at least the welcome message
        assert any(
            "Welcome to The Rusted Tankard" in e.message for e in game_state.events
        )


class TestGameTimeIntegration:
    """Integration tests for game time and state management."""

    def test_game_state_updates_over_time(self):
        """Test that game state updates correctly over multiple time steps."""
        game = GameState()

        # Simulate multiple update steps
        initial_clock_time = game.clock.time.hours

        for _ in range(3):
            game.update()

        # Time should have advanced (not by a specific amount since it's real-time based)
        assert game.clock.time.hours > initial_clock_time

    def test_time_based_events(self):
        """Test that time-based events are triggered correctly."""
        game = GameState()
        events_triggered = []

        # Schedule an event for 5 hours from now

        def test_handler():
            events_triggered.append("test_event")

        game.clock.schedule_event(5.0, test_handler, "test_event")

        # Manually advance time in the clock
        game.clock.advance(10.0)  # Past the event time
        game.update()  # Process events
        assert events_triggered == ["test_event"]


class TestPlayerStateIntegration:
    """Integration tests for player state within the game."""

    def test_player_state_persistence(self, game_state):
        """Test that player state persists through game updates."""
        # Give player some gold
        initial_gold = 100
        game_state.player.gold = initial_gold

        # Update game state
        game_state.update()

        # Player's gold should remain the same
        assert game_state.player.gold == initial_gold

    def test_player_inventory_management(self, game_state):
        """Test that player inventory works with game state."""
        # Add an item to inventory
        test_item = "test_item"
        game_state.player.inventory.add_item(test_item, 1)

        # Update game state
        game_state.update()

        # Item should still be there
        assert game_state.player.inventory.has_item(test_item)
