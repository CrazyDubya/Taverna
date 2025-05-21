#!/usr/bin/env python3
"""Test script for the CLI interface."""
import sys
import cmd
from unittest.mock import patch, MagicMock
from cli import GameCLI
from core.game_state import GameState

def test_cli_interaction():
    """Test basic CLI interaction."""
    game = GameState()
    cli = GameCLI(game)
    
    # Test status command
    print("=== Testing status command ===")
    cli.onecmd("status")
    
    # Test time command
    print("\n=== Testing time command ===")
    cli.onecmd("time")
    
    # Test inventory command
    print("\n=== Testing inventory command ===")
    cli.onecmd("inventory")
    
    # Test help command
    print("\n=== Testing help command ===")
    cli.onecmd("help")

if __name__ == "__main__":
    print("Starting CLI tests...")
    test_cli_interaction()
    print("\nAll tests completed.")
