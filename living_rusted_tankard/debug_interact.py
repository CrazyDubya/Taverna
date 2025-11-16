#!/usr/bin/env python3
"""
Debug script to isolate NPC interaction issues
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.game_state import GameState


def debug_interact():
    print("🔍 DEBUGGING NPC INTERACTION")
    print("=" * 50)

    # Create game
    game = GameState()

    # Force Gene to be present
    gene = game.npc_manager.get_npc("gene_bartender")
    if gene:
        gene.is_present = True
        print(f"✓ Gene forced present: {gene.is_present}")

    # Try a simple interact command and catch the exact error
    print("\n🎯 Testing: interact gene_bartender talk")

    try:
        result = game.process_command("interact gene_bartender talk")
        print(f"Success: {result['success']}")
        print(f"Message: {result.get('message', 'No message')}")
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        import traceback

        print("\nFull traceback:")
        traceback.print_exc()

    print("\n🔧 Checking clock methods:")
    try:
        print(f"clock.current_time_hours: {game.clock.current_time_hours}")
    except Exception as e:
        print(f"❌ current_time_hours failed: {e}")

    try:
        current_time = game.clock.get_current_time()
        print(f"clock.get_current_time(): {current_time}")
        print(f"type: {type(current_time)}")
        if hasattr(current_time, "total_hours"):
            print(f"total_hours: {current_time.total_hours}")
        else:
            print("❌ No total_hours attribute")
    except Exception as e:
        print(f"❌ get_current_time() failed: {e}")


if __name__ == "__main__":
    debug_interact()
