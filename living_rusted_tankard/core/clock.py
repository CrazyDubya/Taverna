from typing import Callable, Optional, Dict, List, Any
import time
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from .event_bus import EventBus, Event, EventType
from .callable_registry import get_callback


class GameTime(BaseModel):
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

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Convert to a dictionary representation, including properties."""
        # Use dict() method for older Pydantic versions or direct field access
        try:
            dump = super().model_dump(**kwargs)
        except AttributeError:
            # Fallback for older Pydantic versions
            dump = self.dict(**kwargs)

        dump["hour_of_day"] = self.hour_of_day
        dump["day"] = self.day
        dump["formatted_time"] = self.format_time()  # Now uses natural time by default
        dump["legacy_time"] = self.format_time(style="legacy")  # Keep decimal version for backward compatibility
        return dump

    def format_time(self, format_str: str = None, style: str = "natural") -> str:
        """Format current time as a readable string.

        Args:
            format_str: Optional format string. If None, uses default format based on style.
                Available placeholders for legacy format: {day}, {hour:02d}, {minute:02d}, {ampm}
            style: Display style - "natural" (default), "legacy", "bell", "narrative", "formal"

        Returns:
            Formatted time string
        """
        # Import here to avoid circular imports
        from .time_display import format_time_for_display

        if style == "natural" and format_str is None:
            # Use natural fantasy time display
            return format_time_for_display(self.hours, "ui_main")
        elif style == "bell":
            return format_time_for_display(self.hours, "ui_main")
        elif style == "narrative":
            return format_time_for_display(self.hours, "npc_casual")
        elif style == "formal":
            return format_time_for_display(self.hours, "npc_formal")
        else:
            # Legacy decimal format or custom format string
            hours = int(self.hour_of_day)
            minutes = int((self.hour_of_day % 1) * 60)
            ampm = "AM" if hours < 12 else "PM"

            if format_str is None:
                return f"Day {self.day}, {hours:02d}:{minutes:02d}"

            return format_str.format(day=self.day, hour=hours if hours <= 12 else hours - 12, minute=minutes, ampm=ampm)

    def to_real_time(self) -> datetime:
        """Convert to a real datetime (using current date)."""
        now = datetime.now()
        days = int(self.hours // 24)
        hours = self.hours % 24
        return now + timedelta(days=days, hours=hours)

    @classmethod
    def from_real_time(cls, dt: datetime, start_time: Optional[datetime] = None) -> "GameTime":
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


# Helper type for scheduled events to make Pydantic validation work with Callables
# We won't directly use this in the list if we're serializing callback names,
# but it's good for type hinting if we were to pass actual callables around.
class ScheduledEvent(BaseModel):
    id: str
    name: str
    time: float
    callback_name: str  # Store the registered name of the callback
    repeat: bool
    interval: float
    kwargs: Dict[str, Any]

    class Config:
        arbitrary_types_allowed = True  # For Callable if we were to store it


class GameClock(BaseModel):
    """Manages the game's passage of time and scheduled events."""

    time: GameTime = Field(default_factory=GameTime)
    paused: bool = False
    time_scale: float = 1.0

    # Pydantic v1 doesn't allow fields with leading underscores, so we renamed them
    scheduled_events_data: List[Dict[str, Any]] = Field(default_factory=list, exclude=True)
    event_bus_field: EventBus = Field(default_factory=EventBus, exclude=True)
    last_tick: float = Field(default=0.0, exclude=True)
    day_callbacks: Dict[str, Callable[[int], None]] = Field(default_factory=dict, exclude=True)
    hour_callbacks: Dict[str, Callable[[int], None]] = Field(default_factory=dict, exclude=True)
    minute_callbacks: Dict[str, Callable[[int], None]] = Field(default_factory=dict, exclude=True)
    last_day_field: int = Field(default=0, exclude=True)
    last_hour_field: int = Field(default=0, exclude=True)
    last_minute_field: int = Field(default=0, exclude=True)

    class Config:
        # Allow extra attributes for backward compatibility
        extra = "allow"
        # Allow arbitrary types for EventBus and other non-standard fields
        arbitrary_types_allowed = True

    # For GameState to hook into, not serialized with clock's own state
    on_time_advanced_handler: Optional[Callable[[float, float, float], None]] = Field(None, exclude=True)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.last_tick = time.monotonic()
        self.last_day_field = self.time.day
        self.last_hour_field = int(self.time.hour_of_day)
        self.last_minute_field = int((self.time.hour_of_day % 1) * 60)

        # Initialize scheduled_events_data if it's still a field
        if isinstance(self.scheduled_events_data, FieldInfo):
            self.scheduled_events_data = []

        # Initialize all FieldInfo attributes
        if isinstance(self.event_bus_field, FieldInfo):
            self.event_bus_field = EventBus()

        if isinstance(self.day_callbacks, FieldInfo):
            self.day_callbacks = {}

        if isinstance(self.hour_callbacks, FieldInfo):
            self.hour_callbacks = {}

        if isinstance(self.minute_callbacks, FieldInfo):
            self.minute_callbacks = {}

        # Rebuild runtime scheduled events from scheduled_events_data if loading
        self._rebuild_runtime_scheduled_events()

    def _rebuild_runtime_scheduled_events(self):
        """
        Rebuilds the runtime scheduled events list (which would use actual callbacks)
        from scheduled_events_data (which stores callback names).
        This method is conceptual for now if scheduled_events_data is directly manipulated
        by Pydantic's dict/model_dump.
        For now, scheduled_events_data will BE the source of truth for serialization.
        The actual runtime execution will use get_callback.
        """
        # No actual runtime list of callables is stored persistently in this design.
        # Callbacks are retrieved from registry on-the-fly in _process_scheduled_events.

    @property
    def event_bus(self) -> EventBus:  # Provide access to the event_bus_field attribute
        return self.event_bus_field

    # For backward compatibility
    @property
    def _event_bus(self) -> EventBus:
        return self.event_bus_field

    @property
    def _scheduled_events_data(self) -> List[Dict[str, Any]]:
        return self.scheduled_events_data

    @_scheduled_events_data.setter
    def _scheduled_events_data(self, value: List[Dict[str, Any]]):
        self.scheduled_events_data = value

    @property
    def _last_day(self) -> int:
        return self.last_day_field

    @_last_day.setter
    def _last_day(self, value: int):
        self.last_day_field = value

    @property
    def _last_hour(self) -> int:
        return self.last_hour_field

    @_last_hour.setter
    def _last_hour(self, value: int):
        self.last_hour_field = value

    @property
    def _last_minute(self) -> int:
        return self.last_minute_field

    @_last_minute.setter
    def _last_minute(self, value: int):
        self.last_minute_field = value

    @property
    def _last_tick(self) -> float:
        return self.last_tick

    @_last_tick.setter
    def _last_tick(self, value: float):
        self.last_tick = value

    @property
    def _day_callbacks(self) -> Dict[str, Callable[[int], None]]:
        return self.day_callbacks

    @_day_callbacks.setter
    def _day_callbacks(self, value: Dict[str, Callable[[int], None]]):
        self.day_callbacks = value

    @property
    def _hour_callbacks(self) -> Dict[str, Callable[[int], None]]:
        return self.hour_callbacks

    @_hour_callbacks.setter
    def _hour_callbacks(self, value: Dict[str, Callable[[int], None]]):
        self.hour_callbacks = value

    @property
    def _minute_callbacks(self) -> Dict[str, Callable[[int], None]]:
        return self.minute_callbacks

    @_minute_callbacks.setter
    def _minute_callbacks(self, value: Dict[str, Callable[[int], None]]):
        self.minute_callbacks = value

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Serialize GameClock state."""
        # Exclude runtime-only or complex objects that are handled separately
        kwargs.setdefault("exclude", {"on_time_advanced_handler"})  # Already excluded by Field option

        data = super().model_dump(**kwargs)
        # scheduled_events_data is already handled by Pydantic if it's a regular field.
        # If it's PrivateAttr, we need to explicitly add it.
        data["_scheduled_events_data"] = self.scheduled_events_data  # Use old name for compatibility
        return data

    @classmethod
    def model_validate(cls, obj: Any, **kwargs) -> "GameClock":
        """Deserialize GameClock state."""
        # If scheduled_events_data is a PrivateAttr, Pydantic won't populate it automatically from obj
        # We need to handle it manually or ensure it's part of the main model fields.
        # For now, assume scheduled_events_data is a regular field that Pydantic handles.
        instance = super().model_validate(obj, **kwargs)

        # If _scheduled_events_data was a PrivateAttr and not directly in obj for Pydantic:
        if isinstance(obj, dict) and "_scheduled_events_data" in obj:
            instance.scheduled_events_data = obj["_scheduled_events_data"]

        instance.last_tick = time.monotonic()  # Reset runtime timer
        instance.event_bus_field = EventBus()  # New event bus
        instance.day_callbacks = {}  # Reset callbacks, to be re-registered by systems
        instance.hour_callbacks = {}
        instance.minute_callbacks = {}

        # Re-initialize last known time details based on loaded time
        instance.last_day_field = instance.time.day
        instance.last_hour_field = int(instance.time.hour_of_day)
        instance.last_minute_field = int((instance.time.hour_of_day % 1) * 60)

        return instance

    def update(self) -> None:
        """Advance time based on real time passed."""
        if self.paused:
            self.last_tick = time.monotonic()  # Prevent large delta when unpausing
            return

        current_real_time = time.monotonic()
        delta_real_time = current_real_time - self.last_tick
        self.last_tick = current_real_time

        # Convert real seconds to game hours and advance time
        game_hours_delta = (delta_real_time * self.time_scale) / 3600.0

        if game_hours_delta > 0:
            self.advance_time(game_hours_delta)
            # _process_scheduled_events and _process_time_callbacks are called by advance_time

    @property
    def current_time(self) -> "GameTime":
        """Get current game time."""
        return self.time

    @property
    def current_time_hours(self) -> float:
        """Get current game time in hours for backward compatibility."""
        return self.time.hours

    def get_current_time(self) -> "GameTime":
        """Get current game time."""
        return self.time

    def pause(self) -> None:
        """Pause the game clock."""
        self.paused = True

    def resume(self) -> None:
        """Resume the game clock."""
        self.paused = False
        self.last_tick = time.monotonic()  # Reset tick to prevent jump

    def set_time_scale(self, scale: float) -> None:
        """Set the time scale factor.

        Args:
            scale: Time scale factor (1.0 = realtime, 2.0 = 2x speed, etc.)
        """
        self.time_scale = max(0.0, scale)  # Ensure non-negative

    def schedule_event(
        self,
        delay: float,
        # handler: Callable[[], None], # Original handler
        callback_name: str,  # Registered name of the callback
        name: str = "",
        repeats: bool = False,
        interval: float = 0.0,
        **kwargs,
    ) -> str:
        """Schedule an event to occur after a delay in game hours.

        Args:
            delay: Hours from now when the event should trigger
            callback_name: Registered name of the function to call
            name: Optional name for the event
            repeats: Whether the event should repeat
            interval: If repeating, time between occurrences in hours
            **kwargs: Additional arguments to pass to the callback

        Returns:
            str: Event ID that can be used to cancel the event
        """
        from uuid import uuid4

        event_id = str(uuid4())

        # Ensure the callback is registered before scheduling
        get_callback(callback_name)  # Will raise ValueError if not found

        if repeats and interval <= 0:
            interval = delay  # If repeating and no interval, use delay as interval

        event_data = {
            "id": event_id,
            "name": name,
            "time": self.time.hours + delay,
            "callback_name": callback_name,  # Store the name
            "repeat": repeats,
            "interval": interval,
            "kwargs": kwargs or {},
        }
        self.scheduled_events_data.append(event_data)

        # Sort events by time to ensure they're processed in order
        # This is important if _process_scheduled_events iterates and pops
        self.scheduled_events_data.sort(key=lambda e: e["time"])

        return event_id

    def cancel_event(self, event_id: str) -> bool:
        """Cancel a scheduled event.

        Args:
            event_id: ID of the event to cancel

        Returns:
            True if the event was found and cancelled, False otherwise
        """
        original_len = len(self.scheduled_events_data)
        self.scheduled_events_data = [event for event in self.scheduled_events_data if event["id"] != event_id]
        return len(self.scheduled_events_data) < original_len

    def on_day_change(self, callback: Callable[[int], None]) -> Callable:
        """Register a callback for when the day changes.

        Args:
            callback: Function to call when the day changes
                Receives the new day number

        Returns:
            Function to unregister the callback
        """
        from uuid import uuid4  # Keep local import for utility

        callback_id = str(uuid4())
        self.day_callbacks[callback_id] = callback

        def unregister():
            self.day_callbacks.pop(callback_id, None)

        return unregister

    def on_hour_change(self, callback: Callable[[int], None]) -> Callable:
        """Register a callback for when the hour changes.

        Args:
            callback: Function to call when the hour changes
                Receives the new hour (0-23)

        Returns:
            Function to unregister the callback
        """
        from uuid import uuid4  # Keep local import

        callback_id = str(uuid4())
        self.hour_callbacks[callback_id] = callback

        def unregister():
            self.hour_callbacks.pop(callback_id, None)

        return unregister

    def on_minute_change(self, callback: Callable[[int], None]) -> Callable:
        """Register a callback for when the minute changes.

        Args:
            callback: Function to call when the minute changes
                Receives the new minute (0-59)

        Returns:
            Function to unregister the callback
        """
        from uuid import uuid4  # Keep local import

        callback_id = str(uuid4())
        self.minute_callbacks[callback_id] = callback

        def unregister():
            self.minute_callbacks.pop(callback_id, None)

        return unregister

    def _process_scheduled_events(self) -> None:
        """Process any scheduled events that are due."""
        current_clock_time = self.time.hours

        # Iterate safely for modification
        new_scheduled_events_data = []
        processed_any = False

        for event_data in self.scheduled_events_data:
            if current_clock_time >= event_data["time"]:
                processed_any = True
                try:
                    callback_func = get_callback(event_data["callback_name"])
                    callback_func(**event_data["kwargs"])

                    if event_data["repeat"]:
                        event_data["time"] += event_data["interval"]
                        new_scheduled_events_data.append(event_data)  # Re-add if repeating
                    # else: it's removed by not re-adding
                except Exception as e:
                    print(f"Error processing event '{event_data.get('name', 'Unnamed')}': {e}")
                    # Decide if a failing repeating event should be rescheduled or not
                    # For now, if it fails, it's not rescheduled.
            else:
                new_scheduled_events_data.append(event_data)  # Keep if not yet due

        if processed_any:
            # Re-sort if any repeating events were re-added
            self.scheduled_events_data = sorted(new_scheduled_events_data, key=lambda e: e["time"])
        else:
            self.scheduled_events_data = new_scheduled_events_data

    def _process_time_callbacks(self) -> None:
        """Process time-based callbacks (day, hour, minute changes)."""
        current_hour_val = int(self.time.hour_of_day)
        current_minute_val = int((self.time.hour_of_day % 1) * 60)

        if self.time.day != self.last_day_field:
            self.last_day_field = self.time.day
            for callback_id, callback_func in list(self.day_callbacks.items()):
                try:
                    callback_func(self.time.day)
                except Exception as e:
                    print(f"Error in day change callback (id: {callback_id}): {e}")

        if current_hour_val != self.last_hour_field:
            self.last_hour_field = current_hour_val
            for callback_id, callback_func in list(self.hour_callbacks.items()):
                try:
                    callback_func(current_hour_val)
                except Exception as e:
                    print(f"Error in hour change callback (id: {callback_id}): {e}")

        if current_minute_val != self.last_minute_field:
            self.last_minute_field = current_minute_val
            for callback_id, callback_func in list(self.minute_callbacks.items()):
                try:
                    callback_func(current_minute_val)
                except Exception as e:
                    print(f"Error in minute change callback (id: {callback_id}): {e}")

            # Dispatch general time update event (e.g. every minute)
            self.event_bus_field.dispatch(
                Event(EventType.TIME_ADVANCED, {"time": self.time.model_dump()})  # Use Pydantic model_dump for GameTime
            )

        # If GameState has an on_time_advanced_handler, call it
        # This is where the GameState._setup_event_handlers logic for on_time_advanced connects
        # We need to calculate the actual delta for this call based on the change that just occurred.
        # This part is tricky as advance_time itself is what causes these.
        # The TIME_ADVANCED event dispatched above is more generic.
        # The specific on_time_advanced_handler is usually for the main GameState update loop.
        # Let's assume advance_time handles calling this directly.

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
        if hours <= 0:  # Do not advance if hours is zero or negative
            return

        old_time_hours = self.time.hours
        self.time.hours += hours

        # Process scheduled events before time callbacks, as events might trigger further state changes
        self._process_scheduled_events()

        # Process general time-based callbacks (day/hour/minute changes)
        self._process_time_callbacks()

        # Explicitly call the GameState's on_time_advanced handler if it's set
        if self.on_time_advanced_handler:
            try:
                self.on_time_advanced_handler(old_time_hours, self.time.hours, hours)
            except Exception as e:
                print(f"Error in GameState on_time_advanced_handler: {e}")

        # A more generic TIME_ADVANCED event for other systems, if needed.
        # This might be redundant if GameState's handler covers the main logic.
        self.event_bus_field.dispatch(
            Event(EventType.TIME_ADVANCED, {"old_time": old_time_hours, "new_time": self.time.hours, "delta": hours})
        )

    # _fire_time_based_events seems to be duplicative of _process_time_callbacks
    # and the direct call to on_time_advanced_handler. It is removed to simplify.

    # cancel_event was defined twice. Keeping the one that works with _scheduled_events_data

    def get_time_of_day(self) -> str:
        """Get the current time of day as a string.

        Returns:
            Formatted string representing the current in-game time
        """
        return self.time.format_time()
