"""
Interactive demo for room and sleep functionality in The Living Rusted Tankard.
"""
from core.clock import GameClock
from core.room import RoomManager
from core.player import PlayerState


def print_status(player, clock, room_manager):
    """Print the current game status."""
    print("\n--- The Rusted Tankard ---")
    print(f"Time: {clock.time}")
    print(f"Gold: {player.gold}")
    print(f"Tiredness: {player.tiredness:.1f}")

    if player.has_room:
        print(f"You have a room: {player.room_number}")
    else:
        print("You don't have a room.")

    if player.no_sleep_quest_unlocked:
        print("The no-sleep quest is UNLOCKED!")

    print("-----------------------")


def main():
    """Run the interactive demo."""
    # Initialize game state
    clock = GameClock()
    player = PlayerState(gold=10)  # Start with 10 gold
    room_manager = RoomManager(num_rooms=3)

    print("Welcome to The Rusted Tankard!")
    print("Type 'help' for a list of commands.\n")

    # Game loop
    while True:
        print_status(player, clock, room_manager)

        # Get player input
        try:
            command = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        # Process commands
        if command in ("q", "quit", "exit"):
            print("Goodbye!")
            break

        elif command in ("h", "help"):
            print("\nAvailable commands:")
            print("  look, l       - Look around")
            print("  wait [hours]  - Wait for some time (default: 1 hour)")
            print("  rooms         - List available rooms")
            print("  rent          - Rent a room")
            print("  sleep         - Sleep in your room")
            print("  work          - Work to earn gold (increases tiredness)")
            print("  help, h       - Show this help")
            print("  quit, q       - Quit the game")

        elif command in ("look", "l"):
            print("\nYou're in the common room of The Rusted Tankard.")
            print("The door is locked tight. You're not going anywhere.")

            # Advance time by 0.5 hours for looking around
            clock.advance_time(0.5)
            player.tiredness = min(100, player.tiredness + 0.2)

        elif command.startswith("wait"):
            try:
                _, hours = command.split()
                hours = float(hours)
            except ValueError:
                hours = 1.0

            if hours <= 0:
                print("You can't travel back in time!")
                continue

            print(f"\nYou wait for {hours} hours.")
            clock.advance_time(hours)
            player.tiredness = min(100, player.tiredness + hours * 0.2)

        elif command == "rooms":
            available_rooms = room_manager.get_available_rooms()
            if available_rooms:
                print("\nAvailable rooms:")
                for room in available_rooms:
                    print(
                        f"- Room {room['number']} ({room['price_per_night']} gold per night)"
                    )
            else:
                print("\nNo rooms available at the moment.")

        elif command == "rent":
            if player.has_room:
                print("\nYou already have a room!")
                continue

            success, room_number = room_manager.rent_room(player)
            if success:
                print(f"\nYou've rented room {room_number} for 5 gold per night.")
                print("You can now sleep to recover your energy.")
            else:
                print("\nYou can't afford a room or no rooms are available.")

        elif command == "sleep":
            if not player.has_room:
                print("\nYou need to rent a room first!")
                continue

            success = room_manager.sleep(player, clock)
            if success:
                print("\nYou sleep soundly in your room, recovering your energy.")

                # Check for the no-sleep quest
                if (
                    clock.time.hours >= 48
                    and not player.has_room
                    and not player.no_sleep_quest_unlocked
                ):
                    print("\nYou've been awake for 48 hours without sleeping...")
                    print(
                        "Something strange is happening. The air feels charged with energy."
                    )
                    player.no_sleep_quest_unlocked = True
                    player.rest_immune = True
            else:
                print("\nYou can't sleep right now.")

        elif command == "work":
            earnings = 2 + int(clock.time.hours) % 5  # 2-6 gold
            print(f"\nYou work for an hour and earn {earnings} gold.")
            player.gold += earnings
            player.tiredness = min(100, player.tiredness + 5)
            clock.advance_time(1)

        else:
            print(
                "\nI don't understand that command. Type 'help' for a list of commands."
            )

        # Check for the no-sleep quest trigger
        if (
            clock.time.hours >= 48
            and not player.has_room
            and not player.no_sleep_quest_unlocked
        ):
            print("\nYou feel exhausted. You've been awake for 48 hours...")
            player.no_sleep_quest_unlocked = True
            player.rest_immune = True
            print("The world seems to shimmer around you. Something is not right...")


if __name__ == "__main__":
    main()
