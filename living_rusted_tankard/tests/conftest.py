"""Pytest configuration and fixtures for The Living Rusted Tankard tests."""

import pytest
from core.game_state import GameState
from models.player import PlayerState

@pytest.fixture
def game_state():
    """Create a fresh game state for testing."""
    return GameState()

@pytest.fixture
def player():
    """Create a fresh player for testing."""
    return PlayerState()

@pytest.fixture
def inventory():
    """Create a fresh inventory for testing."""
    from models.player import Inventory
    return Inventory()

@pytest.fixture
def game_clock():
    """Create a fresh game clock for testing."""
    from core.clock import GameClock
    return GameClock()

@pytest.fixture
def event_queue():
    """Create a fresh event queue for testing."""
    from core.event import EventQueue
    return EventQueue()
