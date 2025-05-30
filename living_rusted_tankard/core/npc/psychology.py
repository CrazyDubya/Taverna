"""NPC psychology and behavioral system."""

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
from datetime import datetime


class Personality(Enum):
    """Basic personality types."""
    FRIENDLY = "friendly"
    SUSPICIOUS = "suspicious"
    NEUTRAL = "neutral"
    AGGRESSIVE = "aggressive"
    SHY = "shy"
    GREGARIOUS = "gregarious"
    MYSTERIOUS = "mysterious"


class Mood(Enum):
    """Current mood states."""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    EXCITED = "excited"
    BORED = "bored"
    CONTENT = "content"
    ANXIOUS = "anxious"


class MotivationType(Enum):
    """Types of motivations."""
    WEALTH = "wealth"
    POWER = "power"
    KNOWLEDGE = "knowledge"
    SOCIAL = "social"
    SURVIVAL = "survival"
    REVENGE = "revenge"
    LOVE = "love"
    DUTY = "duty"
    PLEASURE = "pleasure"


@dataclass
class PersonaLayer:
    """A layer of personality - public face vs private thoughts."""
    traits: Dict[str, float] = field(default_factory=dict)  # trait -> strength (0-1)
    beliefs: List[str] = field(default_factory=list)
    fears: List[str] = field(default_factory=list)
    desires: List[str] = field(default_factory=list)
    
    def get_trait_strength(self, trait: str) -> float:
        """Get strength of a personality trait."""
        return self.traits.get(trait, 0.5)
    
    def modify_trait(self, trait: str, delta: float) -> None:
        """Modify a personality trait."""
        current = self.get_trait_strength(trait)
        self.traits[trait] = max(0.0, min(1.0, current + delta))


@dataclass
class Motivation:
    """A driving motivation for an NPC."""
    type: MotivationType
    description: str
    strength: float = 0.5  # 0-1, how important
    target: Optional[str] = None  # Specific target (person, object, etc)
    fulfilled: bool = False
    conditions: List[str] = field(default_factory=list)  # Conditions to fulfill
    
    def check_fulfillment(self, world_state: Dict[str, Any]) -> bool:
        """Check if motivation has been fulfilled."""
        # This would check world state against conditions
        # Simplified for now
        return self.fulfilled
    
    def adjust_strength(self, delta: float) -> None:
        """Adjust motivation strength."""
        self.strength = max(0.0, min(1.0, self.strength + delta))


@dataclass
class Secret:
    """A secret the NPC holds."""
    id: str
    content: str
    danger_level: float = 0.5  # 0-1, how dangerous if revealed
    shame_level: float = 0.5  # 0-1, how shameful
    
    # Who knows
    known_by: Set[str] = field(default_factory=set)
    suspected_by: Set[str] = field(default_factory=set)
    
    # Evidence
    evidence_items: List[str] = field(default_factory=list)
    evidence_locations: List[str] = field(default_factory=list)
    
    # Revelation
    revelation_conditions: List[str] = field(default_factory=list)
    consequences: Dict[str, str] = field(default_factory=dict)
    
    # Protection
    protection_actions: List[str] = field(default_factory=list)
    cover_story: Optional[str] = None
    
    def is_compromised(self) -> bool:
        """Check if secret is at risk."""
        return len(self.suspected_by) > 2 or len(self.evidence_items) > 0
    
    def reveal_to(self, character_id: str) -> None:
        """Reveal secret to someone."""
        self.known_by.add(character_id)
        if character_id in self.suspected_by:
            self.suspected_by.remove(character_id)
    
    def add_suspicion(self, character_id: str) -> None:
        """Add someone who suspects the secret."""
        if character_id not in self.known_by:
            self.suspected_by.add(character_id)


@dataclass
class Memory:
    """A memory of an interaction or event."""
    timestamp: datetime
    event_type: str
    participants: List[str]
    location: str
    description: str
    emotional_impact: float = 0.0  # -1 to 1
    importance: float = 0.5  # 0 to 1
    
    def fade(self, time_passed: float) -> None:
        """Memories fade over time."""
        # Importance decreases over time, modified by emotional impact
        fade_rate = 0.01 * (1.0 - abs(self.emotional_impact))
        self.importance = max(0.0, self.importance - fade_rate * time_passed)


