"""Test event bus system."""
import pytest
import asyncio
from unittest.mock import Mock, call
from typing import List

from tests.utils.test_helpers import EventCollector, wait_for_condition

from core.event_bus import EventBus, Event, EventType


class TestEventBus:
    """Test core event bus functionality."""
    
    def test_event_bus_initialization(self):
        """Test event bus initializes correctly."""
        event_bus = EventBus()
        
        assert event_bus is not None
        assert hasattr(event_bus, '_subscribers')
        assert len(event_bus._subscribers) == 0
    
    def test_event_subscription(self):
        """Test subscribing to events."""
        event_bus = EventBus()
        callback = Mock()
        
        # Subscribe to event
        unsubscribe = event_bus.subscribe(EventType.TIME_ADVANCED, callback)
        
        assert EventType.TIME_ADVANCED in event_bus._subscribers
        assert callback in event_bus._subscribers[EventType.TIME_ADVANCED]
        assert callable(unsubscribe)
    
    def test_event_unsubscription(self):
        """Test unsubscribing from events."""
        event_bus = EventBus()
        callback = Mock()
        
        # Subscribe and then unsubscribe
        unsubscribe = event_bus.subscribe(EventType.TIME_ADVANCED, callback)
        unsubscribe()
        
        # Callback should be removed
        if EventType.TIME_ADVANCED in event_bus._subscribers:
            assert callback not in event_bus._subscribers[EventType.TIME_ADVANCED]
    
    def test_event_dispatch(self):
        """Test dispatching events to subscribers."""
        event_bus = EventBus()
        callback = Mock()
        
        # Subscribe to event
        event_bus.subscribe(EventType.TIME_ADVANCED, callback)
        
        # Dispatch event
        event = Event(
            event_type=EventType.TIME_ADVANCED,
            data={"hours": 2, "new_time": "10:00"}
        )
        event_bus.dispatch(event)
        
        # Callback should be called with event
        callback.assert_called_once_with(event)
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers receive events."""
        event_bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        # Subscribe multiple callbacks
        event_bus.subscribe(EventType.NPC_SPAWN, callback1)
        event_bus.subscribe(EventType.NPC_SPAWN, callback2)
        event_bus.subscribe(EventType.NPC_SPAWN, callback3)
        
        # Dispatch event
        event = Event(
            event_type=EventType.NPC_SPAWN,
            data={"npc_id": "test_npc", "location": "tavern"}
        )
        event_bus.dispatch(event)
        
        # All callbacks should be called
        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)
        callback3.assert_called_once_with(event)
    
    def test_event_type_isolation(self):
        """Test events only go to subscribers of that type."""
        event_bus = EventBus()
        time_callback = Mock()
        npc_callback = Mock()
        
        # Subscribe to different event types
        event_bus.subscribe(EventType.TIME_ADVANCED, time_callback)
        event_bus.subscribe(EventType.NPC_SPAWN, npc_callback)
        
        # Dispatch time event
        time_event = Event(event_type=EventType.TIME_ADVANCED, data={"hours": 1})
        event_bus.dispatch(time_event)
        
        # Only time callback should be called
        time_callback.assert_called_once_with(time_event)
        npc_callback.assert_not_called()
    
    def test_event_error_handling(self):
        """Test event bus handles subscriber errors gracefully."""
        event_bus = EventBus()
        
        # Create callback that raises exception
        error_callback = Mock(side_effect=Exception("Subscriber error"))
        normal_callback = Mock()
        
        # Subscribe both callbacks
        event_bus.subscribe(EventType.PLAYER_STAT_CHANGE, error_callback)
        event_bus.subscribe(EventType.PLAYER_STAT_CHANGE, normal_callback)
        
        # Dispatch event
        event = Event(
            event_type=EventType.PLAYER_STAT_CHANGE,
            data={"stat": "health", "change": -10}
        )
        event_bus.dispatch(event)
        
        # Normal callback should still be called despite error
        error_callback.assert_called_once_with(event)
        normal_callback.assert_called_once_with(event)
    
    def test_clear_subscribers(self):
        """Test clearing all subscribers."""
        event_bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()
        
        # Subscribe to different events
        event_bus.subscribe(EventType.TIME_ADVANCED, callback1)
        event_bus.subscribe(EventType.NPC_SPAWN, callback2)
        
        # Clear all subscribers
        event_bus.clear()
        
        # No subscribers should remain
        assert len(event_bus._subscribers) == 0


class TestEvent:
    """Test Event class functionality."""
    
    def test_event_creation(self):
        """Test creating events."""
        event = Event(
            event_type=EventType.TIME_ADVANCED,
            data={"hours": 3, "new_hour": 15}
        )
        
        assert event.event_type == EventType.TIME_ADVANCED
        assert event.data["hours"] == 3
        assert event.data["new_hour"] == 15
    
    def test_event_without_data(self):
        """Test creating events without data."""
        event = Event(event_type=EventType.TIME_ADVANCED)
        
        assert event.event_type == EventType.TIME_ADVANCED
        assert event.data == {}  # Should default to empty dict
    
    def test_event_data_modification(self):
        """Test event data can be modified."""
        event = Event(
            event_type=EventType.NPC_INTERACTION,
            data={"npc_id": "barkeeper", "player_id": "player1"}
        )
        
        # Modify data
        event.data["interaction_type"] = "conversation"
        event.data["reputation_change"] = 5
        
        assert event.data["interaction_type"] == "conversation"
        assert event.data["reputation_change"] == 5


class TestEventTypes:
    """Test all defined event types."""
    
    def test_time_events(self):
        """Test time-related events."""
        event_bus = EventBus()
        time_callback = Mock()
        
        event_bus.subscribe(EventType.TIME_ADVANCED, time_callback)
        
        # Test time advancement event
        event = Event(
            event_type=EventType.TIME_ADVANCED,
            data={
                "previous_time": {"hour": 10, "day": 1},
                "current_time": {"hour": 12, "day": 1},
                "hours_passed": 2
            }
        )
        event_bus.dispatch(event)
        
        time_callback.assert_called_once_with(event)
    
    def test_npc_events(self):
        """Test NPC-related events."""
        event_bus = EventBus()
        npc_callback = Mock()
        
        # Subscribe to all NPC events
        event_bus.subscribe(EventType.NPC_SPAWN, npc_callback)
        event_bus.subscribe(EventType.NPC_DEPART, npc_callback)
        event_bus.subscribe(EventType.NPC_INTERACTION, npc_callback)
        event_bus.subscribe(EventType.NPC_RELATIONSHIP_CHANGE, npc_callback)
        
        # Test NPC spawn
        spawn_event = Event(
            event_type=EventType.NPC_SPAWN,
            data={"npc_id": "merchant", "location": "main_hall"}
        )
        event_bus.dispatch(spawn_event)
        
        # Test NPC interaction
        interaction_event = Event(
            event_type=EventType.NPC_INTERACTION,
            data={
                "npc_id": "barkeeper",
                "player_id": "player1",
                "interaction_type": "buy_drink"
            }
        )
        event_bus.dispatch(interaction_event)
        
        # Both events should be received
        assert npc_callback.call_count == 2
        calls = npc_callback.call_args_list
        assert calls[0][0][0] == spawn_event
        assert calls[1][0][0] == interaction_event
    
    def test_player_events(self):
        """Test player-related events."""
        event_bus = EventBus()
        player_callback = Mock()
        
        event_bus.subscribe(EventType.PLAYER_STAT_CHANGE, player_callback)
        event_bus.subscribe(EventType.PLAYER_ITEM_CHANGE, player_callback)
        
        # Test stat change
        stat_event = Event(
            event_type=EventType.PLAYER_STAT_CHANGE,
            data={
                "player_id": "player1",
                "stat": "health",
                "old_value": 100,
                "new_value": 90,
                "change": -10
            }
        )
        event_bus.dispatch(stat_event)
        
        # Test item change
        item_event = Event(
            event_type=EventType.PLAYER_ITEM_CHANGE,
            data={
                "player_id": "player1",
                "action": "add",
                "item": "health_potion",
                "quantity": 1
            }
        )
        event_bus.dispatch(item_event)
        
        assert player_callback.call_count == 2
    
    def test_room_events(self):
        """Test room-related events."""
        event_bus = EventBus()
        room_callback = Mock()
        
        event_bus.subscribe(EventType.ROOM_CHANGE, room_callback)
        event_bus.subscribe(EventType.ROOM_OCCUPANT_ADDED, room_callback)
        event_bus.subscribe(EventType.ROOM_OCCUPANT_REMOVED, room_callback)
        
        # Test room change
        room_change_event = Event(
            event_type=EventType.ROOM_CHANGE,
            data={
                "player_id": "player1",
                "from_room": "main_hall",
                "to_room": "private_room_1"
            }
        )
        event_bus.dispatch(room_change_event)
        
        room_callback.assert_called_once_with(room_change_event)


class TestEventBusIntegration:
    """Test event bus integration with game systems."""
    
    def test_event_chain_reaction(self):
        """Test events can trigger other events."""
        event_bus = EventBus()
        event_collector = EventCollector()
        
        def time_handler(event):
            """Handle time events and trigger NPC events."""
            event_collector.collect_event("time_advanced", event.data)
            
            # Time advancing might cause NPCs to spawn
            if event.data.get("hours_passed", 0) >= 1:
                npc_event = Event(
                    event_type=EventType.NPC_SPAWN,
                    data={"npc_id": "random_patron", "reason": "time_passed"}
                )
                event_bus.dispatch(npc_event)
        
        def npc_handler(event):
            """Handle NPC events."""
            event_collector.collect_event("npc_spawned", event.data)
        
        # Subscribe handlers
        event_bus.subscribe(EventType.TIME_ADVANCED, time_handler)
        event_bus.subscribe(EventType.NPC_SPAWN, npc_handler)
        
        # Trigger initial event
        time_event = Event(
            event_type=EventType.TIME_ADVANCED,
            data={"hours_passed": 2, "new_hour": 14}
        )
        event_bus.dispatch(time_event)
        
        # Both events should be collected
        assert len(event_collector.get_events()) == 2
        time_events = event_collector.get_events("time_advanced")
        npc_events = event_collector.get_events("npc_spawned")
        
        assert len(time_events) == 1
        assert len(npc_events) == 1
        assert npc_events[0]["data"]["reason"] == "time_passed"
    
    def test_event_filtering(self):
        """Test filtering events based on conditions."""
        event_bus = EventBus()
        filtered_events = []
        
        def selective_handler(event):
            """Only handle events for specific NPC."""
            if event.data.get("npc_id") == "important_npc":
                filtered_events.append(event)
        
        event_bus.subscribe(EventType.NPC_INTERACTION, selective_handler)
        
        # Send multiple NPC interaction events
        for npc_id in ["random_npc", "important_npc", "another_npc", "important_npc"]:
            event = Event(
                event_type=EventType.NPC_INTERACTION,
                data={"npc_id": npc_id, "interaction": "talk"}
            )
            event_bus.dispatch(event)
        
        # Only important_npc events should be filtered
        assert len(filtered_events) == 2
        assert all(event.data["npc_id"] == "important_npc" for event in filtered_events)
    
    def test_event_bus_performance(self):
        """Test event bus performance with many subscribers."""
        event_bus = EventBus()
        callbacks = []
        
        # Create many subscribers
        for i in range(100):
            callback = Mock()
            callbacks.append(callback)
            event_bus.subscribe(EventType.TIME_ADVANCED, callback)
        
        # Dispatch event
        event = Event(event_type=EventType.TIME_ADVANCED, data={"hours": 1})
        
        import time
        start_time = time.time()
        event_bus.dispatch(event)
        end_time = time.time()
        
        # Should complete quickly even with many subscribers
        dispatch_time = end_time - start_time
        assert dispatch_time < 0.1  # Should take less than 100ms
        
        # All callbacks should be called
        for callback in callbacks:
            callback.assert_called_once_with(event)
    
    def test_async_event_handling(self):
        """Test event bus with async handlers."""
        event_bus = EventBus()
        async_results = []
        
        async def async_handler(event):
            """Async event handler."""
            await asyncio.sleep(0.01)  # Simulate async work
            async_results.append(event.data)
        
        def sync_wrapper(event):
            """Wrapper to handle async in sync context."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(async_handler(event))
            loop.close()
        
        event_bus.subscribe(EventType.PLAYER_STAT_CHANGE, sync_wrapper)
        
        # Dispatch event
        event = Event(
            event_type=EventType.PLAYER_STAT_CHANGE,
            data={"stat": "gold", "change": 50}
        )
        event_bus.dispatch(event)
        
        # Give time for async operation
        assert len(async_results) == 1
        assert async_results[0]["stat"] == "gold"


