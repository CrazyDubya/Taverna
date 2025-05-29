"""Dynamic dialogue system with context awareness."""

from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import random

from .psychology import NPCPsychology, Mood, Personality
from .relationships import RelationshipType


class DialogueType(Enum):
    """Types of dialogue interactions."""
    GREETING = "greeting"
    FAREWELL = "farewell"
    SMALL_TALK = "small_talk"
    GOSSIP = "gossip"
    BUSINESS = "business"
    PERSONAL = "personal"
    ROMANTIC = "romantic"
    THREATENING = "threatening"
    PLEADING = "pleading"
    INFORMATION = "information"
    QUEST = "quest"
    BANTER = "banter"


class DialogueTone(Enum):
    """Emotional tone of dialogue."""
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    HOSTILE = "hostile"
    FEARFUL = "fearful"
    ROMANTIC = "romantic"
    SUSPICIOUS = "suspicious"
    EXCITED = "excited"
    BORED = "bored"
    DESPERATE = "desperate"


@dataclass
class DialogueContext:
    """Context for dialogue generation."""
    speaker_id: str
    listener_id: str
    location: str
    time_of_day: str
    
    # Relationship context
    relationship_type: RelationshipType
    relationship_strength: float
    last_interaction_type: Optional[str] = None
    
    # Current situation
    current_event: Optional[str] = None
    nearby_characters: List[str] = field(default_factory=list)
    environmental_factors: Dict[str, Any] = field(default_factory=dict)
    
    # History
    topics_discussed: Set[str] = field(default_factory=set)
    secrets_known: Set[str] = field(default_factory=set)
    
    # Goals
    speaker_goal: Optional[str] = None
    listener_goal: Optional[str] = None


@dataclass
class DialogueOption:
    """A possible dialogue choice."""
    text: str
    type: DialogueType
    tone: DialogueTone
    
    # Requirements
    requires_relationship: Optional[float] = None
    requires_mood: Optional[List[Mood]] = None
    requires_personality: Optional[List[Personality]] = None
    requires_knowledge: Optional[str] = None
    
    # Effects
    relationship_change: float = 0.0
    reveals_secret: Optional[str] = None
    gives_information: Optional[str] = None
    triggers_event: Optional[str] = None
    
    # Metadata
    priority: float = 0.5
    can_repeat: bool = True
    cooldown: int = 0  # Turns before can use again
    
    def is_available(self, context: DialogueContext, speaker_psychology: NPCPsychology) -> bool:
        """Check if this dialogue option is available."""
        # Check relationship requirement
        if self.requires_relationship is not None:
            if context.relationship_strength < self.requires_relationship:
                return False
        
        # Check mood requirement
        if self.requires_mood is not None:
            if speaker_psychology.current_mood not in self.requires_mood:
                return False
        
        # Check personality requirement
        if self.requires_personality is not None:
            if speaker_psychology.base_personality not in self.requires_personality:
                return False
        
        # Check knowledge requirement
        if self.requires_knowledge is not None:
            if self.requires_knowledge not in context.secrets_known:
                return False
        
        return True


@dataclass
class DialogueResponse:
    """A response to dialogue."""
    text: str
    tone: DialogueTone
    emotion: Optional[str] = None
    
    # Follow-up
    ends_conversation: bool = False
    changes_topic: bool = False
    new_topic: Optional[DialogueType] = None
    
    # Side effects
    relationship_change: float = 0.0
    mood_change: Optional[Mood] = None
    triggers_event: Optional[str] = None


