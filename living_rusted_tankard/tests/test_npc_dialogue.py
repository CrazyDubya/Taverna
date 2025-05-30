"""Tests for the dynamic dialogue system."""

import pytest
from unittest.mock import Mock, patch

from core.npc_systems.dialogue import (
    DialogueGenerator, DialogueContext, DialogueOption, DialogueResponse,
    DialogueType, DialogueTone
)
from core.npc_systems.psychology import NPCPsychology, Personality, Mood
from core.npc_systems.relationships import RelationshipType


class TestDialogueOption:
    """Test DialogueOption functionality."""
    
    def test_dialogue_option_creation(self):
        """Test creating dialogue options."""
        option = DialogueOption(
            text="How are you today?",
            type=DialogueType.SMALL_TALK,
            tone=DialogueTone.FRIENDLY,
            requires_relationship=0.3,
            relationship_change=0.05
        )
        
        assert option.text == "How are you today?"
        assert option.type == DialogueType.SMALL_TALK
        assert option.tone == DialogueTone.FRIENDLY
        assert option.priority == 0.5  # Default
    
    def test_availability_checks(self):
        """Test checking dialogue availability."""
        option = DialogueOption(
            text="Share a secret",
            type=DialogueType.GOSSIP,
            tone=DialogueTone.EXCITED,
            requires_relationship=0.6,
            requires_mood=[Mood.HAPPY, Mood.CONTENT]
        )
        
        context = DialogueContext(
            speaker_id="npc1",
            listener_id="npc2",
            location="tavern",
            time_of_day="evening",
            relationship_type=RelationshipType.FRIEND,
            relationship_strength=0.7
        )
        
        psychology = NPCPsychology("npc1", Personality.FRIENDLY)
        psychology.current_mood = Mood.HAPPY
        
        # Should be available
        assert option.is_available(context, psychology)
        
        # Low relationship - not available
        context.relationship_strength = 0.4
        assert not option.is_available(context, psychology)
        
        # Wrong mood - not available
        context.relationship_strength = 0.7
        psychology.current_mood = Mood.ANGRY
        assert not option.is_available(context, psychology)
    
    def test_knowledge_requirements(self):
        """Test knowledge-based availability."""
        option = DialogueOption(
            text="I know about your secret...",
            type=DialogueType.THREATENING,
            tone=DialogueTone.SUSPICIOUS,
            requires_knowledge="dark_secret"
        )
        
        context = DialogueContext(
            speaker_id="npc1",
            listener_id="npc2",
            location="private_booth",
            time_of_day="night",
            relationship_type=RelationshipType.RIVAL,
            relationship_strength=0.2
        )
        
        psychology = NPCPsychology("npc1")
        
        # Without knowledge
        assert not option.is_available(context, psychology)
        
        # With knowledge
        context.secrets_known.add("dark_secret")
        assert option.is_available(context, psychology)


