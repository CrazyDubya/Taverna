# The Living Rusted Tankard - Game Engine Documentation

## Overview
This document describes the current game engine architecture, its capabilities, design principles, and roadmap for future development. It serves as a guide for maintaining consistency across development iterations.

## Current Engine Architecture

### Core Systems

#### 1. Game State Management (`core/game_state.py`)
**Current Capabilities:**
- Central state coordination for all game systems
- Event-driven architecture with observer pattern
- Turn-based processing with idle world progression
- Save/load functionality with database persistence
- Performance optimizations (caching, batching)

**Key Components:**
```python
GameState:
  - clock: GameClock
  - player: PlayerState
  - room_manager: RoomManager
  - npc_manager: NPCManager
  - economy: Economy
  - event_bus: EventBus
  - narrative_engine: LLMGameMaster
```

**Design Principles:**
- Single source of truth for game state
- All state changes go through GameState
- Events propagate to interested systems
- State must be fully serializable

#### 2. Time System (`core/clock.py`)
**Current Capabilities:**
- Fantasy calendar with custom months/seasons
- Configurable time flow (minutes per turn)
- Scheduled event system
- Time-based callbacks
- Natural language time display

**Key Features:**
- 24-hour days, 30-day months, 12-month years
- Event scheduling with recurring events
- Time-aware NPC behaviors
- Atmospheric time descriptions

#### 3. NPC System (`core/npc.py`)
**Current Capabilities:**
- Dynamic NPC presence based on schedules
- Personality-driven behaviors
- Relationship tracking with players
- Conversation memory
- Inventory for merchants
- Interaction conditions and actions

**Architecture:**
```python
NPC:
  - schedule: List[TimeRange]
  - relationships: Dict[player_id, float]
  - disposition: NPCDisposition
  - interactions: List[NPCInteraction]
  - conversation_topics: List[str]
```

#### 4. LLM Integration (`core/llm_game_master.py`)
**Current Capabilities:**
- Natural language command processing
- Dynamic narrative generation
- Context-aware responses
- Fallback mechanisms for offline mode
- Narrative action system with tags

**Integration Points:**
- Command parsing and interpretation
- NPC dialogue generation
- Scene description
- Quest/event generation

#### 5. Event System (`core/event_bus.py`)
**Current Capabilities:**
- Publish/subscribe event model
- Type-safe event definitions
- Async event handling
- Event filtering and routing

**Event Types:**
- Time events (TIME_ADVANCED)
- NPC events (SPAWN, DEPART, INTERACTION)
- Player events (STAT_CHANGE, ITEM_CHANGE)
- Room events (ROOM_CHANGE, OCCUPANT_CHANGE)

### What the Engine Does

1. **Simulates a Living World**
   - NPCs follow schedules and routines
   - Time passes with meaningful changes
   - Economy fluctuates based on events
   - Stories emerge from character interactions

2. **Processes Natural Language**
   - Understands player intent from text
   - Generates contextual responses
   - Creates dynamic narratives
   - Maintains conversation coherence

3. **Manages Complex State**
   - Tracks all entities and relationships
   - Persists state across sessions
   - Handles concurrent state changes
   - Optimizes performance with caching

4. **Provides Player Agency**
   - Multiple ways to solve problems
   - Consequences for actions
   - Relationship building
   - Economic participation

### What the Engine Should Do (Planned)

1. **Deep Narrative Management**
   - Track multiple story arcs simultaneously
   - Ensure narrative coherence with rules
   - Generate emergent storylines
   - Provide satisfying closure

2. **Expanded Location System**
   - Multiple tavern areas (cellar, floors, attic)
   - Area-specific atmospheres and events
   - Hidden locations and secrets
   - Dynamic area properties

3. **Advanced NPC Narratives**
   - Secret motivations and hidden depths
   - Complex relationship webs
   - Story role assignment (protagonist/antagonist)
   - Behavioral rules based on conditions

4. **GM Control Framework**
   - Story seed injection
   - Tension management
   - Arc orchestration
   - Narrative health monitoring

