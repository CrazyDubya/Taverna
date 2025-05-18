"""
Example usage of the narrative caching system.

This example demonstrates how to use the @cached_narrative decorator
and the NarrativeCache class to cache narrative generation.
"""
import logging
from pathlib import Path
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the caching decorator
from core.llm.narrative_decorators import cached_narrative, validate_state

# Example 1: Basic usage with @cached_narrative
@cached_narrative("./narrative_cache")
def generate_tavern_description(state):
    """Generate a description of the tavern based on the game state."""
    logger.info("Generating tavern description...")
    time.sleep(1)  # Simulate expensive computation
    
    time_of_day = state.get("time", "day")
    npc_name = state.get("npc", {}).get("name", "barkeep")
    npc_mood = state.get("npc", {}).get("mood", "neutral")
    
    return (
        f"The tavern is quiet in the {time_of_day}. "
        f"The {npc_name} stands behind the bar, looking {npc_mood}."
    )

# Example 2: With state validation
@validate_state(required_keys=["time", "player"])
@cached_narrative("./narrative_cache")
def generate_player_greeting(state):
    """Generate a greeting for the player based on the time of day."""
    time_of_day = state["time"]
    player_name = state["player"].get("name", "adventurer")
    
    if time_of_day == "morning":
        return f"Good morning, {player_name}! The sun is just rising over the mountains."
    elif time_of_day == "afternoon":
        return f"Good afternoon, {player_name}! How goes your day?"
    else:
        return f"Good evening, {player_name}! The night is still young."

def run_example():
    """Run the narrative caching example."""
    # Create a cache directory
    cache_dir = Path("./narrative_cache")
    cache_dir.mkdir(exist_ok=True)
    
    # Define some test states
    morning_state = {
        "time": "morning",
        "player": {"name": "Aria", "location": "tavern"},
        "npc": {"name": "Barkeep", "mood": "sleepy"}
    }
    
    afternoon_state = {
        "time": "afternoon",
        "player": {"name": "Aria", "location": "tavern"},
        "npc": {"name": "Barkeep", "mood": "busy"}
    }
    
    # First run (should generate)
    print("=== First run (should generate) ===")
    desc1 = generate_tavern_description(morning_state)
    print(desc1)
    
    # Second run with same state (should use cache)
    print("\n=== Second run (should use cache) ===")
    desc2 = generate_tavern_description(morning_state)
    print(desc2)
    
    # Different state (should generate again)
    print("\n=== Different state (should generate) ===")
    desc3 = generate_tavern_description(afternoon_state)
    print(desc3)
    
    # Test state validation
    print("\n=== Testing state validation ===")
    try:
        # This will fail validation (missing required keys)
        generate_player_greeting({"time": "morning"})
    except ValueError as e:
        print(f"Validation failed as expected: {e}")
    
    # This will pass validation
    greeting = generate_player_greeting({
        "time": "morning",
        "player": {"name": "Aria"}
    })
    print(f"Generated greeting: {greeting}")

if __name__ == "__main__":
    run_example()
