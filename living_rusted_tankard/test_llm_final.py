#!/usr/bin/env python3
"""Final test of LLM integration."""

import logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise

from core.game_state import GameState

def test_llm():
    print("🧙 TESTING LLM NATURAL LANGUAGE UNDERSTANDING")
    print("=" * 50)
    
    game = GameState()
    
    # Wait for NPCs to spawn
    game.process_command("wait 2")
    
    test_cases = [
        ("talk to the bartender", "Should translate to 'interact bartender talk'"),
        ("go to the cellar", "Should translate to 'move cellar'"),
        ("look around", "Should translate to 'look'"),
        ("check my inventory", "Should translate to 'inventory'"),
        ("what time is it?", "Should show current time"),
        ("I want to buy a drink", "Should help buy items"),
        ("hey bartender", "Should interact with bartender"),
    ]
    
    successes = 0
    for cmd, expected in test_cases:
        print(f"\n📝 Testing: '{cmd}'")
        print(f"   Expected: {expected}")
        result = game.process_command(cmd)
        success = result.get('success', False)
        message = result.get('message', 'No message')[:100]
        
        if success:
            print(f"   ✅ Success: {message}...")
            successes += 1
        else:
            print(f"   ❌ Failed: {message}...")
    
    print(f"\n📊 Score: {successes}/{len(test_cases)} ({successes/len(test_cases)*100:.1f}%)")
    
    # Test specific scenarios
    print("\n🎯 SPECIFIC SCENARIOS:")
    
    # Move to ensure NPCs are present
    game.process_command("move cellar")
    game.process_command("move main_room")
    game.process_command("wait 1")
    
    print("\n1. After moving around:")
    result = game.process_command("talk to whoever is here")
    print(f"   Result: {result['message'][:100]}...")
    
    print("\n2. Complex request:")
    result = game.process_command("I'm tired and need a place to sleep")
    print(f"   Result: {result['message'][:100]}...")

if __name__ == "__main__":
    test_llm()