class TestDialogueGenerator:
    """Test DialogueGenerator functionality."""
    
    def test_generator_initialization(self):
        """Test dialogue generator setup."""
        generator = DialogueGenerator()
        
        assert DialogueType.GREETING in generator.dialogue_templates
        assert Personality.FRIENDLY in generator.personality_modifiers
        assert Mood.HAPPY in generator.mood_modifiers
    
    def test_appropriate_dialogue_types(self):
        """Test determining appropriate dialogue types."""
        generator = DialogueGenerator()
        
        # High relationship - personal topics
        context = DialogueContext(
            speaker_id="npc1",
            listener_id="npc2",
            location="main_hall",
            time_of_day="evening",
            relationship_type=RelationshipType.FRIEND,
            relationship_strength=0.8
        )
        
        psychology = NPCPsychology("npc1", Personality.FRIENDLY)
        
        appropriate = generator._get_appropriate_dialogue_types(context, psychology)
        
        assert DialogueType.PERSONAL in appropriate
        assert DialogueType.GOSSIP in appropriate
        
        # Low relationship - different topics
        context.relationship_strength = 0.2
        appropriate = generator._get_appropriate_dialogue_types(context, psychology)
        
        assert DialogueType.THREATENING in appropriate
        assert DialogueType.BUSINESS in appropriate
    
    def test_mood_influence(self):
        """Test mood influence on dialogue types."""
        generator = DialogueGenerator()
        
        context = DialogueContext(
            speaker_id="npc1",
            listener_id="npc2",
            location="main_hall",
            time_of_day="afternoon",
            relationship_type=RelationshipType.ACQUAINTANCE,
            relationship_strength=0.5
        )
        
        # Happy mood
        happy_psych = NPCPsychology("npc1")
        happy_psych.current_mood = Mood.HAPPY
        
        appropriate = generator._get_appropriate_dialogue_types(context, happy_psych)
        assert DialogueType.BANTER in appropriate
        assert DialogueType.GOSSIP in appropriate
        
        # Angry mood
        angry_psych = NPCPsychology("npc1")
        angry_psych.current_mood = Mood.ANGRY
        
        appropriate = generator._get_appropriate_dialogue_types(context, angry_psych)
        assert DialogueType.THREATENING in appropriate
    
    def test_goal_driven_dialogue(self):
        """Test goal-influenced dialogue selection."""
        generator = DialogueGenerator()
        
        context = DialogueContext(
            speaker_id="npc1",
            listener_id="npc2",
            location="main_hall",
            time_of_day="noon",
            relationship_type=RelationshipType.NEUTRAL,
            relationship_strength=0.5,
            speaker_goal="get_information"
        )
        
        psychology = NPCPsychology("npc1")
        
        appropriate = generator._get_appropriate_dialogue_types(context, psychology)
        assert DialogueType.INFORMATION in appropriate
    
    def test_dialogue_generation(self):
        """Test generating dialogue options."""
        generator = DialogueGenerator()
        
        context = DialogueContext(
            speaker_id="npc_bartender",
            listener_id="npc_patron",
            location="bar_area",
            time_of_day="evening",
            relationship_type=RelationshipType.ACQUAINTANCE,
            relationship_strength=0.6
        )
        
        psychology = NPCPsychology("npc_bartender", Personality.FRIENDLY)
        
        options = generator.generate_dialogue_options(context, psychology, num_options=3)
        
        assert len(options) <= 3
        assert all(isinstance(opt, DialogueOption) for opt in options)
        
        # Should be sorted by priority
        priorities = [opt.priority for opt in options]
        assert priorities == sorted(priorities, reverse=True)
    
    def test_template_filling(self):
        """Test filling dialogue templates."""
        generator = DialogueGenerator()
        
        context = DialogueContext(
            speaker_id="npc1",
            listener_id="Bob",
            location="main_hall",
            time_of_day="morning",
            relationship_type=RelationshipType.FRIEND,
            relationship_strength=0.7,
            nearby_characters=["Alice", "Charlie"]
        )
        
        context.environmental_factors = {"weather": "rainy"}
        
        psychology = NPCPsychology("npc1")
        
        template = "Good morning, {listener}! The weather's been {weather} lately, hasn't it?"
        filled = generator._fill_template(template, context, psychology)
        
        assert "Bob" in filled
        assert "rainy" in filled
    
    def test_tone_determination(self):
        """Test determining dialogue tone."""
        generator = DialogueGenerator()
        
        # Friendly context
        friendly_context = DialogueContext(
            speaker_id="npc1",
            listener_id="npc2",
            location="tavern",
            time_of_day="evening",
            relationship_type=RelationshipType.FRIEND,
            relationship_strength=0.8
        )
        
        happy_psych = NPCPsychology("npc1")
        happy_psych.current_mood = Mood.HAPPY
        
        tone = generator._determine_tone(DialogueType.GREETING, friendly_context, happy_psych)
        assert tone == DialogueTone.FRIENDLY
        
        # Hostile context
        hostile_context = DialogueContext(
            speaker_id="npc1",
            listener_id="npc2",
            location="tavern",
            time_of_day="night",
            relationship_type=RelationshipType.ENEMY,
            relationship_strength=0.1
        )
        
        angry_psych = NPCPsychology("npc1")
        angry_psych.current_mood = Mood.ANGRY
        
        tone = generator._determine_tone(DialogueType.GREETING, hostile_context, angry_psych)
        assert tone in [DialogueTone.NEUTRAL, DialogueTone.SUSPICIOUS]
    
    def test_priority_calculation(self):
        """Test calculating dialogue priority."""
        generator = DialogueGenerator()
        
        context = DialogueContext(
            speaker_id="npc1",
            listener_id="npc2",
            location="main_hall",
            time_of_day="evening",
            relationship_type=RelationshipType.FRIEND,
            relationship_strength=0.8,
            speaker_goal="get_information"
        )
        
        psychology = NPCPsychology("npc1", Personality.FRIENDLY)
        
        # Information option aligned with goal
        info_option = DialogueOption(
            text="What have you heard lately?",
            type=DialogueType.INFORMATION,
            tone=DialogueTone.NEUTRAL
        )
        
        priority = generator._calculate_priority(info_option, context, psychology)
        assert priority > 0.5  # Higher than base
        
        # Threatening option not aligned
        threat_option = DialogueOption(
            text="You better watch yourself",
            type=DialogueType.THREATENING,
            tone=DialogueTone.HOSTILE
        )
        
        threat_priority = generator._calculate_priority(threat_option, context, psychology)
        assert threat_priority < priority  # Lower than goal-aligned


