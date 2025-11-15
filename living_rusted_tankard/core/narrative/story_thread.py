"""Story thread system for narrative management."""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import random


class ThreadStage(Enum):
    """Stages of story thread progression."""

    SETUP = "setup"  # Introduction and exposition
    RISING_ACTION = "rising_action"  # Building tension and complications
    CLIMAX = "climax"  # Peak moment of conflict
    FALLING_ACTION = "falling_action"  # Aftermath and consequences
    RESOLUTION = "resolution"  # Conclusion and closure


class ThreadType(Enum):
    """Types of story threads."""

    MAIN = "main"  # Core storyline
    SUBPLOT = "subplot"  # Secondary storyline
    ROMANCE = "romance"  # Romantic storyline
    MYSTERY = "mystery"  # Investigation/mystery
    CONFLICT = "conflict"  # Interpersonal conflict
    QUEST = "quest"  # Goal-oriented thread
    POLITICAL = "political"  # Political intrigue
    ECONOMIC = "economic"  # Trade/financial thread


class BeatType(Enum):
    """Types of story beats."""

    INTRODUCTION = "introduction"
    COMPLICATION = "complication"
    REVELATION = "revelation"
    CONFRONTATION = "confrontation"
    SETBACK = "setback"
    VICTORY = "victory"
    CLIFFHANGER = "cliffhanger"
    RESOLUTION = "resolution"


@dataclass
class StoryBeat:
    """A single narrative moment in a story thread."""

    id: str
    type: BeatType
    description: str
    participants: List[str]
    location: str

    # Timing
    scheduled_time: Optional[datetime] = None
    actual_time: Optional[datetime] = None
    duration_estimate: float = 30.0  # minutes

    # Requirements
    prerequisites: List[str] = field(default_factory=list)  # Beat IDs
    conditions: List[str] = field(default_factory=list)  # World state conditions

    # Effects
    tension_change: float = 0.0  # -1 to 1
    participant_changes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    world_changes: Dict[str, Any] = field(default_factory=dict)

    # Player involvement
    player_present: bool = True
    player_agency: float = 0.5  # How much player can influence

    # Execution
    executed: bool = False
    success: bool = False
    actual_participants: List[str] = field(default_factory=list)

    def can_execute(self, world_state: Dict[str, Any], available_participants: Set[str]) -> bool:
        """Check if beat can be executed."""
        if self.executed:
            return False

        # Check prerequisites
        for prereq in self.prerequisites:
            if not world_state.get(f"beat_{prereq}_completed", False):
                return False

        # Check participants available
        required_participants = set(self.participants)
        if not required_participants.issubset(available_participants):
            return False

        # Check conditions
        for condition in self.conditions:
            if not self._evaluate_condition(condition, world_state):
                return False

        return True

    def _evaluate_condition(self, condition: str, world_state: Dict[str, Any]) -> bool:
        """Evaluate a world state condition."""
        # Simple condition evaluation - could be expanded
        if "=" in condition:
            key, value = condition.split("=")
            return world_state.get(key.strip()) == value.strip()
        elif ">" in condition:
            key, value = condition.split(">")
            return world_state.get(key.strip(), 0) > float(value.strip())
        elif "<" in condition:
            key, value = condition.split("<")
            return world_state.get(key.strip(), 0) < float(value.strip())

        # Default: check if key exists and is truthy
        return bool(world_state.get(condition))

    def execute(self, actual_participants: List[str]) -> Dict[str, Any]:
        """Execute the beat and return results."""
        self.executed = True
        self.actual_time = datetime.now()
        self.actual_participants = actual_participants

        # Calculate success based on participant alignment
        expected_set = set(self.participants)
        actual_set = set(actual_participants)
        alignment = len(expected_set & actual_set) / len(expected_set)
        self.success = alignment > 0.7

        # Return changes to apply
        results = {
            "tension_change": self.tension_change,
            "participant_changes": self.participant_changes.copy(),
            "world_changes": self.world_changes.copy(),
            "success": self.success,
        }

        return results


