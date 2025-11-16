"""
Demonstration of the Event Formatter system.

This script shows how to use the EventFormatter to track and display game events.
"""
import os
import sys
import random
from enum import Enum

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.event_formatter import EventFormatter
from core.npc import NPC, NPCType, NPCDisposition


def demo():
    """Run a demo of the event formatter system."""
    print("=== Event Formatter Demo ===\n")

    # Initialize the formatter
    formatter = EventFormatter()

    # Create some sample NPCs
    npcs = [
        NPC(
            id="npc_1",
            name="Gandal",
            description="A wise old wizard",
            npc_type=NPCType.BARD,
            disposition=NPCDisposition.FRIENDLY,
        ),
        NPC(
            id="npc_2",
            name="Aragorn",
            description="The ranger from the North",
            npc_type=NPCType.ADVENTURER,
            disposition=NPCDisposition.NEUTRAL,
        ),
        NPC(
            id="npc_3",
            name="Gimli",
            description="A dwarf warrior",
            npc_type=NPCType.GUARD,
            disposition=NPCDisposition.NEUTRAL,
        ),
    ]

    # Simulate some game events
    print("=== Simulating Game Events ===\n")

    # NPCs arrive
    for npc in npcs:
        formatter.add_event(
            "npc_spawn", npc_name=npc.name, npc_id=npc.id, location="tavern"
        )

    # Player rents a room
    formatter.add_event("rent_success", amount=5, room_id=101)

    # Player sleeps
    formatter.add_event("sleep_success", hours=8, room_id=101)

    # Some gambling happens
    for _ in range(3):
        if random.random() > 0.5:
            formatter.add_event(
                "gamble_win",
                amount=random.randint(1, 10),
                game=random.choice(["dice", "blackjack", "poker"]),
            )
        else:
            formatter.add_event(
                "gamble_lose",
                amount=random.randint(1, 5),
                game=random.choice(["dice", "blackjack", "poker"]),
            )

    # NPCs leave
    for npc in npcs:
        if random.random() > 0.3:  # 70% chance to leave
            formatter.add_event(
                "npc_depart",
                npc_name=npc.name,
                npc_id=npc.id,
                reason=random.choice(["tired", "work", "adventure"]),
            )

    # Get and display the formatted events
    print("=== Formatted Events ===\n")
    events = formatter.get_formatted_events()
    for i, event in enumerate(events, 1):
        print(f"{i}. {event}")

    print("\n=== End of Demo ===")


if __name__ == "__main__":
    demo()
