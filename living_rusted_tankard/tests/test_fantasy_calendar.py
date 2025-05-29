"""Test fantasy calendar system."""
import pytest
from unittest.mock import Mock

from tests.utils.assertion_helpers import assert_string_contains_all

from core.fantasy_calendar import (
    FantasyCalendar, SeasonType, DisplayStyle,
    CalendarEvent, get_season_from_month
)
from core.clock import GameTime


class TestFantasyCalendar:
    """Test FantasyCalendar functionality."""
    
    def test_fantasy_calendar_initialization(self):
        """Test FantasyCalendar initializes correctly."""
        calendar = FantasyCalendar()
        
        assert calendar is not None
        assert len(calendar.month_names) == 12
        assert len(calendar.season_descriptions) == 4
        assert calendar.days_per_month == 30
        assert calendar.hours_per_day == 24
    
    def test_month_names(self):
        """Test fantasy month names are defined."""
        calendar = FantasyCalendar()
        
        expected_months = [
            "Frosthold", "Thawmoon", "Greenvale", "Bloomtide",
            "Suncrest", "Harvestmoon", "Goldleaf", "Dimmerfall",
            "Frostwind", "Shadowmere", "Iceveil", "Starfall"
        ]
        
        assert calendar.month_names == expected_months
    
    def test_season_calculation(self):
        """Test season calculation from month."""
        calendar = FantasyCalendar()
        
        # Test each season
        assert calendar.get_season(1) == SeasonType.WINTER  # Frosthold
        assert calendar.get_season(3) == SeasonType.SPRING  # Greenvale
        assert calendar.get_season(6) == SeasonType.SUMMER  # Harvestmoon
        assert calendar.get_season(9) == SeasonType.AUTUMN  # Frostwind
        assert calendar.get_season(12) == SeasonType.WINTER  # Starfall
    
    def test_season_descriptions(self):
        """Test season descriptions."""
        calendar = FantasyCalendar()
        
        descriptions = calendar.season_descriptions
        
        assert "winter" in descriptions[SeasonType.WINTER].lower()
        assert "spring" in descriptions[SeasonType.SPRING].lower()
        assert "summer" in descriptions[SeasonType.SUMMER].lower()
        assert "autumn" in descriptions[SeasonType.AUTUMN].lower()
    
    def test_time_display_natural(self):
        """Test natural time display style."""
        calendar = FantasyCalendar()
        game_time = GameTime(hour=14, day=15, month=6, year=2)
        
        display = calendar.format_time(game_time, DisplayStyle.NATURAL)
        
        # Should contain fantasy elements
        assert_string_contains_all(display, ["Harvestmoon", "15th"])
        assert "bell" in display.lower() or "hour" in display.lower()
    
    def test_time_display_atmospheric(self):
        """Test atmospheric time display style."""
        calendar = FantasyCalendar()
        
        # Test morning time
        morning_time = GameTime(hour=7, day=5, month=3, year=1)
        morning_display = calendar.format_time(morning_time, DisplayStyle.ATMOSPHERIC)
        
        assert "dawn" in morning_display.lower() or "morning" in morning_display.lower()
        
        # Test evening time
        evening_time = GameTime(hour=19, day=5, month=3, year=1)
        evening_display = calendar.format_time(evening_time, DisplayStyle.ATMOSPHERIC)
        
        assert "dusk" in evening_display.lower() or "evening" in evening_display.lower()
    
    def test_time_display_precise(self):
        """Test precise time display style."""
        calendar = FantasyCalendar()
        game_time = GameTime(hour=14, day=15, month=6, year=2, minute=30)
        
        display = calendar.format_time(game_time, DisplayStyle.PRECISE)
        
        # Should contain exact numbers
        assert "14" in display or "2" in display  # Hour in 24h or 12h format
        assert "30" in display  # Minutes
        assert "15" in display  # Day
        assert "Harvestmoon" in display  # Month name
    
    def test_time_of_day_classification(self):
        """Test time of day classification."""
        calendar = FantasyCalendar()
        
        # Test different times of day
        assert calendar.get_time_of_day(5) == "dawn"
        assert calendar.get_time_of_day(10) == "morning"
        assert calendar.get_time_of_day(14) == "afternoon"
        assert calendar.get_time_of_day(19) == "evening"
        assert calendar.get_time_of_day(23) == "night"
        assert calendar.get_time_of_day(2) == "deep night"
    
    def test_day_ordinal_formatting(self):
        """Test day ordinal formatting (1st, 2nd, 3rd, etc.)."""
        calendar = FantasyCalendar()
        
        assert calendar.format_day_ordinal(1) == "1st"
        assert calendar.format_day_ordinal(2) == "2nd"
        assert calendar.format_day_ordinal(3) == "3rd"
        assert calendar.format_day_ordinal(4) == "4th"
        assert calendar.format_day_ordinal(11) == "11th"
        assert calendar.format_day_ordinal(21) == "21st"
        assert calendar.format_day_ordinal(22) == "22nd"
        assert calendar.format_day_ordinal(23) == "23rd"
    
    def test_bell_system(self):
        """Test fantasy bell time system."""
        calendar = FantasyCalendar()
        
        # Test bell conversion
        assert calendar.hour_to_bells(0) == "Midnight Bell"
        assert calendar.hour_to_bells(6) == "First Bell"
        assert calendar.hour_to_bells(12) == "High Bell"
        assert calendar.hour_to_bells(18) == "Evening Bell"
        
        # Test partial hours
        bell_time = calendar.format_bell_time(14, 30)
        assert "bell" in bell_time.lower()
        assert "half" in bell_time.lower() or "30" in bell_time


