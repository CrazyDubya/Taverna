"""
Personality Model for Deep Agents.

Based on:
- Big Five personality traits (OCEAN)
- Core values that guide decision-making
- Traits that modify behavior

Personality is relatively stable but can shift slowly over time
based on profound experiences.
"""

from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum


class PersonalityTrait(Enum):
    """Big Five personality dimensions (OCEAN)."""

    OPENNESS = "openness"  # Imagination, curiosity, preference for variety
    CONSCIENTIOUSNESS = "conscientiousness"  # Organization, responsibility, self-discipline
    EXTRAVERSION = "extraversion"  # Sociability, assertiveness, energy
    AGREEABLENESS = "agreeableness"  # Compassion, cooperation, trust
    NEUROTICISM = "neuroticism"  # Anxiety, emotional instability, sensitivity to stress


@dataclass
class Value:
    """A core value that guides decision-making."""

    name: str
    strength: float  # 0.0-1.0, how strongly held
    description: str = ""

    def __post_init__(self):
        assert 0.0 <= self.strength <= 1.0, "Value strength must be between 0 and 1"


@dataclass
class Personality:
    """
    Complete personality model for an agent.

    Influences:
    - How agent perceives events (optimist vs pessimist)
    - Which goals are prioritized (achievement vs relationships)
    - Emotional responses to situations
    - Decision-making under uncertainty
    - Social interaction style
    """

    # Big Five traits (all 0.0-1.0)
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    # Core values (ordered by importance)
    values: List[Value] = field(default_factory=list)

    # Additional traits
    risk_tolerance: float = 0.5  # 0=very cautious, 1=very bold
    optimism: float = 0.5  # 0=pessimist, 1=optimist
    patience: float = 0.5  # 0=impulsive, 1=patient

    def __post_init__(self):
        """Validate trait values."""
        for trait in [
            self.openness,
            self.conscientiousness,
            self.extraversion,
            self.agreeableness,
            self.neuroticism,
            self.risk_tolerance,
            self.optimism,
            self.patience,
        ]:
            assert 0.0 <= trait <= 1.0, f"Trait value {trait} must be between 0 and 1"

    def get_trait(self, trait: PersonalityTrait) -> float:
        """Get value of a Big Five trait."""
        return getattr(self, trait.value)

    def influences_emotion(self, emotion_type: str) -> float:
        """
        How personality influences emotional intensity.

        Returns multiplier (0.5-1.5) for emotional response.
        """
        multipliers = {
            "anxiety": 1.0 + (self.neuroticism - 0.5),
            "joy": 1.0 + (self.extraversion - 0.5) * 0.5,
            "anger": 1.0 + (self.neuroticism - 0.5) * 0.5 - (self.agreeableness - 0.5) * 0.3,
            "sadness": 1.0 + (self.neuroticism - 0.5) * 0.7,
            "fear": 1.0 + (self.neuroticism - 0.5) * 0.8,
            "trust": 1.0 + (self.agreeableness - 0.5),
            "disgust": 1.0 + (self.conscientiousness - 0.5) * 0.4,
        }
        return max(0.5, min(1.5, multipliers.get(emotion_type, 1.0)))

    def evaluate_action_alignment(self, action_description: str, action_values: List[str]) -> float:
        """
        Evaluate how well an action aligns with personality values.

        Args:
            action_description: What the action does
            action_values: List of value names this action satisfies/violates

        Returns:
            Alignment score (-1.0 to 1.0)
            Positive = aligned, Negative = conflicts
        """
        if not self.values:
            return 0.0

        alignment = 0.0
        total_weight = 0.0

        for value in self.values:
            if value.name in action_values:
                alignment += value.strength
                total_weight += value.strength
            elif f"violates_{value.name}" in action_values:
                alignment -= value.strength
                total_weight += value.strength

        if total_weight == 0:
            return 0.0

        return alignment / total_weight

    def get_decision_bias(self) -> Dict[str, float]:
        """
        Get decision-making biases based on personality.

        Returns:
            Dictionary of bias factors
        """
        return {
            "prefer_new_experiences": self.openness,
            "prefer_planning": self.conscientiousness,
            "prefer_social_solutions": self.extraversion + self.agreeableness,
            "prefer_safe_options": 1.0 - self.risk_tolerance,
            "expect_positive_outcomes": self.optimism,
            "deliberate_before_acting": self.patience,
            "worry_about_consequences": self.neuroticism,
            "trust_others": self.agreeableness,
        }

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
            "risk_tolerance": self.risk_tolerance,
            "optimism": self.optimism,
            "patience": self.patience,
            "values": [
                {"name": v.name, "strength": v.strength, "description": v.description}
                for v in self.values
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Personality":
        """Deserialize from saved data."""
        values = [Value(**v) for v in data.pop("values", [])]
        return cls(values=values, **data)

    def __repr__(self) -> str:
        traits = f"O:{self.openness:.2f} C:{self.conscientiousness:.2f} "
        traits += f"E:{self.extraversion:.2f} A:{self.agreeableness:.2f} "
        traits += f"N:{self.neuroticism:.2f}"

        top_values = ", ".join(v.name for v in self.values[:3])

        return f"Personality({traits}, values=[{top_values}])"


def create_personality_archetype(archetype: str) -> Personality:
    """
    Create pre-defined personality archetypes.

    Archetypes:
    - "merchant": Practical, responsible, moderately social
    - "scholar": Curious, introverted, thoughtful
    - "warrior": Bold, disciplined, low neuroticism
    - "rogue": High openness, low agreeableness, risk-seeking
    - "healer": High agreeableness, conscientious, empathetic
    """
    archetypes = {
        "merchant": Personality(
            openness=0.6,
            conscientiousness=0.8,
            extraversion=0.6,
            agreeableness=0.6,
            neuroticism=0.4,
            risk_tolerance=0.4,
            optimism=0.6,
            patience=0.7,
            values=[
                Value("independence", 0.9, "Self-reliance and business ownership"),
                Value("fairness", 0.8, "Fair deals and honest business"),
                Value("prosperity", 0.7, "Financial success and security"),
                Value("reputation", 0.6, "Good standing in community"),
            ],
        ),
        "scholar": Personality(
            openness=0.9,
            conscientiousness=0.7,
            extraversion=0.3,
            agreeableness=0.5,
            neuroticism=0.5,
            risk_tolerance=0.5,
            optimism=0.5,
            patience=0.8,
            values=[
                Value("knowledge", 0.9, "Understanding and wisdom"),
                Value("truth", 0.8, "Seeking facts and reality"),
                Value("curiosity", 0.8, "Exploring the unknown"),
            ],
        ),
        "warrior": Personality(
            openness=0.4,
            conscientiousness=0.8,
            extraversion=0.6,
            agreeableness=0.4,
            neuroticism=0.2,
            risk_tolerance=0.7,
            optimism=0.6,
            patience=0.5,
            values=[
                Value("honor", 0.9, "Acting with integrity and courage"),
                Value("strength", 0.8, "Physical and mental prowess"),
                Value("loyalty", 0.7, "Devotion to allies"),
            ],
        ),
        "rogue": Personality(
            openness=0.8,
            conscientiousness=0.3,
            extraversion=0.7,
            agreeableness=0.3,
            neuroticism=0.4,
            risk_tolerance=0.9,
            optimism=0.7,
            patience=0.3,
            values=[
                Value("freedom", 0.9, "Personal liberty above all"),
                Value("excitement", 0.8, "Thrill and adventure"),
                Value("cleverness", 0.7, "Wit and cunning"),
            ],
        ),
        "healer": Personality(
            openness=0.6,
            conscientiousness=0.8,
            extraversion=0.5,
            agreeableness=0.9,
            neuroticism=0.5,
            risk_tolerance=0.3,
            optimism=0.6,
            patience=0.8,
            values=[
                Value("compassion", 0.9, "Caring for others' wellbeing"),
                Value("harmony", 0.8, "Peace and balance"),
                Value("duty", 0.7, "Responsibility to help"),
            ],
        ),
    }

    if archetype not in archetypes:
        raise ValueError(
            f"Unknown archetype '{archetype}'. "
            f"Choose from: {', '.join(archetypes.keys())}"
        )

    return archetypes[archetype]
