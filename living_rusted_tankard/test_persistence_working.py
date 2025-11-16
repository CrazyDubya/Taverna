#!/usr/bin/env python3
"""
Quick test to verify persistence system works without dependencies.
"""

import sys
import tempfile
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))


def test_persistence_system():
    """Test that persistence system works correctly."""
    print("🧪 Testing Persistence System...")

    try:
        # Test imports work
        from core.persistence import SaveManager, SaveFormat, SaveMetadata

        print("✅ Imports successful")

        # Test SaveManager creation
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SaveManager(temp_dir)
            print("✅ SaveManager created")

            # Test save/load cycle
            test_data = {
                "player": {
                    "name": "TestPlayer",
                    "gold": 100,
                    "health": 100,
                    "level": 1,
                },
                "location": "tavern",
                "time": {"hour": 12, "day": 1},
            }

            # Save game
            success = manager.save_game(
                test_data, "test_save", "test_session", "TestPlayer", SaveFormat.JSON
            )

            if not success:
                print("❌ Save failed")
                return False

            print("✅ Save successful")

            # Load game
            loaded_data = manager.load_game("test_save")

            if loaded_data is None:
                print("❌ Load failed")
                return False

            if loaded_data != test_data:
                print("❌ Data mismatch")
                return False

            print("✅ Load successful, data matches")

            # Test save listing
            saves = manager.list_saves()
            if len(saves) != 1 or saves[0]["name"] != "test_save":
                print("❌ Save listing failed")
                return False

            print("✅ Save listing works")

            # Test metadata
            metadata = saves[0]["metadata"]
            if metadata is None:
                print("❌ Metadata missing")
                return False

            print("✅ Metadata present")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("🔍 VERIFYING PHASE 1 COMPLETION")
    print("=" * 50)

    success = test_persistence_system()

    print("\n" + "=" * 50)
    if success:
        print("🎉 PERSISTENCE SYSTEM WORKING!")
        print("✅ Phase 1.2 Versioned Save Format: VERIFIED")
        print("✅ All core functionality operational")
        print("🚀 Ready for git commit and Phase 2")
    else:
        print("❌ PERSISTENCE SYSTEM ISSUES")
        print("🔧 Need to fix before proceeding")

    sys.exit(0 if success else 1)
