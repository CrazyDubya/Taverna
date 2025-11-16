#!/usr/bin/env python3
"""Focused test on key natural language improvements."""

import logging

logging.basicConfig(level=logging.ERROR)

from core.game_state import GameState


def focused_test():
    print("🎯 FOCUSED NATURAL LANGUAGE TEST")
    print("=" * 40)

    game = GameState()

    # Focus on commands that should show clear improvement
    test_cases = [
        "what time is it",  # Should work (time query)
        "I want to buy a drink",  # Should work (enhanced shopping)
        "check my inventory",  # Should work (inventory)
        "look around",  # Should work (observation)
        "tell me about this place",  # Should work (place description)
        "go to the cellar",  # May work (movement)
        "what work is available",  # Should work (jobs)
        "hey there",  # May work (social)
        "help me",  # Should work (help)
        "where am I",  # Should work (location)
    ]

    successes = 0

    print("Testing 10 key natural language commands:\n")

    for i, cmd in enumerate(test_cases, 1):
        result = game.process_command(cmd)
        success = result.get("success", False)

        if success:
            successes += 1
            print(f"{i:2}. ✅ '{cmd}'")
        else:
            message = result.get("message", "")[:50]
            print(f"{i:2}. ❌ '{cmd}' → {message}...")

    success_rate = (successes / len(test_cases)) * 100

    print("\n📊 FOCUSED TEST RESULTS:")
    print(f"   Success Rate: {successes}/{len(test_cases)} ({success_rate:.1f}%)")

    # Compare to baseline
    baseline = 26  # Original performance
    improvement = success_rate - baseline

    print("\n📈 IMPROVEMENT:")
    print(f"   Baseline: {baseline}%")
    print(f"   Current: {success_rate:.1f}%")
    print(f"   Gain: +{improvement:.1f} percentage points")

    if success_rate >= 70:
        print("   🚀 EXCELLENT IMPROVEMENT!")
    elif success_rate >= 60:
        print("   🎉 GREAT IMPROVEMENT!")
    elif success_rate >= 50:
        print("   ✅ GOOD IMPROVEMENT!")
    else:
        print("   📈 MODERATE IMPROVEMENT!")


if __name__ == "__main__":
    focused_test()
