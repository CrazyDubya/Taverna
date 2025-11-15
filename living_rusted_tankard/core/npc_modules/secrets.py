"""Enhanced secrets and evidence system for NPCs."""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random


class SecretType(Enum):
    """Types of secrets NPCs can hold."""

    CRIMINAL = "criminal"
    ROMANTIC = "romantic"
    FINANCIAL = "financial"
    POLITICAL = "political"
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    SUPERNATURAL = "supernatural"
    HISTORICAL = "historical"


class EvidenceType(Enum):
    """Types of evidence that can reveal secrets."""

    PHYSICAL = "physical"  # Objects, items
    WITNESS = "witness"  # Someone saw something
    DOCUMENT = "document"  # Written evidence
    RUMOR = "rumor"  # Hearsay
    BEHAVIOR = "behavior"  # Suspicious actions
    CONFESSION = "confession"  # Direct admission
    MAGICAL = "magical"  # Divination, truth spells


class SecretState(Enum):
    """Current state of a secret."""

    HIDDEN = "hidden"  # Completely unknown
    SUSPECTED = "suspected"  # Some have suspicions
    INVESTIGATED = "investigated"  # Actively being investigated
    EXPOSED = "exposed"  # Partially revealed
    REVEALED = "revealed"  # Fully known
    RESOLVED = "resolved"  # Dealt with


@dataclass
class Evidence:
    """A piece of evidence related to a secret."""

    id: str
    type: EvidenceType
    description: str
    location: Optional[str] = None
    holder: Optional[str] = None  # Who has this evidence
    reliability: float = 0.7  # 0-1, how trustworthy
    discovered_by: Set[str] = field(default_factory=set)
    created: datetime = field(default_factory=datetime.now)

    # Discovery conditions
    discovery_difficulty: float = 0.5  # 0-1, how hard to find
    requires_skill: Optional[str] = None  # e.g., "investigation", "persuasion"
    requires_relationship: Optional[float] = None  # Min relationship level

    # Impact
    revelation_power: float = 0.3  # How much this reveals (0-1)
    can_be_destroyed: bool = True
    can_be_faked: bool = True

    def is_discovered_by(self, character_id: str) -> bool:
        """Check if character has discovered this evidence."""
        return character_id in self.discovered_by

    def discover(self, character_id: str) -> None:
        """Mark evidence as discovered by character."""
        self.discovered_by.add(character_id)

    def get_revelation_value(self) -> float:
        """Get how much this evidence reveals, modified by reliability."""
        return self.revelation_power * self.reliability


@dataclass
class SecretConsequence:
    """Consequences of a secret being revealed."""

    description: str
    severity: float = 0.5  # 0-1
    affects_reputation: bool = True
    affects_relationships: List[str] = field(default_factory=list)
    triggers_event: Optional[str] = None
    creates_conflict: Optional[str] = None

    # Mitigation
    can_be_mitigated: bool = True
    mitigation_conditions: List[str] = field(default_factory=list)


@dataclass
class SecretProtection:
    """Ways an NPC protects their secret."""

    method: str  # "bribery", "threats", "misdirection", etc.
    target: Optional[str] = None  # Who/what is targeted
    effectiveness: float = 0.5  # 0-1
    cost: Dict[str, Any] = field(default_factory=dict)  # Resources spent
    active: bool = True

    def apply(self, discovery_chance: float) -> float:
        """Apply protection to reduce discovery chance."""
        if self.active:
            return discovery_chance * (1.0 - self.effectiveness)
        return discovery_chance


