"""
Audio system for The Living Rusted Tankard.

This module provides:
- Ambient tavern sounds
- Sound effects for game events
- Audio management and settings
- Web Audio API integration
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AudioType(Enum):
    AMBIENT = "ambient"
    EFFECT = "effect"
    MUSIC = "music"
    VOICE = "voice"


@dataclass
class AudioAsset:
    """Represents an audio asset with metadata."""

    id: str
    name: str
    file_path: str
    audio_type: AudioType
    volume: float = 1.0
    loop: bool = False
    duration: Optional[float] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class AudioEvent:
    """Represents an audio event trigger."""

    event_type: str
    audio_id: str
    volume: float = 1.0
    delay: float = 0.0
    fade_in: float = 0.0
    fade_out: float = 0.0


class AudioManager:
    """Manages audio assets and playback for the game."""

    def __init__(self, audio_dir: str = "static/audio"):
        self.audio_dir = Path(audio_dir)
        self.assets: Dict[str, AudioAsset] = {}
        self.event_mappings: Dict[str, List[AudioEvent]] = {}
        self.volume_settings = {
            AudioType.AMBIENT: 0.3,
            AudioType.EFFECT: 0.7,
            AudioType.MUSIC: 0.5,
            AudioType.VOICE: 0.8,
        }
        self.master_volume = 0.6
        self.enabled = True

        self._initialize_default_assets()
        self._initialize_event_mappings()

    def _initialize_default_assets(self):
        """Initialize default audio assets for the tavern."""
        # Ambient sounds
        self.register_asset(
            AudioAsset(
                id="tavern_ambience",
                name="Tavern Ambience",
                file_path="ambience/tavern-general.mp3",
                audio_type=AudioType.AMBIENT,
                volume=0.4,
                loop=True,
                tags=["background", "tavern", "ambient"],
            )
        )

        self.register_asset(
            AudioAsset(
                id="fireplace_crackling",
                name="Fireplace Crackling",
                file_path="ambience/fireplace.mp3",
                audio_type=AudioType.AMBIENT,
                volume=0.2,
                loop=True,
                tags=["fire", "crackling", "cozy"],
            )
        )

        self.register_asset(
            AudioAsset(
                id="crowd_chatter",
                name="Crowd Chatter",
                file_path="ambience/crowd-chatter.mp3",
                audio_type=AudioType.AMBIENT,
                volume=0.3,
                loop=True,
                tags=["voices", "crowd", "talking"],
            )
        )

        # Sound effects
        self.register_asset(
            AudioAsset(
                id="coin_drop",
                name="Coin Drop",
                file_path="effects/coin-drop.mp3",
                audio_type=AudioType.EFFECT,
                volume=0.8,
                tags=["money", "gold", "transaction"],
            )
        )

        self.register_asset(
            AudioAsset(
                id="door_open",
                name="Door Opening",
                file_path="effects/door-open.mp3",
                audio_type=AudioType.EFFECT,
                volume=0.6,
                tags=["door", "entrance", "room"],
            )
        )

        self.register_asset(
            AudioAsset(
                id="drink_pour",
                name="Drink Pouring",
                file_path="effects/drink-pour.mp3",
                audio_type=AudioType.EFFECT,
                volume=0.7,
                tags=["drink", "ale", "tavern"],
            )
        )

        self.register_asset(
            AudioAsset(
                id="footsteps",
                name="Footsteps",
                file_path="effects/footsteps.mp3",
                audio_type=AudioType.EFFECT,
                volume=0.5,
                tags=["walking", "movement"],
            )
        )

        self.register_asset(
            AudioAsset(
                id="quest_complete",
                name="Quest Complete",
                file_path="effects/quest-complete.mp3",
                audio_type=AudioType.EFFECT,
                volume=0.9,
                tags=["success", "achievement", "quest"],
            )
        )

        # Music (optional)
        self.register_asset(
            AudioAsset(
                id="tavern_music",
                name="Tavern Music",
                file_path="music/medieval-tavern.mp3",
                audio_type=AudioType.MUSIC,
                volume=0.3,
                loop=True,
                tags=["background", "medieval", "music"],
            )
        )

    def _initialize_event_mappings(self):
        """Map game events to audio triggers."""
        self.event_mappings = {
            # Gold/money events
            "gold_gained": [AudioEvent("gold_gained", "coin_drop", volume=0.8, delay=0.1)],
            "gold_lost": [AudioEvent("gold_lost", "coin_drop", volume=0.6, delay=0.1)],
            "purchase_made": [
                AudioEvent("purchase_made", "coin_drop", volume=0.7),
                AudioEvent("purchase_made", "drink_pour", volume=0.5, delay=0.5),
            ],
            # Quest events
            "quest_completed": [AudioEvent("quest_completed", "quest_complete", volume=1.0)],
            "quest_started": [AudioEvent("quest_started", "footsteps", volume=0.6)],
            # Movement events
            "room_entered": [
                AudioEvent("room_entered", "door_open", volume=0.7),
                AudioEvent("room_entered", "footsteps", volume=0.4, delay=0.3),
            ],
            # NPC events
            "npc_interaction": [AudioEvent("npc_interaction", "crowd_chatter", volume=0.3, fade_in=0.5)],
            # Ambient events
            "game_start": [
                AudioEvent("game_start", "tavern_ambience", volume=0.4, fade_in=2.0),
                AudioEvent("game_start", "fireplace_crackling", volume=0.2, delay=1.0, fade_in=1.5),
            ],
        }

    def register_asset(self, asset: AudioAsset):
        """Register an audio asset."""
        self.assets[asset.id] = asset
        logger.debug(f"Registered audio asset: {asset.id}")

    def get_asset(self, asset_id: str) -> Optional[AudioAsset]:
        """Get an audio asset by ID."""
        return self.assets.get(asset_id)

    def get_assets_by_type(self, audio_type: AudioType) -> List[AudioAsset]:
        """Get all assets of a specific type."""
        return [asset for asset in self.assets.values() if asset.audio_type == audio_type]

    def get_assets_by_tag(self, tag: str) -> List[AudioAsset]:
        """Get all assets with a specific tag."""
        return [asset for asset in self.assets.values() if tag in asset.tags]

    def trigger_event(self, event_type: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Trigger audio events for a game event."""
        if not self.enabled:
            return []

        events = self.event_mappings.get(event_type, [])
        if not events:
            return []

        audio_commands = []
        for event in events:
            asset = self.get_asset(event.audio_id)
            if not asset:
                logger.warning(f"Audio asset not found: {event.audio_id}")
                continue

            # Calculate final volume
            type_volume = self.volume_settings.get(asset.audio_type, 1.0)
            final_volume = event.volume * type_volume * self.master_volume

            audio_command = {
                "action": "play",
                "asset_id": asset.id,
                "file_path": f"/static/audio/{asset.file_path}",
                "volume": final_volume,
                "loop": asset.loop,
                "delay": event.delay,
                "fade_in": event.fade_in,
                "fade_out": event.fade_out,
                "audio_type": asset.audio_type.value,
            }

            audio_commands.append(audio_command)

        return audio_commands

    def set_volume(self, audio_type: AudioType, volume: float):
        """Set volume for a specific audio type."""
        self.volume_settings[audio_type] = max(0.0, min(1.0, volume))

    def set_master_volume(self, volume: float):
        """Set master volume."""
        self.master_volume = max(0.0, min(1.0, volume))

    def enable_audio(self, enabled: bool = True):
        """Enable or disable audio."""
        self.enabled = enabled

    def get_client_config(self) -> Dict[str, Any]:
        """Get configuration for client-side audio management."""
        return {
            "enabled": self.enabled,
            "master_volume": self.master_volume,
            "volume_settings": {k.value: v for k, v in self.volume_settings.items()},
            "assets": {
                asset_id: {
                    "id": asset.id,
                    "name": asset.name,
                    "file_path": f"/static/audio/{asset.file_path}",
                    "type": asset.audio_type.value,
                    "volume": asset.volume,
                    "loop": asset.loop,
                    "tags": asset.tags,
                }
                for asset_id, asset in self.assets.items()
            },
        }

    def create_ambient_playlist(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Create an ambient playlist based on tags."""
        matching_assets = []
        for tag in tags:
            matching_assets.extend(self.get_assets_by_tag(tag))

        # Remove duplicates and filter for ambient sounds
        unique_assets = []
        seen = set()
        for asset in matching_assets:
            if asset.id not in seen and asset.audio_type == AudioType.AMBIENT:
                unique_assets.append(asset)
                seen.add(asset.id)

        playlist = []
        for asset in unique_assets:
            type_volume = self.volume_settings.get(asset.audio_type, 1.0)
            final_volume = asset.volume * type_volume * self.master_volume

            playlist.append(
                {
                    "asset_id": asset.id,
                    "file_path": f"/static/audio/{asset.file_path}",
                    "volume": final_volume,
                    "loop": asset.loop,
                    "name": asset.name,
                }
            )

        return playlist


class GameAudioIntegration:
    """Integrates audio system with game events."""

    def __init__(self, audio_manager: AudioManager):
        self.audio_manager = audio_manager
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def process_game_events(self, events: List[Dict[str, Any]], session_id: str) -> List[Dict[str, Any]]:
        """Process game events and return audio commands."""
        audio_commands = []

        for event in events:
            event_type = event.get("type", "")
            event_data = event.get("data", {})

            # Map different event types to audio events
            if event_type == "success" and "gold" in event.get("message", "").lower():
                commands = self.audio_manager.trigger_event("gold_gained")
            elif event_type == "quest" and "completed" in event.get("message", "").lower():
                commands = self.audio_manager.trigger_event("quest_completed")
            elif event_type == "quest" and "started" in event.get("message", "").lower():
                commands = self.audio_manager.trigger_event("quest_started")
            elif event_type == "room_change":
                commands = self.audio_manager.trigger_event("room_entered")
            elif event_type == "npc_interaction":
                commands = self.audio_manager.trigger_event("npc_interaction")
            else:
                commands = []

            audio_commands.extend(commands)

        return audio_commands

    def initialize_session_audio(self, session_id: str) -> List[Dict[str, Any]]:
        """Initialize audio for a new session."""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {"initialized": True, "ambient_playing": [], "last_activity": 0}

            # Return initial ambient audio
            return self.audio_manager.trigger_event("game_start")

        return []

    def get_session_audio_state(self, session_id: str) -> Dict[str, Any]:
        """Get audio state for a session."""
        return self.active_sessions.get(session_id, {})

    def cleanup_session_audio(self, session_id: str):
        """Clean up audio for a session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]


# Global audio manager instance
audio_manager = AudioManager()
game_audio = GameAudioIntegration(audio_manager)


# Utility functions for easy integration
def trigger_audio_event(event_type: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Trigger an audio event and return commands for the client."""
    return audio_manager.trigger_event(event_type, context)


def get_audio_config() -> Dict[str, Any]:
    """Get audio configuration for client."""
    return audio_manager.get_client_config()


def process_game_audio(events: List[Dict[str, Any]], session_id: str) -> List[Dict[str, Any]]:
    """Process game events for audio triggers."""
    return game_audio.process_game_events(events, session_id)


def initialize_session_audio(session_id: str) -> List[Dict[str, Any]]:
    """Initialize audio for a new game session."""
    return game_audio.initialize_session_audio(session_id)
