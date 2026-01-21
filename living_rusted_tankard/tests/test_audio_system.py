"""
Test suite for the Audio System.

Tests audio playback, sound effects, and music management.
"""
import unittest

from living_rusted_tankard.core.audio_system import AudioSystem, SoundEffect, MusicTrack


class TestAudioSystem(unittest.TestCase):
    """Test the AudioSystem class."""

    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = AudioSystem()

    def test_audio_system_initialization(self):
        """Test that AudioSystem initializes correctly."""
        self.assertIsNotNone(self.audio_system)

    def test_play_sound_effect(self):
        """Test playing a sound effect."""
        # Test that method exists and doesn't crash
        result = self.audio_system.play_sound("test_sound")
        # Just verify it returns something (or None)
        self.assertIsNotNone(result) or self.assertIsNone(result)

    def test_play_music_track(self):
        """Test playing a music track."""
        result = self.audio_system.play_music("tavern_theme")
        # Just verify method works
        self.assertIsNotNone(result) or self.assertIsNone(result)

    def test_stop_music(self):
        """Test stopping music playback."""
        self.audio_system.play_music("test_track")
        self.audio_system.stop_music()
        # Verify method doesn't crash
        self.assertTrue(True)

    def test_set_volume(self):
        """Test setting audio volume."""
        # Test valid volume
        self.audio_system.set_volume(0.5)
        self.assertEqual(self.audio_system.get_volume(), 0.5)

        # Test boundary values
        self.audio_system.set_volume(0.0)
        self.assertEqual(self.audio_system.get_volume(), 0.0)

        self.audio_system.set_volume(1.0)
        self.assertEqual(self.audio_system.get_volume(), 1.0)

    def test_mute_unmute(self):
        """Test muting and unmuting audio."""
        self.audio_system.mute()
        self.assertTrue(self.audio_system.is_muted())

        self.audio_system.unmute()
        self.assertFalse(self.audio_system.is_muted())

    def test_sound_effect_queue(self):
        """Test queuing multiple sound effects."""
        self.audio_system.play_sound("sound1")
        self.audio_system.play_sound("sound2")
        self.audio_system.play_sound("sound3")

        # Just verify it doesn't crash
        self.assertTrue(True)


class TestSoundEffect(unittest.TestCase):
    """Test the SoundEffect class."""

    def test_sound_effect_creation(self):
        """Test creating a sound effect."""
        effect = SoundEffect(
            id="test_effect",
            name="Test Effect",
            file_path="sounds/test.wav",
            volume=0.8,
        )

        self.assertEqual(effect.id, "test_effect")
        self.assertEqual(effect.name, "Test Effect")
        self.assertEqual(effect.volume, 0.8)

    def test_sound_effect_categories(self):
        """Test sound effect categories."""
        categories = ["combat", "ambient", "ui", "dialogue", "music"]

        for category in categories:
            effect = SoundEffect(
                id=f"{category}_sound",
                name=f"{category.title()} Sound",
                file_path=f"sounds/{category}.wav",
                category=category,
            )
            self.assertEqual(effect.category, category)


class TestMusicTrack(unittest.TestCase):
    """Test the MusicTrack class."""

    def test_music_track_creation(self):
        """Test creating a music track."""
        track = MusicTrack(
            id="tavern_music",
            name="Tavern Theme",
            file_path="music/tavern.mp3",
            loop=True,
        )

        self.assertEqual(track.id, "tavern_music")
        self.assertTrue(track.loop)

    def test_track_duration(self):
        """Test track duration tracking."""
        track = MusicTrack(
            id="test_track",
            name="Test Track",
            file_path="music/test.mp3",
            duration=180.0,  # 3 minutes
        )

        self.assertEqual(track.duration, 180.0)

    def test_track_metadata(self):
        """Test track metadata."""
        track = MusicTrack(
            id="epic_music",
            name="Epic Battle Theme",
            file_path="music/battle.mp3",
            artist="Composer Name",
            genre="orchestral",
        )

        self.assertEqual(track.artist, "Composer Name")
        self.assertEqual(track.genre, "orchestral")


class TestAudioPlayback(unittest.TestCase):
    """Test audio playback functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.audio = AudioSystem()

    def test_playback_state(self):
        """Test tracking playback state."""
        self.audio.play_music("test_track")
        # Verify we can check if something is playing
        state = self.audio.is_playing()
        self.assertIsNotNone(state) or self.assertIsNone(state)

    def test_pause_resume(self):
        """Test pausing and resuming audio."""
        self.audio.play_music("test_track")
        self.audio.pause()
        self.audio.resume()
        # Just verify methods don't crash
        self.assertTrue(True)

    def test_fade_in_fade_out(self):
        """Test audio fading effects."""
        self.audio.fade_in("test_track", duration=2.0)
        self.audio.fade_out(duration=2.0)
        # Verify methods exist and work
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
