"""
Story Thread Management System.
Creates and manages interconnected narrative threads that emerge from player actions.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random
import time
import logging
import uuid

logger = logging.getLogger(__name__)


class ThreadType(Enum):
    """Types of story threads that can emerge."""

    PERSONAL_RELATIONSHIP = "personal_relationship"
    BUSINESS_VENTURE = "business_venture"
    COMMUNITY_PROBLEM = "community_problem"
    MYSTERY = "mystery"
    CONFLICT = "conflict"
    ROMANCE = "romance"
    QUEST_CHAIN = "quest_chain"
    POLITICAL_INTRIGUE = "political_intrigue"
    ECONOMIC_DISRUPTION = "economic_disruption"
    SUPERNATURAL_EVENT = "supernatural_event"
    FAMILY_DRAMA = "family_drama"
    REPUTATION_CHALLENGE = "reputation_challenge"


class ThreadStatus(Enum):
    """Current status of a story thread."""

    DORMANT = "dormant"  # Thread exists but inactive
    EMERGING = "emerging"  # Just starting to develop
    ACTIVE = "active"  # Currently developing
    ESCALATING = "escalating"  # Building to climax
    CLIMAX = "climax"  # Peak moment
    RESOLVING = "resolving"  # Winding down
    RESOLVED = "resolved"  # Complete
    ABANDONED = "abandoned"  # Player ignored, faded away
    FAILED = "failed"  # Player failed to handle properly


class ThreadPriority(Enum):
    """Priority levels for story threads."""

    BACKGROUND = "background"  # Subtle, atmospheric
    LOW = "low"  # Minor side story
    MEDIUM = "medium"  # Significant subplot
    HIGH = "high"  # Major story arc
    CRITICAL = "critical"  # Main narrative focus


@dataclass
class ThreadEvent:
    """A significant event within a story thread."""

    event_id: str
    description: str
    timestamp: float
    location: str
    participants: List[str]  # NPC IDs involved
    player_action: Optional[str] = None  # What player did to trigger
    consequences: Dict[str, Any] = field(default_factory=dict)
    emotional_impact: float = 0.0  # -1.0 to 1.0
    story_significance: float = 0.5  # 0.0 to 1.0

    def age_in_hours(self) -> float:
        """Get the age of this event in hours."""
        return (time.time() - self.timestamp) / 3600.0


@dataclass
class ThreadCondition:
    """Condition that must be met for thread progression."""

    condition_type: str  # "reputation", "relationship", "item", "time", "location", etc.
    target: str  # What the condition applies to
    operator: str  # ">=", "<=", "==", "in", "not_in", etc.
    value: Any  # Required value
    description: str  # Human-readable description

    def is_met(self, game_state: Any) -> bool:
        """Check if this condition is currently met."""
        try:
            if self.condition_type == "reputation":
                # Check overall reputation level
                if hasattr(game_state, "reputation_network"):
                    rep_summary = game_state.reputation_network.get_overall_reputation_summary()
                    current_value = rep_summary["overall_score"]
                    return self._compare_values(current_value, self.operator, self.value)

            elif self.condition_type == "relationship":
                # Check relationship with specific NPC
                if hasattr(game_state, "character_memory_manager"):
                    memory = game_state.character_memory_manager.get_memory(self.target)
                    if memory:
                        current_value = memory.relationship_score
                        return self._compare_values(current_value, self.operator, self.value)

            elif self.condition_type == "time":
                # Check game time
                current_hour = game_state.clock.get_current_time().total_hours % 24
                return self._compare_values(current_hour, self.operator, self.value)

            elif self.condition_type == "location":
                # Check player location
                current_room = (
                    getattr(game_state.room_manager.current_room, "id", "")
                    if game_state.room_manager.current_room
                    else ""
                )
                if self.operator == "==":
                    return current_room == self.value
                elif self.operator == "in":
                    return current_room in self.value

            elif self.condition_type == "gold":
                # Check player gold
                current_value = game_state.player.gold
                return self._compare_values(current_value, self.operator, self.value)

            elif self.condition_type == "wait":
                # Simple time-based condition (always true after creation)
                return True

        except Exception as e:
            logger.warning(f"Error checking condition {self.condition_type}: {e}")

        return False

    def _compare_values(self, current: Any, operator: str, target: Any) -> bool:
        """Compare two values using the given operator."""
        if operator == ">=":
            return current >= target
        elif operator == "<=":
            return current <= target
        elif operator == "==":
            return current == target
        elif operator == "!=":
            return current != target
        elif operator == ">":
            return current > target
        elif operator == "<":
            return current < target
        elif operator == "in":
            return current in target
        elif operator == "not_in":
            return current not in target
        return False


@dataclass
class ThreadStage:
    """A stage within a story thread's progression."""

    stage_id: str
    title: str
    description: str
    conditions: List[ThreadCondition] = field(default_factory=list)
    events_to_trigger: List[str] = field(default_factory=list)  # Event descriptions
    npc_reactions: Dict[str, str] = field(default_factory=dict)  # NPC ID -> reaction
    world_changes: Dict[str, Any] = field(default_factory=dict)  # Changes to apply
    completion_rewards: Dict[str, Any] = field(default_factory=dict)
    time_pressure: Optional[float] = None  # Hours before stage expires
    created_at: float = field(default_factory=time.time)

    def is_ready_to_progress(self, game_state: Any) -> bool:
        """Check if all conditions are met to progress past this stage."""
        if not self.conditions:
            return True

        return all(condition.is_met(game_state) for condition in self.conditions)

    def is_expired(self) -> bool:
        """Check if this stage has expired due to time pressure."""
        if self.time_pressure is None:
            return False

        age_hours = (time.time() - self.created_at) / 3600.0
        return age_hours > self.time_pressure


