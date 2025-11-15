"""
Time Display System for The Living Rusted Tankard.

This module replaces decimal time displays throughout the application with natural,
immersive fantasy time descriptions. Integrates with existing GameClock system.

Usage:
    from core.time_display import format_time_for_display, format_time_for_npc

    # Replace decimal time displays
    display_time = format_time_for_display(game_clock.current_time_hours)
    npc_time = format_time_for_npc(game_clock.current_time_hours, npc.personality)
"""

from typing import Optional, Dict, Any
from .fantasy_calendar import TavernCalendar, get_natural_time_display, get_time_context_for_llm


class TimeDisplayManager:
    """Manages time display across different contexts and audiences."""

    # Display styles for different contexts
    DISPLAY_STYLES = {
        "ui_main": "bell",  # Main UI displays
        "ui_short": "short",  # Status bars, tooltips
        "npc_formal": "formal",  # Formal NPC speech
        "npc_casual": "narrative",  # Casual NPC conversation
        "room_desc": "narrative",  # Room descriptions
        "llm_context": "bell",  # LLM prompt context
    }

    # NPC personality-based time preferences
    NPC_TIME_STYLES = {
        "formal": "formal",  # Nobles, officials
        "casual": "narrative",  # Common folk
        "traditional": "bell",  # Barkeeps, old-timers
        "poetic": "narrative",  # Bards, artists
        "practical": "short",  # Merchants, guards
    }

    @classmethod
    def format_time_for_context(cls, game_time_hours: float, context: str = "ui_main") -> str:
        """Format time appropriate for the given context.

        Args:
            game_time_hours: Current game time in hours
            context: Display context (ui_main, ui_short, npc_formal, etc.)

        Returns:
            Appropriately formatted time string
        """
        style = cls.DISPLAY_STYLES.get(context, "bell")
        return get_natural_time_display(game_time_hours, style)

    @classmethod
    def format_time_for_npc(cls, game_time_hours: float, npc_personality: str = "casual") -> str:
        """Format time as an NPC would say it based on their personality.

        Args:
            game_time_hours: Current game time in hours
            npc_personality: NPC personality type

        Returns:
            Time string appropriate for the NPC's speaking style
        """
        style = cls.NPC_TIME_STYLES.get(npc_personality, "narrative")
        return get_natural_time_display(game_time_hours, style)

    @classmethod
    def get_time_greeting(cls, game_time_hours: float) -> str:
        """Get an appropriate time-based greeting.

        Returns greetings like "Good morning" based on current time.
        """
        TavernCalendar.get_fantasy_time(game_time_hours)

        greetings = {
            "Deep Night": "A late night to you",
            "Early Dawn": "Early dawn greetings",
            "Morning": "Good morning",
            "Midday": "Good day",
            "Afternoon": "Good afternoon",
            "Evening": "Good evening",
            "Night": "Good evening",
        }

        _, period_desc = TavernCalendar.get_time_period(game_time_hours)
        return greetings.get(period_desc, "Greetings")

    @classmethod
    def get_time_reference_for_scheduling(cls, game_time_hours: float, hours_ahead: int) -> str:
        """Get natural time reference for future scheduling.

        Args:
            game_time_hours: Current time
            hours_ahead: Hours in the future

        Returns:
            Natural reference like "later this evening" or "tomorrow morning"
        """
        future_time = game_time_hours + hours_ahead
        current_day = int(game_time_hours // 24)
        future_day = int(future_time // 24)

        _, future_period = TavernCalendar.get_time_period(future_time)

        if future_day == current_day:
            # Same day
            if hours_ahead <= 2:
                return "soon"
            elif hours_ahead <= 4:
                return f"later this {future_period.lower()}"
            else:
                return f"this {future_period.lower()}"
        elif future_day == current_day + 1:
            # Tomorrow
            return f"tomorrow {future_period.lower()}"
        else:
            # Multiple days
            days_ahead = future_day - current_day
            return f"in {days_ahead} days"


# Main interface functions for easy integration
def format_time_for_display(game_time_hours: float, context: str = "ui_main") -> str:
    """Main function to replace decimal time displays throughout the app.

    Use this function wherever you currently display time to users.
    """
    return TimeDisplayManager.format_time_for_context(game_time_hours, context)


def format_time_for_npc_speech(game_time_hours: float, npc_data: Optional[Dict[str, Any]] = None) -> str:
    """Format time for NPC dialogue and conversations.

    Args:
        game_time_hours: Current game time
        npc_data: Optional NPC data dictionary with personality info

    Returns:
        Time formatted as the NPC would naturally say it
    """
    personality = "casual"
    if npc_data:
        # Extract personality from NPC data
        npc_type = npc_data.get("npc_type", "").lower()
        if npc_type in ["noble", "guard"]:
            personality = "formal"
        elif npc_type in ["barkeep", "cook"]:
            personality = "traditional"
        elif npc_type in ["bard", "adventurer"]:
            personality = "poetic"
        elif npc_type in ["merchant", "thie"]:
            personality = "practical"

    return TimeDisplayManager.format_time_for_npc(game_time_hours, personality)


def get_time_context_for_room_description(game_time_hours: float, weather: Optional[str] = None) -> str:
    """Get atmospheric time description for room descriptions.

    This provides rich context for room examinations and scene setting.
    """
    return TavernCalendar.get_atmospheric_description(game_time_hours, weather)


def get_time_greeting(game_time_hours: float) -> str:
    """Get appropriate time-based greeting for NPCs."""
    return TimeDisplayManager.get_time_greeting(game_time_hours)


def get_scheduling_reference(game_time_hours: float, hours_ahead: int) -> str:
    """Get natural time reference for future events."""
    return TimeDisplayManager.get_time_reference_for_scheduling(game_time_hours, hours_ahead)


def replace_decimal_time_in_text(text: str, game_time_hours: float) -> str:
    """Replace any decimal time references in text with natural time.

    This can be used to clean up LLM responses or other text that might
    contain decimal time references.
    """
    import re

    # Pattern to match decimal time like "14.75" or "6.25 hours"
    decimal_time_pattern = r"\b(\d{1,2}\.\d+)(?:\s*hours?)?\b"

    def replace_match(match):
        try:
            decimal_time = float(match.group(1))
            if 0 <= decimal_time <= 24:  # Likely a time reference
                return format_time_for_display(decimal_time, "narrative")
        except ValueError:
            pass
        return match.group(0)  # Return original if not a valid time

    return re.sub(decimal_time_pattern, replace_match, text)


# Integration helpers for existing systems
class GameClockTimeDisplay:
    """Helper class to integrate natural time with existing GameClock."""

    @staticmethod
    def get_formatted_time(game_clock) -> str:
        """Get formatted time from a GameClock instance."""
        return format_time_for_display(game_clock.current_time_hours)

    @staticmethod
    def get_atmospheric_time(game_clock, weather: Optional[str] = None) -> str:
        """Get atmospheric time description from GameClock."""
        return get_time_context_for_room_description(game_clock.current_time_hours, weather)

    @staticmethod
    def get_llm_time_context(game_clock, weather: Optional[str] = None) -> str:
        """Get time context suitable for LLM prompts."""
        return get_time_context_for_llm(game_clock.current_time_hours, weather)


# Backward compatibility helpers
def convert_decimal_to_natural(decimal_time: float) -> str:
    """Convert decimal time to natural time display.

    This function provides backward compatibility for any code that
    currently uses decimal time formatting.
    """
    return format_time_for_display(decimal_time)


def get_bell_time(decimal_time: float) -> str:
    """Get bell-based time display (primary tavern timekeeping)."""
    return format_time_for_display(decimal_time, "ui_main")


def get_narrative_time(decimal_time: float) -> str:
    """Get narrative time display for atmospheric descriptions."""
    return format_time_for_display(decimal_time, "npc_casual")


# Testing and validation
if __name__ == "__main__":
    print("=== Time Display System Test ===")

    test_times = [6.25, 9.0, 12.0, 14.75, 18.5, 22.1]
    contexts = ["ui_main", "ui_short", "npc_formal", "npc_casual"]

    for time_val in test_times:
        print(f"\n--- Testing time: {time_val} ---")
        for context in contexts:
            display = format_time_for_display(time_val, context)
            print(f"{context:12}: {display}")

        # Test NPC speech
        npc_speech = format_time_for_npc_speech(time_val, {"npc_type": "BARKEEP"})
        print(f"{'barkeep':12}: {npc_speech}")

        # Test greeting
        greeting = get_time_greeting(time_val)
        print(f"{'greeting':12}: {greeting}")

    print("\n--- Testing text replacement ---")
    test_text = "It's currently 14.75 hours and the meeting is at 18.5."
    replaced = replace_decimal_time_in_text(test_text, 0)
    print(f"Original: {test_text}")
    print(f"Natural:  {replaced}")
