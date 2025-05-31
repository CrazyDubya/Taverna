"""
Story Orchestrator - Tension and Pacing Management.
Manages the overall narrative flow, tension, and pacing of the player's experience.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
import time
import random
import logging
import math
from .story_threads import StoryThread, ThreadType, ThreadStatus, ThreadPriority
from .consequence_engine import ConsequenceEngine, TrackedAction
from .dynamic_quest_generator import DynamicQuestGenerator, QuestType

logger = logging.getLogger(__name__)


class StoryPhase(Enum):
    """Different phases of story development."""
    INTRODUCTION = "introduction"       # Getting to know the world
    RISING_ACTION = "rising_action"    # Building tension and stakes
    COMPLICATIONS = "complications"     # Things get more complex
    CLIMAX = "climax"                  # Peak drama and tension
    FALLING_ACTION = "falling_action"  # Resolving consequences
    RESOLUTION = "resolution"          # Wrapping up storylines
    INTERLUDE = "interlude"           # Calm period between stories


class TensionLevel(Enum):
    """Current tension level in the story."""
    PEACEFUL = "peaceful"        # 0.0-0.2
    CALM = "calm"               # 0.2-0.4
    BUILDING = "building"       # 0.4-0.6
    TENSE = "tense"            # 0.6-0.8
    DRAMATIC = "dramatic"       # 0.8-1.0


class PacingMode(Enum):
    """Current pacing of the narrative."""
    LEISURELY = "leisurely"     # Slow, exploratory
    STEADY = "steady"          # Normal progression
    BRISK = "brisk"           # Faster events
    INTENSE = "intense"        # Rapid-fire events
    EXPLOSIVE = "explosive"     # Everything happening at once


@dataclass
class StoryMoment:
    """A significant moment in the player's story."""
    moment_id: str
    timestamp: float
    description: str
    emotional_impact: float  # -1.0 to 1.0
    tension_change: float   # How much this changed tension
    story_significance: float  # 0.0 to 1.0
    involved_npcs: List[str]
    tags: Set[str] = field(default_factory=set)
    
    def age_in_hours(self) -> float:
        return (time.time() - self.timestamp) / 3600.0


@dataclass
class NarrativeArc:
    """A complete narrative arc spanning multiple story threads."""
    arc_id: str
    title: str
    description: str
    theme: str  # Central theme of this arc
    
    # Arc state
    current_phase: StoryPhase = StoryPhase.INTRODUCTION
    overall_tension: float = 0.0
    target_duration_hours: float = 48.0  # Expected length of arc
    
    # Thread management
    primary_threads: Set[str] = field(default_factory=set)
    supporting_threads: Set[str] = field(default_factory=set)
    completed_threads: Set[str] = field(default_factory=set)
    
    # Timing
    started_at: float = field(default_factory=time.time)
    last_major_event: float = field(default_factory=time.time)
    
    # Player engagement
    player_investment_score: float = 0.0
    player_choices_made: List[str] = field(default_factory=list)
    
    def get_progress_ratio(self) -> float:
        """Get how far through this arc we are (0.0 to 1.0)."""
        elapsed_hours = (time.time() - self.started_at) / 3600.0
        return min(1.0, elapsed_hours / self.target_duration_hours)
    
    def calculate_target_tension(self) -> float:
        """Calculate what tension should be based on current phase."""
        phase_tensions = {
            StoryPhase.INTRODUCTION: 0.1,
            StoryPhase.RISING_ACTION: 0.4,
            StoryPhase.COMPLICATIONS: 0.6,
            StoryPhase.CLIMAX: 0.9,
            StoryPhase.FALLING_ACTION: 0.5,
            StoryPhase.RESOLUTION: 0.2,
            StoryPhase.INTERLUDE: 0.1
        }
        return phase_tensions.get(self.current_phase, 0.3)


