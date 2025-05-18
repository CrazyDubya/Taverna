"""Tests for the narrative caching system."""

import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.llm.narrative_cache import NarrativeCache
from core.llm.narrative_decorators import cached_narrative, validate_state

# Test data
SAMPLE_STATE_1 = {
    "player": {"name": "Test Player", "location": "tavern"},
    "time": "morning",
    "npc": {"name": "Barkeep", "mood": "friendly"}
}

SAMPLE_STATE_2 = {
    "player": {"name": "Test Player", "location": "tavern"},
    "time": "afternoon",  # Only this field is different
    "npc": {"name": "Barkeep", "mood": "friendly"}
}

SAMPLE_STATE_INVALID = "not a dictionary"


def test_generate_state_hash():
    """Test that the state hash is consistent for the same input."""
    cache = NarrativeCache()
    hash1 = cache._generate_state_hash(SAMPLE_STATE_1)
    hash2 = cache._generate_state_hash(SAMPLE_STATE_1)

    # Same state should produce same hash
    assert hash1 == hash2

    # Different state should produce different hash
    hash3 = cache._generate_state_hash(SAMPLE_STATE_2)
    assert hash1 != hash3


def test_cache_operations(tmp_path):
    """Test basic cache operations."""
    cache_dir = tmp_path / "test_cache"
    cache = NarrativeCache(str(cache_dir))

    # Cache should be empty initially
    assert cache.get_cached_narrative(SAMPLE_STATE_1) is None

    # Add to cache
    test_narrative = "This is a test narrative."
    cache.cache_narrative(SAMPLE_STATE_1, test_narrative)

    # Should be able to retrieve from cache
    assert cache.get_cached_narrative(SAMPLE_STATE_1) == test_narrative

    # Different state should not return the same narrative
    assert cache.get_cached_narrative(SAMPLE_STATE_2) is None


def test_cache_persistence(tmp_path):
    """Test that the cache persists between instances."""
    cache_dir = tmp_path / "test_cache"

    # Create cache and add item
    cache1 = NarrativeCache(str(cache_dir))
    test_narrative = "Persistent test narrative"
    cache1.cache_narrative(SAMPLE_STATE_1, test_narrative)

    # New instance should load the cached item
    cache2 = NarrativeCache(str(cache_dir))
    assert cache2.get_cached_narrative(SAMPLE_STATE_1) == test_narrative


def test_cache_decorator(tmp_path):
    """Test the @cached_narrative decorator."""
    # Create a test function
    call_count = 0

    @cached_narrative(str(tmp_path))
    def generate_narrative(state):
        nonlocal call_count
        call_count += 1
        return f"Generated narrative for {state['time']}"

    # First call should generate the narrative
    result1 = generate_narrative(SAMPLE_STATE_1)
    assert call_count == 1
    assert "morning" in result1

    # Second call with same state should use cache
    result2 = generate_narrative(SAMPLE_STATE_1)
    assert call_count == 1  # Should not increment
    assert result2 == result1

    # Different state should generate new narrative
    result3 = generate_narrative(SAMPLE_STATE_2)
    assert call_count == 2
    assert "afternoon" in result3


def test_validate_state_decorator():
    """Test the @validate_state decorator."""
    @validate_state(required_keys=["player", "time"])
    def generate_narrative(state):
        return "Valid state"

    # Should work with valid state
    result = generate_narrative({"player": {}, "time": "now"})
    assert result == "Valid state"

    # Should raise with invalid state
    with pytest.raises(ValueError):
        generate_narrative({"player": {}})  # Missing 'time'

    with pytest.raises(ValueError):
        generate_narrative("not a dict")  # Not a dictionary
