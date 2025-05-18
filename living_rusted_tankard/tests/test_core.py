import pytest
from datetime import timedelta
import time

from core.clock import GameClock, GameTime
from core.event import EventQueue, GameEvent
from models.player import PlayerState, Inventory

def test_game_time_properties():
    """Test GameTime properties and formatting."""
    t = GameTime(25.5)  # 1 day, 1 hour, 30 minutes
    
    assert t.hour_of_day == 1.5
    assert t.day == 2  # Day 2 (after 25.5 hours)
    assert "Day 2, 01:30" in t.format_time()

def test_event_queue():
    """Test event scheduling and triggering."""
    events_fired = []
    
    def handler1():
        events_fired.append("event1")
    
    def handler2():
        events_fired.append("event2")
    
    queue = EventQueue()
    
    # Schedule events out of order
    queue.schedule_event(10.0, handler2, "event2")
    queue.schedule_event(5.0, handler1, "event1")
    
    # Process events up to time 7.0 - only event1 should fire
    queue.process_events(7.0)
    assert events_fired == ["event1"]
    
    # Process remaining events
    queue.process_events(15.0)
    assert events_fired == ["event1", "event2"]

def test_player_inventory():
    """Test inventory management."""
    inv = Inventory()
    
    # Test adding items
    inv.add_item("gold coin", 5)
    inv.add_item("gold coin", 3)
    inv.add_item("key", 1)
    
    assert inv.items == {"gold coin": 8, "key": 1}
    assert inv.has_item("gold coin", 5)
    assert not inv.has_item("key", 2)
    
    # Test removing items
    assert inv.remove_item("gold coin", 3)
    assert inv.items == {"gold coin": 5, "key": 1}
    assert not inv.remove_item("key", 2)  # Not enough keys
    assert inv.items == {"gold coin": 5, "key": 1}

def test_player_state():
    """Test player state management."""
    player = PlayerState()
    
    # Test gold management
    assert player.add_gold(10)
    assert player.gold == 50  # Starts with 40 + 10
    assert not player.add_gold(-60)  # Not enough gold
    assert player.gold == 50  # Unchanged
    
    # Test tiredness
    player.tiredness = 50
    player.update_tiredness(10, None)  # Pass None for clock since we're not testing time-based effects
    assert player.tiredness > 50  # Tiredness increases when awake
    
    # Test serialization
    data = player.to_dict()
    new_player = PlayerState.from_dict(data)
    assert new_player.gold == player.gold
    assert new_player.tiredness == player.tiredness

def test_game_clock():
    """Test the game clock and event scheduling."""
    clock = GameClock()
    events_fired = []
    
    def test_event():
        events_fired.append("test")
    
    # Schedule an event in 2 hours
    clock.schedule_event(2.0, test_event, "test_event")
    
    # Advance time - event shouldn't fire yet
    clock.advance_time(1.0)
    assert not events_fired
    
    # Advance past the event time
    clock.advance_time(1.5)
    assert events_fired == ["test"]

if __name__ == "__main__":
    pytest.main(["-v"])
