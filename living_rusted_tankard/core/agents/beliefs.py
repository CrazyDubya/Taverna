"""
Belief System for Deep Agents.

Implements:
- Beliefs about the world (facts, probabilities)
- Beliefs about other agents (theory of mind)
- Belief updating based on evidence
- Confidence levels in beliefs

Beliefs drive decision-making - agents act based on what they
believe to be true, not objective reality.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import time


class BeliefType(Enum):
    """Categories of beliefs."""

    FACT = "fact"  # "The tavern opens at dawn"
    PROBABILITY = "probability"  # "It will probably rain"
    PREFERENCE = "preference"  # "I like Gene"
    ABILITY = "ability"  # "I can pick locks"
    NORM = "norm"  # "People tip performers"
    GOAL_OF_OTHER = "goal_of_other"  # "Sarah wants to succeed"
    TRAIT_OF_OTHER = "trait_of_other"  # "Marcus is trustworthy"


@dataclass
class Belief:
    """
    A single belief with confidence level.

    Beliefs have:
    - Content (what is believed)
    - Confidence (0.0-1.0, how certain)
    - Evidence (what supports this belief)
    - Last updated timestamp
    """

    belief_type: BeliefType
    subject: str  # What this belief is about
    content: str  # The actual belief
    confidence: float = 0.5  # 0.0-1.0, how strongly believed

    # Evidence supporting or contradicting this belief
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)

    # Metadata
    formed_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    update_count: int = 0

    def update_confidence(self, evidence: str, supports: bool, weight: float = 0.1) -> None:
        """
        Update confidence based on new evidence.

        Args:
            evidence: Description of the evidence
            supports: True if evidence supports, False if contradicts
            weight: How much to adjust confidence (0.0-1.0)
        """
        if supports:
            self.supporting_evidence.append(evidence)
            # Increase confidence, with diminishing returns
            confidence_increase = weight * (1.0 - self.confidence) * 0.5
            self.confidence = min(1.0, self.confidence + confidence_increase)
        else:
            self.contradicting_evidence.append(evidence)
            # Decrease confidence
            confidence_decrease = weight * self.confidence * 0.5
            self.confidence = max(0.0, self.confidence - confidence_decrease)

        self.last_updated = time.time()
        self.update_count += 1

    def is_strong(self, threshold: float = 0.7) -> bool:
        """Check if this is a strongly held belief."""
        return self.confidence >= threshold

    def is_weak(self, threshold: float = 0.3) -> bool:
        """Check if this is a weakly held belief."""
        return self.confidence <= threshold

    def get_age_hours(self) -> float:
        """Get age of belief in hours."""
        return (time.time() - self.formed_at) / 3600.0

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "belief_type": self.belief_type.value,
            "subject": self.subject,
            "content": self.content,
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "formed_at": self.formed_at,
            "last_updated": self.last_updated,
            "update_count": self.update_count,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Belief":
        """Deserialize from saved data."""
        data["belief_type"] = BeliefType(data["belief_type"])
        return cls(**data)

    def __repr__(self) -> str:
        return f"Belief({self.subject}: '{self.content}', confidence={self.confidence:.2f})"


@dataclass
class TheoryOfMind:
    """
    Agent's beliefs about another agent's mental state.

    Represents what one agent thinks another agent:
    - Believes
    - Wants (goals)
    - Feels (emotions)
    - Is like (traits)

    This enables social reasoning and prediction of behavior.
    """

    target_agent: str  # Who this theory is about

    # Beliefs about their beliefs (meta-beliefs)
    beliefs_about_beliefs: List[Belief] = field(default_factory=list)

    # Beliefs about their goals
    perceived_goals: List[str] = field(default_factory=list)

    # Beliefs about their traits
    perceived_traits: Dict[str, float] = field(default_factory=dict)  # trait -> strength

    # Beliefs about their emotional state
    perceived_emotions: Dict[str, float] = field(default_factory=dict)  # emotion -> intensity

    # Confidence in this model (0.0-1.0)
    model_confidence: float = 0.3  # Start uncertain

    last_updated: float = field(default_factory=time.time)

    def update_perceived_goal(self, goal: str, confidence: float = 0.6) -> None:
        """Update belief about target's goal."""
        if goal not in self.perceived_goals:
            self.perceived_goals.append(goal)
        self.last_updated = time.time()

    def update_perceived_trait(self, trait: str, strength: float) -> None:
        """Update belief about target's trait."""
        self.perceived_traits[trait] = strength
        self.last_updated = time.time()

    def update_perceived_emotion(self, emotion: str, intensity: float) -> None:
        """Update belief about target's current emotion."""
        self.perceived_emotions[emotion] = intensity
        self.last_updated = time.time()

    def predict_behavior(self, situation: str) -> str:
        """
        Predict how target might behave in a situation.

        Returns predicted behavior description.
        """
        # Use perceived goals and traits to predict
        if "trustworthy" in self.perceived_traits:
            if self.perceived_traits["trustworthy"] > 0.7:
                return "likely to be honest and helpful"
            elif self.perceived_traits["trustworthy"] < 0.3:
                return "might be deceptive or unhelpful"

        if "desperate" in self.perceived_goals:
            return "might take risky or unethical actions"

        return "behavior uncertain, need more information"

    def get_trust_estimate(self) -> float:
        """
        Estimate how trustworthy the target is believed to be.

        Returns 0.0-1.0
        """
        trust = 0.5  # Start neutral

        # Check perceived traits
        if "trustworthy" in self.perceived_traits:
            trust = self.perceived_traits["trustworthy"]
        elif "deceptive" in self.perceived_traits:
            trust = 1.0 - self.perceived_traits["deceptive"]

        # Adjust by model confidence
        # Low confidence pulls toward neutral
        return trust * self.model_confidence + 0.5 * (1.0 - self.model_confidence)

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "target_agent": self.target_agent,
            "beliefs_about_beliefs": [b.to_dict() for b in self.beliefs_about_beliefs],
            "perceived_goals": self.perceived_goals,
            "perceived_traits": self.perceived_traits,
            "perceived_emotions": self.perceived_emotions,
            "model_confidence": self.model_confidence,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TheoryOfMind":
        """Deserialize from saved data."""
        data["beliefs_about_beliefs"] = [
            Belief.from_dict(b) for b in data.get("beliefs_about_beliefs", [])
        ]
        return cls(**data)


