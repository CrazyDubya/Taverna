"""
Event Integration for Narrative Engine

Connects the narrative engine to the game's event system, ensuring
narrative threads respond to and influence gameplay.
"""

from typing import Dict, Any, Optional, List, Set
import logging
from dataclasses import dataclass

from ..event_bus import EventType, Event
from .story_thread import StoryThread, StoryBeat, ThreadType, ThreadStage
from .thread_manager import ThreadManager
from .orchestrator import NarrativeOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class NarrativeEffect:
    """Effect that narrative beats have on game state"""
    type: str  # 'npc_disposition', 'room_atmosphere', 'item_spawn', etc.
    target: str  # Target entity ID
    value: Any  # Effect value
    duration: Optional[float] = None  # Duration in game time, if temporary


class NarrativeEventHandler:
    """Connects narrative engine to game events"""
    
    def __init__(self, game_state, narrative_orchestrator: NarrativeOrchestrator):
        self.game_state = game_state
        self.orchestrator = narrative_orchestrator
        self.thread_manager = narrative_orchestrator.thread_manager
        
        # Track active narrative effects
        self.active_effects: List[NarrativeEffect] = []
        
        # Subscribe to game events
        event_bus = game_state.event_bus
        event_bus.subscribe(EventType.NPC_INTERACTION, self.on_npc_interaction)
        event_bus.subscribe(EventType.ROOM_CHANGE, self.on_room_change)
        event_bus.subscribe(EventType.TIME_ADVANCED, self.on_time_advanced)
        event_bus.subscribe(EventType.NPC_SPAWN, self.on_npc_spawn)
        event_bus.subscribe(EventType.NPC_DEPART, self.on_npc_depart)
        
        # Custom narrative events
        event_bus.subscribe("QUEST_STARTED", self.on_quest_started)
        event_bus.subscribe("ITEM_ACQUIRED", self.on_item_acquired)
        event_bus.subscribe("REPUTATION_CHANGED", self.on_reputation_changed)
        
        logger.info("NarrativeEventHandler initialized and subscribed to events")
    
    def on_npc_interaction(self, event: Event):
        """Handle NPC interaction events"""
        npc_name = event.data.get('npc_name')
        interaction_type = event.data.get('interaction_type', 'talk')
        
        if not npc_name:
            return
        
        # Find threads involving this NPC
        relevant_threads = self._get_threads_for_participant(npc_name)
        
        # Check if interaction triggers any beats
        for thread in relevant_threads:
            triggered_beats = self._check_interaction_triggers(
                thread, npc_name, interaction_type
            )
            
            for beat in triggered_beats:
                self._execute_narrative_beat(beat, thread)
        
        # Check for convergence opportunities
        if len(relevant_threads) > 1:
            convergences = self.thread_manager.detect_convergences()
            for convergence in convergences:
                if npc_name in convergence.shared_participants:
                    logger.info(f"Convergence opportunity detected involving {npc_name}")
                    self._handle_convergence(convergence)
    
    def on_room_change(self, event: Event):
        """Handle room change events"""
        new_room = event.data.get('new_room')
        old_room = event.data.get('old_room')
        
        if not new_room:
            return
        
        # Check if room change advances any threads
        room_threads = self._get_threads_for_location(new_room)
        
        for thread in room_threads:
            # Check if entering this room satisfies any beat prerequisites
            pending_beats = [b for b in thread.beats if not hasattr(b, 'executed')]
            
            for beat in pending_beats:
                if beat.prerequisites.get('location') == new_room:
                    logger.info(f"Room change to {new_room} triggers beat in thread {thread.id}")
                    self._execute_narrative_beat(beat, thread)
        
        # Update narrative atmosphere based on active threads
        self._update_room_atmosphere(new_room)
    
    def on_time_advanced(self, event: Event):
        """Handle time progression events"""
        current_time = event.data.get('current_time')
        elapsed = event.data.get('elapsed_minutes', 1)
        
        # Get current world state for narrative decisions
        world_state = self._build_world_state()
        
        # Let orchestrator handle time-based progression
        available_participants = self._get_available_participants()
        orchestration_actions = self.orchestrator.orchestrate_narrative(
            self.thread_manager.get_active_threads(),
            world_state
        )
        
        # Process orchestration actions
        for action in orchestration_actions:
            self._process_orchestration_action(action)
        
        # Clean up expired effects
        self._update_active_effects(elapsed)
    
    def on_npc_spawn(self, event: Event):
        """Handle NPC spawn events"""
        npc_data = event.data.get('npc')
        if not npc_data:
            return
        
        npc_name = npc_data.get('name')
        
        # Check if this NPC's arrival triggers new threads
        if self._should_create_thread_for_npc(npc_data):
            thread = self._create_npc_arrival_thread(npc_data)
            if thread:
                self.thread_manager.add_thread(thread)
                logger.info(f"Created new thread '{thread.title}' for {npc_name}'s arrival")
    
    def on_npc_depart(self, event: Event):
        """Handle NPC departure events"""
        npc_name = event.data.get('npc_name')
        if not npc_name:
            return
        
        # Check if departure affects any threads
        affected_threads = self._get_threads_for_participant(npc_name)
        
        for thread in affected_threads:
            if npc_name in thread.primary_participants:
                # Primary participant leaving might pause or alter thread
                logger.warning(f"Primary participant {npc_name} leaving thread {thread.id}")
                self._handle_participant_departure(thread, npc_name)
    
    def on_quest_started(self, event: Event):
        """Handle quest start events"""
        quest_data = event.data.get('quest')
        if not quest_data:
            return
        
        # Convert quest to narrative thread
        thread = self._create_quest_thread(quest_data)
        if thread:
            self.thread_manager.add_thread(thread)
            logger.info(f"Created narrative thread for quest: {thread.title}")
    
    def on_item_acquired(self, event: Event):
        """Handle item acquisition events"""
        item_id = event.data.get('item_id')
        source = event.data.get('source', 'found')
        
        # Check if item acquisition triggers narrative beats
        for thread in self.thread_manager.get_active_threads():
            for beat in thread.beats:
                if beat.prerequisites.get('has_item') == item_id:
                    logger.info(f"Item {item_id} acquisition triggers beat in thread {thread.id}")
                    self._execute_narrative_beat(beat, thread)
    
    def on_reputation_changed(self, event: Event):
        """Handle reputation change events"""
        faction = event.data.get('faction')
        old_value = event.data.get('old_value', 0)
        new_value = event.data.get('new_value', 0)
        
        # Check if reputation change triggers narrative consequences
        if abs(new_value - old_value) >= 20:  # Significant change
            self._handle_reputation_milestone(faction, new_value)
    
    def get_narrative_context_for_npc(self, npc_name: str) -> Dict[str, Any]:
        """Get narrative context for NPC interactions"""
        threads = self._get_threads_for_participant(npc_name)
        
        context = {
            'active_threads': [],
            'npc_role': None,
            'current_tension': 0.0,
            'suggested_topics': [],
            'emotional_state': 'neutral'
        }
        
        for thread in threads:
            thread_info = {
                'title': thread.title,
                'stage': thread.stage.value,
                'tension': thread.tension_level,
                'player_involvement': thread.player_involvement
            }
            
            # Determine NPC's role in this thread
            if npc_name in thread.primary_participants:
                thread_info['role'] = 'primary'
            else:
                thread_info['role'] = 'secondary'
            
            context['active_threads'].append(thread_info)
            context['current_tension'] = max(context['current_tension'], thread.tension_level)
            
            # Add suggested conversation topics based on thread
            if thread.stage == ThreadStage.RISING_ACTION:
                context['suggested_topics'].extend(self._get_thread_topics(thread))
        
        # Set emotional state based on tension
        if context['current_tension'] > 0.7:
            context['emotional_state'] = 'anxious'
        elif context['current_tension'] > 0.4:
            context['emotional_state'] = 'concerned'
        
        return context
    
    def apply_narrative_effects(self, effects: Dict[str, Any]) -> List[str]:
        """Apply narrative effects to game state"""
        results = []
        
        for effect_type, effect_data in effects.items():
            if effect_type == 'npc_disposition':
                # Change NPC disposition
                npc_name = effect_data.get('npc')
                change = effect_data.get('change', 0)
                if npc_name and npc_name in self.game_state.npcs:
                    old_disp = self.game_state.npcs[npc_name].disposition
                    self.game_state.npcs[npc_name].disposition += change
                    results.append(f"{npc_name}'s disposition changed from {old_disp} to {self.game_state.npcs[npc_name].disposition}")
            
            elif effect_type == 'spawn_item':
                # Create item in room
                item_id = effect_data.get('item_id')
                location = effect_data.get('location', self.game_state.current_room)
                # Implementation depends on item system
                results.append(f"Item {item_id} appeared in {location}")
            
            elif effect_type == 'trigger_event':
                # Emit custom event
                event_name = effect_data.get('event_name')
                event_data_dict = effect_data.get('data', {})
                self.game_state.event_bus.emit(Event(event_name, event_data_dict))
                results.append(f"Triggered event: {event_name}")
            
            elif effect_type == 'room_atmosphere':
                # Change room atmosphere
                room_id = effect_data.get('room', self.game_state.current_room)
                atmosphere = effect_data.get('atmosphere')
                # Store as active effect
                effect = NarrativeEffect(
                    type='room_atmosphere',
                    target=room_id,
                    value=atmosphere,
                    duration=effect_data.get('duration', 60)  # Default 1 hour
                )
                self.active_effects.append(effect)
                results.append(f"Room {room_id} atmosphere changed to: {atmosphere}")
        
        return results
    
    def _get_threads_for_participant(self, participant: str) -> List[StoryThread]:
        """Get all active threads involving a participant"""
        threads = []
        for thread in self.thread_manager.get_active_threads():
            if (participant in thread.primary_participants or 
                participant in thread.secondary_participants):
                threads.append(thread)
        return threads
    
    def _get_threads_for_location(self, location: str) -> List[StoryThread]:
        """Get threads relevant to a location"""
        threads = []
        for thread in self.thread_manager.get_active_threads():
            # Check if any beats reference this location
            for beat in thread.beats:
                if beat.prerequisites.get('location') == location:
                    threads.append(thread)
                    break
        return threads
    
    def _execute_narrative_beat(self, beat: StoryBeat, thread: StoryThread):
        """Execute a narrative beat and apply its effects"""
        logger.info(f"Executing beat '{beat.id}' in thread '{thread.title}'")
        
        # Mark beat as executed
        beat.executed = True
        
        # Apply beat effects
        if beat.effects:
            effect_results = self.apply_narrative_effects(beat.effects)
            for result in effect_results:
                logger.info(f"Beat effect: {result}")
        
        # Update thread tension if specified
        if 'tension_change' in beat.effects:
            thread.tension_level = max(0, min(1, 
                thread.tension_level + beat.effects['tension_change']))
        
        # Check for stage transition
        if beat.effects.get('stage_transition'):
            new_stage = ThreadStage[beat.effects['stage_transition'].upper()]
            thread.stage = new_stage
            logger.info(f"Thread '{thread.title}' transitioned to {new_stage.value}")
        
        # Emit narrative event for other systems
        self.game_state.event_bus.emit(Event(
            "NARRATIVE_BEAT_EXECUTED",
            {
                'thread_id': thread.id,
                'beat_id': beat.id,
                'content': beat.content,
                'participants': beat.participants
            }
        ))
    
    def _check_interaction_triggers(self, thread: StoryThread, npc: str, 
                                   interaction_type: str) -> List[StoryBeat]:
        """Check if an interaction triggers any beats"""
        triggered = []
        
        for beat in thread.beats:
            if hasattr(beat, 'executed') and beat.executed:
                continue
                
            # Check prerequisites
            prereqs = beat.prerequisites
            if prereqs.get('interact_with') == npc:
                if not prereqs.get('interaction_type') or prereqs['interaction_type'] == interaction_type:
                    triggered.append(beat)
        
        return triggered
    
    def _handle_convergence(self, convergence):
        """Handle thread convergence"""
        logger.info(f"Handling convergence: {convergence.id}")
        
        # Execute convergence through orchestrator
        world_state = self._build_world_state()
        result = self.orchestrator.execute_convergence(convergence.id, world_state)
        
        if result:
            # Apply convergence effects
            if 'effects' in result:
                self.apply_narrative_effects(result['effects'])
    
    def _update_room_atmosphere(self, room_id: str):
        """Update room atmosphere based on active narrative elements"""
        # Collect all atmosphere effects for this room
        atmospheres = []
        
        for effect in self.active_effects:
            if effect.type == 'room_atmosphere' and effect.target == room_id:
                atmospheres.append(effect.value)
        
        # Also consider thread-based atmosphere
        room_threads = self._get_threads_for_location(room_id)
        for thread in room_threads:
            if thread.tension_level > 0.7:
                atmospheres.append('tense')
            elif thread.tension_level > 0.4:
                atmospheres.append('mysterious')
        
        # Apply to room if we have atmosphere modifiers
        if atmospheres and hasattr(self.game_state.rooms.get(room_id), 'atmosphere'):
            self.game_state.rooms[room_id].atmosphere = atmospheres
    
    def _build_world_state(self) -> Dict[str, Any]:
        """Build current world state for narrative decisions"""
        return {
            'current_time': self.game_state.clock.time,
            'current_location': self.game_state.current_room,
            'active_npcs': list(self.game_state.npcs.keys()),
            'player_inventory': list(self.game_state.player.inventory.keys()),
            'reputation': dict(self.game_state.reputation.standings),
            'economy_state': {
                'player_gold': self.game_state.player.gold,
                'total_gold': self.game_state.economy.total_gold
            }
        }
    
    def _get_available_participants(self) -> Set[str]:
        """Get all available participants for narrative events"""
        participants = {'player'}
        
        # Add NPCs in current room
        current_room = self.game_state.rooms.get(self.game_state.current_room)
        if current_room:
            participants.update(current_room.npcs)
        
        # Add all active NPCs
        participants.update(self.game_state.npcs.keys())
        
        return participants
    
    def _process_orchestration_action(self, action: Dict[str, Any]):
        """Process an action from the narrative orchestrator"""
        action_type = action.get('type')
        
        if action_type == 'execute_climax':
            # Handle climactic moment
            beat_data = action.get('beat', {})
            self._execute_climax_beat(beat_data, action.get('intensity', 0.8))
        
        elif action_type == 'pause_thread':
            # Pause thread temporarily
            thread_id = action.get('thread_id')
            logger.info(f"Pausing thread {thread_id} due to {action.get('reason')}")
        
        elif action_type == 'introduce_thread':
            # Create new thread
            thread_type = action.get('thread_type', 'side_quest')
            self._create_dynamic_thread(thread_type, action.get('initial_tension', 0.3))
        
        elif action_type == 'adjust_tension':
            # Adjust thread tension
            thread_id = action.get('thread_id')
            target_tension = action.get('target_tension', 0.5)
            thread = self.thread_manager.get_thread(thread_id)
            if thread:
                thread.tension_level = target_tension
    
    def _update_active_effects(self, elapsed_minutes: int):
        """Update and clean up active narrative effects"""
        remaining_effects = []
        
        for effect in self.active_effects:
            if effect.duration is not None:
                effect.duration -= elapsed_minutes
                if effect.duration > 0:
                    remaining_effects.append(effect)
                else:
                    logger.info(f"Narrative effect expired: {effect.type} on {effect.target}")
            else:
                # Permanent effect
                remaining_effects.append(effect)
        
        self.active_effects = remaining_effects
    
    def _should_create_thread_for_npc(self, npc_data: Dict[str, Any]) -> bool:
        """Determine if an NPC arrival should create a new thread"""
        # Check if NPC has special flags or high importance
        if npc_data.get('quest_giver'):
            return True
        if npc_data.get('importance', 0) > 0.7:
            return True
        if npc_data.get('has_secret'):
            return True
        return False
    
    def _create_npc_arrival_thread(self, npc_data: Dict[str, Any]) -> Optional[StoryThread]:
        """Create a narrative thread for an NPC arrival"""
        npc_name = npc_data.get('name')
        
        # Determine thread type based on NPC
        if npc_data.get('quest_giver'):
            thread_type = ThreadType.SIDE_QUEST
        elif npc_data.get('has_secret'):
            thread_type = ThreadType.MYSTERY
        else:
            thread_type = ThreadType.SOCIAL
        
        thread = StoryThread(
            id=f"arrival_{npc_name}_{int(self.game_state.clock.time)}",
            title=f"{npc_name}'s Arrival",
            type=thread_type,
            description=f"The arrival of {npc_name} at the tavern",
            primary_participants=[npc_name, 'player'],
            tension_level=0.3 if thread_type == ThreadType.MYSTERY else 0.1
        )
        
        # Create initial beats
        thread.beats.append(StoryBeat(
            id=f"arrival_notice_{npc_name}",
            thread_id=thread.id,
            beat_type="observation",
            content=f"Notice {npc_name}'s arrival",
            participants=['player'],
            prerequisites={},
            effects={'npc_disposition': {'npc': npc_name, 'change': 5}}
        ))
        
        return thread
    
    def _create_quest_thread(self, quest_data: Dict[str, Any]) -> Optional[StoryThread]:
        """Create a narrative thread from a quest"""
        quest_id = quest_data.get('id')
        quest_name = quest_data.get('name', 'Unknown Quest')
        
        thread = StoryThread(
            id=f"quest_{quest_id}",
            title=quest_name,
            type=ThreadType.MAIN_QUEST if quest_data.get('is_main') else ThreadType.SIDE_QUEST,
            description=quest_data.get('description', ''),
            primary_participants=['player'] + quest_data.get('npcs', []),
            tension_level=0.4
        )
        
        # Generate beats from quest objectives
        for i, objective in enumerate(quest_data.get('objectives', [])):
            beat = StoryBeat(
                id=f"quest_{quest_id}_obj_{i}",
                thread_id=thread.id,
                beat_type="objective",
                content=objective.get('description', ''),
                participants=['player'],
                prerequisites=objective.get('prerequisites', {}),
                effects=objective.get('effects', {})
            )
            thread.beats.append(beat)
        
        return thread
    
    def _handle_participant_departure(self, thread: StoryThread, participant: str):
        """Handle a participant leaving an active thread"""
        if thread.stage in [ThreadStage.CLIMAX, ThreadStage.RISING_ACTION]:
            # Critical departure - might need intervention
            logger.warning(f"Critical participant {participant} departed during {thread.stage.value}")
            
            # Create intervention request
            self.game_state.event_bus.emit(Event(
                "NARRATIVE_INTERVENTION_NEEDED",
                {
                    'thread_id': thread.id,
                    'reason': 'participant_departure',
                    'participant': participant,
                    'severity': 'high' if thread.stage == ThreadStage.CLIMAX else 'medium'
                }
            ))
    
    def _handle_reputation_milestone(self, faction: str, new_value: int):
        """Handle significant reputation changes"""
        # Determine milestone type
        if new_value >= 80:
            milestone = 'allied'
        elif new_value >= 50:
            milestone = 'friendly'
        elif new_value <= -80:
            milestone = 'hostile'
        elif new_value <= -50:
            milestone = 'unfriendly'
        else:
            return
        
        # Create or modify threads based on reputation
        logger.info(f"Reputation milestone reached: {faction} is now {milestone}")
        
        # This could trigger faction-specific narrative threads
        self.game_state.event_bus.emit(Event(
            "NARRATIVE_REPUTATION_MILESTONE",
            {
                'faction': faction,
                'milestone': milestone,
                'value': new_value
            }
        ))
    
    def _get_thread_topics(self, thread: StoryThread) -> List[str]:
        """Get conversation topics based on thread content"""
        topics = []
        
        # Add topics based on thread type
        if thread.type == ThreadType.MYSTERY:
            topics.extend(['strange occurrences', 'missing items', 'suspicious behavior'])
        elif thread.type == ThreadType.ROMANCE:
            topics.extend(['relationships', 'feelings', 'future plans'])
        elif thread.type == ThreadType.POLITICAL:
            topics.extend(['local politics', 'faction tensions', 'power struggles'])
        
        # Add topics from recent beats
        for beat in thread.beats[-3:]:  # Last 3 beats
            if hasattr(beat, 'executed') and beat.executed:
                # Extract keywords from beat content
                words = beat.content.lower().split()
                topics.extend([w for w in words if len(w) > 5][:2])
        
        return list(set(topics))  # Remove duplicates
    
    def _create_dynamic_thread(self, thread_type: str, initial_tension: float):
        """Create a dynamic thread based on current game state"""
        # Implementation would analyze game state and create appropriate thread
        pass
    
    def _execute_climax_beat(self, beat_data: Dict[str, Any], intensity: float):
        """Execute a climactic narrative beat"""
        # Implementation for dramatic climax execution
        pass