class StoryOrchestrator:
    """Main orchestrator managing story flow, tension, and pacing."""
    
    def __init__(self):
        # Core systems integration
        self.story_threads: Dict[str, StoryThread] = {}
        self.consequence_engine = ConsequenceEngine()
        self.quest_generator = DynamicQuestGenerator()
        
        # Narrative state
        self.current_arc: Optional[NarrativeArc] = None
        self.story_moments: List[StoryMoment] = []
        self.overall_tension: float = 0.0
        self.current_pacing: PacingMode = PacingMode.STEADY
        
        # Tension management
        self.tension_decay_rate = 0.02  # How fast tension naturally decreases
        self.tension_smoothing = 0.1    # How much to smooth tension changes
        self.last_tension_update = time.time()
        
        # Pacing control
        self.event_cooldown = 1800.0    # 30 minutes between major events
        self.last_major_event = time.time()
        self.events_this_hour = 0
        self.max_events_per_hour = 3
        
        # Player behavior tracking
        self.player_engagement_score = 0.5
        self.player_preferred_pacing = PacingMode.STEADY
        self.player_action_frequency = 0.0
        self.last_player_action = time.time()
        
        # Story preferences
        self.active_themes: Set[str] = {"introduction", "exploration", "community"}
        self.story_preferences: Dict[str, float] = {
            "action": 0.5,
            "mystery": 0.4,
            "social": 0.7,
            "romance": 0.3,
            "conflict": 0.4,
            "exploration": 0.6
        }
    
    def update(self, game_state: Any) -> List[str]:
        """Main update loop for the story orchestrator."""
        notifications = []
        
        # Update tension and pacing
        self._update_tension()
        self._update_pacing()
        
        # Update integrated systems
        consequence_notifications = self.consequence_engine.update(game_state)
        quest_notifications = self.quest_generator.update(game_state)
        notifications.extend(consequence_notifications)
        notifications.extend(quest_notifications)
        
        # Update story threads
        thread_notifications = self._update_story_threads(game_state)
        notifications.extend(thread_notifications)
        
        # Check if we need narrative interventions
        intervention_notifications = self._check_narrative_interventions(game_state)
        notifications.extend(intervention_notifications)
        
        # Update current arc
        if self.current_arc:
            self._update_current_arc(game_state)
        
        return notifications
    
    def process_player_action(self, command: str, result: Dict[str, Any], 
                            game_state: Any) -> List[str]:
        """Process a player action and update all narrative systems."""
        notifications = []
        
        # Track action for consequences
        tracked_action = self.consequence_engine.create_action_from_command(
            command, result, game_state
        )
        if tracked_action:
            self.consequence_engine.track_action(tracked_action)
        
        # Update quest progress
        quest_notifications = self.quest_generator.process_player_action(command, game_state)
        notifications.extend(quest_notifications)
        
        # Update player engagement
        self._update_player_engagement(command, result)
        
        # Check if this action creates new story opportunities
        story_notifications = self._evaluate_story_opportunities(command, result, game_state)
        notifications.extend(story_notifications)
        
        # Create story moment if significant
        if self._is_significant_action(command, result):
            self._create_story_moment(command, result, game_state)
        
        return notifications
    
    def _update_tension(self):
        """Update overall tension level."""
        current_time = time.time()
        time_delta = (current_time - self.last_tension_update) / 3600.0  # Hours
        
        # Natural tension decay
        tension_decay = self.tension_decay_rate * time_delta
        target_tension = self.overall_tension - tension_decay
        
        # Factor in active threads
        thread_tension = 0.0
        active_thread_count = 0
        
        for thread in self.story_threads.values():
            if thread.status in [ThreadStatus.ACTIVE, ThreadStatus.ESCALATING, ThreadStatus.CLIMAX]:
                thread_tension += thread.tension_level * thread.priority.value * 0.2
                active_thread_count += 1
        
        if active_thread_count > 0:
            thread_tension /= active_thread_count
        
        # Factor in current arc
        arc_tension = 0.0
        if self.current_arc:
            arc_tension = self.current_arc.calculate_target_tension()
        
        # Combine all tension sources
        combined_tension = max(target_tension, thread_tension, arc_tension)
        
        # Smooth tension changes
        self.overall_tension = (
            self.overall_tension * (1 - self.tension_smoothing) +
            combined_tension * self.tension_smoothing
        )
        
        # Clamp to valid range
        self.overall_tension = max(0.0, min(1.0, self.overall_tension))
        
        self.last_tension_update = current_time
    
    def _update_pacing(self):
        """Update narrative pacing based on current conditions."""
        # Base pacing on tension level
        if self.overall_tension < 0.2:
            base_pacing = PacingMode.LEISURELY
        elif self.overall_tension < 0.4:
            base_pacing = PacingMode.STEADY
        elif self.overall_tension < 0.6:
            base_pacing = PacingMode.BRISK
        elif self.overall_tension < 0.8:
            base_pacing = PacingMode.INTENSE
        else:
            base_pacing = PacingMode.EXPLOSIVE
        
        # Factor in player engagement
        if self.player_engagement_score < 0.3:
            # Player seems disengaged, slow down
            if base_pacing.value > PacingMode.STEADY.value:
                base_pacing = PacingMode.STEADY
        elif self.player_engagement_score > 0.7:
            # Player is highly engaged, can handle faster pacing
            if base_pacing == PacingMode.LEISURELY:
                base_pacing = PacingMode.STEADY
        
        # Gradual pacing changes
        if base_pacing != self.current_pacing:
            # Don't change too abruptly
            pacing_values = list(PacingMode)
            current_index = pacing_values.index(self.current_pacing)
            target_index = pacing_values.index(base_pacing)
            
            if abs(target_index - current_index) > 1:
                # Move one step at a time
                if target_index > current_index:
                    self.current_pacing = pacing_values[current_index + 1]
                else:
                    self.current_pacing = pacing_values[current_index - 1]
            else:
                self.current_pacing = base_pacing
    
    def _update_story_threads(self, game_state: Any) -> List[str]:
        """Update all active story threads."""
        notifications = []
        
        for thread in list(self.story_threads.values()):
            # Check for thread progression
            if thread.progress_to_next_stage(game_state):
                notifications.append(f"Story development: {thread.title}")
                
                # Update tension based on thread progression
                if thread.status == ThreadStatus.ESCALATING:
                    self.overall_tension = min(1.0, self.overall_tension + 0.1)
                elif thread.status == ThreadStatus.CLIMAX:
                    self.overall_tension = min(1.0, self.overall_tension + 0.2)
                elif thread.status == ThreadStatus.RESOLVED:
                    self.overall_tension = max(0.0, self.overall_tension - 0.3)
            
            # Remove completed or abandoned threads
            if thread.status in [ThreadStatus.RESOLVED, ThreadStatus.ABANDONED, ThreadStatus.FAILED]:
                if self.current_arc:
                    self.current_arc.completed_threads.add(thread.thread_id)
                    if thread.thread_id in self.current_arc.primary_threads:
                        self.current_arc.primary_threads.remove(thread.thread_id)
                    if thread.thread_id in self.current_arc.supporting_threads:
                        self.current_arc.supporting_threads.remove(thread.thread_id)
        
        return notifications
    
    def _check_narrative_interventions(self, game_state: Any) -> List[str]:
        """Check if we need to intervene to improve narrative flow."""
        notifications = []
        current_time = time.time()
        
        # Check if tension has been too low for too long (lowered thresholds for Phase 1)
        if self.overall_tension < 0.5 and len(self.story_threads) < 3:
            time_since_last_event = current_time - self.last_major_event
            if time_since_last_event > 600:  # 10 minutes
                # Generate a new story thread to add interest
                new_thread = self._generate_tension_building_thread(game_state)
                if new_thread:
                    self.add_story_thread(new_thread)
                    notifications.append(f"Something interesting is developing: {new_thread.title}")
                    self.last_major_event = current_time
        
        # Check if player seems disengaged (lowered threshold for Phase 1)
        if self.player_engagement_score < 0.8:
            time_since_action = current_time - self.last_player_action
            if time_since_action > 1800:  # 30 minutes of inactivity
                # Create an attention-grabbing event
                attention_event = self._create_attention_grabbing_event(game_state)
                if attention_event:
                    notifications.append(attention_event)
        
        # Check if there are too many threads (overwhelming)
        active_threads = [t for t in self.story_threads.values() 
                         if t.status in [ThreadStatus.ACTIVE, ThreadStatus.ESCALATING]]
        if len(active_threads) > 5:
            # Encourage resolution of some threads
            for thread in active_threads:
                if thread.priority == ThreadPriority.LOW and random.random() < 0.3:
                    thread.status = ThreadStatus.RESOLVING
                    notifications.append(f"The situation with {thread.title} seems to be settling down.")
        
        return notifications
    
    def _generate_tension_building_thread(self, game_state: Any) -> Optional[StoryThread]:
        """Generate a new story thread to build tension."""
        from .story_threads import create_mystery_thread, create_business_thread
        
        # Choose thread type based on current story preferences
        possible_threads = []
        
        if self.story_preferences.get("mystery", 0) > 0.4:
            possible_threads.append("mystery")
        if self.story_preferences.get("conflict", 0) > 0.4:
            possible_threads.append("conflict")
        if self.story_preferences.get("social", 0) > 0.5:
            possible_threads.append("relationship")
        
        if not possible_threads:
            possible_threads = ["mystery"]  # Default fallback
        
        thread_type = random.choice(possible_threads)
        
        if thread_type == "mystery":
            location = "tavern_main"  # Default location
            if hasattr(game_state, 'room_manager') and game_state.room_manager.current_room:
                location = game_state.room_manager.current_room.id
            
            return create_mystery_thread("strange_sounds", location)
        
        elif thread_type == "relationship":
            # Find an NPC to build relationship with
            if hasattr(game_state, 'npc_manager'):
                available_npcs = list(game_state.npc_manager.npcs.keys())
                if available_npcs:
                    npc_id = random.choice(available_npcs)
                    npc = game_state.npc_manager.npcs[npc_id]
                    from .story_threads import create_relationship_thread
                    return create_relationship_thread(npc_id, npc.name, "stranger")
        
        return None
    
    def _create_attention_grabbing_event(self, game_state: Any) -> Optional[str]:
        """Create an event to grab player attention."""
        attention_events = [
            "You hear unusual sounds coming from outside.",
            "A stranger approaches you with an urgent expression.",
            "You notice something glittering in the corner.",
            "Someone calls your name from across the room.",
            "An interesting conversation catches your attention.",
            "You sense that something important is about to happen."
        ]
        
        return random.choice(attention_events)
    
    def _update_player_engagement(self, command: str, result: Dict[str, Any]):
        """Update player engagement score based on their actions."""
        current_time = time.time()
        
        # Update action frequency
        time_since_last = current_time - self.last_player_action
        if time_since_last > 0:
            # Exponential moving average
            alpha = 0.1
            action_rate = 1.0 / (time_since_last / 60.0)  # Actions per minute
            self.player_action_frequency = (
                self.player_action_frequency * (1 - alpha) + 
                action_rate * alpha
            )
        
        # Update engagement based on action type
        engagement_boost = 0.0
        
        if result.get('success', False):
            engagement_boost += 0.05
            
            # Different actions show different levels of engagement
            if 'interact' in command and 'talk' in command:
                engagement_boost += 0.1  # Social interaction shows high engagement
            elif 'buy' in command or 'sell' in command:
                engagement_boost += 0.05  # Economic activity
            elif 'help' in command or 'quest' in command:
                engagement_boost += 0.15  # Quest activity shows very high engagement
            elif 'investigate' in command or 'search' in command:
                engagement_boost += 0.12  # Exploration shows high engagement
        else:
            # Failed actions slightly reduce engagement
            engagement_boost -= 0.02
        
        # Update engagement score (with decay)
        decay = 0.05 * (time_since_last / 3600.0)  # Decay over time
        self.player_engagement_score = max(0.0, min(1.0, 
            self.player_engagement_score - decay + engagement_boost
        ))
        
        self.last_player_action = current_time
    
    def _evaluate_story_opportunities(self, command: str, result: Dict[str, Any], 
                                    game_state: Any) -> List[str]:
        """Evaluate if a player action creates new story opportunities."""
        notifications = []
        
        # Look for patterns that suggest story potential
        if 'interact' in command and 'talk' in command and result.get('success'):
            # Social interaction - potential relationship thread
            if random.random() < 0.2:  # 20% chance
                npc_id = command.split()[1] if len(command.split()) > 1 else None
                if npc_id and hasattr(game_state, 'character_memory_manager'):
                    memory = game_state.character_memory_manager.get_memory(npc_id)
                    if memory and memory.interaction_count > 3:
                        # This could develop into a relationship thread
                        notifications.append("You sense a deepening connection...")
        
        elif ('investigate' in command or 'search' in command) and result.get('success'):
            # Investigation - potential mystery thread
            if random.random() < 0.3:  # 30% chance
                notifications.append("Your investigation has uncovered something intriguing...")
        
        elif 'help' in command and result.get('success'):
            # Helping behavior - potential quest chain
            if random.random() < 0.25:  # 25% chance
                notifications.append("Your helpfulness has been noticed...")
        
        return notifications
    
    def _is_significant_action(self, command: str, result: Dict[str, Any]) -> bool:
        """Determine if an action is significant enough to create a story moment."""
        # Successful quest completions are always significant
        if 'quest' in result.get('message', '').lower() and 'complet' in result.get('message', '').lower():
            return True
        
        # First interactions with NPCs
        if 'interact' in command and 'first time' in result.get('message', ''):
            return True
        
        # Large economic transactions
        if ('buy' in command or 'sell' in command) and result.get('success'):
            # Check if this was an expensive transaction (would need price info)
            return True
        
        # Actions that mention consequences
        if any(word in result.get('message', '').lower() 
               for word in ['consequence', 'result', 'impact', 'effect']):
            return True
        
        return False
    
    def _create_story_moment(self, command: str, result: Dict[str, Any], game_state: Any):
        """Create a story moment from a significant action."""
        moment_id = f"moment_{int(time.time() * 1000)}"
        
        # Determine emotional impact
        emotional_impact = 0.0
        message = result.get('message', '').lower()
        
        if any(word in message for word in ['happy', 'pleased', 'delighted', 'grateful']):
            emotional_impact = 0.3
        elif any(word in message for word in ['sad', 'disappointed', 'upset', 'angry']):
            emotional_impact = -0.3
        elif any(word in message for word in ['excited', 'thrilled', 'amazed']):
            emotional_impact = 0.5
        elif any(word in message for word in ['worried', 'concerned', 'afraid']):
            emotional_impact = -0.2
        
        # Determine tension change
        tension_change = 0.0
        if 'conflict' in message or 'fight' in message:
            tension_change = 0.2
        elif 'resolved' in message or 'peaceful' in message:
            tension_change = -0.1
        elif 'mystery' in message or 'strange' in message:
            tension_change = 0.1
        
        # Get involved NPCs
        involved_npcs = []
        if 'interact' in command:
            parts = command.split()
            if len(parts) > 1:
                involved_npcs.append(parts[1])
        
        # Create the moment
        moment = StoryMoment(
            moment_id=moment_id,
            timestamp=time.time(),
            description=f"Player action: {command} - {result.get('message', 'Unknown result')[:100]}",
            emotional_impact=emotional_impact,
            tension_change=tension_change,
            story_significance=0.5,  # Default significance
            involved_npcs=involved_npcs
        )
        
        self.story_moments.append(moment)
        
        # Keep only recent moments
        if len(self.story_moments) > 100:
            self.story_moments = self.story_moments[-100:]
        
        # Apply tension change
        self.overall_tension = max(0.0, min(1.0, self.overall_tension + tension_change))
    
    def _update_current_arc(self, game_state: Any):
        """Update the current narrative arc."""
        if not self.current_arc:
            return
        
        progress = self.current_arc.get_progress_ratio()
        
        # Update arc phase based on progress and tension
        if progress < 0.2:
            self.current_arc.current_phase = StoryPhase.INTRODUCTION
        elif progress < 0.4:
            self.current_arc.current_phase = StoryPhase.RISING_ACTION
        elif progress < 0.6:
            if self.overall_tension > 0.6:
                self.current_arc.current_phase = StoryPhase.COMPLICATIONS
            else:
                self.current_arc.current_phase = StoryPhase.RISING_ACTION
        elif progress < 0.8:
            if self.overall_tension > 0.8:
                self.current_arc.current_phase = StoryPhase.CLIMAX
            else:
                self.current_arc.current_phase = StoryPhase.COMPLICATIONS
        elif progress < 0.95:
            self.current_arc.current_phase = StoryPhase.FALLING_ACTION
        else:
            self.current_arc.current_phase = StoryPhase.RESOLUTION
        
        # Update arc tension
        self.current_arc.overall_tension = self.overall_tension
    
    def add_story_thread(self, thread: StoryThread):
        """Add a new story thread to the orchestrator."""
        self.story_threads[thread.thread_id] = thread
        
        # Add to current arc if exists
        if self.current_arc:
            if thread.priority in [ThreadPriority.HIGH, ThreadPriority.CRITICAL]:
                self.current_arc.primary_threads.add(thread.thread_id)
            else:
                self.current_arc.supporting_threads.add(thread.thread_id)
        
        logger.info(f"Added story thread: {thread.title}")
    
    def get_story_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the story systems."""
        tension_level = TensionLevel.PEACEFUL
        if self.overall_tension >= 0.8:
            tension_level = TensionLevel.DRAMATIC
        elif self.overall_tension >= 0.6:
            tension_level = TensionLevel.TENSE
        elif self.overall_tension >= 0.4:
            tension_level = TensionLevel.BUILDING
        elif self.overall_tension >= 0.2:
            tension_level = TensionLevel.CALM
        
        active_threads = [
            thread.get_summary() for thread in self.story_threads.values()
            if thread.status in [ThreadStatus.ACTIVE, ThreadStatus.ESCALATING, ThreadStatus.CLIMAX]
        ]
        
        return {
            'overall_tension': self.overall_tension,
            'tension_level': tension_level.value,
            'current_pacing': self.current_pacing.value,
            'player_engagement': self.player_engagement_score,
            'active_threads': len(active_threads),
            'story_threads': active_threads,
            'current_arc': self.current_arc.title if self.current_arc else None,
            'arc_phase': self.current_arc.current_phase.value if self.current_arc else None,
            'recent_moments': len([m for m in self.story_moments if m.age_in_hours() < 24]),
            'consequence_stats': self.consequence_engine.get_engine_statistics(),
            'quest_stats': self.quest_generator.get_generator_statistics()
        }