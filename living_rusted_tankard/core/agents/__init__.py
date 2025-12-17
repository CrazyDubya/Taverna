"""
Deep Agent Architecture for The Living Rusted Tankard.

This module implements truly autonomous agents with:
- BDI (Belief-Desire-Intention) architecture
- Psychological simulation (needs, emotions, personality)
- Cognitive modeling (memory, beliefs, theory of mind)
- Emergent behavior from internal states

Design Philosophy:
- Behavior emerges from internal state, not scripts
- Agents have reasons for their actions
- Learning and adaptation through experience
- Interpretable decision-making for debugging
"""

from .personality import Personality, PersonalityTrait, Value, create_personality_archetype
from .needs import Need, PhysiologicalNeeds, Drive, NeedType, create_standard_drives
from .emotions import Emotion, EmotionalState, Mood, EmotionType
from .beliefs import Belief, BeliefSystem, BeliefType, TheoryOfMind
from .memory import Memory, EpisodicMemory, SemanticMemory
from .goals import Goal, GoalHierarchy, Plan, Action, GoalType, GoalStatus
from .agent import DeepAgent
from .observer import AgentObserver, DecisionTrace

# Agent creators
from .sarah import create_sarah, get_sarah_narrative_description
from .gene import create_gene, get_gene_narrative_description
from .marcus import create_marcus, get_marcus_narrative_description
from .raven import create_raven, get_raven_narrative_description
from .aldric import create_aldric, get_aldric_narrative_description
from .lyra import create_lyra, get_lyra_narrative_description

__all__ = [
    # Core systems
    "Personality",
    "PersonalityTrait",
    "Value",
    "create_personality_archetype",
    "Need",
    "NeedType",
    "PhysiologicalNeeds",
    "Drive",
    "create_standard_drives",
    "Emotion",
    "EmotionType",
    "EmotionalState",
    "Mood",
    "Belief",
    "BeliefType",
    "BeliefSystem",
    "TheoryOfMind",
    "Memory",
    "EpisodicMemory",
    "SemanticMemory",
    "Goal",
    "GoalType",
    "GoalStatus",
    "GoalHierarchy",
    "Plan",
    "Action",
    "DeepAgent",
    "AgentObserver",
    "DecisionTrace",
    # Agent creators
    "create_sarah",
    "get_sarah_narrative_description",
    "create_gene",
    "get_gene_narrative_description",
    "create_marcus",
    "get_marcus_narrative_description",
    "create_raven",
    "get_raven_narrative_description",
    "create_aldric",
    "get_aldric_narrative_description",
    "create_lyra",
    "get_lyra_narrative_description",
]
