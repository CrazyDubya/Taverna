#!/usr/bin/env python3
"""
PHASE 1 COMPLETE INTEGRATION TEST
Tests all narrative systems working together as a unified storytelling engine.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.game_state import GameState
import time


def test_phase1_complete_integration():
    """Test the complete Phase 1 narrative engine."""
    print("🎭 PHASE 1 COMPLETE NARRATIVE ENGINE TEST")
    print("=" * 60)

    # Create game with complete narrative systems
    game = GameState()

    # Check if all systems are available
    if not hasattr(game, "story_orchestrator"):
        print("❌ Complete narrative systems not available")
        return

    print("✅ Complete Phase 1 narrative engine initialized")
    print(f"   📚 Story Orchestrator: {hasattr(game, 'story_orchestrator')}")
    print(f"   💾 Narrative Persistence: {hasattr(game, 'narrative_persistence')}")
    print(
        f"   🎯 Quest Generation: {hasattr(game.story_orchestrator, 'quest_generator')}"
    )
    print(
        f"   ⚡ Consequence Engine: {hasattr(game.story_orchestrator, 'consequence_engine')}"
    )

    # Get initial narrative status
    initial_status = game.get_narrative_status()
    print("\n📊 Initial Narrative State:")
    print(f"   Tension Level: {initial_status.get('tension_level', 'unknown')}")
    print(f"   Pacing Mode: {initial_status.get('current_pacing', 'unknown')}")
    print(f"   Player Engagement: {initial_status.get('player_engagement', 0):.2f}")
    print(f"   Active Threads: {initial_status.get('active_threads', 0)}")

    # Test comprehensive story emergence through player actions
    print("\n🎮 STORY EMERGENCE TEST")
    print("-" * 40)

    story_actions = [
        ("wait 6", "⏰ Wait for morning"),
        ("look", "👀 Survey the world"),
        ("interact grim_bartender talk", "💬 First conversation"),
        ("interact grim_bartender talk", "💬 Continued conversation"),
        ("help grim_bartender", "🤝 Offer assistance"),
        ("buy ale from grim", "💰 Economic interaction"),
        ("interact grim_bartender talk", "💬 Post-transaction talk"),
        ("interact mira_merchant talk", "🆕 New relationship"),
        ("buy bread from mira", "💰 Build merchant rapport"),
        ("help mira_merchant", "🤝 Show generosity pattern"),
        ("interact mira_merchant talk", "💬 Relationship deepening"),
        ("wait 2", "⏰ Time progression"),
        ("interact grim_bartender talk", "💬 Check reputation spread"),
        ("look around", "👀 Investigate environment"),
        ("interact grim_bartender talk", "💬 Build deeper connection"),
    ]

    for i, (command, description) in enumerate(story_actions):
        print(f"\n[{i+1:2d}] {description}")
        print(f"     Command: {command}")

        result = game.process_command(command)

        if result["success"]:
            message = result.get("message", "")
            # Truncate long messages for readability
            if len(message) > 200:
                message = message[:200] + "..."
            print(f"     ✓ {message}")

            # Check for story consequences in the message
            if any(
                phrase in message.lower()
                for phrase in [
                    "consequence",
                    "reputation",
                    "relationship",
                    "story",
                    "quest",
                    "tension",
                ]
            ):
                print("     🎭 Story consequence detected!")
        else:
            print(f"     ✗ {result.get('message', 'Failed')}")

        # Show narrative evolution every few actions
        if (i + 1) % 5 == 0:
            status = game.get_narrative_status()
            print("     📈 Narrative Update:")
            print(f"        Tension: {status.get('tension_level', 'unknown')}")
            print(f"        Engagement: {status.get('player_engagement', 0):.2f}")
            print(f"        Active Threads: {status.get('active_threads', 0)}")

    # Final comprehensive analysis
    print("\n🎯 FINAL NARRATIVE ANALYSIS")
    print("=" * 60)

    final_status = game.get_narrative_status()

    # Overall story status
    print("📊 Story Orchestrator Status:")
    print(f"   Overall Tension: {final_status.get('overall_tension', 0):.2f}")
    print(f"   Tension Level: {final_status.get('tension_level', 'unknown')}")
    print(f"   Current Pacing: {final_status.get('current_pacing', 'unknown')}")
    print(f"   Player Engagement: {final_status.get('player_engagement', 0):.2f}")
    print(f"   Active Story Threads: {final_status.get('active_threads', 0)}")
    print(f"   Recent Story Moments: {final_status.get('recent_moments', 0)}")

    # Consequence system status
    consequence_stats = final_status.get("consequence_stats", {})
    print("\n⚡ Consequence Engine Status:")
    print(f"   Actions Tracked: {consequence_stats.get('total_actions_tracked', 0)}")
    print(
        f"   Consequences Triggered: {consequence_stats.get('total_consequences_triggered', 0)}"
    )
    print(
        f"   Pending Consequences: {consequence_stats.get('pending_consequences', 0)}"
    )
    print(f"   Active Chains: {consequence_stats.get('active_chains', 0)}")

    # Quest system status
    quest_stats = final_status.get("quest_stats", {})
    print("\n🎯 Quest Generator Status:")
    print(f"   Total Generated: {quest_stats.get('total_generated', 0)}")
    print(f"   Total Completed: {quest_stats.get('total_completed', 0)}")
    print(f"   Active Quests: {quest_stats.get('active_quests', 0)}")
    print(f"   Completion Rate: {quest_stats.get('completion_rate', 0):.1f}%")

    # Relationship status
    relationships = final_status.get("relationships", {})
    if relationships:
        print("\n💖 Relationship Status:")
        for npc_id, info in relationships.items():
            print(
                f"   {info['name']}: {info['relationship']} ({info['interactions']} interactions)"
            )

    # Reputation status
    reputation = final_status.get("reputation", {})
    if reputation:
        print("\n🌟 Reputation Status:")
        print(f"   Overall Score: {reputation.get('overall_score', 0):.2f}")
        print(f"   Reputation Level: {reputation.get('reputation_level', 'unknown')}")
        print(f"   Social Connections: {reputation.get('social_connections', 0)}")

    # Available quests
    available_quests = game.get_available_quests()
    active_quests = game.get_active_quests()
    print("\n🎯 Quest Status:")
    print(f"   Available Quests: {len(available_quests)}")
    print(f"   Active Quests: {len(active_quests)}")

    if available_quests:
        print("   Available Quest Examples:")
        for quest in available_quests[:2]:
            print(
                f"     - {quest.get('title', 'Unknown')} ({quest.get('type', 'unknown')})"
            )

    # Test persistence
    print("\n💾 Testing Narrative Persistence...")
    save_success = game.save_narrative_state()
    print(f"   Save Success: {'✅' if save_success else '❌'}")

    if save_success:
        print("   All narrative state saved successfully")

        # Test loading (would normally be in a new session)
        load_success = game.load_narrative_state()
        print(f"   Load Success: {'✅' if load_success else '❌'}")

    # Calculate story emergence score
    story_score = calculate_story_emergence_score(
        final_status, consequence_stats, quest_stats, relationships
    )
    print(f"\n🎭 STORY EMERGENCE SCORE: {story_score}/100")
    print(f"   {get_story_quality_description(story_score)}")

    return story_score


def calculate_story_emergence_score(status, consequences, quests, relationships):
    """Calculate how well the story systems are working together."""
    score = 0

    # Tension and pacing (20 points)
    tension = status.get("overall_tension", 0)
    engagement = status.get("player_engagement", 0)
    score += (tension + engagement) * 10

    # Consequence system (25 points)
    actions_tracked = consequences.get("total_actions_tracked", 0)
    consequences_triggered = consequences.get("total_consequences_triggered", 0)
    if actions_tracked > 0:
        consequence_ratio = min(1.0, consequences_triggered / actions_tracked)
        score += consequence_ratio * 25

    # Quest system (20 points)
    total_generated = quests.get("total_generated", 0)
    active_quests = quests.get("active_quests", 0)
    score += min(20, total_generated * 5 + active_quests * 3)

    # Relationships (20 points)
    relationship_count = len(relationships)
    avg_interactions = sum(
        info["interactions"] for info in relationships.values()
    ) / max(1, relationship_count)
    score += min(20, relationship_count * 5 + avg_interactions * 2)

    # Active threads (15 points)
    active_threads = status.get("active_threads", 0)
    score += min(15, active_threads * 5)

    return min(100, int(score))


def get_story_quality_description(score):
    """Get a description of story quality based on score."""
    if score >= 90:
        return "🌟 LEGENDARY - Rich, interconnected storytelling"
    elif score >= 80:
        return "🔥 EXCELLENT - Engaging narrative with meaningful consequences"
    elif score >= 70:
        return "✨ GOOD - Solid story foundation with emerging threads"
    elif score >= 60:
        return "📈 DEVELOPING - Basic systems working, needs more depth"
    elif score >= 50:
        return "🔧 FUNCTIONAL - Systems operational but limited impact"
    else:
        return "⚠️  BASIC - Narrative systems need significant development"


def test_story_persistence():
    """Test that story state persists across 'sessions'."""
    print("\n💾 STORY PERSISTENCE TEST")
    print("-" * 40)

    # Create first 'session'
    game1 = GameState()

    if not hasattr(game1, "story_orchestrator"):
        print("❌ Story systems not available for persistence test")
        return

    # Build up some story state
    commands = [
        "wait 6",
        "interact grim_bartender talk",
        "help grim_bartender",
        "buy ale from grim",
    ]

    print("🎮 Building story state in session 1...")
    for command in commands:
        result = game1.process_command(command)
        if result["success"]:
            print(f"   ✓ {command}")

    # Get state before saving
    status_before = game1.get_narrative_status()
    relationships_before = status_before.get("relationships", {})

    print("📊 State before save:")
    print(f"   Relationships: {len(relationships_before)}")
    print(f"   Engagement: {status_before.get('player_engagement', 0):.2f}")

    # Save state
    save_success = game1.save_narrative_state()
    print(f"💾 Save result: {'✅' if save_success else '❌'}")

    if save_success:
        # Create second 'session' and load
        game2 = GameState()
        load_success = game2.load_narrative_state()
        print(f"📂 Load result: {'✅' if load_success else '❌'}")

        if load_success:
            # Compare state after loading
            status_after = game2.get_narrative_status()
            relationships_after = status_after.get("relationships", {})

            print("📊 State after load:")
            print(f"   Relationships: {len(relationships_after)}")
            print(f"   Engagement: {status_after.get('player_engagement', 0):.2f}")

            # Check if data matches
            persistence_quality = 0
            if len(relationships_before) == len(relationships_after):
                persistence_quality += 50
                print("   ✅ Relationship count preserved")

            engagement_diff = abs(
                status_before.get("player_engagement", 0)
                - status_after.get("player_engagement", 0)
            )
            if engagement_diff < 0.1:
                persistence_quality += 50
                print("   ✅ Engagement score preserved")

            print(f"🎯 Persistence Quality: {persistence_quality}%")
            return persistence_quality >= 80

    return False


if __name__ == "__main__":
    print("🚀 PHASE 1 COMPLETE NARRATIVE ENGINE TEST SUITE")
    print("=" * 60)

    # Test complete integration
    story_score = test_phase1_complete_integration()

    # Test persistence
    persistence_success = test_story_persistence()

    # Final assessment
    print("\n🎭 PHASE 1 ASSESSMENT")
    print("=" * 60)
    print(f"📊 Story Emergence Score: {story_score}/100")
    print(f"💾 Persistence Test: {'✅ PASS' if persistence_success else '❌ FAIL'}")

    overall_grade = (story_score + (50 if persistence_success else 0)) / 1.5

    print(f"\n🏆 OVERALL PHASE 1 GRADE: {overall_grade:.0f}/100")

    if overall_grade >= 90:
        print("🌟 PHASE 1 COMPLETE - READY FOR SHARING!")
        print("   The narrative engine creates rich, emergent stories")
        print("   worthy of player engagement and community feedback.")
    elif overall_grade >= 75:
        print("✨ PHASE 1 SUCCESSFUL - NEARLY READY")
        print("   Strong narrative foundation with minor polish needed.")
    elif overall_grade >= 60:
        print("📈 PHASE 1 FUNCTIONAL - NEEDS IMPROVEMENT")
        print("   Basic systems working but require more development.")
    else:
        print("⚠️  PHASE 1 INCOMPLETE - SIGNIFICANT WORK NEEDED")
        print("   Core systems need substantial development before sharing.")

    print(f"\n{'='*60}")
    print("🎉 PHASE 1 NARRATIVE ENGINE TEST COMPLETE!")
    print(
        "🚀 Ready to advance to Phase 2: Emotional Intelligence & Adaptive Storytelling"
    )
    print("=" * 60)
