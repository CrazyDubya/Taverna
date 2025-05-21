#!/usr/bin/env python3
"""
Starter script for The Living Rusted Tankard game.
This script initializes and starts the game in CLI mode.
"""
import sys
import os
from pathlib import Path

# Add the living_rusted_tankard directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(script_dir, "living_rusted_tankard")
sys.path.insert(0, project_dir)

try:
    # Import required modules
    from core.game_state import GameState
    from core.npc import NPC
    from cli import GameCLI
    
    # Initialize the game state
    print("Starting The Living Rusted Tankard...")
    game = GameState()
    
    # Add test NPCs for demonstration
    from core.npc import NPCType, NPCDisposition
    
    game.npc_manager.add_npc(NPC(
        id="barkeep",
        definition_id="barkeep_def",
        name="Old Tom",
        description="The grizzled barkeep with a mysterious past.",
        npc_type=NPCType.BARKEEP,
        disposition=NPCDisposition.FRIENDLY,
        schedule=[(8, 24)],  # Works from 8:00 to midnight
        departure_chance=0.0  # Never leaves
    ))
    
    game.npc_manager.add_npc(NPC(
        id="patron1",
        definition_id="patron1_def",
        name="Sally",
        description="A regular patron who always seems to be here.",
        npc_type=NPCType.PATRON,
        disposition=NPCDisposition.NEUTRAL,
        schedule=[(12, 23)],  # Afternoons and evenings
        departure_chance=0.3
    ))
    
    print("\nType 'help' to see available commands and 'inventory' to check your items.")
    print("Try 'status' to see your current status in the game.\n")
    
    # Start the command-line interface
    cli = GameCLI(game)
    cli.cmdloop()
    
except ImportError as e:
    print(f"Error: Failed to import required modules. {e}")
    print("Make sure you have installed all dependencies with 'poetry install'")
    
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()