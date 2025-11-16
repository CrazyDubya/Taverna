#!/usr/bin/env python3
"""Simple test of narrative memory without AI player."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.game_state import GameState


def test_memory_simple():
    """Test that memories are created during interactions."""
    print("=== Testing Memory Creation in Game ===\n")

    # Create game state
    game = GameState()

    # Test commands
    commands = [
        ("look", "Initial look"),
        ("wait 6", "Wait for morning - NPCs should arrive"),
        ("look", "Look again - should see NPCs"),
        ("interact grim_bartender talk", "First talk with Grim"),
        ("buy ale from grim", "Buy ale from Grim"),
        ("interact grim_bartender talk", "Second talk - should show memory"),
        ("go upstairs", "Go upstairs"),
        ("interact mira_merchant talk", "Talk to Mira"),
        ("buy bread from mira", "Buy from Mira"),
        ("interact mira_merchant talk", "Talk again - should remember"),
    ]

    for command, description in commands:
        print(f"\n{'='*50}")
        print(f"Command: {command} ({description})")
        print("=" * 50)

        result = game.process_command(command)

        if result["success"]:
            print(f"✓ Success: {result.get('message', '')[:200]}")

            # Check memories after NPC interactions
            if "interact" in command and "talk" in command:
                npc_id = command.split()[1]

                # Check character memory
                if hasattr(game, "character_memory_manager"):
                    memory = game.character_memory_manager.get_memory(npc_id)
                    if memory:
                        print(f"\n📝 Memory Status for {memory.npc_name}:")
                        print(
                            f"   Relationship: {memory.get_relationship_level().value}"
                        )
                        print(f"   Trust: {memory.trust_level:.2f}")
                        print(f"   Interactions: {memory.interaction_count}")

                        # Show recent memories
                        if memory.memories:
                            print("   Recent memories:")
                            for mem in memory.memories[-3:]:
                                print(f"     - {mem.to_narrative()}")

                        # Show greeting
                        print(f"   Current greeting: {memory.get_greeting()}")

                # Check character state
                if hasattr(game, "character_state_manager"):
                    state = game.character_state_manager.character_states.get(npc_id)
                    if state:
                        print(f"\n🎭 State for {state.npc_name}:")
                        print(f"   Mood: {state.mood.value}")
                        print(f"   Energy: {state.energy:.2f}")
                        print(f"   Stress: {state.stress:.2f}")
                        print(f"   Status: {state.get_status_description()}")
        else:
            print(f"✗ Failed: {result.get('message', 'Unknown error')}")

    # Final summary
    if hasattr(game, "character_memory_manager"):
        print("\n\n" + "=" * 60)
        print("=== FINAL RELATIONSHIP SUMMARY ===")
        print("=" * 60)

        summary = game.character_memory_manager.get_relationship_summary()
        for npc_id, info in sorted(summary.items()):
            print(f"\n{info['name']}:")
            print(f"  Relationship Level: {info['relationship']}")
            print(f"  Trust Level: {info['trust']:.2%}")
            print(f"  Total Interactions: {info['interactions']}")

            # Get full memory for more details
            memory = game.character_memory_manager.get_memory(npc_id)
            if memory and memory.personal_facts:
                print("  Personal facts learned:")
                for category, facts in memory.personal_facts.items():
                    for fact in facts:
                        print(f"    - {category}: {fact}")


if __name__ == "__main__":
    test_memory_simple()
