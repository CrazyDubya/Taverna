#!/usr/bin/env python3
"""
The Living Rusted Tankard - A text-based RPG where time moves forward and choices matter.
"""
import cmd
import sys
import os
from pathlib import Path
from typing import Optional

from core.game_state import GameState
from utils import snapshot_taker, save_game_state, load_game_state, get_latest_save

# Constants
SAVE_DIR = 'saves'

def print_banner():
    """Print the game banner."""
    print("""
  _______ _                   _____           _           _   _____         _           _     
 |__   __| |                 |  __ \         | |         | | |_   _|       | |         | |    
    | |  | |_   _ _ __ _ __  | |__) |   _  __| | __ _  __| |   | |  _ __ __| | __ _  __| |___ 
    | |  | | | | | '__| '_ \ |  _  / | | |/ _` |/ _` |/ _` |   | | | '__/ _` |/ _` |/ _` / __|
    | |  | | |_| | |  | | | || | \ \ |_| | (_| | (_| | (_| |  _| |_| | | (_| | (_| | (_| \__ \
    |_|  |_|\__,_|_|  |_| |_||_|  \_\__,_|\__,_|\__,_| |_____|_|  \__,_|\__,_|\__,_|___/
    """)
    print("Welcome to The Rusted Tankard, where time moves forward and choices matter...")
    print("Type 'help' for a list of commands.\n")
    print("Available commands: look, wait, save, load, quit\n")

class GameShell(cmd.Cmd):
    """Simple command shell for the game."""
    prompt = "> "
    
    def __init__(self, game_state, save_dir='saves'):
        super().__init__()
        self.game_state = game_state
        self.should_quit = False
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
    
    def emptyline(self):
        """Do nothing on empty input."""
        pass
    
    def default(self, line):
        """Handle unknown commands."""
        result = self.game_state.process_command(line)
        if result.get('should_quit', False):
            self.should_quit = True
            return True
        
        # Print the result message
        print(result['message'])
        
        # Take a snapshot after each command
        self._take_snapshot(line)
    
    def _take_snapshot(self, command: str) -> None:
        """Take a snapshot of the current game state."""
        try:
            # Get the current game state
            state = {
                'time': self.game_state.time_elapsed,
                'player': {
                    'gold': self.game_state.player.gold,
                    'has_room': self.game_state.player.has_room,
                    'tiredness': self.game_state.player.tiredness
                },
                'location': 'The Rusted Tankard',
                'npcs': [
                    {'name': npc.name, 'present': npc.is_present}
                    for npc in getattr(self.game_state, 'npcs', [])
                ]
            }
            
            # Capture and print the snapshot
            snapshot = snapshot_taker.capture(state, command)
            print(snapshot)
            
        except Exception as e:
            print(f"⚠️ Could not take snapshot: {e}")
    
    def do_save(self, arg):
        """Save the current game state. Usage: save [filename]"""
        filename = arg.strip() if arg else None
        try:
            # Get the current game state as a dictionary
            state = self.game_state.to_dict()
            
            # Save the game state
            save_path = save_game_state(
                state,
                save_dir=str(self.save_dir),
                filename=filename
            )
            
            print(f"Game saved to {save_path}")
            return False
            
        except Exception as e:
            print(f"⚠️ Failed to save game: {e}")
            return False
    
    def do_load(self, arg):
        """Load a saved game. Usage: load [filename]"""
        try:
            if arg.strip():
                # Load specific save file
                save_path = self.save_dir / arg.strip()
                if not save_path.exists():
                    print(f"Error: Save file '{arg}' not found.")
                    return False
            else:
                # Load the most recent save
                save_path = get_latest_save(str(self.save_dir))
                if not save_path:
                    print("No save files found.")
                    return False
            
            # Load the game state
            loaded_state = load_game_state(str(save_path))
            
            # Update the current game state
            self.game_state = GameState.from_dict(loaded_state)
            
            print(f"Game loaded from {save_path}")
            self._take_snapshot("load")
            return False
            
        except Exception as e:
            print(f"⚠️ Failed to load game: {e}")
            return False
    
    def do_look(self, arg):
        """Look around the current location."""
        result = self.game_state.process_command('look')
        print(result['message'])
        self._take_snapshot("look")
    
    def do_wait(self, arg):
        """Wait for a number of hours. Usage: wait [hours]"""
        try:
            hours = float(arg) if arg else 1.0
            result = self.game_state.process_command(f'wait {hours}')
            print(result['message'])
            self._take_snapshot(f"wait {hours}")
        except ValueError:
            print("Please specify a valid number of hours.")
    
    def do_quit(self, arg):
        """Quit the game."""
        print("Leaving The Rusted Tankard...")
        return True
    
    def do_help(self, arg):
        """Show help for commands."""
        print("\nAvailable commands:")
        print("  look        - Look around the current location")
        print("  wait [hrs]  - Wait for a number of hours")
        print("  save [name] - Save the current game")
        print("  load [name] - Load a saved game")
        print("  help        - Show this help message")
        print("  quit/exit   - Quit the game\n")
    
    do_exit = do_quit
    do_q = do_quit

def main():
    """Main game loop."""
    print_banner()
    
    try:
        # Try to load the most recent save if it exists
        latest_save = get_latest_save(SAVE_DIR)
        if latest_save and input(f"Load latest save from {latest_save}? (y/n): ").lower() == 'y':
            try:
                loaded_state = load_game_state(latest_save)
                game_state = GameState.from_dict(loaded_state)
                print(f"Loaded game from {latest_save}")
            except Exception as e:
                print(f"⚠️ Could not load save: {e}")
                print("Starting a new game...")
                game_state = GameState()
        else:
            game_state = GameState()
        
        # Start the REPL
        shell = GameShell(game_state, save_dir=SAVE_DIR)
        
        # Print initial state
        print("\nType 'help' for a list of commands.")
        look_result = game_state.process_command('look')
        print(look_result['message'])
        
        # Start the command loop
        shell.cmdloop()
        
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user.")
    except Exception as e:
        print(f"\n⚠️ An error occurred: {e}")
        if input("Would you like to save the game before exiting? (y/n): ").lower() == 'y':
            try:
                save_path = save_game_state(game_state.to_dict(), save_dir=SAVE_DIR)
                print(f"Game saved to {save_path}")
            except Exception as save_error:
                print(f"⚠️ Failed to save game: {save_error}")
    
    print("\nThank you for playing The Rusted Tankard!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Goodbye!")
        sys.exit(0)
