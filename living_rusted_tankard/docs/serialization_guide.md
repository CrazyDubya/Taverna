# Serialization and Snapshot Guide

This document provides an overview of the serialization and snapshot features implemented for The Living Rusted Tankard game.

## Table of Contents
- [Serialization System](#serialization-system)
- [Snapshot System](#snapshot-system)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Best Practices](#best-practices)

## Serialization System

The serialization system provides a way to save and load game states to/from persistent storage.

### Key Components

1. **Serializable Base Class**
   - Base class that provides `to_dict()` and `from_dict()` methods
   - Inherit from this class for any game object that needs to be serialized

2. **save_game_state(state, save_dir, filename=None)**
   - Saves the game state to a JSON file
   - Automatically handles serialization of nested Serializable objects
   - Returns the path to the saved file

3. **load_game_state(filepath)**
   - Loads a game state from a JSON file
   - Returns the deserialized state dictionary

4. **get_latest_save(save_dir)**
   - Finds the most recent save file in the specified directory
   - Returns the path to the most recent save, or None if none exist

### Example

```python
from utils.serialization import Serializable, save_game_state, load_game_state

class Player(Serializable):
    def __init__(self, name, gold=0):
        self.name = name
        self.gold = gold

# Create and save a game state
player = Player("Test Player", 100)
game_state = {
    "player": player,
    "time": 10.5,
    "location": "Tavern"
}

save_path = save_game_state(game_state, "saves")

# Later, load the game state
loaded_state = load_game_state(save_path)
player = Player.from_dict(loaded_state["player"])
```

## Snapshot System

The snapshot system provides debugging tools to capture and display the game state at any point.

### Key Components

1. **GameSnapshot Class**
   - Captures and formats the current game state
   - Can save snapshots to disk for later analysis
   - Provides a human-readable console output

2. **Global Instance**
   - `snapshot_taker`: Global instance of GameSnapshot for easy access

### Example

```python
from utils.snapshot import snapshot_taker

# Capture and display a snapshot
state = {
    "time": 10.5,
    "player": {"gold": 100, "has_room": True, "tiredness": 3},
    "location": "Tavern",
    "npcs": [{"name": "Barkeep", "present": True}]
}

snapshot = snapshot_taker.capture(state, "test command")
print(snapshot)
```

## Testing

Run the test suite to verify the serialization and snapshot functionality:

```bash
python -m unittest tests/test_serialization.py -v
```

## Best Practices

1. **Serialization**
   - Always inherit from `Serializable` for game objects that need to be saved
   - Keep serialized data minimal - only save what's necessary
   - Handle versioning if the data structure changes between game versions

2. **Snapshots**
   - Use snapshots liberally during development for debugging
   - Include relevant context (like the command that triggered the snapshot)
   - Be mindful of sensitive data in snapshots

3. **Error Handling**
   - Always wrap save/load operations in try/except blocks
   - Provide meaningful error messages
   - Handle missing or corrupted save files gracefully