@dataclass
class StoryThread:
    """A narrative thread tracking a story arc."""

    id: str
    title: str
    type: ThreadType
    description: str

    # Participants
    primary_participants: List[str]  # Main characters
    secondary_participants: List[str] = field(default_factory=list)

    # Thread state
    stage: ThreadStage = ThreadStage.SETUP
    tension_level: float = 0.0  # 0-1
    player_involvement: float = 0.5  # 0-1
    priority: float = 0.5  # 0-1

    # Story structure
    beats: List[StoryBeat] = field(default_factory=list)
    current_beat_index: int = 0

    # Timeline
    started: datetime = field(default_factory=datetime.now)
    estimated_duration: timedelta = field(default_factory=lambda: timedelta(hours=4))
    deadline: Optional[datetime] = None

    # Connections
    connected_threads: List[str] = field(default_factory=list)  # Thread IDs
    spawned_from: Optional[str] = None  # Parent thread
    spawned_threads: List[str] = field(default_factory=list)  # Child threads

    # Requirements and blockers
    prerequisites: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)

    # Completion
    completed: bool = False
    completion_time: Optional[datetime] = None
    resolution_quality: float = 0.0  # 0-1, how satisfying the resolution

    def add_beat(self, beat: StoryBeat) -> None:
        """Add a story beat to the thread."""
        self.beats.append(beat)
        self._update_stage()

    def get_current_beat(self) -> Optional[StoryBeat]:
        """Get the current beat to execute."""
        if self.current_beat_index < len(self.beats):
            return self.beats[self.current_beat_index]
        return None

    def advance_beat(self) -> bool:
        """Advance to the next beat."""
        if self.current_beat_index < len(self.beats) - 1:
            self.current_beat_index += 1
            self._update_stage()
            return True
        return False

    def _update_stage(self) -> None:
        """Update thread stage based on beat progress."""
        if not self.beats:
            return

        progress = self.current_beat_index / len(self.beats)

        if progress < 0.2:
            self.stage = ThreadStage.SETUP
        elif progress < 0.6:
            self.stage = ThreadStage.RISING_ACTION
        elif progress < 0.8:
            self.stage = ThreadStage.CLIMAX
        elif progress < 1.0:
            self.stage = ThreadStage.FALLING_ACTION
        else:
            self.stage = ThreadStage.RESOLUTION
            if not self.completed:
                self.complete()

    def calculate_tension(self) -> float:
        """Calculate current tension level."""
        if not self.beats:
            return 0.0

        # Base tension from stage
        stage_tension = {
            ThreadStage.SETUP: 0.2,
            ThreadStage.RISING_ACTION: 0.6,
            ThreadStage.CLIMAX: 1.0,
            ThreadStage.FALLING_ACTION: 0.4,
            ThreadStage.RESOLUTION: 0.1,
        }

        base = stage_tension.get(self.stage, 0.5)

        # Add beat-specific tension
        current_beat = self.get_current_beat()
        if current_beat:
            beat_tension = {
                BeatType.COMPLICATION: 0.3,
                BeatType.CONFRONTATION: 0.8,
                BeatType.SETBACK: 0.6,
                BeatType.CLIFFHANGER: 0.9,
                BeatType.RESOLUTION: -0.5,
            }
            base += beat_tension.get(current_beat.type, 0.0)

        self.tension_level = max(0.0, min(1.0, base))
        return self.tension_level

    def get_progress(self) -> float:
        """Get thread completion progress (0-1)."""
        if not self.beats:
            return 0.0
        return self.current_beat_index / len(self.beats)

    def is_stalled(self) -> bool:
        """Check if thread is stalled."""
        current_beat = self.get_current_beat()
        if not current_beat:
            return False

        # Check if beat has been waiting too long
        if current_beat.scheduled_time:
            wait_time = datetime.now() - current_beat.scheduled_time
            if wait_time > timedelta(hours=2):  # Arbitrary threshold
                return True

        # Check for blockers
        return len(self.blockers) > 0

    def estimate_remaining_time(self) -> timedelta:
        """Estimate time remaining for thread completion."""
        remaining_beats = len(self.beats) - self.current_beat_index
        if remaining_beats <= 0:
            return timedelta(0)

        avg_duration = sum(beat.duration_estimate for beat in self.beats[self.current_beat_index :]) / remaining_beats
        return timedelta(minutes=avg_duration * remaining_beats)

    def complete(self, quality: float = 0.5) -> None:
        """Mark thread as completed."""
        self.completed = True
        self.completion_time = datetime.now()
        self.resolution_quality = quality
        self.stage = ThreadStage.RESOLUTION

    def get_all_participants(self) -> Set[str]:
        """Get all characters involved in this thread."""
        participants = set(self.primary_participants + self.secondary_participants)

        # Add participants from beats
        for beat in self.beats:
            participants.update(beat.participants)

        return participants

    def check_convergence_potential(self, other_thread: "StoryThread") -> float:
        """Check potential for convergence with another thread."""
        # Shared participants increase convergence potential
        shared_participants = self.get_all_participants() & other_thread.get_all_participants()
        participant_factor = len(shared_participants) * 0.3

        # Similar types converge better
        type_compatibility = {
            (ThreadType.ROMANCE, ThreadType.CONFLICT): 0.8,
            (ThreadType.MYSTERY, ThreadType.POLITICAL): 0.7,
            (ThreadType.QUEST, ThreadType.ECONOMIC): 0.6,
        }

        type_factor = type_compatibility.get(
            (self.type, other_thread.type), type_compatibility.get((other_thread.type, self.type), 0.3)
        )

        # Stage alignment
        stage_factor = 0.5
        if self.stage == other_thread.stage:
            stage_factor = 0.8
        elif abs(list(ThreadStage).index(self.stage) - list(ThreadStage).index(other_thread.stage)) <= 1:
            stage_factor = 0.6

        return min(1.0, participant_factor + type_factor * 0.5 + stage_factor * 0.2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert thread to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "description": self.description,
            "primary_participants": self.primary_participants,
            "secondary_participants": self.secondary_participants,
            "stage": self.stage.value,
            "tension_level": self.tension_level,
            "player_involvement": self.player_involvement,
            "priority": self.priority,
            "current_beat_index": self.current_beat_index,
            "started": self.started.isoformat(),
            "estimated_duration": self.estimated_duration.total_seconds(),
            "completed": self.completed,
            "beats": [
                {
                    "id": beat.id,
                    "type": beat.type.value,
                    "description": beat.description,
                    "participants": beat.participants,
                    "location": beat.location,
                    "executed": beat.executed,
                    "tension_change": beat.tension_change,
                }
                for beat in self.beats
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoryThread":
        """Create thread from dictionary."""
        thread = cls(
            id=data["id"],
            title=data["title"],
            type=ThreadType(data["type"]),
            description=data["description"],
            primary_participants=data["primary_participants"],
            secondary_participants=data.get("secondary_participants", []),
        )

        thread.stage = ThreadStage(data["stage"])
        thread.tension_level = data["tension_level"]
        thread.player_involvement = data["player_involvement"]
        thread.priority = data["priority"]
        thread.current_beat_index = data["current_beat_index"]
        thread.started = datetime.fromisoformat(data["started"])
        thread.estimated_duration = timedelta(seconds=data["estimated_duration"])
        thread.completed = data["completed"]

        # Recreate beats (simplified)
        for beat_data in data["beats"]:
            beat = StoryBeat(
                id=beat_data["id"],
                type=BeatType(beat_data["type"]),
                description=beat_data["description"],
                participants=beat_data["participants"],
                location=beat_data["location"],
                tension_change=beat_data["tension_change"],
            )
            beat.executed = beat_data["executed"]
            thread.beats.append(beat)

        return thread


class ThreadTemplate:
    """Template for generating story threads."""

    def __init__(self, thread_type: ThreadType, title_template: str, beat_templates: List[Dict[str, Any]]):
        self.thread_type = thread_type
        self.title_template = title_template
        self.beat_templates = beat_templates

    def create_thread(self, participants: List[str], context: Dict[str, Any]) -> StoryThread:
        """Create a thread from this template."""
        # Fill in template variables
        title = self._fill_template(self.title_template, participants, context)

        thread = StoryThread(
            id=f"thread_{datetime.now().timestamp()}_{self.thread_type.value}",
            title=title,
            type=self.thread_type,
            description=f"A {self.thread_type.value} thread involving {', '.join(participants)}",
            primary_participants=participants[:2],  # First two are primary
            secondary_participants=participants[2:] if len(participants) > 2 else [],
        )

        # Create beats from templates
        for i, beat_template in enumerate(self.beat_templates):
            beat = StoryBeat(
                id=f"{thread.id}_beat_{i}",
                type=BeatType(beat_template["type"]),
                description=self._fill_template(beat_template["description"], participants, context),
                participants=beat_template.get("participants", participants[:2]),
                location=beat_template.get("location", context.get("default_location", "main_hall")),
                tension_change=beat_template.get("tension_change", 0.0),
                player_agency=beat_template.get("player_agency", 0.5),
            )
            thread.add_beat(beat)

        return thread

    def _fill_template(self, template: str, participants: List[str], context: Dict[str, Any]) -> str:
        """Fill template with actual values."""
        result = template

        # Replace participant placeholders
        for i, participant in enumerate(participants):
            result = result.replace(f"{{participant_{i}}}", participant)
            result = result.replace(f"{{p{i}}}", participant)

        if participants:
            result = result.replace("{participant}", participants[0])
            result = result.replace("{other}", participants[1] if len(participants) > 1 else "someone")

        # Replace context variables
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))

        return result


