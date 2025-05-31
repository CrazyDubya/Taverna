#!/usr/bin/env python3
"""Test regex fallback performance without LLM."""

import logging
logging.basicConfig(level=logging.ERROR)

from core.game_state import GameState

def test_regex_baseline():
    print("🔧 TESTING REGEX BASELINE (NO LLM)")
    print("=" * 40)
    
    game = GameState()
    # Disable LLM to test pure regex performance
    game.llm_parser.use_llm = False
    
    test_cases = [
        "look around",
        "check my inventory", 
        "what time is it",
        "I want to buy a drink",
        "go to the cellar",
        "talk to the bartender",
        "hey bartender",
        "jobs",
        "what work is available",
        "read notice board",
        "move cellar",
        "help",
        "status",
        "inventory",
        "buy ale"
    ]
    
    successes = 0
    for cmd in test_cases:
        result = game.process_command(cmd)
        success = result.get('success', False)
        
        if success:
            print(f"✅ '{cmd}'")
            successes += 1
        else:
            print(f"❌ '{cmd}' → {result.get('message', '')[:50]}...")
    
    rate = (successes / len(test_cases)) * 100
    print(f"\n📊 Regex Baseline: {successes}/{len(test_cases)} ({rate:.1f}%)")
    return rate

if __name__ == "__main__":
    test_regex_baseline()