class DialogueGenerator:
    """Generates contextual dialogue for NPCs."""
    
    def __init__(self):
        self.dialogue_templates: Dict[DialogueType, List[str]] = self._load_templates()
        self.personality_modifiers: Dict[Personality, Dict[str, Any]] = self._load_personality_modifiers()
        self.mood_modifiers: Dict[Mood, Dict[str, Any]] = self._load_mood_modifiers()
    
    def _load_templates(self) -> Dict[DialogueType, List[str]]:
        """Load dialogue templates."""
        return {
            DialogueType.GREETING: [
                "Well met, {listener}!",
                "Ah, {listener}, good to see you.",
                "{listener}! What brings you here?",
                "Evening, {listener}.",
                "By the gods, {listener}! It's been too long!"
            ],
            DialogueType.SMALL_TALK: [
                "The weather's been {weather} lately, hasn't it?",
                "Have you heard about {recent_event}?",
                "Business has been {business_state} recently.",
                "I was just thinking about {random_topic}.",
                "This {location} gets more {adjective} every day."
            ],
            DialogueType.GOSSIP: [
                "You didn't hear this from me, but {gossip_content}...",
                "I heard the most interesting thing about {character}...",
                "Between you and me, {secret_hint}.",
                "Word around the tavern is that {rumor}.",
                "Don't spread this around, but {juicy_gossip}."
            ],
            DialogueType.THREATENING: [
                "You'd best watch yourself, {listener}.",
                "I know what you did, {listener}.",
                "Stay away from {protected_thing}, or else.",
                "This is your only warning.",
                "You're playing a dangerous game."
            ],
            DialogueType.ROMANTIC: [
                "Your eyes sparkle like {poetic_comparison}.",
                "I can't stop thinking about you, {listener}.",
                "Would you join me for {romantic_activity}?",
                "Every moment with you is {romantic_adjective}.",
                "My heart races when I see you."
            ]
        }
    
    def _load_personality_modifiers(self) -> Dict[Personality, Dict[str, Any]]:
        """Load personality-specific modifiers."""
        return {
            Personality.FRIENDLY: {
                "greeting_enthusiasm": 1.5,
                "gossip_likelihood": 0.8,
                "hostility_threshold": 0.8,
                "compliment_frequency": 0.7
            },
            Personality.SUSPICIOUS: {
                "greeting_enthusiasm": 0.5,
                "gossip_likelihood": 0.3,
                "hostility_threshold": 0.3,
                "information_guardedness": 0.9
            },
            Personality.AGGRESSIVE: {
                "greeting_enthusiasm": 0.3,
                "threat_likelihood": 0.8,
                "hostility_threshold": 0.2,
                "dominance_assertions": 0.9
            }
        }
    
    def _load_mood_modifiers(self) -> Dict[Mood, Dict[str, Any]]:
        """Load mood-specific modifiers."""
        return {
            Mood.HAPPY: {
                "tone_shift": 0.3,  # More positive
                "talkativeness": 1.3,
                "secret_looseness": 0.2
            },
            Mood.ANGRY: {
                "tone_shift": -0.5,  # More negative
                "talkativeness": 0.8,
                "aggression_boost": 0.5
            },
            Mood.SAD: {
                "tone_shift": -0.3,
                "talkativeness": 0.6,
                "sympathy_seeking": 0.7
            }
        }
    
    def generate_dialogue_options(self, context: DialogueContext, 
                                speaker_psychology: NPCPsychology,
                                num_options: int = 3) -> List[DialogueOption]:
        """Generate dialogue options based on context."""
        options = []
        
        # Determine appropriate dialogue types
        appropriate_types = self._get_appropriate_dialogue_types(context, speaker_psychology)
        
        for dialogue_type in appropriate_types[:num_options]:
            # Generate option for this type
            option = self._generate_option(dialogue_type, context, speaker_psychology)
            if option:
                options.append(option)
        
        # Sort by priority
        options.sort(key=lambda x: x.priority, reverse=True)
        
        return options
    
    def _get_appropriate_dialogue_types(self, context: DialogueContext,
                                      psychology: NPCPsychology) -> List[DialogueType]:
        """Determine appropriate dialogue types for situation."""
        appropriate = []
        
        # Always consider greeting if haven't talked recently
        if context.last_interaction_type is None:
            appropriate.append(DialogueType.GREETING)
        
        # Consider relationship
        if context.relationship_strength > 0.7:
            appropriate.extend([DialogueType.PERSONAL, DialogueType.GOSSIP])
            if context.relationship_type == RelationshipType.LOVER:
                appropriate.append(DialogueType.ROMANTIC)
        elif context.relationship_strength < 0.3:
            appropriate.extend([DialogueType.THREATENING, DialogueType.BUSINESS])
        else:
            appropriate.extend([DialogueType.SMALL_TALK, DialogueType.INFORMATION])
        
        # Consider mood
        if psychology.current_mood == Mood.HAPPY:
            appropriate.extend([DialogueType.BANTER, DialogueType.GOSSIP])
        elif psychology.current_mood == Mood.ANGRY:
            appropriate.append(DialogueType.THREATENING)
        elif psychology.current_mood == Mood.ANXIOUS:
            appropriate.append(DialogueType.PLEADING)
        
        # Consider goals
        if context.speaker_goal == "get_information":
            appropriate.append(DialogueType.INFORMATION)
        elif context.speaker_goal == "threaten":
            appropriate.append(DialogueType.THREATENING)
        elif context.speaker_goal == "romance":
            appropriate.append(DialogueType.ROMANTIC)
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for item in appropriate:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        
        return unique
    
    def _generate_option(self, dialogue_type: DialogueType,
                        context: DialogueContext,
                        psychology: NPCPsychology) -> Optional[DialogueOption]:
        """Generate a specific dialogue option."""
        # Get base template
        templates = self.dialogue_templates.get(dialogue_type, [])
        if not templates:
            return None
        
        template = random.choice(templates)
        
        # Fill in template
        text = self._fill_template(template, context, psychology)
        
        # Determine tone
        tone = self._determine_tone(dialogue_type, context, psychology)
        
        # Create option
        option = DialogueOption(
            text=text,
            type=dialogue_type,
            tone=tone
        )
        
        # Set requirements based on type
        if dialogue_type == DialogueType.GOSSIP:
            option.requires_relationship = 0.5
        elif dialogue_type == DialogueType.ROMANTIC:
            option.requires_relationship = 0.7
            option.requires_mood = [Mood.HAPPY, Mood.CONTENT, Mood.EXCITED]
        elif dialogue_type == DialogueType.THREATENING:
            option.requires_mood = [Mood.ANGRY, Mood.SUSPICIOUS, Mood.FEARFUL]
        
        # Set effects
        if dialogue_type == DialogueType.GOSSIP:
            option.relationship_change = 0.1
            option.reveals_secret = random.choice(["minor_secret", None])
        elif dialogue_type == DialogueType.THREATENING:
            option.relationship_change = -0.2
        elif dialogue_type == DialogueType.ROMANTIC:
            option.relationship_change = 0.2
        
        # Set priority based on context
        option.priority = self._calculate_priority(option, context, psychology)
        
        return option
    
    def _fill_template(self, template: str, context: DialogueContext,
                      psychology: NPCPsychology) -> str:
        """Fill in a dialogue template with contextual information."""
        replacements = {
            "{listener}": context.listener_id,
            "{location}": context.location,
            "{weather}": context.environmental_factors.get("weather", "strange"),
            "{recent_event}": context.current_event or "the usual happenings",
            "{business_state}": random.choice(["slow", "busy", "strange", "profitable"]),
            "{random_topic}": random.choice(["the old days", "the future", "life", "fate"]),
            "{adjective}": random.choice(["interesting", "peculiar", "lively", "quiet"]),
            "{character}": random.choice(context.nearby_characters) if context.nearby_characters else "someone",
            "{gossip_content}": "something scandalous is happening",
            "{secret_hint}": "not everything is as it seems",
            "{rumor}": "changes are coming",
            "{juicy_gossip}": "certain people aren't who they claim to be",
            "{protected_thing}": "what's mine",
            "{poetic_comparison}": random.choice(["stars", "gems", "moonlight", "sunrise"]),
            "{romantic_activity}": random.choice(["a walk", "dinner", "a drink"]),
            "{romantic_adjective}": random.choice(["magical", "perfect", "wonderful", "special"])
        }
        
        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
        
        return result
    
    def _determine_tone(self, dialogue_type: DialogueType,
                       context: DialogueContext,
                       psychology: NPCPsychology) -> DialogueTone:
        """Determine the tone of dialogue."""
        # Base tone from dialogue type
        base_tones = {
            DialogueType.GREETING: DialogueTone.FRIENDLY,
            DialogueType.THREATENING: DialogueTone.HOSTILE,
            DialogueType.ROMANTIC: DialogueTone.ROMANTIC,
            DialogueType.PLEADING: DialogueTone.DESPERATE,
            DialogueType.GOSSIP: DialogueTone.EXCITED
        }
        
        base_tone = base_tones.get(dialogue_type, DialogueTone.NEUTRAL)
        
        # Modify based on relationship
        if context.relationship_strength < 0.3:
            if base_tone == DialogueTone.FRIENDLY:
                base_tone = DialogueTone.NEUTRAL
            elif base_tone == DialogueTone.NEUTRAL:
                base_tone = DialogueTone.SUSPICIOUS
        
        # Modify based on mood
        mood_tone_map = {
            Mood.HAPPY: DialogueTone.FRIENDLY,
            Mood.ANGRY: DialogueTone.HOSTILE,
            Mood.FEARFUL: DialogueTone.FEARFUL,
            Mood.SAD: DialogueTone.NEUTRAL
        }
        
        if psychology.current_mood in mood_tone_map:
            # Blend with mood tone
            mood_influence = 0.3
            if random.random() < mood_influence:
                base_tone = mood_tone_map[psychology.current_mood]
        
        return base_tone
    
    def _calculate_priority(self, option: DialogueOption,
                          context: DialogueContext,
                          psychology: NPCPsychology) -> float:
        """Calculate priority for a dialogue option."""
        priority = 0.5
        
        # Goal alignment
        if context.speaker_goal:
            if option.type == DialogueType.INFORMATION and context.speaker_goal == "get_information":
                priority += 0.3
            elif option.type == DialogueType.THREATENING and context.speaker_goal == "intimidate":
                priority += 0.3
        
        # Personality alignment
        personality_preferences = {
            Personality.FRIENDLY: [DialogueType.GREETING, DialogueType.GOSSIP, DialogueType.SMALL_TALK],
            Personality.SUSPICIOUS: [DialogueType.INFORMATION, DialogueType.THREATENING],
            Personality.AGGRESSIVE: [DialogueType.THREATENING, DialogueType.BUSINESS]
        }
        
        if psychology.base_personality in personality_preferences:
            if option.type in personality_preferences[psychology.base_personality]:
                priority += 0.2
        
        # Mood influence
        if psychology.current_mood == Mood.HAPPY and option.tone == DialogueTone.FRIENDLY:
            priority += 0.1
        elif psychology.current_mood == Mood.ANGRY and option.tone == DialogueTone.HOSTILE:
            priority += 0.2
        
        # Relationship influence
        if context.relationship_strength > 0.7 and option.type in [DialogueType.PERSONAL, DialogueType.GOSSIP]:
            priority += 0.15
        
        return min(1.0, priority)
    
    def generate_response(self, chosen_option: DialogueOption,
                         context: DialogueContext,
                         responder_psychology: NPCPsychology) -> DialogueResponse:
        """Generate a response to chosen dialogue."""
        # Determine response tone based on relationship and option
        response_tone = self._determine_response_tone(
            chosen_option, context, responder_psychology
        )
        
        # Generate response text
        response_text = self._generate_response_text(
            chosen_option, response_tone, context, responder_psychology
        )
        
        # Determine if conversation continues
        ends_conversation = self._should_end_conversation(
            chosen_option, context, responder_psychology
        )
        
        # Create response
        response = DialogueResponse(
            text=response_text,
            tone=response_tone,
            ends_conversation=ends_conversation
        )
        
        # Set relationship changes
        if chosen_option.tone == DialogueTone.HOSTILE:
            response.relationship_change = -0.1
        elif chosen_option.tone == DialogueTone.ROMANTIC:
            if context.relationship_type == RelationshipType.LOVER:
                response.relationship_change = 0.1
            else:
                response.relationship_change = -0.05  # Unwanted advance
        
        # Set mood changes
        if chosen_option.tone == DialogueTone.HOSTILE:
            if responder_psychology.base_personality == Personality.AGGRESSIVE:
                response.mood_change = Mood.ANGRY
            else:
                response.mood_change = Mood.FEARFUL
        
        return response
    
    def _determine_response_tone(self, option: DialogueOption,
                                context: DialogueContext,
                                psychology: NPCPsychology) -> DialogueTone:
        """Determine tone of response."""
        # Mirror friendly tones if relationship is good
        if option.tone == DialogueTone.FRIENDLY and context.relationship_strength > 0.5:
            return DialogueTone.FRIENDLY
        
        # Respond to hostility based on personality
        if option.tone == DialogueTone.HOSTILE:
            if psychology.base_personality == Personality.AGGRESSIVE:
                return DialogueTone.HOSTILE
            elif psychology.base_personality == Personality.FRIENDLY:
                return DialogueTone.FEARFUL
            else:
                return DialogueTone.SUSPICIOUS
        
        # Default to neutral
        return DialogueTone.NEUTRAL
    
    def _generate_response_text(self, option: DialogueOption,
                               tone: DialogueTone,
                               context: DialogueContext,
                               psychology: NPCPsychology) -> str:
        """Generate response text."""
        response_templates = {
            (DialogueType.GREETING, DialogueTone.FRIENDLY): [
                "Good to see you too!",
                "Always a pleasure!",
                "How have you been?"
            ],
            (DialogueType.THREATENING, DialogueTone.HOSTILE): [
                "You don't scare me.",
                "Try it and see what happens.",
                "I'm not afraid of you."
            ],
            (DialogueType.THREATENING, DialogueTone.FEARFUL): [
                "Please, I don't want any trouble.",
                "I... I understand.",
                "There's no need for threats."
            ],
            (DialogueType.GOSSIP, DialogueTone.EXCITED): [
                "Oh, do tell me more!",
                "I hadn't heard that!",
                "How scandalous!"
            ]
        }
        
        # Get appropriate templates
        templates = response_templates.get((option.type, tone), [
            "I see.",
            "Interesting.",
            "Is that so?"
        ])
        
        return random.choice(templates)
    
    def _should_end_conversation(self, option: DialogueOption,
                                context: DialogueContext,
                                psychology: NPCPsychology) -> bool:
        """Determine if conversation should end."""
        # Threats often end conversations
        if option.type == DialogueType.THREATENING:
            return random.random() < 0.7
        
        # Farewells always end
        if option.type == DialogueType.FAREWELL:
            return True
        
        # Low relationship might end sooner
        if context.relationship_strength < 0.3:
            return random.random() < 0.3
        
        return False