class ThreadLibrary:
    """Library of thread templates."""

    def __init__(self):
        self.templates: Dict[ThreadType, List[ThreadTemplate]] = {}
        self._initialize_templates()

    def _initialize_templates(self) -> None:
        """Initialize default thread templates."""
        # Romance thread
        romance_template = ThreadTemplate(
            ThreadType.ROMANCE,
            "Romance between {p0} and {p1}",
            [
                {
                    "type": "introduction",
                    "description": "{p0} and {p1} meet and feel an attraction",
                    "participants": ["{p0}", "{p1}"],
                    "tension_change": 0.2,
                },
                {
                    "type": "complication",
                    "description": "Obstacles arise to their budding romance",
                    "tension_change": 0.4,
                },
                {
                    "type": "confrontation",
                    "description": "{p0} and {p1} must overcome their challenges",
                    "tension_change": 0.6,
                },
                {
                    "type": "resolution",
                    "description": "The romantic situation reaches its conclusion",
                    "tension_change": -0.4,
                },
            ],
        )

        # Mystery thread
        mystery_template = ThreadTemplate(
            ThreadType.MYSTERY,
            "The Mystery of {mystery_object}",
            [
                {
                    "type": "introduction",
                    "description": "A mysterious occurrence catches attention",
                    "tension_change": 0.3,
                },
                {
                    "type": "complication",
                    "description": "The mystery deepens as more clues emerge",
                    "tension_change": 0.4,
                },
                {
                    "type": "revelation",
                    "description": "A crucial piece of evidence is discovered",
                    "tension_change": 0.5,
                },
                {"type": "confrontation", "description": "The truth is finally revealed", "tension_change": 0.8},
                {
                    "type": "resolution",
                    "description": "The mystery is solved and justice served",
                    "tension_change": -0.6,
                },
            ],
        )

        # Conflict thread
        conflict_template = ThreadTemplate(
            ThreadType.CONFLICT,
            "Conflict between {p0} and {p1}",
            [
                {
                    "type": "introduction",
                    "description": "Tension begins to build between {p0} and {p1}",
                    "tension_change": 0.3,
                },
                {
                    "type": "complication",
                    "description": "The disagreement escalates into open conflict",
                    "tension_change": 0.6,
                },
                {
                    "type": "confrontation",
                    "description": "{p0} and {p1} have their final confrontation",
                    "tension_change": 0.9,
                },
                {"type": "resolution", "description": "The conflict reaches its resolution", "tension_change": -0.7},
            ],
        )

        self.templates[ThreadType.ROMANCE] = [romance_template]
        self.templates[ThreadType.MYSTERY] = [mystery_template]
        self.templates[ThreadType.CONFLICT] = [conflict_template]

    def get_template(
        self, thread_type: ThreadType, context: Optional[Dict[str, Any]] = None
    ) -> Optional[ThreadTemplate]:
        """Get a template for the specified thread type."""
        templates = self.templates.get(thread_type, [])
        if not templates:
            return None

        # For now, just return a random template
        # Could be enhanced to select based on context
        return random.choice(templates)

    def create_thread_from_participants(
        self,
        participants: List[str],
        preferred_type: Optional[ThreadType] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[StoryThread]:
        """Create a thread based on participants and context."""
        if not participants:
            return None

        context = context or {}

        # Determine thread type if not specified
        if not preferred_type:
            # Simple heuristic based on participant count and context
            if len(participants) == 2:
                preferred_type = random.choice([ThreadType.ROMANCE, ThreadType.CONFLICT])
            else:
                preferred_type = random.choice([ThreadType.MYSTERY, ThreadType.QUEST])

        template = self.get_template(preferred_type, context)
        if not template:
            return None

        return template.create_thread(participants, context)
