# Dev A & B Integration Guide

## 1. Time System Integration

### Decision: Event-Based Time Updates
- NPC and economic updates will be triggered by time-based events
- The `GameClock` will fire `on_hour_advanced` events
- NPCs will subscribe to these events for their updates

### Implementation:
```python
# In GameClock class
def advance_time(self, hours: float) -> None:
    old_time = self.time.hours
    self.time.hours += hours
    
    # Process any events that should trigger in this time period
    self.event_queue.process_events(self.time.hours)
    
    # Fire time update events
    if hasattr(self, 'on_time_advanced'):
        self.on_time_advanced(old_time, self.time.hours, hours)
    
    # Fire hourly updates
    old_hour = int(old_time) % 24
    new_hour = int(self.time.hours) % 24
    if old_hour != new_hour:
        if hasattr(self, 'on_hour_advanced'):
            self.on_hour_advanced(new_hour)
```

## 2. Player State Integration

### Decision: Unified Player State
- Merge both player state implementations
- Core attributes (gold, inventory, tiredness) will be in the base `PlayerState`
- NPC-related state will be in an `NPCState` component

### PlayerState Structure:
```python
@dataclass
class PlayerState:
    gold: int = 40
    inventory: Inventory = field(default_factory=Inventory)
    tiredness: float = 0.0
    room_rented: bool = False
    no_sleep_quest_active: bool = False
    npc_state: NPCState = field(default_factory=NPCState)
```

## 3. Event System

### Event Types:
1. `TimeAdvancedEvent`
   - Triggered every hour
   - Contains: `current_hour` (0-23)

2. `NPCStateUpdateEvent`
   - Triggered when NPCs enter/leave
   - Contains: `npc_id`, `is_present`, `location`

3. `EconomyTransactionEvent`
   - Triggered on financial transactions
   - Contains: `amount`, `transaction_type`, `participants`

## 4. NPC System Integration

### Decision: Time-Based NPC Updates
- NPCs will update their state based on hourly events
- NPCManager will handle scheduling and state updates

### Example Usage:
```python
def setup_npc_system(clock: GameClock, npc_manager: NPCManager):
    def on_hour_advanced(hour: int):
        npc_manager.update_npcs_for_hour(hour)
    
    clock.on_hour_advanced = on_hour_advanced
```

## 5. Save/Load System

### Decision: JSON-Based Serialization
- Use Pydantic for serialization/deserialization
- Version game state for compatibility
- Save file structure:
  ```json
  {
    "version": "1.0",
    "player": { ... },
    "npcs": [ ... ],
    "economy": { ... },
    "timestamp": "2025-05-17T23:24:19-04:00"
  }
  ```

## 6. Error Handling

### Decision: Centralized Error Handling
- Use custom exceptions for game-specific errors
- Log all errors with context
- Provide user-friendly error messages

## 7. Next Steps

1. Implement the agreed-upon changes in both codebases
2. Update tests to cover the integrated systems
3. Test the interaction between time, NPCs, and economy
4. Document any additional edge cases found

## 8. Contact

For any questions or adjustments needed, please contact:
- Dev A: [Your Contact Info]
- Dev B: [Their Contact Info]

Last Updated: 2025-05-17 23:24 EDT
