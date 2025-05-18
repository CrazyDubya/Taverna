"""Tests for NPC integration with game systems."""
import pytest
from models.player import PlayerState
from models.npc_state import NPCSchedule
from core.clock import GameClock, GameTime


def test_npc_scheduling():
    """Test that NPCs appear and disappear according to their schedules."""
    # Setup
    player = PlayerState()
    clock = GameClock()
    
    # Add an NPC that should be present from 12:00 to 18:00 on weekdays
    schedule = NPCSchedule(
        start_hour=12,
        end_hour=18,
        days={0, 1, 2, 3, 4},  # Weekdays
        probability=1.0
    )
    player.npc_state.add_npc_schedule("test_npc", schedule)
    
    # Test at 11:00 on Monday - NPC should not be present
    clock.time = GameTime(hours=11 + 0*24)  # Monday 11:00
    player.npc_state.update_npc_presence(
        current_hour=11,
        current_weekday=0  # Monday
    )
    assert "test_npc" not in player.npc_state.get_available_npcs()
    
    # Test at 15:00 on Monday - NPC should be present
    clock.time = GameTime(hours=15 + 0*24)  # Monday 15:00
    player.npc_state.update_npc_presence(
        current_hour=15,
        current_weekday=0  # Monday
    )
    assert "test_npc" in player.npc_state.get_available_npcs()
    
    # Test at 19:00 on Monday - NPC should have left
    clock.time = GameTime(hours=19 + 0*24)  # Monday 19:00
    player.npc_state.update_npc_presence(
        current_hour=19,
        current_weekday=0  # Monday
    )
    assert "test_npc" not in player.npc_state.get_available_npcs()
    
    # Test at 15:00 on Saturday - NPC should not be present (weekend)
    clock.time = GameTime(hours=15 + 5*24)  # Saturday 15:00
    player.npc_state.update_npc_presence(
        current_hour=15,
        current_weekday=5  # Saturday
    )
    assert "test_npc" not in player.npc_state.get_available_npcs()


def test_npc_relationships():
    """Test NPC relationship tracking."""
    player = PlayerState()
    
    # Initial relationship should be 0
    assert player.npc_state.get_relationship("test_npc") == 0
    
    # Improve relationship
    player.npc_state.modify_relationship("test_npc", 10)
    assert player.npc_state.get_relationship("test_npc") == 10
    
    # Worsen relationship
    player.npc_state.modify_relationship("test_npc", -5)
    assert player.npc_state.get_relationship("test_npc") == 5
    
    # Test bounds (should be capped at -100 to 100)
    player.npc_state.modify_relationship("test_npc", -200)
    assert player.npc_state.get_relationship("test_npc") == -100  # Capped at -100
    
    player.npc_state.modify_relationship("test_npc", 300)
    assert player.npc_state.get_relationship("test_npc") == 100  # Capped at 100


def test_conversation_state():
    """Test NPC conversation state management."""
    player = PlayerState()
    
    # Start a conversation
    player.npc_state.start_conversation("test_npc", "greeting")
    assert "test_npc" in player.npc_state.active_conversations
    assert player.npc_state.active_conversations["test_npc"] == "greeting"
    
    # Update conversation state
    player.npc_state.start_conversation("test_npc", "discussion")
    assert player.npc_state.active_conversations["test_npc"] == "discussion"
    
    # End conversation
    player.npc_state.end_conversation("test_npc")
    assert "test_npc" not in player.npc_state.active_conversations
