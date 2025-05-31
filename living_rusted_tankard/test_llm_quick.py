#!/usr/bin/env python3
"""Quick LLM test with gemma2:2b for speed."""

import logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise

from core.game_state import GameState

def test_llm_quick():
    print("🧙 QUICK LLM TEST WITH GEMMA2:2B")
    print("=" * 40)
    
    # Create game with gemma2:2b parser for speed
    game = GameState()
    game.llm_parser.llm_model = "gemma2:2b"  # Override to faster model
    
    # Wait for NPCs
    game.process_command("wait 2")
    
    test_cases = [
        "talk to the bartender",
        "go to the cellar", 
        "look around",
        "check my inventory",
        "what time is it?",
        "I want to buy a drink",
        "hey bartender",
    ]
    
    successes = 0
    llm_successes = 0
    total = len(test_cases)
    
    for cmd in test_cases:
        print(f"\n📝 Testing: '{cmd}'")
        result = game.process_command(cmd)
        success = result.get('success', False)
        message = result.get('message', '')[:80]
        
        if success:
            print(f"   ✅ Success: {message}...")
            successes += 1
        else:
            print(f"   ❌ Failed: {message}...")
    
    print(f"\n📊 RESULTS:")
    print(f"   Success Rate: {successes}/{total} ({successes/total*100:.1f}%)")
    print(f"   Model Used: {game.llm_parser.llm_model}")

if __name__ == "__main__":
    test_llm_quick()