class StoryThread:
    """A complete story thread with multiple stages and branching possibilities."""

    def __init__(
        self,
        thread_id: str,
        title: str,
        thread_type: ThreadType,
        description: str,
        priority: ThreadPriority = ThreadPriority.LOW,
    ):
        self.thread_id = thread_id
        self.title = title
        self.thread_type = thread_type
        self.description = description
        self.priority = priority

        # Thread state
        self.status = ThreadStatus.DORMANT
        self.current_stage_index = 0
        self.stages: List[ThreadStage] = []
        self.events: List[ThreadEvent] = []

        # Thread metadata
        self.created_at = time.time()
        self.last_updated = time.time()
        self.involved_npcs: Set[str] = set()
        self.tags: Set[str] = set()

        # Player engagement tracking
        self.player_actions_count = 0
        self.player_engagement_score = 0.0  # How actively player is participating
        self.tension_level = 0.0  # Current dramatic tension (0.0 to 1.0)

        # Thread relationships
        self.connected_threads: Set[str] = set()  # Related thread IDs
        self.conflicts_with: Set[str] = set()  # Threads this conflicts with

    def add_stage(self, stage: ThreadStage) -> None:
        """Add a new stage to the thread."""
        self.stages.append(stage)
        # Add involved NPCs from stage reactions
        self.involved_npcs.update(stage.npc_reactions.keys())
        logger.debug(f"Added stage '{stage.title}' to thread '{self.title}'")

    def get_current_stage(self) -> Optional[ThreadStage]:
        """Get the current active stage."""
        if 0 <= self.current_stage_index < len(self.stages):
            return self.stages[self.current_stage_index]
        return None

    def progress_to_next_stage(self, game_state: Any) -> bool:
        """Progress to the next stage if conditions are met."""
        current_stage = self.get_current_stage()
        if not current_stage:
            return False

        if current_stage.is_ready_to_progress(game_state):
            # Apply any world changes from completing this stage
            self._apply_stage_completion_effects(current_stage, game_state)

            # Move to next stage
            self.current_stage_index += 1
            self.last_updated = time.time()

            # Update thread status based on progression
            if self.current_stage_index >= len(self.stages):
                self.status = ThreadStatus.RESOLVED
                logger.info(f"Thread '{self.title}' completed!")
            else:
                # Determine new status based on stage progression
                progress_ratio = self.current_stage_index / len(self.stages)
                if progress_ratio < 0.3:
                    self.status = ThreadStatus.EMERGING
                elif progress_ratio < 0.7:
                    self.status = ThreadStatus.ACTIVE
                elif progress_ratio < 0.9:
                    self.status = ThreadStatus.ESCALATING
                else:
                    self.status = ThreadStatus.CLIMAX

            return True

        return False

    def _apply_stage_completion_effects(self, stage: ThreadStage, game_state: Any) -> None:
        """Apply the effects of completing a stage."""
        # Apply world changes
        for change_type, change_data in stage.world_changes.items():
            if change_type == "reputation_change":
                # Modify reputation with specific NPCs
                for npc_id, change in change_data.items():
                    if hasattr(game_state, "reputation_network"):
                        # Record a reputation-affecting action
                        game_state.reputation_network.record_player_action(
                            "story_progression",
                            "stage_completed",
                            [npc_id],
                            {"stage": stage.title, "witnessed_directly": True, "reputation_change": change},
                        )

            elif change_type == "npc_mood_change":
                # Affect NPC moods
                for npc_id, mood_effect in change_data.items():
                    if hasattr(game_state, "character_state_manager"):
                        state = game_state.character_state_manager.character_states.get(npc_id)
                        if state:
                            # Add mood modifier
                            state.mood_modifiers[f"story_{stage.stage_id}"] = (
                                mood_effect,
                                datetime.now() + timedelta(hours=24),
                            )

            elif change_type == "world_event":
                # Trigger a world event
                if hasattr(game_state, "character_state_manager"):
                    game_state.character_state_manager.apply_world_event(
                        change_data["event_type"], change_data.get("event_data", {})
                    )

        # Give rewards
        for reward_type, reward_data in stage.completion_rewards.items():
            if reward_type == "gold":
                game_state.player.gold += reward_data
            elif reward_type == "item":
                # Add item to player inventory (would need proper item creation)
                pass
            elif reward_type == "reputation":
                # Bonus reputation with all NPCs
                if hasattr(game_state, "reputation_network"):
                    for npc_id in self.involved_npcs:
                        game_state.reputation_network.record_player_action(
                            "story_heroics", "completed", [npc_id], {"reward": reward_data, "witnessed_directly": True}
                        )

    def add_event(self, event: ThreadEvent) -> None:
        """Add an event to this thread."""
        self.events.append(event)
        self.last_updated = time.time()

        # Update player engagement if this was a player action
        if event.player_action:
            self.player_actions_count += 1
            self.player_engagement_score += 0.1 * event.story_significance

            # Increase tension for significant events
            if event.story_significance > 0.7:
                self.tension_level = min(1.0, self.tension_level + 0.2)

    def calculate_relevance_score(self, current_context: Dict[str, Any]) -> float:
        """Calculate how relevant this thread is right now."""
        base_score = 0.0

        # Priority factor
        priority_weights = {
            ThreadPriority.BACKGROUND: 0.1,
            ThreadPriority.LOW: 0.3,
            ThreadPriority.MEDIUM: 0.6,
            ThreadPriority.HIGH: 0.8,
            ThreadPriority.CRITICAL: 1.0,
        }
        base_score += priority_weights[self.priority]

        # Status factor
        status_weights = {
            ThreadStatus.DORMANT: 0.1,
            ThreadStatus.EMERGING: 0.4,
            ThreadStatus.ACTIVE: 0.8,
            ThreadStatus.ESCALATING: 0.9,
            ThreadStatus.CLIMAX: 1.0,
            ThreadStatus.RESOLVING: 0.6,
            ThreadStatus.RESOLVED: 0.0,
            ThreadStatus.ABANDONED: 0.0,
            ThreadStatus.FAILED: 0.0,
        }
        base_score += status_weights[self.status]

        # Player engagement factor
        base_score += min(0.5, self.player_engagement_score * 0.1)

        # Recency factor
        hours_since_update = (time.time() - self.last_updated) / 3600.0
        recency_factor = max(0.1, 1.0 - (hours_since_update / 168.0))  # Decay over a week
        base_score *= recency_factor

        # Context relevance
        player_location = current_context.get("location", "")
        if any(player_location in event.location for event in self.events[-3:]):
            base_score += 0.2

        involved_npcs_present = current_context.get("present_npcs", [])
        if any(npc_id in involved_npcs_present for npc_id in self.involved_npcs):
            base_score += 0.3

        return min(1.0, base_score)

    def get_next_suggested_action(self) -> Optional[str]:
        """Get a suggestion for what the player could do to progress this thread."""
        current_stage = self.get_current_stage()
        if not current_stage:
            return None

        # Check which conditions are not yet met
        unmet_conditions = [
            cond
            for cond in current_stage.conditions
            if not hasattr(self, "_temp_game_state") or not cond.is_met(self._temp_game_state)
        ]

        if unmet_conditions:
            # Return description of first unmet condition
            return unmet_conditions[0].description

        return f"Continue with: {current_stage.description}"

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of this thread's current state."""
        current_stage = self.get_current_stage()

        return {
            "thread_id": self.thread_id,
            "title": self.title,
            "type": self.thread_type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "description": self.description,
            "current_stage": current_stage.title if current_stage else None,
            "progress": f"{self.current_stage_index}/{len(self.stages)}",
            "involved_npcs": list(self.involved_npcs),
            "player_engagement": self.player_engagement_score,
            "tension_level": self.tension_level,
            "events_count": len(self.events),
            "age_hours": (time.time() - self.created_at) / 3600.0,
            "next_action": self.get_next_suggested_action(),
        }


