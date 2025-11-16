"""Simple event bus implementation for game events."""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events that can be dispatched."""

    # Time events
    TIME_ADVANCED = "time_advanced"

    # NPC events
    NPC_SPAWN = "npc_spawn"
    NPC_DEPART = "npc_depart"
    NPC_INTERACTION = "npc_interaction"
    NPC_RELATIONSHIP_CHANGE = "npc_relationship_change"

    # Player events
    PLAYER_STAT_CHANGE = "player_stat_change"
    PLAYER_ITEM_CHANGE = "player_item_change"

    # Room events
    ROOM_CHANGE = "room_change"
    ROOM_OCCUPANT_ADDED = "room_occupant_added"
    ROOM_OCCUPANT_REMOVED = "room_occupant_removed"


@dataclass
class Event:
    """Base event class."""

    event_type: EventType
    data: Dict[str, Any] = None

    def __post_init__(self):
        self.data = self.data or {}


class EventBus:
    """Simple event bus for dispatching and subscribing to game events."""

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}

    def subscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> Callable[[], None]:
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is dispatched

        Returns:
            Function to unsubscribe
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(callback)

        def unsubscribe():
            if (
                event_type in self._subscribers
                and callback in self._subscribers[event_type]
            ):
                self._subscribers[event_type].remove(callback)

        return unsubscribe

    def dispatch(self, event: Event) -> None:
        """Dispatch an event to all subscribers.

        Args:
            event: Event to dispatch
        """
        event_type = event.event_type

        # Convert string event types to EventType if needed
        if isinstance(event_type, str):
            try:
                event_type = EventType(event_type)
            except ValueError:
                logger.warning(f"Unknown event type: {event_type}")
                return

        if event_type not in self._subscribers:
            return

        for callback in list(self._subscribers[event_type]):
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler for {event_type}: {e}", exc_info=True
                )

    def clear(self) -> None:
        """Clear all subscribers."""
        self._subscribers.clear()
