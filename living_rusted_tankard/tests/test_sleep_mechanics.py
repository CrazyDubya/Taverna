"""Tests for sleep and time mechanics in The Living Rusted Tankard."""

import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock


class TestSleepMechanics:
    """Test cases for sleep and time advancement."""

    def test_sleep_advances_time(self, sleep_setup):
        """Test that sleeping advances time and reduces tiredness."""
        setup = sleep_setup
        player = setup['player']
        clock = setup['clock']
        room_manager = setup['room_manager']

        # Rent a room first
        player.gold = 20
        with patch('core.room_manager.ROOM_COST', 10):
            room_manager.rent_room(player)

        # Make player tired
        player.tiredness = 8
        initial_time = clock.current_time

        # Sleep for 8 hours
        hours_slept = player.sleep(8)

        assert hours_slept == 8
        assert clock.current_time == initial_time + timedelta(hours=8)
        assert player.tiredness == 0  # 8 - 8 = 0

    def test_sleep_without_room(self, sleep_setup):
        """Test that sleeping without a room is not possible."""
        setup = sleep_setup
        player = setup['player']
        clock = setup['clock']

        initial_time = clock.current_time
        initial_tiredness = player.tiredness = 5

        # Try to sleep without a room
        hours_slept = player.sleep(8)

        assert hours_slept == 0  # No sleep occurred
        assert clock.current_time == initial_time  # Time didn't advance
        assert player.tiredness == initial_tiredness  # Tiredness unchanged

    def test_sleep_reduces_tiredness(self, sleep_setup):
        """Test that sleeping reduces tiredness by the correct amount."""
        setup = sleep_setup
        player = setup['player']
        room_manager = setup['room_manager']

        # Rent a room
        player.gold = 20
        with patch('core.room_manager.ROOM_COST', 10):
            room_manager.rent_room(player)

        # Set high tiredness
        player.tiredness = 10

        # Sleep for 4 hours (should reduce tiredness by 4)
        hours_slept = player.sleep(4)
        assert hours_slept == 4
        assert player.tiredness == 6  # 10 - 4 = 6

        # Sleep again (should cap at 0)
        hours_slept = player.sleep(10)
        assert hours_slept == 6  # Only slept 6 hours to reach 0 tiredness
        assert player.tiredness == 0

    def test_sleep_command_integration(self, game_state):
        """Test the sleep command through the game state."""
        # Rent a room first
        game_state.player.gold = 20
        with patch('core.room_manager.ROOM_COST', 10):
            game_state.process_command("rent room")

        # Set up tiredness
        game_state.player.tiredness = 5
        initial_time = game_state.clock.current_time

        # Execute sleep command
        result = game_state.process_command("sleep 8")

        # Verify results
        assert result["hours_slept"] == 8
        assert game_state.player.tiredness == 0
        assert game_state.clock.current_time == initial_time + timedelta(hours=8)
        assert "slept for 8 hours" in result["message"].lower()


class TestTimeMechanics:
    """Test cases for time-based mechanics."""

    def test_time_advancement(self, game_clock):
        """Test that time advances correctly."""
        initial_time = game_clock.current_time

        # Advance by 1.5 hours
        game_clock.advance(1.5)

        assert game_clock.current_time == initial_time + timedelta(hours=1.5)

    def test_day_night_cycle(self, game_clock):
        """Test the day/night cycle calculations."""
        # Start at 6:00 AM
        game_clock.current_time = game_clock.current_time.replace(hour=6, minute=0)

        assert game_clock.is_daytime() is True

        # Advance to 8:00 PM - should be night
        game_clock.advance(14)  # 6:00 AM + 14 hours = 8:00 PM
        assert game_clock.is_daytime() is False

        # Advance to 6:00 AM next day - should be day again
        game_clock.advance(10)  # 8:00 PM + 10 hours = 6:00 AM
        assert game_clock.is_daytime() is True

    def test_time_of_day_events(self, game_state):
        """Test that time-based events fire correctly."""
        # Set up a mock event handler
        mock_handler = MagicMock()

        # Schedule an event for 2 hours from now
        event_time = game_state.clock.current_time + timedelta(hours=2)
        game_state.clock.schedule_event(event_time, mock_handler)

        # Advance time by 1 hour - event should not fire yet
        game_state.clock.advance(1)
        mock_handler.assert_not_called()

        # Advance past the event time
        game_state.clock.advance(1.1)  # Now at 2.1 hours
        mock_handler.assert_called_once()


class TestTirednessMechanics:
    """Test cases for player tiredness mechanics."""

    def test_tiredness_increases_over_time(self, game_state):
        """Test that tiredness increases as time passes."""
        initial_tiredness = game_state.player.tiredness

        # Advance time by 4 hours
        game_state.clock.advance(4)
        game_state.update_tiredness()

        # Tiredness should have increased
        assert game_state.player.tiredness > initial_tiredness

    def test_rest_reduces_tiredness(self, game_state):
        """Test that resting reduces tiredness."""
        # Make player tired
        game_state.player.tiredness = 7

        # Rest for a bit
        game_state.process_command("rest")

        # Tiredness should be reduced
        assert game_state.player.tiredness < 7

    def test_rest_requires_bench(self, game_state):
        """Test that resting requires sitting on a bench."""
        # Make player tired
        game_state.player.tiredness = 7

        # Try to rest without sitting
        result = game_state.process_command("rest")
        assert "sit on a bench" in result["message"].lower()
        assert game_state.player.tiredness == 7  # No change

        # Sit on a bench
        game_state.process_command("sit on bench")

        # Now rest should work
        result = game_state.process_command("rest")
        assert game_state.player.tiredness < 7  # Reduced
