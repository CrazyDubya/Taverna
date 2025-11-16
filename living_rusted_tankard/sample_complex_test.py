#!/usr/bin/env python3
"""Sample of complex command testing with analysis."""

import json
import time
import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.ERROR)

from core.game_state import GameState


def run_sample_complex_test():
    """Run a sample of 50 complex commands for analysis."""
    print("🧪 SAMPLE COMPLEX COMMAND ANALYSIS")
    print("=" * 50)

    game = GameState()

    # Sample of 50 diverse complex commands
    sample_commands = [
        # Natural language complexity
        ("I'd like to purchase some refreshments", "commerce", "complex"),
        ("Could you help me find something to eat", "commerce", "complex"),
        ("I'm feeling quite parched and need a beverage", "commerce", "complex"),
        ("What sort of victuals do you have available", "commerce", "complex"),
        ("I seek conversation with the proprietor", "social", "complex"),
        ("Would it be possible to speak with someone", "social", "complex"),
        ("I wish to engage in discourse", "social", "complex"),
        ("I'm curious about local happenings", "info", "complex"),
        ("What news from the surrounding lands", "info", "complex"),
        ("Are there any matters requiring attention", "work", "complex"),
        # Ambiguous commands
        ("do something", "ambiguous", "edge"),
        ("make it happen", "ambiguous", "edge"),
        ("the usual", "ambiguous", "edge"),
        ("fix this", "ambiguous", "edge"),
        ("sort me out", "ambiguous", "edge"),
        ("hook me up", "ambiguous", "edge"),
        ("surprise me", "ambiguous", "edge"),
        ("whatever works", "ambiguous", "edge"),
        ("figure it out", "ambiguous", "edge"),
        ("deal with this situation", "ambiguous", "edge"),
        # Multi-part commands
        (
            "I want to buy some ale and then talk to the bartender",
            "multipart",
            "complex",
        ),
        (
            "Show me the jobs available and also check what time it is",
            "multipart",
            "complex",
        ),
        (
            "Check the notice board and if there's anything interesting, accept it",
            "multipart",
            "complex",
        ),
        (
            "Talk to whoever's here and ask them about work opportunities",
            "multipart",
            "complex",
        ),
        (
            "I need to rest but first make sure I have enough money",
            "multipart",
            "complex",
        ),
        # Emotional/roleplay
        ("I'm feeling overwhelmed by all these choices", "emotional", "complex"),
        (
            "This place makes me nervous, I don't know what to do",
            "emotional",
            "complex",
        ),
        ("I'm excited to be here, what should I try first", "emotional", "complex"),
        ("I feel lost and confused, can someone help me", "emotional", "complex"),
        ("I'm bored out of my mind, entertain me", "emotional", "complex"),
        # Technical edge cases
        ("", "technical", "edge"),
        ("   ", "technical", "edge"),
        ("!@#$%^&*()", "technical", "edge"),
        ("buy buy buy buy buy", "technical", "edge"),
        ("This is a very long command that goes on and on", "technical", "edge"),
        ("BUY ALE NOW IMMEDIATELY", "technical", "edge"),
        ("look; buy ale; talk to bartender", "technical", "edge"),
        ("SELECT * FROM inventory", "technical", "edge"),
        ("<script>alert('xss')</script>", "technical", "edge"),
        ("rm -rf /", "technical", "edge"),
        # Typos/misspellings
        ("lok around", "typos", "edge"),
        ("inventori", "typos", "edge"),
        ("hlep me", "typos", "edge"),
        ("buy alr", "typos", "edge"),
        ("tlak to bartender", "typos", "edge"),
        ("whta time is it", "typos", "edge"),
        ("raed notice board", "typos", "edge"),
        ("purcase bread", "typos", "edge"),
        ("hwere am I", "typos", "edge"),
        ("shwo inventory", "typos", "edge"),
    ]

    results = []
    categories = {}

    print(f"Testing {len(sample_commands)} complex commands:\n")

    start_time = time.time()

    for i, (command, category, complexity) in enumerate(sample_commands, 1):
        cmd_start = time.time()
        result = game.process_command(command)
        cmd_time = time.time() - cmd_start

        success = result.get("success", False)
        message = result.get("message", "")

        # Analyze error type
        error_type = ""
        if not success:
            if "Unknown command" in message:
                error_type = "command_not_recognized"
            elif "don't understand" in message:
                error_type = "parsing_failed"
            elif "not present" in message or "not available" in message:
                error_type = "context_missing"
            elif "Invalid" in message:
                error_type = "parameter_invalid"
            else:
                error_type = "other_failure"

        # Store result
        result_data = {
            "command": command,
            "category": category,
            "complexity": complexity,
            "success": success,
            "message": message,
            "response_time": cmd_time,
            "error_type": error_type,
        }
        results.append(result_data)

        # Track categories
        if category not in categories:
            categories[category] = {"total": 0, "successes": 0, "failures": []}
        categories[category]["total"] += 1
        if success:
            categories[category]["successes"] += 1
            print(f"{i:2d}. ✅ [{category}] '{command[:50]}...'")
        else:
            categories[category]["failures"].append(
                {"command": command, "error_type": error_type, "message": message[:50]}
            )
            print(f"{i:2d}. ❌ [{category}] '{command[:50]}...' → {error_type}")

    total_time = time.time() - start_time
    successes = sum(1 for r in results if r["success"])
    success_rate = (successes / len(results)) * 100

    print("\n📊 SAMPLE TEST RESULTS:")
    print(f"   Commands Tested: {len(results)}")
    print(f"   Successful: {successes} ({success_rate:.1f}%)")
    print(f"   Failed: {len(results) - successes}")
    print(f"   Total Time: {total_time:.1f}s")
    print(f"   Avg Time/Command: {total_time/len(results):.3f}s")

    print("\n📈 CATEGORY ANALYSIS:")
    for cat, stats in sorted(categories.items()):
        rate = (stats["successes"] / stats["total"]) * 100
        print(f"   {cat.title()}: {stats['successes']}/{stats['total']} ({rate:.1f}%)")

        # Show failures for this category
        if stats["failures"]:
            print("      Top failures:")
            for failure in stats["failures"][:3]:
                print(
                    f"        • '{failure['command'][:40]}...' → {failure['error_type']}"
                )

    # Error pattern analysis
    error_patterns = {}
    for result in results:
        if not result["success"] and result["error_type"]:
            error_patterns[result["error_type"]] = (
                error_patterns.get(result["error_type"], 0) + 1
            )

    print("\n🚨 ERROR PATTERN ANALYSIS:")
    total_errors = sum(error_patterns.values())
    for error_type, count in sorted(
        error_patterns.items(), key=lambda x: x[1], reverse=True
    ):
        percentage = (count / total_errors) * 100 if total_errors > 0 else 0
        print(f"   {error_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")

    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = f"sample_complex_test_{timestamp}.json"

    output_data = {
        "metadata": {
            "timestamp": timestamp,
            "total_commands": len(results),
            "success_rate": success_rate,
            "test_duration": total_time,
        },
        "category_breakdown": {
            cat: {
                "total": stats["total"],
                "successes": stats["successes"],
                "success_rate": (stats["successes"] / stats["total"]) * 100,
                "failure_count": len(stats["failures"]),
            }
            for cat, stats in categories.items()
        },
        "error_patterns": error_patterns,
        "detailed_results": results,
    }

    with open(results_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n💾 Results saved to: {results_file}")

    return success_rate, results_file, output_data


if __name__ == "__main__":
    rate, file, data = run_sample_complex_test()
    print(f"\n🎯 Sample Success Rate: {rate:.1f}%")
