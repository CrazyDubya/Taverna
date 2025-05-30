# Narrative Engine Integration Plan

## Overview
This document outlines how to connect the Phase 4 Narrative Engine with the existing game systems to ensure it actually affects gameplay.

## Current State Analysis

### What We Have:
1. **Narrative Engine (Phase 4)**
   - Story threads with beats and progression
   - Thread management with convergence detection
   - Rules engine with health monitoring
   - Orchestration for climaxes and arcs

2. **Existing Systems**
   - EventBus for game events
   - GameState managing all mechanics
   - NPCs with relationships and schedules
   - LLMGameMaster for AI responses
   - NarrativeActionProcessor for game effects

### The Problem:
The narrative engine exists in isolation. It needs to be connected to actual gameplay events.

## Integration Architecture

```
Player Action → GameState.process_command()
                    ↓
                EventBus.emit(event)
                    ↓
         NarrativeEngine.on_event()
                    ↓
         ThreadManager.update_threads()
                    ↓
         Generate Narrative Beats
                    ↓
         Apply Effects via NarrativeActionProcessor
                    ↓
         Update GameState & Generate Response
```

## Integration Points

### 1. Event Integration (Priority: HIGH)
**File**: `core/narrative/event_integration.py`

```python
class NarrativeEventHandler:
    """Connects narrative engine to game events"""
    
    def __init__(self, game_state, narrative_orchestrator):
        self.game_state = game_state
        self.orchestrator = narrative_orchestrator
        self.thread_manager = narrative_orchestrator.thread_manager
        
        # Subscribe to game events
        event_bus = game_state.event_bus
        event_bus.subscribe(EventType.NPC_INTERACTION, self.on_npc_interaction)
        event_bus.subscribe(EventType.ROOM_CHANGE, self.on_room_change)
        event_bus.subscribe(EventType.TIME_ADVANCED, self.on_time_advanced)
        event_bus.subscribe(EventType.QUEST_UPDATE, self.on_quest_update)
```

### 2. GameState Enhancement (Priority: HIGH)
**Modify**: `core/game_state.py`

Add narrative engine to GameState:
```python
def __init__(self, ...):
    # ... existing init ...
    
    # Initialize narrative engine
    from core.narrative import ThreadManager, NarrativeRulesEngine, NarrativeOrchestrator
    self.thread_manager = ThreadManager()
    self.rules_engine = NarrativeRulesEngine()
    self.narrative_orchestrator = NarrativeOrchestrator(
        self.thread_manager, 
        self.rules_engine
    )
    
    # Connect to events
    from core.narrative.event_integration import NarrativeEventHandler
    self.narrative_handler = NarrativeEventHandler(self, self.narrative_orchestrator)
```

### 3. NPC Dialogue Integration (Priority: HIGH)
**Modify**: `core/npc.py`

Enhance NPC interactions with narrative context:
```python
def interact_with_npc(self, npc_name: str) -> str:
    # ... existing interaction logic ...
    
    # Get narrative context for this NPC
    active_threads = self.narrative_orchestrator.get_threads_for_participant(npc_name)
    narrative_context = self.narrative_orchestrator.get_interaction_context(
        npc_name, 
        active_threads
    )
    
    # Pass to LLM with narrative context
    response = self.llm_game_master.process_interaction(
        player_input="",
        npc=npc,
        narrative_context=narrative_context
    )
```

### 4. Command Processing Enhancement (Priority: MEDIUM)
**Modify**: `core/game_state.py`

Add narrative beats to command results:
```python
def process_command(self, command: str) -> str:
    # ... existing command processing ...
    
    # Check if command triggers narrative beats
    triggered_beats = self.narrative_orchestrator.check_command_triggers(
        command, 
        self.current_room,
        self.get_available_participants()
    )
    
    # Execute beats and get narrative
    for beat in triggered_beats:
        beat_result = self.narrative_orchestrator.execute_beat(beat, self.get_world_state())
        result += "\n\n" + beat_result.narrative
        
        # Apply beat effects
        self._apply_narrative_effects(beat_result.effects)
```

