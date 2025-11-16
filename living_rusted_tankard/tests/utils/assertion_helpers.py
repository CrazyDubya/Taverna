"""Custom assertion helpers for testing."""
import json
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from unittest.mock import Mock


def assert_game_state_valid(game_state: Dict[str, Any]):
    """Assert that a game state has required fields and valid structure."""
    required_fields = ["session_id", "player", "current_location"]

    for field in required_fields:
        assert field in game_state, f"Game state missing required field: {field}"

    # Validate player structure
    player = game_state["player"]
    assert isinstance(player, dict), "Player must be a dictionary"
    assert "name" in player, "Player must have a name"
    assert "gold" in player, "Player must have gold amount"
    assert "health" in player, "Player must have health"

    # Validate numeric fields
    assert isinstance(player["gold"], (int, float)), "Player gold must be numeric"
    assert isinstance(player["health"], (int, float)), "Player health must be numeric"
    assert player["gold"] >= 0, "Player gold cannot be negative"
    assert player["health"] >= 0, "Player health cannot be negative"


def assert_npc_valid(npc_data: Dict[str, Any]):
    """Assert that NPC data has required fields and valid structure."""
    required_fields = ["name", "personality", "location"]

    for field in required_fields:
        assert field in npc_data, f"NPC missing required field: {field}"

    assert isinstance(npc_data["name"], str), "NPC name must be a string"
    assert len(npc_data["name"].strip()) > 0, "NPC name cannot be empty"
    assert isinstance(npc_data["personality"], str), "NPC personality must be a string"
    assert isinstance(npc_data["location"], str), "NPC location must be a string"


def assert_player_valid(player_data: Dict[str, Any]):
    """Assert that player data has required fields and valid structure."""
    required_fields = ["name", "gold", "health"]

    for field in required_fields:
        assert field in player_data, f"Player missing required field: {field}"

    assert isinstance(player_data["name"], str), "Player name must be a string"
    assert len(player_data["name"].strip()) > 0, "Player name cannot be empty"
    assert isinstance(player_data["gold"], (int, float)), "Player gold must be numeric"
    assert isinstance(
        player_data["health"], (int, float)
    ), "Player health must be numeric"

    # Business logic validations
    assert player_data["gold"] >= 0, "Player gold cannot be negative"
    assert player_data["health"] >= 0, "Player health cannot be negative"

    if "max_health" in player_data:
        assert (
            player_data["health"] <= player_data["max_health"]
        ), "Player health cannot exceed max health"


def assert_economy_transaction_valid(transaction: Dict[str, Any]):
    """Assert that an economy transaction is valid."""
    required_fields = ["type", "amount", "participant"]

    for field in required_fields:
        assert field in transaction, f"Transaction missing required field: {field}"

    valid_types = ["purchase", "sale", "job_payment", "gambling_win", "gambling_loss"]
    assert (
        transaction["type"] in valid_types
    ), f"Invalid transaction type: {transaction['type']}"

    assert isinstance(
        transaction["amount"], (int, float)
    ), "Transaction amount must be numeric"
    assert transaction["amount"] >= 0, "Transaction amount cannot be negative"
    assert isinstance(transaction["participant"], str), "Participant must be a string"


def assert_event_structure(event: Dict[str, Any]):
    """Assert that an event has proper structure."""
    required_fields = ["type", "data", "timestamp"]

    for field in required_fields:
        assert field in event, f"Event missing required field: {field}"

    assert isinstance(event["type"], str), "Event type must be a string"
    assert len(event["type"].strip()) > 0, "Event type cannot be empty"
    assert isinstance(
        event["timestamp"], (int, float)
    ), "Event timestamp must be numeric"
    assert event["timestamp"] > 0, "Event timestamp must be positive"


def assert_llm_response_valid(response: Dict[str, Any]):
    """Assert that an LLM response has valid structure."""
    assert isinstance(response, dict), "LLM response must be a dictionary"
    assert "response" in response, "LLM response must contain 'response' field"
    assert isinstance(response["response"], str), "LLM response text must be a string"
    assert len(response["response"].strip()) > 0, "LLM response cannot be empty"

    if "confidence" in response:
        assert isinstance(
            response["confidence"], (int, float)
        ), "Confidence must be numeric"
        assert 0 <= response["confidence"] <= 1, "Confidence must be between 0 and 1"


def assert_api_response_format(
    response: Dict[str, Any], expected_status: str = "success"
):
    """Assert that an API response has proper format."""
    assert isinstance(response, dict), "API response must be a dictionary"
    assert "status" in response, "API response must contain 'status' field"
    assert (
        response["status"] == expected_status
    ), f"Expected status '{expected_status}', got '{response['status']}'"

    if expected_status == "error":
        assert "error" in response, "Error response must contain 'error' field"
        assert isinstance(response["error"], str), "Error message must be a string"
    elif expected_status == "success":
        assert "data" in response, "Success response must contain 'data' field"