def create_relationship_thread(npc_id: str, npc_name: str, relationship_level: str) -> StoryThread:
    """Create a personal relationship thread based on current relationship."""
    thread_id = f"relationship_{npc_id}_{int(time.time())}"

    if relationship_level in ["stranger", "acquaintance"]:
        # Early relationship thread
        thread = StoryThread(
            thread_id=thread_id,
            title=f"Getting to Know {npc_name}",
            thread_type=ThreadType.PERSONAL_RELATIONSHIP,
            description=f"Building a relationship with {npc_name}",
            priority=ThreadPriority.LOW,
        )

        # Stage 1: Learn about them
        stage1 = ThreadStage(
            stage_id=f"{thread_id}_learn",
            title="Learn About Their Life",
            description=f"Have several conversations with {npc_name} to learn about their background",
            conditions=[
                ThreadCondition(
                    condition_type="relationship",
                    target=npc_id,
                    operator=">=",
                    value=0.3,
                    description=f"Continue talking with {npc_name} to build rapport",
                )
            ],
            npc_reactions={npc_id: "becomes more open and talkative"},
            completion_rewards={"reputation": 0.1},
        )

        # Stage 2: Personal connection
        stage2 = ThreadStage(
            stage_id=f"{thread_id}_connect",
            title="Personal Connection",
            description=f"Develop a genuine friendship with {npc_name}",
            conditions=[
                ThreadCondition(
                    condition_type="relationship",
                    target=npc_id,
                    operator=">=",
                    value=0.6,
                    description=f"Continue being helpful and friendly to {npc_name}",
                )
            ],
            npc_reactions={npc_id: "considers you a true friend"},
            world_changes={"npc_mood_change": {npc_id: 0.3}},
            completion_rewards={"reputation": 0.2},
        )

        thread.add_stage(stage1)
        thread.add_stage(stage2)

    elif relationship_level in ["friendly", "friend"]:
        # Deeper relationship thread
        thread = StoryThread(
            thread_id=thread_id,
            title=f"Deep Bond with {npc_name}",
            thread_type=ThreadType.PERSONAL_RELATIONSHIP,
            description=f"Becoming truly close to {npc_name}",
            priority=ThreadPriority.MEDIUM,
        )

        # This could involve personal favors, sharing secrets, etc.
        stage1 = ThreadStage(
            stage_id=f"{thread_id}_trust",
            title="Earning Deep Trust",
            description=f"Prove your loyalty to {npc_name} through actions",
            conditions=[
                ThreadCondition(
                    condition_type="relationship",
                    target=npc_id,
                    operator=">=",
                    value=0.8,
                    description=f"Continue demonstrating loyalty to {npc_name}",
                )
            ],
            npc_reactions={npc_id: "trusts you completely"},
            completion_rewards={"reputation": 0.3},
        )

        thread.add_stage(stage1)

    thread.involved_npcs.add(npc_id)
    return thread


