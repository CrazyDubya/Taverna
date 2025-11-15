"""
Phase Integration Module

Connects all phase implementations (1-4) to the core game systems.
This is the critical piece that makes all our phase work actually functional.
"""

import logging
from typing import Dict, Any, Optional

# Phase 2: World System
from ..world.atmosphere import AtmosphereManager
from ..world.area_manager import AreaManager
from ..world.floor_manager import FloorManager

# Phase 3: NPC Systems
from ..npc.psychology import NPCPsychologyManager
from ..npc.secrets import SecretsManager
from ..npc.dialogue import DialogueGenerator, DialogueContext
from ..npc.gossip import GossipNetwork
from ..npc.goals import GoalManager
from ..npc.interactions import InteractionManager

# Phase 4: Narrative Engine
from ..narrative import ThreadManager, NarrativeRulesEngine, NarrativeOrchestrator, StoryThread, ThreadType
from ..narrative.event_integration import NarrativeEventHandler

logger = logging.getLogger(__name__)


class PhaseIntegration:
    """
    Master integration class that connects all phase systems.
    This replaces the basic implementations with our enhanced systems.
    """

    def __init__(self, game_state):
        """Initialize all phase systems and connect them"""
        self.game_state = game_state
        logger.info("Initializing Phase Integration...")

        # Phase 2: World System
        self._init_phase2_world_system()

        # Phase 3: NPC Systems
        self._init_phase3_npc_systems()

        # Phase 4: Narrative Engine
        self._init_phase4_narrative_engine()

        # Connect cross-phase integrations
        self._connect_cross_phase_systems()

        logger.info("Phase Integration complete - all systems connected")

    def _init_phase2_world_system(self):
        """Initialize Phase 2 world and atmosphere systems"""
        logger.info("Initializing Phase 2: World System")

        # Create managers
        self.atmosphere_manager = AtmosphereManager()
        self.area_manager = AreaManager()
        self.floor_manager = FloorManager()

        # Replace basic room system with enhanced world
        self.game_state.atmosphere_manager = self.atmosphere_manager
        self.game_state.area_manager = self.area_manager
        self.game_state.floor_manager = self.floor_manager

        # Initialize all areas and floors
        self.area_manager.initialize_all_areas()
        self.floor_manager.initialize_all_floors()

        # Set initial atmosphere for current room
        if hasattr(self.game_state, "current_room"):
            area = self.area_manager.get_area_for_room(self.game_state.current_room)
            if area:
                self.atmosphere_manager.apply_area_atmosphere(area)

    def _init_phase3_npc_systems(self):
        """Initialize Phase 3 enhanced NPC systems"""
        logger.info("Initializing Phase 3: NPC Systems")

        # Create managers
        self.npc_psychology = NPCPsychologyManager()
        self.secrets_manager = SecretsManager()
        self.dialogue_generator = DialogueGenerator()
        self.gossip_network = GossipNetwork()
        self.goal_manager = GoalManager()
        self.interaction_manager = InteractionManager()

        # Attach to game state
        self.game_state.npc_psychology = self.npc_psychology
        self.game_state.secrets_manager = self.secrets_manager
        self.game_state.dialogue_generator = self.dialogue_generator
        self.game_state.gossip_network = self.gossip_network
        self.game_state.goal_manager = self.goal_manager
        self.game_state.interaction_manager = self.interaction_manager

        # Initialize psychology for existing NPCs
        for npc_name, npc in self.game_state.npcs.items():
            self.npc_psychology.initialize_npc(npc_name, npc)

            # Load secrets if NPC has them
            if hasattr(npc, "has_secret") and npc.has_secret:
                self.secrets_manager.initialize_npc_secrets(npc_name)

            # Initialize goals
            self.goal_manager.initialize_npc_goals(npc_name, npc)

    def _init_phase4_narrative_engine(self):
        """Initialize Phase 4 narrative engine"""
        logger.info("Initializing Phase 4: Narrative Engine")

        # Create narrative components
        self.thread_manager = ThreadManager()
        self.rules_engine = NarrativeRulesEngine()
        self.narrative_orchestrator = NarrativeOrchestrator(self.thread_manager, self.rules_engine)

        # Attach to game state
        self.game_state.thread_manager = self.thread_manager
        self.game_state.rules_engine = self.rules_engine
        self.game_state.narrative_orchestrator = self.narrative_orchestrator

        # Create and connect event handler
        self.narrative_handler = NarrativeEventHandler(self.game_state, self.narrative_orchestrator)
        self.game_state.narrative_handler = self.narrative_handler

        # Create initial narrative threads based on game state
        self._create_initial_threads()

    def _connect_cross_phase_systems(self):
        """Connect systems across phases for synergy"""
        logger.info("Connecting cross-phase systems")

        # Connect atmosphere to NPC psychology
        # NPCs react to atmosphere changes
        self.atmosphere_manager.on_atmosphere_change = self._on_atmosphere_change

        # Connect NPC goals to narrative threads
        # NPC goals can spawn new narrative threads
        self.goal_manager.on_goal_achieved = self._on_npc_goal_achieved

        # Connect gossip to narrative
        # Gossip can reveal story beats
        self.gossip_network.on_rumor_spread = self._on_rumor_spread

        # Connect secrets to narrative
        # Discovering secrets advances threads
        self.secrets_manager.on_secret_discovered = self._on_secret_discovered

    def process_enhanced_command(self, command: str) -> str:
        """
        Process commands through all enhanced systems.
        This replaces the basic command processing.
        """
        base_result = self.game_state.process_command(command)

        # Enhance with narrative context
        narrative_context = self._get_narrative_enhancement(command)
        if narrative_context:
            base_result += "\n\n" + narrative_context

        # Check for atmosphere effects
        atmosphere_effect = self._get_atmosphere_effect(command)
        if atmosphere_effect:
            base_result += "\n\n" + atmosphere_effect

        return base_result

    def enhance_npc_interaction(self, npc_name: str, base_response: str) -> str:
        """
        Enhance NPC interactions with all phase systems.
        This replaces basic NPC dialogue.
        """
        npc = self.game_state.npcs.get(npc_name)
        if not npc:
            return base_response

        # Get psychological state
        psychology = self.npc_psychology.get_npc_state(npc_name)

        # Get narrative context
        narrative_context = self.narrative_handler.get_narrative_context_for_npc(npc_name)

        # Create dialogue context
        dialogue_context = DialogueContext(
            npc_name=npc_name,
            player_name="player",
            location=self.game_state.current_room,
            time_of_day=self.game_state.clock.get_time_period(),
            relationship_level=npc.get_relationship("player"),
            current_mood=psychology.get("mood", "neutral"),
            active_threads=narrative_context.get("active_threads", []),
            recent_events=self.game_state.get_recent_events(limit=5),
        )

        # Generate enhanced dialogue
        enhanced_dialogue = self.dialogue_generator.generate_dialogue(
            npc_name, dialogue_context, base_prompt=base_response
        )

        # Check for gossip
        gossip = self.gossip_network.get_npc_gossip(npc_name)
        if gossip:
            enhanced_dialogue += f"\n\n{npc_name} leans in and whispers: '{gossip}'"

        # Check for goal-driven dialogue
        current_goal = self.goal_manager.get_current_goal(npc_name)
        if current_goal and current_goal.involves_player:
            goal_dialogue = self.goal_manager.get_goal_dialogue(npc_name, current_goal)
            if goal_dialogue:
                enhanced_dialogue += f"\n\n{goal_dialogue}"

        return enhanced_dialogue

    def update_all_systems(self, elapsed_time: float):
        """Update all phase systems with time progression"""
        # Update atmosphere
        self.atmosphere_manager.update(elapsed_time)

        # Update NPC psychology
        for npc_name in self.game_state.npcs:
            self.npc_psychology.update_npc_state(npc_name, elapsed_time)

        # Process NPC goals
        self.goal_manager.update_all_goals(elapsed_time)

        # Update gossip network
        self.gossip_network.propagate_rumors(elapsed_time)

        # Narrative is updated via events, not time

    def _create_initial_threads(self):
        """Create initial narrative threads based on game state"""
        # Create a main tavern thread
        tavern_thread = StoryThread(
            id="tavern_main_thread",
            title="The Living Rusted Tankard",
            type=ThreadType.MAIN_QUEST,
            description="The ongoing story of the tavern and its patrons",
            primary_participants=["player", "bartender"],
            tension_level=0.2,
        )
        self.thread_manager.add_thread(tavern_thread)

        # Create threads for NPCs with secrets
        for npc_name, npc in self.game_state.npcs.items():
            if hasattr(npc, "has_secret") and npc.has_secret:
                secret_thread = StoryThread(
                    id=f"secret_{npc_name}",
                    title=f"{npc_name}'s Secret",
                    type=ThreadType.MYSTERY,
                    description=f"Uncover the truth about {npc_name}",
                    primary_participants=["player", npc_name],
                    tension_level=0.4,
                )
                self.thread_manager.add_thread(secret_thread)

    def _on_atmosphere_change(self, area: str, old_atmosphere: Dict, new_atmosphere: Dict):
        """Handle atmosphere changes affecting NPCs"""
        # NPCs in the area react to atmosphere
        npcs_in_area = self.area_manager.get_npcs_in_area(area)

        for npc_name in npcs_in_area:
            # Atmosphere affects mood
            if new_atmosphere.get("mood_modifier"):
                self.npc_psychology.modify_mood(npc_name, new_atmosphere["mood_modifier"])

    def _on_npc_goal_achieved(self, npc_name: str, goal: Any):
        """Handle NPC goal achievement"""
        # Create narrative thread for significant goals
        if goal.significance > 0.7:
            thread = StoryThread(
                id=f"goal_achieved_{npc_name}_{goal.id}",
                title=f"{npc_name}'s Achievement",
                type=ThreadType.CHARACTER_ARC,
                description=f"{npc_name} has achieved: {goal.description}",
                primary_participants=[npc_name, "player"],
                tension_level=0.3,
            )
            self.thread_manager.add_thread(thread)

    def _on_rumor_spread(self, rumor: Dict[str, Any]):
        """Handle rumor propagation affecting narrative"""
        # Rumors can reveal or advance narrative threads
        if rumor.get("reveals_secret"):
            secret_holder = rumor.get("about_npc")
            if secret_holder:
                # Advance the secret thread
                thread = self.thread_manager.get_thread(f"secret_{secret_holder}")
                if thread:
                    thread.tension_level = min(1.0, thread.tension_level + 0.2)

    def _on_secret_discovered(self, npc_name: str, secret: Dict[str, Any]):
        """Handle secret discovery"""
        # Progress the mystery thread
        thread = self.thread_manager.get_thread(f"secret_{npc_name}")
        if thread:
            # Move to next stage
            from ..narrative import ThreadStage

            if thread.stage == ThreadStage.RISING_ACTION:
                thread.stage = ThreadStage.CLIMAX
                thread.tension_level = 0.8

    def _get_narrative_enhancement(self, command: str) -> Optional[str]:
        """Get narrative enhancement for command result"""
        # Check if command relates to active threads
        active_threads = self.thread_manager.get_active_threads()

        for thread in active_threads:
            # Simple keyword matching for now
            if any(participant in command.lower() for participant in thread.primary_participants):
                return f"[This action relates to: {thread.title}]"

        return None

    def _get_atmosphere_effect(self, command: str) -> Optional[str]:
        """Get atmosphere effect description"""
        current_atmosphere = self.atmosphere_manager.get_current_atmosphere()

        if current_atmosphere.get("tension", 0) > 0.7:
            return "The tense atmosphere makes everyone nervous."
        elif current_atmosphere.get("comfort", 0) > 0.8:
            return "The cozy atmosphere puts everyone at ease."

        return None
