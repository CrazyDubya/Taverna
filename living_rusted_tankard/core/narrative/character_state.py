"""
Dynamic character state system for NPCs.
Makes NPCs feel alive with moods, concerns, and goals that change based on world events.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random


class Mood(Enum):
    """NPC emotional states that affect dialogue and behavior."""
    CHEERFUL = "cheerful"
    CONTENT = "content"
    NEUTRAL = "neutral"
    WORRIED = "worried"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    SAD = "sad"
    EXCITED = "excited"
    TIRED = "tired"
    FOCUSED = "focused"


class ConcernType(Enum):
    """Types of concerns NPCs can have."""
    PERSONAL = "personal"      # Health, money, relationships
    BUSINESS = "business"       # Shop, trade, customers
    COMMUNITY = "community"     # Town events, other NPCs
    DANGER = "danger"          # Threats, rumors
    OPPORTUNITY = "opportunity" # Potential gains, deals


@dataclass
class Concern:
    """Something an NPC is currently worried or thinking about."""
    type: ConcernType
    description: str
    intensity: float  # 0.0 to 1.0
    source: str  # What caused this concern
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if this concern has expired."""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    def decay(self, amount: float = 0.1) -> None:
        """Reduce concern intensity over time."""
        self.intensity = max(0.0, self.intensity - amount)


@dataclass
class Goal:
    """Something an NPC wants to achieve."""
    description: str
    priority: float  # 0.0 to 1.0
    progress: float  # 0.0 to 1.0
    required_actions: List[str]  # What needs to happen
    blockers: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_blocked(self) -> bool:
        """Check if goal is currently blocked."""
        return len(self.blockers) > 0
    
    def is_complete(self) -> bool:
        """Check if goal is complete."""
        return self.progress >= 1.0


