# The Living Tavern: Deep Narrative Engine Design

## Overview
A comprehensive design for a deeply simulated single-location narrative engine where the player never leaves the tavern, but experiences rich, interconnected stories across multiple areas and floors.

## Core Principles
- **Single Location, Infinite Depth**: The tavern has multiple areas across several floors, each with unique atmosphere and purpose
- **Turn-Based with Living World**: Performance is turn-based, but the world slowly evolves during player idle time
- **Rule-Based Narrative**: Strong guardrails ensure coherent story progression with proper growth, arcs, and closure
- **Complete Knowledge**: The system tracks everything for rich, consequential storytelling

## 1. Tavern Architecture System

```python
class TavernArea:
    """Distinct areas within the tavern"""
    id: str
    floor: int
    name: str
    atmosphere: Dict[str, float]  # warmth, noise, light, crowd
    connections: List[str]  # Connected areas
    capacity: int
    features: List[Feature]  # Bar, fireplace, stage, etc.
    secrets: List[Secret]  # Hidden passages, loose floorboards
    
class TavernFloor:
    CELLAR = -1     # Storage, secrets, maybe something darker
    GROUND = 0      # Main hall, bar, kitchen
    FIRST = 1       # Private rooms, gambling den
    SECOND = 2      # Premium rooms, owner's quarters
    ATTIC = 3       # Storage, hidden areas, crow's nest view

class AreaTransition:
    """Movement between areas affects narrative"""
    visibility: float  # How observed is this transition
    requirements: List[str]  # Keys, permissions, time of day
    triggers: List[str]  # What happens when used
```

## 2. Narrative Arc Management

```python
class NarrativeArc:
    """Story structure with clear progression"""
    id: str
    title: str
    act: int  # 1-3 (Setup, Confrontation, Resolution)
    tension_level: float
    stakes: List[Stake]
    active_threads: List[StoryThread]
    completion_requirements: List[Requirement]
    consequences: Dict[str, Consequence]
    
class StoryThread:
    """Individual storylines that weave together"""
    id: str
    arc_id: str
    participants: List[str]  # NPCs involved
    stage: ThreadStage  # SEED, GROWING, CRISIS, RESOLVING, COMPLETE
    tension_contribution: float
    player_involvement: float
    available_actions: List[PlayerAction]
    next_beat_conditions: List[Condition]

class ThreadStage(Enum):
    SEED = "seed"  # Just beginning, barely noticeable
    GROWING = "growing"  # Building tension
    CRISIS = "crisis"  # Demands action
    RESOLVING = "resolving"  # Playing out consequences
    COMPLETE = "complete"  # Resolved, becomes history
```

## 3. Rule-Based Story Engine

```python
class StoryRules:
    """Guardrails for narrative coherence"""
    
    # Pacing Rules
    MIN_BEATS_BETWEEN_CRISES = 5
    MAX_SIMULTANEOUS_CRISES = 2
    TENSION_BUILD_RATE = 0.1
    TENSION_RELEASE_RATE = 0.3
    
    # Arc Rules
    MAX_ACTIVE_MAJOR_ARCS = 3
    MAX_ACTIVE_MINOR_ARCS = 7
    MIN_SETUP_DURATION = 10  # turns
    
    # Character Rules
    MAX_NPC_SECRETS = 3
    RELATIONSHIP_CHANGE_RATE = 0.2
    TRUST_REVEAL_THRESHOLD = 0.7
    
    # Consequence Rules
    CONSEQUENCE_DECAY_RATE = 0.05
    REPUTATION_IMPACT_MULTIPLIER = 1.5
    
class NarrativeGM:
    """The GM's rule-based control system"""
    
    def evaluate_story_state(self) -> StoryState:
        """Check narrative health"""
        return {
            'tension_level': self.calculate_overall_tension(),
            'arc_balance': self.check_arc_distribution(),
            'pacing_score': self.evaluate_pacing(),
            'player_engagement': self.measure_engagement()
        }
    
    def get_next_beat_options(self) -> List[StoryBeat]:
        """What should happen next?"""
        options = []
        
        # Check each thread for ready beats
        for thread in self.active_threads:
            if thread.is_ready_for_next_beat():
                options.extend(thread.get_possible_beats())
        
        # Filter by rules
        return self.apply_narrative_rules(options)
    
    def inject_story_seed(self, seed_type: str, intensity: float):
        """Plant a new story element"""
        # Examples: 'mysterious_stranger', 'old_debt', 'hidden_treasure'
```

