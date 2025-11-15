"""Thread management and convergence detection."""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random

from .story_thread import StoryThread, ThreadStage, ThreadType, BeatType, ThreadLibrary


@dataclass
class ThreadConvergence:
    """Represents a convergence between story threads."""

    id: str
    thread_ids: List[str]
    convergence_type: str  # "collision", "merger", "support", "opposition"
    convergence_point: str  # Location or beat where they converge

    # Timing
    scheduled_time: Optional[datetime] = None
    executed: bool = False

    # Participants
    shared_participants: List[str] = field(default_factory=list)
    all_participants: List[str] = field(default_factory=list)

    # Effects
    tension_multiplier: float = 1.5  # How much tension increases
    new_beats: List[str] = field(default_factory=list)  # New beats created
    resolution_paths: List[str] = field(default_factory=list)

    # Requirements
    prerequisites: List[str] = field(default_factory=list)
    player_presence_required: bool = True

    def get_dramatic_weight(self) -> float:
        """Calculate dramatic impact of this convergence."""
        base_weight = len(self.thread_ids) * 0.3
        participant_weight = len(self.shared_participants) * 0.2
        tension_weight = (self.tension_multiplier - 1.0) * 0.5

        return min(1.0, base_weight + participant_weight + tension_weight)


class ThreadManager:
    """Manages active story threads and their interactions."""

    def __init__(self, max_active_threads: int = 7):
        self.max_active_threads = max_active_threads

        # Thread storage
        self.active_threads: Dict[str, StoryThread] = {}
        self.completed_threads: Dict[str, StoryThread] = {}
        self.paused_threads: Dict[str, StoryThread] = {}

        # Convergence management
        self.detected_convergences: List[ThreadConvergence] = []
        self.executed_convergences: List[ThreadConvergence] = []

        # Thread generation
        self.thread_library = ThreadLibrary()

        # Tracking
        self.thread_history: List[Dict[str, Any]] = []
        self.last_update: datetime = datetime.now()

    def add_thread(self, thread: StoryThread) -> bool:
        """Add a new active thread."""
        if len(self.active_threads) >= self.max_active_threads:
            # Try to pause lowest priority thread
            if not self._make_room_for_thread(thread):
                return False

        self.active_threads[thread.id] = thread
        self._log_thread_event(thread.id, "added", {"priority": thread.priority})

        # Check for immediate convergences
        self._detect_convergences_for_thread(thread)

        return True

    def _make_room_for_thread(self, new_thread: StoryThread) -> bool:
        """Make room for a new thread by pausing others."""
        # Find lowest priority active thread
        lowest_priority = min(self.active_threads.values(), key=lambda t: t.priority, default=None)

        if lowest_priority and lowest_priority.priority < new_thread.priority:
            self.pause_thread(lowest_priority.id)
            return True

        return False

    def pause_thread(self, thread_id: str) -> bool:
        """Pause an active thread."""
        if thread_id in self.active_threads:
            thread = self.active_threads.pop(thread_id)
            self.paused_threads[thread_id] = thread
            self._log_thread_event(thread_id, "paused")
            return True
        return False

    def resume_thread(self, thread_id: str) -> bool:
        """Resume a paused thread."""
        if thread_id in self.paused_threads:
            thread = self.paused_threads.pop(thread_id)

            # Check if we have room
            if len(self.active_threads) >= self.max_active_threads:
                if not self._make_room_for_thread(thread):
                    # Put it back
                    self.paused_threads[thread_id] = thread
                    return False

            self.active_threads[thread_id] = thread
            self._log_thread_event(thread_id, "resumed")
            return True
        return False

    def complete_thread(self, thread_id: str, quality: float = 0.5) -> bool:
        """Complete an active thread."""
        thread = self.active_threads.get(thread_id)
        if not thread:
            return False

        thread.complete(quality)
        self.completed_threads[thread_id] = self.active_threads.pop(thread_id)
        self._log_thread_event(thread_id, "completed", {"quality": quality})

        # Check if any paused threads can now resume
        self._try_resume_paused_threads()

        return True

    def _try_resume_paused_threads(self) -> None:
        """Try to resume paused threads if there's room."""
        while len(self.active_threads) < self.max_active_threads and self.paused_threads:
            # Resume highest priority paused thread
            highest_priority = max(self.paused_threads.values(), key=lambda t: t.priority)
            self.resume_thread(highest_priority.id)

    def advance_threads(self, available_participants: Set[str], world_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advance all active threads and return events."""
        events = []

        for thread in list(self.active_threads.values()):
            if thread.completed:
                continue

            # Check if thread is stalled
            if thread.is_stalled():
                events.append(
                    {
                        "type": "thread_stalled",
                        "thread_id": thread.id,
                        "reason": "blockers" if thread.blockers else "scheduling",
                    }
                )
                continue

            # Try to execute current beat
            current_beat = thread.get_current_beat()
            if current_beat and current_beat.can_execute(world_state, available_participants):
                # Execute beat
                results = current_beat.execute(list(available_participants))

                events.append(
                    {
                        "type": "beat_executed",
                        "thread_id": thread.id,
                        "beat_id": current_beat.id,
                        "beat_type": current_beat.type.value,
                        "participants": current_beat.actual_participants,
                        "success": results["success"],
                        "tension_change": results["tension_change"],
                    }
                )

                # Apply world changes
                world_state.update(results["world_changes"])

                # Advance thread
                if not thread.advance_beat():
                    # Thread completed
                    self.complete_thread(thread.id, 0.7)  # Good completion
                    events.append({"type": "thread_completed", "thread_id": thread.id, "title": thread.title})

        # Update tension levels
        for thread in self.active_threads.values():
            thread.calculate_tension()

        self.last_update = datetime.now()
        return events

    def detect_convergences(self) -> List[ThreadConvergence]:
        """Detect potential convergences between active threads."""
        new_convergences = []
        thread_list = list(self.active_threads.values())

        for i, thread1 in enumerate(thread_list):
            for thread2 in thread_list[i + 1 :]:
                convergence_potential = thread1.check_convergence_potential(thread2)

                if convergence_potential > 0.6:  # Threshold for convergence
                    convergence = self._create_convergence(thread1, thread2, convergence_potential)
                    new_convergences.append(convergence)

        # Filter out convergences that are too similar to existing ones
        filtered = []
        for conv in new_convergences:
            if not self._is_similar_convergence(conv):
                filtered.append(conv)
                self.detected_convergences.append(conv)

        return filtered

    def _detect_convergences_for_thread(self, new_thread: StoryThread) -> None:
        """Detect convergences for a newly added thread."""
        for thread in self.active_threads.values():
            if thread.id == new_thread.id:
                continue

            potential = new_thread.check_convergence_potential(thread)
            if potential > 0.6:
                convergence = self._create_convergence(new_thread, thread, potential)
                if not self._is_similar_convergence(convergence):
                    self.detected_convergences.append(convergence)

    def _create_convergence(self, thread1: StoryThread, thread2: StoryThread, potential: float) -> ThreadConvergence:
        """Create a convergence between two threads."""
        shared_participants = list(thread1.get_all_participants() & thread2.get_all_participants())
        all_participants = list(thread1.get_all_participants() | thread2.get_all_participants())

        # Determine convergence type
        if thread1.type == ThreadType.CONFLICT or thread2.type == ThreadType.CONFLICT:
            conv_type = "collision"
            tension_mult = 2.0
        elif thread1.stage == thread2.stage and thread1.stage == ThreadStage.CLIMAX:
            conv_type = "collision"
            tension_mult = 1.8
        else:
            conv_type = "merger"
            tension_mult = 1.3

        convergence = ThreadConvergence(
            id=f"conv_{thread1.id}_{thread2.id}_{datetime.now().timestamp()}",
            thread_ids=[thread1.id, thread2.id],
            convergence_type=conv_type,
            convergence_point="main_hall",  # Default location
            shared_participants=shared_participants,
            all_participants=all_participants,
            tension_multiplier=tension_mult,
        )

        return convergence

    def _is_similar_convergence(self, new_convergence: ThreadConvergence) -> bool:
        """Check if a similar convergence already exists."""
        for existing in self.detected_convergences:
            # Same threads involved
            if set(existing.thread_ids) == set(new_convergence.thread_ids):
                return True

            # Very similar participants
            existing_participants = set(existing.all_participants)
            new_participants = set(new_convergence.all_participants)
            similarity = len(existing_participants & new_participants) / len(existing_participants | new_participants)

            if similarity > 0.8:
                return True

        return False

    def execute_convergence(self, convergence_id: str, world_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a detected convergence."""
        convergence = next((c for c in self.detected_convergences if c.id == convergence_id), None)

        if not convergence or convergence.executed:
            return None

        # Get involved threads
        threads = [self.active_threads[tid] for tid in convergence.thread_ids if tid in self.active_threads]

        if len(threads) != len(convergence.thread_ids):
            return None  # Some threads no longer active

        # Create convergence beat
        convergence_beat = self._create_convergence_beat(convergence, threads)

        # Add beat to all involved threads
        for thread in threads:
            thread.beats.append(convergence_beat)

        # Execute immediately if conditions met
        if convergence_beat.can_execute(world_state, set(convergence.all_participants)):
            results = convergence_beat.execute(convergence.all_participants)

            # Apply tension multiplier
            for thread in threads:
                thread.tension_level *= convergence.tension_multiplier
                thread.tension_level = min(1.0, thread.tension_level)

            convergence.executed = True
            self.executed_convergences.append(convergence)

            return {
                "type": "convergence_executed",
                "convergence_id": convergence_id,
                "threads": [t.id for t in threads],
                "participants": convergence.all_participants,
                "tension_change": results["tension_change"] * convergence.tension_multiplier,
                "new_beats": convergence.new_beats,
            }

        return None

    def _create_convergence_beat(self, convergence: ThreadConvergence, threads: List[StoryThread]) -> "StoryBeat":
        """Create a story beat for the convergence."""
        from .story_thread import StoryBeat  # Import here to avoid circular import

        beat_descriptions = {
            "collision": f"The paths of {' and '.join(convergence.shared_participants)} collide dramatically",
            "merger": f"The stories of {' and '.join(convergence.shared_participants)} intertwine",
            "support": f"{convergence.shared_participants[0]} aids in the unfolding drama",
            "opposition": f"Forces align against {' and '.join(convergence.shared_participants)}",
        }

        description = beat_descriptions.get(
            convergence.convergence_type, f"The threads converge around {' and '.join(convergence.shared_participants)}"
        )

        beat = StoryBeat(
            id=f"{convergence.id}_beat",
            type=BeatType.CONFRONTATION,
            description=description,
            participants=convergence.all_participants,
            location=convergence.convergence_point,
            tension_change=0.5 * convergence.tension_multiplier,
            player_agency=0.8,  # High agency in convergences
        )

        return beat

    def get_thread_status(self) -> Dict[str, Any]:
        """Get status of all threads."""
        return {
            "active_threads": len(self.active_threads),
            "completed_threads": len(self.completed_threads),
            "paused_threads": len(self.paused_threads),
            "detected_convergences": len(self.detected_convergences),
            "executed_convergences": len(self.executed_convergences),
            "total_tension": sum(t.tension_level for t in self.active_threads.values()),
            "average_tension": sum(t.tension_level for t in self.active_threads.values())
            / max(len(self.active_threads), 1),
        }

    def get_narrative_summary(self) -> Dict[str, Any]:
        """Get summary of current narrative state."""
        active_by_stage = {}
        for thread in self.active_threads.values():
            stage = thread.stage.value
            active_by_stage[stage] = active_by_stage.get(stage, 0) + 1

        active_by_type = {}
        for thread in self.active_threads.values():
            thread_type = thread.type.value
            active_by_type[thread_type] = active_by_type.get(thread_type, 0) + 1

        return {
            "active_threads_by_stage": active_by_stage,
            "active_threads_by_type": active_by_type,
            "threads_near_climax": len([t for t in self.active_threads.values() if t.stage == ThreadStage.CLIMAX]),
            "high_tension_threads": len([t for t in self.active_threads.values() if t.tension_level > 0.7]),
            "stalled_threads": len([t for t in self.active_threads.values() if t.is_stalled()]),
            "pending_convergences": len([c for c in self.detected_convergences if not c.executed]),
        }

    def suggest_new_threads(self, available_participants: List[str], context: Dict[str, Any]) -> List[StoryThread]:
        """Suggest new threads based on current state."""
        suggestions = []

        # Don't suggest if we're at capacity
        if len(self.active_threads) >= self.max_active_threads:
            return suggestions

        # Analyze current thread gaps
        active_types = {t.type for t in self.active_threads.values()}

        # Suggest missing thread types
        if ThreadType.ROMANCE not in active_types and len(available_participants) >= 2:
            romance_thread = self.thread_library.create_thread_from_participants(
                available_participants[:2], ThreadType.ROMANCE, context
            )
            if romance_thread:
                suggestions.append(romance_thread)

        if ThreadType.MYSTERY not in active_types:
            mystery_thread = self.thread_library.create_thread_from_participants(
                available_participants[:3], ThreadType.MYSTERY, context
            )
            if mystery_thread:
                suggestions.append(mystery_thread)

        # Suggest based on low tension
        if self.get_thread_status()["average_tension"] < 0.3:
            conflict_thread = self.thread_library.create_thread_from_participants(
                available_participants[:2], ThreadType.CONFLICT, context
            )
            if conflict_thread:
                suggestions.append(conflict_thread)

        return suggestions[:2]  # Maximum 2 suggestions

    def _log_thread_event(self, thread_id: str, event_type: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log a thread event for analysis."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "thread_id": thread_id,
            "event_type": event_type,
            "details": details or {},
        }
        self.thread_history.append(event)

        # Keep only recent history
        if len(self.thread_history) > 1000:
            self.thread_history = self.thread_history[-800:]

    def cleanup_old_data(self, days_old: int = 7) -> None:
        """Clean up old completed threads and convergences."""
        cutoff = datetime.now() - timedelta(days=days_old)

        # Remove old completed threads
        old_completed = []
        for thread_id, thread in self.completed_threads.items():
            if thread.completion_time and thread.completion_time < cutoff:
                old_completed.append(thread_id)

        for thread_id in old_completed:
            del self.completed_threads[thread_id]

        # Remove old convergences
        self.executed_convergences = [
            conv for conv in self.executed_convergences if conv.scheduled_time is None or conv.scheduled_time > cutoff
        ]

        # Remove old history
        self.thread_history = [
            event for event in self.thread_history if datetime.fromisoformat(event["timestamp"]) > cutoff
        ]

    def get_active_threads(self) -> List[StoryThread]:
        """Get all currently active threads"""
        return list(self.active_threads.values())

    def get_thread(self, thread_id: str) -> Optional[StoryThread]:
        """Get a specific thread by ID"""
        return self.active_threads.get(thread_id) or self.completed_threads.get(thread_id)
