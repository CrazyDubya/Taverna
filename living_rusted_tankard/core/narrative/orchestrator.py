"""
Arc Orchestration and Climax Management

This module implements the high-level orchestration of narrative arcs,
managing the timing and coordination of climaxes across multiple story threads.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import random
from collections import defaultdict
import logging

from .story_thread import StoryThread, ThreadStage, ThreadType, StoryBeat
from .thread_manager import ThreadManager, ThreadConvergence
from .rules import NarrativeRulesEngine, NarrativeHealth, InterventionAction

logger = logging.getLogger(__name__)


class OrchestrationType(Enum):
    """Types of narrative orchestration"""
    SEQUENTIAL = "sequential"  # One climax after another
    PARALLEL = "parallel"  # Multiple climaxes at once
    CASCADING = "cascading"  # Climaxes trigger each other
    CONVERGENT = "convergent"  # Multiple threads converge to single climax


@dataclass
class ClimaticMoment:
    """A coordinated climactic moment across multiple threads"""
    id: str
    timestamp: float
    primary_thread_id: str
    supporting_thread_ids: List[str]
    orchestration_type: OrchestrationType
    intensity_level: float  # 0.0 to 1.0
    participants: Set[str]
    world_impact: Dict[str, Any]
    resolution_effects: Dict[str, Any]
    
    def get_total_threads(self) -> int:
        """Get total number of threads involved"""
        return 1 + len(self.supporting_thread_ids)


@dataclass
class ArcPlan:
    """Plan for orchestrating a narrative arc"""
    id: str
    title: str
    target_threads: List[str]
    planned_climaxes: List[ClimaticMoment]
    estimated_duration: float  # Minutes
    priority: float
    constraints: Dict[str, Any]
    success_metrics: Dict[str, float]


class ClimaticSequencer:
    """Manages the sequencing and timing of climactic moments"""
    
    def __init__(self):
        self.scheduled_climaxes: List[ClimaticMoment] = []
        self.climax_history: List[ClimaticMoment] = []
        self.min_climax_spacing = 1800  # 30 minutes minimum between major climaxes
        self.max_parallel_climaxes = 2
        
    def schedule_climax(self, thread: StoryThread, target_time: Optional[float] = None) -> Optional[ClimaticMoment]:
        """Schedule a climactic moment for a thread"""
        if target_time is None:
            target_time = self._calculate_optimal_timing(thread)
        
        # Check for conflicts
        if self._has_scheduling_conflict(target_time):
            # Try to find alternative timing
            alternative_time = self._find_alternative_timing(target_time)
            if alternative_time is None:
                logger.warning(f"Cannot schedule climax for thread {thread.id} - no available slots")
                return None
            target_time = alternative_time
        
        climax = ClimateMoment(
            id=f"climax_{thread.id}_{int(target_time)}",
            timestamp=target_time,
            primary_thread_id=thread.id,
            supporting_thread_ids=[],
            orchestration_type=OrchestrationType.SEQUENTIAL,
            intensity_level=thread.tension_level,
            participants=set(thread.primary_participants),
            world_impact={},
            resolution_effects={}
        )
        
        self.scheduled_climaxes.append(climax)
        self.scheduled_climaxes.sort(key=lambda c: c.timestamp)
        
        logger.info(f"Scheduled climax for thread {thread.id} at {target_time}")
        return climax
    
    def find_convergence_opportunities(self, threads: List[StoryThread]) -> List[ClimaticMoment]:
        """Find opportunities for converging multiple threads into a single climax"""
        opportunities = []
        current_time = time.time()
        
        # Group threads by potential convergence windows
        climax_ready_threads = [t for t in threads if t.stage == ThreadStage.RISING_ACTION 
                               and t.tension_level > 0.6]
        
        if len(climax_ready_threads) < 2:
            return opportunities
        
        # Find threads with overlapping participants
        for i, thread1 in enumerate(climax_ready_threads):
            for thread2 in climax_ready_threads[i+1:]:
                shared_participants = set(thread1.primary_participants) & set(thread2.primary_participants)
                if shared_participants or self._can_converge_thematically(thread1, thread2):
                    
                    # Calculate optimal convergence time
                    convergence_time = self._calculate_convergence_timing(thread1, thread2)
                    
                    convergence = ClimateMoment(
                        id=f"convergence_{thread1.id}_{thread2.id}_{int(convergence_time)}",
                        timestamp=convergence_time,
                        primary_thread_id=thread1.id,
                        supporting_thread_ids=[thread2.id],
                        orchestration_type=OrchestrationType.CONVERGENT,
                        intensity_level=(thread1.tension_level + thread2.tension_level) / 2,
                        participants=set(thread1.primary_participants) | set(thread2.primary_participants),
                        world_impact={},
                        resolution_effects={}
                    )
                    
                    opportunities.append(convergence)
        
        return opportunities
    
    def _calculate_optimal_timing(self, thread: StoryThread) -> float:
        """Calculate optimal timing for a thread's climax"""
        current_time = time.time()
        
        # Base timing on thread tension and stage
        if thread.stage == ThreadStage.RISING_ACTION:
            # Schedule climax when tension would naturally peak
            tension_factor = thread.tension_level
            base_delay = 1800 * (1 - tension_factor)  # 0-30 minutes based on tension
        else:
            base_delay = 900  # 15 minutes for other stages
        
        # Adjust for thread type
        type_multipliers = {
            ThreadType.MAIN_QUEST: 1.0,
            ThreadType.MYSTERY: 1.2,
            ThreadType.CHARACTER_ARC: 0.8,
            ThreadType.ROMANCE: 0.6,
            ThreadType.POLITICAL: 1.1
        }
        
        multiplier = type_multipliers.get(thread.type, 1.0)
        adjusted_delay = base_delay * multiplier
        
        return current_time + adjusted_delay
    
    def _has_scheduling_conflict(self, target_time: float) -> bool:
        """Check if target time conflicts with existing climaxes"""
        conflicts = 0
        for climax in self.scheduled_climaxes:
            time_diff = abs(climax.timestamp - target_time)
            if time_diff < self.min_climax_spacing:
                conflicts += 1
        
        return conflicts >= self.max_parallel_climaxes
    
    def _find_alternative_timing(self, preferred_time: float) -> Optional[float]:
        """Find alternative timing that avoids conflicts"""
        current_time = time.time()
        
        # Try slots before and after preferred time
        for offset in [self.min_climax_spacing, -self.min_climax_spacing, 
                      self.min_climax_spacing * 2, -self.min_climax_spacing * 2]:
            candidate_time = preferred_time + offset
            
            # Don't schedule in the past
            if candidate_time < current_time:
                continue
                
            if not self._has_scheduling_conflict(candidate_time):
                return candidate_time
        
        return None
    
    def _can_converge_thematically(self, thread1: StoryThread, thread2: StoryThread) -> bool:
        """Check if two threads can converge thematically"""
        # Certain thread types work well together
        compatible_pairs = {
            (ThreadType.MAIN_QUEST, ThreadType.CHARACTER_ARC),
            (ThreadType.MYSTERY, ThreadType.POLITICAL),
            (ThreadType.ROMANCE, ThreadType.CHARACTER_ARC),
            (ThreadType.ECONOMIC, ThreadType.POLITICAL),
            (ThreadType.SOCIAL, ThreadType.CHARACTER_ARC)
        }
        
        thread_pair = (thread1.type, thread2.type)
        return thread_pair in compatible_pairs or (thread_pair[1], thread_pair[0]) in compatible_pairs
    
    def _calculate_convergence_timing(self, thread1: StoryThread, thread2: StoryThread) -> float:
        """Calculate optimal timing for converging two threads"""
        time1 = self._calculate_optimal_timing(thread1)
        time2 = self._calculate_optimal_timing(thread2)
        
        # Take the later of the two times, plus some coordination delay
        return max(time1, time2) + 300  # 5 minute coordination buffer


