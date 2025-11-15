"""
Narrative Rules Engine

This module implements the pacing rules, tension management, and narrative health
monitoring systems for the Living Rusted Tankard narrative engine.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
from collections import defaultdict, deque
import logging

from .story_thread import StoryThread, ThreadStage, ThreadType

logger = logging.getLogger(__name__)


class PacingRule(Enum):
    """Rules governing narrative pacing"""

    ESCALATION_RATE = "escalation_rate"
    TENSION_BUILDUP = "tension_buildup"
    CLIMAX_SPACING = "climax_spacing"
    RESOLUTION_TIME = "resolution_time"
    THREAD_DENSITY = "thread_density"


class NarrativeHealth(Enum):
    """Health states of the narrative system"""

    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class PacingMetrics:
    """Metrics for tracking narrative pacing"""

    tension_rate: float = 0.0  # Rate of tension increase per minute
    climax_frequency: float = 0.0  # Climaxes per hour
    thread_density: float = 0.0  # Active threads per participant
    player_involvement: float = 0.0  # Player participation ratio
    resolution_ratio: float = 0.0  # Resolved vs active threads
    last_major_event: float = 0.0  # Time since last climax

    def calculate_pacing_score(self) -> float:
        """Calculate overall pacing health score (0-1)"""
        # Ideal values for comparison
        ideal_tension_rate = 0.1  # Gradual tension buildup
        ideal_climax_freq = 0.5  # One climax every 2 hours
        ideal_density = 2.0  # 2 threads per main participant
        ideal_involvement = 0.7  # 70% player involvement
        ideal_resolution = 0.8  # 80% resolution rate

        # Calculate component scores
        tension_score = max(0, 1 - abs(self.tension_rate - ideal_tension_rate) / ideal_tension_rate)
        climax_score = max(0, 1 - abs(self.climax_frequency - ideal_climax_freq) / ideal_climax_freq)
        density_score = max(0, 1 - abs(self.thread_density - ideal_density) / ideal_density)
        involvement_score = min(1.0, self.player_involvement / ideal_involvement)
        resolution_score = min(1.0, self.resolution_ratio / ideal_resolution)

        # Weighted average
        return (
            tension_score * 0.2
            + climax_score * 0.25
            + density_score * 0.2
            + involvement_score * 0.2
            + resolution_score * 0.15
        )


@dataclass
class InterventionAction:
    """Action to take to improve narrative health"""

    type: str
    target_thread_id: Optional[str]
    parameters: Dict[str, Any]
    priority: float
    description: str

    def __lt__(self, other):
        return self.priority > other.priority  # Higher priority first


class TensionManager:
    """Manages tension levels across all narrative threads"""

    def __init__(self):
        self.global_tension: float = 0.0
        self.tension_history: deque = deque(maxlen=100)  # Last 100 measurements
        self.tension_targets: Dict[str, float] = {}  # Target tension by thread
        self.max_global_tension: float = 0.8  # Prevent overwhelming players

    def update_global_tension(self, threads: List[StoryThread]) -> float:
        """Update global tension based on active threads"""
        if not threads:
            self.global_tension = 0.0
            return self.global_tension

        # Calculate weighted tension from all threads
        total_weight = 0.0
        weighted_tension = 0.0

        for thread in threads:
            # Weight by player involvement and thread importance
            weight = thread.player_involvement * self._get_thread_weight(thread)
            weighted_tension += thread.tension_level * weight
            total_weight += weight

        if total_weight > 0:
            self.global_tension = min(weighted_tension / total_weight, self.max_global_tension)
        else:
            self.global_tension = 0.0

        self.tension_history.append((time.time(), self.global_tension))
        return self.global_tension

    def _get_thread_weight(self, thread: StoryThread) -> float:
        """Get importance weight for a thread"""
        weights = {
            ThreadType.MAIN_QUEST: 1.0,
            ThreadType.SIDE_QUEST: 0.6,
            ThreadType.CHARACTER_ARC: 0.8,
            ThreadType.MYSTERY: 0.9,
            ThreadType.ROMANCE: 0.5,
            ThreadType.POLITICAL: 0.7,
            ThreadType.ECONOMIC: 0.4,
            ThreadType.SOCIAL: 0.3,
        }
        return weights.get(thread.type, 0.5)

    def get_tension_trend(self, window_minutes: int = 30) -> float:
        """Get tension change trend over time window"""
        cutoff_time = time.time() - (window_minutes * 60)
        recent_points = [(t, tension) for t, tension in self.tension_history if t >= cutoff_time]

        if len(recent_points) < 2:
            return 0.0

        # Simple linear trend calculation
        times = [p[0] for p in recent_points]
        tensions = [p[1] for p in recent_points]

        # Calculate slope
        n = len(recent_points)
        sum_t = sum(times)
        sum_tension = sum(tensions)
        sum_t_squared = sum(t * t for t in times)
        sum_t_tension = sum(times[i] * tensions[i] for i in range(n))

        denominator = n * sum_t_squared - sum_t * sum_t
        if abs(denominator) < 1e-10:
            return 0.0

        slope = (n * sum_t_tension - sum_t * sum_tension) / denominator
        return slope * 3600  # Convert to tension change per hour

    def recommend_tension_adjustment(self, thread: StoryThread) -> float:
        """Recommend tension adjustment for a thread"""
        current_tension = thread.tension_level
        target_tension = self._calculate_target_tension(thread)

        # Gradual adjustment to avoid jarring changes
        max_change = 0.1
        difference = target_tension - current_tension

        if abs(difference) <= max_change:
            return target_tension
        else:
            return current_tension + max_change * (1 if difference > 0 else -1)

    def _calculate_target_tension(self, thread: StoryThread) -> float:
        """Calculate ideal tension for a thread based on its stage"""
        stage_tensions = {
            ThreadStage.SETUP: 0.2,
            ThreadStage.RISING_ACTION: 0.5,
            ThreadStage.CLIMAX: 0.9,
            ThreadStage.FALLING_ACTION: 0.3,
            ThreadStage.RESOLUTION: 0.1,
        }

        base_tension = stage_tensions.get(thread.stage, 0.5)

        # Adjust based on thread type
        type_multipliers = {
            ThreadType.MAIN_QUEST: 1.2,
            ThreadType.MYSTERY: 1.1,
            ThreadType.CHARACTER_ARC: 0.9,
            ThreadType.ROMANCE: 0.7,
            ThreadType.SOCIAL: 0.6,
        }

        multiplier = type_multipliers.get(thread.type, 1.0)
        return min(1.0, base_tension * multiplier)


class NarrativeRulesEngine:
    """Main engine for managing narrative rules and health"""

    def __init__(self):
        self.tension_manager = TensionManager()
        self.pacing_metrics = PacingMetrics()
        self.last_health_check = time.time()
        self.intervention_queue: List[InterventionAction] = []
        self.rule_violations: defaultdict = defaultdict(int)

        # Configurable thresholds
        self.health_thresholds = {
            NarrativeHealth.EXCELLENT: 0.9,
            NarrativeHealth.GOOD: 0.75,
            NarrativeHealth.ADEQUATE: 0.6,
            NarrativeHealth.POOR: 0.4,
            NarrativeHealth.CRITICAL: 0.0,
        }

    def evaluate_narrative_health(self, threads: List[StoryThread], world_state: Dict[str, Any]) -> NarrativeHealth:
        """Evaluate overall narrative health"""
        self._update_pacing_metrics(threads, world_state)

        pacing_score = self.pacing_metrics.calculate_pacing_score()
        tension_score = self._evaluate_tension_health(threads)
        diversity_score = self._evaluate_thread_diversity(threads)
        engagement_score = self._evaluate_player_engagement(threads)

        # Weighted overall score
        overall_score = pacing_score * 0.3 + tension_score * 0.25 + diversity_score * 0.2 + engagement_score * 0.25

        # Determine health level
        for health, threshold in self.health_thresholds.items():
            if overall_score >= threshold:
                return health

        return NarrativeHealth.CRITICAL

    def generate_interventions(self, threads: List[StoryThread], health: NarrativeHealth) -> List[InterventionAction]:
        """Generate intervention actions to improve narrative health"""
        interventions = []

        if health in [NarrativeHealth.POOR, NarrativeHealth.CRITICAL]:
            # Emergency interventions
            interventions.extend(self._generate_emergency_interventions(threads))

        if health in [NarrativeHealth.ADEQUATE, NarrativeHealth.POOR]:
            # Preventive interventions
            interventions.extend(self._generate_preventive_interventions(threads))

        # Always check for pacing issues
        interventions.extend(self._generate_pacing_interventions(threads))

        # Sort by priority
        interventions.sort()
        return interventions[:5]  # Limit to top 5 interventions

    def check_pacing_rules(self, threads: List[StoryThread]) -> List[str]:
        """Check for pacing rule violations"""
        violations = []

        # Check climax spacing
        climax_threads = [t for t in threads if t.stage == ThreadStage.CLIMAX]
        if len(climax_threads) > 2:
            violations.append("Too many simultaneous climaxes")
            self.rule_violations[PacingRule.CLIMAX_SPACING] += 1

        # Check thread density
        if len(threads) > 7:
            violations.append("Too many active threads")
            self.rule_violations[PacingRule.THREAD_DENSITY] += 1

        # Check tension escalation rate
        tension_trend = self.tension_manager.get_tension_trend()
        if tension_trend > 0.5:  # Too rapid escalation
            violations.append("Tension escalating too rapidly")
            self.rule_violations[PacingRule.ESCALATION_RATE] += 1

        # Check for stagnant threads
        current_time = time.time()
        for thread in threads:
            if hasattr(thread, "last_activity"):
                if current_time - thread.last_activity > 3600:  # 1 hour
                    violations.append(f"Thread '{thread.title}' has been stagnant")

        return violations

    def _update_pacing_metrics(self, threads: List[StoryThread], world_state: Dict[str, Any]):
        """Update pacing metrics based on current state"""
        current_time = time.time()
        time_diff = current_time - self.last_health_check

        if time_diff > 0:
            # Update tension rate
            tension_change = self.tension_manager.global_tension - getattr(self, "_last_tension", 0)
            self.pacing_metrics.tension_rate = tension_change / (time_diff / 60)  # Per minute
            self._last_tension = self.tension_manager.global_tension

        # Update other metrics
        active_threads = [t for t in threads if t.stage != ThreadStage.RESOLUTION]
        total_participants = len(set().union(*[t.primary_participants + t.secondary_participants for t in threads]))

        if total_participants > 0:
            self.pacing_metrics.thread_density = len(active_threads) / total_participants

        # Player involvement
        player_threads = [t for t in threads if "player" in t.primary_participants]
        if threads:
            self.pacing_metrics.player_involvement = len(player_threads) / len(threads)

        # Resolution ratio
        resolved_threads = [t for t in threads if t.stage == ThreadStage.RESOLUTION]
        if threads:
            self.pacing_metrics.resolution_ratio = len(resolved_threads) / len(threads)

        self.last_health_check = current_time

    def _evaluate_tension_health(self, threads: List[StoryThread]) -> float:
        """Evaluate tension management health"""
        if not threads:
            return 1.0

        # Check for appropriate tension distribution
        tension_variance = self._calculate_tension_variance(threads)
        tension_trend = abs(self.tension_manager.get_tension_trend())

        # Ideal: moderate variance, controlled trend
        variance_score = max(0, 1 - tension_variance / 0.3)  # Penalty for high variance
        trend_score = max(0, 1 - tension_trend / 0.3)  # Penalty for rapid changes

        return (variance_score + trend_score) / 2

    def _evaluate_thread_diversity(self, threads: List[StoryThread]) -> float:
        """Evaluate thread type diversity"""
        if not threads:
            return 1.0

        thread_types = [t.type for t in threads]
        unique_types = set(thread_types)

        # Encourage diversity but not chaos
        if len(unique_types) >= 3 and len(unique_types) <= 5:
            return 1.0
        elif len(unique_types) < 3:
            return len(unique_types) / 3
        else:
            return max(0.5, 1 - (len(unique_types) - 5) * 0.1)

    def _evaluate_player_engagement(self, threads: List[StoryThread]) -> float:
        """Evaluate player engagement level"""
        if not threads:
            return 0.5

        involvement_sum = sum(t.player_involvement for t in threads)
        avg_involvement = involvement_sum / len(threads)

        # Ideal involvement is around 0.7
        return max(0, 1 - abs(avg_involvement - 0.7) / 0.7)

    def _calculate_tension_variance(self, threads: List[StoryThread]) -> float:
        """Calculate variance in tension levels"""
        if len(threads) < 2:
            return 0.0

        tensions = [t.tension_level for t in threads]
        mean_tension = sum(tensions) / len(tensions)
        variance = sum((t - mean_tension) ** 2 for t in tensions) / len(tensions)
        return variance**0.5  # Standard deviation

    def _generate_emergency_interventions(self, threads: List[StoryThread]) -> List[InterventionAction]:
        """Generate emergency interventions for critical narrative health"""
        interventions = []

        # Pause overwhelming threads
        climax_threads = [t for t in threads if t.stage == ThreadStage.CLIMAX]
        if len(climax_threads) > 2:
            for thread in climax_threads[2:]:
                interventions.append(
                    InterventionAction(
                        type="pause_thread",
                        target_thread_id=thread.id,
                        parameters={"reason": "too_many_climaxes"},
                        priority=0.9,
                        description=f"Pause thread '{thread.title}' to reduce climax overload",
                    )
                )

        # Reduce tension if too high
        if self.tension_manager.global_tension > 0.8:
            high_tension_threads = [t for t in threads if t.tension_level > 0.7]
            for thread in high_tension_threads[:2]:
                interventions.append(
                    InterventionAction(
                        type="reduce_tension",
                        target_thread_id=thread.id,
                        parameters={"target_tension": 0.5},
                        priority=0.85,
                        description=f"Reduce tension in '{thread.title}' to prevent overwhelm",
                    )
                )

        return interventions

    def _generate_preventive_interventions(self, threads: List[StoryThread]) -> List[InterventionAction]:
        """Generate preventive interventions for adequate/poor narrative health"""
        interventions = []

        # Introduce new threads if too few
        if len(threads) < 3:
            interventions.append(
                InterventionAction(
                    type="introduce_thread",
                    target_thread_id=None,
                    parameters={"type": "side_quest", "tension": 0.3},
                    priority=0.6,
                    description="Introduce new side quest to increase narrative density",
                )
            )

        # Boost player involvement if low
        low_involvement_threads = [t for t in threads if t.player_involvement < 0.4]
        for thread in low_involvement_threads[:2]:
            interventions.append(
                InterventionAction(
                    type="boost_involvement",
                    target_thread_id=thread.id,
                    parameters={"target_involvement": 0.7},
                    priority=0.7,
                    description=f"Increase player involvement in '{thread.title}'",
                )
            )

        return interventions

    def _generate_pacing_interventions(self, threads: List[StoryThread]) -> List[InterventionAction]:
        """Generate interventions for pacing issues"""
        interventions = []

        # Advance stagnant threads
        current_time = time.time()
        for thread in threads:
            if hasattr(thread, "last_activity"):
                if current_time - thread.last_activity > 2700:  # 45 minutes
                    interventions.append(
                        InterventionAction(
                            type="advance_thread",
                            target_thread_id=thread.id,
                            parameters={"force_beat": True},
                            priority=0.5,
                            description=f"Advance stagnant thread '{thread.title}'",
                        )
                    )

        return interventions
