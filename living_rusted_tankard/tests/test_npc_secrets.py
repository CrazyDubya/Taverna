"""Tests for the enhanced secrets system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from core.npc_systems.secrets import (
    EnhancedSecret,
    SecretType,
    SecretState,
    Evidence,
    EvidenceType,
    SecretConsequence,
    SecretProtection,
    SecretGenerator,
)


class TestEvidence:
    """Test Evidence functionality."""

    def test_evidence_creation(self):
        """Test creating evidence."""
        evidence = Evidence(
            id="test_evidence",
            type=EvidenceType.DOCUMENT,
            description="Incriminating letter",
            location="hidden_drawer",
            reliability=0.8,
            discovery_difficulty=0.6,
        )

        assert evidence.id == "test_evidence"
        assert evidence.type == EvidenceType.DOCUMENT
        assert evidence.reliability == 0.8
        assert not evidence.is_discovered_by("anyone")

    def test_evidence_discovery(self):
        """Test discovering evidence."""
        evidence = Evidence(
            id="test_evidence", type=EvidenceType.PHYSICAL, description="Bloody knife"
        )

        # Discover evidence
        evidence.discover("investigator")
        assert evidence.is_discovered_by("investigator")
        assert "investigator" in evidence.discovered_by

        # Multiple discoverers
        evidence.discover("guard")
        assert len(evidence.discovered_by) == 2

    def test_revelation_value(self):
        """Test calculating revelation value."""
        evidence = Evidence(
            id="test",
            type=EvidenceType.WITNESS,
            description="Saw the crime",
            reliability=0.9,
            revelation_power=0.7,
        )

        value = evidence.get_revelation_value()
        assert value == pytest.approx(0.63)  # 0.9 * 0.7


class TestEnhancedSecret:
    """Test EnhancedSecret functionality."""

    def test_secret_creation(self):
        """Test creating a secret."""
        secret = EnhancedSecret(
            id="test_secret",
            type=SecretType.CRIMINAL,
            content="Stole from the merchant",
            holder_id="npc_thie",
            danger_level=0.8,
            criminal_level=0.9,
        )

        assert secret.id == "test_secret"
        assert secret.type == SecretType.CRIMINAL
        assert secret.state == SecretState.HIDDEN
        assert secret.revelation_progress == 0.0

    def test_adding_evidence(self):
        """Test adding evidence to a secret."""
        secret = EnhancedSecret(
            id="test_secret",
            type=SecretType.FINANCIAL,
            content="Embezzling funds",
            holder_id="npc_treasurer",
        )

        evidence = Evidence(
            id="ledger",
            type=EvidenceType.DOCUMENT,
            description="Falsified ledger",
            revelation_power=0.4,
        )

        initial_progress = secret.revelation_progress
        secret.add_evidence(evidence)

        assert evidence in secret.evidence_trail
        assert secret.revelation_progress > initial_progress

    def test_suspicion_system(self):
        """Test the suspicion system."""
        secret = EnhancedSecret(
            id="test_secret",
            type=SecretType.ROMANTIC,
            content="Having an affair",
            holder_id="npc_spouse",
        )

        # Add suspicion
        secret.add_suspicion("npc_friend", 0.3)
        assert "npc_friend" in secret.suspected_by
        assert secret.suspected_by["npc_friend"] == 0.3

        # Increase suspicion
        secret.add_suspicion("npc_friend", 0.4)
        assert secret.suspected_by["npc_friend"] == 0.7

        # High suspicion triggers investigation
        assert "npc_friend" in secret.investigating

        # State should update
        assert secret.state == SecretState.SUSPECTED

    def test_investigation_system(self):
        """Test investigating a secret."""
        secret = EnhancedSecret(
            id="test_secret",
            type=SecretType.CRIMINAL,
            content="Smuggling operation",
            holder_id="npc_smuggler",
        )

        # Add evidence
        evidence1 = Evidence(
            id="evidence1",
            type=EvidenceType.PHYSICAL,
            description="Hidden contraband",
            discovery_difficulty=0.3,
            revelation_power=0.5,
        )
        evidence2 = Evidence(
            id="evidence2",
            type=EvidenceType.WITNESS,
            description="Saw suspicious activity",
            discovery_difficulty=0.7,
            revelation_power=0.3,
        )

        secret.add_evidence(evidence1)
        secret.add_evidence(evidence2)

        # Investigate with high skill
        found = secret.investigate("investigator", skill_level=0.8)

        # Should find at least the easier evidence
        assert len(found) >= 1
        assert any(e.id == "evidence1" for e in found)

        # Investigator added to investigating list
        assert "investigator" in secret.investigating

        # State should progress
        assert secret.state != SecretState.HIDDEN

    def test_protection_system(self):
        """Test secret protection."""
        secret = EnhancedSecret(
            id="test_secret",
            type=SecretType.POLITICAL,
            content="Plotting against the lord",
            holder_id="npc_conspirator",
        )

        # Add protection
        protection = SecretProtection(
            method="bribery", target="guards", effectiveness=0.6, cost={"gold": 100}
        )

        secret.add_protection(protection)
        assert protection in secret.protections

        # Protection reduces discovery chance
        base_chance = 0.5
        protected_chance = protection.apply(base_chance)
        assert protected_chance < base_chance
        assert protected_chance == pytest.approx(0.2)  # 0.5 * (1 - 0.6)

    def test_revelation_and_consequences(self):
        """Test revealing secrets and consequences."""
        secret = EnhancedSecret(
            id="test_secret",
            type=SecretType.CRIMINAL,
            content="Murdered someone",
            holder_id="npc_killer",
            danger_level=1.0,
        )

        # Add consequences
        consequence = SecretConsequence(
            description="Arrest and execution",
            severity=1.0,
            triggers_event="guard_arrest",
        )
        secret.consequences.append(consequence)

        # Partial revelation
        secret.reveal_to("npc_witness", partial=True)
        assert "npc_witness" in secret.suspected_by
        assert "npc_witness" not in secret.known_by

        # Full revelation
        secret.reveal_to("npc_guard", partial=False)
        assert "npc_guard" in secret.known_by
        assert len(secret.exposure_events) == 1

        # Check total consequences
        assert secret.get_total_consequences() == 1.0

    def test_discovery_risk(self):
        """Test calculating discovery risk."""
        secret = EnhancedSecret(
            id="test_secret",
            type=SecretType.PERSONAL,
            content="Hidden illness",
            holder_id="npc_sick",
        )

        # Initial risk should be low
        assert secret.get_discovery_risk() < 0.1

        # Add suspicions
        secret.add_suspicion("npc1", 0.5)
        secret.add_suspicion("npc2", 0.8)

        # Risk increases
        risk_with_suspicion = secret.get_discovery_risk()
        assert risk_with_suspicion > 0.1

        # Add investigation
        secret.investigating.add("npc3")

        # Risk increases more
        risk_with_investigation = secret.get_discovery_risk()
        assert risk_with_investigation > risk_with_suspicion

        # Add protection
        protection = SecretProtection(method="misdirection", effectiveness=0.5)
        secret.add_protection(protection)

        # Risk decreases
        final_risk = secret.get_discovery_risk()
        assert final_risk < risk_with_investigation

    def test_state_transitions(self):
        """Test secret state transitions."""
        secret = EnhancedSecret(
            id="test_secret",
            type=SecretType.FINANCIAL,
            content="Hidden treasure",
            holder_id="npc_miser",
        )

        # Initially hidden
        assert secret.state == SecretState.HIDDEN

        # Add suspicion -> suspected
        secret.add_suspicion("npc1", 0.3)
        assert secret.state == SecretState.SUSPECTED

        # Add investigation -> investigated
        secret.investigating.add("npc1")
        secret._update_state()
        assert secret.state == SecretState.INVESTIGATED

        # Progress revelation -> exposed
        secret.revelation_progress = 0.6
        secret._update_state()
        assert secret.state == SecretState.EXPOSED

        # Many know -> revealed
        secret.known_by.update(["npc1", "npc2", "npc3"])
        secret._update_state()
        assert secret.state == SecretState.REVEALED

    def test_false_evidence(self):
        """Test creating false evidence."""
        secret = EnhancedSecret(
            id="test_secret",
            type=SecretType.ROMANTIC,
            content="Secret lover",
            holder_id="npc_lover",
        )

        # Create false evidence
        false_ev = secret.create_false_evidence(
            "Forged love letter", EvidenceType.DOCUMENT
        )

        assert false_ev in secret.false_evidence
        assert false_ev.reliability < 0.5
        assert false_ev.revelation_power == 0.0
        assert not false_ev.can_be_faked  # Already fake


class TestSecretGenerator:
    """Test SecretGenerator functionality."""

    def test_generate_merchant_secret(self):
        """Test generating secrets for merchants."""
        npc_data = {"id": "npc_merchant", "occupation": "merchant"}

        secret = SecretGenerator.generate_secret(npc_data)

        assert secret.holder_id == "npc_merchant"
        assert secret.type in [
            SecretType.FINANCIAL,
            SecretType.CRIMINAL,
            SecretType.PROFESSIONAL,
        ]
        assert len(secret.evidence_trail) > 0
        assert len(secret.consequences) > 0

    def test_generate_specific_type(self):
        """Test generating specific secret type."""
        npc_data = {"id": "npc_test"}

        secret = SecretGenerator.generate_secret(
            npc_data, secret_type=SecretType.ROMANTIC
        )

        assert secret.type == SecretType.ROMANTIC
        assert "affair" in secret.content.lower() or "love" in secret.content.lower()

    def test_evidence_generation(self):
        """Test evidence trail generation."""
        npc_data = {"id": "npc_criminal"}

        secret = SecretGenerator.generate_secret(
            npc_data, secret_type=SecretType.CRIMINAL
        )

        # Should have multiple evidence pieces
        assert len(secret.evidence_trail) >= 2

        # Evidence should have variety
        evidence_types = {e.type for e in secret.evidence_trail}
        assert len(evidence_types) > 1

        # High danger secrets have more evidence
        if secret.danger_level > 0.7:
            assert len(secret.evidence_trail) >= 3

    def test_consequence_generation(self):
        """Test consequence generation."""
        npc_data = {"id": "npc_test"}

        # Criminal secret should have legal consequences
        criminal_secret = SecretGenerator.generate_secret(
            npc_data, secret_type=SecretType.CRIMINAL
        )

        legal_consequences = [
            c
            for c in criminal_secret.consequences
            if "legal" in c.description.lower() or "arrest" in c.description.lower()
        ]
        assert len(legal_consequences) > 0

        # Romantic secret should have relationship consequences
        romantic_secret = SecretGenerator.generate_secret(
            npc_data, secret_type=SecretType.ROMANTIC
        )

        relationship_consequences = [
            c for c in romantic_secret.consequences if len(c.affects_relationships) > 0
        ]
        assert len(relationship_consequences) > 0


class TestIntegration:
    """Integration tests for secrets system."""

    def test_complete_secret_lifecycle(self):
        """Test complete secret lifecycle from creation to revelation."""
        # Generate secret
        npc_data = {"id": "npc_criminal", "occupation": "merchant"}
        secret = SecretGenerator.generate_secret(
            npc_data, secret_type=SecretType.CRIMINAL
        )

        # Initial state
        assert secret.state == SecretState.HIDDEN
        assert len(secret.known_by) == 0

        # Someone becomes suspicious
        secret.add_suspicion("npc_guard", 0.4)
        assert secret.state == SecretState.SUSPECTED

        # Guard investigates
        found_evidence = secret.investigate("npc_guard", skill_level=0.7)
        assert secret.state == SecretState.INVESTIGATED

        # Evidence builds up
        for _ in range(3):
            secret.investigate("npc_guard", skill_level=0.8)

        # Should be exposed or revealed
        assert secret.state in [SecretState.EXPOSED, SecretState.REVEALED]

        # Full revelation
        secret.reveal_to("npc_captain")

        # Check consequences
        total_severity = secret.get_total_consequences()
        assert total_severity > 0

        # Should protect if dangerous
        assert secret.should_protect()

    def test_multiple_investigators(self):
        """Test multiple NPCs investigating same secret."""
        secret = EnhancedSecret(
            id="conspiracy",
            type=SecretType.POLITICAL,
            content="Planning rebellion",
            holder_id="npc_rebel",
        )

        # Add complex evidence trail
        for i in range(5):
            evidence = Evidence(
                id=f"evidence_{i}",
                type=EvidenceType.DOCUMENT,
                description=f"Clue {i}",
                discovery_difficulty=0.3 + i * 0.1,
                revelation_power=0.2,
            )
            secret.add_evidence(evidence)

        # Multiple investigators
        investigators = ["guard1", "guard2", "spy"]
        all_found = []

        for investigator in investigators:
            found = secret.investigate(investigator, skill_level=0.6)
            all_found.extend(found)

        # Different investigators might find different evidence
        assert len(all_found) > 0

        # All should be investigating
        assert all(inv in secret.investigating for inv in investigators)

        # Progress should advance
        assert secret.revelation_progress > 0

        # State should progress
        assert secret.state != SecretState.HIDDEN