class NarrativeOrchestrator:
    """Main orchestrator for managing narrative arcs and climax coordination"""
    
    def __init__(self, thread_manager: ThreadManager, rules_engine: NarrativeRulesEngine):
        self.thread_manager = thread_manager
        self.rules_engine = rules_engine
        self.sequencer = ClimaticSequencer()
        
        self.active_arcs: List[ArcPlan] = []
        self.completed_arcs: List[ArcPlan] = []
        self.orchestration_history: List[Dict[str, Any]] = []
        
        # Configuration
        self.max_concurrent_arcs = 3
        self.arc_success_threshold = 0.7
        
    def orchestrate_narrative(self, threads: List[StoryThread], 
                            world_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Main orchestration method - coordinates all narrative elements"""
        orchestration_actions = []
        
        # Evaluate current narrative health
        narrative_health = self.rules_engine.evaluate_narrative_health(threads, world_state)
        
        # Generate and execute interventions if needed
        if narrative_health in [NarrativeHealth.POOR, NarrativeHealth.CRITICAL]:
            interventions = self.rules_engine.generate_interventions(threads, narrative_health)
            orchestration_actions.extend(self._execute_interventions(interventions, threads))
        
        # Plan new arcs if needed
        if len(self.active_arcs) < self.max_concurrent_arcs:
            new_arcs = self._plan_new_arcs(threads, world_state)
            self.active_arcs.extend(new_arcs)
            for arc in new_arcs:
                orchestration_actions.append({
                    'type': 'arc_initiated',
                    'arc_id': arc.id,
                    'threads': arc.target_threads,
                    'estimated_duration': arc.estimated_duration
                })
        
        # Schedule climaxes
        climax_opportunities = self.sequencer.find_convergence_opportunities(threads)
        for opportunity in climax_opportunities[:2]:  # Limit to prevent overwhelm
            if self._should_execute_climax(opportunity, threads):
                orchestration_actions.append(self._prepare_climactic_moment(opportunity, threads))
        
        # Advance active arcs
        for arc in self.active_arcs[:]:
            arc_actions = self._advance_arc(arc, threads, world_state)
            orchestration_actions.extend(arc_actions)
            
            # Check if arc is complete
            if self._is_arc_complete(arc, threads):
                self._complete_arc(arc, threads)
        
        # Update orchestration history
        self.orchestration_history.append({
            'timestamp': time.time(),
            'narrative_health': narrative_health.value,
            'active_arcs': len(self.active_arcs),
            'actions_taken': len(orchestration_actions),
            'thread_count': len(threads)
        })
        
        return orchestration_actions
    
    def _execute_interventions(self, interventions: List[InterventionAction], 
                             threads: List[StoryThread]) -> List[Dict[str, Any]]:
        """Execute narrative interventions"""
        actions = []
        
        for intervention in interventions:
            if intervention.type == "pause_thread":
                thread = self._find_thread(intervention.target_thread_id, threads)
                if thread:
                    actions.append({
                        'type': 'pause_thread',
                        'thread_id': thread.id,
                        'reason': intervention.parameters.get('reason', 'health_intervention')
                    })
            
            elif intervention.type == "reduce_tension":
                thread = self._find_thread(intervention.target_thread_id, threads)
                if thread:
                    target_tension = intervention.parameters.get('target_tension', 0.5)
                    actions.append({
                        'type': 'adjust_tension',
                        'thread_id': thread.id,
                        'target_tension': target_tension,
                        'current_tension': thread.tension_level
                    })
            
            elif intervention.type == "introduce_thread":
                actions.append({
                    'type': 'introduce_thread',
                    'thread_type': intervention.parameters.get('type', 'side_quest'),
                    'initial_tension': intervention.parameters.get('tension', 0.3)
                })
            
            elif intervention.type == "boost_involvement":
                thread = self._find_thread(intervention.target_thread_id, threads)
                if thread:
                    target_involvement = intervention.parameters.get('target_involvement', 0.7)
                    actions.append({
                        'type': 'boost_involvement',
                        'thread_id': thread.id,
                        'target_involvement': target_involvement,
                        'current_involvement': thread.player_involvement
                    })
        
        return actions
    
    def _plan_new_arcs(self, threads: List[StoryThread], world_state: Dict[str, Any]) -> List[ArcPlan]:
        """Plan new narrative arcs based on current state"""
        new_arcs = []
        
        # Look for threads that could form an arc
        available_threads = [t for t in threads if not self._is_thread_in_arc(t.id)]
        
        if len(available_threads) >= 2:
            # Create thematic groupings
            arc_candidates = self._identify_arc_candidates(available_threads)
            
            for candidate in arc_candidates[:2]:  # Limit new arcs
                arc = ArcPlan(
                    id=f"arc_{int(time.time())}_{random.randint(1000, 9999)}",
                    title=candidate['title'],
                    target_threads=candidate['thread_ids'],
                    planned_climaxes=[],
                    estimated_duration=candidate['duration'],
                    priority=candidate['priority'],
                    constraints={},
                    success_metrics={'tension_peak': 0.8, 'resolution_rate': 0.9}
                )
                new_arcs.append(arc)
        
        return new_arcs
    
    def _should_execute_climax(self, climax: ClimaticMoment, threads: List[StoryThread]) -> bool:
        """Determine if a climactic moment should be executed"""
        current_time = time.time()
        
        # Check timing
        if climax.timestamp > current_time + 1800:  # More than 30 minutes away
            return False
        
        # Check if threads are ready
        primary_thread = self._find_thread(climax.primary_thread_id, threads)
        if not primary_thread or primary_thread.stage != ThreadStage.RISING_ACTION:
            return False
        
        # Check narrative health constraints
        if self.rules_engine.tension_manager.global_tension > 0.8:
            return False  # Too much tension already
        
        return True
    
    def _prepare_climactic_moment(self, climax: ClimaticMoment, threads: List[StoryThread]) -> Dict[str, Any]:
        """Prepare a climactic moment for execution"""
        primary_thread = self._find_thread(climax.primary_thread_id, threads)
        
        # Create climactic beat
        climactic_beat = StoryBeat(
            id=f"climax_beat_{climax.id}",
            thread_id=climax.primary_thread_id,
            beat_type="climax",
            content=f"Climactic moment for {primary_thread.title}",
            participants=list(climax.participants),
            prerequisites={},
            effects={
                'tension_change': -0.3,  # Tension release after climax
                'stage_transition': 'falling_action'
            },
            emotional_weight=0.9,
            narrative_significance=1.0
        )
        
        return {
            'type': 'execute_climax',
            'climax_id': climax.id,
            'primary_thread': climax.primary_thread_id,
            'supporting_threads': climax.supporting_thread_ids,
            'beat': climactic_beat.__dict__,
            'intensity': climax.intensity_level
        }
    
    def _advance_arc(self, arc: ArcPlan, threads: List[StoryThread], 
                    world_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advance an active narrative arc"""
        actions = []
        
        # Check progress of threads in this arc
        arc_threads = [self._find_thread(tid, threads) for tid in arc.target_threads]
        arc_threads = [t for t in arc_threads if t is not None]
        
        # Coordinate thread progression
        for thread in arc_threads:
            if thread.stage == ThreadStage.SETUP and thread.tension_level < 0.3:
                actions.append({
                    'type': 'accelerate_thread',
                    'thread_id': thread.id,
                    'target_tension': 0.4,
                    'reason': 'arc_coordination'
                })
        
        return actions
    
    def _is_arc_complete(self, arc: ArcPlan, threads: List[StoryThread]) -> bool:
        """Check if an arc has been completed"""
        arc_threads = [self._find_thread(tid, threads) for tid in arc.target_threads]
        resolved_threads = [t for t in arc_threads if t and t.stage == ThreadStage.RESOLUTION]
        
        # Arc is complete if most threads are resolved
        completion_ratio = len(resolved_threads) / max(1, len(arc.target_threads))
        return completion_ratio >= 0.75
    
    def _complete_arc(self, arc: ArcPlan, threads: List[StoryThread]):
        """Complete an arc and move it to completed list"""
        self.completed_arcs.append(arc)
        self.active_arcs.remove(arc)
        
        logger.info(f"Completed narrative arc: {arc.title}")
    
    def _find_thread(self, thread_id: str, threads: List[StoryThread]) -> Optional[StoryThread]:
        """Find a thread by ID"""
        return next((t for t in threads if t.id == thread_id), None)
    
    def _is_thread_in_arc(self, thread_id: str) -> bool:
        """Check if a thread is already part of an active arc"""
        for arc in self.active_arcs:
            if thread_id in arc.target_threads:
                return True
        return False
    
    def _identify_arc_candidates(self, threads: List[StoryThread]) -> List[Dict[str, Any]]:
        """Identify potential arc groupings from available threads"""
        candidates = []
        
        # Group by theme/type
        theme_groups = defaultdict(list)
        for thread in threads:
            theme_groups[thread.type].append(thread)
        
        # Create multi-thread arcs
        for thread_type, group_threads in theme_groups.items():
            if len(group_threads) >= 2:
                candidate = {
                    'title': f"{thread_type.value.title()} Arc",
                    'thread_ids': [t.id for t in group_threads],
                    'duration': 3600,  # 1 hour estimated
                    'priority': 0.7
                }
                candidates.append(candidate)
        
        return candidates