class TestCalendarEvent:
    """Test calendar event functionality."""
    
    def test_calendar_event_creation(self):
        """Test creating calendar events."""
        event = CalendarEvent(
            name="Harvest Festival",
            month=7,  # Goldleaf
            day=15,
            duration_days=3,
            description="Annual celebration of the harvest"
        )
        
        assert event.name == "Harvest Festival"
        assert event.month == 7
        assert event.day == 15
        assert event.duration_days == 3
        assert "harvest" in event.description.lower()
    
    def test_event_date_range(self):
        """Test event date range calculation."""
        event = CalendarEvent(
            name="Winter Solstice",
            month=1,
            day=1,
            duration_days=1
        )
        
        date_range = event.get_date_range()
        assert date_range["start_month"] == 1
        assert date_range["start_day"] == 1
        assert date_range["end_month"] == 1
        assert date_range["end_day"] == 1
    
    def test_multi_day_event(self):
        """Test multi-day event spanning."""
        event = CalendarEvent(
            name="Spring Fair",
            month=3,
            day=28,  # Near end of month
            duration_days=5  # Should span into next month
        )
        
        date_range = event.get_date_range()
        assert date_range["start_month"] == 3
        assert date_range["start_day"] == 28
        # Should handle month rollover correctly
    
    def test_event_occurs_on_date(self):
        """Test checking if event occurs on specific date."""
        event = CalendarEvent(
            name="Test Event",
            month=5,
            day=10,
            duration_days=3
        )
        
        # Should occur on event days
        assert event.occurs_on_date(5, 10) is True
        assert event.occurs_on_date(5, 11) is True
        assert event.occurs_on_date(5, 12) is True
        
        # Should not occur on other days
        assert event.occurs_on_date(5, 9) is False
        assert event.occurs_on_date(5, 13) is False
        assert event.occurs_on_date(4, 10) is False