### 5. Thread Creation from Game Events (Priority: HIGH)
**File**: `core/narrative/thread_factory.py`

```python
class ThreadFactory:
    """Creates narrative threads from game events"""
    
    @staticmethod
    def create_from_quest(quest: Quest) -> StoryThread:
        """Convert a quest into a narrative thread"""
        return StoryThread(
            id=f"quest_{quest.id}",
            title=quest.name,
            type=ThreadType.MAIN_QUEST if quest.is_main else ThreadType.SIDE_QUEST,
            description=quest.description,
            primary_participants=['player'] + quest.npcs,
            beats=ThreadFactory._create_quest_beats(quest)
        )
    
    @staticmethod
    def create_from_npc_event(npc: NPC, event_type: str) -> Optional[StoryThread]:
        """Create threads from significant NPC events"""
        # Implementation for NPC-driven narratives
```

### 6. Testing Framework (Priority: HIGH)
**File**: `tests/test_narrative_integration.py`

```python
def test_narrative_affects_gameplay():
    """Test that narrative events actually change game state"""
    game_state = GameState()
    
    # Create a narrative thread
    thread = StoryThread(
        id="test_thread",
        title="Test Mystery",
        type=ThreadType.MYSTERY,
        primary_participants=["player", "merchant_john"]
    )
    
    # Add thread and trigger a beat
    game_state.narrative_orchestrator.thread_manager.add_thread(thread)
    
    # Interact with NPC involved in thread
    result = game_state.interact_with_npc("merchant_john")
    
    # Verify narrative influenced the interaction
    assert "mystery" in result.lower()
    assert game_state.narrative_orchestrator.thread_manager.get_thread("test_thread").stage != ThreadStage.SETUP
```

## Implementation Steps

### Phase 1: Core Connections (Week 1)
1. Create `NarrativeEventHandler` to connect to EventBus
2. Add narrative engine to GameState initialization
3. Create `ThreadFactory` for converting game events to threads
4. Write integration tests

### Phase 2: NPC Integration (Week 2)
1. Enhance NPC interactions with narrative context
2. Generate dynamic dialogue based on active threads
3. Create NPC-driven narrative events
4. Test multi-participant threads

### Phase 3: Player Actions (Week 3)
1. Connect command processing to narrative beats
2. Implement narrative effects on game state
3. Add narrative descriptions to mechanical results
4. Create player choice points in threads

### Phase 4: Full Integration Testing (Week 4)
1. Test complete narrative cycles
2. Verify climax coordination works
3. Test narrative health interventions
4. Performance optimization

## Success Criteria

1. **Functional Integration**
   - [ ] NPCs reference active story threads in dialogue
   - [ ] Player actions advance narrative threads
   - [ ] Narrative beats trigger game state changes
   - [ ] Climactic moments create memorable gameplay

2. **No Hacks**
   - [ ] All tests use actual game flow, no mocks
   - [ ] Integration tests play through real scenarios
   - [ ] No auto-passing tests or simplified logic
   - [ ] Performance remains acceptable

3. **Player Experience**
   - [ ] Narrative enhances gameplay, not replaces it
   - [ ] Story threads feel organic and responsive
   - [ ] Multiple threads create interesting convergences
   - [ ] Player choices matter to narrative outcomes

## Anti-Patterns to Avoid

1. **Isolated Systems**: Don't let narrative exist separately from gameplay
2. **Forced Narrative**: Don't override player agency for story
3. **Mock Testing**: Don't test with mocks that hide integration issues
4. **Performance Hacks**: Don't disable features for speed
5. **Complexity Creep**: Keep integration points clean and maintainable

## Verification Method

Run this command to verify integration:
```bash
python verify_narrative_integration.py
```

This will:
1. Start a game instance
2. Create narrative threads
3. Perform player actions
4. Verify narrative affects gameplay
5. Check performance metrics