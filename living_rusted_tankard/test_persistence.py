#!/usr/bin/env python3
"""
Test persistence features for The Living Rusted Tankard.
Demonstrates save/load functionality.
"""

from core.game_state import GameState
from utils.serialization import save_game_state, load_game_state, get_latest_save
from pathlib import Path
import json


def test_save_load():
    print("🍺 Testing Save/Load System for The Living Rusted Tankard")
    print("=" * 60)

    # Create initial game state
    print("1. Creating new game...")
    game1 = GameState()

    # Make some changes
    print("2. Making changes to game state...")
    game1.player.gold = 50
    game1.player.inventory.add_item("ale", 3)
    game1.clock.advance_time(2.5)  # Advance 2.5 hours

    print(f"   - Player gold: {game1.player.gold}")
    print(f"   - Player items: {list(game1.player.inventory.items.keys())}")
    print(f"   - Game time: {game1.clock.current_time.hours:.1f} hours")

    # Save the game
    print("3. Saving game...")
    save_path = save_game_state(game1, save_dir="test_saves", filename_base="demo_save")
    print(f"   - Saved to: {save_path}")

    # Create a new game (different state)
    print("4. Creating fresh game state...")
    game2 = GameState()
    print(f"   - Fresh gold: {game2.player.gold}")
    print(f"   - Fresh time: {game2.clock.current_time.hours:.1f} hours")

    # Load the saved game
    print("5. Loading saved game...")
    try:
        # Create mock narrator and parser for loading
        class MockNarrator:
            pass

        class MockParser:
            pass

        loaded_game = load_game_state(save_path, MockNarrator(), MockParser())
        print(f"   - Loaded gold: {loaded_game.player.gold}")
        print(f"   - Loaded items: {list(loaded_game.player.inventory.items.keys())}")
        print(f"   - Loaded time: {loaded_game.clock.current_time.hours:.1f} hours")

        # Verify the data matches
        if (
            loaded_game.player.gold == 50
            and "ale" in loaded_game.player.inventory.items
            and abs(loaded_game.clock.current_time.hours - 2.5) < 0.1
        ):
            print("✅ Save/Load test PASSED!")
        else:
            print("❌ Save/Load test FAILED - data mismatch")

    except Exception as e:
        print(f"❌ Save/Load test FAILED: {e}")

    # Test getting latest save
    print("6. Testing latest save detection...")
    latest = get_latest_save("test_saves")
    if latest:
        print(f"   - Latest save found: {Path(latest).name}")
    else:
        print("   - No saves found")

    # Cleanup
    print("7. Cleaning up test files...")
    import shutil

    if Path("test_saves").exists():
        shutil.rmtree("test_saves")
        print("   - Test files cleaned up")

    print("\n🎉 Persistence test completed!")


if __name__ == "__main__":
    test_save_load()