def create_business_thread(player_gold: int, merchant_npc_id: str) -> StoryThread:
    """Create a business venture thread."""
    thread_id = f"business_{merchant_npc_id}_{int(time.time())}"

    thread = StoryThread(
        thread_id=thread_id,
        title="Business Partnership",
        thread_type=ThreadType.BUSINESS_VENTURE,
        description="Partner with a merchant to create a profitable venture",
        priority=ThreadPriority.MEDIUM,
    )

    # Stage 1: Prove financial capability
    stage1 = ThreadStage(
        stage_id=f"{thread_id}_capital",
        title="Gather Capital",
        description="Accumulate enough gold to invest in the business",
        conditions=[
            ThreadCondition(
                condition_type="gold",
                target="player",
                operator=">=",
                value=max(100, player_gold * 2),
                description=f"Gather {max(100, player_gold * 2)} gold for investment",
            )
        ],
        npc_reactions={merchant_npc_id: "is impressed by your financial acumen"},
    )

    # Stage 2: Establish partnership
    stage2 = ThreadStage(
        stage_id=f"{thread_id}_partnership",
        title="Formal Partnership",
        description="Establish the business partnership officially",
        conditions=[
            ThreadCondition(
                condition_type="wait",
                target="time",
                operator=">=",
                value=1,
                description="Wait for the business to be established",
            )
        ],
        world_changes={"reputation_change": {merchant_npc_id: 0.5}},
        completion_rewards={"gold": 50},
    )

    thread.add_stage(stage1)
    thread.add_stage(stage2)
    thread.involved_npcs.add(merchant_npc_id)

    return thread


