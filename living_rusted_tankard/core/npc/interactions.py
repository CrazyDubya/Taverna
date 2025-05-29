"""Inter-NPC autonomous interactions and conflict generation."""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import random

from .psychology import NPCPsychology, Personality, Mood
from .relationships import RelationshipWeb, RelationshipType, Conflict, ConflictType
from .dialogue import DialogueGenerator, DialogueContext, DialogueType
from .gossip import GossipNetwork
from .goals import Goal, GoalCategory, NPCAgency


class InteractionType(Enum):
    """Types of NPC-to-NPC interactions."""
    GREETING = "greeting"
    CONVERSATION = "conversation"
    ARGUMENT = "argument"
    NEGOTIATION = "negotiation"
    COOPERATION = "cooperation"
    COMPETITION = "competition"
    ROMANCE = "romance"
    INTIMIDATION = "intimidation"
    ASSISTANCE = "assistance"
    TRANSACTION = "transaction"


class InteractionOutcome(Enum):
    """Possible outcomes of interactions."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    INTERRUPTED = "interrupted"


@dataclass
class InteractionContext:
    """Context for an NPC interaction."""
    location: str
    time_of_day: str
    witnesses: List[str] = field(default_factory=list)
    
    # Environmental factors
    crowded: bool = False
    private: bool = False
    atmosphere_tension: float = 0.5
    
    # Interaction history
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    
    # Current states
    initiator_goal: Optional[str] = None
    responder_goal: Optional[str] = None
    
    # Modifiers
    alcohol_involved: bool = False
    authority_present: bool = False


@dataclass
class NPCInteraction:
    """Record of an interaction between NPCs."""
    id: str
    timestamp: datetime
    initiator: str
    responder: str
    type: InteractionType
    context: InteractionContext
    
    # Interaction flow
    duration: float = 0.0  # minutes
    turns: List[Dict[str, Any]] = field(default_factory=list)
    
    # Outcome
    outcome: InteractionOutcome = InteractionOutcome.NEUTRAL
    relationship_changes: Dict[str, float] = field(default_factory=dict)
    
    # Side effects
    goals_affected: List[Tuple[str, str]] = field(default_factory=list)  # (npc_id, goal_id)
    rumors_created: List[str] = field(default_factory=list)
    conflicts_triggered: List[str] = field(default_factory=list)
    
    # Witnesses reactions
    witness_reactions: Dict[str, str] = field(default_factory=dict)
    
    def add_turn(self, speaker: str, action: str, 
                 dialogue: Optional[str] = None) -> None:
        """Add a turn to the interaction."""
        turn = {
            "speaker": speaker,
            "action": action,
            "dialogue": dialogue,
            "timestamp": datetime.now()
        }
        self.turns.append(turn)
        
    def calculate_duration(self) -> float:
        """Calculate interaction duration from turns."""
        if len(self.turns) >= 2:
            first = self.turns[0]["timestamp"]
            last = self.turns[-1]["timestamp"]
            self.duration = (last - first).total_seconds() / 60.0
        return self.duration


class InteractionManager:
    """Manages autonomous NPC-to-NPC interactions."""
    
    def __init__(self, relationship_web: RelationshipWeb,
                 gossip_network: GossipNetwork):
        self.relationship_web = relationship_web
        self.gossip_network = gossip_network
        self.dialogue_generator = DialogueGenerator()
        
        # Interaction history
        self.interactions: List[NPCInteraction] = []
        self.pending_interactions: List[Tuple[str, str, str]] = []  # (initiator, responder, reason)
        
        # Interaction tendencies
        self.interaction_frequency: Dict[str, float] = {}  # How often NPC initiates
        self.interaction_preferences: Dict[str, List[InteractionType]] = {}
        
    def check_interaction_opportunity(self, npc1: str, npc2: str,
                                    context: InteractionContext) -> Optional[InteractionType]:
        """Check if NPCs should interact."""
        # Get relationship
        relationship = self.relationship_web.get_relationship(npc1, npc2)
        if not relationship:
            # Strangers might still interact
            return InteractionType.GREETING if random.random() < 0.3 else None
        
        # Check last interaction time
        if context.last_interaction:
            time_since = datetime.now() - context.last_interaction
            if time_since < timedelta(minutes=30):
                return None  # Too soon
        
        # Determine interaction type based on relationship
        disposition = relationship.get_overall_disposition()
        
        if disposition > 0.7:
            # Positive relationship
            options = [InteractionType.CONVERSATION, InteractionType.COOPERATION]
            if relationship.romance:
                options.append(InteractionType.ROMANCE)
        elif disposition < 0.3:
            # Negative relationship
            options = [InteractionType.ARGUMENT, InteractionType.INTIMIDATION]
            if relationship.rivalry:
                options.append(InteractionType.COMPETITION)
        else:
            # Neutral
            options = [InteractionType.GREETING, InteractionType.CONVERSATION,
                      InteractionType.TRANSACTION]
        
        # Consider goals
        if context.initiator_goal:
            if "information" in context.initiator_goal:
                options.append(InteractionType.CONVERSATION)
            elif "intimidate" in context.initiator_goal:
                options.append(InteractionType.INTIMIDATION)
            elif "cooperate" in context.initiator_goal:
                options.append(InteractionType.COOPERATION)
        
        # Random selection with preference
        if options:
            preferences = self.interaction_preferences.get(npc1, [])
            preferred = [opt for opt in options if opt in preferences]
            if preferred:
                return random.choice(preferred)
            return random.choice(options)
        
        return None
    
    def initiate_interaction(self, initiator: str, responder: str,
                           initiator_psych: NPCPsychology,
                           responder_psych: NPCPsychology,
                           interaction_type: InteractionType,
                           context: InteractionContext) -> NPCInteraction:
        """Start an interaction between NPCs."""
        interaction = NPCInteraction(
            id=f"interaction_{datetime.now().timestamp()}_{initiator}_{responder}",
            timestamp=datetime.now(),
            initiator=initiator,
            responder=responder,
            type=interaction_type,
            context=context
        )
        
        # Generate opening
        opening = self._generate_opening(
            initiator, responder, 
            initiator_psych, interaction_type, context
        )
        interaction.add_turn(initiator, "speak", opening)
        
        # Get response
        response = self._generate_response(
            responder, initiator,
            responder_psych, opening, interaction_type, context
        )
        interaction.add_turn(responder, "respond", response)
        
        # Continue interaction
        self._continue_interaction(
            interaction, initiator_psych, responder_psych
        )
        
        # Determine outcome
        interaction.outcome = self._determine_outcome(interaction)
        
        # Apply effects
        self._apply_interaction_effects(interaction)
        
        # Record interaction
        self.interactions.append(interaction)
        
        return interaction
    
    def _generate_opening(self, initiator: str, responder: str,
                         psychology: NPCPsychology,
                         interaction_type: InteractionType,
                         context: InteractionContext) -> str:
        """Generate opening line for interaction."""
        # Map interaction types to dialogue types
        dialogue_type_map = {
            InteractionType.GREETING: DialogueType.GREETING,
            InteractionType.CONVERSATION: DialogueType.SMALL_TALK,
            InteractionType.ARGUMENT: DialogueType.THREATENING,
            InteractionType.ROMANCE: DialogueType.ROMANTIC,
            InteractionType.INTIMIDATION: DialogueType.THREATENING,
            InteractionType.NEGOTIATION: DialogueType.BUSINESS
        }
        
        dialogue_type = dialogue_type_map.get(interaction_type, DialogueType.SMALL_TALK)
        
        # Create dialogue context
        relationship = self.relationship_web.get_relationship(initiator, responder)
        rel_strength = relationship.get_overall_disposition() if relationship else 0.5
        
        dialogue_context = DialogueContext(
            speaker_id=initiator,
            listener_id=responder,
            location=context.location,
            time_of_day=context.time_of_day,
            relationship_type=RelationshipType.ACQUAINTANCE,  # Simplified
            relationship_strength=rel_strength
        )
        
        # Generate options
        options = self.dialogue_generator.generate_dialogue_options(
            dialogue_context, psychology, num_options=1
        )
        
        if options:
            return options[0].text
        
        # Fallback
        return f"*{initiator} approaches {responder}*"
    
    def _generate_response(self, responder: str, initiator: str,
                          psychology: NPCPsychology,
                          opening: str,
                          interaction_type: InteractionType,
                          context: InteractionContext) -> str:
        """Generate response to interaction."""
        # Determine response based on mood and relationship
        relationship = self.relationship_web.get_relationship(responder, initiator)
        
        if interaction_type == InteractionType.GREETING:
            if relationship and relationship.get_overall_disposition() > 0.5:
                return "Good to see you too!"
            else:
                return "*nods*"
        
        elif interaction_type == InteractionType.ARGUMENT:
            if psychology.base_personality == Personality.AGGRESSIVE:
                return "You want to take this outside?"
            elif psychology.base_personality == Personality.SHY:
                return "I... I don't want any trouble."
            else:
                return "Let's not do this here."
        
        elif interaction_type == InteractionType.ROMANCE:
            if relationship and relationship.romance:
                return "I've been thinking about you too..."
            else:
                return "I'm flattered, but..."
        
        # Default
        return "I see what you mean."
    
    def _continue_interaction(self, interaction: NPCInteraction,
                            initiator_psych: NPCPsychology,
                            responder_psych: NPCPsychology) -> None:
        """Continue interaction with additional turns."""
        # Determine number of turns based on interaction type
        turn_counts = {
            InteractionType.GREETING: 1,
            InteractionType.CONVERSATION: random.randint(3, 8),
            InteractionType.ARGUMENT: random.randint(2, 5),
            InteractionType.NEGOTIATION: random.randint(4, 10),
            InteractionType.ROMANCE: random.randint(2, 6)
        }
        
        target_turns = turn_counts.get(interaction.type, 3)
        current_speaker = interaction.responder
        
        while len(interaction.turns) < target_turns * 2:
            # Alternate speakers
            if current_speaker == interaction.initiator:
                current_speaker = interaction.responder
                psychology = responder_psych
            else:
                current_speaker = interaction.initiator
                psychology = initiator_psych
            
            # Generate next turn
            if interaction.type == InteractionType.CONVERSATION:
                # Share gossip occasionally
                if random.random() < 0.3:
                    known_rumors = self.gossip_network.get_npc_known_rumors(current_speaker)
                    if known_rumors:
                        rumor = random.choice(known_rumors)
                        interaction.add_turn(
                            current_speaker, "gossip", 
                            f"Did you hear? {rumor['content']}"
                        )
                        continue
            
            # Default continuation
            action = "speak" if random.random() < 0.8 else "gesture"
            interaction.add_turn(current_speaker, action, "...")
            
            # Check for escalation or resolution
            if self._check_escalation(interaction, psychology):
                interaction.outcome = InteractionOutcome.ESCALATED
                break
            
            if self._check_resolution(interaction):
                interaction.outcome = InteractionOutcome.RESOLVED
                break
    
    def _check_escalation(self, interaction: NPCInteraction,
                         current_speaker_psych: NPCPsychology) -> bool:
        """Check if interaction should escalate."""
        if interaction.type == InteractionType.ARGUMENT:
            # Arguments can escalate to conflicts
            if current_speaker_psych.current_mood == Mood.ANGRY:
                return random.random() < 0.5
            if len(interaction.turns) > 6:
                return random.random() < 0.3
        
        return False
    
    def _check_resolution(self, interaction: NPCInteraction) -> bool:
        """Check if interaction should resolve positively."""
        if interaction.type == InteractionType.NEGOTIATION:
            # Negotiations might succeed
            if len(interaction.turns) > 8:
                return random.random() < 0.6
        
        return False
    
    def _determine_outcome(self, interaction: NPCInteraction) -> InteractionOutcome:
        """Determine final outcome of interaction."""
        if interaction.outcome in [InteractionOutcome.ESCALATED, 
                                  InteractionOutcome.RESOLVED]:
            return interaction.outcome
        
        # Analyze turns for tone
        positive_turns = sum(1 for turn in interaction.turns 
                           if "friendly" in str(turn.get("action", "")))
        negative_turns = sum(1 for turn in interaction.turns
                           if "hostile" in str(turn.get("action", "")))
        
        total_turns = len(interaction.turns)
        
        if positive_turns > total_turns * 0.6:
            return InteractionOutcome.POSITIVE
        elif negative_turns > total_turns * 0.5:
            return InteractionOutcome.NEGATIVE
        else:
            return InteractionOutcome.NEUTRAL
    
    def _apply_interaction_effects(self, interaction: NPCInteraction) -> None:
        """Apply effects of interaction."""
        # Get relationship
        relationship = self.relationship_web.get_relationship(
            interaction.initiator, interaction.responder
        )
        
        if not relationship:
            # Create new relationship
            relationship = self.relationship_web.create_relationship(
                interaction.initiator, interaction.responder,
                RelationshipType.ACQUAINTANCE
            )
        
        # Apply relationship changes based on outcome
        if interaction.outcome == InteractionOutcome.POSITIVE:
            change = 0.1
            if interaction.type == InteractionType.COOPERATION:
                change = 0.2
            elif interaction.type == InteractionType.ROMANCE:
                change = 0.15
        elif interaction.outcome == InteractionOutcome.NEGATIVE:
            change = -0.15
            if interaction.type == InteractionType.ARGUMENT:
                change = -0.2
        elif interaction.outcome == InteractionOutcome.ESCALATED:
            change = -0.3
            # Create conflict
            conflict = self._create_conflict_from_interaction(interaction)
            if conflict:
                interaction.conflicts_triggered.append(conflict.id)
        else:
            change = 0.05 if interaction.type == InteractionType.CONVERSATION else 0.0
        
        if change != 0:
            relationship.modify_relationship(
                trust_delta=change * 0.5,
                affection_delta=change * 0.7,
                respect_delta=change * 0.3
            )
            interaction.relationship_changes["overall"] = change
        
        # Record interaction in relationship
        relationship.record_interaction(
            positive=interaction.outcome in [InteractionOutcome.POSITIVE, 
                                          InteractionOutcome.RESOLVED]
        )
        
        # Create rumors if witnessed
        if interaction.context.witnesses and not interaction.context.private:
            self._create_rumors_from_interaction(interaction)
        
        # Update last interaction time
        interaction.context.last_interaction = datetime.now()
    
    def _create_conflict_from_interaction(self, interaction: NPCInteraction) -> Optional[Conflict]:
        """Create a conflict from an escalated interaction."""
        if interaction.type == InteractionType.ARGUMENT:
            conflict_type = ConflictType.PERSONAL
            description = f"Heated argument between {interaction.initiator} and {interaction.responder}"
        elif interaction.type == InteractionType.COMPETITION:
            conflict_type = ConflictType.COMPETITION
            description = f"Rivalry between {interaction.initiator} and {interaction.responder}"
        else:
            return None
        
        conflict = self.relationship_web.create_conflict(
            conflict_type,
            [interaction.initiator, interaction.responder],
            description,
            f"Escalated from {interaction.type.value}",
            intensity=0.6
        )
        
        return conflict
    
    def _create_rumors_from_interaction(self, interaction: NPCInteraction) -> None:
        """Create rumors based on witnessed interaction."""
        for witness in interaction.context.witnesses:
            # Determine what they saw
            if interaction.type == InteractionType.ARGUMENT:
                description = f"having a heated argument"
            elif interaction.type == InteractionType.ROMANCE:
                description = f"in a romantic moment"
            elif interaction.type == InteractionType.INTIMIDATION:
                description = f"threatening each other"
            else:
                continue  # Not interesting enough
            
            # Create rumor
            rumor = self.gossip_network.create_rumor_from_event(
                interaction.type.value,
                [interaction.initiator, interaction.responder],
                witness,
                description
            )
            
            interaction.rumors_created.append(rumor.id)
    
    def simulate_autonomous_interactions(self, npcs: Dict[str, NPCPsychology],
                                       agencies: Dict[str, NPCAgency],
                                       location: str,
                                       time_of_day: str) -> List[NPCInteraction]:
        """Simulate autonomous interactions between NPCs in a location."""
        interactions_created = []
        npc_list = list(npcs.keys())
        
        # Check each pair
        for i, npc1 in enumerate(npc_list):
            for npc2 in npc_list[i+1:]:
                # Check interaction probability
                base_prob = self.interaction_frequency.get(npc1, 0.3)
                
                # Modify by relationship
                relationship = self.relationship_web.get_relationship(npc1, npc2)
                if relationship:
                    if relationship.get_overall_disposition() > 0.7:
                        base_prob *= 1.5
                    elif relationship.get_overall_disposition() < 0.3:
                        base_prob *= 0.5
                
                if random.random() < base_prob:
                    # Create context
                    context = InteractionContext(
                        location=location,
                        time_of_day=time_of_day,
                        witnesses=[n for n in npc_list if n not in [npc1, npc2]][:3]
                    )
                    
                    # Add goals if available
                    if npc1 in agencies and agencies[npc1].goals:
                        context.initiator_goal = agencies[npc1].goals[0].name
                    if npc2 in agencies and agencies[npc2].goals:
                        context.responder_goal = agencies[npc2].goals[0].name
                    
                    # Check for interaction type
                    interaction_type = self.check_interaction_opportunity(
                        npc1, npc2, context
                    )
                    
                    if interaction_type:
                        # Initiate interaction
                        interaction = self.initiate_interaction(
                            npc1, npc2,
                            npcs[npc1], npcs[npc2],
                            interaction_type, context
                        )
                        
                        interactions_created.append(interaction)
                        
                        # Limit interactions per cycle
                        if len(interactions_created) >= 3:
                            return interactions_created
        
        return interactions_created
    
    def get_interaction_history(self, npc_id: str, 
                              limit: int = 10) -> List[NPCInteraction]:
        """Get recent interactions involving an NPC."""
        relevant = [
            i for i in self.interactions
            if i.initiator == npc_id or i.responder == npc_id
        ]
        
        # Sort by timestamp
        relevant.sort(key=lambda x: x.timestamp, reverse=True)
        
        return relevant[:limit]
    
    def analyze_social_dynamics(self) -> Dict[str, Any]:
        """Analyze overall social dynamics from interactions."""
        if not self.interactions:
            return {"status": "no_interactions"}
        
        # Count interaction types
        type_counts = {}
        for interaction in self.interactions:
            type_counts[interaction.type.value] = type_counts.get(
                interaction.type.value, 0
            ) + 1
        
        # Count outcomes
        outcome_counts = {}
        for interaction in self.interactions:
            outcome_counts[interaction.outcome.value] = outcome_counts.get(
                interaction.outcome.value, 0
            ) + 1
        
        # Find most interactive NPCs
        interaction_counts = {}
        for interaction in self.interactions:
            interaction_counts[interaction.initiator] = interaction_counts.get(
                interaction.initiator, 0
            ) + 1
            interaction_counts[interaction.responder] = interaction_counts.get(
                interaction.responder, 0
            ) + 0.5
        
        most_interactive = sorted(
            interaction_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Calculate social temperature
        positive_ratio = outcome_counts.get(InteractionOutcome.POSITIVE.value, 0) / len(self.interactions)
        negative_ratio = outcome_counts.get(InteractionOutcome.NEGATIVE.value, 0) / len(self.interactions)
        escalated_ratio = outcome_counts.get(InteractionOutcome.ESCALATED.value, 0) / len(self.interactions)
        
        social_temperature = "peaceful"
        if escalated_ratio > 0.2:
            social_temperature = "tense"
        elif negative_ratio > 0.4:
            social_temperature = "hostile"
        elif positive_ratio > 0.6:
            social_temperature = "friendly"
        
        return {
            "total_interactions": len(self.interactions),
            "interaction_types": type_counts,
            "outcomes": outcome_counts,
            "most_interactive": most_interactive,
            "social_temperature": social_temperature,
            "conflicts_created": sum(1 for i in self.interactions if i.conflicts_triggered),
            "rumors_spread": sum(len(i.rumors_created) for i in self.interactions)
        }