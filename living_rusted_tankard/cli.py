#!/usr/bin/env python3
"""Command-line interface for The Living Rusted Tankard."""
import cmd
import sys
import time
from typing import Dict, Any, List, Optional
from core.game_state import GameState
from core.npc import NPC, NPCType, NPCDisposition, NPCSkill, NPCInteraction
from core.items import TAVERN_ITEMS


class GameCLI(cmd.Cmd):
    """Command-line interface for The Living Rusted Tankard."""

    intro = """🍺 Welcome to The Living Rusted Tankard 🍺

The heavy wooden door creaks open, revealing the warm glow of the tavern within.
Flickering candlelight dances across weathered stone walls as the aroma of ale
and roasted meat fills your nostrils.

Type 'help' to see available commands, 'new' to start fresh, or 'load' to continue a saved game.
"""
    prompt = "(tavern) "

    def __init__(self, game_state):
        super().__init__()
        self.game = game_state
        self.last_update_time = game_state.clock.current_time

    def preloop(self) -> None:
        """Initialize before starting the command loop."""
        self.update_game()

    def precmd(self, line: str) -> str:
        """Process command before execution."""
        self.update_game()
        return line

    def update_game(self) -> None:
        """Update game state and show any new events."""
        current_time = self.game.clock.current_time
        # Don't try to compute delta, just update

        # Update game state
        self.game.update()
        self.last_update_time = current_time

        # Show any new events
        self.show_events()

    def show_events(self) -> None:
        """Show any new game events."""
        # In a real implementation, this would show events that happened since last update
        pass

    def do_EOF(self, arg: str) -> bool:
        """Exit on Ctrl+D."""
        print("\nGoodbye!")
        return True

    def do_help(self, arg: str) -> None:
        """Show available commands."""
        print("\nAvailable commands:")
        print("-------------------")
        print("status - Show your current status (gold, inventory, etc.)")
        print("look - Look around the current location")
        print("inventory - Show your inventory")
        print("talk [npc_id] - Talk to an NPC")
        print("gamble [amount] - Try your luck at gambling")
        print("rest - Rest for a while")
        print("quit - Exit the game")
        print("help - Show this help message")

    def do_status(self, arg: str) -> None:
        """Show current game status."""
        status = self.game._handle_status()
        if not status.get("success", False):
            print("Error getting status.")
            return

        data = status.get("data", {})
        print("\n=== Status ===")
        print(f"Time: {data.get('time', 'Unknown')}")
        print(f"Gold: {data.get('gold', 0)}")
        print(f"Room: {'Yes' if data.get('has_room', False) else 'No'}")
        print(f"Tiredness: {data.get('tiredness', 0)}")
        print(f"Energy: {data.get('energy', 0)}")

        if "status_effects" in data and data["status_effects"]:
            print(f"Status Effects: {data['status_effects']}")

        if "active_bounties" in data and data["active_bounties"]:
            print("\nActive Bounties:")
            if isinstance(data["active_bounties"], list):
                for bounty in data["active_bounties"]:
                    print(f"- {bounty}")
            else:
                print(f"- {data['active_bounties']}")

        if "present_npcs" in data:
            print("\nPresent NPCs:")
            for npc in data["present_npcs"]:
                print(f"- {npc['name']}: {npc['description']}")

        print("\nType 'help' for a list of commands.")

    def do_inventory_simple(self, arg: str) -> None:
        """Show your inventory (simplified version)."""
        print("\nYour Inventory:")
        print("--------------")
        if self.game.player.inventory.is_empty():
            print("Your inventory is empty.")
        else:
            for item in self.game.player.inventory.list_items_for_display():
                print(f"{item['name']} (x{item['quantity']}) - {item['description']}")

        print(f"\nGold: {self.game.player.gold} coins")

    def do_time(self, arg: str) -> None:
        """Show current in-game time."""
        try:
            time_str = self.game.clock.get_formatted_time()
            hours_passed = self.game.clock.time.hours
            print(f"Current time: {time_str}")
            print(f"Hours passed: {hours_passed:.1f}")
        except Exception as e:
            print(f"Error getting time: {e}")

    def do_inventory(self, arg: str) -> None:
        """Show your inventory."""
        inv = self.game._handle_inventory()
        if not inv.get("success", False):
            print(inv.get("message", "Can't access inventory."))
            return

        data = inv.get("data", {})
        print(f"\n=== Inventory ({data.get('count', 0)} items) ===")
        print(f"Gold: {data.get('gold', 0)}")

        if data.get("items"):
            print("\nItems:")
            for item in data["items"]:
                print(f"- {item['name']}: {item['description']}")
        else:
            print("\nYour inventory is empty.")

    def do_buy(self, arg: str) -> None:
        """Buy an item. Usage: buy <item_id>"""
        if not arg:
            # Show items for sale
            result = self.game._handle_buy("")
            if result["status"] != "success" or not result.get("items"):
                print("No items available for purchase.")
                return

            print("\n=== Items for Sale ===")
            for item in result["items"]:
                print(f"{item['id']}: {item['name']} - {item['price']} gold")
                print(f"   {item['description']}\n")
        else:
            # Buy the specified item
            result = self.game._handle_buy(arg)
            print(result.get("message", "Purchase completed."))

    def do_use(self, arg: str) -> None:
        """Use an item. Usage: use <item_id>"""
        if not arg:
            # Show usable items
            result = self.game._handle_eat("")
            if result["status"] != "success" or not result.get("items"):
                print("No usable items in inventory.")
                return

            print("\n=== Usable Items ===")
            for item in result["items"]:
                print(f"{item['id']}: {item['name']}")
        else:
            # Use the specified item
            result = self.game._handle_eat(arg)
            print(result.get("message", "Item used."))

    def do_work(self, arg: str) -> None:
        """Work a job. Usage: work [job_id]"""
        if not arg:
            # List available jobs
            result = self.game._handle_available_jobs()
            if result["status"] != "success" or not result.get("data"):
                print("No jobs available right now.")
                return

            print("\n=== Available Jobs ===")
            for job in result["data"]:
                print(f"{job['id']}: {job['name']} - {job['reward']}")
                print(f"   {job['description']}")
                print(f"   Tiredness: {job['tiredness']}\n")
        else:
            # Do the specified job
            result = self.game._handle_work(arg)
            print(result.get("message", "Work completed."))

            if "reward" in result:
                print(f"Earned: {result['reward']} gold")

            if "items" in result and result["items"]:
                print(f"Found: {', '.join(result['items'])}")

    def do_rest(self, arg: str) -> None:
        """Rest for a while. Usage: rest [hours]"""
        result = self.game._handle_rest(arg.split() if arg else [])
        print(result.get("message", "Rest completed."))

    def do_talk(self, arg: str) -> None:
        """Talk to an NPC. Usage: talk <npc_id>"""
        if not arg:
            # List NPCs to talk to
            npcs = self.game.npc_manager.get_interactive_npcs(self.game.player)
            if not npcs:
                print("No one is willing to talk right now.")
                return

            print("\n=== People to Talk To ===")
            for npc in npcs:
                print(f"{npc['id']}: {npc['name']} - {npc['description']}")
        else:
            # Talk to the specified NPC
            npc = self.game.npc_manager.get_npc(arg)
            if not npc or not npc.is_present:
                print(f"{arg} is not here right now.")
                return

            # Use the game's interaction system
            result = self.game.interact_with_npc(arg, "talk", topic=None)

            if result.get("success", False):
                print(result.get("message", f"You talk with {npc.name}."))

                # If there are available topics, show them
                if "topics" in result:
                    print("\nPossible topics:")
                    for topic in result["topics"]:
                        print(f"- {topic}")
            else:
                print(result.get("message", f"Couldn't talk to {npc.name}"))

    def do_gamble(self, arg: str) -> None:
        """Gamble some gold. Usage: gamble <amount> [npc_id]"""
        args = arg.split()
        if not args:
            print("Usage: gamble <amount> [npc_id]")
            return

        try:
            amount = int(args[0])
            npc_id = args[1] if len(args) > 1 else None

            result = self.game._handle_gamble(amount, npc_id)
            if result["status"] != "success":
                print(f"Error: {result.get('message', 'Unknown error')}")
                return

            print(result["message"])
            print(f"New balance: {result['new_balance']} gold")

        except (ValueError, IndexError):
            print("Invalid amount. Usage: gamble <amount> [npc_id]")

    def do_rent(self, arg: str) -> None:
        """Rent a room for the night (costs 10 gold)."""
        if self.game.player.has_room:
            print("You already have a room!")
            return

        if self.game.player.spend_gold(10):
            self.game.player.has_room = True
            print("You've rented a room for the night!")
        else:
            print("You can't afford a room (10 gold needed).")

    def do_help(self, arg: str) -> None:
        """Show help for commands."""
        if arg:
            # Show help for specific command
            cmd = self.get_command(arg)
            if cmd:
                print(f"\n{arg}: {cmd.__doc__ or 'No help available.'}")
            else:
                print(f"\nNo such command: {arg}")
        else:
            # Show general help
            print("\nAvailable commands:")
            print("==================")

            commands = [
                ("status", "Show your current status"),
                ("time", "Show current in-game time"),
                ("inventory", "Show your inventory"),
                ("buy [item]", "Buy an item (list items if none specified)"),
                ("use [item]", "Use an item (list usable items if none specified)"),
                ("work [job]", "Work a job (list jobs if none specified)"),
                ("rest [hours]", "Rest for a number of hours (default: 8)"),
                ("talk [npc]", "Talk to an NPC (list NPCs if none specified)"),
                ("gamble <amount> [npc]", "Gamble some gold"),
                ("rent", "Rent a room for the night (10 gold)"),
                ("help [command]", "Show help for commands"),
                ("quit", "Quit the game"),
            ]

            for cmd, desc in commands:
                print(f"{cmd:20} {desc}")

            print("\nType 'help <command>' for more information on a command.")

    def do_quit(self, arg: str) -> bool:
        """Quit the game."""
        print("\nThanks for playing The Living Rusted Tankard!")
        return True

    def emptyline(self) -> None:
        """Do nothing on empty input."""
        pass

    def default(self, line: str) -> None:
        """Handle unknown commands."""
        print(f"Unknown command: {line}")
        print("Type 'help' for a list of commands.")


def main() -> None:
    """Main entry point for the CLI."""
    print("Initializing game...")
    game = GameState()

    # The NPCs are now initialized in the NPCManager.__init__

    try:
        GameCLI(game).cmdloop()
    except KeyboardInterrupt:
        print("\nGame saved. Goodbye!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        if input("Show traceback? (y/n): ").lower() == "y":
            import traceback

            traceback.print_exc()

    print("Thanks for playing!")
    sys.exit(0)


if __name__ == "__main__":
    main()
