#!/usr/bin/env python3
"""
Simple game loop for The Living Rusted Tankard.
"""
import time
from core.game_state import GameState

def print_help():
    """Print available commands."""
    print("\nAvailable commands:")
    print("  look - Look around the current location")
    print("  wait [hours] - Wait for a specified number of hours (default: 1)")
    print("  help - Show this help message")
    print("  quit - Quit the game")

def main():
    """Main game loop."""
    print("Welcome to The Living Rusted Tankard!")
    print("Type 'help' for a list of commands.\n")
    
    # Initialize game state
    game_state = GameState()
    
    # Main game loop
    running = True
    while running:
        try:
            # Get player input
            command = input("\n> ").strip().lower()
            
            if not command:
                continue
                
            if command == "quit" or command == "exit":
                print("Goodbye!")
                running = False
            elif command == "help":
                print_help()
            else:
                # Process the command
                result = game_state.process_command(command)
                print(result['message'])
                
                # Update game state
                game_state.update()
                
        except KeyboardInterrupt:
            print("\nUse 'quit' or 'exit' to leave the game.")
        except Exception as e:
            print(f"An error occurred: {e}")
            running = False

if __name__ == "__main__":
    main()
