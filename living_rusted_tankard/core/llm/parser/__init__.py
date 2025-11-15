"""LLM Parser module for The Living Rusted Tankard.

This module provides functionality to parse natural language input from players
and convert it into structured commands that the game can understand. It uses
a local Ollama LLM for natural language understanding with a fallback to
regex-based parsing when the LLM is not available.
"""

from .parser import parse, format_command_output, Parser, GameSnapshot, Command
from .prompts import PARSER_PROMPT
from .schemas import CommandSchema, CommandOutput, ActionType
from ..ollama_client import OllamaClient

__all__ = [
    # Core functions
    "parse",
    "format_command_output",
    # Classes
    "Parser",
    "GameSnapshot",
    "Command",
    "CommandSchema",
    "CommandOutput",
    "ActionType",
    "OllamaClient",
    # Constants
    "PARSER_PROMPT",
]