## 4. Deep NPC Narrative System

```python
class NPCNarrative:
    """Rich inner lives for NPCs"""
    
    npc_id: str
    
    # Public Face
    public_story: str  # What everyone knows
    reputation: Dict[str, float]  # Different groups view differently
    
    # Hidden Depths  
    secrets: List[Secret]
    true_motivations: List[Motivation]
    past_wounds: List[Trauma]
    
    # Relationships
    alliances: List[Alliance]
    rivalries: List[Rivalry]
    debts: List[Debt]  # Owed and owing
    
    # Story Participation
    active_threads: List[str]
    thread_roles: Dict[str, Role]  # protagonist, antagonist, catalyst
    
    # Behavioral Rules
    will_reveal_secret_if: List[Condition]
    will_betray_if: List[Condition]
    will_help_if: List[Condition]

class Secret:
    """Information with narrative weight"""
    id: str
    content: str
    danger_level: float  # How bad if revealed
    known_by: List[str]  # Who else knows
    evidence: List[str]  # What could expose it
    revelation_impact: Dict[str, Impact]
```

## 5. Tavern Activity Cycles

```python
class TavernCycle:
    """Natural rhythms that drive stories"""
    
    DAILY_PHASES = [
        "dawn_prep",      # 4-6am: Staff preparing
        "morning_crowd",  # 6-10am: Travelers leaving
        "midday_lull",    # 10am-2pm: Quiet plotting time
        "afternoon_trade", # 2-5pm: Merchants, deals
        "evening_rush",   # 5-9pm: Main crowd
        "night_revelry",  # 9pm-1am: Drinking, gambling
        "deep_night"      # 1-4am: Secrets, danger
    ]
    
    WEEKLY_EVENTS = [
        "market_day",     # Traders flood in
        "courier_day",    # News arrives
        "celebration",    # Local festival
        "tax_day",       # Tensions high
    ]
    
    SEASONAL_ARCS = [
        "harvest_festival",
        "winter_isolation",  # Snowed in!
        "spring_travelers",
        "summer_tournament"
    ]

class ActivityPattern:
    """What happens in each area during each phase"""
    area_id: str
    phase: str
    typical_npcs: List[str]
    typical_activities: List[str]
    story_opportunities: List[str]
```

## 6. Multi-Level Narrative Tracking

```python
class NarrativeLayer(Enum):
    IMMEDIATE = "immediate"    # This conversation
    SCENE = "scene"           # This evening  
    CHAPTER = "chapter"       # This week
    ARC = "arc"              # This storyline
    CAMPAIGN = "campaign"     # Overall journey

class NarrativeTracker:
    """Tracks all story elements"""
    
    def get_active_elements(self, layer: NarrativeLayer) -> List[Element]:
        """What's happening at each scale"""
        
    def check_convergence_points(self) -> List[Convergence]:
        """When will threads collide?"""
        
    def predict_crisis_points(self) -> List[Crisis]:
        """Where is tension building?"""
        
    def find_resolution_opportunities(self) -> List[Resolution]:
        """How can threads resolve?"""
```

## 7. GM Decision Engine

```python
class GMDecisionEngine:
    """Makes narrative choices based on rules"""
    
    def decide_npc_action(self, npc: NPC, context: Context) -> Action:
        """What should this NPC do now?"""
        
        # Check narrative role
        if npc.is_protagonist_in_active_thread():
            return self.advance_protagonist_goal(npc)
        
        # Check relationships  
        if npc.has_unresolved_conflict():
            return self.pursue_conflict_resolution(npc)
            
        # Check opportunities
        if self.spot_story_opportunity(npc, context):
            return self.create_new_thread(npc)
            
        # Default behavior
        return self.routine_behavior(npc)
    
    def orchestrate_scene(self, location: str, time: str) -> Scene:
        """Compose a meaningful scene"""
        
        # Gather participants
        npcs = self.get_npcs_in_area(location)
        threads = self.get_active_threads(location)
        
        # Check for convergence
        if self.detect_thread_collision(threads):
            return self.create_confrontation_scene()
            
        # Build tension
        if self.narrative_needs_tension():
            return self.create_complication_scene()
            
        # Develop relationships
        return self.create_character_scene()
```

