"""Pytest configuration and fixtures for The Living Rusted Tankard tests."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from core.game_state import GameState
from core.clock import GameClock
from core.room import RoomManager
from core.player import PlayerState, Inventory

# Core Fixtures

@pytest.fixture
def game_state():
    """Create a fresh game state for testing."""
    return GameState()

@pytest.fixture
def player():
    """Create a fresh player for testing."""
    return PlayerState(player_id="test_player", name="Test Player")

@pytest.fixture
def player_state():
    """Create a fresh player state for testing."""
    return PlayerState(player_id="test_player", name="Test Player")

@pytest.fixture
def inventory():
    """Create a fresh inventory for testing."""
    return Inventory()

@pytest.fixture
def game_clock():
    """Create a fresh game clock for testing."""
    return GameClock()

@pytest.fixture
def event_queue():
    """Create a fresh event queue for testing."""
    from core.event import EventQueue
    return EventQueue()

# Meta-Quest Fixtures

@pytest.fixture
def meta_quest_setup():
    """Set up a meta-quest test environment."""
    clock = GameClock()
    player = PlayerState(player_id="test_player", name="Test Player")
    room_manager = RoomManager()
    return {
        'clock': clock,
        'player': player,
        'room_manager': room_manager
    }

# Room and Economy Fixtures

@pytest.fixture
def room_manager():
    """Create a fresh room manager for testing."""
    return RoomManager()

@pytest.fixture
def player_with_gold():
    """Create a player with a specific amount of gold."""
    def _player_with_gold(amount):
        player = PlayerState()
        player.gold = amount
        return player
    return _player_with_gold

# Sleep Mechanics Fixtures


@pytest.fixture
def sleep_setup():
    """Set up a sleep test environment."""
    clock = GameClock()
    player = PlayerState()
    room_manager = RoomManager()
    return {
        'clock': clock,
        'player': player,
        'room_manager': room_manager
    }

# Mock Fixtures


@pytest.fixture
def mock_time():
    """Mock the time module for testing time-based functionality."""
    with patch('time.time') as mock_time:
        mock_time.return_value = 0  # Start at Unix epoch
        yield mock_time



@pytest.fixture
def mock_datetime():
    """Mock datetime for testing time-based functionality."""
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2023, 1, 1, 12, 0)  # Fixed time
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield mock_dt