class TestSeasonalEffects:
    """Test seasonal effects and atmosphere."""
    
    def test_seasonal_atmosphere(self):
        """Test seasonal atmosphere descriptions."""
        calendar = FantasyCalendar()
        
        # Test each season's atmosphere
        winter_atmo = calendar.get_seasonal_atmosphere(SeasonType.WINTER)
        spring_atmo = calendar.get_seasonal_atmosphere(SeasonType.SPRING)
        summer_atmo = calendar.get_seasonal_atmosphere(SeasonType.SUMMER)
        autumn_atmo = calendar.get_seasonal_atmosphere(SeasonType.AUTUMN)
        
        assert "cold" in winter_atmo.lower() or "frost" in winter_atmo.lower()
        assert "bloom" in spring_atmo.lower() or "fresh" in spring_atmo.lower()
        assert "warm" in summer_atmo.lower() or "sun" in summer_atmo.lower()
        assert "fall" in autumn_atmo.lower() or "harvest" in autumn_atmo.lower()
    
    def test_weather_by_season(self):
        """Test weather patterns by season."""
        calendar = FantasyCalendar()
        
        winter_weather = calendar.get_seasonal_weather(SeasonType.WINTER)
        summer_weather = calendar.get_seasonal_weather(SeasonType.SUMMER)
        
        assert isinstance(winter_weather, list)
        assert isinstance(summer_weather, list)
        assert len(winter_weather) > 0
        assert len(summer_weather) > 0
        
        # Winter should have cold weather options
        winter_words = " ".join(winter_weather).lower()
        assert any(word in winter_words for word in ["snow", "frost", "cold", "ice"])
        
        # Summer should have warm weather options
        summer_words = " ".join(summer_weather).lower()
        assert any(word in summer_words for word in ["sun", "warm", "clear", "hot"])
    
    def test_daylight_hours(self):
        """Test daylight hours vary by season."""
        calendar = FantasyCalendar()
        
        winter_daylight = calendar.get_daylight_hours(SeasonType.WINTER)
        summer_daylight = calendar.get_daylight_hours(SeasonType.SUMMER)
        
        # Summer should have more daylight than winter
        assert summer_daylight > winter_daylight
        assert winter_daylight >= 6  # Minimum reasonable daylight
        assert summer_daylight <= 18  # Maximum reasonable daylight


class TestCalendarIntegration:
    """Test calendar integration with game systems."""
    
    def test_calendar_with_game_time(self):
        """Test calendar integration with GameTime."""
        calendar = FantasyCalendar()
        game_time = GameTime(hour=15, day=20, month=8, year=3)
        
        # Should provide comprehensive time information
        time_info = calendar.get_time_info(game_time)
        
        assert "month_name" in time_info
        assert "season" in time_info
        assert "time_of_day" in time_info
        assert "day_ordinal" in time_info
        
        assert time_info["month_name"] == "Dimmerfall"
        assert time_info["season"] == SeasonType.AUTUMN
        assert time_info["time_of_day"] == "afternoon"
    
    def test_calendar_events_integration(self):
        """Test calendar events with game time."""
        calendar = FantasyCalendar()
        
        # Add some events
        harvest_festival = CalendarEvent(
            name="Harvest Festival",
            month=7,
            day=1,
            duration_days=7
        )
        
        winter_solstice = CalendarEvent(
            name="Winter Solstice",
            month=12,
            day=21,
            duration_days=1
        )
        
        calendar.add_event(harvest_festival)
        calendar.add_event(winter_solstice)
        
        # Test event lookup
        harvest_time = GameTime(hour=12, day=5, month=7, year=1)
        active_events = calendar.get_active_events(harvest_time)
        
        assert len(active_events) == 1
        assert active_events[0].name == "Harvest Festival"
        
        # Test no events
        normal_time = GameTime(hour=12, day=15, month=5, year=1)
        no_events = calendar.get_active_events(normal_time)
        
        assert len(no_events) == 0
    
    def test_calendar_narrative_integration(self):
        """Test calendar integration with narrative systems."""
        calendar = FantasyCalendar()
        game_time = GameTime(hour=22, day=31, month=10, year=1)  # Late night, Shadowmere
        
        narrative_context = calendar.get_narrative_context(game_time)
        
        assert "atmosphere" in narrative_context
        assert "time_description" in narrative_context
        assert "seasonal_mood" in narrative_context
        
        # Late night in autumn should be atmospheric
        atmosphere = narrative_context["atmosphere"].lower()
        assert any(word in atmosphere for word in ["dark", "shadow", "mysterious", "quiet"])


