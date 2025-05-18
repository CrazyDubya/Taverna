"""Tests for the NPC and NPCManager classes."""
import pytest
from unittest.mock import patch

class TestNPC:
    def test_npc_initialization(self):
        """Test that an NPC is initialized with the correct attributes."""
        from core.npc import NPC
        
        npc = NPC(
            id="test_npc",
            name="Test NPC",
            description="A test NPC",
            schedule=[(9, 17)],  # 9 AM to 5 PM
            departure_chance=0.5
        )
        
        assert npc.id == "test_npc"
        assert npc.name == "Test NPC"
        assert npc.schedule == [(9, 17)]
        assert npc.departure_chance == 0.5
        assert npc.present is False
        assert npc.last_seen_day == -1
    
    @pytest.mark.parametrize("hour,expected_present", [
        (8, False),   # Before schedule
        (12, True),   # During schedule
        (17, False),  # At end of schedule (exclusive)
        (20, False)   # After schedule
    ])
    def test_update_presence_during_schedule(self, hour, expected_present):
        """Test that NPC presence is updated correctly based on schedule."""
        from core.npc import NPC
        
        npc = NPC(
            id="worker",
            name="Worker",
            description="Works 9-5",
            schedule=[(9, 17)]
        )
        
        # Game time in hours (day 1 at specified hour)
        game_time = 24 + hour
        
        # First update should set presence
        npc.update_presence(game_time)
        assert npc.last_seen_day == 1
        
        # Second update on same day should be a no-op
        npc.present = not expected_present  # Flip to test it doesn't change
        npc.update_presence(game_time + 0.5)  # Same day, different hour
        assert npc.present == (not expected_present)  # Shouldn't have changed
        
        # Next day, should update again
        npc.update_presence(game_time + 24)  # Next day, same hour
        assert npc.last_seen_day == 2
        assert npc.present == expected_present
    
    @patch('random.random')
    def test_departure_chance(self, mock_random):
        """Test that NPCs can randomly decide to leave based on departure_chance."""
        from core.npc import NPC
        
        # Mock random to return 0.4 (below 0.5, so NPC stays)
        mock_random.return_value = 0.4
        
        npc = NPC(
            id="visitor",
            name="Visitor",
            description="Might leave",
            schedule=[(0, 24)],  # All day
            departure_chance=0.5  # 50% chance to leave
        )
        
        npc.update_presence(12.0)  # Middle of day 1
        assert npc.present is True  # Should be present (0.4 < 0.5)
        
        # Next day, mock random to return 0.6 (above 0.5, so NPC leaves)
        mock_random.return_value = 0.6
        npc.update_presence(36.0)  # Middle of day 2
        assert npc.present is False  # Should be gone (0.6 > 0.5)


class TestNPCManager:
    def test_add_and_get_npc(self, npc_manager):
        """Test adding and retrieving NPCs from the manager."""
        # Test getting existing NPC
        barkeep = npc_manager.get_npc("barkeep")
        assert barkeep is not None
        assert barkeep.name == "Old Tom"
        
        # Test getting non-existent NPC
        assert npc_manager.get_npc("nonexistent") is None
        
        # Test finding NPC by name
        sally = npc_manager.find_npc_by_name("sally")
        assert sally is not None
        assert sally.id == "patron1"
        
        # Test case-insensitive name search
        assert npc_manager.find_npc_by_name("OLD TOM") is not None
        
        # Test finding non-existent NPC by name
        assert npc_manager.find_npc_by_name("nobody") is None
    
    def test_update_all_npcs(self, npc_manager):
        """Test updating all NPCs' presence."""
        # Initially, no NPCs should be present
        assert len(npc_manager.get_present_npcs()) == 0
        
        # Update to noon - both NPCs should be in schedule
        npc_manager.update_all_npcs(12.0)  # Noon on day 1
        present_npcs = npc_manager.get_present_npcs()
        assert len(present_npcs) == 2
        assert {npc.id for npc in present_npcs} == {"barkeep", "patron1"}
        
        # Update to midnight - only barkeep should be present
        npc_manager.update_all_npcs(24.0)  # Midnight
        present_npcs = npc_manager.get_present_npcs()
        present_ids = {npc.id for npc in present_npcs}
        assert "barkeep" in present_ids
        assert "patron1" not in present_ids
        
        # Update to next day at same time - should be same result
        npc_manager.update_all_npcs(48.0)  # Next midnight
        present_npcs_tomorrow = npc_manager.get_present_npcs()
        assert {npc.id for npc in present_npcs_tomorrow} == {"barkeep"}
