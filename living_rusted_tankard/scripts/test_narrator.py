"""Test script for the narrator module."""
import asyncio
import json
import logging
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.llm import narrator

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Sample game contexts
SAMPLE_CONTEXTS = [
    {
        "time": "evening",
        "location": "main_room",
        "characters": ["bartender", "merchant", "drunken_patron"],
        "objects": ["hearth", "bar", "tables", "notice_board"],
        "player": {"state": "alert", "inventory": ["key", "coin_purse"]},
        "previous_action": "look",
        "focus": "room",
    },
    {
        "time": "night",
        "location": "bar",
        "characters": ["bartender"],
        "objects": ["polished_wooden_bar", "shelves_of_bottles"],
        "player": {"state": "curious", "inventory": ["mysterious_note"]},
        "previous_action": "examine",
        "focus": "shelves",
    },
    {
        "time": "morning",
        "location": "window_seat",
        "characters": [],
        "objects": ["window", "bench", "drapes"],
        "player": {"state": "tired", "inventory": ["empty_mug"]},
        "previous_action": "look",
        "focus": "window",
    },
]


async def test_narrator():
    """Test the narrator with sample contexts."""
    print("Narrator Test Console")
    print("Type 'quit' or 'exit' to quit\n")

    # Initialize the narrator
    n = narrator

    try:
        while True:
            # Display menu
            print("\nChoose a context to test:")
            for i, ctx in enumerate(SAMPLE_CONTEXTS, 1):
                print(
                    f"{i}. {ctx['location']} at {ctx['time']} (focus: {ctx['focus']})"
                )
            print("q. Quit")

            # Get user input
            choice = input("\n> ").strip().lower()

            if choice in ("q", "quit", "exit"):
                print("Goodbye!")
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(SAMPLE_CONTEXTS):
                    context = SAMPLE_CONTEXTS[idx]
                    print("\n=== Context ===")
                    print(json.dumps(context, indent=2))

                    print("\n=== Narration ===")
                    narration = await n.narrate(context)
                    print("\n" + narration + "\n")
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number or 'q' to quit.")

    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")


if __name__ == "__main__":
    asyncio.run(test_narrator())
