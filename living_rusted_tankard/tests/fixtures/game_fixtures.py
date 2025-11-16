"""Game state fixtures for testing."""

import pytest
from typing import Dict, Any, List
from core.game_state import GameState
from core.player import Player
from core.room import Room
from core.npc import NPC
from core.items import Item
from core.clock import GameClock
from core.economy import Economy


@pytest.fixture
def basic_game_state():
    """Create a basic game state for testing."""
    game_state = GameState()
    game_state.initialize()
    return game_state


@pytest.fixture
def game_state_with_player():
    """Create a game state with a player."""
    game_state = GameState()
    game_state.initialize()

    player = Player("TestPlayer")
    player.gold = 100
    game_state.add_player(player)

    return game_state


@pytest.fixture
def game_state_with_npcs():
    """Create a game state with NPCs."""
    game_state = GameState()
    game_state.initialize()

    # Add some test NPCs
    npc1 = NPC("Bartender", "The friendly tavern keeper", room_id="main_hall")
    npc2 = NPC("Merchant", "A traveling trader", room_id="main_hall")

    game_state.add_npc(npc1)
    game_state.add_npc(npc2)

    return game_state


@pytest.fixture
def complete_game_state():
    """Create a complete game state with player, NPCs, and items."""
    game_state = GameState()
    game_state.initialize()

    # Add player
    player = Player("TestPlayer")
    player.gold = 100
    game_state.add_player(player)

    # Add NPCs
    npc1 = NPC("Bartender", "The friendly tavern keeper", room_id="main_hall")
    npc2 = NPC("Merchant", "A traveling trader", room_id="main_hall")
    game_state.add_npc(npc1)
    game_state.add_npc(npc2)

    # Add items
    item1 = Item("ale", "A frothy mug of ale", 5)
    item2 = Item("bread", "Fresh baked bread", 2)
    game_state.add_item(item1)
    game_state.add_item(item2)

    return game_state


@pytest.fixture
def game_clock():
    """Create a game clock for testing."""
    return GameClock()


@pytest.fixture
def economy():
    """Create an economy system for testing."""
    return Economy()


@pytest.fixture
def sample_room():
    """Create a sample room for testing."""
    room = Room(
        "main_hall",
        "The Main Hall",
        "A cozy tavern hall with wooden tables and a warm fireplace.",
    )
    return room


@pytest.fixture
def sample_items():
    """Create sample items for testing."""
    return [
        Item("ale", "A frothy mug of ale", 5),
        Item("bread", "Fresh baked bread", 2),
        Item("cheese", "Aged tavern cheese", 3),
        Item("wine", "Fine vintage wine", 10),
    ]


@pytest.fixture
def sample_game_data():
    """Create sample game data dictionary."""
    return {
        "player": {
            "name": "TestPlayer",
            "gold": 100,
            "location": "main_hall",
            "inventory": [],
        },
        "npcs": [
            {
                "name": "Bartender",
                "description": "The friendly tavern keeper",
                "room_id": "main_hall",
                "disposition": "friendly",
            }
        ],
        "rooms": [
            {
                "id": "main_hall",
                "name": "The Main Hall",
                "description": "A cozy tavern hall",
            }
        ],
        "time": {"hour": 12, "day": 1, "season": "spring"},
    }
