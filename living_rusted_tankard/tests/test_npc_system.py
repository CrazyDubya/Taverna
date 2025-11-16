"""Tests for the NPC system."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.npc import NPC, NPCType, NPCDisposition, NPCManager
from core.items import Item


def test_npc_creation():
    """Test creating a basic NPC."""
    npc = NPC(
        id="test_npc",
        name="Test NPC",
        description="A test NPC",
        npc_type=NPCType.PATRON,
        disposition=NPCDisposition.NEUTRAL,
        schedule=[(9, 17)],  # 9 AM to 5 PM
        departure_chance=0.1,
        visit_frequency=0.9,
        gold=100,
    )

    assert npc.id == "test_npc"
    assert npc.name == "Test NPC"
    assert npc.npc_type == NPCType.PATRON
    assert npc.disposition == NPCDisposition.NEUTRAL
    assert npc.schedule == [(9, 17)]
    assert npc.departure_chance == 0.1
    assert npc.visit_frequency == 0.9
    assert npc.gold == 100
    assert not npc.is_present


def test_npc_update_presence():
    """Test updating NPC presence based on game time."""
    npc = NPC(
        id="test_npc",
        name="Test NPC",
        description="A test NPC",
        npc_type=NPCType.PATRON,
        schedule=[(9, 17)],  # 9 AM to 5 PM
        visit_frequency=1.0,  # Always visit when scheduled
    )

    # Test outside schedule (8 AM)
    npc.update_presence(8)
    assert not npc.is_present

    # Test inside schedule (10 AM)
    npc.update_presence(10)
    assert npc.is_present
    assert npc.last_visit_day == 0  # First visit

    # Test random departure (mock random to return lower than departure chance)
    npc.departure_chance = 1.0  # 100% chance to leave
    npc.update_presence(11)
    assert not npc.is_present


def test_npc_manager():
    """Test the NPC manager."""
    manager = NPCManager()

    # Get initial count of PATRON NPCs
    initial_patrons = len(manager.get_npcs_by_type(NPCType.PATRON))

    # Test adding an NPC
    npc = NPC(
        id="test_npc",
        name="Test NPC",
        description="A test NPC",
        npc_type=NPCType.PATRON,
        schedule=[(9, 17)],
        visit_frequency=1.0,
    )
    manager.add_npc(npc)

    # Test getting NPC by ID
    assert manager.get_npc("test_npc") is not None
    assert manager.get_npc("nonexistent") is None

    # Test finding NPC by name
    assert manager.find_npc_by_name("Test NPC") is not None
    assert manager.find_npc_by_name("Nonexistent") is None

    # Test getting NPCs by type (should be initial patrons + 1)
    assert len(manager.get_npcs_by_type(NPCType.PATRON)) == initial_patrons + 1

    # Test getting NPCs of a different type
    initial_barkeeps = len(manager.get_npcs_by_type(NPCType.BARKEEP))
    assert len(manager.get_npcs_by_type(NPCType.BARKEEP)) == initial_barkeeps


def test_npc_loader():
    """Test loading NPCs from JSON."""
    # Create a temporary directory with test data

    import tempfile
    import json
    import os

    test_data = {
        "npc_definitions": [
            {
                "id": "test_npc",
                "name": "Test NPC",
                "description": "A test NPC",
                "npc_type": "PATRON",
                "schedule": [[9, 17]],
                "departure_chance": 0.1,
                "visit_frequency": 0.9,
                "gold": 100,
                "inventory": [],
                "relationships": {},
                "conversation_topics": ["test"],
            }
        ]
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test data file
        test_file = os.path.join(temp_dir, "npcs.json")
        with open(test_file, "w") as f:
            json.dump(test_data, f)

        # Test loading NPCs
        manager = NPCManager(temp_dir)

        # Verify that our test NPC was loaded
        npc = manager.get_npc("test_npc")
        assert npc is not None, "Test NPC was not loaded"
        assert npc.name == "Test NPC"
        assert npc.npc_type == NPCType.PATRON
        assert npc.schedule == [(9, 17)]
        assert npc.visit_frequency == 0.9

        # Verify that the NPC was added to the manager
        assert "test_npc" in manager.npcs, "Test NPC was not added to NPC manager"


def test_npc_interactions():
    """Test NPC interactions."""
    npc = NPC(
        id="test_npc",
        name="Test NPC",
        description="A test NPC",
        npc_type=NPCType.PATRON,
        is_present=True,
    )

    # Test getting interactive NPCs
    manager = NPCManager()
    manager.add_npc(npc)

    interactive = manager.get_interactive_npcs()
    assert len(interactive) == 1
    assert interactive[0]["id"] == "test_npc"
    assert (
        len(interactive[0]["interactions"]) > 0
    )  # At least the default "Talk" interaction
