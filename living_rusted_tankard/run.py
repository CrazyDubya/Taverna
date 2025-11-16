#!/usr/bin/env python3
"""
Main entry point for The Living Rusted Tankard.

This script initializes and starts the game.
"""


def main():
    """Run the game."""
    print("Starting The Living Rusted Tankard...")

    try:
        # Import the modules first to check for errors
        import sys
        import os

        # Add current directory to path just in case
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        from core.game_state import GameState
        from cli import GameCLI
        from core.npc import NPC, NPCType, NPCDisposition, NPCSkill
        from pathlib import Path

        # Initialize game state
        game = GameState()
        game.npc_manager.add_npc(
            NPC(
                id="barkeep",
                name="Old Tom",
                description="The grizzled barkeep with a mysterious past.",
                schedule=[(8, 24)],  # Works from 8:00 to midnight
                departure_chance=0.0,  # Never leaves
            )
        )

        game.npc_manager.add_npc(
            NPC(
                id="patron1",
                name="Sally",
                description="A regular patron who always seems to be here.",
                schedule=[(12, 23)],  # Afternoons and evenings
                departure_chance=0.3,
            )
        )

        # Start the CLI
        cli = GameCLI(game)
        cli.cmdloop()

    except ImportError as e:
        print(f"Error: Failed to import required modules. {e}")
        print("Make sure you have installed all dependencies with 'poetry install'")
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