@dataclass
class EnhancedSecret:
    """Enhanced secret with full discovery and evidence system."""

    id: str
    type: SecretType
    content: str
    holder_id: str  # Who has this secret

    # Danger and impact
    danger_level: float = 0.5  # 0-1, consequences if revealed
    shame_level: float = 0.5  # 0-1, personal shame
    criminal_level: float = 0.0  # 0-1, legal consequences

    # State tracking
    state: SecretState = SecretState.HIDDEN
    revelation_progress: float = 0.0  # 0-1, how close to revealed

    # Who knows what
    known_by: Set[str] = field(default_factory=set)  # Fully know
    suspected_by: Dict[str, float] = field(default_factory=dict)  # ID -> suspicion level
    investigating: Set[str] = field(default_factory=set)  # Actively investigating

    # Evidence
    evidence_trail: List[Evidence] = field(default_factory=list)
    false_evidence: List[Evidence] = field(default_factory=list)  # Red herrings

    # Consequences
    consequences: List[SecretConsequence] = field(default_factory=list)

    # Protection
    protections: List[SecretProtection] = field(default_factory=list)
    cover_stories: List[str] = field(default_factory=list)

    # History
    created: datetime = field(default_factory=datetime.now)
    last_investigated: Optional[datetime] = None
    exposure_events: List[Tuple[datetime, str, str]] = field(default_factory=list)  # (when, who, what)

    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence to the trail."""
        self.evidence_trail.append(evidence)
        # Evidence might advance revelation
        self.revelation_progress = min(1.0, self.revelation_progress + evidence.revelation_power * 0.5)
        self._update_state()

    def add_suspicion(self, character_id: str, amount: float = 0.1) -> None:
        """Increase someone's suspicion level."""
        if character_id in self.known_by:
            return  # Already knows

        current = self.suspected_by.get(character_id, 0.0)
        self.suspected_by[character_id] = min(1.0, current + amount)

        # High suspicion might trigger investigation
        if self.suspected_by[character_id] > 0.6:
            self.investigating.add(character_id)

        self._update_state()

    def investigate(self, investigator_id: str, skill_level: float = 0.5) -> List[Evidence]:
        """Investigate the secret, potentially finding evidence."""
        if investigator_id not in self.investigating:
            self.investigating.add(investigator_id)

        self.last_investigated = datetime.now()
        found_evidence = []

        # Check each piece of evidence
        for evidence in self.evidence_trail:
            if evidence.is_discovered_by(investigator_id):
                continue  # Already found

            # Calculate discovery chance
            base_chance = skill_level * (1.0 - evidence.discovery_difficulty)

            # Apply protections
            for protection in self.protections:
                base_chance = protection.apply(base_chance)

            # Check discovery
            if random.random() < base_chance:
                evidence.discover(investigator_id)
                found_evidence.append(evidence)

                # Update revelation progress
                self.revelation_progress = min(1.0, self.revelation_progress + evidence.get_revelation_value())

        # Might also find false evidence
        for false_ev in self.false_evidence:
            if not false_ev.is_discovered_by(investigator_id):
                if random.random() < skill_level * 0.3:  # Lower chance
                    false_ev.discover(investigator_id)
                    found_evidence.append(false_ev)

        self._update_state()
        return found_evidence

    def reveal_to(self, character_id: str, partial: bool = False) -> None:
        """Reveal secret to someone."""
        if partial:
            self.add_suspicion(character_id, 0.5)
        else:
            self.known_by.add(character_id)
            if character_id in self.suspected_by:
                del self.suspected_by[character_id]
            if character_id in self.investigating:
                self.investigating.remove(character_id)

            self.exposure_events.append((datetime.now(), character_id, "full_revelation"))

        self._update_state()

    def add_protection(self, protection: SecretProtection) -> None:
        """Add a protection method."""
        self.protections.append(protection)

    def create_false_evidence(self, description: str, evidence_type: EvidenceType = EvidenceType.DOCUMENT) -> Evidence:
        """Create false evidence to mislead investigators."""
        false_ev = Evidence(
            id=f"{self.id}_false_{len(self.false_evidence)}",
            type=evidence_type,
            description=description,
            reliability=0.3,  # Might be detected as false
            revelation_power=0.0,  # Doesn't actually reveal truth
            can_be_faked=False,  # Already fake
        )
        self.false_evidence.append(false_ev)
        return false_ev

    def _update_state(self) -> None:
        """Update secret state based on current conditions."""
        # Count suspicions and investigations
        high_suspicions = sum(1 for level in self.suspected_by.values() if level > 0.7)

        if self.state == SecretState.HIDDEN:
            if len(self.suspected_by) > 0:
                self.state = SecretState.SUSPECTED

        elif self.state == SecretState.SUSPECTED:
            if len(self.investigating) > 0:
                self.state = SecretState.INVESTIGATED
            elif len(self.suspected_by) == 0:
                self.state = SecretState.HIDDEN

        elif self.state == SecretState.INVESTIGATED:
            if self.revelation_progress > 0.5:
                self.state = SecretState.EXPOSED
            elif len(self.investigating) == 0:
                self.state = SecretState.SUSPECTED

        elif self.state == SecretState.EXPOSED:
            if self.revelation_progress > 0.8 or len(self.known_by) > 2:
                self.state = SecretState.REVEALED

        # Can be marked resolved externally

    def get_discovery_risk(self) -> float:
        """Calculate current risk of discovery."""
        base_risk = 0.0

        # Suspicions increase risk
        base_risk += sum(self.suspected_by.values()) * 0.1

        # Investigations greatly increase risk
        base_risk += len(self.investigating) * 0.2

        # Evidence discovery increases risk
        discovered_evidence = sum(1 for ev in self.evidence_trail if len(ev.discovered_by) > 0)
        base_risk += discovered_evidence * 0.15

        # Protections reduce risk
        for protection in self.protections:
            if protection.active:
                base_risk *= 1.0 - protection.effectiveness * 0.5

        return min(1.0, base_risk)

    def get_total_consequences(self) -> float:
        """Calculate total consequence severity."""
        if not self.consequences:
            return self.danger_level

        total = sum(c.severity for c in self.consequences)
        return min(1.0, total / len(self.consequences))

    def should_protect(self) -> bool:
        """Determine if NPC should actively protect this secret."""
        # High danger secrets should be protected
        if self.danger_level > 0.7:
            return True

        # Protect if discovery risk is high
        if self.get_discovery_risk() > 0.5:
            return True

        # Protect if consequences are severe
        if self.get_total_consequences() > 0.6:
            return True

        return False


