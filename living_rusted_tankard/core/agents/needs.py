"""
Needs and Drives System for Deep Agents.

Implements:
- Physiological needs (hunger, fatigue, pain)
- Psychological drives (achievement, belonging, autonomy)
- Need satisfaction and urgency

Needs create motivation - when a need is unmet, it becomes a drive
that pushes the agent toward goal formation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import time


class NeedType(Enum):
    """Categories of needs."""

    # Physiological (Maslow's hierarchy base)
    HUNGER = "hunger"
    THIRST = "thirst"
    REST = "rest"
    SAFETY = "safety"
    HEALTH = "health"

    # Psychological
    BELONGING = "belonging"  # Social connection
    ACHIEVEMENT = "achievement"  # Accomplish goals
    AUTONOMY = "autonomy"  # Self-determination
    COMPETENCE = "competence"  # Feel capable
    CURIOSITY = "curiosity"  # Learn and explore

    # Social
    RESPECT = "respect"  # Be valued by others
    INTIMACY = "intimacy"  # Close relationships
    PURPOSE = "purpose"  # Meaningful existence


@dataclass
class Need:
    """
    A single need that can be satisfied or unmet.

    Needs have:
    - Current level (0.0 = completely unmet, 1.0 = fully satisfied)
    - Decay rate (how quickly satisfaction decreases)
    - Urgency threshold (when it becomes pressing)
    """

    need_type: NeedType
    level: float = 0.5  # Current satisfaction (0.0-1.0)
    decay_rate: float = 0.01  # How much it decreases per hour
    urgency_threshold: float = 0.3  # Below this, becomes urgent
    critical_threshold: float = 0.1  # Below this, dominates behavior

    last_updated: float = field(default_factory=time.time)

    def update(self, hours_passed: float) -> None:
        """Update need level based on time passage."""
        decay = self.decay_rate * hours_passed
        self.level = max(0.0, self.level - decay)
        self.last_updated = time.time()

    def satisfy(self, amount: float) -> None:
        """Satisfy the need by some amount."""
        self.level = min(1.0, self.level + amount)
        self.last_updated = time.time()

    def is_urgent(self) -> bool:
        """Check if need is urgent."""
        return self.level < self.urgency_threshold

    def is_critical(self) -> bool:
        """Check if need is critical (dominates behavior)."""
        return self.level < self.critical_threshold

    def get_urgency(self) -> float:
        """
        Get urgency level (0.0-1.0).

        0.0 = satisfied
        1.0 = critical
        """
        if self.level >= self.urgency_threshold:
            return 0.0

        # Map from urgency_threshold to 0 → 0.0 to 1.0
        urgency_range = self.urgency_threshold
        return 1.0 - (self.level / urgency_range)

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "need_type": self.need_type.value,
            "level": self.level,
            "decay_rate": self.decay_rate,
            "urgency_threshold": self.urgency_threshold,
            "critical_threshold": self.critical_threshold,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Need":
        """Deserialize from saved data."""
        data["need_type"] = NeedType(data["need_type"])
        return cls(**data)


@dataclass
class PhysiologicalNeeds:
    """
    Collection of all physiological and psychological needs.

    Updates automatically with time passage and provides
    methods to query which needs are most urgent.
    """

    needs: Dict[NeedType, Need] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize with default needs if not provided."""
        if not self.needs:
            self.needs = self._create_default_needs()

    def _create_default_needs(self) -> Dict[NeedType, Need]:
        """Create standard set of needs."""
        return {
            # Physiological needs (decay faster)
            NeedType.HUNGER: Need(
                NeedType.HUNGER,
                level=0.8,
                decay_rate=0.04,  # Gets hungry quickly
                urgency_threshold=0.4,
                critical_threshold=0.2,
            ),
            NeedType.REST: Need(
                NeedType.REST,
                level=0.8,
                decay_rate=0.03,  # Gets tired over time
                urgency_threshold=0.3,
                critical_threshold=0.15,
            ),
            NeedType.SAFETY: Need(
                NeedType.SAFETY,
                level=0.9,
                decay_rate=0.0,  # Only changes with events
                urgency_threshold=0.5,
                critical_threshold=0.3,
            ),
            NeedType.HEALTH: Need(
                NeedType.HEALTH,
                level=1.0,
                decay_rate=0.0,  # Only changes with damage/healing
                urgency_threshold=0.6,
                critical_threshold=0.3,
            ),
            # Psychological needs (decay slower)
            NeedType.BELONGING: Need(
                NeedType.BELONGING,
                level=0.6,
                decay_rate=0.005,  # Slowly needs social contact
                urgency_threshold=0.4,
                critical_threshold=0.2,
            ),
            NeedType.ACHIEVEMENT: Need(
                NeedType.ACHIEVEMENT,
                level=0.5,
                decay_rate=0.003,  # Wants to accomplish things
                urgency_threshold=0.3,
                critical_threshold=0.1,
            ),
            NeedType.AUTONOMY: Need(
                NeedType.AUTONOMY,
                level=0.7,
                decay_rate=0.002,  # Need for control
                urgency_threshold=0.4,
                critical_threshold=0.2,
            ),
            NeedType.CURIOSITY: Need(
                NeedType.CURIOSITY,
                level=0.5,
                decay_rate=0.01,  # Wants novelty
                urgency_threshold=0.3,
                critical_threshold=0.1,
            ),
            NeedType.RESPECT: Need(
                NeedType.RESPECT,
                level=0.6,
                decay_rate=0.002,  # Wants validation
                urgency_threshold=0.4,
                critical_threshold=0.2,
            ),
        }

    def update(self, hours_passed: float) -> None:
        """Update all needs based on time passage."""
        for need in self.needs.values():
            need.update(hours_passed)

    def get_need(self, need_type: NeedType) -> Optional[Need]:
        """Get a specific need."""
        return self.needs.get(need_type)

    def satisfy_need(self, need_type: NeedType, amount: float) -> None:
        """Satisfy a specific need."""
        if need_type in self.needs:
            self.needs[need_type].satisfy(amount)

    def get_urgent_needs(self) -> List[Need]:
        """Get all urgent needs, sorted by urgency."""
        urgent = [need for need in self.needs.values() if need.is_urgent()]
        return sorted(urgent, key=lambda n: n.get_urgency(), reverse=True)

    def get_critical_needs(self) -> List[Need]:
        """Get all critical needs."""
        return [need for need in self.needs.values() if need.is_critical()]

    def get_most_urgent_need(self) -> Optional[Need]:
        """Get the single most urgent need."""
        urgent = self.get_urgent_needs()
        return urgent[0] if urgent else None

    def get_overall_wellbeing(self) -> float:
        """
        Calculate overall wellbeing score (0.0-1.0).

        Weighted average of all needs, with physiological
        needs weighted more heavily.
        """
        if not self.needs:
            return 0.5

        weights = {
            NeedType.HUNGER: 1.5,
            NeedType.REST: 1.5,
            NeedType.SAFETY: 2.0,
            NeedType.HEALTH: 2.0,
            # Psychological needs have weight 1.0 (default)
        }

        total_score = 0.0
        total_weight = 0.0

        for need_type, need in self.needs.items():
            weight = weights.get(need_type, 1.0)
            total_score += need.level * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.5

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "needs": {
                need_type.value: need.to_dict()
                for need_type, need in self.needs.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PhysiologicalNeeds":
        """Deserialize from saved data."""
        needs = {
            NeedType(need_type): Need.from_dict(need_data)
            for need_type, need_data in data.get("needs", {}).items()
        }
        return cls(needs=needs)

    def __repr__(self) -> str:
        urgent = self.get_urgent_needs()
        wellbeing = self.get_overall_wellbeing()

        if urgent:
            urgent_str = ", ".join(n.need_type.value for n in urgent[:3])
            return f"Needs(wellbeing={wellbeing:.2f}, urgent=[{urgent_str}])"
        else:
            return f"Needs(wellbeing={wellbeing:.2f}, all_satisfied)"


@dataclass
class Drive:
    """
    A fundamental psychological drive that motivates behavior.

    Drives are more abstract than needs - they represent
    deep motivations that shape goal formation.

    Examples:
    - Drive for mastery → Goals about skill improvement
    - Drive for connection → Goals about relationships
    - Drive for security → Goals about safety and resources
    """

    name: str
    intensity: float = 0.5  # 0.0-1.0, how strong this drive is
    description: str = ""

    # Which needs this drive relates to
    satisfies_needs: List[NeedType] = field(default_factory=list)

    def __post_init__(self):
        assert 0.0 <= self.intensity <= 1.0, "Drive intensity must be between 0 and 1"

    def get_activation(self, needs: PhysiologicalNeeds) -> float:
        """
        Calculate how activated this drive is based on needs.

        Returns 0.0-1.0, higher means drive is more active.
        """
        if not self.satisfies_needs:
            return self.intensity

        # Check urgency of related needs
        urgency_sum = 0.0
        for need_type in self.satisfies_needs:
            need = needs.get_need(need_type)
            if need:
                urgency_sum += need.get_urgency()

        # Average urgency of related needs, weighted by drive intensity
        avg_urgency = urgency_sum / len(self.satisfies_needs) if self.satisfies_needs else 0.0
        return self.intensity * (0.3 + 0.7 * avg_urgency)

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "name": self.name,
            "intensity": self.intensity,
            "description": self.description,
            "satisfies_needs": [nt.value for nt in self.satisfies_needs],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Drive":
        """Deserialize from saved data."""
        data["satisfies_needs"] = [NeedType(nt) for nt in data.get("satisfies_needs", [])]
        return cls(**data)


def create_standard_drives() -> List[Drive]:
    """Create standard set of psychological drives."""
    return [
        Drive(
            name="survival",
            intensity=1.0,
            description="Preserve life and avoid harm",
            satisfies_needs=[NeedType.HUNGER, NeedType.REST, NeedType.SAFETY, NeedType.HEALTH],
        ),
        Drive(
            name="achievement",
            intensity=0.7,
            description="Accomplish goals and demonstrate competence",
            satisfies_needs=[NeedType.ACHIEVEMENT, NeedType.COMPETENCE, NeedType.RESPECT],
        ),
        Drive(
            name="affiliation",
            intensity=0.6,
            description="Form and maintain relationships",
            satisfies_needs=[NeedType.BELONGING, NeedType.INTIMACY],
        ),
        Drive(
            name="autonomy",
            intensity=0.7,
            description="Maintain independence and self-determination",
            satisfies_needs=[NeedType.AUTONOMY],
        ),
        Drive(
            name="exploration",
            intensity=0.5,
            description="Seek novelty and understanding",
            satisfies_needs=[NeedType.CURIOSITY],
        ),
        Drive(
            name="purpose",
            intensity=0.6,
            description="Find meaning and contribute",
            satisfies_needs=[NeedType.PURPOSE, NeedType.RESPECT],
        ),
    ]
