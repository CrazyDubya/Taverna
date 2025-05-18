"""Tests for the PlayerState class."""
import pytest

def test_player_initial_state(player_state):
    """Test that a new player has the expected initial state."""
    assert player_state.gold == 40
    assert player_state.has_room is False
    assert player_state.tiredness == 0.0
    assert player_state.rest_immune is False
    assert player_state.no_sleep_quest_unlocked is False
    assert player_state.inventory == {}
    assert player_state.flags == {}

def test_gold_management(player_state):
    """Test adding and spending gold."""
    # Test adding gold
    player_state.add_gold(10)
    assert player_state.gold == 50
    
    # Test spending gold
    assert player_state.spend_gold(20) is True
    assert player_state.gold == 30
    
    # Test insufficient funds
    assert player_state.spend_gold(40) is False
    assert player_state.gold == 30  # Should not change

def test_tiredness_mechanics(player_state):
    """Test tiredness increases over time and can be reduced by resting."""
    # Tiredness increases with time
    player_state.update_tiredness(10)  # 10 hours
    assert player_state.tiredness == 1.0  # 10 * 0.1
    
    # Resting without a room doesn't help
    assert player_state.rest(8) is False
    assert player_state.tiredness == 1.0
    
    # Get a room and rest
    player_state.has_room = True
    assert player_state.rest(8) is True
    assert player_state.tiredness == pytest.approx(0.6)  # 1.0 - (8 * 0.2)

def test_no_sleep_quest(player_state):
    """Test the no-sleep meta quest conditions."""
    # Initial state
    assert player_state.no_sleep_quest_unlocked is False
    
    # Not enough time passed
    assert player_state.check_no_sleep_quest_condition(24.0, "inquire_sleep") is False
    assert player_state.no_sleep_quest_unlocked is False
    
    # Enough time but wrong action
    assert player_state.check_no_sleep_quest_condition(48.0, "look_around") is False
    assert player_state.no_sleep_quest_unlocked is False
    
    # All conditions met
    assert player_state.check_no_sleep_quest_condition(48.0, "inquire_sleep") is True
    assert player_state.no_sleep_quest_unlocked is True
    assert player_state.rest_immune is True
    
    # Can't unlock twice
    assert player_state.check_no_sleep_quest_condition(72.0, "inquire_sleep") is False
