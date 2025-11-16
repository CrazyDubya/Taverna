"""Tests for the LLM parser module."""

import pytest

import json
import sys
from dataclasses import asdict
from unittest.mock import MagicMock, Mock, patch

# Create a mock requests module
mock_requests = Mock()
requests_mock = MagicMock()
requests_mock.post.return_value = MagicMock()
requests_mock.post.return_value.json.return_value = {}
requests_mock.exceptions = MagicMock()
requests_mock.exceptions.RequestException = Exception

# Patch sys.modules to include our mock requests
sys.modules["requests"] = requests_mock

# Now import the parser

from core.llm.parser import Parser, GameSnapshot

# Test data
TEST_SNAPSHOT = GameSnapshot(
    location="tavern_main",
    time_of_day="evening",
    visible_objects=["bar", "tables", "door", "bulletin_board"],
    visible_npcs=["bartender", "merchant", "stranger"],
    player_state={"gold": 50, "has_room": False, "tiredness": 0},
)

# Helper function to create a mock LLM response


def create_mock_llm_response(action: str, target: str = None, **extras):
    return {
        "response": json.dumps(
            {"action": action, "target": target, "extras": extras or {}}
        )
    }


# Test the regex fallback parser


def test_regex_fallback_parser():
    """Test the regex fallback parser with various inputs."""
    parser = Parser(use_llm=False)

    # Test look commands
    cmd = parser.parse("look", TEST_SNAPSHOT)
    assert cmd["action"] == "look"
    assert cmd["target"] == "room"

    cmd = parser.parse("look at bar", TEST_SNAPSHOT)
    assert cmd["action"] == "look"
    assert cmd["target"] == "bar"

    # Test movement - this should match the pattern (north|south|east|west|up|down|in|out)
    cmd = parser.parse("go north", TEST_SNAPSHOT)
    assert cmd["action"] == "go"
    assert cmd["target"] == "north"

    # Test interaction
    cmd = parser.parse("talk to bartender", TEST_SNAPSHOT)
    assert cmd["action"] == "talk"
    assert cmd["target"] == "bartender"

    # Test unknown command - should be caught by the catch-all pattern
    cmd = parser.parse("do something weird", TEST_SNAPSHOT)
    assert cmd["action"] == "unknown"
    assert cmd["target"] == "do something weird"


# Test LLM parser with mocks


def test_llm_parser():
    """Test the LLM parser with mocked responses."""
    # Setup mock response for look command
    mock_response = MagicMock()
    mock_response.json.return_value = create_mock_llm_response("look", "room")
    mock_response.raise_for_status.return_value = None

    # Configure the mock to return our response
    requests_mock.post.return_value = mock_response

    # Test with LLM
    parser = Parser(use_llm=True, llm_endpoint="http://test-endpoint")
    cmd = parser.parse("look around", TEST_SNAPSHOT)

    assert cmd["action"] == "look"
    assert cmd["target"] == "room"

    # Verify LLM was called
    assert requests_mock.post.called

    # Test with a more complex command
    mock_response.json.return_value = create_mock_llm_response(
        "ask", "bartender", topic="rumors"
    )

    cmd = parser.parse("ask the bartender about rumors", TEST_SNAPSHOT)
    assert cmd["action"] == "ask"
    assert cmd["target"] == "bartender"
    assert cmd["extras"].get("topic") == "rumors"


# Test LLM fallback to regex


def test_llm_fallback():
    """Test that the parser falls back to regex when LLM fails."""
    # Make the LLM call raise an exception
    requests_mock.post.side_effect = Exception("API error")

    # This should fall back to regex parsing
    parser = Parser(use_llm=True, llm_endpoint="http://test-endpoint")
    cmd = parser.parse("look at door", TEST_SNAPSHOT)

    # Should still get a valid command from regex
    assert cmd["action"] == "look"
    assert cmd["target"] == "door"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