class CharacterState:
    """Manages dynamic state for a single NPC."""
    
    def __init__(self, npc_id: str, npc_name: str, base_personality: Dict[str, float]):
        self.npc_id = npc_id
        self.npc_name = npc_name
        self.base_personality = base_personality
        
        # Current state
        self.mood: Mood = Mood.NEUTRAL
        self.energy: float = 1.0  # 0.0 to 1.0
        self.stress: float = 0.0  # 0.0 to 1.0
        
        # Active concerns and goals
        self.concerns: List[Concern] = []
        self.goals: List[Goal] = []
        
        # Mood modifiers from recent events
        self.mood_modifiers: Dict[str, Tuple[float, datetime]] = {}
        
        # Availability
        self.is_busy: bool = False
        self.busy_reason: Optional[str] = None
        self.busy_until: Optional[datetime] = None
    
    def update_mood(self) -> None:
        """Calculate current mood based on all factors."""
        # Start with personality baseline - initialize all moods
        mood_scores = {
            Mood.CHEERFUL: self.base_personality.get("optimism", 0.5),
            Mood.CONTENT: self.base_personality.get("contentment", 0.5),
            Mood.NEUTRAL: 0.3,
            Mood.WORRIED: self.base_personality.get("anxiety", 0.3),
            Mood.ANXIOUS: self.base_personality.get("anxiety", 0.2) * 0.5,
            Mood.ANGRY: self.base_personality.get("temper", 0.2),
            Mood.SAD: 0.1,
            Mood.EXCITED: self.base_personality.get("optimism", 0.5) * 0.3,
            Mood.TIRED: 0.1,
            Mood.FOCUSED: self.base_personality.get("curiosity", 0.5) * 0.4,
        }
        
        # Apply stress and energy
        if self.stress > 0.7:
            mood_scores[Mood.ANXIOUS] += 0.4
            mood_scores[Mood.ANGRY] += 0.2
        
        if self.energy < 0.3:
            mood_scores[Mood.TIRED] += 0.6
            mood_scores[Mood.CHEERFUL] *= 0.5
        
        # Apply concern intensities
        for concern in self.concerns:
            if concern.type == ConcernType.DANGER:
                mood_scores[Mood.WORRIED] += concern.intensity * 0.5
                mood_scores[Mood.ANXIOUS] += concern.intensity * 0.3
            elif concern.type == ConcernType.OPPORTUNITY:
                mood_scores[Mood.EXCITED] += concern.intensity * 0.4
        
        # Apply mood modifiers
        current_time = datetime.now()
        expired_modifiers = []
        
        for source, (value, expires) in self.mood_modifiers.items():
            if expires < current_time:
                expired_modifiers.append(source)
            else:
                # Distribute modifier across relevant moods
                if value > 0:
                    mood_scores[Mood.CHEERFUL] += value * 0.3
                    mood_scores[Mood.CONTENT] += value * 0.2
                else:
                    mood_scores[Mood.SAD] += abs(value) * 0.3
                    mood_scores[Mood.WORRIED] += abs(value) * 0.2
        
        # Clean up expired modifiers
        for source in expired_modifiers:
            del self.mood_modifiers[source]
        
        # Select mood with highest score
        self.mood = max(mood_scores.items(), key=lambda x: x[1])[0]
    
    def add_concern(self, concern: Concern) -> None:
        """Add a new concern or intensify existing one."""
        # Check if we already have a similar concern
        for existing in self.concerns:
            if existing.type == concern.type and existing.description == concern.description:
                # Intensify existing concern
                existing.intensity = min(1.0, existing.intensity + concern.intensity * 0.5)
                existing.expires_at = concern.expires_at
                return
        
        # Add new concern
        self.concerns.append(concern)
        self.update_mood()
    
    def remove_concern(self, description: str) -> None:
        """Remove a concern by description."""
        self.concerns = [c for c in self.concerns if c.description != description]
        self.update_mood()
    
    def add_goal(self, goal: Goal) -> None:
        """Add a new goal."""
        self.goals.append(goal)
        
        # High priority goals can affect mood
        if goal.priority > 0.7:
            self.mood_modifiers[f"goal_{goal.description}"] = (
                0.3,  # Positive modifier for having purpose
                datetime.now().replace(hour=23, minute=59)  # Until end of day
            )
            self.update_mood()
    
    def complete_goal(self, description: str) -> None:
        """Mark a goal as complete and remove it."""
        for goal in self.goals:
            if goal.description == description:
                goal.progress = 1.0
                # Completing goals improves mood
                self.mood_modifiers[f"completed_{description}"] = (
                    0.5,
                    datetime.now().replace(hour=23, minute=59)
                )
                self.goals.remove(goal)
                self.update_mood()
                break
    
    def set_busy(self, reason: str, duration_minutes: int = 30) -> None:
        """Mark NPC as busy for a period."""
        self.is_busy = True
        self.busy_reason = reason
        self.busy_until = datetime.now() + timedelta(minutes=duration_minutes)
    
    def check_availability(self) -> Tuple[bool, Optional[str]]:
        """Check if NPC is available for interaction."""
        if self.is_busy and self.busy_until:
            if datetime.now() > self.busy_until:
                # Busy period expired
                self.is_busy = False
                self.busy_reason = None
                self.busy_until = None
            else:
                return False, self.busy_reason
        
        # Check if too stressed or tired
        if self.stress > 0.9:
            return False, "looking too stressed to talk"
        
        if self.energy < 0.1:
            return False, "looking exhausted"
        
        return True, None
    
    def tick(self) -> None:
        """Update state over time."""
        # Decay concerns
        expired_concerns = []
        for concern in self.concerns:
            concern.decay(0.05)
            if concern.intensity <= 0 or concern.is_expired():
                expired_concerns.append(concern)
        
        for concern in expired_concerns:
            self.concerns.remove(concern)
        
        # Restore energy slowly
        self.energy = min(1.0, self.energy + 0.02)
        
        # Reduce stress slowly
        self.stress = max(0.0, self.stress - 0.01)
        
        # Update mood based on current state
        self.update_mood()
    
    def get_dialogue_modifiers(self) -> Dict[str, any]:
        """Get state modifiers for dialogue generation."""
        return {
            "mood": self.mood.value,
            "energy_level": "exhausted" if self.energy < 0.3 else "tired" if self.energy < 0.6 else "energetic",
            "stress_level": "calm" if self.stress < 0.3 else "tense" if self.stress < 0.7 else "very stressed",
            "primary_concern": self.concerns[0].description if self.concerns else None,
            "current_goal": self.goals[0].description if self.goals else None,
            "is_busy": self.is_busy,
            "busy_reason": self.busy_reason
        }
    
    def get_status_description(self) -> str:
        """Get a human-readable description of current state."""
        descriptions = []
        
        # Mood description
        mood_descriptions = {
            Mood.CHEERFUL: "seems to be in good spirits",
            Mood.WORRIED: "looks worried about something",
            Mood.ANXIOUS: "appears anxious and restless",
            Mood.ANGRY: "looks irritated",
            Mood.SAD: "seems downcast",
            Mood.TIRED: "looks exhausted",
            Mood.EXCITED: "seems excited about something",
            Mood.FOCUSED: "appears deeply focused",
            Mood.CONTENT: "looks content",
            Mood.NEUTRAL: "seems calm"
        }
        descriptions.append(f"{self.npc_name} {mood_descriptions[self.mood]}")
        
        # Energy level
        if self.energy < 0.3:
            descriptions.append("and could clearly use some rest")
        
        # Stress indicators
        if self.stress > 0.7:
            descriptions.append("while showing signs of stress")
        
        # Current activity
        if self.is_busy and self.busy_reason:
            descriptions.append(f"and is currently {self.busy_reason}")
        
        return " ".join(descriptions) + "."