def assert_session_valid(session_data: Dict[str, Any]):
    """Assert that session data is valid."""
    required_fields = ["session_id", "player_name", "created_at"]

    for field in required_fields:
        assert field in session_data, f"Session missing required field: {field}"

    assert isinstance(session_data["session_id"], str), "Session ID must be a string"
    assert len(session_data["session_id"].strip()) > 0, "Session ID cannot be empty"
    assert isinstance(session_data["player_name"], str), "Player name must be a string"
    assert isinstance(
        session_data["created_at"], (int, float)
    ), "Created at must be numeric"


def assert_mock_called_with_pattern(mock_obj: Mock, call_pattern: Dict[str, Any]):
    """Assert that a mock was called with arguments matching a pattern."""
    assert mock_obj.called, "Mock was not called"

    # Get the last call
    last_call = mock_obj.call_args

    if "args" in call_pattern:
        expected_args = call_pattern["args"]
        actual_args = last_call.args if last_call else ()
        assert (
            actual_args == expected_args
        ), f"Expected args {expected_args}, got {actual_args}"

    if "kwargs" in call_pattern:
        expected_kwargs = call_pattern["kwargs"]
        actual_kwargs = last_call.kwargs if last_call else {}

        for key, expected_value in expected_kwargs.items():
            assert key in actual_kwargs, f"Expected kwarg '{key}' not found"
            assert (
                actual_kwargs[key] == expected_value
            ), f"Expected {key}={expected_value}, got {key}={actual_kwargs[key]}"


def assert_async_function_called(async_mock: Mock, timeout: float = 1.0):
    """Assert that an async function was called within timeout."""

    def was_called():
        return async_mock.called

    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        if was_called():
            return
        # Small delay to prevent busy waiting
        asyncio.create_task(asyncio.sleep(0.01))

    assert False, f"Async function was not called within {timeout} seconds"


def assert_json_serializable(data: Any):
    """Assert that data is JSON serializable."""
    try:
        json.dumps(data)
    except (TypeError, ValueError) as e:
        assert False, f"Data is not JSON serializable: {e}"


def assert_performance_within_limits(
    execution_time: float,
    max_time: float,
    memory_mb: float = None,
    max_memory_mb: float = None,
):
    """Assert that performance metrics are within acceptable limits."""
    assert (
        execution_time <= max_time
    ), f"Execution time {execution_time:.3f}s exceeds limit {max_time}s"

    if memory_mb is not None and max_memory_mb is not None:
        assert (
            memory_mb <= max_memory_mb
        ), f"Memory usage {memory_mb:.1f}MB exceeds limit {max_memory_mb}MB"


def assert_list_contains_items_matching(
    items: List[Any],
    matcher: Callable[[Any], bool],
    min_count: int = 1,
    max_count: int = None,
):
    """Assert that a list contains a specific number of items matching a condition."""
    matching_items = [item for item in items if matcher(item)]
    count = len(matching_items)

    assert (
        count >= min_count
    ), f"Expected at least {min_count} matching items, found {count}"

    if max_count is not None:
        assert (
            count <= max_count
        ), f"Expected at most {max_count} matching items, found {count}"


def assert_dict_has_nested_value(data: Dict, key_path: str, expected_value: Any):
    """Assert that a nested dictionary has a specific value at a key path."""
    keys = key_path.split(".")
    current = data

    for key in keys[:-1]:
        assert key in current, f"Key '{key}' not found in path '{key_path}'"
        current = current[key]
        assert isinstance(current, dict), f"Value at '{key}' is not a dictionary"

    final_key = keys[-1]
    assert (
        final_key in current
    ), f"Final key '{final_key}' not found in path '{key_path}'"
    assert (
        current[final_key] == expected_value
    ), f"Expected {expected_value} at '{key_path}', got {current[final_key]}"


def assert_string_contains_all(text: str, required_substrings: List[str]):
    """Assert that a string contains all required substrings."""
    for substring in required_substrings:
        assert substring in text, f"Required substring '{substring}' not found in text"


def assert_string_matches_pattern(text: str, pattern: str):
    """Assert that a string matches a regex pattern."""
    import re

    assert re.search(pattern, text), f"Text does not match pattern '{pattern}'"


def assert_timestamp_recent(timestamp: float, max_age_seconds: float = 60.0):
    """Assert that a timestamp is recent (within max_age_seconds of now)."""
    import time

    current_time = time.time()
    age = current_time - timestamp

    assert age >= 0, f"Timestamp {timestamp} is in the future"
    assert (
        age <= max_age_seconds
    ), f"Timestamp is {age:.1f} seconds old, exceeds max age {max_age_seconds}"
