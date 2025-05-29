"""NPC fixtures for testing."""

import pytest
from typing import Dict, Any, List
from core.npc import NPC
from core.reputation import ReputationManager


@pytest.fixture
def basic_npc():
    """Create a basic NPC for testing."""
    return NPC("TestNPC", "A test character", room_id="main_hall")


@pytest.fixture
def bartender_npc():
    """Create a bartender NPC."""
    npc = NPC("Gareth", "The friendly tavern keeper", room_id="main_hall")
    npc.disposition = "friendly"
    npc.dialogue_state = "greeting"
    return npc


@pytest.fixture
def merchant_npc():
    """Create a merchant NPC."""
    npc = NPC("Tobias", "A traveling merchant", room_id="main_hall")
    npc.disposition = "neutral"
    npc.dialogue_state = "trading"
    return npc


@pytest.fixture
def guard_npc():
    """Create a guard NPC."""
    npc = NPC("Captain Marcus", "The tavern's security", room_id="main_hall")
    npc.disposition = "suspicious"
    npc.dialogue_state = "watching"
    return npc


@pytest.fixture
def multiple_npcs():
    """Create multiple NPCs for testing."""
    return [
        NPC("Gareth", "The friendly tavern keeper", room_id="main_hall"),
        NPC("Tobias", "A traveling merchant", room_id="main_hall"),
        NPC("Captain Marcus", "The tavern's security", room_id="main_hall"),
        NPC("Elena", "A mysterious stranger", room_id="main_hall")
    ]


@pytest.fixture
def npc_with_dialogue():
    """Create an NPC with dialogue options."""
    npc = NPC("Chatty Pete", "A talkative patron", room_id="main_hall")
    npc.dialogue_options = [
        "Tell me about the weather",
        "What's new in town?",
        "Buy me a drink"
    ]
    return npc


@pytest.fixture
def npc_with_inventory():
    """Create an NPC with inventory items."""
    npc = NPC("Trader Sam", "A merchant with goods", room_id="main_hall")
    npc.inventory = [
        {"name": "healing_potion", "quantity": 3, "price": 25},
        {"name": "rope", "quantity": 1, "price": 10},
        {"name": "lantern", "quantity": 2, "price": 15}
    ]
    return npc


@pytest.fixture
def reputation_manager():
    """Create a reputation manager for NPC testing."""
    return ReputationManager()


@pytest.fixture
def npc_data_samples():
    """Create sample NPC data for testing."""
    return [
        {
            "name": "Gareth",
            "description": "The friendly tavern keeper",
            "room_id": "main_hall",
            "disposition": "friendly",
            "dialogue_state": "greeting",
            "stats": {"charisma": 15, "intelligence": 12}
        },
        {
            "name": "Mysterious Figure",
            "description": "A hooded stranger in the corner",
            "room_id": "main_hall",
            "disposition": "mysterious",
            "dialogue_state": "observing",
            "stats": {"charisma": 8, "intelligence": 18}
        }
    ]


@pytest.fixture
def npc_interaction_history():
    """Create sample NPC interaction history."""
    return {
        "player_interactions": [
            {
                "npc_name": "Gareth",
                "interaction_type": "dialogue",
                "timestamp": "2024-01-01T12:00:00",
                "outcome": "positive"
            },
            {
                "npc_name": "Tobias",
                "interaction_type": "trade",
                "timestamp": "2024-01-01T12:30:00",
                "outcome": "successful"
            }
        ]
    }