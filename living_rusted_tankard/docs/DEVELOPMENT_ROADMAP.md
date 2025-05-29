# The Living Rusted Tankard - Development Roadmap

## Overview
This document provides a logical, step-by-step development plan for transforming the current single-room tavern into a deep, multi-area narrative engine. Each phase builds upon the previous while maintaining system stability.

## Current State Assessment

**✅ Completed:**
- Basic game state management
- Simple NPC system with schedules
- Time/clock system with fantasy calendar
- LLM integration for natural language
- Event bus architecture
- Room management (single tavern room)
- Basic economy and inventory
- Save/load persistence

**🔄 In Progress:**
- AI player system (session isolation completed)
- Thread safety improvements
- Resource management cleanup

**❌ Missing:**
- Multi-area tavern architecture
- Deep narrative system
- Story thread management
- NPC inner lives and secrets
- GM control framework

## Development Philosophy

### Branch Strategy
```
main (stable) 
├── feature/tavern-expansion
├── feature/narrative-engine  
├── feature/npc-depth
├── feature/gm-controls
└── feature/integration
```

### Testing Requirements
- Every feature must have tests
- No breaking changes to existing save files
- Performance benchmarks must be maintained
- LLM integration must have offline fallbacks

### Merge Criteria
- All tests passing
- Code review completed
- Documentation updated
- Performance validated

## Phase 1: Foundation Strengthening (Weeks 1-2)

### 1.1 Code Quality & Architecture
**Priority: CRITICAL**
**Dependencies: None**

**Tasks:**
- [ ] Complete test infrastructure setup
- [ ] Fix remaining thread safety issues
- [ ] Implement comprehensive error handling
- [ ] Establish coding standards and linting
- [ ] Create development environment documentation

**Files to Modify:**
- `tests/` (expand test coverage)
- `core/error_recovery.py` (enhance)
- `docs/DEVELOPMENT_SETUP.md` (create)

**Success Criteria:**
- 90%+ test coverage on core systems
- All race conditions eliminated
- Clean development environment setup

**Validation:**
```bash
pytest tests/ --cov=core --cov-report=html
python -m pytest tests/test_thread_safety.py -v
```

### 1.2 Enhanced Persistence Layer
**Priority: HIGH**
**Dependencies: 1.1**

**Tasks:**
- [ ] Implement versioned save format
- [ ] Add migration system for saves
- [ ] Create backup/restore functionality
- [ ] Add save validation

**Files to Create:**
- `core/persistence/save_manager.py`
- `core/persistence/migrations.py`
- `core/persistence/validation.py`

**Success Criteria:**
- Backward compatible save loading
- Automatic migration of old saves
- Corruption detection and recovery

### 1.3 Performance Baseline
**Priority: MEDIUM**
**Dependencies: 1.1**

**Tasks:**
- [ ] Establish performance benchmarks
- [ ] Create performance monitoring
- [ ] Optimize critical paths
- [ ] Document performance expectations

**Files to Create:**
- `tests/performance/benchmarks.py`
- `core/monitoring/performance.py`

**Success Criteria:**
- Sub-100ms turn processing
- Memory usage under 200MB
- Consistent frame times

## Phase 2: Tavern Architecture Expansion (Weeks 3-4)

### 2.1 Multi-Area System
**Priority: CRITICAL**
**Dependencies: 1.2 (save system)**

**Tasks:**
- [ ] Design area connection graph
- [ ] Implement area transitions
- [ ] Create area-specific properties
- [ ] Add movement validation

**Files to Create:**
- `core/world/area.py`
- `core/world/area_manager.py`
- `core/world/connections.py`

**Files to Modify:**
- `core/room.py` → integrate with area system
- `core/game_state.py` → add area tracking

**Implementation Details:**
```python
class TavernArea:
    id: str
    floor: int
    name: str
    description: str
    atmosphere: AtmosphereState
    connections: List[Connection]
    features: List[Feature]
    capacity: int
    current_occupants: List[str]
    
class AreaManager:
    areas: Dict[str, TavernArea]
    current_area: str
    
    def move_to_area(player_id, area_id) -> MoveResult
    def get_available_exits() -> List[Connection]
    def update_area_state() -> None
```

**Success Criteria:**
- Player can move between 5+ distinct areas
- Each area has unique properties and atmosphere
- Movement respects time, permissions, visibility

**Validation:**
- Create test tavern with cellar, ground floor, upper rooms
- Verify smooth transitions between areas
- Test save/load preserves area state

### 2.2 Floor-Based Layout
**Priority: HIGH**
**Dependencies: 2.1**

