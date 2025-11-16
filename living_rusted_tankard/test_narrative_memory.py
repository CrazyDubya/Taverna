#!/usr/bin/env python3
"""Test script for the new narrative memory and state systems."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.narrative.character_memory import (
    CharacterMemoryManager,
    Memory,
    RelationshipLevel,
)
from core.narrative.character_state import (
    CharacterStateManager,
    Mood,
    Concern,
    ConcernType,
    Goal,
)
from datetime import datetime, timedelta
import time


def test_character_memory():
    """Test character memory functionality."""
    print("=== Testing Character Memory System ===\n")

    # Create memory manager
    memory_manager = CharacterMemoryManager()

    # Create memory for Grim the bartender
    grim_memory = memory_manager.get_or_create_memory("grim_bartender", "Grim")

    print(f"Initial relationship: {grim_memory.get_relationship_level()}")
    print(f"Initial greeting: {grim_memory.get_contextual_greeting()}\n")

    # Add some interactions
    grim_memory.add_interaction_memory(
        "Player ordered an ale", {"item": "ale", "price": 5}
    )

    grim_memory.add_interaction_memory(
        "Had a conversation about the weather", {"topic": "weather", "mood": "friendly"}
    )

    # Improve relationship
    grim_memory.improve_relationship(0.3)

    print(f"After interactions - Relationship: {grim_memory.get_relationship_level()}")
    print(f"New greeting: {grim_memory.get_contextual_greeting()}\n")

    # Add personal facts
    grim_memory.add_personal_fact("profession", "former soldier")
    grim_memory.add_personal_fact("preference", "likes strong ale")

    # Get relevant memories
    relevant = grim_memory.get_relevant_memories("ale", limit=2)
    print("Relevant memories for 'ale':")
    for mem in relevant:
        print(f"  - {mem.to_narrative()}")

    print("\nPersonal facts learned:")
    for category, facts in grim_memory.personal_facts.items():
        for fact in facts:
            print(f"  - {category}: {fact}")

    print("\n" + "=" * 50 + "\n")


def test_character_state():
    """Test character state functionality."""
    print("=== Testing Character State System ===\n")

    # Create state manager
    state_manager = CharacterStateManager()

    # Create state for Mira the merchant
    mira_state = state_manager.get_or_create_state(
        "mira_merchant",
        "Mira",
        personality={
            "optimism": 0.7,
            "anxiety": 0.4,
            "temper": 0.2,
            "contentment": 0.6,
        },
    )

    print("Initial state:")
    print(f"  Mood: {mira_state.mood.value}")
    print(f"  Energy: {mira_state.energy}")
    print(f"  Stress: {mira_state.stress}")
    print(f"  Status: {mira_state.get_status_description()}\n")

    # Add a concern about theft
    mira_state.add_concern(
        Concern(
            type=ConcernType.DANGER,
            description="theft reported at the market",
            intensity=0.8,
            source="town_news",
        )
    )

    # Update mood based on concern
    mira_state.update_mood()

    print("After hearing about theft:")
    print(f"  Mood: {mira_state.mood.value}")
    print(
        f"  Primary concern: {mira_state.concerns[0].description if mira_state.concerns else 'None'}"
    )
    print(f"  Status: {mira_state.get_status_description()}\n")

    # Add a goal
    mira_state.add_goal(
        Goal(
            description="Hire a guard for the shop",
            priority=0.9,
            progress=0.0,
            required_actions=[
                "find trustworthy guard",
                "negotiate payment",
                "set schedule",
            ],
        )
    )

    print(f"Added goal: {mira_state.goals[0].description}")
    print(f"  Priority: {mira_state.goals[0].priority}")
    print(f"  Required actions: {', '.join(mira_state.goals[0].required_actions)}\n")

    # Make her busy
    mira_state.set_busy("counting inventory", duration_minutes=2)
    available, reason = mira_state.check_availability()
    print(f"Availability: {'Yes' if available else 'No'}")
    if not available:
        print(f"  Reason: {reason}\n")

    # Simulate time passing
    print("Simulating time passing (3 ticks)...")
    for i in range(3):
        mira_state.tick()
        print(
            f"  Tick {i+1}: stress={mira_state.stress:.2f}, energy={mira_state.energy:.2f}"
        )

    print(f"\nFinal status: {mira_state.get_status_description()}")

    # Get dialogue modifiers
    modifiers = mira_state.get_dialogue_modifiers()
    print("\nDialogue modifiers:")
    for key, value in modifiers.items():
        if value is not None:
            print(f"  {key}: {value}")

    print("\n" + "=" * 50 + "\n")


def test_world_event():
    """Test how world events affect multiple NPCs."""
    print("=== Testing World Event System ===\n")

    state_manager = CharacterStateManager()

    # Create states for multiple NPCs
    npcs = [
        ("grim_bartender", "Grim", {"optimism": 0.4, "anxiety": 0.3}),
        ("mira_merchant", "Mira", {"optimism": 0.7, "anxiety": 0.5}),
        ("jonas_blacksmith", "Jonas", {"optimism": 0.6, "anxiety": 0.2}),
    ]

    for npc_id, name, personality in npcs:
        state = state_manager.get_or_create_state(npc_id, name, personality)
        print(f"{name} - Initial mood: {state.mood.value}")

    # Apply a theft event
    print("\n[Event: Theft reported at the market]\n")
    state_manager.apply_world_event("theft_reported", {"location": "market"})

    # Check how each NPC reacted
    for npc_id, name, _ in npcs:
        state = state_manager.character_states[npc_id]
        print(f"{name}:")
        print(f"  New mood: {state.mood.value}")
        print(f"  Stress level: {state.stress:.2f}")
        if state.concerns:
            print(f"  Primary concern: {state.concerns[0].description}")
        print()


def test_integration():
    """Test integration of memory and state."""
    print("=== Testing Memory + State Integration ===\n")

    memory_manager = CharacterMemoryManager()
    state_manager = CharacterStateManager()

    # Create integrated character
    npc_id = "elara_healer"
    npc_name = "Elara"

    memory = memory_manager.get_or_create_memory(npc_id, npc_name)
    state = state_manager.get_or_create_state(
        npc_id,
        npc_name,
        personality={"optimism": 0.8, "anxiety": 0.3, "contentment": 0.7},
    )

    print(f"Character: {npc_name} the Healer")
    print(f"Initial state: {state.get_status_description()}")
    print(f"Greeting: {memory.get_contextual_greeting()}\n")

    # Simulate multiple interactions
    interactions = [
        ("Player asked about healing potions", {"topic": "potions"}),
        ("Player bought a healing potion", {"item": "healing potion", "price": 50}),
        (
            "Player shared news about bandits",
            {"topic": "danger", "location": "forest road"},
        ),
    ]

    for description, details in interactions:
        print(f"[Interaction: {description}]")
        memory.add_interaction_memory(description, details)

        # React based on interaction
        if "danger" in details.get("topic", ""):
            state.add_concern(
                Concern(
                    type=ConcernType.DANGER,
                    description=f"bandits on the {details.get('location', 'roads')}",
                    intensity=0.6,
                    source="player_report",
                )
            )
            state.stress += 0.2
        elif "bought" in description:
            memory.improve_relationship(0.15)
            state.mood_modifiers["good_sale"] = (
                0.3,
                datetime.now() + timedelta(hours=1),
            )

        state.update_mood()
        print(
            f"  Mood: {state.mood.value}, Relationship: {memory.get_relationship_level()}"
        )

    print(f"\nFinal state: {state.get_status_description()}")
    print(f"Final greeting: {memory.get_contextual_greeting()}")

    # Show how memory affects future interactions
    print("\n[Next day - Player returns]")
    relevant_memories = memory.get_relevant_memories("potion", limit=1)
    if relevant_memories:
        print(f'Elara remembers: "{relevant_memories[0].player_action}"')
        print('Elara: "Back for more healing potions? I\'ve got a fresh batch!"')


if __name__ == "__main__":
    test_character_memory()
    test_character_state()
    test_world_event()
    test_integration()

    print("\n=== All tests completed successfully! ===")