5. **Enhanced Player Integration**
   - Deeper consequence tracking
   - Reputation with multiple factions
   - Personal story arcs
   - Character development

## Design Principles

### 1. Coherent Simulation
- Every system follows consistent rules
- No "fake" events - everything emerges from simulation
- Time always matters
- NPCs have lives outside player interaction

### 2. Narrative First
- Mechanics serve story, not vice versa
- Every action should have narrative weight
- Character relationships drive gameplay
- Emotional stakes matter more than numbers

### 3. Player Agency
- Multiple valid approaches to problems
- No single "correct" path
- Consequences shape future opportunities
- Player choices genuinely matter

### 4. Living World
- Things happen without player involvement
- NPCs pursue their own goals
- Stories progress naturally
- World state evolves continuously

### 5. Performance Awareness
- Turn-based for predictability
- Efficient idle processing
- Cached computations where sensible
- Async operations for LLM calls

## Technical Architecture

### State Management
```python
# All state changes flow through GameState
game_state.process_command(command) -> Result

# Events propagate to systems
event_bus.publish(Event) -> subscribers.handle()

# Time drives change
clock.advance() -> triggers scheduled events

# Persistence maintains continuity
game_state.save() -> database/file
```

### System Communication
```
Player Input -> Command Parser -> Game State
                                      |
                                      v
                               Event Bus
                                /    |    \
                               v     v     v
                           NPCs  Economy  Narrative
```

### LLM Integration Pattern
```python
# Always have fallbacks
try:
    response = llm.generate(context)
except LLMUnavailable:
    response = rule_based_fallback(context)

# Maintain context
narrative_context = build_context(game_state, history)
response = llm.generate_with_context(narrative_context)

# Parse structured output
action = parse_narrative_action(response)
apply_to_game_state(action)
```

## Development Guidelines

### Adding New Systems
1. Define clear interfaces with existing systems
2. Use event bus for loose coupling
3. Ensure state is serializable
4. Provide both LLM and rule-based implementations
5. Add appropriate caching for performance

### Modifying Core Systems
1. Maintain backward compatibility when possible
2. Update serialization methods
3. Ensure event contracts are preserved
4. Test with both online/offline modes
5. Document state changes clearly

### Narrative Development
1. Stories should emerge from character goals
2. Use rules to ensure coherence
3. Provide multiple resolution paths
4. Track long-term consequences
5. Balance player agency with narrative structure

## Future Architecture Goals

### Phase 1: Tavern Expansion
- Implement multi-area tavern system
- Add vertical movement (floors)
- Create area-specific events
- Hide secrets and discoveries

### Phase 2: Deep NPCs
- Implement secret/motivation system
- Add behavioral rule engine
- Create relationship web visualization
- Enable dynamic alliance/rivalry

### Phase 3: Narrative Engine
- Build story thread tracking
- Implement tension management
- Create arc progression system
- Add closure detection

### Phase 4: GM Framework
- Create story seed system
- Build narrative health metrics
- Implement intervention tools
- Add story orchestration

### Phase 5: Advanced Integration
- Connect all systems through narrative
- Ensure emergent story generation
- Polish player agency mechanics
- Optimize for long-term play

## Performance Considerations

### Current Optimizations
- NPC presence caching (0.5s TTL)
- Snapshot caching (1.0s TTL)
- Event batching (5 events)
- Lazy loading of resources

### Planned Optimizations
- Narrative state indexing
- Relationship graph caching
- Story thread prioritization
- Background narrative processing

## Testing Strategy

### Unit Tests
- Each system in isolation
- State serialization/deserialization
- Event handling
- Rule evaluation

### Integration Tests
- System communication
- State consistency
- Event propagation
- Save/load cycles

### Narrative Tests
- Story coherence
- Arc progression
- Closure quality
- Player agency impact

## Conclusion

The Living Rusted Tankard engine is designed to create a deeply simulated, narrative-rich experience within a single location. By following these principles and architecture patterns, future development can maintain consistency while expanding the depth and complexity of the simulation.

The key is to remember: **Every mechanic serves the story, and every story emerges from the living world.**