**Tasks:**
- [ ] Implement vertical movement system
- [ ] Add floor-specific events
- [ ] Create accessibility rules
- [ ] Design floor-specific NPCs

**Areas to Implement:**
```
CELLAR (-1):
├── Storage Room
├── Wine Cellar  
├── Deep Cellar (secrets)
└── Hidden Passage

GROUND (0):
├── Main Hall
├── Bar Area
├── Kitchen
├── Private Booth
└── Fireplace Nook

FIRST (1):
├── Guest Rooms (3-4)
├── Gambling Den
├── Private Dining
└── Balcony Overlook

SECOND (2):
├── Owner's Quarters
├── Premium Suites
├── Storage Attic
└── Crow's Nest
```

**Files to Create:**
- `data/areas/tavern_layout.json`
- `core/world/floor_manager.py`

**Success Criteria:**
- All floors accessible with proper permissions
- Each floor has distinct atmosphere and purpose
- Vertical sound/sight propagation works

### 2.3 Dynamic Area Properties
**Priority: MEDIUM**
**Dependencies: 2.2**

**Tasks:**
- [ ] Implement atmospheric changes
- [ ] Add crowd density effects
- [ ] Create lighting/temperature systems
- [ ] Enable area-specific rules

**Implementation:**
```python
class AtmosphereState:
    noise_level: float  # 0.0 (silent) to 1.0 (raucous)
    lighting: float     # 0.0 (dark) to 1.0 (bright)
    crowd_density: float # 0.0 (empty) to 1.0 (packed)
    temperature: float   # Affects comfort
    
    def affects_conversation() -> bool
    def affects_stealth() -> bool
    def affects_eavesdropping() -> bool
```

**Success Criteria:**
- Atmosphere affects gameplay mechanics
- Changes propagate logically (noise travels)
- Time of day influences all areas appropriately

## Phase 3: Deep NPC System (Weeks 5-6)

### 3.1 NPC Inner Lives
**Priority: CRITICAL**
**Dependencies: 2.1 (areas for context)**

**Tasks:**
- [ ] Design secret and motivation system
- [ ] Implement behavioral rules engine
- [ ] Create memory and relationship depth
- [ ] Add multi-layered personalities

**Files to Create:**
- `core/npc/psychology.py`
- `core/npc/secrets.py`
- `core/npc/motivations.py`
- `core/npc/behavioral_rules.py`

**Implementation:**
```python
class NPCPsychology:
    public_persona: PersonaLayer
    private_thoughts: PersonaLayer
    hidden_secrets: List[Secret]
    core_motivations: List[Motivation]
    behavioral_rules: List[BehaviorRule]
    
class Secret:
    content: str
    danger_level: float
    known_by: List[str]
    evidence_trail: List[Evidence]
    revelation_conditions: List[Condition]
    consequences: Dict[str, Consequence]
    
class BehaviorRule:
    condition: Condition
    action: Action
    priority: float
    cooldown: float
```

**Success Criteria:**
- NPCs have 2-3 secrets each with varying danger levels
- Behavioral rules create consistent but complex personalities
- Secrets can be discovered through investigation
- NPC actions driven by hidden motivations

### 3.2 Relationship Web System
**Priority: HIGH**
**Dependencies: 3.1**

**Tasks:**
- [ ] Implement complex relationship tracking
- [ ] Create faction and alliance system
- [ ] Add reputation with multiple groups
- [ ] Design relationship propagation

**Files to Create:**
- `core/social/relationships.py`
- `core/social/factions.py`
- `core/social/reputation.py`

**Implementation:**
```python
class RelationshipWeb:
    relationships: Dict[Tuple[str, str], Relationship]
    factions: Dict[str, Faction]
    reputation_scores: Dict[Tuple[str, str], float]
    
    def propagate_reputation_change()
    def detect_relationship_conflicts()
    def find_mutual_connections()
    
class Relationship:
    relationship_type: RelationType  # friend, rival, lover, enemy
    strength: float
    history: List[RelationshipEvent]
    secrets_shared: List[str]
    debts_owed: List[Debt]
```

**Success Criteria:**
- Actions toward one NPC affect relationships with others
- Faction membership influences interactions
- Relationship history affects current behavior
- Complex social dynamics emerge naturally

### 3.3 NPC Agency and Goals
**Priority: MEDIUM**
**Dependencies: 3.1, 3.2**

**Tasks:**
- [ ] Implement NPC goal pursuit
- [ ] Create inter-NPC interactions
- [ ] Add NPC-driven events
- [ ] Design conflict generation