class CharacterStateManager:
    """Manages character states for all NPCs in the game."""
    
    def __init__(self):
        self.character_states: Dict[str, CharacterState] = {}
    
    def get_or_create_state(self, npc_id: str, npc_name: str, 
                           personality: Optional[Dict[str, float]] = None) -> CharacterState:
        """Get existing state or create new one."""
        if npc_id not in self.character_states:
            if personality is None:
                # Generate random personality if not provided
                personality = {
                    "optimism": random.uniform(0.3, 0.8),
                    "anxiety": random.uniform(0.1, 0.6),
                    "temper": random.uniform(0.1, 0.5),
                    "contentment": random.uniform(0.4, 0.9),
                    "sociability": random.uniform(0.3, 0.9),
                    "curiosity": random.uniform(0.2, 0.8)
                }
            
            self.character_states[npc_id] = CharacterState(npc_id, npc_name, personality)
        
        return self.character_states[npc_id]
    
    def apply_world_event(self, event_type: str, event_data: Dict[str, any]) -> None:
        """Apply a world event to all relevant NPCs."""
        # Example: A theft in the market
        if event_type == "theft_reported":
            location = event_data.get("location", "market")
            
            for state in self.character_states.values():
                # Merchants become very concerned
                if "merchant" in state.npc_id.lower():
                    state.add_concern(Concern(
                        type=ConcernType.DANGER,
                        description=f"theft reported at the {location}",
                        intensity=0.8,
                        source="town_news"
                    ))
                    state.stress = min(1.0, state.stress + 0.3)
                # Others mildly concerned
                else:
                    state.add_concern(Concern(
                        type=ConcernType.COMMUNITY,
                        description=f"increased crime in {location}",
                        intensity=0.4,
                        source="town_news"
                    ))
        
        # Update all moods after world event
        for state in self.character_states.values():
            state.update_mood()
    
    def tick_all(self) -> None:
        """Update all character states."""
        for state in self.character_states.values():
            state.tick()