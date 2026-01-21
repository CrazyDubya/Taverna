"""
Test suite for the Audio System.

Tests audio asset management and configuration.
"""
import unittest

from living_rusted_tankard.core.audio_system import (
    AudioManager,
    AudioAsset,
    AudioType,
    AudioEvent,
)


class TestAudioAsset(unittest.TestCase):
    """Test the AudioAsset class."""

    def test_audio_asset_creation(self):
        """Test creating an audio asset."""
        asset = AudioAsset(
            id="test_sound",
            name="Test Sound",
            file_path="sounds/test.wav",
            audio_type=AudioType.EFFECT,
            volume=0.8,
        )

        self.assertEqual(asset.id, "test_sound")
        self.assertEqual(asset.name, "Test Sound")
        self.assertEqual(asset.volume, 0.8)
        self.assertEqual(asset.audio_type, AudioType.EFFECT)

    def test_audio_asset_with_loop(self):
        """Test audio asset with loop enabled."""
        asset = AudioAsset(
            id="ambient_sound",
            name="Ambient",
            file_path="ambient.mp3",
            audio_type=AudioType.AMBIENT,
            loop=True,
        )

        self.assertTrue(asset.loop)

    def test_audio_asset_tags(self):
        """Test audio asset with tags."""
        asset = AudioAsset(
            id="tagged_sound",
            name="Tagged Sound",
            file_path="sound.mp3",
            audio_type=AudioType.MUSIC,
            tags=["combat", "intense"],
        )

        self.assertIn("combat", asset.tags)
        self.assertIn("intense", asset.tags)


class TestAudioTypes(unittest.TestCase):
    """Test audio type enumeration."""

    def test_audio_types_exist(self):
        """Test that all audio types are defined."""
        types = [AudioType.AMBIENT, AudioType.EFFECT, AudioType.MUSIC, AudioType.VOICE]
        
        for audio_type in types:
            self.assertIsNotNone(audio_type)
            self.assertIsInstance(audio_type, AudioType)


class TestAudioEvent(unittest.TestCase):
    """Test the AudioEvent class."""

    def test_audio_event_creation(self):
        """Test creating an audio event."""
        event = AudioEvent(
            event_type="player_action",
            audio_id="sound_effect_1",
            volume=0.7,
            delay=0.5,
        )

        self.assertEqual(event.event_type, "player_action")
        self.assertEqual(event.audio_id, "sound_effect_1")
        self.assertEqual(event.volume, 0.7)
        self.assertEqual(event.delay, 0.5)

    def test_audio_event_with_fade(self):
        """Test audio event with fade effects."""
        event = AudioEvent(
            event_type="music_transition",
            audio_id="new_track",
            fade_in=2.0,
            fade_out=1.5,
        )

        self.assertEqual(event.fade_in, 2.0)
        self.assertEqual(event.fade_out, 1.5)


class TestAudioManager(unittest.TestCase):
    """Test the AudioManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.audio_manager = AudioManager()

    def test_audio_manager_initialization(self):
        """Test that AudioManager initializes correctly."""
        self.assertIsNotNone(self.audio_manager)
        self.assertIsInstance(self.audio_manager.assets, dict)

    def test_default_volume_settings(self):
        """Test default volume settings."""
        self.assertIn(AudioType.AMBIENT, self.audio_manager.volume_settings)
        self.assertIn(AudioType.EFFECT, self.audio_manager.volume_settings)
        self.assertIn(AudioType.MUSIC, self.audio_manager.volume_settings)

    def test_master_volume(self):
        """Test master volume configuration."""
        self.assertGreaterEqual(self.audio_manager.master_volume, 0.0)
        self.assertLessEqual(self.audio_manager.master_volume, 1.0)

    def test_audio_enabled_flag(self):
        """Test audio enabled flag."""
        self.assertTrue(self.audio_manager.enabled)
        self.audio_manager.enabled = False
        self.assertFalse(self.audio_manager.enabled)

    def test_default_assets_loaded(self):
        """Test that default assets are loaded."""
        # Check if any default assets exist
        self.assertGreater(len(self.audio_manager.assets), 0)

    def test_register_asset(self):
        """Test registering a new audio asset."""
        new_asset = AudioAsset(
            id="custom_sound",
            name="Custom Sound",
            file_path="custom.mp3",
            audio_type=AudioType.EFFECT,
        )

        self.audio_manager.register_asset(new_asset)
        self.assertIn("custom_sound", self.audio_manager.assets)

    def test_get_asset(self):
        """Test retrieving an audio asset."""
        # Register an asset first
        test_asset = AudioAsset(
            id="retrievable",
            name="Retrievable",
            file_path="test.mp3",
            audio_type=AudioType.EFFECT,
        )
        self.audio_manager.register_asset(test_asset)

        # Retrieve it
        retrieved = self.audio_manager.get_asset("retrievable")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "retrievable")

    def test_event_mappings(self):
        """Test event mappings structure."""
        self.assertIsInstance(self.audio_manager.event_mappings, dict)


if __name__ == "__main__":
    unittest.main()
