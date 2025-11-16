#!/usr/bin/env python3
"""Test to see when LLM actually works vs regex fallback."""

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from core.game_state import GameState


def test_llm_vs_regex():
    print("🧙 LLM vs REGEX COMPARISON TEST")
    print("=" * 50)

    game = GameState()

    test_cases = [
        "talk to the bartender",
        "I want to buy a drink",
        "what time is it",
        "go to the cellar",
        "look around",
        "hey there bartender",
    ]

    print("📊 Looking for 'LLM parsed' messages vs 'regex' fallbacks:\n")

    llm_successes = 0
    regex_successes = 0

    for cmd in test_cases:
        print(f"🧪 Testing: '{cmd}'")

        # Capture logs to see if LLM or regex was used
        import io
        import sys

        # Redirect logs to capture them
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        result = game.process_command(cmd)

        # Restore stdout
        sys.stdout = old_stdout
        logs = buffer.getvalue()

        # Check what method was used
        if "LLM parsed" in logs:
            method = "🤖 LLM"
            llm_successes += 1
        elif "regex" in logs.lower() or "fallback" in logs.lower():
            method = "🔧 Regex"
            regex_successes += 1
        else:
            method = "❓ Unknown"

        success = "✅" if result.get("success", False) else "❌"
        print(f"   {method} → {success} {result.get('message', '')[:60]}...")
        print()

    print("📈 PARSING METHOD BREAKDOWN:")
    print(f"   LLM Parsing: {llm_successes} commands")
    print(f"   Regex Fallback: {regex_successes} commands")

    if llm_successes > 0:
        print("   🎉 LLM is working! No more rushing.")
    else:
        print("   ⚠️ Still falling back to regex - may need more timeout")


if __name__ == "__main__":
    test_llm_vs_regex()
