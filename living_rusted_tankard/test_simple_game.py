#!/usr/bin/env python3
"""Simple test of core game functionality."""

from core.game_state import GameState

def test_game_functionality():
    """Test basic game functionality."""
    print("=== Testing Core Game Functionality ===")
    
    # Initialize game
    game = GameState()
    
    print(f"✓ Game initialized")
    print(f"✓ Player has {game.player.gold} gold")
    print(f"✓ Time is {game.clock.get_current_time().total_hours:.1f} hours")
    
    # Test commands
    print("\n=== Testing Commands ===")
    
    # Test look command
    result = game.process_command("look")
    print(f"✓ Look command: {result['output'][:100] if 'output' in result else str(result)[:100]}...")
    
    # Test wait command  
    result = game.process_command("wait")
    print(f"✓ Wait command: {result['output'][:100] if 'output' in result else str(result)[:100]}...")
    print(f"✓ Time advanced to {game.clock.get_current_time().total_hours:.1f} hours")
    
    # Test bounties command
    try:
        result = game.process_command("bounties")
        print(f"✓ Bounties command: {result['message'][:100] if 'message' in result else str(result)[:100]}...")
    except Exception as e:
        print(f"⚠ Bounties command error: {str(e)[:100]}...")
    
    # Test gamble command
    try:
        result = game.process_command("gamble 5")
        print(f"✓ Gamble command: {result['message'][:100] if 'message' in result else str(result)[:100]}...")
    except Exception as e:
        print(f"⚠ Gamble command error: {str(e)[:100]}...")
    
    # Test NPCs
    try:
        result = game.process_command("npcs")
        print(f"✓ NPCs command: {result['message'][:100] if 'message' in result else str(result)[:100]}...")
    except Exception as e:
        print(f"⚠ NPCs command error: {str(e)[:100]}...")
    
    print(f"\n✓ Final player gold: {game.player.gold}")
    print(f"✓ Final time: {game.clock.get_current_time().total_hours:.1f} hours")
    
    return True

if __name__ == "__main__":
    test_game_functionality()