"""Integration tests for the LLM Parser with Ollama."""

import asyncio
import json
import logging
import os
from pathlib import Path

import pytest

from core.llm.parser import parse, CommandSchema, ActionType
from core.llm.ollama_client import OllamaClient

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test cases
TEST_CASES = [
    ("look around", {"action": ActionType.LOOK}),
    ("talk to gene", {"action": ActionType.TALK, "target": "gene"}),
    ("ask gene about the key", {"action": "ask", "target": "gene", "subject": "key"}),
    ("gamble 10 gold", {"action": ActionType.GAMBLE, "amount": 10}),
    ("rent a room", {"action": ActionType.RENT}),
    ("go to sleep", {"action": ActionType.SLEEP}),
    ("what do I have", {"action": ActionType.INVENTORY}),
    ("help", {"action": ActionType.HELP}),
]

# Sample game state
SAMPLE_GAME_STATE = {
    "time": "14:30",
    "location": "The Rusted Tankard",
    "npcs": ["Gene", "Marlene", "Old Tom"],
    "items": ["mug", "chair", "table", "dice"],
    "gold": 50,
    "has_room": False,
}


@pytest.mark.asyncio
async def test_llm_parser_integration():
    """Test the LLM parser with the Ollama API."""
    # Skip if OLLAMA_HOST is not set
    if not os.getenv("OLLAMA_HOST"):
        pytest.skip("OLLAMA_HOST environment variable not set")

    # Initialize the Ollama client
    client = OllamaClient(base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

    # Test each case
    for input_text, expected in TEST_CASES:
        logger.info(f"Testing input: {input_text}")

        # Call the parse function
        result = await parse(
            input_text=input_text,
            game_state=SAMPLE_GAME_STATE,
            use_llm=True
        )

        # Log the result
        logger.info(f"Result: {result}")

        # Basic assertions
        assert result.success, f"Failed to parse input: {input_text}"
        assert result.command is not None, f"No command returned for input: {input_text}"

        # Verify action matches
        if isinstance(expected["action"], ActionType):
            assert result.command.action == expected["action"], \
                f"Action mismatch for input: {input_text}"
        else:
            assert str(result.command.action).lower() == expected["action"].lower(), \
                f"Action string mismatch for input: {input_text}"

        # Verify target if expected
        if "target" in expected:
            assert result.command.target is not None, \
                f"Expected target for input: {input_text}"
            assert str(result.command.target).lower() == expected["target"].lower(), \
                f"Target mismatch for input: {input_text}"

        # Verify subject if expected
        if "subject" in expected:
            assert result.command.subject is not None, \
                f"Expected subject for input: {input_text}"
            assert expected["subject"].lower() in str(result.command.subject).lower(), \
                f"Subject mismatch for input: {input_text}"

        # Verify amount if expected
        if "amount" in expected:
            assert result.command.amount is not None, \
                f"Expected amount for input: {input_text}"
            assert result.command.amount == expected["amount"], \
                f"Amount mismatch for input: {input_text}"

    # Clean up
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_llm_parser_integration())
