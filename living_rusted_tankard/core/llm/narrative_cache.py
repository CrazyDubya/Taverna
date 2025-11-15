"""
Narrative Caching Layer

This module provides a caching mechanism for narrative generation to improve performance
by reusing previously generated narratives when the game state hasn't changed.
"""

import hashlib
import json
from typing import Any, Dict, Optional
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class NarrativeCache:
    """
    A cache for narrative generation that stores and retrieves narratives based on
    a hash of the game state.
    """

    def __init__(self, cache_dir: str = ".narrative_cache"):
        """
        Initialize the narrative cache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache: Dict[str, str] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load the cache from disk if it exists."""
        cache_file = self.cache_dir / "narrative_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached narratives from {cache_file}")
            except Exception as e:
                logger.error(f"Error loading narrative cache: {e}")
                self.cache = {}

    def _save_cache(self) -> None:
        """Save the cache to disk."""
        cache_file = self.cache_dir / "narrative_cache.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving narrative cache: {e}")

    def _generate_state_hash(self, state: Dict[str, Any]) -> str:
        """
        Generate a hash from the game state dictionary.

        Args:
            state: The game state dictionary

        Returns:
            A hex digest of the state hash
        """
        # Convert the state to a JSON string with sorted keys for consistent hashing
        state_str = json.dumps(state, sort_keys=True)
        return hashlib.md5(state_str.encode("utf-8")).hexdigest()

    def get_cached_narrative(self, state: Dict[str, Any]) -> Optional[str]:
        """
        Get a cached narrative for the given game state, if it exists.

        Args:
            state: The game state dictionary

        Returns:
            The cached narrative, or None if not found
        """
        state_hash = self._generate_state_hash(state)
        return self.cache.get(state_hash)

    def cache_narrative(self, state: Dict[str, Any], narrative: str) -> None:
        """
        Cache a narrative for the given game state.

        Args:
            state: The game state dictionary
            narrative: The generated narrative to cache
        """
        state_hash = self._generate_state_hash(state)
        self.cache[state_hash] = narrative
        self._save_cache()
        logger.debug(f"Cached narrative for state {state_hash[:8]}...")

    def clear_cache(self) -> None:
        """Clear the entire cache."""
        self.cache = {}
        self._save_cache()
        logger.info("Narrative cache cleared")
