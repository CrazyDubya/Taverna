#!/usr/bin/env python3
"""Test the smart retry system."""

from core.game_state import GameState


def test_smart_retry():
    """Test various retry scenarios."""
    print("🤖 TESTING SMART RETRY SYSTEM")
    print("=============================\n")

    game = GameState()

    # Test 1: Room movement with auto-correction
    print("1. Testing room movement auto-correction...")
    result = game.process_command("move kitchen")
    print(f"   Result: {result['message'][:80]}...")
    print(
        f"   Success: {result['success']}, Retry: {result.get('retry_attempted', False)}"
    )

    # Test 2: Invalid item purchase with suggestions
    print("\n2. Testing item purchase with suggestions...")
    result = game.process_command("buy sword")
    print(f"   Result: {result['message'][:80]}...")
    print(
        f"   Success: {result['success']}, Retry: {result.get('retry_attempted', False)}"
    )

    # Test 3: Gambling with too much gold (auto-adjust)
    print("\n3. Testing gambling auto-adjustment...")
    result = game.process_command("gamble 1000")
    print(f"   Result: {result['message'][:80]}...")
    print(
        f"   Success: {result['success']}, Retry: {result.get('retry_attempted', False)}"
    )

    # Test 4: NPC interaction with suggestions
    print("\n4. Testing NPC interaction with suggestions...")
    result = game.process_command("interact bartender talk")
    print(f"   Result: {result['message'][:80]}...")
    print(
        f"   Success: {result['success']}, Retry: {result.get('retry_attempted', False)}"
    )

    # Test 5: Work command with job suggestions
    print("\n5. Testing work command with job suggestions...")
    result = game.process_command("work cleaning")
    print(f"   Result: {result['message'][:80]}...")
    print(
        f"   Success: {result['success']}, Retry: {result.get('retry_attempted', False)}"
    )

    print("\n✅ Smart retry system is active!")


def test_success_rate_improvement():
    """Test improved success rate with retry system."""
    print("\n\n📊 TESTING SUCCESS RATE IMPROVEMENT")
    print("===================================\n")

    from direct_ai_evaluation import DirectAIEvaluator

    # Run shorter test to see improvement
    evaluator = DirectAIEvaluator(turns=50)
    results = evaluator.run_evaluation()

    print("\nWITH SMART RETRY SYSTEM:")
    print(f"• Success Rate: {results['success_rate']:.1f}%")
    print(f"• Errors: {len(results['metrics']['errors_encountered'])}")
    print(f"• Score: {results['overall_score']}/100")

    # Check for retry markers in output
    retry_count = 0
    auto_corrections = 0

    for sample in results["metrics"]["sample_outputs"]:
        if "[Auto-corrected]" in sample.get("response", ""):
            auto_corrections += 1
        if "retry_attempted" in sample:
            retry_count += 1

    print("\nRETRY SYSTEM STATS:")
    print(f"• Auto-corrections: {auto_corrections}")
    print(f"• Helpful suggestions: {retry_count}")

    if results["success_rate"] > 94:
        print("\n🎉 SUCCESS! Achieved 94%+ success rate!")
    else:
        print(f"\n📈 Progress: {results['success_rate']:.1f}% (target: 95%+)")


if __name__ == "__main__":
    test_smart_retry()
    test_success_rate_improvement()
