"""
Fantasy Calendar System for The Living Rusted Tankard.

This module provides natural time display to replace decimal time with immersive
fantasy time references like "Third bell past sunset" instead of "19.25 hours".

Integrates with existing GameClock system without breaking functionality.
"""

from typing import Dict, Tuple, Optional
from enum import Enum
from dataclasses import dataclass


class DisplayStyle(Enum):
    """Style for displaying time"""

    NATURAL = "natural"
    ATMOSPHERIC = "atmospheric"
    PRECISE = "precise"


class TimeOfDay(Enum):
    DEEP_NIGHT = "deep_night"
    EARLY_DAWN = "early_dawn"
    MORNING = "morning"
    MIDDAY = "midday"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class Season(Enum):
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"


@dataclass
class TavernTime:
    """Represents a specific moment in tavern time with all contextual information."""

    hour: int
    minute: int
    day_of_week: str
    day_of_month: int
    month: str
    season: Season
    time_of_day: TimeOfDay
    bell_count: int
    bell_period: str


class TavernCalendar:
    """Fantasy calendar system for immersive time display."""

    # Fantasy day names - evocative of tavern life
    DAYS_OF_WEEK = [
        "Moonday",  # Day 0 - quiet start to week
        "Forgeday",  # Day 1 - craftsmen work
        "Midweek",  # Day 2 - middle of week
        "Brewday",  # Day 3 - brewing and preparation
        "Marketday",  # Day 4 - trading and commerce
        "Revelday",  # Day 5 - celebration and festivities
        "Restday",  # Day 6 - day of rest
    ]

    # Fantasy month names - 12 months following natural cycles
    MONTHS = [
        "Frostmoon",  # January - deep winter
        "Thawmoon",  # February - winter's end
        "Plantmoon",  # March - spring planting
        "Bloomoon",  # April - flowers bloom
        "Sunmoon",  # May - warm spring
        "Harvestmoon",  # June - early harvest
        "Goldmoon",  # July - peak summer
        "Windmoon",  # August - late summer winds
        "Mistmoon",  # September - autumn mists
        "Fallmoon",  # October - leaves fall
        "Icemoon",  # November - first frost
        "Darkest Moon",  # December - deepest winter
    ]

    # Time periods for atmospheric descriptions
    TIME_PERIODS = {
        (0, 6): (TimeOfDay.DEEP_NIGHT, "Deep Night"),
        (6, 9): (TimeOfDay.EARLY_DAWN, "Early Dawn"),
        (9, 12): (TimeOfDay.MORNING, "Morning"),
        (12, 15): (TimeOfDay.MIDDAY, "Midday"),
        (15, 18): (TimeOfDay.AFTERNOON, "Afternoon"),
        (18, 21): (TimeOfDay.EVENING, "Evening"),
        (21, 24): (TimeOfDay.NIGHT, "Night"),
    }

    # Bell system: 8 bells per day, 3 hours each
    # Traditional tavern timekeeping
    BELL_PERIODS = {
        0: "Deep Night Bell",  # Midnight - 3 AM
        3: "Dawn Bell",  # 3 AM - 6 AM
        6: "Morning Bell",  # 6 AM - 9 AM
        9: "Second Morning Bell",  # 9 AM - Noon
        12: "Midday Bell",  # Noon - 3 PM
        15: "Afternoon Bell",  # 3 PM - 6 PM
        18: "Evening Bell",  # 6 PM - 9 PM
        21: "Night Bell",  # 9 PM - Midnight
    }

    # Season definitions (months 0-11 mapped to seasons)
    SEASON_MAP = {
        0: Season.WINTER,
        1: Season.WINTER,
        2: Season.SPRING,
        3: Season.SPRING,
        4: Season.SPRING,
        5: Season.SUMMER,
        6: Season.SUMMER,
        7: Season.SUMMER,
        8: Season.AUTUMN,
        9: Season.AUTUMN,
        10: Season.AUTUMN,
        11: Season.WINTER,
    }

    @classmethod
    def get_time_period(cls, hour: float) -> Tuple[TimeOfDay, str]:
        """Get the time of day period for a given hour."""
        hour_int = int(hour) % 24
        for (start, end), (time_of_day, description) in cls.TIME_PERIODS.items():
            if start <= hour_int < end:
                return time_of_day, description
        # Fallback for hour 24 edge case
        return TimeOfDay.DEEP_NIGHT, "Deep Night"

    @classmethod
    def get_bell_info(cls, hour: float) -> Tuple[int, str, str]:
        """Get bell count, period, and position for a given hour.

        Returns:
            (bell_count, bell_period, bell_position)
            - bell_count: Which bell within the period (1, 2, or 3)
            - bell_period: Name of the bell period
            - bell_position: Descriptive position ("early", "past", "late")
        """
        hour_int = int(hour) % 24
        minutes = int((hour % 1) * 60)

        # Find the bell period (every 3 hours)
        bell_period_start = (hour_int // 3) * 3
        bell_period_name = cls.BELL_PERIODS.get(bell_period_start, "Unknown Bell")

        # Calculate position within the 3-hour period
        hour_in_period = hour_int % 3
        minute_in_period = hour_in_period * 60 + minutes

        if minute_in_period < 30:
            return 1, bell_period_name, "early"
        elif minute_in_period < 90:
            return 1, bell_period_name, "past"
        elif minute_in_period < 120:
            return 2, bell_period_name, "early"
        elif minute_in_period < 150:
            return 2, bell_period_name, "past"
        else:
            return 3, bell_period_name, "late"

    @classmethod
    def get_fantasy_time(cls, game_time_hours: float, start_day: int = 1) -> TavernTime:
        """Convert game time hours to complete fantasy time information.

        Args:
            game_time_hours: Hours since game start (can be decimal)
            start_day: Starting day number (default 1)

        Returns:
            TavernTime object with all time information
        """
        # Calculate basic time components
        total_days = int(game_time_hours // 24)
        hour_of_day = game_time_hours % 24
        hour = int(hour_of_day)
        minute = int((hour_of_day % 1) * 60)

        # Calculate calendar information
        current_day = start_day + total_days
        day_of_week = cls.DAYS_OF_WEEK[current_day % 7]

        # Simple month/year calculation (30 days per month)
        days_since_start = current_day - 1
        month_index = (days_since_start // 30) % 12
        day_of_month = (days_since_start % 30) + 1
        month = cls.MONTHS[month_index]
        season = cls.SEASON_MAP[month_index]

        # Get time period and bell information
        time_of_day, _ = cls.get_time_period(hour_of_day)
        bell_count, bell_period, bell_position = cls.get_bell_info(hour_of_day)

        return TavernTime(
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month=month,
            season=season,
            time_of_day=time_of_day,
            bell_count=bell_count,
            bell_period=bell_period,
        )

    @classmethod
    def format_natural_time(
        cls, game_time_hours: float, style: str = "narrative"
    ) -> str:
        """Format time in a natural, immersive way.

        Args:
            game_time_hours: Hours since game start
            style: Format style - "narrative", "bell", "formal", or "short"

        Returns:
            Naturally formatted time string
        """
        tavern_time = cls.get_fantasy_time(game_time_hours)

        if style == "bell":
            # Bell-based time: "Second bell past evening"
            bell_count, bell_period, position = cls.get_bell_info(game_time_hours)

            # Convert bell period to simpler form
            period_simple = bell_period.replace(" Bell", "").lower()

            if position == "early":
                return f"Early {period_simple} bell"
            elif position == "past":
                if bell_count == 1:
                    return f"First bell past {period_simple.replace('second ', '')}"
                else:
                    return f"{cls._ordinal(bell_count)} bell past {period_simple.replace('second ', '')}"
            else:  # late
                return f"Late {period_simple} bell"

        elif style == "narrative":
            # Descriptive narrative time
            _, period_desc = cls.get_time_period(game_time_hours)
            if tavern_time.minute < 15:
                return f"{period_desc}"
            elif tavern_time.minute < 45:
                return f"Mid-{period_desc.lower()}"
            else:
                return f"Late {period_desc.lower()}"

        elif style == "formal":
            # Formal fantasy time with date
            return f"{tavern_time.day_of_week}, {tavern_time.day_of_month} {tavern_time.month}"

        elif style == "short":
            # Short atmospheric description
            _, period_desc = cls.get_time_period(game_time_hours)
            return period_desc

        else:
            # Default to bell time
            return cls.format_natural_time(game_time_hours, "bell")

    @classmethod
    def _ordinal(cls, n: int) -> str:
        """Convert number to ordinal string (1st, 2nd, 3rd, etc.)."""
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    @classmethod
    def get_atmospheric_description(
        cls, game_time_hours: float, weather: Optional[str] = None
    ) -> str:
        """Get rich atmospheric description of current time.

        Args:
            game_time_hours: Current game time
            weather: Optional weather condition

        Returns:
            Rich description suitable for LLM context or room descriptions
        """
        tavern_time = cls.get_fantasy_time(game_time_hours)
        time_of_day, period_desc = cls.get_time_period(game_time_hours)

        # Base atmospheric descriptions
        atmosphere_map = {
            TimeOfDay.DEEP_NIGHT: "The tavern is quiet in the deep of night, with only the crackling fire and distant sounds breaking the silence.",
            TimeOfDay.EARLY_DAWN: "Early dawn light filters through the windows as the tavern prepares for another day.",
            TimeOfDay.MORNING: "Morning light fills the tavern as patrons enjoy their breakfast and plan their day.",
            TimeOfDay.MIDDAY: "Bright midday sun streams through the windows, and the tavern bustles with activity.",
            TimeOfDay.AFTERNOON: "The afternoon brings a steady flow of patrons seeking refreshment and conversation.",
            TimeOfDay.EVENING: "Evening settles over the tavern as candles are lit and the day's stories are shared.",
            TimeOfDay.NIGHT: "Night has fallen, and the tavern glows with warm light as patrons gather for drinks and tales.",
        }

        base_description = atmosphere_map.get(
            time_of_day, "The tavern continues its timeless rhythm."
        )

        # Add weather if provided
        if weather:
            weather_additions = {
                "rain": " Rain patters against the windows, driving more people inside for warmth.",
                "snow": " Snow falls outside, making the tavern's warmth even more welcoming.",
                "storm": " A storm rages outside, but the tavern remains a safe haven.",
                "clear": " Clear skies outside complement the tavern's bright atmosphere.",
                "fog": " Fog shrouds the world outside, making the tavern feel like an island of warmth.",
            }
            base_description += weather_additions.get(weather.lower(), "")

        return base_description


def get_natural_time_display(game_time_hours: float, style: str = "bell") -> str:
    """Convenience function for getting natural time display.

    This is the main function other systems should use to replace decimal time.
    """
    return TavernCalendar.format_natural_time(game_time_hours, style)


def get_time_context_for_llm(
    game_time_hours: float, weather: Optional[str] = None
) -> str:
    """Get time context suitable for LLM prompts.

    Returns rich time and atmospheric information for LLM context.
    """
    tavern_time = TavernCalendar.get_fantasy_time(game_time_hours)
    natural_time = TavernCalendar.format_natural_time(game_time_hours, "bell")
    atmosphere = TavernCalendar.get_atmospheric_description(game_time_hours, weather)

    return f"Current time: {natural_time} on {tavern_time.day_of_week}. {atmosphere}"


# Example usage and testing
if __name__ == "__main__":
    # Test various times
    test_times = [6.25, 12.0, 14.75, 18.5, 22.1]

    print("=== Fantasy Calendar System Test ===")
    for time_hours in test_times:
        print(f"\nDecimal Time: {time_hours}")
        print(f"Bell Time: {get_natural_time_display(time_hours, 'bell')}")
        print(f"Narrative: {get_natural_time_display(time_hours, 'narrative')}")
        print(f"Formal: {get_natural_time_display(time_hours, 'formal')}")

        tavern_time = TavernCalendar.get_fantasy_time(time_hours)
        print(
            f"Full Info: {tavern_time.day_of_week}, {tavern_time.day_of_month} {tavern_time.month}"
        )
        print(f"LLM Context: {get_time_context_for_llm(time_hours, 'clear')}")

# Compatibility aliases for tests
FantasyCalendar = TavernCalendar
SeasonType = Season