@dataclass
class Relationship:
    """Relationship with another character."""
    character_id: str
    trust: float = 0.5  # 0-1
    affection: float = 0.5  # 0-1
    respect: float = 0.5  # 0-1
    fear: float = 0.0  # 0-1
    
    # History
    positive_interactions: int = 0
    negative_interactions: int = 0
    last_interaction: Optional[datetime] = None
    
    # Knowledge about them
    known_secrets: List[str] = field(default_factory=list)
    suspected_secrets: List[str] = field(default_factory=list)
    
    # Dynamics
    owes_favor: bool = False
    owed_favor: bool = False
    rivalry: bool = False
    romance: bool = False
    
    def get_overall_disposition(self) -> float:
        """Get overall disposition towards this character."""
        # Weighted combination of factors
        positive = (self.trust * 0.3 + self.affection * 0.4 + self.respect * 0.3)
        negative = self.fear * 0.5
        return max(-1.0, min(1.0, positive - negative))
    
    def modify_relationship(self, trust_delta: float = 0, affection_delta: float = 0,
                          respect_delta: float = 0, fear_delta: float = 0) -> None:
        """Modify relationship values."""
        self.trust = max(0.0, min(1.0, self.trust + trust_delta))
        self.affection = max(0.0, min(1.0, self.affection + affection_delta))
        self.respect = max(0.0, min(1.0, self.respect + respect_delta))
        self.fear = max(0.0, min(1.0, self.fear + fear_delta))
    
    def record_interaction(self, positive: bool) -> None:
        """Record an interaction."""
        if positive:
            self.positive_interactions += 1
        else:
            self.negative_interactions += 1
        self.last_interaction = datetime.now()


