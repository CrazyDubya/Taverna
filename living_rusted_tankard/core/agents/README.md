#Deep Agent Architecture for The Living Rusted Tankard

**Status:** Complete foundational implementation
**Created:** 2025-11-23
**Purpose:** True autonomous agents with emergent behavior

---

## What This Is

This is a complete **BDI (Belief-Desire-Intention) architecture** for creating truly autonomous agents that exhibit emergent, believable behavior. Not scripted NPCs, not chatbots, but agents with:

- Internal mental states that drive behavior
- Emotions that color decision-making
- Memories that shape beliefs
- Goals that emerge from needs
- Plans that adapt to circumstances

**This is what "alive" looks like in code.**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    DEEP AGENT                           │
│                                                         │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐│
│  │ PERSONALITY  │  │ NEEDS/DRIVES  │  │  EMOTIONS    ││
│  │  - Big 5     │  │ - Physiological│ │ - Plutchik   ││
│  │  - Values    │  │ - Psychological│ │ - Mood       ││
│  └──────┬───────┘  └───────┬───────┘  └──────┬───────┘│
│         │                  │                  │        │
│         └──────────────────┼──────────────────┘        │
│                            │                           │
│                 ┌──────────▼──────────┐                │
│                 │  COGNITIVE CYCLE    │                │
│                 │  1. Perceive        │                │
│                 │  2. Update Beliefs  │                │
│                 │  3. Evaluate Needs  │                │
│                 │  4. Form/Select Goal│                │
│                 │  5. Plan/Execute    │                │
│                 │  6. Learn           │                │
│                 └──────────┬──────────┘                │
│                            │                           │
│         ┌──────────────────┼──────────────────┐        │
│         │                  │                  │        │
│  ┌──────▼───────┐  ┌───────▼───────┐  ┌──────▼──────┐ │
│  │   BELIEFS    │  │    MEMORY     │  │    GOALS    │ │
│  │ - About World│  │ - Episodic    │  │ - Hierarchy │ │
│  │ - Theory Mind│  │ - Semantic    │  │ - Plans     │ │
│  └──────────────┘  └───────────────┘  └─────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Core Systems

### 1. Personality (`personality.py`)
**What:** Stable traits that shape how agents think and feel
**Based on:** Big Five (OCEAN) + core values
**Influences:** Emotional responses, decision biases, social behavior

```python
personality = Personality(
    openness=0.8,          # Curious, creative
    conscientiousness=0.7,  # Organized, responsible
    extraversion=0.5,       # Moderate sociability
    agreeableness=0.6,      # Cooperative
    neuroticism=0.4,        # Emotionally stable
    values=[
        Value("independence", 0.9),
        Value("fairness", 0.8),
    ]
)
```

**Key Insight:** Personality creates *consistency* - Sarah always values independence, which creates internal conflict when she needs help.

---

### 2. Needs & Drives (`needs.py`)
**What:** Physiological and psychological needs that motivate behavior
**Based on:** Maslow's hierarchy + Self-Determination Theory
**Creates:** The "pressure" that forms goals

```python
# Hunger decreases over time
needs.needs[NeedType.HUNGER].level = 0.3  # Getting hungry
needs.update(hours_passed=2.0)  # Even hungrier

# This urgency creates goals
if needs.needs[NeedType.HUNGER].is_urgent():
    # Agent will form goal: "Find food"
```

**Key Insight:** Needs create *motivation* - when Sarah's achievement need is unfulfilled, she becomes driven to prove herself.

---

### 3. Emotions (`emotions.py`)
**What:** Moment-to-moment emotional states with intensity and decay
**Based on:** Plutchik's wheel + OCC appraisal theory
**Influences:** Risk tolerance, social behavior, perception

```python
# Event happens
emotions.appraise_event(
    event_description="Supplier raised prices",
    event_outcome="negative",
    unexpectedness=0.3,
    personal_relevance=0.9
)

# Triggers: Sadness + Anger
# These emotions:
# - Decrease friendliness
# - Increase risk-seeking (anger)
# - Color perception of future events
```

**Key Insight:** Emotions create *color* - Sarah's anxiety makes her see threats everywhere, affecting her decisions.

---

### 4. Beliefs (`beliefs.py`)
**What:** What the agent thinks is true about the world
**Includes:** Facts, probabilities, and theory of mind about other agents
**Updates:** Based on evidence, with confidence levels

```python
# Sarah believes:
beliefs.add_belief(
    BeliefType.FACT,
    subject="suppliers",
    content="Suppliers are raising prices unfairly",
    confidence=0.9,
    evidence="Seen it happen repeatedly"
)

# Theory of mind about Gene:
gene_theory = beliefs.get_theory_of_mind("gene_bartender")
gene_theory.update_perceived_trait("trustworthy", 0.6)
gene_theory.predict_behavior("If I ask for help...")
```

