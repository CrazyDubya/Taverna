"""NPC fixtures for testing."""

import pytest
from typing import Dict, Any, List
from core.npc import NPC, NPCType, NPCDisposition
from core.reputation import ReputationManager


@pytest.fixture
def basic_npc():
    """Create a basic NPC for testing."""
    return NPC(
        id="test_npc",
        name="TestNPC",
        description="A test character",
        npc_type=NPCType.PATRON,
        current_room="main_hall"
    )


@pytest.fixture
def bartender_npc():
    """Create a bartender NPC."""
    npc = NPC(
        id="gareth",
        name="Gareth",
        description="The friendly tavern keeper",
        npc_type=NPCType.BARKEEP,
        disposition=NPCDisposition.FRIENDLY,
        current_room="main_hall"
    )
    return npc


@pytest.fixture
def merchant_npc():
    """Create a merchant NPC."""
    npc = NPC(
        id="tobias",
        name="Tobias",
        description="A traveling merchant",
        npc_type=NPCType.MERCHANT,
        disposition=NPCDisposition.NEUTRAL,
        current_room="main_hall"
    )
    return npc


@pytest.fixture
def guard_npc():
    """Create a guard NPC."""
    npc = NPC(
        id="captain_marcus",
        name="Captain Marcus",
        description="The tavern's security",
        npc_type=NPCType.GUARD,
        disposition=NPCDisposition.UNFRIENDLY,
        current_room="main_hall"
    )
    return npc


@pytest.fixture
def multiple_npcs():
    """Create multiple NPCs for testing."""
    return [
        NPC(
            id="gareth",
            name="Gareth",
            description="The friendly tavern keeper",
            npc_type=NPCType.BARKEEP,
            current_room="main_hall"
        ),
        NPC(
            id="tobias",
            name="Tobias",
            description="A traveling merchant",
            npc_type=NPCType.MERCHANT,
            current_room="main_hall"
        ),
        NPC(
            id="captain_marcus",
            name="Captain Marcus",
            description="The tavern's security",
            npc_type=NPCType.GUARD,
            current_room="main_hall"
        ),
        NPC(
            id="elena",
            name="Elena",
            description="A mysterious stranger",
            npc_type=NPCType.PATRON,
            current_room="main_hall"
        ),
    ]


@pytest.fixture
def npc_with_dialogue():
    """Create an NPC with dialogue options."""
    npc = NPC(
        id="chatty_pete",
        name="Chatty Pete",
        description="A talkative patron",
        npc_type=NPCType.PATRON,
        current_room="main_hall"
    )
    npc.conversation_topics = [
        "Tell me about the weather",
        "What's new in town?",
        "Buy me a drink",
    ]
    return npc


@pytest.fixture
def npc_with_inventory():
    """Create an NPC with inventory items."""
    npc = NPC(
        id="trader_sam",
        name="Trader Sam",
        description="A merchant with goods",
        npc_type=NPCType.MERCHANT,
        current_room="main_hall"
    )
    npc.inventory = [
        {"name": "healing_potion", "quantity": 3, "price": 25},
        {"name": "rope", "quantity": 1, "price": 10},
        {"name": "lantern", "quantity": 2, "price": 15},
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
            "stats": {"charisma": 15, "intelligence": 12},
        },
        {
            "name": "Mysterious Figure",
            "description": "A hooded stranger in the corner",
            "room_id": "main_hall",
            "disposition": "mysterious",
            "dialogue_state": "observing",
            "stats": {"charisma": 8, "intelligence": 18},
        },
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
                "outcome": "positive",
            },
            {
                "npc_name": "Tobias",
                "interaction_type": "trade",
                "timestamp": "2024-01-01T12:30:00",
                "outcome": "successful",
            },
        ]
    }
