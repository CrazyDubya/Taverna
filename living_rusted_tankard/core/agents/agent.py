"""
Deep Agent - Complete Autonomous Agent Implementation.

Integrates all cognitive systems:
- Personality (how they think and feel)
- Needs and Drives (what motivates them)
- Emotions (how they feel)
- Beliefs (what they think is true)
- Memory (what they remember)
- Goals (what they want)
- Planning (how they achieve goals)

This is the BDI (Belief-Desire-Intention) architecture in action.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import time
import logging

from .personality import Personality
from .needs import PhysiologicalNeeds, Drive, NeedType
from .emotions import EmotionalState, EmotionType
from .beliefs import BeliefSystem, BeliefType
from .memory import EpisodicMemory, SemanticMemory, MemoryType
from .goals import GoalHierarchy, Goal, GoalType, Plan, Action

logger = logging.getLogger(__name__)


@dataclass
class DeepAgent:
    """
    A fully autonomous agent with complete cognitive architecture.

    The agent operates in a cognitive cycle:
    1. Perceive environment
    2. Update beliefs
    3. Evaluate needs and emotions
    4. Select/update goals
    5. Form/execute plans
    6. Learn from outcomes
    """

    name: str
    agent_id: str

    # Core cognitive systems
    personality: Personality = field(default_factory=Personality)
    needs: PhysiologicalNeeds = field(default_factory=PhysiologicalNeeds)
    drives: List[Drive] = field(default_factory=list)
    emotions: EmotionalState = field(default_factory=EmotionalState)
    beliefs: BeliefSystem = field(default_factory=BeliefSystem)
    episodic_memory: EpisodicMemory = field(default_factory=EpisodicMemory)
    semantic_memory: SemanticMemory = field(default_factory=SemanticMemory)
    goals: GoalHierarchy = field(default_factory=GoalHierarchy)

    # Current state
    current_location: str = "main_hall"
    current_activity: Optional[str] = None

    # Timing
    last_update: float = field(default_factory=time.time)
    game_time: float = 0.0  # Game time in hours

    def cognitive_cycle(self, game_state: Dict[str, Any]) -> Optional[Action]:
        """
        Execute one cognitive cycle and return next action.

        This is the heart of the agent - where all systems integrate.

        Args:
            game_state: Current game world state

        Returns:
            Next action to perform, or None if waiting/thinking
        """
        current_time = time.time()
        hours_passed = (current_time - self.last_update) / 3600.0

        # 1. UPDATE INTERNAL STATE
        self._update_needs(hours_passed)
        self._update_emotions(hours_passed)

        # 2. PERCEIVE ENVIRONMENT
        perceptions = self._perceive(game_state)

        # 3. UPDATE BELIEFS
        self._integrate_perceptions(perceptions)

        # 4. EVALUATE NEEDS AND FORM GOALS
        self._evaluate_needs_and_goals()

        # 5. SELECT GOAL TO PURSUE
        active_goal = self.goals.get_active_goal()
        if not active_goal or active_goal.is_complete():
            # Need to select a new goal
            active_goal = self.goals.select_goal_to_pursue(self.game_time)
            if active_goal:
                self.goals.set_active_goal(active_goal.goal_id)
                logger.info(
                    f"{self.name} selected new goal: {active_goal.description}"
                )

        # 6. PLAN OR EXECUTE
        if active_goal:
            # Check if we have a plan
            active_plan = self.goals.get_active_plan()

            if not active_plan or active_plan.is_complete():
                # Need to create a new plan
                plan = self._form_plan(active_goal)
                if plan:
                    self.goals.add_plan(
                        active_goal.goal_id, plan.actions, plan.confidence
                    )
                    self.goals.set_active_plan(plan.plan_id)
                    active_plan = plan

            # Execute next action from plan
            if active_plan:
                next_action = self.goals.get_next_action()
                if next_action:
                    self.goals.advance_plan()
                    self.last_update = current_time
                    return next_action

        # 7. DEFAULT: IDLE BEHAVIOR
        self.last_update = current_time
        return self._idle_action()

    def _update_needs(self, hours_passed: float) -> None:
        """Update physiological and psychological needs."""
        self.needs.update(hours_passed)
        self.game_time += hours_passed

    def _update_emotions(self, hours_passed: float) -> None:
        """Update emotional state."""
        self.emotions.update(hours_passed)

    def _perceive(self, game_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Perceive the current environment.

        Returns list of perceptions (observations about the world).
        """
        perceptions = []

        # Perceive location
        if "location" in game_state:
            perceptions.append(
                {
                    "type": "location",
                    "content": f"I am in {game_state['location']}",
                    "data": game_state["location"],
                }
            )

        # Perceive other agents
        if "agents_present" in game_state:
            for agent in game_state["agents_present"]:
                perceptions.append(
                    {
                        "type": "agent_present",
                        "content": f"{agent} is here",
                        "data": agent,
                    }
                )

        # Perceive events
        if "recent_events" in game_state:
            for event in game_state["recent_events"]:
                perceptions.append({"type": "event", "content": event, "data": event})

        return perceptions

    def _integrate_perceptions(self, perceptions: List[Dict[str, Any]]) -> None:
        """
        Update beliefs and memory based on perceptions.

        This is where the agent learns about the world.
        """
        for perception in perceptions:
            perception_type = perception["type"]
            content = perception["content"]
            data = perception["data"]

            # Update semantic memory (facts about the world)
            if perception_type == "location":
                self.semantic_memory.add_knowledge(
                    "my_location", content, confidence=1.0
                )

            # Update episodic memory (experiences)
            if perception_type in ["event", "agent_present"]:
                # Determine emotional valence of perception
                valence = self._appraise_perception(perception)

                self.episodic_memory.add_memory(
                    content=content,
                    location=self.current_location,
                    emotional_valence=valence,
                    emotional_intensity=abs(valence) * 0.5,
                    importance=0.5,
                )

                # If it's about another agent, update theory of mind
                if perception_type == "agent_present":
                    self.beliefs.get_theory_of_mind(data)

    def _appraise_perception(self, perception: Dict[str, Any]) -> float:
        """
        Appraise a perception for emotional significance.

        Returns emotional valence (-1.0 to 1.0).
        """
        # Simple heuristic appraisal
        # TODO: Make this more sophisticated

        content = perception["content"].lower()

        positive_words = ["help", "gift", "success", "friend", "good"]
        negative_words = ["threat", "danger", "failure", "enemy", "bad"]

        valence = 0.0

        for word in positive_words:
            if word in content:
                valence += 0.3

        for word in negative_words:
            if word in content:
                valence -= 0.3

        # Personality influences perception
        valence = self.emotions.mood.influences_perception(valence)

        return max(-1.0, min(1.0, valence))

    def _evaluate_needs_and_goals(self) -> None:
        """
        Evaluate current needs and create/update goals accordingly.

        This is where drives translate into desires.
        """
        # Check for urgent needs
        urgent_needs = self.needs.get_urgent_needs()

        for need in urgent_needs:
            # Create goal to satisfy need
            goal_description = self._need_to_goal_description(need)

            # Check if we already have this goal
            existing_goals = [
                g
                for g in self.goals.goals.values()
                if goal_description in g.description and not g.is_complete()
            ]

            if not existing_goals:
                # Create new goal
                priority = need.get_urgency()
                goal_type = self._need_to_goal_type(need)

                self.goals.add_goal(
                    description=goal_description,
                    goal_type=goal_type,
                    priority=priority,
                    motivated_by=[need.need_type.value],
                )

        # Check drives for goal formation
        for drive in self.drives:
            activation = drive.get_activation(self.needs)

            if activation > 0.6:  # Drive is strongly activated
                # Form goals based on drive
                goal_descriptions = self._drive_to_goal_descriptions(drive)

                for desc in goal_descriptions:
                    # Check if goal exists
                    existing = [
                        g
                        for g in self.goals.goals.values()
                        if desc in g.description and not g.is_complete()
                    ]

                    if not existing:
                        self.goals.add_goal(
                            description=desc,
                            goal_type=GoalType.ACHIEVEMENT,
                            priority=activation * drive.intensity,
                            motivated_by=[drive.name],
                        )

    def _need_to_goal_description(self, need: Any) -> str:
        """Convert a need into a goal description."""
        need_type = need.need_type

        descriptions = {
            NeedType.HUNGER: "Find food to eat",
            NeedType.REST: "Find a place to rest",
            NeedType.SAFETY: "Ensure my safety",
            NeedType.BELONGING: "Connect with others socially",
            NeedType.ACHIEVEMENT: "Accomplish something meaningful",
            NeedType.CURIOSITY: "Explore and learn something new",
            NeedType.RESPECT: "Earn respect from others",
        }

        return descriptions.get(need_type, f"Satisfy {need_type.value}")

    def _need_to_goal_type(self, need: Any) -> GoalType:
        """Convert a need into a goal type."""
        need_type = need.need_type

        mappings = {
            NeedType.HUNGER: GoalType.SURVIVAL,
            NeedType.REST: GoalType.SURVIVAL,
            NeedType.SAFETY: GoalType.SURVIVAL,
            NeedType.HEALTH: GoalType.SURVIVAL,
            NeedType.BELONGING: GoalType.SOCIAL,
            NeedType.ACHIEVEMENT: GoalType.ACHIEVEMENT,
            NeedType.CURIOSITY: GoalType.EXPLORATION,
            NeedType.RESPECT: GoalType.SOCIAL,
        }

        return mappings.get(need_type, GoalType.MAINTENANCE)

    def _drive_to_goal_descriptions(self, drive: Drive) -> List[str]:
        """Convert a drive into potential goal descriptions."""
        drive_goals = {
            "survival": ["Maintain health and safety", "Ensure I have resources"],
            "achievement": [
                "Complete a challenging task",
                "Improve my skills",
                "Accomplish something noteworthy",
            ],
            "affiliation": [
                "Make a new friend",
                "Strengthen relationship with someone",
                "Help someone in need",
            ],
            "autonomy": [
                "Make my own choices",
                "Resist coercion",
                "Maintain independence",
            ],
            "exploration": [
                "Discover something new",
                "Learn about the tavern's mysteries",
                "Explore unknown areas",
            ],
            "purpose": ["Find meaningful work", "Contribute to something larger"],
        }

        return drive_goals.get(drive.name, [])

    def _form_plan(self, goal: Goal) -> Optional[Plan]:
        """
        Form a plan to achieve a goal.

        This is means-end reasoning - figuring out HOW to achieve the goal.

        For now, simple hard-coded plans. In the future, this could use:
        - HTN (Hierarchical Task Network) planning
        - LLM-based plan generation
        - Learning from past successes
        """
        # Simple plan generation based on goal type and description
        actions = self._generate_actions_for_goal(goal)

        if actions:
            import hashlib

            plan_id = hashlib.md5(
                f"{goal.goal_id}:{time.time()}".encode()
            ).hexdigest()[:16]

            return Plan(
                plan_id=plan_id,
                goal_id=goal.goal_id,
                actions=actions,
                confidence=0.7,  # Moderate confidence
            )

        return None

    def _generate_actions_for_goal(self, goal: Goal) -> List[Action]:
        """Generate actions to achieve a goal."""
        # Hard-coded simple plans for now
        # TODO: Make this more sophisticated with learning

        actions = []

        if "food" in goal.description.lower():
            # Plan to get food
            actions.append(
                Action(
                    action_id="check_gold",
                    command="status",
                    description="Check if I have gold to buy food",
                    estimated_time=0.1,
                )
            )
            actions.append(
                Action(
                    action_id="buy_food",
                    command="buy bread",
                    description="Buy bread from tavern",
                    estimated_time=0.5,
                    resource_cost={"gold": 2.0},
                )
            )

        elif "rest" in goal.description.lower():
            actions.append(
                Action(
                    action_id="rest",
                    command="wait",
                    description="Rest and recover energy",
                    estimated_time=2.0,
                )
            )

        elif "connect" in goal.description.lower() or "social" in goal.description.lower():
            actions.append(
                Action(
                    action_id="greet",
                    command="interact gene_bartender talk",
                    description="Talk to Gene to socialize",
                    estimated_time=1.0,
                )
            )

        elif "explore" in goal.description.lower() or "learn" in goal.description.lower():
            actions.append(
                Action(
                    action_id="look_around",
                    command="look",
                    description="Look around to learn about environment",
                    estimated_time=0.5,
                )
            )
            actions.append(
                Action(
                    action_id="read_board",
                    command="read notice board",
                    description="Read notice board for information",
                    estimated_time=1.0,
                )
            )

        elif "accomplish" in goal.description.lower() or "task" in goal.description.lower():
            actions.append(
                Action(
                    action_id="check_jobs",
                    command="jobs",
                    description="Check available work",
                    estimated_time=0.5,
                )
            )
            actions.append(
                Action(
                    action_id="work",
                    command="work clean_tables",
                    description="Work to accomplish something",
                    estimated_time=2.0,
                )
            )

        return actions

    def _idle_action(self) -> Action:
        """Generate an idle/default action when no active goal."""
        # Default behavior based on personality

        if self.personality.extraversion > 0.6:
            # Extraverted: seek social interaction
            return Action(
                action_id="idle_social",
                command="look",
                description="Look around for people to talk to",
                estimated_time=0.5,
            )
        elif self.personality.openness > 0.6:
            # Open: seek novelty
            return Action(
                action_id="idle_explore",
                command="read notice board",
                description="See what's new",
                estimated_time=0.5,
            )
        else:
            # Default: observe
            return Action(
                action_id="idle_observe",
                command="look",
                description="Observe surroundings",
                estimated_time=0.5,
            )

    def process_outcome(
        self,
        action: Action,
        outcome: Dict[str, Any],
        success: bool
    ) -> None:
        """
        Process the outcome of an action and learn.

        Args:
            action: The action that was performed
            outcome: The result of the action
            success: Whether the action succeeded
        """
        # Create episodic memory of the event
        outcome_description = outcome.get("description", "Action completed")

        emotional_valence = 0.5 if success else -0.3
        emotional_intensity = 0.4

        self.episodic_memory.add_memory(
            content=f"I {action.description}: {outcome_description}",
            location=self.current_location,
            emotional_valence=emotional_valence,
            emotional_intensity=emotional_intensity,
            importance=0.6 if success else 0.4,
        )

        # Trigger emotions based on outcome
        if success:
            self.emotions.appraise_event(
                event_description=outcome_description,
                event_outcome="positive",
                personal_relevance=0.7,
            )
        else:
            self.emotions.appraise_event(
                event_description=outcome_description,
                event_outcome="negative",
                personal_relevance=0.6,
            )

        # Update beliefs if action revealed new information
        if "learned" in outcome:
            for fact in outcome["learned"]:
                self.semantic_memory.add_knowledge(
                    topic=fact["topic"],
                    content=fact["content"],
                    confidence=fact.get("confidence", 0.7),
                )

    def get_internal_state_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the agent's internal state.

        Useful for debugging and observation.
        """
        return {
            "name": self.name,
            "location": self.current_location,
            "activity": self.current_activity,
            "wellbeing": self.needs.get_overall_wellbeing(),
            "urgent_needs": [n.need_type.value for n in self.needs.get_urgent_needs()],
            "emotional_state": self.emotions.get_emotional_summary(),
            "beliefs_summary": self.beliefs.get_summary(),
            "memory_summary": self.episodic_memory.get_memory_summary(),
            "goals_summary": self.goals.get_goal_summary(),
            "active_goal": (
                self.goals.get_active_goal().description
                if self.goals.get_active_goal()
                else None
            ),
        }

    def to_dict(self) -> Dict:
        """Serialize complete agent state."""
        return {
            "name": self.name,
            "agent_id": self.agent_id,
            "personality": self.personality.to_dict(),
            "needs": self.needs.to_dict(),
            "drives": [d.to_dict() for d in self.drives],
            "emotions": self.emotions.to_dict(),
            "beliefs": self.beliefs.to_dict(),
            "episodic_memory": self.episodic_memory.to_dict(),
            "semantic_memory": self.semantic_memory.to_dict(),
            "goals": self.goals.to_dict(),
            "current_location": self.current_location,
            "current_activity": self.current_activity,
            "last_update": self.last_update,
            "game_time": self.game_time,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DeepAgent":
        """Deserialize agent from saved data."""
        from .needs import Drive

        personality = Personality.from_dict(data["personality"])
        needs = PhysiologicalNeeds.from_dict(data["needs"])
        drives = [Drive.from_dict(d) for d in data.get("drives", [])]
        emotions = EmotionalState.from_dict(data["emotions"])
        beliefs = BeliefSystem.from_dict(data["beliefs"])
        episodic_memory = EpisodicMemory.from_dict(data["episodic_memory"])
        semantic_memory = SemanticMemory.from_dict(data["semantic_memory"])
        goals = GoalHierarchy.from_dict(data["goals"])

        return cls(
            name=data["name"],
            agent_id=data["agent_id"],
            personality=personality,
            needs=needs,
            drives=drives,
            emotions=emotions,
            beliefs=beliefs,
            episodic_memory=episodic_memory,
            semantic_memory=semantic_memory,
            goals=goals,
            current_location=data.get("current_location", "main_hall"),
            current_activity=data.get("current_activity"),
            last_update=data.get("last_update", time.time()),
            game_time=data.get("game_time", 0.0),
        )

    def __repr__(self) -> str:
        state = self.get_internal_state_summary()
        return (
            f"DeepAgent({self.name}, "
            f"wellbeing={state['wellbeing']:.2f}, "
            f"mood={state['emotional_state']['mood']}, "
            f"active_goal='{state['active_goal']}')"
        )
