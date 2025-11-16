#!/usr/bin/env python3
"""
Test with forced NPC spawn for debugging
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.game_state import GameState
import time


def test_with_forced_npcs():
    """Test Phase 1 with forced NPC spawning."""
    print("🎭 PHASE 1 TEST - FORCED NPC SPAWN")
    print("=" * 60)

    # Create game
    game = GameState()

    if not hasattr(game, "story_orchestrator"):
        print("❌ Narrative systems not available")
        return 0

    print("✅ Phase 1 narrative systems initialized")

    # Force Gene to spawn for testing
    print("\n🔧 Forcing Gene to spawn for testing...")
    gene = game.npc_manager.get_npc("gene_bartender")
    if gene:
        gene.is_present = True
        print(f"   Gene forced present: {gene.is_present}")

    # Check NPCs
    present_npcs = game.npc_manager.get_present_npcs()
    print(f"\n👥 NPCs present: {len(present_npcs)}")
    for npc in present_npcs:
        print(f"   - {npc.name}")

    # Test narrative interactions
    print("\n🎮 TESTING NARRATIVE INTERACTIONS")
    print("-" * 40)

    test_commands = [
        ("look", "Survey tavern"),
        ("interact gene_bartender talk", "Talk to Gene"),
        ("interact gene_bartender talk The old days", "Ask about old days"),
        ("buy ale from gene", "Buy from Gene"),
        ("interact gene_bartender talk", "Chat again"),
        ("wait 1", "Wait"),
        ("interact gene_bartender talk Rumors in town", "Ask about rumors"),
    ]

    success_count = 0
    narrative_moments = []

    for cmd, desc in test_commands:
        print(f"\n[{desc}] {cmd}")
        result = game.process_command(cmd)

        if result["success"]:
            success_count += 1
            msg = result.get("message", "")[:150]
            print(f"✓ {msg}...")

            # Check for narrative content
            full_msg = result.get("message", "")
            if any(
                word in full_msg.lower()
                for word in [
                    "rep:",
                    "memory",
                    "remember",
                    "relationship",
                    "trust",
                    "mood",
                    "quest",
                    "consequence",
                    "story",
                ]
            ):
                narrative_moments.append((cmd, desc))
                print("  🎭 Narrative moment!")
        else:
            print(f"✗ {result.get('message', 'Failed')}")

    # Check narrative systems
    print("\n📊 NARRATIVE SYSTEMS CHECK")
    print("-" * 40)

    status = game.get_narrative_status()

    # Character relationships
    print("\n💬 Character Relationships:")
    relationships = status.get("relationships", {})
    for npc_id, rel_info in relationships.items():
        if rel_info.get("interactions", 0) > 0:
            print(f"   {npc_id}: {rel_info}")

    # Character memories
    print("\n🧠 Character Memories:")
    if hasattr(game, "character_memory_manager"):
        gene_memory = game.character_memory_manager.get_or_create_memory(
            "gene_bartender", "Gene"
        )
        if gene_memory:
            print(f"   Gene memories: {len(gene_memory.memories)}")
            print(f"   Relationship score: {gene_memory.relationship_score}")
            print(f"   Trust level: {gene_memory.trust_level}")
            for i, mem in enumerate(gene_memory.memories[:3]):
                print(
                    f"   Memory {i+1}: {mem.interaction_type} - {mem.player_action[:50]}..."
                )

    # Consequence tracking
    print("\n⚡ Consequence Engine:")
    cons = status.get("consequence_engine", {})
    print(f"   Actions tracked: {cons.get('total_actions_tracked', 0)}")
    print(f"   Consequences: {cons.get('total_consequences_triggered', 0)}")

    # Calculate score
    score = 0
    score += min(20, success_count * 3)
    score += min(20, len(narrative_moments) * 5)
    score += min(20, status.get("player_engagement", 0) * 20)
    score += min(20, cons.get("total_actions_tracked", 0) * 2)
    score += min(20, len(relationships) * 5)

    print(f"\n🏆 SCORE: {score}/100")
    print(f"   Success: {success_count}/{len(test_commands)}")
    print(f"   Narrative moments: {len(narrative_moments)}")

    return score


if __name__ == "__main__":
    score = test_with_forced_npcs()
    print(f"\n{'='*60}")
    print(f"COMPLETE - Score: {score}/100")