**Key Insight:** Beliefs enable *social reasoning* - Sarah models what Gene might think/do, enabling strategic social interaction.

---

### 5. Memory (`memory.py`)
**What:** Episodic (experiences) and semantic (knowledge) memory
**Features:** Emotional tagging, importance-based retention, accessibility decay
**Enables:** Learning from experience, context-aware recall

```python
# Traumatic memory
memory.add_memory(
    content="Supplier laughed when I couldn't pay",
    emotional_valence=-0.8,
    emotional_intensity=0.9,
    importance=0.95,
    participants=["supplier"]
)

# Later, this memory is recalled when considering asking for help
# It makes Sarah hesitant, expecting rejection
```

**Key Insight:** Memory creates *history* - Sarah's past shapes her present, making her reluctant to be vulnerable.

---

### 6. Goals & Planning (`goals.py`)
**What:** Desired states (goals) and sequences of actions (plans) to achieve them
**BDI:** Desires (goals) → Deliberation → Intentions (plans)
**Features:** Priority, deadlines, subgoals, progress tracking

```python
# Goal emerges from need
goal = goals.add_goal(
    description="Make 30 gold this month",
    goal_type=GoalType.SURVIVAL,
    priority=1.0,
    deadline=30_days_from_now,
    motivated_by=["survival", "achievement"]
)

# Plan generated
plan = Plan(actions=[
    Action(command="jobs", description="Check available work"),
    Action(command="work clean_tables", description="Work for gold"),
])
```

**Key Insight:** Goals create *direction* - Sarah's behavior is purposeful, not random. We can see WHY she does things.

---

### 7. The Agent (`agent.py`)
**What:** Integrates all systems into cognitive cycle
**Cycle:** Perceive → Believe → Desire → Intend → Act → Learn
**Emergent:** Behavior arises from system interactions

```python
action = agent.cognitive_cycle(game_state)

# Internally:
# 1. Updates needs (gets hungrier, more tired)
# 2. Updates emotions (anxiety builds)
# 3. Perceives environment (sees Gene, player)
# 4. Updates beliefs (adds to theory of mind)
# 5. Evaluates needs → forms goals
# 6. Selects most urgent goal
# 7. Forms/executes plan
# 8. Returns next action

# The beauty: NO IF-THEN SCRIPTS
# Behavior emerges from internal state
```

**Key Insight:** The cognitive cycle creates *emergence* - complex, believable behavior from simple rules.

---

## Sarah the Merchant (`sarah.py`)

Sarah is our **proof of concept** - the first fully realized deep agent.

### Her Situation
- Struggling merchant with mounting debt
- Exhausted from overwork
- Ashamed to ask for help despite desperation
- Values independence fiercely

### Why She's Interesting

**Internal Conflict:**
- Drive for autonomy vs. need for help
- Value of fairness vs. desperation
- Pride vs. survival

**Emergent Behaviors:**
- Hesitant in social interactions (learned from painful memories)
- Overworks herself (trying to solve problems alone)
- Anxious decision-making (elevated neuroticism)
- Might eventually ask for help (if anxiety >> pride)

**Observable:**
- Dark circles under eyes (low REST need)
- Clutches ledger book (ACHIEVEMENT need unfulfilled)
- Forces professional smile (RESPECT need)
- Weighs every word (fear of vulnerability)

### What Makes Her Alive

1. **She changes:** Stress builds, emotions shift, memories accumulate
2. **She has reasons:** Every action traces back to needs, beliefs, goals
3. **She's unpredictable:** Same situation, different internal state = different action
4. **She learns:** Outcomes update beliefs, shape future behavior
5. **She feels real:** Players will say "Sarah needs help" not "the Sarah NPC"

---

## Observer System (`observer.py`)

Tools for studying emergent behavior:

```python
observer = AgentObserver(sarah)

# Records every decision with full context
observer.record_decision(
    action_taken="ask gene for help",
    reasoning="Desperation > pride threshold"
)

# Analyzes patterns
patterns = observer.analyze_decision_patterns()
# {
#   "need_driven_ratio": 0.7,
#   "most_common_goal": "survive this month",
#   "success_rate": 0.65
# }

# Detects problems
loops = observer.detect_behavioral_loops()
# Alerts if agent is stuck repeating same actions

# Generates narrative
story = observer.generate_narrative_summary()
# "While feeling anxious, Sarah decided to..."
```

**Use cases:**
- Debugging: Why did Sarah do that?
- Balancing: Is this agent too stressed?
- Research: What patterns emerge?
- Storytelling: Generate agent autobiographies

