#!/usr/bin/env python3
"""Debug LLM parser integration."""

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

from core.game_state import GameState
from core.player import Player

def test_llm_parsing():
    print("Testing LLM Parser Integration\n")
    
    # Create game
    game = GameState()
    game.player.name = "TestPlayer"
    
    # Wait to spawn NPCs
    print("1. Waiting for NPCs to spawn...")
    result = game.process_command("wait 2")
    print(f"   Result: {result['message']}\n")
    
    # Test natural language
    test_commands = [
        "talk to the bartender",
        "go to the cellar", 
        "look around",
        "where am I?"
    ]
    
    print("2. Testing natural language commands:\n")
    for cmd in test_commands:
        print(f"   Command: '{cmd}'")
        result = game.process_command(cmd)
        print(f"   Result: {result['message'][:100]}...")
        print(f"   Success: {result.get('success', False)}\n")

if __name__ == "__main__":
    test_llm_parsing()