def create_mystery_thread(trigger_event: str, location: str) -> StoryThread:
    """Create a mystery investigation thread."""
    thread_id = f"mystery_{int(time.time())}"

    thread = StoryThread(
        thread_id=thread_id,
        title="Strange Occurrences",
        thread_type=ThreadType.MYSTERY,
        description="Investigate mysterious events in the area",
        priority=ThreadPriority.HIGH,
    )

    # Stage 1: Gather clues
    stage1 = ThreadStage(
        stage_id=f"{thread_id}_investigate",
        title="Gather Information",
        description="Talk to people and investigate the mystery",
        conditions=[
            ThreadCondition(
                condition_type="location",
                target="player",
                operator="==",
                value=location,
                description=f"Visit {location} to investigate",
            )
        ],
        events_to_trigger=["You notice something strange in the area"],
    )

    # Stage 2: Uncover truth
    stage2 = ThreadStage(
        stage_id=f"{thread_id}_reveal",
        title="Uncover the Truth",
        description="Piece together the clues to solve the mystery",
        conditions=[
            ThreadCondition(
                condition_type="wait",
                target="time",
                operator=">=",
                value=2,
                description="Continue investigating to uncover the truth",
            )
        ],
        completion_rewards={"reputation": 0.4, "gold": 75},
    )

    thread.add_stage(stage1)
    thread.add_stage(stage2)

    return thread