class TestDialogueResponse:
    """Test dialogue response generation."""
    
    def test_response_creation(self):
        """Test creating dialogue responses."""
        response = DialogueResponse(
            text="I understand what you mean.",
            tone=DialogueTone.NEUTRAL,
            emotion="thoughtful",
            relationship_change=0.05
        )
        
        assert response.text == "I understand what you mean."
        assert response.tone == DialogueTone.NEUTRAL
        assert not response.ends_conversation
    
    def test_response_generation(self):
        """Test generating responses to dialogue."""
        generator = DialogueGenerator()
        
        # Friendly greeting
        friendly_option = DialogueOption(
            text="Good to see you!",
            type=DialogueType.GREETING,
            tone=DialogueTone.FRIENDLY
        )
        
        context = DialogueContext(
            speaker_id="npc1",
            listener_id="npc2",
            location="main_hall",
            time_of_day="morning",
            relationship_type=RelationshipType.FRIEND,
            relationship_strength=0.7
        )
        
        responder_psych = NPCPsychology("npc2", Personality.FRIENDLY)
        
        response = generator.generate_response(friendly_option, context, responder_psych)
        
        assert response.tone == DialogueTone.FRIENDLY
        assert response.relationship_change >= 0
        
        # Hostile threat
        threat_option = DialogueOption(
            text="Stay away or else!",
            type=DialogueType.THREATENING,
            tone=DialogueTone.HOSTILE
        )
        
        aggressive_psych = NPCPsychology("npc2", Personality.AGGRESSIVE)
        response = generator.generate_response(threat_option, context, aggressive_psych)
        
        assert response.tone == DialogueTone.HOSTILE
        assert response.mood_change == Mood.ANGRY
    
    def test_conversation_flow(self):
        """Test conversation ending logic."""
        generator = DialogueGenerator()
        
        # Threat often ends conversation
        threat_option = DialogueOption(
            text="This is your last warning",
            type=DialogueType.THREATENING,
            tone=DialogueTone.HOSTILE
        )
        
        context = DialogueContext(
            speaker_id="npc1",
            listener_id="npc2",
            location="alley",
            time_of_day="night",
            relationship_type=RelationshipType.ENEMY,
            relationship_strength=0.1
        )
        
        psychology = NPCPsychology("npc2")
        
        should_end = generator._should_end_conversation(threat_option, context, psychology)
        # High probability of ending after threat
        
        # Farewell always ends
        farewell_option = DialogueOption(
            text="Goodbye",
            type=DialogueType.FAREWELL,
            tone=DialogueTone.NEUTRAL
        )
        
        should_end = generator._should_end_conversation(farewell_option, context, psychology)
        assert should_end


class TestIntegration:
    """Integration tests for dialogue system."""
    
    def test_complete_dialogue_exchange(self):
        """Test a complete dialogue exchange."""
        generator = DialogueGenerator()
        
        # Setup NPCs
        bartender = NPCPsychology("bartender", Personality.FRIENDLY)
        patron = NPCPsychology("patron", Personality.NEUTRAL)
        
        # Create context
        context = DialogueContext(
            speaker_id="bartender",
            listener_id="patron",
            location="bar_area",
            time_of_day="evening",
            relationship_type=RelationshipType.ACQUAINTANCE,
            relationship_strength=0.6
        )
        
        # Bartender initiates
        options = generator.generate_dialogue_options(context, bartender, num_options=3)
        assert len(options) > 0
        
        # Pick an option
        chosen = options[0]
        
        # Generate patron's response
        response = generator.generate_response(chosen, context, patron)
        assert response is not None
        
        # Check effects
        if chosen.type == DialogueType.GOSSIP:
            assert chosen.reveals_secret is not None or chosen.relationship_change > 0
    
    def test_personality_driven_conversation(self):
        """Test how personality affects conversation."""
        generator = DialogueGenerator()
        
        # Friendly NPC
        friendly_npc = NPCPsychology("friendly", Personality.FRIENDLY)
        friendly_npc.current_mood = Mood.HAPPY
        
        # Suspicious NPC
        suspicious_npc = NPCPsychology("suspicious", Personality.SUSPICIOUS)
        suspicious_npc.current_mood = Mood.ANXIOUS
        
        context = DialogueContext(
            speaker_id="friendly",
            listener_id="suspicious",
            location="main_hall",
            time_of_day="afternoon",
            relationship_type=RelationshipType.STRANGER,
            relationship_strength=0.0
        )
        
        # Friendly initiates
        friendly_options = generator.generate_dialogue_options(context, friendly_npc)
        
        # Should favor friendly/gossip types
        friendly_types = [opt.type for opt in friendly_options]
        assert any(t in [DialogueType.GREETING, DialogueType.SMALL_TALK] 
                  for t in friendly_types)
        
        # Suspicious response
        suspicious_context = DialogueContext(
            speaker_id="suspicious",
            listener_id="friendly",
            location="main_hall",
            time_of_day="afternoon",
            relationship_type=RelationshipType.STRANGER,
            relationship_strength=0.0
        )
        
        suspicious_options = generator.generate_dialogue_options(
            suspicious_context, suspicious_npc
        )
        
        # Should be more guarded
        assert len([opt for opt in suspicious_options 
                   if opt.type == DialogueType.GOSSIP]) == 0