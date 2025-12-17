# Deep Agent System - Integration & Scaling Plan

## Vision: Epic-Scale Emergent Simulation

This document outlines how to integrate the Deep Agent System with Taverna's existing systems and scale it to create an unprecedented emergent simulation ecosystem.

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Integration Points](#integration-points)
3. [Scaling Strategy](#scaling-strategy)
4. [Emergent Culture & Evolution](#emergent-culture--evolution)
5. [Performance Optimization](#performance-optimization)
6. [Implementation Phases](#implementation-phases)
7. [Demonstration Examples](#demonstration-examples)
8. [Future Enhancements](#future-enhancements)

---

## System Architecture Overview

### Current State
We have built:
- **6 Deep Agents**: Sarah, Gene, Marcus, Raven, Aldric, Lyra (each ~450 lines of psychological modeling)
- **8 Core Systems**: Personality, Needs, Emotions, Beliefs, Memory, Goals, Agent, Observer (~4,000 lines)
- **Social Dynamics Engine**: Multi-agent interactions, relationships, gossip, conversations (~800 lines)

### Integration Vision
```
                    ┌─────────────────────────────────┐
                    │   TAVERNA GAME ENGINE          │
                    │  (Existing Event/NPC/Economy)  │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │   DEEP AGENT ORCHESTRATOR      │
                    │  - Agent Lifecycle Management   │
                    │  - Cognitive Cycle Scheduling   │
                    │  - Inter-System Communication   │
                    └──────────────┬──────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐    ┌───────────▼────────┐    ┌──────────▼─────────┐
│  INDIVIDUAL    │    │  SOCIAL DYNAMICS   │    │  CULTURAL          │
│  AGENTS        │◄───┤  ENGINE            │───►│  EVOLUTION         │
│                │    │                    │    │  TRACKER           │
│ - Cognitive    │    │ - Relationships    │    │ - Shared Beliefs   │
│   Cycles       │    │ - Conversations    │    │ - Traditions       │
│ - Memories     │    │ - Gossip Network   │    │ - Narratives       │
│ - Goals        │    │ - Reputation       │    │ - Artifacts        │
└────────────────┘    └────────────────────┘    └────────────────────┘
        │                          │                          │
        └──────────────────────────┴──────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │   GAME STATE & PERSISTENCE     │
                    │  - Save/Load Agent States      │
                    │  - Relationship Serialization  │
                    │  - Historical Event Log        │
                    └─────────────────────────────────┘
```

---

## Integration Points

### 1. Event System Integration

**Current**: Taverna has an event bus (`living_rusted_tankard/core/events/bus.py`)

**Integration**:
```python
# agents/game_integration.py

from ..events.bus import EventBus
from .agent import DeepAgent

class AgentEventAdapter:
    """Connects agents to game event system."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.agents: Dict[str, DeepAgent] = {}

    def register_agent(self, agent: DeepAgent):
        """Register agent to receive events."""
        self.agents[agent.agent_id] = agent

    def on_event(self, event: Dict[str, Any]):
        """
        Event from game → Update agent beliefs, memories, emotions.

        Examples:
        - ECONOMY_PRICE_CHANGE → Sarah updates beliefs about suppliers
        - NPC_INTERACTION → Agents update theory of mind
        - PLAYER_ACTION → Agents observe and react
        """
        event_type = event['type']

        # Route to relevant agents
        for agent in self.agents.values():
            if self._is_event_relevant(agent, event):
                self._process_event_for_agent(agent, event)

    def _process_event_for_agent(self, agent: DeepAgent, event: Dict):
        """Process event through agent's perception."""

        # Update beliefs
        if event['type'] == 'ECONOMY_PRICE_CHANGE':
            agent.beliefs.add_belief(
                BeliefType.FACT,
                "economy",
                f"Prices changed: {event['description']}",
                confidence=0.9,
                evidence="Direct observation"
            )

        # Create memory
        if event.get('importance', 0) > 0.5:
            agent.episodic_memory.add_memory(
                content=event['description'],
                location=event.get('location', 'unknown'),
                participants=event.get('participants', []),
                emotional_valence=event.get('emotional_impact', 0),
                emotional_intensity=event.get('intensity', 0.5),
                importance=event['importance']
            )

        # Trigger emotions
        if event['type'] == 'THREAT':
            agent.emotions.trigger_emotion(
                EmotionType.FEAR,
                intensity=event.get('intensity', 0.5),
                trigger=event['description']
            )
```

### 2. NPC System Replacement

**Current**: Taverna has basic NPCs (`living_rusted_tankard/game/npcs/`)

**Migration Strategy**:
```python
# agents/npc_bridge.py

class DeepAgentNPC:
    """
    Wrapper to make DeepAgent compatible with existing NPC interface.

    Allows gradual migration: start with deep agents for key NPCs,
    keep simple NPCs for background characters.
    """

    def __init__(self, deep_agent: DeepAgent):
        self.agent = deep_agent

    # Implement existing NPC interface
    def get_dialogue(self, player_input: str) -> str:
        """
        OLD NPC: Returns scripted dialogue
        NEW: Returns dialogue based on agent's internal state
        """
        # Agent's cognitive cycle processes player input
        game_state = {
            'player_input': player_input,
            'location': self.agent.current_location,
            'participants': ['player']
        }

        action = self.agent.cognitive_cycle(game_state)

        if action and action.command.startswith('SAY:'):
            return action.command[4:]  # Remove 'SAY:' prefix

        # Fallback: Generate based on emotional state
        emotion = self.agent.emotions.get_dominant_emotion()
        return self._generate_contextual_dialogue(emotion)

    def _generate_contextual_dialogue(self, emotion):
        """Generate dialogue based on current emotional state."""
        # This could call LLM with agent's internal state as context
        # For now, simple mood-based responses

        mood = self.agent.emotions.mood.get_mood_descriptor()
        active_goal = self.agent.goals.get_active_goal()

        # Combine mood + goal → contextual response
        if active_goal and active_goal.goal_type == GoalType.SURVIVAL:
            if mood == "anxious":
                return "I... I need to focus on business right now."

        return "Hello."  # Fallback
```

### 3. Economy System Integration

**Current**: Taverna has dynamic economy (`living_rusted_tankard/game/economy/`)

**Integration**:
```python
# agents/economy_integration.py

class AgentEconomicBehavior:
    """Agents participate in economy based on their needs and goals."""

    def __init__(self, economy_engine, social_engine):
        self.economy = economy_engine
        self.social = social_engine

    def agent_economic_decision(self, agent: DeepAgent) -> Optional[Dict]:
        """
        Agent makes economic decision based on:
        - Current needs (hunger → buy food)
        - Active goals (survival → sell goods)
        - Personality (risk tolerance → investments)
        - Beliefs (price fairness → boycotts)
        - Relationships (buy from friends)
        """

        # Check needs
        urgent_needs = agent.needs.get_urgent_needs()

        if NeedType.HUNGER in urgent_needs:
            # Try to buy food
            return {
                'action': 'BUY',
                'item': 'food',
                'max_price': agent.personality.risk_tolerance * 10,
                'reasoning': 'Hungry - need food urgently'
            }

        # Check goals
        active_goal = agent.goals.get_active_goal()

        if active_goal and 'gold' in active_goal.description:
            # Trying to make money
            # Decision influenced by personality

            if agent.personality.conscientiousness > 0.7:
                # Honest approach (like Sarah)
                return {
                    'action': 'SELL',
                    'item': 'goods',
                    'min_price': 'fair_market_value',
                    'reasoning': f"Working toward: {active_goal.description}"
                }
            else:
                # Might consider shady deals (like Raven)
                if agent.personality.values:
                    honesty_value = next(
                        (v for v in agent.personality.values if v.name == 'fairness'),
                        None
                    )
                    if not honesty_value or honesty_value.strength < 0.5:
                        return {
                            'action': 'STEAL',  # Raven's approach
                            'target': 'wealthy_merchant',
                            'reasoning': "Survival over rules"
                        }

        # Check relationships - buy from friends
        relationships = self.social.social_network.get_agent_relationships(
            agent.agent_id
        )

        friends = [
            r for r in relationships
            if r.relationship_type == RelationshipType.FRIEND
        ]

        if friends and random.random() < 0.3:
            friend_rel = random.choice(friends)
            friend_id = (
                friend_rel.agent_b_id
                if friend_rel.agent_a_id == agent.agent_id
                else friend_rel.agent_a_id
            )

            return {
                'action': 'BUY_FROM',
                'seller': friend_id,
                'preference_bonus': 0.2,  # Willing to pay 20% more for friend
                'reasoning': f"Supporting friend {friend_id}"
            }

        return None
```

### 4. Quest/Task System

**Integration**:
```python
# agents/quest_integration.py

class AgentQuestGenerator:
    """Generate dynamic quests from agent states."""

    def generate_quests_from_agents(
        self, agents: List[DeepAgent]
    ) -> List[Dict]:
        """
        Scan agents for urgent needs/goals → create quests for player.

        This creates REACTIVE content - quests emerge from agent states,
        not scripted by designers.
        """
        quests = []

        for agent in agents:
            # Sarah needs money → quest opportunity
            if agent.agent_id == 'sarah_merchant':
                goal = agent.goals.get_active_goal()
                if goal and 'gold' in goal.description:
                    quests.append({
                        'title': "Help Sarah with her Business",
                        'description': f"{agent.name} is struggling. She needs: {goal.description}",
                        'giver': agent.agent_id,
                        'reward': 'sarah_friendship',
                        'objectives': [
                            f"Help Sarah make {goal.success_condition}",
                        ],
                        'emergent': True,  # Flag as emergent content
                    })

            # Aldric suspects Raven → investigation quest
            if agent.agent_id == 'aldric_guard':
                beliefs = agent.beliefs.get_beliefs_about('raven')
                if beliefs and any('thief' in b.content.lower() for b in beliefs):
                    quests.append({
                        'title': "The Hooded Thief",
                        'description': "Captain Aldric suspects someone in the tavern of theft",
                        'giver': agent.agent_id,
                        'reward': 'law_reputation',
                        'objectives': [
                            "Gather evidence about the thief",
                            "Decide: Help Aldric arrest her, or help Raven escape"
                        ],
                        'moral_choice': True,
                        'emergent': True,
                    })

            # Marcus's mystery → exploration quest
            if agent.agent_id == 'marcus_wanderer':
                memories = agent.episodic_memory.recall_emotional(
                    valence=-0.5, min_intensity=0.7
                )
                if memories:
                    quests.append({
                        'title': "The Wanderer's Lost Memory",
                        'description': "Marcus speaks of forgotten places and lost purposes",
                        'giver': agent.agent_id,
                        'reward': 'cosmic_knowledge',
                        'objectives': [
                            "Help Marcus remember his origins",
                            "Discover the truth about the tavern"
                        ],
                        'mystery': True,
                        'emergent': True,
                    })

        return quests
```

---

## Scaling Strategy

### Agent Population Management

**Challenge**: Can't run 100 deep agents in real-time (too computationally expensive)

**Solution**: Tiered Agent System

```python
# agents/scaling.py

class AgentTier(Enum):
    DEEP = "deep"        # Full cognitive cycles (6 agents)
    MEDIUM = "medium"    # Simplified cycles (20 agents)
    SIMPLE = "simple"    # Reactive only (100+ agents)
    BACKGROUND = "background"  # Statistical simulation (1000+ agents)

class AgentScalingManager:
    """
    Dynamically allocate cognitive resources.

    DEEP agents: Key NPCs near player, involved in active storylines
    MEDIUM agents: Secondary NPCs, shopkeepers, guards
    SIMPLE agents: Crowd NPCs, random tavern patrons
    BACKGROUND: City population (simulated statistically)
    """

    def __init__(self):
        self.deep_agents: List[DeepAgent] = []
        self.medium_agents: List[MediumAgent] = []
        self.simple_agents: List[SimpleAgent] = []

        # Budget: Max cognitive cycles per game tick
        self.cycle_budget = 10  # Can process 10 full cycles per tick

    def tick(self, game_state: Dict):
        """
        Each game tick:
        1. Promote/demote agents based on relevance
        2. Allocate cycles to most relevant agents
        3. Run cognitive cycles
        """

        # Determine relevance (distance to player, storyline involvement)
        relevance_scores = self._calculate_relevance(game_state)

        # Promote agents near player to DEEP tier
        self._rebalance_tiers(relevance_scores)

        # Run cycles with budget
        cycles_remaining = self.cycle_budget

        for agent in sorted(
            self.deep_agents,
            key=lambda a: relevance_scores.get(a.agent_id, 0),
            reverse=True
        ):
            if cycles_remaining <= 0:
                break

            agent.cognitive_cycle(game_state)
            cycles_remaining -= 1

        # Medium agents: Run every N ticks
        # Simple agents: React only to direct triggers

    def _calculate_relevance(self, game_state: Dict) -> Dict[str, float]:
        """
        Relevance score based on:
        - Distance to player
        - Active in conversation with player
        - Involved in active quest
        - Recently observed by player
        - Dramatic state (urgent needs, high emotions)
        """
        scores = {}

        player_location = game_state.get('player_location')

        for agent in self.deep_agents:
            score = 0.0

            # Same location as player
            if agent.current_location == player_location:
                score += 1.0

            # In conversation
            if agent.agent_id in game_state.get('active_conversation', []):
                score += 2.0

            # Urgent internal state
            urgent_needs = agent.needs.get_urgent_needs()
            if urgent_needs:
                score += 0.5 * len(urgent_needs)

            # High emotion
            dominant_emotion = agent.emotions.get_dominant_emotion()
            if dominant_emotion:
                intensity = agent.emotions.emotions[dominant_emotion].intensity
                score += intensity

            scores[agent.agent_id] = score

        return scores
```

### Performance Optimization

**Techniques**:

1. **Lazy Evaluation**: Don't process agents player can't see
2. **Update Budgets**: Cap cognitive cycles per frame
3. **State Caching**: Cache expensive calculations (personality evaluations)
4. **Parallel Processing**: Run agent cycles in parallel (separate thread pool)
5. **Progressive Disclosure**: Load agent state progressively (personality → needs → memories as needed)

```python
# agents/performance.py

from concurrent.futures import ThreadPoolExecutor
import functools

class OptimizedAgentRunner:
    """Run agents with performance optimizations."""

    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    @functools.lru_cache(maxsize=128)
    def cached_personality_evaluation(self, agent_id: str, action: str):
        """Cache personality alignment checks."""
        # Expensive: Checking action against all values
        # Solution: Cache results for action types
        pass

    def parallel_cognitive_cycles(
        self, agents: List[DeepAgent], game_state: Dict
    ):
        """Run multiple agent cognitive cycles in parallel."""

        # Submit all cycles
        futures = [
            self.executor.submit(agent.cognitive_cycle, game_state)
            for agent in agents
        ]

        # Collect results
        actions = []
        for future in futures:
            try:
                action = future.result(timeout=0.1)  # 100ms timeout
                if action:
                    actions.append(action)
            except TimeoutError:
                # Agent took too long, skip this cycle
                continue

        return actions
```

---

## Emergent Culture & Evolution

### Cultural Artifacts System

**Vision**: Agents create culture that persists and evolves

```python
# agents/culture.py

@dataclass
class CulturalArtifact:
    """
    Something created by agents that becomes part of culture.

    Examples:
    - Lyra's song about Sarah → becomes famous ballad
    - Shared belief about tavern → becomes legend
    - Recurring event → becomes tradition
    """

    artifact_id: str
    type: str  # "song", "story", "tradition", "belief", "saying"
    content: str
    creator_id: str
    created_at: float

    # How widely known
    known_by: List[str] = field(default_factory=list)  # Agent IDs

    # How agents feel about it
    sentiment: Dict[str, float] = field(default_factory=dict)  # agent_id → -1 to 1

    # Variations (artifacts evolve through retelling)
    variations: List[str] = field(default_factory=list)

    def spread_to(self, agent_id: str, variation: Optional[str] = None):
        """Artifact spreads to new agent."""
        if agent_id not in self.known_by:
            self.known_by.append(agent_id)

        if variation and variation not in self.variations:
            self.variations.append(variation)


class CulturalEvolutionTracker:
    """
    Tracks emergence and evolution of culture.

    Culture emerges from:
    - Agents sharing stories (Lyra sings → others learn song)
    - Repeated behaviors becoming traditions
    - Shared beliefs forming worldview
    - Artifacts gaining symbolic meaning
    """

    def __init__(self):
        self.artifacts: Dict[str, CulturalArtifact] = {}
        self.traditions: List[Dict] = []
        self.shared_narratives: List[str] = []

    def agent_creates_artifact(
        self, agent: DeepAgent, artifact_type: str, content: str
    ) -> CulturalArtifact:
        """Agent creates new cultural artifact."""

        import hashlib
        artifact_id = hashlib.md5(
            f"{agent.agent_id}:{content}:{time.time()}".encode()
        ).hexdigest()[:16]

        artifact = CulturalArtifact(
            artifact_id=artifact_id,
            type=artifact_type,
            content=content,
            creator_id=agent.agent_id,
            created_at=time.time(),
            known_by=[agent.agent_id]
        )

        self.artifacts[artifact_id] = artifact
        return artifact

    def spread_artifact(
        self,
        artifact: CulturalArtifact,
        from_agent: DeepAgent,
        to_agent: DeepAgent,
        social_network: SocialNetwork
    ):
        """Artifact spreads through social network."""

        # Check relationship
        relationship = social_network.get_relationship(
            from_agent.agent_id, to_agent.agent_id
        )

        # More likely to spread between friends
        if not relationship or relationship.affinity < 0.2:
            return

        # Agent might modify artifact based on personality
        variation = None
        if to_agent.personality.openness > 0.7:
            # Creative agents add variations
            variation = f"{artifact.content} (as told by {to_agent.name})"

        artifact.spread_to(to_agent.agent_id, variation)

        # Record sentiment
        # How does to_agent feel about this artifact?
        sentiment = to_agent.personality.agreeableness * 0.5  # Base positivity
        artifact.sentiment[to_agent.agent_id] = sentiment

    def detect_traditions(
        self, agents: List[DeepAgent], min_participants: int = 3
    ) -> List[Dict]:
        """
        Detect emerging traditions.

        Tradition = repeated behavior by multiple agents
        """

        # Analyze agent goals and behaviors
        behavior_patterns = {}

        for agent in agents:
            for goal in agent.goals.goals.values():
                if goal.status == GoalStatus.ACHIEVED:
                    # This goal was achieved - what was the behavior?
                    behavior = goal.description
                    if behavior not in behavior_patterns:
                        behavior_patterns[behavior] = []
                    behavior_patterns[behavior].append(agent.agent_id)

        # Find patterns with multiple agents
        traditions = []
        for behavior, participants in behavior_patterns.items():
            if len(participants) >= min_participants:
                traditions.append({
                    'behavior': behavior,
                    'participants': participants,
                    'strength': len(participants) / len(agents),
                })

        return traditions

    def generate_shared_narrative(
        self, agents: List[DeepAgent]
    ) -> str:
        """
        Generate narrative about shared experiences.

        Combines agents' memories to create shared history.
        """

        # Find memories about same events
        memory_clusters = {}

        for agent in agents:
            for memory in agent.episodic_memory.memories:
                # Simple clustering by location and time
                key = f"{memory.location}:{int(memory.timestamp / 3600)}"  # Hour bucket

                if key not in memory_clusters:
                    memory_clusters[key] = []
                memory_clusters[key].append((agent.name, memory))

        # Find clusters with multiple agents (shared experiences)
        shared_events = [
            (key, memories)
            for key, memories in memory_clusters.items()
            if len(memories) > 1
        ]

        if not shared_events:
            return "No shared experiences yet."

        # Build narrative
        narrative_parts = ["Shared History of the Tavern:\n"]

        for key, memories in shared_events[:5]:  # Top 5 shared events
            location = key.split(':')[0]
            narrative_parts.append(f"\nAt {location}:")

            for agent_name, memory in memories:
                narrative_parts.append(
                    f"  - {agent_name} remembers: {memory.content}"
                )

        return "\n".join(narrative_parts)
```

### Emergent Storylines

**Vision**: Storylines emerge from agent interactions, not scripts

```python
# agents/storylines.py

class StorylineTracker:
    """
    Detect and track emergent storylines.

    A storyline emerges when:
    - Agents have conflicting goals
    - Relationships evolve dramatically
    - Cultural artifacts spread widely
    - Repeated interactions form patterns
    """

    def __init__(self):
        self.active_storylines: List[Dict] = []

    def detect_storylines(
        self,
        agents: List[DeepAgent],
        social_network: SocialNetwork,
        culture_tracker: CulturalEvolutionTracker
    ) -> List[Dict]:
        """Scan for emerging storylines."""

        storylines = []

        # 1. Conflict storyline: Agents with opposing goals
        storylines.extend(self._detect_conflicts(agents))

        # 2. Romance storyline: High affinity + growing intimacy
        storylines.extend(self._detect_romance(social_network))

        # 3. Redemption storyline: Agent changing values/beliefs
        storylines.extend(self._detect_redemption(agents))

        # 4. Mystery storyline: Agents seeking same information
        storylines.extend(self._detect_mysteries(agents))

        # 5. Cultural movement: Artifact spreading rapidly
        storylines.extend(self._detect_cultural_movements(culture_tracker))

        return storylines

    def _detect_conflicts(self, agents: List[DeepAgent]) -> List[Dict]:
        """Find agents with conflicting goals."""
        conflicts = []

        # Raven (steal) vs Aldric (arrest)
        raven = next((a for a in agents if a.agent_id == 'raven_thief'), None)
        aldric = next((a for a in agents if a.agent_id == 'aldric_guard'), None)

        if raven and aldric:
            # Check if Raven has active theft goal and Aldric has arrest goal
            raven_goals = [g for g in raven.goals.goals.values() if 'acquire' in g.description.lower()]
            aldric_goals = [g for g in aldric.goals.goals.values() if 'evidence' in g.description.lower() or 'thief' in g.description.lower()]

            if raven_goals and aldric_goals:
                conflicts.append({
                    'type': 'LAW_VS_SURVIVAL',
                    'participants': ['raven_thief', 'aldric_guard'],
                    'description': "The guard captain suspects the desperate thief",
                    'tension': 0.8,
                    'stakes': "Raven's freedom vs Aldric's duty"
                })

        return conflicts

    def _detect_redemption(self, agents: List[DeepAgent]) -> List[Dict]:
        """Detect agents whose values/beliefs are changing."""
        redemptions = []

        # Raven potentially seeking redemption
        raven = next((a for a in agents if a.agent_id == 'raven_thief'), None)

        if raven:
            # Check for goal about going straight
            redemption_goals = [
                g for g in raven.goals.goals.values()
                if 'honest' in g.description.lower() or 'different' in g.description.lower()
            ]

            if redemption_goals:
                redemptions.append({
                    'type': 'REDEMPTION',
                    'participant': 'raven_thief',
                    'description': "The thief questions her path",
                    'stage': 'contemplation',
                    'catalysts': "Watching Sarah's honesty, Gene's knowing looks"
                })

        return redemptions
```

---

## Implementation Phases

### Phase 1: Foundation Integration (Week 1-2)
- [ ] Connect agents to event bus
- [ ] Create `DeepAgentNPC` wrapper for backward compatibility
- [ ] Set up agent lifecycle management
- [ ] Implement save/load for agent states

### Phase 2: Social Dynamics (Week 3-4)
- [ ] Integrate `SocialDynamicsEngine` with game loop
- [ ] Implement conversation system with UI
- [ ] Build gossip propagation
- [ ] Create relationship visualization (for debugging)

### Phase 3: Economic Integration (Week 5-6)
- [ ] Connect agents to economy system
- [ ] Implement agent economic decision-making
- [ ] Build dynamic pricing based on agent needs
- [ ] Create emergent quests from agent goals

### Phase 4: Cultural Evolution (Week 7-8)
- [ ] Implement cultural artifact system
- [ ] Build tradition detection
- [ ] Create shared narrative generation
- [ ] Develop storyline tracking

### Phase 5: Scaling & Optimization (Week 9-10)
- [ ] Implement tiered agent system
- [ ] Build relevance-based resource allocation
- [ ] Optimize cognitive cycle performance
- [ ] Add parallel processing

### Phase 6: Polish & Content (Week 11-12)
- [ ] Create 10+ more deep agents
- [ ] Build agent creation tools for designers
- [ ] Implement observation/debug tools
- [ ] Create demo scenarios

---

## Demonstration Examples

### Example 1: The Theft Dilemma

**Setup**:
- Raven needs 10 gold urgently (survival goal)
- Sarah has 15 gold in visible purse
- Aldric is in the tavern (observing)
- Lyra is performing nearby

**Emergent Sequence**:
1. Raven's cognitive cycle: Urgent hunger need + theft skill → considers stealing from Sarah
2. Raven checks: Aldric present (risk +0.4), Sarah struggling (guilt +0.3)
3. Decision: Raven's personality (survival > fairness) → attempts theft
4. Aldric observes: Updates theory of mind (Raven = thief confirmed)
5. Sarah discovers: Triggers fear emotion, updates beliefs (tavern unsafe)
6. Lyra observes entire scene: Creates memory, later writes song about it
7. Social network updates: Aldric-Raven (trust -0.4), Sarah-Raven (affinity -0.6)
8. Aldric faces dilemma: Duty says arrest, but Raven was starving
9. Cultural impact: Lyra's song spreads, becomes "The Ballad of the Desperate Hand"

**Emergent Quest**: Player walks in during #4, must choose:
- Help Aldric arrest Raven (law reputation +)
- Help Raven escape (outlaw reputation +)
- Pay Sarah back and convince Aldric to show mercy (wisdom check)

Each choice has cascading effects on relationships and future storylines.

### Example 2: Sarah's Breaking Point

**Setup**:
- Sarah's needs: Achievement 0.1 (failing), Rest 0.2 (exhausted)
- Active goal: Make 30 gold this month (deadline approaching)
- Beliefs: "Hard work pays off" confidence dropping to 0.4
- Emotion: Anxiety 0.8, Despair 0.6

**Emergent Sequence**:
1. Sarah's cognitive cycle: All values predict failure
2. Conflict: Value(independence) vs Need(survival)
3. Decision point: Accept shady deal or maintain honor?
4. Personality.conscientiousness (0.8) + Value(fairness, 0.85) → refuses deal
5. But: Need(survival) triggers desperation emotion
6. Gene observes: Sarah on verge of breakdown
7. Gene's cognitive cycle: Goal(help discretely) + Relationship(respect Sarah) → offers loan with honor-preserving terms
8. Sarah faces choice: Accept help (violates independence) or refuse (might fail)
9. Lyra watches: Writes song about pride vs pragmatism
10. Cultural impact: Story spreads, becomes parable about merchant honor

**Player involvement**:
- Could offer quest that pays well
- Could buy from Sarah at premium
- Could introduce her to better supplier
- Or do nothing and watch storyline unfold

### Example 3: The Wanderer's Truth

**Setup**:
- Marcus's goal: "Discover why I was brought to this tavern"
- Marcus's memories: Fragmented, mentions "tower", "stars", "someone calling my name"
- Gene's hidden knowledge: Knows tavern is special
- Player: Asks Marcus about his past

**Emergent Sequence**:
1. Player question triggers Marcus's memory recall
2. Marcus searches episodic memories for relevant fragments
3. Describes tower memory with high emotional intensity
4. Gene observes: Updates theory of mind (Marcus is not what he seems)
5. Gene's belief: "Marcus was sent here for a reason" (confidence 0.7)
6. Lyra overhears: Creates song "The Wanderer's Lament"
7. Song triggers Marcus's emotion: Hope + Anticipation spike
8. Marcus's cognitive cycle: Song felt significant → new goal "Talk to Lyra about the song"
9. Conversation between Marcus and Lyra (high depth, intimacy)
10. Shared understanding: Both feel tavern is supernatural
11. Cultural artifact: "The Tavern Exists Between" belief spreads

**Storyline Emerges**: The Cosmic Mystery
- Multiple agents developing belief about tavern's true nature
- Marcus + Lyra alliance forms (seeking truth together)
- Gene watches, says nothing, but knows
- Player can investigate or dismiss as superstition

---

## Future Enhancements

### 1. LLM Integration for Dialogue

**Vision**: Agent internal state → LLM prompt → natural dialogue

```python
def generate_dialogue_with_llm(agent: DeepAgent, context: str) -> str:
    """Use LLM with agent state as context."""

    # Build rich context from agent state
    state = agent.get_internal_state_summary()

    prompt = f"""
    You are {agent.name}, an NPC in a tavern. Generate a single line of dialogue.

    YOUR PERSONALITY:
    - Openness: {agent.personality.openness:.0%}
    - Conscientiousness: {agent.personality.conscientiousness:.0%}
    - Extraversion: {agent.personality.extraversion:.0%}
    - Agreeableness: {agent.personality.agreeableness:.0%}
    - Neuroticism: {agent.personality.neuroticism:.0%}

    YOUR VALUES (what matters most):
    {chr(10).join(f"- {v.name}: {v.strength:.0%}" for v in agent.personality.values)}

    YOUR CURRENT STATE:
    - Feeling: {state['emotional_state']['mood']}
    - Dominant Emotion: {state['emotional_state']['dominant_emotion']}
    - Urgent Needs: {', '.join(state['urgent_needs']) if state['urgent_needs'] else 'None'}
    - Active Goal: {state['active_goal']}

    RECENT MEMORIES:
    {chr(10).join(m.content for m in agent.episodic_memory.recall_recent(hours=24, limit=3))}

    CONTEXT: {context}

    Respond as {agent.name} would, given their personality, current state, and memories.
    Keep it brief (1-2 sentences).
    """

    # Call LLM
    response = llm_client.generate(prompt, max_tokens=100)
    return response
```

### 2. Long-Term Memory Consolidation

**Vision**: Agents "sleep" and consolidate memories like humans

```python
def consolidate_memories(agent: DeepAgent):
    """
    During sleep/downtime:
    - Move important episodic → semantic
    - Strengthen frequently accessed memories
    - Fade unimportant memories
    - Update beliefs based on patterns
    """

    # Find patterns in episodic memories
    recent_memories = agent.episodic_memory.recall_recent(hours=168)  # Week

    # Cluster similar memories
    theft_memories = [m for m in recent_memories if 'steal' in m.content.lower()]

    if len(theft_memories) >= 3:
        # Pattern detected → update semantic memory
        agent.semantic_memory.add_knowledge(
            "crime_pattern",
            "There's been increased theft in the tavern lately",
            confidence=0.8
        )

        # Update beliefs
        agent.beliefs.add_belief(
            BeliefType.FACT,
            "tavern",
            "The tavern is becoming less safe",
            confidence=0.7,
            evidence="Multiple theft incidents witnessed"
        )
```

### 3. Genetic Personality Inheritance

**Vision**: Agent children inherit personality traits (for long-term simulation)

```python
def create_child_agent(parent_a: DeepAgent, parent_b: DeepAgent) -> DeepAgent:
    """Create child agent with inherited traits."""

    child_personality = Personality(
        openness=(parent_a.personality.openness + parent_b.personality.openness) / 2 + random.gauss(0, 0.1),
        conscientiousness=(parent_a.personality.conscientiousness + parent_b.personality.conscientiousness) / 2 + random.gauss(0, 0.1),
        # ... etc
    )

    # Inherit some values
    child_values = []
    for value in parent_a.personality.values[:2]:  # Top 2 values from each parent
        child_values.append(Value(value.name, value.strength * 0.8, value.description))

    # Child starts with some parents' semantic knowledge
    child_semantic = SemanticMemory()
    for knowledge in parent_a.semantic_memory.knowledge_base.values():
        if knowledge.confidence > 0.8:
            child_semantic.add_knowledge(
                knowledge.category,
                f"Learned from parent: {knowledge.content}",
                confidence=knowledge.confidence * 0.6  # Weaker than parent
            )
```

### 4. Group Dynamics & Factions

**Vision**: Agents form factions with shared goals

```python
class Faction:
    """Group of agents with shared goals."""

    def __init__(self, name: str, founding_members: List[str]):
        self.name = name
        self.members = founding_members
        self.shared_goals: List[Goal] = []
        self.reputation: Dict[str, float] = {}  # How others view the faction

    def recruit(self, agent: DeepAgent, faction_goal: Goal) -> bool:
        """Try to recruit agent to faction."""

        # Check alignment with faction goals
        alignment = 0.0
        for f_goal in self.shared_goals:
            for a_goal in agent.goals.goals.values():
                if self._goals_align(f_goal, a_goal):
                    alignment += 0.3

        # Check relationships with members
        avg_affinity = sum(
            relationship.affinity
            for relationship in relationships_with_members
        ) / len(relationships_with_members)

        if alignment > 0.5 and avg_affinity > 0.3:
            self.members.append(agent.agent_id)
            agent.goals.add_goal(
                description=faction_goal.description,
                goal_type=faction_goal.goal_type,
                priority=0.7,  # Faction goals high priority
                motivated_by=["affiliation", "purpose"]
            )
            return True

        return False
```

---

## Metrics & Success Criteria

### Emergent Behavior Metrics

Track these to measure emergent simulation quality:

1. **Unpredictability**: % of agent actions that weren't scripted
   - Target: >90%

2. **Consistency**: Agents act according to personality/values
   - Measure: Correlation between actions and personality traits
   - Target: >0.8

3. **Relationship Complexity**: Average relationships per agent
   - Target: >5 meaningful relationships

4. **Cultural Artifacts**: New artifacts created per hour
   - Target: >2

5. **Emergent Storylines**: Detected storylines without designer input
   - Target: >3 active storylines at any time

6. **Player Impact**: % of agent state changes due to player actions
   - Target: 30-40% (rest is agent-agent interaction)

7. **Memory Utilization**: % of decisions influenced by memories
   - Target: >60%

8. **Emotional Variance**: Range of emotions experienced per agent per session
   - Target: >5 different emotions

---

## Conclusion

This integration plan transforms Taverna from a game with NPCs into a **living simulation** where:

- **Individual agents** have rich inner lives (needs, emotions, memories, goals)
- **Social dynamics** emerge from agent interactions (relationships, gossip, alliances)
- **Culture evolves** through shared artifacts and traditions
- **Storylines emerge** from agent conflicts and collaborations
- **The player** affects and is affected by this living ecosystem

The system scales from 6 deep agents to hundreds through tiered simulation, maintains performance through optimization, and creates unprecedented emergent gameplay.

**This is not a game with NPCs. This is a society simulator where you happen to be a member.**

Welcome to the future of RPG simulation.