## 8. Player Agency & Story Integration

```python
class PlayerStoryIntegration:
    """How player actions affect narrative"""
    
    def evaluate_action_impact(self, action: PlayerAction) -> Impact:
        """How does this affect active stories?"""
        
        impacts = []
        
        # Direct thread impacts
        for thread in self.active_threads:
            if thread.involves(action.target):
                impacts.append(thread.calculate_impact(action))
        
        # Relationship ripples
        for npc in self.get_affected_npcs(action):
            impacts.append(self.calculate_relationship_change(npc, action))
            
        # New thread potential
        if self.action_creates_opportunity(action):
            impacts.append(self.spawn_new_thread(action))
            
        return self.combine_impacts(impacts)
```

## 9. Narrative Closure System

```python
class ClosureManager:
    """Ensures satisfying conclusions"""
    
    def evaluate_thread_completion(self, thread: StoryThread) -> ClosureQuality:
        """Is this ready to end well?"""
        
        checks = {
            'stakes_addressed': thread.all_stakes_resolved(),
            'character_growth': thread.characters_changed(),
            'player_agency': thread.player_made_difference(),
            'thematic_resonance': thread.theme_expressed(),
            'emotional_satisfaction': thread.emotional_arc_complete()
        }
        
        return self.calculate_closure_quality(checks)
    
    def force_closure_if_needed(self, thread: StoryThread):
        """Gracefully end overlong threads"""
        
        if thread.duration > MAX_THREAD_DURATION:
            return self.create_climactic_event(thread)
```

## 10. Living Story Example

```python
# Morning in the tavern
phase = "morning_crowd"
location = "main_hall"

# GM evaluates state
gm.evaluate_story_state()
# Result: Low tension, need to plant seeds

# GM injects story seed
gm.inject_story_seed("mysterious_package_arrives", intensity=0.6)

# This creates:
thread = StoryThread(
    id="package_mystery_001",
    stage=ThreadStage.SEED,
    participants=["courier", "innkeeper", "curious_patron"],
    available_actions=[
        "ask_about_package",
        "try_to_peek",
        "offer_to_help",
        "ignore_it"
    ]
)

# Player asks about package
# GM rules engine determines:
- Courier is nervous (secret: package contains evidence)
- Innkeeper is protective (debt: owes sender favor)  
- Curious patron is scheming (motivation: always looking for leverage)

# This spawns new threads:
- "Courier's Dilemma" (will they deliver or flee?)
- "Innkeeper's Debt" (old obligation comes due)
- "Patron's Scheme" (blackmail opportunity?)

# As player investigates, threads interweave
# Building toward confrontation where all parties' interests collide
# Player choices determine which thread becomes dominant
# Leading to different but satisfying conclusions
```

## Key Design Principles

1. **Every NPC has a story** - Not just quest givers
2. **Time pressure creates drama** - Things happen without player
3. **Consequences cascade** - Small actions have big effects
4. **Multiple valid endings** - No single "correct" path
5. **Emotional stakes** - Not just mechanical rewards

## Implementation Priority

1. **Phase 1**: Tavern architecture and basic area system
2. **Phase 2**: Story thread management and rules engine
3. **Phase 3**: Deep NPC narratives and relationships
4. **Phase 4**: GM decision engine and dynamic events
5. **Phase 5**: Player integration and closure systems

## Technical Considerations

- **State Management**: Every narrative element must be serializable
- **Performance**: Turn-based with efficient idle processing
- **Determinism**: Same inputs should create similar (not identical) story beats
- **Extensibility**: Easy to add new story seeds, NPC types, and rules
- **Debugging**: Clear visibility into why narrative decisions were made