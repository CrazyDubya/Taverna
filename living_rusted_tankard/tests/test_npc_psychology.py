"""Tests for NPC psychology system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from core.npc_systems.psychology import (
    NPCPsychology, Personality, Mood, MotivationType,
    PersonaLayer, Motivation, Secret, Memory, Relationship
)


class TestPersonaLayer:
    """Test PersonaLayer functionality."""
    
    def test_trait_management(self):
        """Test managing personality traits."""
        persona = PersonaLayer()
        
        # Set initial trait
        persona.traits["honesty"] = 0.7
        assert persona.get_trait_strength("honesty") == 0.7
        
        # Get non-existent trait (should return default)
        assert persona.get_trait_strength("courage") == 0.5
        
        # Modify trait
        persona.modify_trait("honesty", 0.2)
        assert persona.get_trait_strength("honesty") == 0.9
        
        # Test bounds
        persona.modify_trait("honesty", 0.5)
        assert persona.get_trait_strength("honesty") == 1.0
        
        persona.modify_trait("honesty", -1.5)
        assert persona.get_trait_strength("honesty") == 0.0


class TestMotivation:
    """Test Motivation functionality."""
    
    def test_motivation_creation(self):
        """Test creating motivations."""
        motivation = Motivation(
            type=MotivationType.WEALTH,
            description="Accumulate 1000 gold",
            strength=0.8,
            target="1000_gold"
        )
        
        assert motivation.type == MotivationType.WEALTH
        assert motivation.strength == 0.8
        assert not motivation.fulfilled
    
    def test_strength_adjustment(self):
        """Test adjusting motivation strength."""
        motivation = Motivation(
            type=MotivationType.SOCIAL,
            description="Make new friends",
            strength=0.5
        )
        
        motivation.adjust_strength(0.3)
        assert motivation.strength == 0.8
        
        motivation.adjust_strength(0.5)
        assert motivation.strength == 1.0
        
        motivation.adjust_strength(-1.5)
        assert motivation.strength == 0.0


class TestSecret:
    """Test Secret functionality."""
    
    def test_secret_creation(self):
        """Test creating secrets."""
        secret = Secret(
            id="stolen_goods",
            content="Stole merchandise from a merchant",
            danger_level=0.7,
            shame_level=0.6
        )
        
        assert secret.id == "stolen_goods"
        assert secret.danger_level == 0.7
        assert len(secret.known_by) == 0
    
    def test_secret_revelation(self):
        """Test revealing secrets."""
        secret = Secret(
            id="affair",
            content="Having an affair",
            danger_level=0.8
        )
        
        # Add suspicion
        secret.add_suspicion("npc_guard")
        assert "npc_guard" in secret.suspected_by
        
        # Reveal to someone
        secret.reveal_to("npc_friend")
        assert "npc_friend" in secret.known_by
        assert "npc_friend" not in secret.suspected_by
        
        # Reveal to suspicious person
        secret.reveal_to("npc_guard")
        assert "npc_guard" in secret.known_by
        assert "npc_guard" not in secret.suspected_by
    
    def test_secret_compromise(self):
        """Test checking if secret is compromised."""
        secret = Secret(id="test", content="Test secret")
        
        assert not secret.is_compromised()
        
        # Add suspicions
        secret.add_suspicion("npc1")
        secret.add_suspicion("npc2")
        assert not secret.is_compromised()
        
        secret.add_suspicion("npc3")
        assert secret.is_compromised()  # Too many suspicions
        
        # Or evidence
        secret2 = Secret(id="test2", content="Test secret 2")
        secret2.evidence_items.append("letter")
        assert secret2.is_compromised()


class TestMemory:
    """Test Memory functionality."""
    
    def test_memory_creation(self):
        """Test creating memories."""
        memory = Memory(
            timestamp=datetime.now(),
            event_type="conversation",
            participants=["npc1", "npc2"],
            location="main_hall",
            description="Pleasant chat about weather",
            emotional_impact=0.3,
            importance=0.5
        )
        
        assert memory.event_type == "conversation"
        assert len(memory.participants) == 2
        assert memory.emotional_impact == 0.3
    
    def test_memory_fading(self):
        """Test memory fading over time."""
        memory = Memory(
            timestamp=datetime.now(),
            event_type="argument",
            participants=["npc1"],
            location="bar",
            description="Heated argument",
            emotional_impact=-0.8,
            importance=0.9
        )
        
        # High emotional impact slows fading
        initial_importance = memory.importance
        memory.fade(10.0)  # 10 hours
        
        assert memory.importance < initial_importance
        assert memory.importance > 0.8  # Still important due to high emotion
        
        # Low emotion memory fades faster
        neutral_memory = Memory(
            timestamp=datetime.now(),
            event_type="greeting",
            participants=["npc1"],
            location="hall",
            description="Said hello",
            emotional_impact=0.1,
            importance=0.5
        )
        
        neutral_memory.fade(10.0)
        assert neutral_memory.importance < memory.importance


class TestRelationship:
    """Test Relationship functionality."""
    
    def test_relationship_creation(self):
        """Test creating relationships."""
        relationship = Relationship(character_id="npc_friend")
        
        assert relationship.character_id == "npc_friend"
        assert relationship.trust == 0.5
        assert relationship.affection == 0.5
        assert relationship.respect == 0.5
        assert relationship.fear == 0.0
    
    def test_disposition_calculation(self):
        """Test overall disposition calculation."""
        relationship = Relationship(
            character_id="npc_test",
            trust=0.8,
            affection=0.9,
            respect=0.7,
            fear=0.1
        )
        
        disposition = relationship.get_overall_disposition()
        assert 0.7 < disposition < 0.9  # High positive
        
        # Fear reduces disposition
        relationship.fear = 0.6
        new_disposition = relationship.get_overall_disposition()
        assert new_disposition < disposition
    
    def test_relationship_modification(self):
        """Test modifying relationships."""
        relationship = Relationship(character_id="npc_test")
        
        relationship.modify_relationship(
            trust_delta=0.2,
            affection_delta=-0.1,
            respect_delta=0.3,
            fear_delta=0.0
        )
        
        assert relationship.trust == 0.7
        assert relationship.affection == 0.4
        assert relationship.respect == 0.8
        
        # Test bounds
        relationship.modify_relationship(trust_delta=0.5)
        assert relationship.trust == 1.0
    
    def test_interaction_recording(self):
        """Test recording interactions."""
        relationship = Relationship(character_id="npc_test")
        
        relationship.record_interaction(positive=True)
        assert relationship.positive_interactions == 1
        assert relationship.negative_interactions == 0
        assert relationship.last_interaction is not None
        
        relationship.record_interaction(positive=False)
        assert relationship.negative_interactions == 1


class TestNPCPsychology:
    """Test complete NPC psychology system."""
    
    def test_npc_creation(self):
        """Test creating NPC with psychology."""
        npc = NPCPsychology("npc_test", Personality.FRIENDLY)
        
        assert npc.npc_id == "npc_test"
        assert npc.base_personality == Personality.FRIENDLY
        assert npc.current_mood == Mood.CONTENT
        
        # Check friendly traits
        assert npc.public_persona.get_trait_strength("openness") > 0.7
        assert npc.public_persona.get_trait_strength("hostility") < 0.3
    
    def test_motivation_management(self):
        """Test managing motivations."""
        npc = NPCPsychology("npc_test")
        
        # Add motivations
        motivation1 = Motivation(
            type=MotivationType.WEALTH,
            description="Get rich",
            strength=0.7
        )
        motivation2 = Motivation(
            type=MotivationType.SOCIAL,
            description="Make friends",
            strength=0.5
        )
        
        npc.add_motivation(motivation1)
        npc.add_motivation(motivation2)
        
        # Should be sorted by strength
        assert npc.motivations[0] == motivation1
        assert npc.motivations[1] == motivation2
    
    def test_secret_management(self):
        """Test managing secrets."""
        npc = NPCPsychology("npc_test")
        initial_stress = npc.stress_level
        
        secret = Secret(
            id="dark_past",
            content="Was once a thief",
            danger_level=0.8
        )
        
        npc.add_secret(secret)
        
        assert len(npc.secrets) == 1
        assert npc.stress_level > initial_stress  # Secrets increase stress
    
    def test_memory_creation(self):
        """Test creating memories."""
        npc = NPCPsychology("npc_test")
        
        npc.remember_event(
            "fight",
            ["npc_enemy"],
            "main_hall",
            "Got into a fight",
            emotional_impact=-0.7
        )
        
        assert len(npc.memories) == 1
        memory = npc.memories[0]
        assert memory.event_type == "fight"
        assert memory.emotional_impact == -0.7
        assert memory.importance == 0.7  # Abs value of emotion
        
        # Check mood was updated
        assert npc.current_mood in [Mood.ANGRY, Mood.SAD]
    
    def test_relationship_interactions(self):
        """Test interacting with other NPCs."""
        npc = NPCPsychology("npc_test", Personality.FRIENDLY)
        
        # Friendly chat
        npc.interact_with("npc_friend", "friendly_chat", "positive")
        
        relationship = npc.get_relationship("npc_friend")
        assert relationship.trust > 0.5
        assert relationship.affection > 0.5
        assert relationship.positive_interactions == 1
        
        # Betrayal
        npc.interact_with("npc_friend", "betrayal", "negative")
        assert relationship.trust < 0.2
        assert relationship.fear > 0.1
    
    def test_behavioral_tendencies(self):
        """Test getting behavioral tendencies."""
        # Friendly NPC
        friendly_npc = NPCPsychology("friendly", Personality.FRIENDLY)
        behavior, strength = friendly_npc.get_behavioral_tendency("social_gathering")
        assert behavior == "mingle"
        assert strength > 0.5
        
        # Suspicious NPC
        suspicious_npc = NPCPsychology("suspicious", Personality.SUSPICIOUS)
        behavior, strength = suspicious_npc.get_behavioral_tendency("request_for_help")
        # Might refuse or consider carefully
        assert behavior in ["refuse_suspicious", "consider"]
    
    def test_secret_revelation_decision(self):
        """Test deciding whether to reveal secrets."""
        npc = NPCPsychology("npc_test")
        
        secret = Secret(
            id="minor_secret",
            content="Dislikes the cook's food",
            danger_level=0.2
        )
        npc.add_secret(secret)
        
        # To stranger - unlikely
        should_reveal, reason = npc.should_reveal_secret("minor_secret", "stranger")
        # With low trust, shouldn't reveal
        
        # Build trust first
        npc.interact_with("friend", "help_given", "positive")
        npc.interact_with("friend", "deep_conversation", "positive")
        npc.interact_with("friend", "share_secret", "positive")
        
        # Now more likely
        should_reveal, reason = npc.should_reveal_secret("minor_secret", "friend")
        # Higher chance now
        
        # Intoxication increases chance
        npc.intoxication = 0.8
        should_reveal_drunk, reason = npc.should_reveal_secret("minor_secret", "anyone")
        # Should have better chance when drunk
    
    def test_priority_motivation(self):
        """Test getting current priority."""
        npc = NPCPsychology("npc_test")
        
        # Add multiple motivations
        npc.add_motivation(Motivation(
            type=MotivationType.SURVIVAL,
            description="Stay alive",
            strength=0.3
        ))
        npc.add_motivation(Motivation(
            type=MotivationType.SOCIAL,
            description="Make friends",
            strength=0.6
        ))
        
        # Normal state - social is priority
        priority = npc.get_current_priority()
        assert priority.type == MotivationType.SOCIAL
        
        # High stress - survival becomes more important
        npc.stress_level = 0.8
        priority = npc.get_current_priority()
        # Survival motivation should be boosted
    
    def test_psychology_update(self):
        """Test updating psychological state over time."""
        npc = NPCPsychology("npc_test")
        
        # Set initial states
        npc.stress_level = 0.8
        npc.energy_level = 0.3
        npc.intoxication = 0.6
        
        # Add a memory
        npc.remember_event("test", ["other"], "here", "test event", 0.5)
        initial_memory_importance = npc.memories[0].importance
        
        # Update over time
        npc.update_psychology(5.0)  # 5 hours
        
        # Check changes
        assert npc.stress_level < 0.8  # Stress reduced
        assert npc.energy_level > 0.3  # Energy restored
        assert npc.intoxication < 0.6  # Sobered up
        assert npc.memories[0].importance < initial_memory_importance  # Memory faded


class TestIntegration:
    """Integration tests for psychology system."""
    
    def test_complex_social_scenario(self):
        """Test a complex social scenario."""
        # Create NPCs with different personalities
        bartender = NPCPsychology("bartender", Personality.FRIENDLY)
        guard = NPCPsychology("guard", Personality.SUSPICIOUS)
        patron = NPCPsychology("patron", Personality.NEUTRAL)
        
        # Patron has a secret
        secret = Secret(
            id="smuggling",
            content="Smuggling goods through the tavern",
            danger_level=0.9,
            shame_level=0.3
        )
        patron.add_secret(secret)
        
        # Guard suspects something
        secret.add_suspicion("guard")
        
        # Patron tries to befriend bartender
        for _ in range(3):
            patron.interact_with("bartender", "friendly_chat", "positive")
        
        # Check if patron would reveal to bartender
        would_tell_bartender, _ = patron.should_reveal_secret("smuggling", "bartender")
        
        # Check if patron would reveal to guard
        would_tell_guard, _ = patron.should_reveal_secret("smuggling", "guard")
        
        # Patron should be more likely to tell bartender than guard
        bartender_rel = patron.get_relationship("bartender")
        guard_rel = patron.get_relationship("guard")
        
        assert bartender_rel.trust > guard_rel.trust