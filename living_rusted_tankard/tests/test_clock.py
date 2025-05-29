"""Test clock and time management system."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from tests.utils.assertion_helpers import assert_timestamp_recent

from core.clock import GameClock, GameTime, ScheduledEvent


class TestGameTime:
    """Test GameTime data structure."""
    
    def test_game_time_creation(self):
        """Test creating GameTime objects."""
        game_time = GameTime(
            hour=14,
            day=5,
            month=3,
            year=1,
            minute=30
        )
        
        assert game_time.hour == 14
        assert game_time.day == 5
        assert game_time.month == 3
        assert game_time.year == 1
        assert game_time.minute == 30
    
    def test_game_time_validation(self):
        """Test GameTime validates values correctly."""
        # Valid time
        valid_time = GameTime(hour=23, day=30, month=12, year=5)
        assert valid_time.hour == 23
        
        # Test boundary values
        boundary_time = GameTime(hour=0, day=1, month=1, year=1)
        assert boundary_time.hour == 0
        assert boundary_time.day == 1
    
    def test_game_time_total_hours(self):
        """Test calculating total hours from game start."""
        game_time = GameTime(hour=10, day=3, month=2, year=1)
        
        # Calculate expected total hours
        # Year 1, Month 2 (1 full month = 30 days), Day 3 (2 full days), Hour 10
        expected_hours = (0 * 12 * 30 * 24) + (1 * 30 * 24) + (2 * 24) + 10
        
        assert game_time.total_hours() == expected_hours
    
    def test_game_time_equality(self):
        """Test GameTime equality comparison."""
        time1 = GameTime(hour=10, day=5, month=3, year=1)
        time2 = GameTime(hour=10, day=5, month=3, year=1)
        time3 = GameTime(hour=11, day=5, month=3, year=1)
        
        assert time1 == time2
        assert time1 != time3
    
    def test_game_time_from_hours(self):
        """Test creating GameTime from total hours."""
        total_hours = 24 * 32 + 15  # 32 days and 15 hours
        game_time = GameTime.from_total_hours(total_hours)
        
        assert game_time.hour == 15
        assert game_time.day == 3  # 32 days = 1 month + 2 days
        assert game_time.month == 2


class TestScheduledEvent:
    """Test scheduled event functionality."""
    
    def test_scheduled_event_creation(self):
        """Test creating scheduled events."""
        callback = Mock()
        event = ScheduledEvent(
            trigger_time=100,
            callback=callback,
            event_data={"type": "npc_arrival"},
            recurring=False
        )
        
        assert event.trigger_time == 100
        assert event.callback == callback
        assert event.event_data["type"] == "npc_arrival"
        assert event.recurring is False
        assert event.is_active is True
    
    def test_scheduled_event_execution(self):
        """Test executing scheduled events."""
        callback = Mock()
        event_data = {"npc_id": "merchant", "location": "tavern"}
        
        event = ScheduledEvent(
            trigger_time=50,
            callback=callback,
            event_data=event_data,
            recurring=False
        )
        
        # Execute the event
        event.execute()
        
        callback.assert_called_once_with(event_data)
        assert event.is_active is False  # Should be deactivated after execution
    
    def test_recurring_scheduled_event(self):
        """Test recurring scheduled events."""
        callback = Mock()
        event = ScheduledEvent(
            trigger_time=24,  # Every 24 hours
            callback=callback,
            event_data={"type": "daily_reset"},
            recurring=True,
            interval=24
        )
        
        # Execute the event
        original_trigger_time = event.trigger_time
        event.execute()
        
        callback.assert_called_once()
        assert event.is_active is True  # Should remain active
        assert event.trigger_time == original_trigger_time + 24  # Should reschedule
    
    def test_scheduled_event_conditions(self):
        """Test scheduled events with conditions."""
        callback = Mock()
        condition = Mock(return_value=True)
        
        event = ScheduledEvent(
            trigger_time=10,
            callback=callback,
            event_data={},
            condition=condition
        )
        
        # Execute when condition is true
        event.execute()
        condition.assert_called_once()
        callback.assert_called_once()
        
        # Reset mocks
        callback.reset_mock()
        condition.reset_mock()
        condition.return_value = False
        
        # Execute when condition is false
        event.is_active = True  # Reactivate for test
        event.execute()
        condition.assert_called_once()
        callback.assert_not_called()  # Should not execute


class TestGameClock:
    """Test GameClock functionality."""
    
    def test_game_clock_initialization(self):
        """Test GameClock initializes correctly."""
        clock = GameClock()
        
        assert clock.current_time.hour == 12  # Default starting time
        assert clock.current_time.day == 1
        assert clock.current_time.month == 1
        assert clock.current_time.year == 1
        assert clock.time_scale == 1.0  # Default time scale
        assert len(clock.scheduled_events) == 0
    
    def test_game_clock_custom_initialization(self):
        """Test GameClock with custom parameters."""
        start_time = GameTime(hour=8, day=15, month=6, year=2)
        clock = GameClock(
            starting_time=start_time,
            time_scale=2.0,
            minutes_per_turn=30
        )
        
        assert clock.current_time == start_time
        assert clock.time_scale == 2.0
        assert clock.minutes_per_turn == 30
    
    def test_advance_time(self):
        """Test advancing game time."""
        clock = GameClock()
        initial_time = clock.current_time.total_hours()
        
        # Advance by 3 hours
        result = clock.advance_time(hours=3)
        
        assert result.hours_advanced == 3
        assert clock.current_time.total_hours() == initial_time + 3
        assert result.events_triggered == 0  # No events scheduled
    
    def test_advance_time_with_minutes(self):
        """Test advancing time with minutes."""
        clock = GameClock()
        initial_hour = clock.current_time.hour
        initial_minute = clock.current_time.minute
        
        # Advance by 90 minutes (1.5 hours)
        result = clock.advance_time(minutes=90)
        
        assert result.minutes_advanced == 90
        expected_hour = (initial_hour + 1) % 24
        expected_minute = (initial_minute + 30) % 60
        
        assert clock.current_time.hour == expected_hour
        assert clock.current_time.minute == expected_minute
    
    def test_advance_time_day_rollover(self):
        """Test time advancement rolls over days correctly."""
        # Start at 23:00
        start_time = GameTime(hour=23, day=5, month=3, year=1)
        clock = GameClock(starting_time=start_time)
        
        # Advance by 2 hours (should roll to next day)
        result = clock.advance_time(hours=2)
        
        assert clock.current_time.hour == 1
        assert clock.current_time.day == 6
        assert result.day_changed is True
    
    def test_advance_time_month_rollover(self):
        """Test time advancement rolls over months correctly."""
        # Start at day 30 (last day of month)
        start_time = GameTime(hour=12, day=30, month=5, year=1)
        clock = GameClock(starting_time=start_time)
        
        # Advance by 24 hours (should roll to next month)
        result = clock.advance_time(hours=24)
        
        assert clock.current_time.day == 1
        assert clock.current_time.month == 6
        assert result.month_changed is True
    
    def test_advance_time_year_rollover(self):
        """Test time advancement rolls over years correctly."""
        # Start at last month of year
        start_time = GameTime(hour=12, day=30, month=12, year=1)
        clock = GameClock(starting_time=start_time)
        
        # Advance by 24 hours (should roll to next year)
        result = clock.advance_time(hours=24)
        
        assert clock.current_time.day == 1
        assert clock.current_time.month == 1
        assert clock.current_time.year == 2
        assert result.year_changed is True
    
    def test_schedule_event(self):
        """Test scheduling events."""
        clock = GameClock()
        callback = Mock()
        
        # Schedule event for 5 hours from now
        event_id = clock.schedule_event(
            hours_from_now=5,
            callback=callback,
            event_data={"type": "test_event"}
        )
        
        assert event_id is not None
        assert len(clock.scheduled_events) == 1
        
        event = clock.scheduled_events[0]
        expected_trigger_time = clock.current_time.total_hours() + 5
        assert event.trigger_time == expected_trigger_time
    
    def test_schedule_recurring_event(self):
        """Test scheduling recurring events."""
        clock = GameClock()
        callback = Mock()
        
        # Schedule daily recurring event
        event_id = clock.schedule_recurring_event(
            interval_hours=24,
            callback=callback,
            event_data={"type": "daily_reset"}
        )
        
        assert event_id is not None
        event = clock.get_event(event_id)
        assert event.recurring is True
        assert event.interval == 24
    
    def test_event_triggering(self):
        """Test events are triggered when time advances."""
        clock = GameClock()
        callback = Mock()
        
        # Schedule event for 2 hours from now
        clock.schedule_event(
            hours_from_now=2,
            callback=callback,
            event_data={"message": "Event triggered"}
        )
        
        # Advance time by 2 hours
        result = clock.advance_time(hours=2)
        
        # Event should be triggered
        assert result.events_triggered == 1
        callback.assert_called_once_with({"message": "Event triggered"})
    
    def test_multiple_events_triggering(self):
        """Test multiple events trigger correctly."""
        clock = GameClock()
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        # Schedule events at different times
        clock.schedule_event(hours_from_now=1, callback=callback1, event_data={"id": 1})
        clock.schedule_event(hours_from_now=2, callback=callback2, event_data={"id": 2})
        clock.schedule_event(hours_from_now=3, callback=callback3, event_data={"id": 3})
        
        # Advance time by 2.5 hours
        result = clock.advance_time(hours=2.5)
        
        # First two events should trigger
        assert result.events_triggered == 2
        callback1.assert_called_once_with({"id": 1})
        callback2.assert_called_once_with({"id": 2})
        callback3.assert_not_called()
    
    def test_event_cancellation(self):
        """Test cancelling scheduled events."""
        clock = GameClock()
        callback = Mock()
        
        # Schedule and then cancel event
        event_id = clock.schedule_event(
            hours_from_now=5,
            callback=callback,
            event_data={}
        )
        
        success = clock.cancel_event(event_id)
        assert success is True
        
        # Advance past event time
        clock.advance_time(hours=6)
        
        # Event should not trigger
        callback.assert_not_called()
    
    def test_time_scale_effect(self):
        """Test time scale affects time advancement."""
        # Create clock with 2x time scale
        clock = GameClock(time_scale=2.0)
        initial_time = clock.current_time.total_hours()
        
        # Advance by 1 real hour (should be 2 game hours)
        result = clock.advance_time(hours=1)
        
        assert clock.current_time.total_hours() == initial_time + 2
        assert result.hours_advanced == 2  # Scaled time
    
    def test_clock_serialization(self):
        """Test clock can be serialized and deserialized."""
        clock = GameClock()
        callback = Mock()
        
        # Schedule an event
        clock.schedule_event(hours_from_now=5, callback=callback, event_data={})
        
        # Advance time
        clock.advance_time(hours=2)
        
        # Serialize
        serialized = clock.model_dump(mode='json')
        
        assert 'current_time' in serialized
        assert 'time_scale' in serialized
        assert 'minutes_per_turn' in serialized
        
        # Note: Events with callbacks can't be easily serialized
        # In real implementation, events would need special handling


class TestClockIntegration:
    """Test clock integration with game systems."""
    
    def test_clock_with_event_bus(self):
        """Test clock integration with event bus."""
        from core.event_bus import EventBus, Event, EventType
        
        clock = GameClock()
        event_bus = EventBus()
        events_received = []
        
        def time_handler(event):
            events_received.append(event.data)
        
        event_bus.subscribe(EventType.TIME_ADVANCED, time_handler)
        
        # Configure clock to publish events
        def publish_time_event(data):
            event = Event(event_type=EventType.TIME_ADVANCED, data=data)
            event_bus.dispatch(event)
        
        clock.on_time_advanced = publish_time_event
        
        # Advance time
        clock.advance_time(hours=3)
        
        # Event should be published
        assert len(events_received) == 1
        assert events_received[0]["hours_advanced"] == 3
    
    def test_clock_performance(self):
        """Test clock performance with many events."""
        clock = GameClock()
        callbacks = []
        
        # Schedule many events
        for i in range(100):
            callback = Mock()
            callbacks.append(callback)
            clock.schedule_event(
                hours_from_now=i,
                callback=callback,
                event_data={"event_id": i}
            )
        
        # Advance time to trigger all events
        import time
        start_time = time.time()
        result = clock.advance_time(hours=100)
        end_time = time.time()
        
        # Should complete quickly
        execution_time = end_time - start_time
        assert execution_time < 0.1  # Less than 100ms
        
        # All events should trigger
        assert result.events_triggered == 100
        for callback in callbacks:
            callback.assert_called_once()
    
    def test_clock_with_npc_schedules(self):
        """Test clock integration with NPC scheduling."""
        clock = GameClock()
        npc_events = []
        
        def npc_schedule_callback(data):
            npc_events.append(data)
        
        # Schedule NPC arrival and departure
        clock.schedule_event(
            hours_from_now=8,  # 8 AM arrival
            callback=npc_schedule_callback,
            event_data={"action": "arrive", "npc": "merchant"}
        )
        
        clock.schedule_event(
            hours_from_now=18,  # 6 PM departure
            callback=npc_schedule_callback,
            event_data={"action": "depart", "npc": "merchant"}
        )
        
        # Advance through the day
        clock.advance_time(hours=20)
        
        # Both events should have triggered
        assert len(npc_events) == 2
        assert npc_events[0]["action"] == "arrive"
        assert npc_events[1]["action"] == "depart"


class TestClockEdgeCases:
    """Test clock edge cases and error conditions."""
    
    def test_advance_negative_time(self):
        """Test advancing negative time is handled."""
        clock = GameClock()
        
        # Attempting to advance negative time should raise error or be ignored
        with pytest.raises(ValueError):
            clock.advance_time(hours=-5)
    
    def test_schedule_event_in_past(self):
        """Test scheduling events in the past."""
        clock = GameClock()
        callback = Mock()
        
        # Try to schedule event in the past
        with pytest.raises(ValueError):
            clock.schedule_event(
                hours_from_now=-5,
                callback=callback,
                event_data={}
            )
    
    def test_cancel_nonexistent_event(self):
        """Test cancelling non-existent event."""
        clock = GameClock()
        
        success = clock.cancel_event("nonexistent_id")
        assert success is False
    
    def test_very_large_time_advancement(self):
        """Test advancing very large amounts of time."""
        clock = GameClock()
        
        # Advance by 1000 years
        very_large_hours = 1000 * 12 * 30 * 24
        result = clock.advance_time(hours=very_large_hours)
        
        assert result.hours_advanced == very_large_hours
        assert clock.current_time.year == 1001  # Should handle large values
    
    def test_clock_precision(self):
        """Test clock maintains precision with small time increments."""
        clock = GameClock()
        
        # Advance by small increments multiple times
        for _ in range(100):
            clock.advance_time(minutes=1)
        
        # Should equal 100 minutes (1 hour 40 minutes)
        assert clock.current_time.hour == 13  # Started at 12
        assert clock.current_time.minute == 40