@dataclass
class BeliefSystem:
    """
    Complete belief system for an agent.

    Manages:
    - Beliefs about the world
    - Theory of mind about other agents
    - Belief updating and revision
    - Consistency checking
    """

    # Beliefs indexed by subject
    beliefs: Dict[str, List[Belief]] = field(default_factory=dict)

    # Theory of mind about other agents
    mental_models: Dict[str, TheoryOfMind] = field(default_factory=dict)

    def add_belief(
        self,
        belief_type: BeliefType,
        subject: str,
        content: str,
        confidence: float = 0.6,
        evidence: Optional[str] = None,
    ) -> Belief:
        """Add a new belief."""
        belief = Belief(
            belief_type=belief_type, subject=subject, content=content, confidence=confidence
        )

        if evidence:
            belief.supporting_evidence.append(evidence)

        if subject not in self.beliefs:
            self.beliefs[subject] = []

        self.beliefs[subject].append(belief)
        return belief

    def get_beliefs_about(self, subject: str) -> List[Belief]:
        """Get all beliefs about a subject."""
        return self.beliefs.get(subject, [])

    def get_belief(
        self, subject: str, content_contains: Optional[str] = None
    ) -> Optional[Belief]:
        """Get a specific belief, optionally filtering by content."""
        beliefs_about_subject = self.get_beliefs_about(subject)

        if not beliefs_about_subject:
            return None

        if content_contains:
            matching = [b for b in beliefs_about_subject if content_contains in b.content]
            if matching:
                # Return strongest belief
                return max(matching, key=lambda b: b.confidence)
            return None

        # Return strongest belief about subject
        return max(beliefs_about_subject, key=lambda b: b.confidence)

    def update_belief(
        self, subject: str, content: str, evidence: str, supports: bool
    ) -> Optional[Belief]:
        """Update an existing belief with new evidence."""
        belief = self.get_belief(subject, content)

        if belief:
            belief.update_confidence(evidence, supports)
            return belief

        # Belief doesn't exist yet
        if supports:
            # Create new belief
            return self.add_belief(
                BeliefType.FACT,  # Default type
                subject,
                content,
                confidence=0.5,
                evidence=evidence,
            )

        return None

    def believes(self, subject: str, content: str, min_confidence: float = 0.5) -> bool:
        """Check if agent believes something with sufficient confidence."""
        belief = self.get_belief(subject, content)
        return belief is not None and belief.confidence >= min_confidence

    def get_theory_of_mind(self, agent_name: str) -> TheoryOfMind:
        """Get or create theory of mind about another agent."""
        if agent_name not in self.mental_models:
            self.mental_models[agent_name] = TheoryOfMind(target_agent=agent_name)

        return self.mental_models[agent_name]

    def update_mental_model(
        self, agent_name: str, observation: str, observation_type: str = "behavior"
    ) -> None:
        """
        Update theory of mind based on observation.

        Observations like:
        - "refused to help" → decreases perceived agreeableness
        - "donated gold" → increases perceived generosity
        - "asked about cellar" → adds perceived goal: investigate cellar
        """
        theory = self.get_theory_of_mind(agent_name)

        # Simple heuristics for updating (can be made much more sophisticated)
        if "refused" in observation or "declined" in observation:
            theory.update_perceived_trait("helpful", max(0.0, theory.perceived_traits.get("helpful", 0.5) - 0.1))

        if "helped" in observation or "donated" in observation:
            theory.update_perceived_trait("generous", min(1.0, theory.perceived_traits.get("generous", 0.5) + 0.1))

        if "lied" in observation or "deceived" in observation:
            theory.update_perceived_trait("trustworthy", max(0.0, theory.perceived_traits.get("trustworthy", 0.5) - 0.2))

        if "asked about" in observation:
            # Infer goal from question
            topic = observation.split("asked about")[-1].strip()
            theory.update_perceived_goal(f"learn about {topic}")

        # Increase model confidence slowly
        theory.model_confidence = min(0.9, theory.model_confidence + 0.01)

    def get_strongest_beliefs(self, min_confidence: float = 0.7) -> List[Belief]:
        """Get all strongly held beliefs."""
        strong_beliefs = []
        for belief_list in self.beliefs.values():
            strong_beliefs.extend([b for b in belief_list if b.is_strong(min_confidence)])
        return sorted(strong_beliefs, key=lambda b: b.confidence, reverse=True)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of belief system."""
        total_beliefs = sum(len(blist) for blist in self.beliefs.values())
        strong_beliefs = len(self.get_strongest_beliefs())

        return {
            "total_beliefs": total_beliefs,
            "strong_beliefs": strong_beliefs,
            "subjects_tracked": len(self.beliefs),
            "agents_modeled": len(self.mental_models),
        }

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "beliefs": {
                subject: [b.to_dict() for b in beliefs]
                for subject, beliefs in self.beliefs.items()
            },
            "mental_models": {
                agent: model.to_dict() for agent, model in self.mental_models.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "BeliefSystem":
        """Deserialize from saved data."""
        beliefs = {
            subject: [Belief.from_dict(b) for b in belief_data]
            for subject, belief_data in data.get("beliefs", {}).items()
        }

        mental_models = {
            agent: TheoryOfMind.from_dict(model_data)
            for agent, model_data in data.get("mental_models", {}).items()
        }

        return cls(beliefs=beliefs, mental_models=mental_models)

    def __repr__(self) -> str:
        summary = self.get_summary()
        return (
            f"BeliefSystem("
            f"beliefs={summary['total_beliefs']}, "
            f"strong={summary['strong_beliefs']}, "
            f"agents_modeled={summary['agents_modeled']})"
        )
