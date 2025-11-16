"""Tests for the meta-quest mechanics in The Living Rusted Tankard."""

import pytest
from datetime import timedelta
from unittest.mock import patch
from core.game_state import GameState


class TestMetaQuestMechanics:
    """Test the meta-quest related mechanics."""

    def test_meta_quest_unlocks_after_48h(self, meta_quest_setup):
        """Test that meta-quest unlocks after 48h without a room when asking about sleep."""
        setup = meta_quest_setup
        clock = setup["clock"]
        player = setup["player"]

        # Advance to just before 48h
        clock.advance(47.9)
        result = player.ask_about_sleep()

        assert not player.no_sleep_quest_unlocked
        assert "tired" in result.lower()

        # Advance past 48h
        clock.advance(0.2)  # Now at 48.1h
        result = player.ask_about_sleep()

        assert player.no_sleep_quest_unlocked
        assert "strange" in result.lower()

    def test_meta_quest_blocked_by_room_rental(self, meta_quest_setup):
        """Test that renting a room blocks the meta-quest permanently."""
        setup = meta_quest_setup
        clock = setup["clock"]
        player = setup["player"]
        room_manager = setup["room_manager"]

        # Rent a room before 48h
        player.gold = 20
        with patch("core.room_manager.ROOM_COST", 10):
            room_manager.rent_room(player)

        # Advance past 48h and ask about sleep
        clock.advance(50)
        result = player.ask_about_sleep()

        assert not player.no_sleep_quest_unlocked
        assert "strange" not in result.lower()
        assert "room" in result.lower()

    def test_meta_quest_persists_after_unlock(self, meta_quest_setup):
        """Test that meta-quest remains unlocked after conditions are no longer met."""
        setup = meta_quest_setup
        clock = setup["clock"]
        player = setup["player"]
        room_manager = setup["room_manager"]

        # Unlock the quest
        clock.advance(50)
        player.ask_about_sleep()

        # Rent a room after unlocking
        player.gold = 20
        with patch("core.room_manager.ROOM_COST", 10):
            room_manager.rent_room(player)

        # Quest should remain unlocked
        assert player.no_sleep_quest_unlocked

    def test_meta_quest_only_triggers_on_ask(self, meta_quest_setup):
        """Test that meta-quest only triggers when explicitly asking about sleep."""
        setup = meta_quest_setup
        clock = setup["clock"]
        player = setup["player"]

        # Advance past 48h
        clock.advance(50)

        # Perform other actions that don't ask about sleep
        player.rest()
        player.look_around()

        # Quest should still be locked
        assert not player.no_sleep_quest_unlocked

        # Now ask about sleep
        result = player.ask_about_sleep()
        assert player.no_sleep_quest_unlocked
        assert "strange" in result.lower()


class TestMetaQuestIntegration:
    """Integration tests for the meta-quest with other systems."""

    def test_meta_quest_with_save_load(self, game_state):
        """Test that meta-quest state persists across save/load."""
        # Advance time past 48h
        game_state.clock.advance(50)

        # Ask about sleep to unlock the quest
        game_state.process_command("ask about sleep")
        assert game_state.player.no_sleep_quest_unlocked

        # Save and reset game state
        saved_state = game_state.to_dict()
        new_state = GameState()
        new_state.load_from_dict(saved_state)

        # Verify quest state was preserved
        assert new_state.player.no_sleep_quest_unlocked

    def test_meta_quest_with_room_rental_after_unlock(self, game_state):
        """Test that renting a room after unlocking the quest doesn't affect it."""
        # Unlock the quest
        game_state.clock.advance(50)
        game_state.process_command("ask about sleep")

        # Rent a room
        game_state.player.gold = 20
        with patch("core.room_manager.ROOM_COST", 10):
            game_state.process_command("rent room")

        # Quest should remain unlocked
        assert game_state.player.no_sleep_quest_unlocked

        # Should be able to sleep normally
        result = game_state.process_command("sleep 8")
        assert result["hours_slept"] == 8