**Files to Create:**
- `core/npc/goals.py`
- `core/npc/interactions.py`
- `core/npc/conflicts.py`

**Success Criteria:**
- NPCs pursue goals independent of player
- NPCs interact meaningfully with each other
- Conflicts arise naturally from competing goals
- Player can influence but not control NPC actions

## Phase 4: Narrative Engine (Weeks 7-9)

### 4.1 Story Thread Management
**Priority: CRITICAL**
**Dependencies: 3.2 (relationship web)**

**Tasks:**
- [ ] Implement story thread tracking
- [ ] Create thread stage progression
- [ ] Add thread convergence detection
- [ ] Design thread resolution system

**Files to Create:**
- `core/narrative/story_thread.py`
- `core/narrative/thread_manager.py`
- `core/narrative/convergence.py`

**Implementation:**
```python
class StoryThread:
    id: str
    title: str
    participants: List[str]
    stage: ThreadStage
    tension_level: float
    player_involvement: float
    beats: List[StoryBeat]
    resolution_conditions: List[Condition]
    
class ThreadManager:
    active_threads: List[StoryThread]
    completed_threads: List[StoryThread]
    
    def advance_threads() -> List[StoryBeat]
    def detect_convergence() -> List[Convergence]
    def resolve_thread() -> Resolution
```

**Success Criteria:**
- 3-7 threads active simultaneously
- Threads progress through clear stages
- Convergences create dramatic moments
- All threads reach satisfying conclusions

### 4.2 Narrative Rules Engine
**Priority: HIGH**
**Dependencies: 4.1**

**Tasks:**
- [ ] Implement pacing rules
- [ ] Create tension management
- [ ] Add narrative health monitoring
- [ ] Design intervention system

**Files to Create:**
- `core/narrative/rules.py`
- `core/narrative/pacing.py`
- `core/narrative/tension.py`
- `core/narrative/health.py`

**Implementation:**
```python
class NarrativeRules:
    MAX_SIMULTANEOUS_CRISES = 2
    MIN_BEATS_BETWEEN_CRISES = 5
    TENSION_BUILD_RATE = 0.1
    
    def evaluate_pacing() -> PacingScore
    def check_tension_level() -> TensionState
    def suggest_interventions() -> List[Intervention]
    
class TensionManager:
    current_tension: float
    tension_sources: List[TensionSource]
    
    def calculate_overall_tension() -> float
    def identify_pressure_points() -> List[Point]
    def recommend_release_valve() -> Action
```

**Success Criteria:**
- Pacing feels natural and engaging
- Tension builds and releases appropriately
- No more than 2 crises simultaneously
- System intervenes to prevent narrative collapse

### 4.3 Arc Orchestration
**Priority: MEDIUM**
**Dependencies: 4.2**

**Tasks:**
- [ ] Implement major arc tracking
- [ ] Create arc progression system
- [ ] Add climax orchestration
- [ ] Design closure validation

**Files to Create:**
- `core/narrative/arcs.py`
- `core/narrative/orchestration.py`
- `core/narrative/closure.py`

**Success Criteria:**
- 1-3 major arcs active over weeks of play
- Arcs have clear setup, confrontation, resolution
- Climaxes feel earned and satisfying
- All arcs reach proper closure

## Phase 5: GM Control Framework (Weeks 10-11)

### 5.1 Story Seed System
**Priority: HIGH**
**Dependencies: 4.1 (story threads)**

**Tasks:**
- [ ] Design seed injection mechanism
- [ ] Create seed library
- [ ] Implement seed evolution
- [ ] Add seed monitoring

**Files to Create:**
- `core/gm/seeds.py`
- `core/gm/seed_library.py`
- `data/story_seeds/`

**Implementation:**
```python
class StorySeed:
    id: str
    seed_type: SeedType
    participants: List[str]
    conditions: List[Condition]
    potential_threads: List[ThreadTemplate]
    intensity: float
    
class SeedManager:
    available_seeds: List[StorySeed]
    planted_seeds: List[PlantedSeed]
    
    def inject_seed() -> PlantedSeed
    def monitor_growth() -> List[SeedStatus]
    def evolve_to_thread() -> StoryThread
```

**Success Criteria:**
- 20+ seed types available
- Seeds evolve naturally into threads
- GM can inject appropriate seeds for current state
- Seed growth feels organic

### 5.2 Narrative Health Dashboard
**Priority: MEDIUM**
**Dependencies: 4.2 (rules engine)**

