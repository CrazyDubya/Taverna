"""Integration tests for core game components."""
import pytest
from unittest.mock import patch
from core import GameState, PlayerState, NPC, NPCManager, Economy

def test_game_state_initialization():
    """Test that the game state initializes with all components."""
    game = GameState()
    
    # Check that all core components are initialized
    assert hasattr(game, 'clock')
    assert hasattr(game, 'player')
    assert hasattr(game, 'npc_manager')
    assert hasattr(game, 'economy')
    
    # Verify player state
    assert isinstance(game.player, PlayerState)
    assert game.player.gold == 40  # Default starting gold
    
    # Verify NPC manager
    assert isinstance(game.npc_manager, NPCManager)
    
    # Verify economy
    assert isinstance(game.economy, Economy)

def test_npc_scheduling():
    """Test that NPCs follow their schedules."""
    # Create a test NPC that should be present at noon
    npc = NPC(
        id="test_npc",
        name="Test NPC",
        description="A test NPC",
        schedule=[(10, 14)],  # 10 AM to 2 PM
        departure_chance=0.0
    )
    
    # Create a manager and add the NPC
    manager = NPCManager()
    manager.add_npc(npc)
    
    # Check at 9 AM - should not be present
    manager.update_all_npcs(9.0)
    assert not npc.present
    
    # Check at 12 PM - should be present
    manager.update_all_npcs(12.0)
    assert npc.present
    
    # Check at 3 PM - should not be present anymore
    manager.update_all_npcs(15.0)
    assert not npc.present

def test_gambling_mechanics():
    """Test the gambling system with the player."""
    player = PlayerState()
    economy = Economy()
    
    # Save initial gold
    initial_gold = player.gold
    
    # Test a winning bet (mock random to always win)
    with patch('random.random', return_value=0.5):  # Will win (0.5 < 0.6)
        won, winnings = economy.gamble(player, 10)
        assert won is True
        assert winnings == 10
        assert player.gold == initial_gold + 10
    
    # Test a losing bet (mock random to always lose)
    with patch('random.random', return_value=0.7):  # Will lose (0.7 > 0.6)
        won, winnings = economy.gamble(player, 10)
        assert won is False
        assert winnings == -10
        assert player.gold == initial_gold  # Back to initial
    
    # Test insufficient funds
    with pytest.raises(ValueError, match="cannot afford"):
        economy.gamble(player, player.gold + 10)
