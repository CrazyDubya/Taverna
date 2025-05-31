#!/usr/bin/env python3
"""Final performance test with working LLM."""

import logging
logging.basicConfig(level=logging.WARNING)

from core.game_state import GameState

def final_test():
    print("🎯 FINAL LLM PERFORMANCE TEST")
    print("=" * 40)
    
    game = GameState()
    
    # Wait for NPCs to potentially spawn
    game.process_command("wait 3")
    
    # Comprehensive natural language test
    test_cases = [
        "talk to the bartender",
        "I want to buy a drink",
        "what time is it", 
        "go to the cellar",
        "look around",
        "hey bartender",
        "check my inventory",
        "where am I",
        "buy some ale",
        "what work is available",
        "I'm looking for work",
        "tell me about this place",
        "get me some food",
        "head upstairs",
        "speak with someone",
        "what can I do here",
        "show me my status",
        "read the notice board",
        "purchase bread",
        "walk to the bar"
    ]
    
    successes = 0
    llm_parsed = 0
    
    print("Testing 20 natural language commands:\n")
    
    for i, cmd in enumerate(test_cases, 1):
        result = game.process_command(cmd)
        success = result.get('success', False)
        message = result.get('message', '')
        
        # Count LLM usage (simplified check)
        if 'Unknown command' not in message and 'not understand' not in message:
            llm_parsed += 1
        
        if success:
            successes += 1
            print(f"{i:2}. ✅ '{cmd}'")
        else:
            print(f"{i:2}. ❌ '{cmd}' → {message[:50]}...")
    
    success_rate = (successes / len(test_cases)) * 100
    llm_rate = (llm_parsed / len(test_cases)) * 100
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Success Rate: {successes}/{len(test_cases)} ({success_rate:.1f}%)")
    print(f"   LLM Parsed: ~{llm_parsed}/{len(test_cases)} ({llm_rate:.1f}%)")
    
    print(f"\n🏆 IMPROVEMENT ASSESSMENT:")
    if success_rate >= 70:
        print("   🚀 EXCELLENT - Major breakthrough achieved!")
    elif success_rate >= 60:
        print("   🎉 GREAT - Significant improvement from 26%!")
    elif success_rate >= 50:
        print("   ✅ GOOD - Solid improvement, nearly doubled!")
    else:
        print("   ⚠️ MODEST - Some improvement but more work needed")
    
    return success_rate

if __name__ == "__main__":
    final_test()