**Tasks:**
- [ ] Create narrative health metrics
- [ ] Build monitoring dashboard
- [ ] Add alert system
- [ ] Design intervention tools

**Files to Create:**
- `core/gm/dashboard.py`
- `core/gm/metrics.py`
- `core/gm/alerts.py`

**Success Criteria:**
- Clear visibility into narrative state
- Early warning for problems
- Actionable intervention suggestions
- Simple interface for GM control

### 5.3 Dynamic Event Generation
**Priority: MEDIUM**
**Dependencies: 5.1**

**Tasks:**
- [ ] Implement event templates
- [ ] Create context-aware generation
- [ ] Add event chaining
- [ ] Design impact assessment

**Files to Create:**
- `core/gm/events.py`
- `core/gm/event_generation.py`
- `data/event_templates/`

**Success Criteria:**
- Events feel appropriate to current context
- Events chain naturally to create larger stories
- Impact assessment predicts consequences
- Generated events enhance rather than disrupt

## Phase 6: Integration & Polish (Weeks 12-14)

### 6.1 System Integration
**Priority: CRITICAL**
**Dependencies: All previous phases**

**Tasks:**
- [ ] Integrate all systems seamlessly
- [ ] Resolve system conflicts
- [ ] Optimize cross-system communication
- [ ] Validate end-to-end functionality

**Focus Areas:**
- Area system ↔ NPC behavior
- Story threads ↔ relationship changes
- GM tools ↔ natural progression
- Player actions ↔ narrative impact

### 6.2 Performance Optimization
**Priority: HIGH**
**Dependencies: 6.1**

**Tasks:**
- [ ] Profile complete system
- [ ] Optimize bottlenecks
- [ ] Implement advanced caching
- [ ] Validate performance targets

**Targets:**
- Turn processing: <100ms
- Memory usage: <500MB
- Save file size: <10MB
- Thread management: <10ms overhead

### 6.3 Content Creation Tools
**Priority: MEDIUM**
**Dependencies: 6.1**

**Tasks:**
- [ ] Create NPC authoring tools
- [ ] Build area design interface
- [ ] Add story seed editor
- [ ] Implement content validation

**Success Criteria:**
- Non-programmers can create NPCs
- Areas can be designed visually
- Story content validates automatically
- Tools integrate with main engine

## Validation Framework

### Phase Gates
Each phase must pass these criteria before proceeding:

**Code Quality:**
- [ ] 90%+ test coverage
- [ ] All tests passing
- [ ] Code review completed
- [ ] Documentation updated

**Functionality:**
- [ ] All acceptance criteria met
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Save/load compatibility maintained

**User Experience:**
- [ ] Features are discoverable
- [ ] Error messages are helpful
- [ ] Performance is acceptable
- [ ] Saves from previous phases still work

### Testing Strategy
```
Unit Tests: Test individual components
Integration Tests: Test system interactions  
Narrative Tests: Test story coherence
Performance Tests: Test speed/memory
Regression Tests: Test compatibility
End-to-End Tests: Test complete workflows
```

## Risk Mitigation

### Technical Risks
- **State explosion**: Implement state pruning and archiving
- **Performance degradation**: Continuous benchmarking
- **Save corruption**: Versioned saves with validation
- **System complexity**: Clear interfaces and documentation

### Design Risks
- **Narrative incoherence**: Strong rule system with validation
- **Player confusion**: Clear feedback and guidance
- **Content drought**: Procedural generation fallbacks
- **Feature creep**: Strict phase gates and scope control

## Success Metrics

### Phase 2 Success:
- Player can navigate 10+ distinct areas
- Each area feels unique and purposeful
- Movement is intuitive and meaningful

### Phase 3 Success:
- NPCs feel like real people with hidden depths
- Relationships are complex and consequential
- Social dynamics drive gameplay

### Phase 4 Success:
- Stories emerge naturally from character interactions
- Multiple threads weave together coherently
- Player choices meaningfully affect outcomes

### Phase 5 Success:
- GM tools enhance rather than replace natural progression
- Narrative health is maintained automatically
- New content can be injected seamlessly

### Phase 6 Success:
- All systems work together harmoniously
- Performance meets all targets
- Game provides deep, replayable narrative experience

## Conclusion

This roadmap provides a logical progression from the current simple tavern to a deep, narrative-rich experience. Each phase builds upon the previous while maintaining system stability and backward compatibility.

The key is to **never break what works** while steadily adding depth and complexity. By the end, we'll have created a unique gaming experience where a single tavern contains infinite stories.

**Remember: The goal is not feature completeness, but narrative depth and emotional engagement.**