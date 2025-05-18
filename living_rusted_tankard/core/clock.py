from dataclasses import dataclass
from typing import Callable, Optional
from .event import EventQueue, GameEvent
import time

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
    
    def format_time(self) -> str:
        """Format current time as a readable string (e.g., 'Day 2, 14:30')."""
        hours = int(self.hour_of_day)
        minutes = int((self.hour_of_day - hours) * 60)
        return f"Day {self.day}, {hours:02d}:{minutes:02d}"

class GameClock:
    """Manages the game's passage of time and scheduled events."""
    def __init__(self, start_time: float = 0.0):
        self.event_queue = EventQueue()
        self.time = GameTime(start_time)
        self.paused = False
        self._last_tick = time.monotonic()
    
    def update(self) -> None:
        """Advance time based on real time passed."""
        if self.paused:
            return
            
        current_time = time.monotonic()
        delta = current_time - self._last_tick
        self._last_tick = current_time
        
        # In a real game, you might want to scale this delta by a time factor
        self.advance_time(delta / 3600)  # Convert seconds to hours
    
    def advance_time(self, hours: float) -> None:
        """Advance the game clock by the specified number of hours.
        
        Args:
            hours: Number of hours to advance. Must be positive.
        """
        if hours <= 0:
            return
            
        old_time = self.time.hours
        self.time.hours += hours
        
        # Process any events that should trigger in this time period
        self.event_queue.process_events(self.time.hours)
        
        # Fire time update event
        if hasattr(self, 'on_time_advanced'):
            self.on_time_advanced(old_time, self.time.hours, hours)
        
        # Fire hourly and daily events
        self._fire_time_based_events(old_time, self.time.hours)
    
    def _fire_time_based_events(self, old_time: float, new_time: float) -> None:
        """Fire events based on time advancement.
        
        Args:
            old_time: Previous game time in hours
            new_time: Current game time in hours
        """
        old_hour = int(old_time) % 24
        current_hour = int(new_time) % 24
        
        # If we've crossed into a new hour
        if int(old_time) < int(new_time) and hasattr(self, 'on_hour_advanced'):
            self.on_hour_advanced(current_hour)
        
        # If we've crossed a day boundary
        if int(old_time // 24) < int(new_time // 24) and hasattr(self, 'on_day_advanced'):
            self.on_day_advanced(int(new_time // 24))
    
    def schedule_event(
        self, 
        delay: float, 
        handler: Callable[[], None], 
        name: str = "",
        repeats: bool = False,
        interval: float = 0.0
    ) -> GameEvent:
        """Schedule an event to occur after a delay in game hours.
        
        Args:
            delay: Hours from now when the event should trigger
            handler: Function to call when the event triggers
            name: Optional name for the event
            repeats: Whether the event should repeat
            interval: If repeating, time between occurrences in hours
            
        Returns:
            The scheduled GameEvent
        """
        return self.event_queue.schedule_event(
            self.time.hours + delay,
            handler,
            name,
            repeats,
            interval
        )
    
    def cancel_event(self, event: GameEvent) -> None:
        """Cancel a scheduled event.
        
        Args:
            event: The event to cancel
        """
        self.event_queue.cancel_event(event)
    
    def pause(self) -> None:
        """Pause the game clock."""
        self.paused = True
    
    def resume(self) -> None:
        """Resume the game clock."""
        self.paused = False
        self._last_tick = time.monotonic()
    
    def get_time_of_day(self) -> str:
        """Get the current time of day as a string.
        
        Returns:
            Formatted string representing the current in-game time
        """
        return self.time.format_time()