class TestCalendarUtilities:
    """Test calendar utility functions."""
    
    def test_get_season_from_month_function(self):
        """Test standalone season calculation function."""
        assert get_season_from_month(1) == SeasonType.WINTER
        assert get_season_from_month(4) == SeasonType.SPRING
        assert get_season_from_month(7) == SeasonType.SUMMER
        assert get_season_from_month(10) == SeasonType.AUTUMN
    
    def test_time_comparison(self):
        """Test time comparison utilities."""
        calendar = FantasyCalendar()
        
        time1 = GameTime(hour=10, day=5, month=3, year=1)
        time2 = GameTime(hour=15, day=5, month=3, year=1)
        time3 = GameTime(hour=10, day=6, month=3, year=1)
        
        # Same day comparison
        assert calendar.is_same_day(time1, time2) is True
        assert calendar.is_same_day(time1, time3) is False
        
        # Time difference calculation
        diff = calendar.time_difference(time1, time2)
        assert diff["hours"] == 5
        assert diff["days"] == 0
    
    def test_calendar_validation(self):
        """Test calendar validation methods."""
        calendar = FantasyCalendar()
        
        # Valid dates
        assert calendar.is_valid_date(1, 1) is True
        assert calendar.is_valid_date(15, 6) is True
        assert calendar.is_valid_date(30, 12) is True
        
        # Invalid dates
        assert calendar.is_valid_date(0, 1) is False
        assert calendar.is_valid_date(31, 1) is False  # Only 30 days per month
        assert calendar.is_valid_date(15, 13) is False  # Only 12 months
        assert calendar.is_valid_date(15, 0) is False
    
    def test_calendar_serialization(self):
        """Test calendar serialization."""
        calendar = FantasyCalendar()
        
        # Add an event
        event = CalendarEvent(name="Test Event", month=5, day=10, duration_days=1)
        calendar.add_event(event)
        
        # Serialize
        serialized = calendar.to_dict()
        
        assert "month_names" in serialized
        assert "events" in serialized
        assert len(serialized["events"]) == 1
        
        # Deserialize
        new_calendar = FantasyCalendar.from_dict(serialized)
        assert len(new_calendar.events) == 1
        assert new_calendar.events[0].name == "Test Event"


class TestCalendarEdgeCases:
    """Test calendar edge cases."""
    
    def test_month_boundary_events(self):
        """Test events that cross month boundaries."""
        calendar = FantasyCalendar()
        
        # Event that starts near end of month
        event = CalendarEvent(
            name="Month Boundary Event",
            month=6,
            day=29,
            duration_days=5  # Should extend into next month
        )
        
        calendar.add_event(event)
        
        # Test dates in both months
        end_of_month = GameTime(hour=12, day=30, month=6, year=1)
        start_of_next = GameTime(hour=12, day=2, month=7, year=1)
        
        events1 = calendar.get_active_events(end_of_month)
        events2 = calendar.get_active_events(start_of_next)
        
        assert len(events1) == 1
        assert len(events2) == 1
        assert events1[0].name == "Month Boundary Event"
        assert events2[0].name == "Month Boundary Event"
    
    def test_year_boundary_events(self):
        """Test events that cross year boundaries."""
        calendar = FantasyCalendar()
        
        # Event that starts in December and continues into next year
        event = CalendarEvent(
            name="New Year Event",
            month=12,
            day=30,
            duration_days=3
        )
        
        calendar.add_event(event)
        
        # Test dates in both years
        end_of_year = GameTime(hour=12, day=30, month=12, year=1)
        start_of_next_year = GameTime(hour=12, day=1, month=1, year=2)
        
        events1 = calendar.get_active_events(end_of_year)
        events2 = calendar.get_active_events(start_of_next_year)
        
        assert len(events1) == 1
        assert len(events2) == 1
    
    def test_extreme_time_values(self):
        """Test calendar with extreme time values."""
        calendar = FantasyCalendar()
        
        # Very late in a very high year
        extreme_time = GameTime(hour=23, day=30, month=12, year=9999)
        
        # Should still work
        time_info = calendar.get_time_info(extreme_time)
        assert time_info["month_name"] == "Starfall"
        assert time_info["season"] == SeasonType.WINTER
        
        # Very early time
        early_time = GameTime(hour=0, day=1, month=1, year=1)
        early_info = calendar.get_time_info(early_time)
        assert early_info["month_name"] == "Frosthold"