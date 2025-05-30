"""Integration tests for core game components."""

import pytest
from unittest.mock import patch
from core import GameState, PlayerState, NPC, NPCManager, Economy, NPCType


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
    assert game.player.gold == 20  # Current starting gold

    # Verify NPC manager
    assert isinstance(game.npc_manager, NPCManager)

    # Verify economy
    assert isinstance(game.economy, Economy)


def test_npc_scheduling():
    """Test that NPCs follow their schedules."""
    # Create a test NPC that should be present at noon
    npc = NPC(
        id="test_npc",
        definition_id="test_npc",
        name="Test NPC",
        description="A test NPC",
        npc_type=NPCType.PATRON,
        schedule=[(10, 14)],  # 10 AM to 2 PM
        departure_chance=0.0
    )

    # Create a manager and add the NPC
    manager = NPCManager(data_dir="data")
    manager.add_npc(npc)

    # Check at 9 AM - should not be present
    manager.update_all_npcs(9.0)
    assert not npc.is_present

    # Check at 12 PM - should be present
    manager.update_all_npcs(12.0)
    assert npc.is_present

    # Check at 3 PM - should not be present anymore
    manager.update_all_npcs(15.0)
    assert not npc.is_present


def test_gambling_mechanics():
    """Test the gambling system with the player."""
    player = PlayerState()
    economy = Economy()

    # Save initial gold
    initial_gold = player.gold

    # Test a winning bet (mock random to always win)
    with patch('random.random', return_value=0.3):  # Will win (0.3 < 0.4 default odds)
        result = economy.gamble(player.gold, 10)
        assert result.success is True
        assert result.amount == 10  # Net gain after getting back bet plus winnings
        player.gold = result.new_balance
        assert player.gold == initial_gold + 10

    # Test a losing bet (mock random to always lose)
    with patch('random.random', return_value=0.7):  # Will lose (0.7 > 0.4 default odds)
        result = economy.gamble(player.gold, 10)
        assert result.success is True
        assert result.amount == -10
        player.gold = result.new_balance
        assert player.gold == initial_gold  # Back to initial

    # Test insufficient funds
    result = economy.gamble(player.gold, player.gold + 10)
    assert result.success is False
    assert "not enough gold" in result.message.lower()
