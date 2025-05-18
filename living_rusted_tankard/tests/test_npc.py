"""Tests for the NPC and NPCManager classes."""

import pytest
from unittest.mock import patch


@pytest.fixture
def npc_manager():

    from core.npc import NPCManager
    return NPCManager()


class TestNPC:

    def test_npc_initialization(self):
        """Test that an NPC is initialized with the correct attributes."""

        from core.npc import NPC
        from core.npc import NPCType

        npc = NPC(
            id="test_npc",
            name="Test NPC",
            description="A test NPC",
            npc_type=NPCType.PATRON,
            schedule=[(9, 17)],  # 9 AM to 5 PM
            departure_chance=0.5
        )

        assert npc.id == "test_npc"
        assert npc.name == "Test NPC"
        assert npc.schedule == [(9, 17)]
        assert npc.departure_chance == 0.5
        assert npc.is_present is False
        assert npc.last_visit_day == -1

    @pytest.mark.parametrize("hour, expected_present", [
        (8, False),   # Before schedule
        (12, True),   # During schedule
        (17, False),  # At end of schedule (exclusive)
        (20, False)   # After schedule
    ])
    def test_update_presence_during_schedule(self, hour, expected_present):
        """Test that NPC presence is updated correctly based on schedule."""

        from core.npc import NPC, NPCType

        npc = NPC(
            id=f"worker_{hour}",
            name="Worker",
            description="Works 9-5",
            npc_type=NPCType.PATRON,
            schedule=[(9, 17)],
            visit_frequency=1.0  # Always visit when in schedule
        )

        # Game time in hours (day 1 at specified hour)
        game_time = 24 + hour

        # Update presence
        npc.update_presence(game_time)

        # Check if NPC should be present based on schedule
        is_within_schedule = 9 <= (hour % 24) < 17
        assert npc.is_present == (is_within_schedule and expected_present)

    @patch('random.random')
    def test_departure_chance(self, mock_random):
        """Test that NPCs can randomly decide to leave based on departure_chance."""

        from core.npc import NPC, NPCType

        # Set up the mock to return values in sequence
        mock_random.side_effect = [0.1, 0.6, 0.1, 0.4]

        # Create an NPC with a 50% departure chance
        npc = NPC(
            id="test_npc",
            name="Test NPC",
            description="Test departure chance",
            npc_type=NPCType.PATRON,
            schedule=[(0, 24)],  # All day
            departure_chance=0.5,  # 50% chance to leave
            visit_frequency=1.0    # Always visit when in schedule
        )

        # First update - should be present (uses first mock value 0.1 for visit check)
        npc.update_presence(12.0)
        assert npc.is_present is True

        # Second update with high random value (0.6) - should stay (0.6 > 0.5)
        npc.update_presence(12.1)
        assert npc.is_present is True

        # Create another NPC for testing departure
        npc2 = NPC(
            id="test_npc2",
            name="Test NPC 2",
            description="Test departure chance 2",
            npc_type=NPCType.PATRON,
            schedule=[(0, 24)],  # All day
            departure_chance=0.5,  # 50% chance to leave
            visit_frequency=1.0    # Always visit when in schedule
        )

        # First update - should be present (uses third mock value 0.1 for visit check)
        npc2.update_presence(12.0)
        assert npc2.is_present is True

        # Second update with low random value (0.4) - should leave (0.4 < 0.5)
        npc2.update_presence(12.1)
        assert npc2.is_present is False


class TestNPCManager:

    def test_add_and_get_npc(self, npc_manager):
        """Test adding and retrieving NPCs from the manager."""

        from core.npc import NPC, NPCType

        # Create a test NPC
        test_npc = NPC(
            id="test_npc",
            name="Test NPC",
            description="A test NPC",
            npc_type=NPCType.PATRON,
            schedule=[(9, 17)],
            visit_frequency=1.0
        )

        # Add NPC to manager
        npc_manager.add_npc(test_npc)

        # Test getting the NPC by ID
        retrieved_npc = npc_manager.get_npc("test_npc")
        assert retrieved_npc is not None
        assert retrieved_npc.name == "Test NPC"
        assert retrieved_npc.id == "test_npc"

        # Test getting non-existent NPC
        assert npc_manager.get_npc("nonexistent") is None

        # Test finding NPC by name (case-insensitive)
        found_npc = npc_manager.find_npc_by_name("test npc")
        assert found_npc is not None
        assert found_npc.id == "test_npc"

        # Test finding non-existent NPC by name
        assert npc_manager.find_npc_by_name("nobody") is None

    def test_update_all_npcs(self, npc_manager):
        """Test updating all NPCs' presence."""

        from core.npc import NPC, NPCType

        # Create test NPCs with different schedules
        day_npc = NPC(
            id="day_npc",
            name="Day NPC",
            description="Works during the day",
            npc_type=NPCType.PATRON,
            schedule=[(9, 17)],  # 9 AM to 5 PM
            visit_frequency=1.0,
            departure_chance=0.0  # Never leave once arrived
        )

        night_npc = NPC(
            id="night_npc",
            name="Night NPC",
            description="Works at night",
            npc_type=NPCType.PATRON,
            schedule=[(20, 4)],  # 8 PM to 4 AM
            visit_frequency=1.0,
            departure_chance=0.0  # Never leave once arrived
        )

        # Add NPCs to manager
        npc_manager.add_npc(day_npc)
        npc_manager.add_npc(night_npc)

        # Update to noon - day NPC should be present
        npc_manager.update_all_npcs(12.0)  # Noon
        present_npcs = [npc.id for npc in npc_manager.get_present_npcs()]
        assert "day_npc" in present_npcs
        assert "night_npc" not in present_npcs

        # Update to 10 PM - night NPC should be present
        npc_manager.update_all_npcs(22.0)  # 10 PM
        present_npcs = [npc.id for npc in npc_manager.get_present_npcs()]
        assert "day_npc" not in present_npcs
        assert "night_npc" in present_npcs