---

## How To Use

### Creating a New Deep Agent

```python
from living_rusted_tankard.core.agents import DeepAgent, Personality, Value
from living_rusted_tankard.core.agents.needs import create_standard_drives

# 1. Define personality
personality = Personality(
    openness=0.7,
    conscientiousness=0.8,
    # ... other traits
    values=[
        Value("honor", 0.9),
        Value("loyalty", 0.8),
    ]
)

# 2. Create agent
agent = DeepAgent(
    name="Marcus",
    agent_id="marcus_wanderer",
    personality=personality,
    drives=create_standard_drives(),
)

# 3. Configure initial state
agent.emotions.trigger_emotion(EmotionType.HOPE, 0.6)
agent.beliefs.add_belief(
    BeliefType.FACT,
    subject="tavern",
    content="This place holds secrets",
    confidence=0.8
)

# 4. Add initial goals
agent.goals.add_goal(
    description="Uncover the tavern's mystery",
    goal_type=GoalType.EXPLORATION,
    priority=0.8
)

# 5. Run cognitive cycle
action = agent.cognitive_cycle(game_state)
```

### Integrating with Game Loop

```python
# Each game tick
for agent in deep_agents:
    # Agent decides what to do
    action = agent.cognitive_cycle(current_game_state)

    if action:
        # Execute in game world
        outcome = game_world.execute_action(action)

        # Agent learns from result
        agent.process_outcome(action, outcome, success=outcome["success"])
```

---

## Advantages Over Traditional NPCs

| Traditional NPC | Deep Agent |
|----------------|------------|
| IF player_reputation > 50 THEN friendly | Relationship emerges from interactions |
| Scripted dialogue trees | Dialogue driven by beliefs and goals |
| Fixed schedule | Schedule emerges from needs and goals |
| Random idle animations | Idle behavior reflects personality |
| No memory | Rich episodic memory |
| No learning | Updates beliefs from experience |
| Predictable | Surprising but consistent |
| Feels mechanical | Feels alive |

---

## Performance Considerations

**CPU Cost:**
- Cognitive cycle: ~1-5ms per agent per tick
- Memory update: ~0.1ms
- Emotion update: ~0.1ms
- Belief update: ~0.5ms
- Goal selection: ~1ms

**Recommendations:**
- 5-10 deep agents for major NPCs
- 20-50 medium agents for supporting cast
- 100+ simple agents for background

**Optimization:**
- Run deep agents at lower tick rate (every 5-10 game seconds)
- Cache plan execution (don't re-plan every tick)
- Lazy evaluation of distant agents

---

## Future Enhancements

### Near Term
- [ ] LLM integration for natural language dialogue
- [ ] HTN (Hierarchical Task Network) planning
- [ ] Social relationship dynamics (reputation, gossip, alliances)
- [ ] Learning from player interactions

### Medium Term
- [ ] Genetic evolution of personality traits
- [ ] Multi-agent coordination (teamwork, conflict)
- [ ] Cultural emergence (shared beliefs, norms)
- [ ] Emotional contagion between agents

### Long Term
- [ ] Theory of mind with uncertainty
- [ ] Metacognition (thinking about thinking)
- [ ] Value drift over time
- [ ] Moral reasoning frameworks

---

## Research Questions

This architecture enables studying:

1. **Emergence:** What complex behaviors arise from simple rules?
2. **Believability:** What makes an agent feel "alive"?
3. **Predictability:** Can we understand agent behavior by examining internal state?
4. **Social Dynamics:** How do agent relationships evolve?
5. **Player Impact:** How do player actions change agent psychology?

---

## Credits & Inspiration

**Theoretical Foundations:**
- BDI Architecture (Rao & Georgeff, 1995)
- Plutchik's Wheel of Emotions
- OCC Model of Emotions (Ortony, Clore, Collins)
- Big Five Personality Model
- Self-Determination Theory (Deci & Ryan)

**Game AI:**
- Goal-Oriented Action Planning (GOAP)
- Utility AI
- Behavior Trees
- The Sims (social AI)
- Dwarf Fortress (emergent narrative)

---

## License & Usage

Part of The Living Rusted Tankard project.

This architecture is designed for:
- Research into agent autonomy
- Narrative game development
- Social simulation
- AI behavior studies

Feel free to learn from, adapt, and extend this work.

---

## Contact & Contribution

This is a living system. As we observe Sarah and other agents, we'll discover:
- What works (keep and enhance)
- What doesn't (iterate and improve)
- What emerges (document and study)

**The goal:** Create agents so believable that players forget they're not human.

---

**"The question is not whether machines can think, but whether we can create systems so rich that thought emerges."**

This is our attempt to answer yes.
