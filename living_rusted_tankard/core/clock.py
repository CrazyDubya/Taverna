from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, List, Any, Union
import time
from datetime import datetime, timedelta

from .event_bus import EventBus, Event, EventType

@dataclass
class GameTime:
    """Represents game time in hours since game start."""
    hours: float = 0.0
    
    @property
    def hour_of_day(self) -> float:
        """Current hour of the day (0-24)."""
        return self.hours % 24
    
    @property
    def day(self) -> int:
        """Current day number (starting from 1)."""
        return int(self.hours // 24) + 1
    
    @property
    def total_hours(self) -> float:
        """Total hours since game start."""
        return self.hours
    
    @property
    def total_days(self) -> float:
        """Total days since game start."""
        return self.hours / 24.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        return {
            'hours': self.hours,
            'hour_of_day': self.hour_of_day,
            'day': self.day,
            'formatted': self.format_time()
        }
    
    def format_time(self, format_str: str = None) -> str:
        """Format current time as a readable string.
        
        Args:
            format_str: Optional format string. If None, uses default format.
                Available placeholders: {day}, {hour:02d}, {minute:02d}, {ampm}
                
        Returns:
            Formatted time string
        """
        hours = int(self.hour_of_day)
        minutes = int((self.hour_of_day % 1) * 60)
        ampm = "AM" if hours < 12 else "PM"
        
        if format_str is None:
            return f"Day {self.day}, {hours:02d}:{minutes:02d}"
            
        return format_str.format(
            day=self.day,
            hour=hours if hours <= 12 else hours - 12,
            minute=minutes,
            ampm=ampm
        )
    
    def to_real_time(self) -> datetime:
        """Convert to a real datetime (using current date)."""
        now = datetime.now()
        days = int(self.hours // 24)
        hours = self.hours % 24
        return now + timedelta(days=days, hours=hours)
    
    @classmethod
    def from_real_time(cls, dt: datetime, start_time: datetime = None) -> 'GameTime':
        """Create a GameTime from a datetime.
        
        Args:
            dt: Datetime to convert from
            start_time: Optional reference start time (defaults to current time)
            
        Returns:
            GameTime instance
        """
        if start_time is None:
            start_time = datetime.now()
            
        delta = dt - start_time
        return cls(hours=delta.total_seconds() / 3600)

class GameClock:
    """Manages the game's passage of time and scheduled events."""
    def __init__(self, start_time: float = 0.0, time_scale: float = 1.0):
        """Initialize the game clock.
        
        Args:
            start_time: Initial game time in hours
            time_scale: Scale factor for time passage (1.0 = realtime)
        """
        self.event_bus = EventBus()
        self.time = GameTime(start_time)
        self.paused = False
        self.time_scale = time_scale
        self._last_tick = time.monotonic()
        self._scheduled_events: List[Dict] = []
        self._day_callbacks = {}
        self._hour_callbacks = {}
        self._minute_callbacks = {}
        self._last_day = self.time.day
        self._last_hour = int(self.time.hour_of_day)
        self._last_minute = int((self.time.hour_of_day % 1) * 60)
        self.event_queue = self.event_bus  # Alias for backward compatibility
    
    def update(self) -> None:
        """Advance time based on real time passed."""
        if self.paused:
            return
            
        current_time = time.monotonic()
        delta = (current_time - self._last_tick) * self.time_scale
        self._last_tick = current_time
        
        # Convert seconds to game hours and advance time
        self.advance_time(delta / 3600)
        
        # Process scheduled events
        self._process_scheduled_events()
        
        # Process time-based callbacks
        self._process_time_callbacks()
    
    @property
    def current_time(self) -> 'GameTime':
        """Get current game time."""
        return self.time
        
    @property
    def current_time_hours(self) -> float:
        """Get current game time in hours for backward compatibility."""
        return self.time.hours
        
    def get_current_time(self) -> 'GameTime':
        """Get current game time."""
        return self.time
        
    def pause(self) -> None:
        """Pause the game clock."""
        self.paused = True
        
    def resume(self) -> None:
        """Resume the game clock."""
        self.paused = False
        self._last_tick = time.monotonic()
        
    def set_time_scale(self, scale: float) -> None:
        """Set the time scale factor.
        
        Args:
            scale: Time scale factor (1.0 = realtime, 2.0 = 2x speed, etc.)
        """
        self.time_scale = max(0, scale)
        
    def schedule_event(
        self, 
        delay: float, 
        handler: Callable[[], None], 
        name: str = "",
        repeats: bool = False,
        interval: float = 0.0,
        **kwargs
    ) -> str:
        """Schedule an event to occur after a delay in game hours.
        
        Args:
            delay: Hours from now when the event should trigger
            handler: Function to call when the event triggers
            name: Optional name for the event
            repeats: Whether the event should repeat
            interval: If repeating, time between occurrences in hours
            **kwargs: Additional arguments to pass to the callback
            
        Returns:
            str: Event ID that can be used to cancel the event
        """
        from uuid import uuid4
        event_id = str(uuid4())
        
        # If this is a repeating event, ensure we have a valid interval
        if repeats and interval <= 0:
            interval = delay
            
        self._scheduled_events.append({
            'id': event_id,
            'name': name,
            'time': self.time.hours + delay,
            'callback': handler,
            'repeat': repeats,
            'interval': interval,
            'kwargs': kwargs or {}
        })
        
        # Sort events by time to ensure they're processed in order
        self._scheduled_events.sort(key=lambda e: e['time'])
        
        return event_id
        
    def cancel_event(self, event_id: str) -> bool:
        """Cancel a scheduled event.
        
        Args:
            event_id: ID of the event to cancel
            
        Returns:
            True if the event was found and cancelled, False otherwise
        """
        for i, event in enumerate(self._scheduled_events):
            if event['id'] == event_id:
                self._scheduled_events.pop(i)
                return True
                
        return False
    
    def on_day_change(self, callback: Callable[[int], None]) -> Callable:
        """Register a callback for when the day changes.
        
        Args:
            callback: Function to call when the day changes
                Receives the new day number
                
        Returns:
            Function to unregister the callback
        """
        from uuid import uuid4
        callback_id = str(uuid4())
        self._day_callbacks[callback_id] = callback
        
        def unregister():
            self._day_callbacks.pop(callback_id, None)
            
        return unregister
    
    def on_hour_change(self, callback: Callable[[int], None]) -> Callable:
        """Register a callback for when the hour changes.
        
        Args:
            callback: Function to call when the hour changes
                Receives the new hour (0-23)
                
        Returns:
            Function to unregister the callback
        """
        from uuid import uuid4
        callback_id = str(uuid4())
        self._hour_callbacks[callback_id] = callback
        
        def unregister():
            self._hour_callbacks.pop(callback_id, None)
            
        return unregister
    
    def on_minute_change(self, callback: Callable[[int], None]) -> Callable:
        """Register a callback for when the minute changes.
        
        Args:
            callback: Function to call when the minute changes
                Receives the new minute (0-59)
                
        Returns:
            Function to unregister the callback
        """
        from uuid import uuid4
        callback_id = str(uuid4())
        self._minute_callbacks[callback_id] = callback
        
        def unregister():
            self._minute_callbacks.pop(callback_id, None)
            
        return unregister
    
    def _process_scheduled_events(self) -> None:
        """Process any scheduled events that are due."""
        current_time = self.time.hours
        events_to_remove = []
        
        for i, event in enumerate(self._scheduled_events):
            if current_time >= event['time']:
                try:
                    # Call the callback with the event data
                    event['callback'](**event['kwargs'])
                    
                    # Reschedule if repeating
                    if event['repeat']:
                        event['time'] += event['interval']
                    else:
                        events_to_remove.append(i)
                except Exception as e:
                    print(f"Error in scheduled event: {e}")
                    events_to_remove.append(i)
        
        # Remove processed events in reverse order to avoid index issues
        for i in sorted(events_to_remove, reverse=True):
            if i < len(self._scheduled_events):
                self._scheduled_events.pop(i)
    
    def _process_time_callbacks(self) -> None:
        """Process time-based callbacks (day, hour, minute changes)."""
        current_hour = int(self.time.hour_of_day)
        current_minute = int((self.time.hour_of_day % 1) * 60)
        
        # Check for day change
        if self.time.day != self._last_day:
            self._last_day = self.time.day
            for callback in list(self._day_callbacks.values()):
                try:
                    callback(self.time.day)
                except Exception as e:
                    print(f"Error in day change callback: {e}")
        
        # Check for hour change
        if current_hour != self._last_hour:
            self._last_hour = current_hour
            for callback in list(self._hour_callbacks.values()):
                try:
                    callback(current_hour)
                except Exception as e:
                    print(f"Error in hour change callback: {e}")
        
        # Check for minute change
        if current_minute != self._last_minute:
            self._last_minute = current_minute
            for callback in list(self._minute_callbacks.values()):
                try:
                    callback(current_minute)
                except Exception as e:
                    print(f"Error in minute change callback: {e}")
            
            # Dispatch time update event every minute
            self.event_bus.dispatch(Event(
                EventType.TIME_ADVANCED,
                {'time': self.time.to_dict()}
            ))
        
    def advance(self, hours: float) -> None:
        """Advance time by the specified number of hours.
        
        This is an alias for advance_time for backward compatibility.
        """
        self.advance_time(hours)
        
    def get_formatted_time(self) -> str:
        """Get formatted game time string."""
        return self.time.format_time()
        
    def advance_time(self, hours: float) -> None:
        """Advance the game clock by the specified number of hours.
        
        Args:
            hours: Number of hours to advance. Must be positive.
        """
        if hours <= 0:
            return
            
        old_time = self.time.hours
        self.time.hours += hours
        
        # Process scheduled events
        self._process_scheduled_events()
        
        # Process time-based callbacks
        self._process_time_callbacks()
        
        # Fire time-based events
        self._fire_time_based_events(old_time, self.time.hours)
        
        # Notify any listeners of the time advancement
        self.event_bus.dispatch(Event(
            EventType.TIME_ADVANCED,
            {'old_time': old_time, 'new_time': self.time.hours, 'delta': hours}
        ))
    
    def _fire_time_based_events(self, old_time: float, new_time: float) -> None:
        """Fire events based on time advancement.
        
        Args:
            old_time: Previous game time in hours
            new_time: Current game time in hours
        """
        old_day = int(old_time // 24)
        new_day = int(new_time // 24)
        
        # Check for day change
        if new_day > old_day:
            for callback in list(self._day_callbacks.values()):
                try:
                    callback(new_day)
                except Exception as e:
                    print(f"Error in day change callback: {e}")
        
        # Check for hour change
        old_hour = int(old_time) % 24
        current_hour = int(new_time) % 24
        if current_hour != old_hour:
            for callback in list(self._hour_callbacks.values()):
                try:
                    callback(current_hour)
                except Exception as e:
                    print(f"Error in hour change callback: {e}")
    
    def cancel_event(self, event_id: str) -> bool:
        """Cancel a scheduled event.
        
        Args:
            event_id: The ID of the event to cancel
            
        Returns:
            bool: True if the event was found and cancelled, False otherwise
        """
        for i, event in enumerate(self._scheduled_events):
            if event['id'] == event_id:
                self._scheduled_events.pop(i)
                return True
        return False
    
    def get_time_of_day(self) -> str:
        """Get the current time of day as a string.
        
        Returns:
            Formatted string representing the current in-game time
        """
        return self.time.format_time()
