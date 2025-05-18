"""Tests for the serialization and snapshot functionality."""

import unittest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.serialization import (
    Serializable,
    save_game_state,
    load_game_state,
    get_latest_save
)
from utils.snapshot import GameSnapshot


class TestSerializable(unittest.TestCase):
    """Test the Serializable base class."""

    def test_serializable_to_dict(self):
        """Test that a serializable object can be converted to a dict."""
        class TestObj(Serializable):

            def __init__(self, x, y):
                self.x = x
                self.y = y

        obj = TestObj(1, "test")
        result = obj.to_dict()

        self.assertEqual(result, {"x": 1, "y": "test"})

    def test_serializable_from_dict(self):
        """Test that an object can be created from a dict."""
        class TestObj(Serializable):

            def __init__(self, x, y):
                self.x = x
                self.y = y

        data = {"x": 1, "y": "test"}
        obj = TestObj.from_dict(data)

        self.assertEqual(obj.x, 1)
        self.assertEqual(obj.y, "test")


class TestSaveLoadGameState(unittest.TestCase):
    """Test saving and loading game state."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path("test_saves")
        self.test_dir.mkdir(exist_ok=True)

        # Sample game state
        self.test_state = {
            "player": {"name": "Test Player", "gold": 100},
            "time": 10.5,
            "location": "Test Location"
        }

    def tearDown(self):
        """Clean up test files."""
        for file in self.test_dir.glob("*"):
            if file.is_file():
                file.unlink()
        self.test_dir.rmdir()

    def test_save_game_state(self):
        """Test saving game state to a file."""
        save_path = save_game_state(self.test_state, save_dir=str(self.test_dir))

        self.assertTrue(Path(save_path).exists())

        with open(save_path, 'r') as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data, self.test_state)

    def test_load_game_state(self):
        """Test loading game state from a file."""
        # First save a test file
        save_path = save_game_state(self.test_state, save_dir=str(self.test_dir))

        # Now load it back
        loaded_state = load_game_state(save_path)

        self.assertEqual(loaded_state, self.test_state)

    def test_get_latest_save(self):
        """Test getting the most recent save file."""
        # Create multiple save files
        save1 = self.test_dir / "save_1.json"
        save2 = self.test_dir / "save_2.json"

        with open(save1, 'w') as f:
            json.dump({"test": 1}, f)

        with open(save2, 'w') as f:
            json.dump({"test": 2}, f)

        # The latest save should be save_2.json
        latest = get_latest_save(str(self.test_dir))
        self.assertEqual(Path(latest).name, "save_2.json")


class TestGameSnapshot(unittest.TestCase):
    """Test the GameSnapshot class."""

    def setUp(self):
        """Set up test environment."""
        self.snapshot_dir = Path("test_snapshots")
        self.snapshot_dir.mkdir(exist_ok=True)
        self.snapshot = GameSnapshot(save_dir=str(self.snapshot_dir))

        self.test_state = {
            "time": 10.5,
            "player": {
                "gold": 100,
                "has_room": True,
                "tiredness": 3
            },
            "location": "Test Tavern",
            "npcs": [
                {"name": "Test NPC", "present": True}
            ]
        }

    def tearDown(self):
        """Clean up test files."""
        for file in self.snapshot_dir.glob("*"):
            if file.is_file():
                file.unlink()
        self.snapshot_dir.rmdir()

    def test_capture(self):
        """Test capturing a snapshot."""
        output = self.snapshot.capture(self.test_state, "test command")

        self.assertIn("GAME SNAPSHOT", output)
        self.assertIn("Test Tavern", output)
        self.assertIn("Test NPC", output)

        # Check that a file was created
        snapshot_files = list(self.snapshot_dir.glob("*.json"))
        self.assertEqual(len(snapshot_files), 1)

        # Check the content of the snapshot file
        with open(snapshot_files[0], 'r') as f:
            snapshot_data = json.load(f)

        self.assertEqual(snapshot_data["command"], "test command")
        self.assertEqual(snapshot_data["state"]["location"], "Test Tavern")


if __name__ == "__main__":
    unittest.main()
