"""Event formatter for converting game events into narrative text."""
from typing import List, Dict, Any, Optional
import random
from datetime import datetime

class EventFormatter:
    """Formats game events into narrative text for the player."""
    
    def __init__(self):
        self.recent_events: List[Dict[str, Any]] = []
        self._event_templates = {
            # Rent events
            'rent_success': [
                "You pay {amount} gold and receive the key to room {room_id}.",
                "The innkeeper hands you the key to room {room_id} after taking {amount} gold.",
            ],
            'rent_failure': [
                "You don't have enough gold to rent a room.",
                "The innkeeper shakes their head - you're {short_amount} gold short for a room.",
            ],
            
            # Sleep events
            'sleep_success': [
                "You retire to your room and get a good night's sleep.",
                "You drift off to sleep in your rented room, resting comfortably.",
            ],
            'sleep_failure': [
                "You need to rent a room before you can sleep here.",
                "The innkeeper points to the 'Rooms for Rent' sign. You'll need to pay first.",
            ],
            
            # Gambling events
            'gamble_win': [
                "You win {amount} gold at {game}!",
                "Lady luck smiles on you - {amount} gold added to your purse from {game}.",
            ],
            'gamble_lose': [
                "You lose {amount} gold at {game}.",
                "The house wins this round - {amount} gold gone at {game}.",
            ],
            'gamble_broke': [
                "You don't have enough gold to place that bet.",
                "The dealer eyes your empty coin purse and shakes their head.",
            ],
            
            # NPC events
            'npc_spawn': [
                "{npc_name} enters the tavern.",
                "The door creaks open as {npc_name} steps inside.",
            ],
            'npc_depart': [
                "{npc_name} leaves the tavern.",
                "With a nod, {npc_name} heads out the door.",
            ],
            'npc_talk': [
                "You chat with {npc_name} about {topic}.",
                "{npc_name} shares some thoughts about {topic} with you.",
            ],
        }
    
    def add_event(self, event_type: str, **kwargs) -> None:
        """Add a new event to the recent events list.
        
        Args:
            event_type: Type of event (e.g., 'rent_success', 'gamble_win')
            **kwargs: Additional data for the event
        """
        self.recent_events.append({
            'type': event_type,
            'data': kwargs,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_formatted_events(self) -> List[str]:
        """Get all recent events as formatted text.
        
        Returns:
            List of formatted event strings
        """
        formatted = []
        for event in self.recent_events:
            template = self._get_template(event['type'])
            if template:
                try:
                    formatted_text = template.format(**event['data'])
                    formatted.append(formatted_text)
                except (KeyError, ValueError) as e:
                    # Fallback to a simple message if formatting fails
                    formatted.append(f"Something happened: {event['type']}")
        
        self.recent_events = []  # Clear processed events
        return formatted
    
    def _get_template(self, event_type: str) -> Optional[str]:
        """Get a random template for the given event type."""
        templates = self._event_templates.get(event_type)
        if templates:
            return random.choice(templates)
        return None
    
    def clear_events(self) -> None:
        """Clear all recent events."""
        self.recent_events = []
