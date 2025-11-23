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

from .personality import Personality, PersonalityTrait, Value
from .needs import Need, PhysiologicalNeeds, Drive
from .emotions import Emotion, EmotionalState, Mood
from .beliefs import Belief, BeliefSystem
from .memory import Memory, EpisodicMemory, SemanticMemory
from .goals import Goal, GoalHierarchy, Plan, Action
from .agent import DeepAgent
from .sarah import SarahTheMerchant

__all__ = [
    "Personality",
    "PersonalityTrait",
    "Value",
    "Need",
    "PhysiologicalNeeds",
    "Drive",
    "Emotion",
    "EmotionalState",
    "Mood",
    "Belief",
    "BeliefSystem",
    "Memory",
    "EpisodicMemory",
    "SemanticMemory",
    "Goal",
    "GoalHierarchy",
    "Plan",
    "Action",
    "DeepAgent",
    "SarahTheMerchant",
]
