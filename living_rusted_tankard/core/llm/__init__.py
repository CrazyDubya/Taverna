"""Core LLM functionality for The Living Rusted Tankard.

This module provides interfaces to various LLM-powered components
used throughout the game, including the command parser and narrator.
"""

from .parser import parse, format_command_output, CommandSchema, CommandOutput, ActionType
from .narrator import narrator, Narrator
from .ollama_client import OllamaClient

__all__ = [
    # Parser components
    "parse",
    "format_command_output",
    "CommandSchema",
    "CommandOutput",
    "ActionType",
    # Narration
    "narrator",
    "Narrator",
    # LLM client
    "OllamaClient",
]
