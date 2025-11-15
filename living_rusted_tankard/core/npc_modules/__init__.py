"""
NPC (Non-Player Character) systems for The Living Rusted Tankard.

This module contains all NPC-related functionality including:
- Psychology and personality systems
- Behavioral rules and patterns
- Dialogue and conversation management
- Goals and autonomous agency
- Secrets and gossip networks
- Relationship management
- Scheduling and interactions

The NPC system provides rich, dynamic characters that feel alive and
respond naturally to player actions and world events.
"""

# Import NPC subsystems from npc_systems directory
try:
    from ..npc_systems.psychology import NPCPsychology, PersonalityTrait, EmotionalState, CognitiveBias
except ImportError:
    NPCPsychology = PersonalityTrait = EmotionalState = CognitiveBias = None

try:
    from ..npc_systems.behavioral_rules import BehaviorEngine, BehaviorRule, Condition, Action
except ImportError:
    BehaviorEngine = BehaviorRule = Condition = Action = None

try:
    from ..npc_systems.dialogue import DialogueGenerator, DialogueContext, DialogueOption, DialogueType
except ImportError:
    DialogueGenerator = DialogueContext = DialogueOption = DialogueType = None

try:
    from ..npc_systems.goals import Goal, GoalStep, NPCAgency, GoalGenerator
except ImportError:
    Goal = GoalStep = NPCAgency = GoalGenerator = None

try:
    from ..npc_systems.secrets import EnhancedSecret, Evidence, SecretConsequence, SecretProtection
except ImportError:
    EnhancedSecret = Evidence = SecretConsequence = SecretProtection = None

try:
    from ..npc_systems.gossip import GossipNetwork, Rumor, RumorType
except ImportError:
    GossipNetwork = Rumor = RumorType = None

try:
    from ..npc_systems.relationships import RelationshipWeb, Conflict, Alliance
except ImportError:
    RelationshipWeb = Conflict = Alliance = None

try:
    from ..npc_systems.schedules import NPCSchedule, ScheduleBlock, DayType
except ImportError:
    NPCSchedule = ScheduleBlock = DayType = None

try:
    from ..npc_systems.interactions import InteractionManager, NPCInteraction, InteractionType
except ImportError:
    InteractionManager = NPCInteraction = InteractionType = None

__all__ = [
    # Psychology system
    "NPCPsychology",
    "PersonalityTrait",
    "EmotionalState",
    "CognitiveBias",
    # Behavioral system
    "BehaviorEngine",
    "BehaviorRule",
    "Condition",
    "Action",
    # Dialogue system
    "DialogueGenerator",
    "DialogueContext",
    "DialogueOption",
    "DialogueType",
    # Goals and agency
    "Goal",
    "GoalStep",
    "NPCAgency",
    "GoalGenerator",
    # Secrets and evidence
    "EnhancedSecret",
    "Evidence",
    "SecretConsequence",
    "SecretProtection",
    # Gossip network
    "GossipNetwork",
    "Rumor",
    "RumorType",
    # Relationships
    "RelationshipWeb",
    "Conflict",
    "Alliance",
    # Scheduling
    "NPCSchedule",
    "ScheduleBlock",
    "DayType",
    # Interactions
    "InteractionManager",
    "NPCInteraction",
    "InteractionType",
]