class SecretGenerator:
    """Generates secrets for NPCs based on context."""

    @staticmethod
    def generate_secret(npc_data: Dict[str, Any], secret_type: Optional[SecretType] = None) -> EnhancedSecret:
        """Generate a contextual secret for an NPC."""
        if secret_type is None:
            # Choose based on NPC role
            occupation = npc_data.get("occupation", "patron")
            if occupation in ["merchant", "trader"]:
                secret_type = random.choice([SecretType.FINANCIAL, SecretType.CRIMINAL, SecretType.PROFESSIONAL])
            elif occupation in ["guard", "soldier"]:
                secret_type = random.choice([SecretType.CRIMINAL, SecretType.POLITICAL, SecretType.PERSONAL])
            elif occupation in ["bartender", "cook", "staff"]:
                secret_type = random.choice([SecretType.PERSONAL, SecretType.ROMANTIC, SecretType.PROFESSIONAL])
            else:
                secret_type = random.choice(list(SecretType))

        # Generate appropriate secret
        secret_templates = {
            SecretType.CRIMINAL: [
                ("Smuggling goods through the tavern", 0.8, 0.6),
                ("Stole from a previous employer", 0.6, 0.7),
                ("Involved in illegal gambling ring", 0.7, 0.5),
                ("Sells information to criminals", 0.9, 0.4),
            ],
            SecretType.ROMANTIC: [
                ("Having an affair", 0.6, 0.8),
                ("In love with someone inappropriate", 0.4, 0.7),
                ("Hiding a past marriage", 0.5, 0.6),
                ("Secret admirer of a regular patron", 0.3, 0.9),
            ],
            SecretType.FINANCIAL: [
                ("Deeply in debt to dangerous people", 0.8, 0.6),
                ("Embezzling funds", 0.9, 0.7),
                ("Hidden wealth from illegal sources", 0.7, 0.5),
                ("Bankrupt but maintaining appearances", 0.5, 0.8),
            ],
            SecretType.PERSONAL: [
                ("Hiding true identity", 0.7, 0.7),
                ("Addicted to substances", 0.5, 0.8),
                ("Suffering from a hidden illness", 0.4, 0.9),
                ("Haunted by past trauma", 0.3, 0.7),
            ],
        }

        # Get random template
        templates = secret_templates.get(secret_type, [("Has a dark secret", 0.5, 0.5)])
        content, danger, shame = random.choice(templates)

        # Create secret
        secret = EnhancedSecret(
            id=f"{npc_data.get('id', 'npc')}_secret_{random.randint(1000, 9999)}",
            type=secret_type,
            content=content,
            holder_id=npc_data.get("id", "unknown"),
            danger_level=danger,
            shame_level=shame,
            criminal_level=danger * 0.7 if secret_type == SecretType.CRIMINAL else 0.0,
        )

        # Add initial evidence
        secret.evidence_trail.extend(SecretGenerator._generate_evidence_trail(secret))

        # Add consequences
        secret.consequences.extend(SecretGenerator._generate_consequences(secret))

        return secret

    @staticmethod
    def _generate_evidence_trail(secret: EnhancedSecret) -> List[Evidence]:
        """Generate evidence for a secret."""
        evidence_list = []

        # Number of evidence pieces based on danger
        num_evidence = random.randint(2, 5)
        if secret.danger_level > 0.7:
            num_evidence = random.randint(3, 6)

        for i in range(num_evidence):
            ev_type = random.choice(list(EvidenceType))

            if ev_type == EvidenceType.PHYSICAL:
                evidence = Evidence(
                    id=f"{secret.id}_evidence_{i}",
                    type=ev_type,
                    description=f"Physical evidence of {secret.type.value} activity",
                    location=random.choice(["private_room", "hidden_spot", "storage"]),
                    discovery_difficulty=0.7,
                    revelation_power=0.4,
                )
            elif ev_type == EvidenceType.WITNESS:
                evidence = Evidence(
                    id=f"{secret.id}_evidence_{i}",
                    type=ev_type,
                    description=f"Someone who saw suspicious behavior",
                    holder=f"witness_{i}",
                    discovery_difficulty=0.6,
                    requires_relationship=0.5,
                    revelation_power=0.5,
                )
            elif ev_type == EvidenceType.DOCUMENT:
                evidence = Evidence(
                    id=f"{secret.id}_evidence_{i}",
                    type=ev_type,
                    description=f"Incriminating documents",
                    location="hidden_compartment",
                    discovery_difficulty=0.8,
                    requires_skill="investigation",
                    revelation_power=0.6,
                )
            else:
                evidence = Evidence(
                    id=f"{secret.id}_evidence_{i}",
                    type=ev_type,
                    description=f"Evidence pointing to the secret",
                    discovery_difficulty=0.5,
                    revelation_power=0.3,
                )

            evidence_list.append(evidence)

        return evidence_list

    @staticmethod
    def _generate_consequences(secret: EnhancedSecret) -> List[SecretConsequence]:
        """Generate consequences for revealing a secret."""
        consequences = []

        # Base consequence
        consequences.append(
            SecretConsequence(
                description=f"Reputation damaged by {secret.type.value} revelation",
                severity=secret.danger_level,
                affects_reputation=True,
            )
        )

        # Type-specific consequences
        if secret.type == SecretType.CRIMINAL:
            consequences.append(
                SecretConsequence(
                    description="Legal action and possible arrest",
                    severity=secret.criminal_level,
                    triggers_event="guard_investigation",
                    can_be_mitigated=False,
                )
            )

        elif secret.type == SecretType.ROMANTIC:
            consequences.append(
                SecretConsequence(
                    description="Relationship conflicts and drama",
                    severity=secret.shame_level,
                    affects_relationships=["lover", "spouse", "family"],
                    creates_conflict="romantic_drama",
                )
            )

        elif secret.type == SecretType.FINANCIAL:
            consequences.append(
                SecretConsequence(
                    description="Financial ruin and debt collection",
                    severity=secret.danger_level,
                    triggers_event="debt_collection",
                    can_be_mitigated=True,
                    mitigation_conditions=["pay_debts", "flee_town"],
                )
            )

        return consequences


