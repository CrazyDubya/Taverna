from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class GameEvent:
    """Represents a scheduled event in the game."""

    time: float  # Game time in hours when the event should trigger
    handler: Callable[[], None]  # Function to call when the event triggers
    name: str = ""  # Optional name for debugging
    repeats: bool = False  # Whether the event should repeat
    interval: float = 0.0  # If repeating, how often (in game hours)

    def __lt__(self, other: "GameEvent") -> bool:
        # For sorting events by time
        return self.time < other.time


class EventQueue:
    """Manages scheduled game events."""

    def __init__(self):
        self.events: list[GameEvent] = []

    def schedule_event(
        self, time: float, handler: Callable[[], None], name: str = "", repeats: bool = False, interval: float = 0.0
    ) -> GameEvent:
        """Schedule a new event."""
        event = GameEvent(time, handler, name, repeats, interval)
        self.events.append(event)
        self.events.sort()
        return event

    def cancel_event(self, event: GameEvent) -> None:
        """Remove an event from the queue."""
        if event in self.events:
            self.events.remove(event)

    def process_events(self, current_time: float) -> None:
        """Process all events that should trigger at or before current_time."""
        while self.events and self.events[0].time <= current_time:
            event = self.events.pop(0)
            event.handler()

            # Reschedule repeating events
            if event.repeats:
                event.time += event.interval
                self.events.append(event)
                self.events.sort()