class NPCPsychology:
    """Complete psychological model for an NPC."""
    
    def __init__(self, npc_id: str, base_personality: Personality = Personality.NEUTRAL):
        self.npc_id = npc_id
        self.base_personality = base_personality
        self.current_mood = Mood.CONTENT
        
        # Personality layers
        self.public_persona = PersonaLayer()
        self.private_thoughts = PersonaLayer()
        
        # Internal state
        self.motivations: List[Motivation] = []
        self.secrets: List[Secret] = []
        self.memories: List[Memory] = []
        self.relationships: Dict[str, Relationship] = {}
        
        # Behavioral modifiers
        self.stress_level: float = 0.0  # 0-1
        self.energy_level: float = 1.0  # 0-1
        self.intoxication: float = 0.0  # 0-1
        
        # Initialize based on personality
        self._initialize_personality()
    
    def _initialize_personality(self) -> None:
        """Set initial traits based on personality type."""
        if self.base_personality == Personality.FRIENDLY:
            self.public_persona.traits = {
                "openness": 0.8,
                "agreeableness": 0.9,
                "trust": 0.7,
                "hostility": 0.1
            }
        elif self.base_personality == Personality.SUSPICIOUS:
            self.public_persona.traits = {
                "openness": 0.3,
                "agreeableness": 0.4,
                "trust": 0.2,
                "paranoia": 0.8
            }
        elif self.base_personality == Personality.AGGRESSIVE:
            self.public_persona.traits = {
                "openness": 0.5,
                "agreeableness": 0.2,
                "hostility": 0.8,
                "dominance": 0.7
            }
        # etc...
        
        # Private thoughts often differ from public persona
        self.private_thoughts.traits = self.public_persona.traits.copy()
        # Add some variation
        for trait in self.private_thoughts.traits:
            self.private_thoughts.traits[trait] += random.uniform(-0.2, 0.2)
            self.private_thoughts.traits[trait] = max(0.0, min(1.0, 
                self.private_thoughts.traits[trait]))
    
    def add_motivation(self, motivation: Motivation) -> None:
        """Add a new motivation."""
        self.motivations.append(motivation)
        # Sort by strength
        self.motivations.sort(key=lambda m: m.strength, reverse=True)
    
    def add_secret(self, secret: Secret) -> None:
        """Add a new secret."""
        self.secrets.append(secret)
        # Secrets increase stress
        self.stress_level = min(1.0, self.stress_level + secret.danger_level * 0.1)
    
    def remember_event(self, event_type: str, participants: List[str], 
                      location: str, description: str, emotional_impact: float) -> None:
        """Create a memory of an event."""
        memory = Memory(
            timestamp=datetime.now(),
            event_type=event_type,
            participants=participants,
            location=location,
            description=description,
            emotional_impact=emotional_impact,
            importance=abs(emotional_impact)  # More emotional = more important
        )
        
        self.memories.append(memory)
        
        # Keep only most important memories if too many
        if len(self.memories) > 100:
            self.memories.sort(key=lambda m: m.importance, reverse=True)
            self.memories = self.memories[:80]
        
        # Update mood based on emotional impact
        self._update_mood_from_emotion(emotional_impact)
    
    def _update_mood_from_emotion(self, emotional_impact: float) -> None:
        """Update mood based on emotional event."""
        if emotional_impact > 0.5:
            self.current_mood = Mood.HAPPY
        elif emotional_impact > 0.2:
            self.current_mood = Mood.CONTENT
        elif emotional_impact < -0.5:
            self.current_mood = Mood.ANGRY if random.random() > 0.5 else Mood.SAD
        elif emotional_impact < -0.2:
            self.current_mood = Mood.ANXIOUS
    
    def get_relationship(self, character_id: str) -> Relationship:
        """Get or create relationship with character."""
        if character_id not in self.relationships:
            self.relationships[character_id] = Relationship(character_id)
        return self.relationships[character_id]
    
    def interact_with(self, character_id: str, interaction_type: str, 
                     outcome: str) -> None:
        """Process an interaction with another character."""
        relationship = self.get_relationship(character_id)
        
        # Define interaction effects
        interaction_effects = {
            "friendly_chat": (0.05, 0.1, 0.05, 0),
            "deep_conversation": (0.15, 0.1, 0.1, 0),
            "argument": (-0.1, -0.05, -0.05, 0.1),
            "threat": (-0.2, -0.1, -0.1, 0.3),
            "help_given": (0.1, 0.15, 0.15, -0.05),
            "help_received": (0.1, 0.1, 0.05, 0),
            "betrayal": (-0.4, -0.3, -0.3, 0.2),
            "share_secret": (0.2, 0.1, 0.1, 0)
        }
        
        if interaction_type in interaction_effects:
            trust_d, affection_d, respect_d, fear_d = interaction_effects[interaction_type]
            relationship.modify_relationship(trust_d, affection_d, respect_d, fear_d)
        
        # Record interaction
        positive = outcome in ["positive", "successful", "pleasant"]
        relationship.record_interaction(positive)
        
        # Create memory
        emotional_impact = 0.5 if positive else -0.5
        self.remember_event(
            interaction_type,
            [character_id],
            "current_location",  # Would be actual location
            f"{interaction_type} with {character_id}: {outcome}",
            emotional_impact
        )
    
    def get_behavioral_tendency(self, situation: str) -> Tuple[str, float]:
        """Get likely behavior in a situation based on psychology."""
        # Combine public and private traits for internal decision-making
        combined_traits = {}
        for trait in set(self.public_persona.traits.keys()) | set(self.private_thoughts.traits.keys()):
            public = self.public_persona.get_trait_strength(trait)
            private = self.private_thoughts.get_trait_strength(trait)
            combined_traits[trait] = (public + private * 2) / 3  # Weight private more
        
        # Modify by current state
        stress_modifier = self.stress_level * 0.3
        energy_modifier = (1.0 - self.energy_level) * 0.2
        intox_modifier = self.intoxication * 0.4
        
        # Determine behavior based on situation
        if situation == "confrontation":
            aggression = combined_traits.get("hostility", 0.5) + stress_modifier
            flee_tendency = combined_traits.get("fear", 0.3) + (1.0 - energy_modifier)
            
            if aggression > flee_tendency and aggression > 0.6:
                return "fight", aggression
            elif flee_tendency > 0.6:
                return "flee", flee_tendency
            else:
                return "negotiate", combined_traits.get("agreeableness", 0.5)
        
        elif situation == "social_gathering":
            openness = combined_traits.get("openness", 0.5) - stress_modifier
            if openness > 0.6:
                return "mingle", openness
            elif openness < 0.3:
                return "withdraw", 1.0 - openness
            else:
                return "observe", 0.5
        
        elif situation == "request_for_help":
            helpfulness = combined_traits.get("agreeableness", 0.5) * energy_modifier
            suspicion = combined_traits.get("paranoia", 0.3) + stress_modifier
            
            if helpfulness > suspicion and helpfulness > 0.5:
                return "help", helpfulness
            elif suspicion > 0.6:
                return "refuse_suspicious", suspicion
            else:
                return "consider", 0.5
        
        else:
            # Default behavior
            return "neutral", 0.5
    
    def should_reveal_secret(self, secret_id: str, to_character: str) -> Tuple[bool, str]:
        """Decide whether to reveal a secret."""
        secret = next((s for s in self.secrets if s.id == secret_id), None)
        if not secret:
            return False, "no such secret"
        
        relationship = self.get_relationship(to_character)
        
        # Factors for revealing
        trust_factor = relationship.trust
        danger_factor = 1.0 - secret.danger_level
        stress_factor = self.stress_level  # More stress = more likely to confide
        intox_factor = self.intoxication * 0.5  # Intoxication loosens tongues
        
        # Calculate probability
        reveal_probability = (trust_factor * 0.4 + danger_factor * 0.3 + 
                            stress_factor * 0.2 + intox_factor * 0.1)
        
        # Personality modifiers
        if self.base_personality == Personality.SUSPICIOUS:
            reveal_probability *= 0.5
        elif self.base_personality == Personality.GREGARIOUS:
            reveal_probability *= 1.3
        
        # Decision
        if reveal_probability > 0.7:
            return True, "trusts you enough"
        elif reveal_probability > 0.5 and self.intoxication > 0.5:
            return True, "alcohol loosened their tongue"
        elif reveal_probability > 0.4 and self.stress_level > 0.7:
            return True, "needed to confide in someone"
        else:
            return False, "not ready to share"
    
    def get_current_priority(self) -> Optional[Motivation]:
        """Get current highest priority motivation."""
        # Filter unfulfilled motivations
        active = [m for m in self.motivations if not m.fulfilled]
        if not active:
            return None
        
        # Modify by current state
        for motivation in active:
            if motivation.type == MotivationType.SURVIVAL:
                # Survival becomes more important when threatened
                if self.stress_level > 0.7 or self.energy_level < 0.3:
                    motivation.adjust_strength(0.2)
            elif motivation.type == MotivationType.SOCIAL:
                # Social needs decrease when stressed
                if self.stress_level > 0.5:
                    motivation.adjust_strength(-0.1)
        
        # Return highest priority
        active.sort(key=lambda m: m.strength, reverse=True)
        return active[0] if active else None
    
    def update_psychology(self, time_passed: float) -> None:
        """Update psychological state over time."""
        # Fade memories
        for memory in self.memories:
            memory.fade(time_passed)
        
        # Remove very faded memories
        self.memories = [m for m in self.memories if m.importance > 0.01]
        
        # Reduce stress naturally
        self.stress_level = max(0.0, self.stress_level - 0.01 * time_passed)
        
        # Restore energy (if resting)
        self.energy_level = min(1.0, self.energy_level + 0.02 * time_passed)
        
        # Reduce intoxication
        self.intoxication = max(0.0, self.intoxication - 0.05 * time_passed)
        
        # Mood tends toward base personality
        if random.random() < 0.1:  # 10% chance per update
            if self.base_personality == Personality.FRIENDLY:
                self.current_mood = Mood.CONTENT
            elif self.base_personality == Personality.AGGRESSIVE:
                self.current_mood = Mood.ANGRY if self.stress_level > 0.5 else Mood.BORED
            # etc...


