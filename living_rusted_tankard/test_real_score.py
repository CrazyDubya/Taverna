#!/usr/bin/env python3
"""
Real Phase 1 score test with proper NPC spawning
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.game_state import GameState


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


def test_real_phase1_score():
    print("📊 REAL PHASE 1 SCORE TEST")
    print("=" * 50)

    # Create game
    game = GameState()

    # Force NPCs to spawn properly
    print("🎬 Forcing NPCs to spawn...")
    gene = game.npc_manager.get_npc("gene_bartender")
    if gene:
        gene.is_present = True
        print(f"✓ Gene present: {gene.is_present}")

    serena = game.npc_manager.get_npc("serena_waitress")
    if serena:
        serena.is_present = True
        print(f"✓ Serena present: {serena.is_present}")

    # Run the same test sequence as Phase 1 test
    story_actions = [
        ("wait 6", "⏰ Wait for morning"),
        ("look", "👀 Survey the world"),
        ("interact gene_bartender talk", "💬 First conversation"),
        ("interact gene_bartender talk", "💬 Continued conversation"),
        ("help gene_bartender", "🤝 Offer assistance"),
        ("buy ale from gene", "💰 Economic interaction"),
        ("interact gene_bartender talk", "💬 Post-transaction talk"),
        ("interact serena_waitress talk", "🆕 New relationship"),
        ("buy bread from serena", "💰 Build merchant rapport"),
        ("help serena_waitress", "🤝 Show generosity pattern"),
        ("interact serena_waitress talk", "💬 Relationship deepening"),
        ("wait 2", "⏰ Time progression"),
        ("interact gene_bartender talk", "💬 Check reputation spread"),
        ("look around", "👀 Investigate environment"),
        ("interact gene_bartender talk", "💬 Build deeper connection"),
    ]

    print("\n🎮 STORY EMERGENCE TEST")
    print("-" * 40)

    successful_actions = 0
    for i, (command, description) in enumerate(story_actions):
        print(f"\n[{i+1:2d}] {description}")
        print(f"     Command: {command}")

        result = game.process_command(command)

        if result["success"]:
            successful_actions += 1
            message = result.get("message", "")
            if len(message) > 200:
                message = message[:200] + "..."
            print(f"     ✓ {message}")
        else:
            print(f"     ✗ {result.get('message', 'Failed')}")

        # Show narrative evolution every 5 actions
        if (i + 1) % 5 == 0:
            status = game.get_narrative_status()
            print("     📈 Narrative Update:")
            print(f"        Tension: {status.get('tension_level', 'unknown')}")
            print(f"        Engagement: {status.get('player_engagement', 0):.2f}")
            print(f"        Active Threads: {status.get('active_threads', 0)}")

    # Get final status
    final_status = game.get_narrative_status()

    print("\n🎯 FINAL NARRATIVE ANALYSIS")
    print("=" * 50)

    print("📊 Story Orchestrator Status:")
    print(f"   Overall Tension: {final_status.get('overall_tension', 0):.2f}")
    print(f"   Tension Level: {final_status.get('tension_level', 'unknown')}")
    print(f"   Current Pacing: {final_status.get('current_pacing', 'unknown')}")
    print(f"   Player Engagement: {final_status.get('player_engagement', 0):.2f}")
    print(f"   Active Story Threads: {final_status.get('active_threads', 0)}")

    consequence_stats = final_status.get("consequence_stats", {})
    print("\n⚡ Consequence Engine Status:")
    print(f"   Actions Tracked: {consequence_stats.get('total_actions_tracked', 0)}")
    print(
        f"   Consequences Triggered: {consequence_stats.get('total_consequences_triggered', 0)}"
    )
    print(
        f"   Pending Consequences: {consequence_stats.get('pending_consequences', 0)}"
    )

    quest_stats = final_status.get("quest_stats", {})
    print("\n🎯 Quest Generator Status:")
    print(f"   Total Generated: {quest_stats.get('total_generated', 0)}")
    print(f"   Total Completed: {quest_stats.get('total_completed', 0)}")
    print(f"   Active Quests: {quest_stats.get('active_quests', 0)}")

    relationships = final_status.get("relationships", {})
    print("\n🌟 Reputation Status:")
    print(f"   Social Connections: {len(relationships)}")
    active_relationships = sum(
        1 for r in relationships.values() if r.get("interactions", 0) > 0
    )
    print(f"   Active Relationships: {active_relationships}")

    # Pass the corrected stats to score calculation
    # Need to ensure the score calculation uses the right data
    story_score = calculate_story_emergence_score(
        final_status, consequence_stats, quest_stats, relationships
    )

    print(f"\n🏆 ACTUAL PHASE 1 SCORE: {story_score}/100")
    print(
        f"   Success Rate: {successful_actions}/{len(story_actions)} ({successful_actions/len(story_actions)*100:.1f}%)"
    )

    if story_score >= 50:
        print("   🌟 EXCELLENT - Ready for sharing!")
    elif story_score >= 40:
        print("   ✨ GOOD - Strong foundation")
    elif story_score >= 30:
        print("   📈 PROMISING - Systems working")
    elif story_score >= 20:
        print("   🔧 FUNCTIONAL - Basic systems operational")
    else:
        print("   ⚠️  BASIC - Needs more development")

    return story_score


if __name__ == "__main__":
    score = test_real_phase1_score()
    print(f"\n{'='*50}")
    print(f"FINAL SCORE: {score}/100")
