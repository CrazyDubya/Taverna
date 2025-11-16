"""
Configuration constants for The Living Rusted Tankard.

This module centralizes all configuration values, making them easier to
maintain and modify. Previously scattered magic numbers are collected here.
"""

from dataclasses import dataclass
from typing import Dict, Any
import os


@dataclass
class GameConfig:
    """Central configuration for game mechanics and behavior."""

    # Economy Configuration
    STARTING_GOLD: int = 40
    ROOM_COST: int = 10
    STORAGE_CHEST_COST_MODIFIER: int = 5
    JOB_COOLDOWN_HOURS: int = 24
    GAMBLING_MIN_BET: int = 1
    GAMBLING_MAX_BET: int = 100

    # Player Configuration
    MAX_TIREDNESS: int = 100
    TIREDNESS_RECOVERY_RATE: float = 0.5  # Per hour of rest
    STARTING_HEALTH: int = 100

    # NPC Configuration
    NPC_UPDATE_INTERVAL: float = 0.1  # Seconds
    MAX_RELATIONSHIP: float = 1.0
    MIN_RELATIONSHIP: float = -1.0
    NPC_INTERACTION_TIMEOUT: int = 30  # Seconds

    # Performance Configuration
    CACHE_TTL: float = 1.0  # Cache time-to-live in seconds
    MAX_EVENTS_IN_QUEUE: int = 100
    MAX_ACTIONS_HISTORY: int = 20
    HTTP_TIMEOUT: int = 30  # Default HTTP timeout

    # AI Configuration
    AI_THINKING_DELAY: float = 2.0  # Seconds between AI actions
    AI_MAX_ACTIONS_PER_SESSION: int = 50
    LLM_REQUEST_TIMEOUT: int = 30

    # Server Configuration
    DEFAULT_GAME_PORT: int = 8888
    AI_OBSERVER_PORT: int = 8889
    MAX_CONCURRENT_SESSIONS: int = 100
    SESSION_TIMEOUT_HOURS: int = 24

    # Time Configuration
    HOURS_PER_DAY: int = 24
    DAYS_PER_WEEK: int = 7
    WEEKS_PER_MONTH: int = 4
    MONTHS_PER_YEAR: int = 12

    # Debug Configuration
    LOG_LEVEL: str = "INFO"
    ENABLE_DEBUG_MODE: bool = False

    @classmethod
    def from_env(cls) -> "GameConfig":
        """Load configuration from environment variables."""
        config = cls()

        # Override with environment variables if present
        for field_name in cls.__dataclass_fields__:
            env_name = f"TAVERNA_{field_name}"
            env_value = os.environ.get(env_name)

            if env_value is not None:
                field_type = cls.__dataclass_fields__[field_name].type
                try:
                    if field_type == int:
                        setattr(config, field_name, int(env_value))
                    elif field_type == float:
                        setattr(config, field_name, float(env_value))
                    elif field_type == bool:
                        setattr(
                            config,
                            field_name,
                            env_value.lower() in ("true", "1", "yes", "on"),
                        )
                    else:
                        setattr(config, field_name, env_value)
                except (ValueError, TypeError) as e:
                    print(
                        f"Warning: Could not parse {env_name}={env_value} as {field_type}: {e}"
                    )

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {field: getattr(self, field) for field in self.__dataclass_fields__}


# Global configuration instance
CONFIG = GameConfig.from_env()


# Convenience functions for common configurations
def get_starting_gold() -> int:
    """Get the starting gold amount for new players."""
    return CONFIG.STARTING_GOLD


def get_room_cost() -> int:
    """Get the cost to rent a room for one night."""
    return CONFIG.ROOM_COST


def get_http_timeout() -> int:
    """Get the default HTTP timeout."""
    return CONFIG.HTTP_TIMEOUT


def get_ai_thinking_delay() -> float:
    """Get the AI thinking delay between actions."""
    return CONFIG.AI_THINKING_DELAY


def get_max_tiredness() -> int:
    """Get the maximum tiredness level."""
    return CONFIG.MAX_TIREDNESS


def get_npc_update_interval() -> float:
    """Get the NPC update interval."""
    return CONFIG.NPC_UPDATE_INTERVAL


def get_cache_ttl() -> float:
    """Get the cache time-to-live."""
    return CONFIG.CACHE_TTL


def get_max_events() -> int:
    """Get the maximum number of events to keep in queue."""
    return CONFIG.MAX_EVENTS_IN_QUEUE


# Legacy constants for backward compatibility
ROOM_COST = CONFIG.ROOM_COST
STORAGE_CHEST_COST_MODIFIER = CONFIG.STORAGE_CHEST_COST_MODIFIER
STARTING_GOLD = CONFIG.STARTING_GOLD