class NPCPsychologyManager:
    """Manager for all NPC psychological states"""
    
    def __init__(self):
        self.npc_psychologies: Dict[str, NPCPsychology] = {}
    
    def initialize_npc(self, npc_id: str, npc: Any) -> None:
        """Initialize psychology for an NPC"""
        # Determine personality from NPC data
        personality = Personality.NEUTRAL
        if hasattr(npc, 'personality'):
            try:
                personality = Personality(npc.personality)
            except ValueError:
                personality = Personality.NEUTRAL
        
        # Create psychology instance
        self.npc_psychologies[npc_id] = NPCPsychology(
            npc_id=npc_id,
            base_personality=personality
        )
        
        # Add any secrets as psychological secrets
        if hasattr(npc, 'has_secret') and npc.has_secret:
            secret = Secret(
                content="This NPC has a secret",
                importance=0.8,
                danger_level=0.5
            )
            self.npc_psychologies[npc_id].secrets.append(secret)
    
    def get_npc_state(self, npc_id: str) -> Dict[str, Any]:
        """Get current psychological state of an NPC"""
        if npc_id not in self.npc_psychologies:
            return {
                'mood': 'neutral',
                'stress_level': 0.0,
                'energy_level': 1.0,
                'personality': 'neutral'
            }
        
        psych = self.npc_psychologies[npc_id]
        return {
            'mood': psych.current_mood.value,
            'stress_level': psych.stress_level,
            'energy_level': psych.energy_level,
            'personality': psych.base_personality.value,
            'openness': psych.public_persona.traits.get('openness', 0.5),
            'agreeableness': psych.public_persona.traits.get('agreeableness', 0.5),
            'trust': psych.public_persona.traits.get('trust', 0.5)
        }
    
    def update_npc_state(self, npc_id: str, elapsed_time: float) -> None:
        """Update NPC psychology over time"""
        if npc_id in self.npc_psychologies:
            self.npc_psychologies[npc_id].update_psychology(elapsed_time)
    
    def modify_mood(self, npc_id: str, mood_modifier: str) -> None:
        """Modify an NPC's mood"""
        if npc_id not in self.npc_psychologies:
            return
        
        psych = self.npc_psychologies[npc_id]
        
        # Apply mood modifier
        if mood_modifier == 'tense':
            psych.stress_level = min(1.0, psych.stress_level + 0.2)
            if psych.stress_level > 0.7:
                psych.current_mood = Mood.ANXIOUS
        elif mood_modifier == 'calm':
            psych.stress_level = max(0.0, psych.stress_level - 0.3)
            psych.current_mood = Mood.CONTENT
        elif mood_modifier == 'excited':
            psych.current_mood = Mood.EXCITED
        elif mood_modifier == 'mysterious':
            psych.current_mood = Mood.ANXIOUS
            psych.stress_level = min(1.0, psych.stress_level + 0.1)