#!/usr/bin/env python3
"""Final comprehensive test - broader command coverage."""

import logging
logging.basicConfig(level=logging.ERROR)  # Only show errors

from core.game_state import GameState

def test_comprehensive():
    print("🎯 FINAL COMPREHENSIVE LLM TEST")
    print("=" * 50)
    
    game = GameState()
    
    # Test cases covering all major natural language patterns
    test_cases = [
        # Time/Status queries (should work well)
        ("what time is it", "Time query"),
        ("check my status", "Status check"),
        ("where am I", "Location query"),
        
        # Inventory/Items (should work well)
        ("check my inventory", "Inventory check"),
        ("what do I have", "Inventory variant"),
        
        # Shopping (should work well with new prompts)
        ("I want to buy a drink", "Natural purchase"),
        ("buy some ale", "Direct purchase"),
        ("get me some food", "Food request"),
        ("purchase bread", "Purchase variant"),
        
        # Looking/Observation (should work)
        ("look around", "Basic observation"),
        ("tell me about this place", "Place description"),
        ("examine the room", "Room examination"),
        
        # Movement (challenging due to room availability)
        ("go to the cellar", "Movement command"),
        ("head upstairs", "Movement variant"),
        ("move to the bar", "Direct movement"),
        
        # Work/Jobs
        ("what work is available", "Job inquiry"),
        ("I'm looking for work", "Work seeking"),
        ("show me the jobs", "Job request"),
        
        # Social (challenging due to NPC availability)
        ("talk to the bartender", "Social interaction"),
        ("hey there", "Casual greeting"),
        ("speak with someone", "Social variant"),
        
        # Information gathering
        ("read the notice board", "Board reading"),
        ("what's on the board", "Board inquiry"),
        
        # Help/Commands
        ("what can I do here", "Capability query"),
        ("help me", "Help request"),
        
        # Complex natural language
        ("I'm tired and need rest", "Complex need"),
        ("what's going on around here", "Situation inquiry")
    ]
    
    successes = 0
    total = len(test_cases)
    categories = {
        'Status/Time': [],
        'Inventory': [],
        'Shopping': [],
        'Observation': [],
        'Movement': [],
        'Work': [],
        'Social': [],
        'Information': [],
        'Help': [],
        'Complex': []
    }
    
    print(f"Testing {total} natural language commands:")
    print()
    
    for i, (cmd, desc) in enumerate(test_cases, 1):
        result = game.process_command(cmd)
        success = result.get('success', False)
        message = result.get('message', '')
        
        # Categorize
        if 'time' in cmd or 'status' in cmd or 'where am' in cmd:
            categories['Status/Time'].append((cmd, success, message))
        elif 'inventory' in cmd or 'what do I have' in cmd:
            categories['Inventory'].append((cmd, success, message))
        elif 'buy' in cmd or 'purchase' in cmd or 'get me' in cmd:
            categories['Shopping'].append((cmd, success, message))
        elif 'look' in cmd or 'examine' in cmd or 'tell me about' in cmd:
            categories['Observation'].append((cmd, success, message))
        elif 'go to' in cmd or 'head' in cmd or 'move to' in cmd:
            categories['Movement'].append((cmd, success, message))
        elif 'work' in cmd or 'job' in cmd:
            categories['Work'].append((cmd, success, message))
        elif 'talk' in cmd or 'hey' in cmd or 'speak' in cmd:
            categories['Social'].append((cmd, success, message))
        elif 'board' in cmd or 'read' in cmd:
            categories['Information'].append((cmd, success, message))
        elif 'help' in cmd or 'what can I do' in cmd:
            categories['Help'].append((cmd, success, message))
        else:
            categories['Complex'].append((cmd, success, message))
        
        if success:
            successes += 1
            print(f"{i:2}. ✅ '{cmd}'")
        else:
            print(f"{i:2}. ❌ '{cmd}' → {message[:60]}...")
    
    success_rate = (successes / total) * 100
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Success Rate: {successes}/{total} ({success_rate:.1f}%)")
    
    print(f"\n📈 CATEGORY BREAKDOWN:")
    for category, tests in categories.items():
        if tests:
            cat_successes = sum(1 for _, success, _ in tests if success)
            cat_total = len(tests)
            cat_rate = (cat_successes / cat_total) * 100
            print(f"   {category}: {cat_successes}/{cat_total} ({cat_rate:.0f}%)")
    
    print(f"\n🎯 ASSESSMENT:")
    if success_rate >= 70:
        print("   🚀 EXCELLENT - Major breakthrough!")
        print("   🎉 The enhanced LLM prompts are working beautifully!")
    elif success_rate >= 60:
        print("   🎉 GREAT - Significant improvement achieved!")
        print("   ✅ Enhanced prompts showing strong results!")
    elif success_rate >= 50:
        print("   ✅ GOOD - Solid improvement from baseline!")
        print("   📈 Enhanced prompts providing measurable gains!")
    elif success_rate >= 40:
        print("   ⚠️ MODERATE - Some improvement visible!")
        print("   🔧 Enhanced prompts helping but need refinement!")
    else:
        print("   🚨 NEEDS WORK - More optimization required!")
    
    # Show comparison to original performance
    original_rate = 26  # From earlier tests
    improvement = success_rate - original_rate
    improvement_percent = (improvement / original_rate) * 100 if original_rate > 0 else 0
    
    print(f"\n📊 IMPROVEMENT ANALYSIS:")
    print(f"   Original Performance: ~{original_rate}%")
    print(f"   Current Performance: {success_rate:.1f}%")
    print(f"   Absolute Improvement: +{improvement:.1f} percentage points")
    print(f"   Relative Improvement: +{improvement_percent:.0f}% increase")
    
    return success_rate

if __name__ == "__main__":
    final_rate = test_comprehensive()
    print(f"\n🏆 FINAL SCORE: {final_rate:.1f}%")