#!/usr/bin/env python3
"""Command-line interface for The Living Rusted Tankard."""
import cmd
from core.game import GameState

class GameCLI(cmd.Cmd):
    """Simple command-line interface for the game."""
    
    intro = 'Welcome to The Living Rusted Tankard. Type help or ? to list commands.\n'
    prompt = '(tavern) '
    
    def __init__(self, game_state):
        super().__init__()
        self.game = game_state
    
    def do_status(self, arg):
        """Show current game status."""
        player = self.game.player
        print(f"Gold: {player.gold}")
        print(f"Has room: {player.has_room}")
        print(f"Tiredness: {player.tiredness:.1f}")
        
        # Show present NPCs
        present_npcs = self.game.npc_manager.get_present_npcs()
        if present_npcs:
            print("\nPresent NPCs:")
            for npc in present_npcs:
                print(f"- {npc.name}: {npc.description}")
    
    def do_gamble(self, arg):
        """Gamble some gold. Usage: gamble <amount> [npc_id]"""
        try:
            args = arg.split()
            if not args:
                print("Usage: gamble <amount> [npc_id]")
                return
                
            amount = int(args[0])
            npc_id = args[1] if len(args) > 1 else None
            
            try:
                won, winnings = self.game.economy.gamble(
                    self.game.player, 
                    amount, 
                    npc_id
                )
                result = "won" if won else "lost"
                print(f"You {result} {abs(winnings)} gold!")
            except ValueError as e:
                print(f"Error: {e}")
                
        except (ValueError, IndexError):
            print("Invalid amount. Usage: gamble <amount> [npc_id]")
    
    def do_rest(self, arg):
        """Rest for a while (if you have a room)."""
        if not self.game.player.has_room:
            print("You need to rent a room first!")
            return
            
        hours = 8  # Default rest time
        if arg.isdigit():
            hours = min(int(arg), 24)  # Cap at 24 hours
            
        if self.game.player.rest(hours):
            print(f"You rest for {hours} hours.")
        else:
            print("You can't rest right now.")
    
    def do_rent(self, arg):
        """Rent a room for the night (costs 10 gold)."""
        if self.game.player.has_room:
            print("You already have a room!")
            return
            
        if self.game.player.spend_gold(10):
            self.game.player.has_room = True
            print("You've rented a room for the night!")
        else:
            print("You can't afford a room (10 gold needed).")
    
    def do_quit(self, arg):
        """Quit the game."""
        print("Thanks for playing!")
        return True

def main():
    """Main entry point for the CLI."""
    game = GameState()
    
    # Add some test NPCs
    from core.npc import NPC
    game.npc_manager.add_npc(NPC(
        id="barkeep",
        name="Old Tom",
        description="The grizzled barkeep with a mysterious past.",
        schedule=[(8, 24)],  # Works from 8:00 to midnight
        departure_chance=0.0  # Never leaves
    ))
    
    game.npc_manager.add_npc(NPC(
        id="patron1",
        name="Sally",
        description="A regular patron who always seems to be here.",
        schedule=[(12, 23)],  # Afternoons and evenings
        departure_chance=0.3
    ))
    
    # Start the CLI
    cli = GameCLI(game)
    cli.cmdloop()

if __name__ == "__main__":
    main()