class SecretsManager:
    """Manager for NPC secrets system"""

    def __init__(self):
        self.npc_secrets: Dict[str, List[EnhancedSecret]] = {}
        self.discovered_secrets: Dict[str, List[str]] = {}  # player_id -> secret_ids

    def initialize_npc_secrets(self, npc_id: str) -> None:
        """Initialize secrets for an NPC"""
        if npc_id not in self.npc_secrets:
            # Create a default secret for NPCs that should have one
            secret = EnhancedSecret(
                id=f"{npc_id}_default_secret",
                content=f"{npc_id} has a mysterious past",
                type=SecretType.PERSONAL,
                danger_level=0.5,
                shame_level=0.3,
                evidence_required=3,
            )
            self.npc_secrets[npc_id] = [secret]

    def npc_has_secrets(self, npc_id: str) -> bool:
        """Check if an NPC has any secrets"""
        return npc_id in self.npc_secrets and len(self.npc_secrets[npc_id]) > 0

    def get_npc_secrets(self, npc_id: str) -> List[EnhancedSecret]:
        """Get all secrets for an NPC"""
        return self.npc_secrets.get(npc_id, [])

    def discover_secret(self, player_id: str, secret_id: str) -> bool:
        """Record that a player discovered a secret"""
        if player_id not in self.discovered_secrets:
            self.discovered_secrets[player_id] = []

        if secret_id not in self.discovered_secrets[player_id]:
            self.discovered_secrets[player_id].append(secret_id)
            return True
        return False

    def is_secret_discovered(self, player_id: str, secret_id: str) -> bool:
        """Check if a player has discovered a specific secret"""
        return player_id in self.discovered_secrets and secret_id in self.discovered_secrets[player_id]