class TestEventBusEdgeCases:
    """Test event bus edge cases and error conditions."""
    
    def test_dispatch_unknown_event_type(self):
        """Test dispatching events with no subscribers."""
        event_bus = EventBus()
        
        # Create event with type that has no subscribers
        event = Event(event_type=EventType.NPC_SPAWN, data={})
        
        # Should not raise exception
        event_bus.dispatch(event)
    
    def test_string_event_type_conversion(self):
        """Test string event types are converted correctly."""
        event_bus = EventBus()
        callback = Mock()
        
        event_bus.subscribe(EventType.TIME_ADVANCED, callback)
        
        # Create event with string type
        event = Event(event_type="time_advanced", data={"hours": 1})
        event_bus.dispatch(event)
        
        # Should be converted and delivered
        callback.assert_called_once()
    
    def test_invalid_string_event_type(self):
        """Test invalid string event types are handled."""
        event_bus = EventBus()
        callback = Mock()
        
        event_bus.subscribe(EventType.TIME_ADVANCED, callback)
        
        # Create event with invalid string type
        event = Event(event_type="invalid_event_type", data={})
        event_bus.dispatch(event)
        
        # Callback should not be called
        callback.assert_not_called()
    
    def test_subscriber_removal_during_dispatch(self):
        """Test subscriber can remove itself during event handling."""
        event_bus = EventBus()
        unsubscribe_func = None
        
        def self_removing_callback(event):
            """Callback that unsubscribes itself."""
            if unsubscribe_func:
                unsubscribe_func()
        
        # Subscribe callback
        unsubscribe_func = event_bus.subscribe(EventType.TIME_ADVANCED, self_removing_callback)
        
        # Dispatch event - should not cause error
        event = Event(event_type=EventType.TIME_ADVANCED, data={})
        event_bus.dispatch(event)
        
        # Subscriber should be removed
        if EventType.TIME_ADVANCED in event_bus._subscribers:
            assert self_removing_callback not in event_bus._subscribers[EventType.TIME_ADVANCED]