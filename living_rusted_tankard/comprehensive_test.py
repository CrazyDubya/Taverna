#!/usr/bin/env python3
"""Comprehensive test of current LLM integration."""

import logging

logging.basicConfig(level=logging.ERROR)  # Only show errors

from core.game_state import GameState


def comprehensive_test():
    print("🎯 COMPREHENSIVE LLM INTEGRATION TEST")
    print("=" * 50)

    game = GameState()

    # Test broader range of natural language
    test_cases = [
        # Basic commands that should work
        ("look", "Basic look command"),
        ("status", "Player status check"),
        ("inventory", "Check inventory"),
        ("help", "Get help"),
        # Natural language variations
        ("look around", "Natural look variation"),
        ("check my status", "Natural status check"),
        ("check my inventory", "Natural inventory check"),
        ("what do I have", "Inventory question"),
        ("where am I", "Location question"),
        ("what time is it", "Time question"),
        # Shopping/economic
        ("buy ale", "Direct purchase"),
        ("I want to buy a drink", "Natural purchase request"),
        ("get me some food", "Natural food request"),
        ("purchase bread", "Alternative purchase"),
        # Movement/exploration
        ("move cellar", "Direct movement"),
        ("go to the cellar", "Natural movement"),
        ("head upstairs", "Movement variation"),
        ("walk to the bar", "Walk command"),
        # Social/NPC interactions
        ("talk to bartender", "Direct interaction"),
        ("speak with the bartender", "Interaction variation"),
        ("hey bartender", "Casual greeting"),
        ("interact with gene", "Specific NPC"),
        # Work/jobs
        ("jobs", "Direct jobs command"),
        ("what work is available", "Natural job query"),
        ("I'm looking for work", "Job seeking statement"),
        ("show me the jobs", "Job request"),
        # Information gathering
        ("read notice board", "Direct board read"),
        ("check the board", "Board variation"),
        ("what's on the notice board", "Natural board query"),
        # Time/waiting
        ("wait", "Basic wait"),
        ("wait 1", "Wait with parameter"),
        ("pass some time", "Natural time passing"),
        # Complex requests
        ("I'm tired and need rest", "Complex need expression"),
        ("tell me about this place", "Information request"),
        ("what can I do here", "Capability query"),
    ]

    successes = 0
    total = len(test_cases)
    results = []

    print(f"Testing {total} natural language commands...\n")

    for cmd, description in test_cases:
        result = game.process_command(cmd)
        success = result.get("success", False)
        message = result.get("message", "")[:100]

        results.append(
            {
                "command": cmd,
                "description": description,
                "success": success,
                "message": message,
            }
        )

        if success:
            successes += 1
            print(f"✅ '{cmd}' → Success")
        else:
            print(f"❌ '{cmd}' → {message[:50]}...")

    # Analysis
    success_rate = (successes / total) * 100

    print("\n📊 FINAL RESULTS:")
    print(f"   Success Rate: {successes}/{total} ({success_rate:.1f}%)")

    # Categorize results
    categories = {
        "Basic Commands": 0,
        "Natural Language": 0,
        "Shopping/Economic": 0,
        "Movement": 0,
        "Social/NPC": 0,
        "Work/Jobs": 0,
        "Information": 0,
        "Time/Waiting": 0,
        "Complex Requests": 0,
    }

    category_totals = {k: 0 for k in categories.keys()}

    # Count by category (simplified mapping)
    for result in results:
        cmd = result["command"].lower()
        success = result["success"]

        if cmd in ["look", "status", "inventory", "help"]:
            category_totals["Basic Commands"] += 1
            if success:
                categories["Basic Commands"] += 1
        elif "buy" in cmd or "purchase" in cmd or "get me" in cmd:
            category_totals["Shopping/Economic"] += 1
            if success:
                categories["Shopping/Economic"] += 1
        elif "move" in cmd or "go to" in cmd or "head" in cmd or "walk" in cmd:
            category_totals["Movement"] += 1
            if success:
                categories["Movement"] += 1
        elif "talk" in cmd or "speak" in cmd or "hey" in cmd or "interact" in cmd:
            category_totals["Social/NPC"] += 1
            if success:
                categories["Social/NPC"] += 1
        elif "job" in cmd or "work" in cmd:
            category_totals["Work/Jobs"] += 1
            if success:
                categories["Work/Jobs"] += 1
        elif "wait" in cmd or "time" in cmd or "pass" in cmd:
            category_totals["Time/Waiting"] += 1
            if success:
                categories["Time/Waiting"] += 1
        elif "read" in cmd or "board" in cmd or "where am" in cmd or "what" in cmd:
            category_totals["Information"] += 1
            if success:
                categories["Information"] += 1
        elif len(cmd.split()) > 3:  # Complex multi-word commands
            category_totals["Complex Requests"] += 1
            if success:
                categories["Complex Requests"] += 1
        else:
            category_totals["Natural Language"] += 1
            if success:
                categories["Natural Language"] += 1

    print("\n📈 CATEGORY BREAKDOWN:")
    for category, successes in categories.items():
        total = category_totals[category]
        if total > 0:
            rate = (successes / total) * 100
            print(f"   {category}: {successes}/{total} ({rate:.0f}%)")

    # Improvement assessment
    print("\n🎯 ASSESSMENT:")
    if success_rate >= 70:
        print("   🚀 EXCELLENT - Major improvement achieved!")
    elif success_rate >= 50:
        print("   ✅ GOOD - Significant improvement, but room for optimization")
    elif success_rate >= 30:
        print("   ⚠️ MODERATE - Some improvement, needs more work")
    else:
        print("   🚨 POOR - Needs major improvements")

    return success_rate


if __name__ == "__main__":
    rate = comprehensive_test()
    print(f"\n🎖️ Final Score: {rate:.1f}%")
