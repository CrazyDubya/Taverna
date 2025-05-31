#!/usr/bin/env python3
"""Test the narrative memory integration with actual game."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.game_state import GameState
from core.ai_player import AIPlayer, AIPlayerPersonality
import asyncio


async def test_narrative_integration():
    """Test that memories are created during gameplay."""
    print("=== Testing Narrative Memory Integration ===\n")
    
    # Create game state
    game = GameState()
    
    # Create AI player
    ai_player = AIPlayer(
        name="TestPlayer",
        personality=AIPlayerPersonality.CURIOUS_EXPLORER
    )
    
    # Test a few interactions
    test_commands = [
        "look",
        "interact grim_bartender talk",
        "buy ale from grim",
        "interact grim_bartender talk",  # Second interaction should show memory
        "move upstairs",
        "interact mira_merchant talk",
        "buy bread from mira",
        "interact mira_merchant talk"  # Should remember purchase
    ]
    
    for i, command in enumerate(test_commands):
        print(f"\n[Turn {i+1}] Command: {command}")
        result = game.process_command(command)
        
        if result['success']:
            print(f"Success: {result.get('message', 'Command executed')}")
            
            # Check if memories were created
            if "interact" in command and "talk" in command:
                npc_id = command.split()[1]
                if hasattr(game, 'character_memory_manager'):
                    memory = game.character_memory_manager.get_memory(npc_id)
                    if memory:
                        print(f"\nMemory check for {npc_id}:")
                        print(f"  Relationship: {memory.get_relationship_level()}")
                        print(f"  Interaction count: {memory.interaction_count}")
                        if memory.memories:
                            print(f"  Last memory: {memory.memories[-1].to_narrative()}")
                
                if hasattr(game, 'character_state_manager'):
                    state = game.character_state_manager.character_states.get(npc_id)
                    if state:
                        print(f"\nState check for {npc_id}:")
                        print(f"  Mood: {state.mood.value}")
                        print(f"  Status: {state.get_status_description()}")
        else:
            print(f"Failed: {result.get('message', 'Unknown error')}")
    
    # Test AI player with memories
    print("\n\n=== Testing AI Player with Narrative System ===")
    
    for turn in range(5):
        print(f"\n[AI Turn {turn+1}]")
        
        # Update AI player's game state
        snapshot = game.get_snapshot()
        ai_player.update_game_state(snapshot)
        
        # Get game context and generate action
        game_context = ai_player.get_game_context()
        action = await ai_player.generate_action(game_context)
        print(f"AI decided: {action}")
        
        result = game.process_command(action)
        print(f"Result: {result.get('message', 'Command executed')}")
        
        # Record the action
        ai_player.record_action(action, f"Turn {turn+1} action")
    
    # Final summary
    if hasattr(game, 'character_memory_manager'):
        print("\n\n=== Final Relationship Summary ===")
        summary = game.character_memory_manager.get_relationship_summary()
        for npc_id, info in summary.items():
            print(f"\n{info['name']}:")
            print(f"  Relationship: {info['relationship']}")
            print(f"  Trust: {info['trust']:.2f}")
            print(f"  Total interactions: {info['interactions']}")
            if info['last_seen'] is not None:
                print(f"  Last seen: {info['last_seen']:.1f} hours ago")


if __name__ == "__main__":
    asyncio.run(test_narrative_integration())