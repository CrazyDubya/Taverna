"""
Emotional System for Deep Agents.

Implements:
- Individual emotions with intensity and decay
- Mood as longer-term emotional state
- Emotional appraisal of events
- Influence of emotions on decision-making

Based on:
- Plutchik's wheel of emotions
- Appraisal theory (emotions from evaluation of events)
- OCC model (Ortony, Clore, Collins)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import time
import math


class EmotionType(Enum):
    """Primary emotions (Plutchik's model)."""

    JOY = "joy"
    TRUST = "trust"
    FEAR = "fear"
    SURPRISE = "surprise"
    SADNESS = "sadness"
    DISGUST = "disgust"
    ANGER = "anger"
    ANTICIPATION = "anticipation"

    # Secondary emotions (combinations)
    ANXIETY = "anxiety"  # Fear + Anticipation
    HOPE = "hope"  # Anticipation + Joy
    DESPAIR = "despair"  # Sadness + Fear
    PRIDE = "pride"  # Joy + Anticipation
    SHAME = "shame"  # Sadness + Disgust
    GRATITUDE = "gratitude"  # Joy + Trust


@dataclass
class Emotion:
    """
    A single emotional state with intensity and duration.

    Emotions:
    - Have intensity (0.0-1.0)
    - Decay over time
    - Can be triggered by events
    - Influence decision-making
    """

    emotion_type: EmotionType
    intensity: float = 0.0  # 0.0-1.0
    decay_rate: float = 0.1  # How quickly it fades (per hour)
    last_updated: float = field(default_factory=time.time)

    # What triggered this emotion
    trigger: Optional[str] = None
    trigger_time: float = field(default_factory=time.time)

    def update(self, hours_passed: float) -> None:
        """Decay emotion over time."""
        decay = self.decay_rate * hours_passed
        self.intensity = max(0.0, self.intensity - decay)
        self.last_updated = time.time()

    def intensify(self, amount: float, trigger: Optional[str] = None) -> None:
        """Increase emotion intensity."""
        self.intensity = min(1.0, self.intensity + amount)
        if trigger:
            self.trigger = trigger
            self.trigger_time = time.time()
        self.last_updated = time.time()

    def diminish(self, amount: float) -> None:
        """Decrease emotion intensity."""
        self.intensity = max(0.0, self.intensity - amount)
        self.last_updated = time.time()

    def is_active(self, threshold: float = 0.1) -> bool:
        """Check if emotion is significantly active."""
        return self.intensity >= threshold

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "emotion_type": self.emotion_type.value,
            "intensity": self.intensity,
            "decay_rate": self.decay_rate,
            "last_updated": self.last_updated,
            "trigger": self.trigger,
            "trigger_time": self.trigger_time,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Emotion":
        """Deserialize from saved data."""
        data["emotion_type"] = EmotionType(data["emotion_type"])
        return cls(**data)


@dataclass
class Mood:
    """
    Longer-term emotional state that acts as a backdrop.

    Mood is less specific than emotions:
    - Positive vs Negative (valence)
    - High vs Low energy (arousal)
    - Changes slowly
    - Influences interpretation of events
    """

    valence: float = 0.0  # -1.0 (negative) to 1.0 (positive)
    arousal: float = 0.0  # -1.0 (low energy) to 1.0 (high energy)

    # Mood changes slowly
    change_rate: float = 0.05  # How fast mood can shift

    def update_from_emotions(self, emotions: Dict[EmotionType, Emotion]) -> None:
        """Update mood based on current emotions."""
        # Calculate target valence/arousal from emotions
        target_valence = 0.0
        target_arousal = 0.0
        total_intensity = 0.0

        emotion_valences = {
            EmotionType.JOY: (1.0, 0.5),
            EmotionType.TRUST: (0.7, 0.0),
            EmotionType.FEAR: (-0.7, 0.8),
            EmotionType.SURPRISE: (0.0, 0.9),
            EmotionType.SADNESS: (-0.9, -0.5),
            EmotionType.DISGUST: (-0.6, 0.2),
            EmotionType.ANGER: (-0.8, 0.7),
            EmotionType.ANTICIPATION: (0.3, 0.6),
            EmotionType.ANXIETY: (-0.6, 0.7),
            EmotionType.HOPE: (0.8, 0.4),
            EmotionType.DESPAIR: (-1.0, -0.3),
            EmotionType.PRIDE: (0.9, 0.5),
            EmotionType.SHAME: (-0.8, -0.4),
            EmotionType.GRATITUDE: (0.8, 0.2),
        }

        for emotion in emotions.values():
            if emotion.is_active():
                valence, arousal_contrib = emotion_valences.get(
                    emotion.emotion_type, (0.0, 0.0)
                )
                weight = emotion.intensity
                target_valence += valence * weight
                target_arousal += arousal_contrib * weight
                total_intensity += weight

        if total_intensity > 0:
            target_valence /= total_intensity
            target_arousal /= total_intensity
        else:
            # No active emotions, drift toward neutral
            target_valence = 0.0
            target_arousal = 0.0

        # Move mood gradually toward target
        valence_diff = target_valence - self.valence
        arousal_diff = target_arousal - self.arousal

        self.valence += valence_diff * self.change_rate
        self.arousal += arousal_diff * self.change_rate

        # Clamp to valid range
        self.valence = max(-1.0, min(1.0, self.valence))
        self.arousal = max(-1.0, min(1.0, self.arousal))

    def get_mood_descriptor(self) -> str:
        """Get human-readable mood description."""
        # Map valence/arousal to mood descriptors
        if self.valence > 0.5:
            if self.arousal > 0.5:
                return "excited"
            elif self.arousal < -0.5:
                return "content"
            else:
                return "happy"
        elif self.valence < -0.5:
            if self.arousal > 0.5:
                return "anxious"
            elif self.arousal < -0.5:
                return "depressed"
            else:
                return "sad"
        else:
            if self.arousal > 0.5:
                return "alert"
            elif self.arousal < -0.5:
                return "tired"
            else:
                return "neutral"

    def influences_perception(self, event_valence: float) -> float:
        """
        How mood colors perception of events.

        Positive mood sees events more positively.
        Negative mood sees events more negatively.

        Returns modified event valence.
        """
        mood_influence = 0.2  # How much mood affects perception
        return event_valence + (self.valence * mood_influence)

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "change_rate": self.change_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Mood":
        """Deserialize from saved data."""
        return cls(**data)

    def __repr__(self) -> str:
        return f"Mood({self.get_mood_descriptor()}, v={self.valence:.2f}, a={self.arousal:.2f})"


@dataclass
class EmotionalState:
    """
    Complete emotional state of an agent.

    Manages:
    - Individual emotions
    - Overall mood
    - Emotional appraisal of events
    - Influence on decision-making
    """

    emotions: Dict[EmotionType, Emotion] = field(default_factory=dict)
    mood: Mood = field(default_factory=Mood)

    def __post_init__(self):
        """Initialize with neutral emotions if not provided."""
        if not self.emotions:
            self.emotions = self._create_neutral_emotions()

    def _create_neutral_emotions(self) -> Dict[EmotionType, Emotion]:
        """Create all emotions at neutral state."""
        return {
            emotion_type: Emotion(emotion_type, intensity=0.0, decay_rate=0.1)
            for emotion_type in EmotionType
        }

    def update(self, hours_passed: float) -> None:
        """Update all emotions and mood."""
        # Decay all emotions
        for emotion in self.emotions.values():
            emotion.update(hours_passed)

        # Update mood from current emotions
        self.mood.update_from_emotions(self.emotions)

    def trigger_emotion(
        self, emotion_type: EmotionType, intensity: float, trigger: Optional[str] = None
    ) -> None:
        """Trigger an emotion with given intensity."""
        if emotion_type in self.emotions:
            self.emotions[emotion_type].intensify(intensity, trigger)

    def appraise_event(
        self,
        event_description: str,
        event_outcome: str,  # "positive", "negative", "neutral"
        unexpectedness: float = 0.0,  # 0.0-1.0
        personal_relevance: float = 0.5,  # 0.0-1.0
    ) -> List[EmotionType]:
        """
        Appraise an event and trigger appropriate emotions.

        Based on OCC model:
        - Event outcome → Joy/Sadness
        - Unexpectedness → Surprise/Anticipation
        - Agent action → Pride/Shame
        - Other agent action → Gratitude/Anger

        Returns list of triggered emotions.
        """
        triggered = []

        # Base intensity from personal relevance
        base_intensity = 0.3 + (0.7 * personal_relevance)

        # Event outcome emotions
        if event_outcome == "positive":
            self.trigger_emotion(EmotionType.JOY, base_intensity, event_description)
            triggered.append(EmotionType.JOY)

            if unexpectedness > 0.5:
                self.trigger_emotion(
                    EmotionType.SURPRISE, unexpectedness * 0.6, event_description
                )
                triggered.append(EmotionType.SURPRISE)

        elif event_outcome == "negative":
            self.trigger_emotion(EmotionType.SADNESS, base_intensity, event_description)
            triggered.append(EmotionType.SADNESS)

            if unexpectedness > 0.5:
                self.trigger_emotion(EmotionType.FEAR, unexpectedness * 0.5, event_description)
                triggered.append(EmotionType.FEAR)

        # Unexpectedness alone
        if unexpectedness > 0.7:
            self.trigger_emotion(EmotionType.SURPRISE, unexpectedness * 0.8, event_description)
            if EmotionType.SURPRISE not in triggered:
                triggered.append(EmotionType.SURPRISE)

        return triggered

    def get_dominant_emotion(self) -> Optional[EmotionType]:
        """Get the currently strongest emotion."""
        active_emotions = [e for e in self.emotions.values() if e.is_active(threshold=0.2)]

        if not active_emotions:
            return None

        return max(active_emotions, key=lambda e: e.intensity).emotion_type

    def get_emotional_summary(self) -> Dict[str, any]:
        """Get summary of current emotional state."""
        active_emotions = {
            etype.value: e.intensity
            for etype, e in self.emotions.items()
            if e.is_active(threshold=0.1)
        }

        dominant = self.get_dominant_emotion()

        return {
            "mood": self.mood.get_mood_descriptor(),
            "mood_valence": self.mood.valence,
            "mood_arousal": self.mood.arousal,
            "active_emotions": active_emotions,
            "dominant_emotion": dominant.value if dominant else None,
        }

    def influences_risk_tolerance(self) -> float:
        """
        Calculate how emotions affect risk tolerance.

        Returns multiplier (0.5-1.5):
        - Fear/Anxiety → more risk-averse
        - Anger/Joy → more risk-seeking
        """
        risk_modifier = 1.0

        # Fear and anxiety make more cautious
        if EmotionType.FEAR in self.emotions:
            risk_modifier -= self.emotions[EmotionType.FEAR].intensity * 0.3

        if EmotionType.ANXIETY in self.emotions:
            risk_modifier -= self.emotions[EmotionType.ANXIETY].intensity * 0.2

        # Anger and joy make bolder
        if EmotionType.ANGER in self.emotions:
            risk_modifier += self.emotions[EmotionType.ANGER].intensity * 0.2

        if EmotionType.JOY in self.emotions:
            risk_modifier += self.emotions[EmotionType.JOY].intensity * 0.15

        return max(0.5, min(1.5, risk_modifier))

    def influences_social_behavior(self) -> Dict[str, float]:
        """
        Calculate how emotions affect social behavior.

        Returns modifiers for:
        - friendliness: How warm in interactions
        - openness: Willingness to share
        - trust: Willingness to trust others
        """
        friendliness = 1.0
        openness = 1.0
        trust_mod = 1.0

        # Joy increases friendliness and openness
        if EmotionType.JOY in self.emotions:
            joy_intensity = self.emotions[EmotionType.JOY].intensity
            friendliness += joy_intensity * 0.3
            openness += joy_intensity * 0.2

        # Trust increases trust (obviously)
        if EmotionType.TRUST in self.emotions:
            trust_mod += self.emotions[EmotionType.TRUST].intensity * 0.4

        # Fear/Anxiety decreases openness and trust
        if EmotionType.FEAR in self.emotions:
            fear_intensity = self.emotions[EmotionType.FEAR].intensity
            openness -= fear_intensity * 0.3
            trust_mod -= fear_intensity * 0.4

        # Anger decreases friendliness
        if EmotionType.ANGER in self.emotions:
            anger_intensity = self.emotions[EmotionType.ANGER].intensity
            friendliness -= anger_intensity * 0.4

        # Sadness decreases social engagement
        if EmotionType.SADNESS in self.emotions:
            sadness_intensity = self.emotions[EmotionType.SADNESS].intensity
            friendliness -= sadness_intensity * 0.2
            openness -= sadness_intensity * 0.2

        return {
            "friendliness": max(0.5, min(1.5, friendliness)),
            "openness": max(0.5, min(1.5, openness)),
            "trust": max(0.5, min(1.5, trust_mod)),
        }

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "emotions": {
                etype.value: emotion.to_dict() for etype, emotion in self.emotions.items()
            },
            "mood": self.mood.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "EmotionalState":
        """Deserialize from saved data."""
        emotions = {
            EmotionType(etype): Emotion.from_dict(edata)
            for etype, edata in data.get("emotions", {}).items()
        }
        mood = Mood.from_dict(data.get("mood", {}))
        return cls(emotions=emotions, mood=mood)

    def __repr__(self) -> str:
        dominant = self.get_dominant_emotion()
        dominant_str = dominant.value if dominant else "none"
        return f"EmotionalState(mood={self.mood.get_mood_descriptor()}, dominant={dominant_str})"
