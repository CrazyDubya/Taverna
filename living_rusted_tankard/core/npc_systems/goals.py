"""NPC goals and agency system."""

from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import random

from .psychology import NPCPsychology, MotivationType, Personality
from .behavioral_rules import (
    BehaviorRule,
    Action,
    Condition,
    ConditionType,
    BehaviorPriority,
)


class GoalType(Enum):
    """Types of goals NPCs can pursue."""

    IMMEDIATE = "immediate"  # Right now (get food, sleep)
    SHORT_TERM = "short_term"  # Today/tomorrow
    LONG_TERM = "long_term"  # Weeks/months
    LIFE_GOAL = "life_goal"  # Major life objectives


class GoalCategory(Enum):
    """Categories of goals."""

    SURVIVAL = "survival"
    SOCIAL = "social"
    FINANCIAL = "financial"
    PROFESSIONAL = "professional"
    ROMANTIC = "romantic"
    KNOWLEDGE = "knowledge"
    REVENGE = "revenge"
    POWER = "power"
    CREATIVE = "creative"
    SPIRITUAL = "spiritual"


class GoalStatus(Enum):
    """Status of a goal."""

    PLANNING = "planning"  # Figuring out how
    ACTIVE = "active"  # Actively pursuing
    BLOCKED = "blocked"  # Can't proceed
    SUSPENDED = "suspended"  # Temporarily on hold
    COMPLETED = "completed"  # Successfully achieved
    FAILED = "failed"  # Cannot be completed
    ABANDONED = "abandoned"  # Given up


@dataclass
class GoalStep:
    """A step toward achieving a goal."""

    description: str
    action_required: Action

    # Requirements
    prerequisites: List[str] = field(default_factory=list)  # Other steps needed first
    conditions: List[Condition] = field(default_factory=list)
    resources_needed: Dict[str, Any] = field(default_factory=dict)

    # Progress
    completed: bool = False
    attempts: int = 0
    last_attempt: Optional[datetime] = None

    # Difficulty
    difficulty: float = 0.5  # 0-1
    time_estimate: float = 1.0  # Hours

    def can_attempt(self, available_resources: Dict[str, Any]) -> bool:
        """Check if step can be attempted."""
        if self.completed:
            return False

        # Check resources
        for resource, amount in self.resources_needed.items():
            if available_resources.get(resource, 0) < amount:
                return False

        # Check cooldown
        if self.last_attempt:
            cooldown = timedelta(hours=self.difficulty * 2)
            if datetime.now() - self.last_attempt < cooldown:
                return False

        return True

    def attempt(self, skill_level: float = 0.5) -> bool:
        """Attempt to complete the step."""
        self.attempts += 1
        self.last_attempt = datetime.now()

        # Success chance based on skill vs difficulty
        success_chance = skill_level * (1.0 - self.difficulty) + 0.2

        if random.random() < success_chance:
            self.completed = True
            return True

        return False


@dataclass
class Goal:
    """A goal that an NPC is pursuing."""

    id: str
    name: str
    description: str
    type: GoalType
    category: GoalCategory
    owner_id: str

    # Importance and urgency
    importance: float = 0.5  # 0-1, how important to NPC
    urgency: float = 0.5  # 0-1, how time-sensitive

    # Status
    status: GoalStatus = GoalStatus.PLANNING
    progress: float = 0.0  # 0-1, overall completion

    # Steps to achieve
    steps: List[GoalStep] = field(default_factory=list)
    current_step: int = 0

    # Requirements and blockers
    prerequisites: List[str] = field(default_factory=list)  # Other goal IDs
    blockers: List[str] = field(default_factory=list)  # What's preventing progress
    enables: List[str] = field(default_factory=list)  # Goals this enables

    # Conflicts
    conflicts_with: List[str] = field(default_factory=list)  # Incompatible goals

    # Motivation
    motivation_type: Optional[MotivationType] = None
    motivation_strength: float = 0.5

    # Lifecycle
    created: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    completed: Optional[datetime] = None

    # Consequences
    success_effects: Dict[str, Any] = field(default_factory=dict)
    failure_effects: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: GoalStep) -> None:
        """Add a step to achieve the goal."""
        self.steps.append(step)
        self._update_progress()

    def get_current_step(self) -> Optional[GoalStep]:
        """Get the current step to work on."""
        if self.status != GoalStatus.ACTIVE:
            return None

        # Find first incomplete step with satisfied prerequisites
        for i, step in enumerate(self.steps):
            if not step.completed:
                # Check prerequisites
                prereqs_met = all(
                    self.steps[self._find_step_index(prereq)].completed
                    for prereq in step.prerequisites
                    if self._find_step_index(prereq) >= 0
                )

                if prereqs_met:
                    self.current_step = i
                    return step

        return None

    def _find_step_index(self, description: str) -> int:
        """Find step index by description."""
        for i, step in enumerate(self.steps):
            if step.description == description:
                return i
        return -1

    def complete_step(self, step_index: int) -> None:
        """Mark a step as completed."""
        if 0 <= step_index < len(self.steps):
            self.steps[step_index].completed = True
            self._update_progress()

    def _update_progress(self) -> None:
        """Update overall progress."""
        if not self.steps:
            self.progress = 0.0
            return

        completed_steps = sum(1 for step in self.steps if step.completed)
        self.progress = completed_steps / len(self.steps)

        # Update status
        if self.progress >= 1.0:
            self.status = GoalStatus.COMPLETED
            self.completed = datetime.now()
        elif self.blockers:
            self.status = GoalStatus.BLOCKED
        elif self.status == GoalStatus.PLANNING and self.steps:
            self.status = GoalStatus.ACTIVE

    def is_achievable(self) -> bool:
        """Check if goal can still be achieved."""
        if self.status in [
            GoalStatus.COMPLETED,
            GoalStatus.FAILED,
            GoalStatus.ABANDONED,
        ]:
            return False

        # Check deadline
        if self.deadline and datetime.now() > self.deadline:
            self.status = GoalStatus.FAILED
            return False

        # Check if permanently blocked
        if len(self.blockers) > 3:  # Too many blockers
            return False

        return True

    def calculate_priority(self, context: Dict[str, Any]) -> float:
        """Calculate current priority of this goal."""
        base_priority = (self.importance + self.urgency) / 2

        # Increase priority as deadline approaches
        if self.deadline:
            time_left = (self.deadline - datetime.now()).total_seconds()
            if time_left < 86400:  # Less than a day
                base_priority *= 1.5
            elif time_left < 604800:  # Less than a week
                base_priority *= 1.2

        # Decrease if blocked
        if self.blockers:
            base_priority *= 0.7

        # Increase if prerequisites are met
        if not self.prerequisites:
            base_priority *= 1.1

        return min(1.0, base_priority)

    def get_resource_requirements(self) -> Dict[str, Any]:
        """Get all resources needed for remaining steps."""
        requirements = {}

        for step in self.steps:
            if not step.completed:
                for resource, amount in step.resources_needed.items():
                    requirements[resource] = requirements.get(resource, 0) + amount

        return requirements


class GoalGenerator:
    """Generates appropriate goals for NPCs."""

    @staticmethod
    def generate_goals_for_npc(
        npc_data: Dict[str, Any], psychology: NPCPsychology, context: Dict[str, Any]
    ) -> List[Goal]:
        """Generate appropriate goals based on NPC data and psychology."""
        goals = []

        # Immediate needs
        if context.get("hunger", 0) > 0.7:
            goals.append(GoalGenerator._create_food_goal(npc_data["id"]))

        if context.get("tiredness", 0) > 0.8:
            goals.append(GoalGenerator._create_rest_goal(npc_data["id"]))

        # Based on occupation
        occupation = npc_data.get("occupation", "patron")
        if occupation == "merchant":
            goals.extend(GoalGenerator._create_merchant_goals(npc_data["id"]))
        elif occupation == "guard":
            goals.extend(GoalGenerator._create_guard_goals(npc_data["id"]))
        elif occupation == "bartender":
            goals.extend(GoalGenerator._create_bartender_goals(npc_data["id"]))

        # Based on personality
        if psychology.base_personality == Personality.FRIENDLY:
            goals.append(GoalGenerator._create_social_goal(npc_data["id"]))
        elif psychology.base_personality == Personality.AGGRESSIVE:
            goals.append(GoalGenerator._create_dominance_goal(npc_data["id"]))
        elif psychology.base_personality == Personality.GREEDY:
            goals.append(GoalGenerator._create_wealth_goal(npc_data["id"]))

        # Based on motivations
        for motivation in psychology.motivations[:3]:  # Top 3 motivations
            if motivation.type == MotivationType.WEALTH:
                goals.append(GoalGenerator._create_wealth_goal(npc_data["id"]))
            elif motivation.type == MotivationType.SOCIAL:
                goals.append(GoalGenerator._create_social_goal(npc_data["id"]))
            elif motivation.type == MotivationType.REVENGE:
                goals.append(
                    GoalGenerator._create_revenge_goal(
                        npc_data["id"], motivation.target
                    )
                )

        return goals

    @staticmethod
    def _create_food_goal(npc_id: str) -> Goal:
        """Create goal to get food."""
        goal = Goal(
            id=f"{npc_id}_goal_food_{random.randint(1000, 9999)}",
            name="Get Food",
            description="Find something to eat",
            type=GoalType.IMMEDIATE,
            category=GoalCategory.SURVIVAL,
            owner_id=npc_id,
            importance=0.9,
            urgency=0.9,
        )

        # Add steps
        goal.add_step(
            GoalStep(
                description="Go to kitchen or bar",
                action_required=Action(
                    "Move to food source", "move", {"destination": "kitchen"}
                ),
                time_estimate=0.1,
            )
        )

        goal.add_step(
            GoalStep(
                description="Order or obtain food",
                action_required=Action(
                    "Get food", "interact", {"target": "food_source"}
                ),
                resources_needed={"gold": 5},
                time_estimate=0.2,
            )
        )

        goal.add_step(
            GoalStep(
                description="Eat food",
                action_required=Action("Eat", "consume", {"item": "food"}),
                time_estimate=0.5,
            )
        )

        return goal

    @staticmethod
    def _create_rest_goal(npc_id: str) -> Goal:
        """Create goal to rest."""
        goal = Goal(
            id=f"{npc_id}_goal_rest_{random.randint(1000, 9999)}",
            name="Get Rest",
            description="Find a place to rest",
            type=GoalType.IMMEDIATE,
            category=GoalCategory.SURVIVAL,
            owner_id=npc_id,
            importance=0.8,
            urgency=0.8,
        )

        goal.add_step(
            GoalStep(
                description="Find a room or quiet place",
                action_required=Action(
                    "Find rest spot", "move", {"destination": "guest_room"}
                ),
                time_estimate=0.2,
            )
        )

        goal.add_step(
            GoalStep(
                description="Rest or sleep",
                action_required=Action("Rest", "rest", {}),
                time_estimate=6.0,
            )
        )

        return goal

    @staticmethod
    def _create_merchant_goals(npc_id: str) -> List[Goal]:
        """Create merchant-specific goals."""
        goals = []

        # Make profit goal
        profit_goal = Goal(
            id=f"{npc_id}_goal_profit_{random.randint(1000, 9999)}",
            name="Make Daily Profit",
            description="Earn at least 50 gold today",
            type=GoalType.SHORT_TERM,
            category=GoalCategory.FINANCIAL,
            owner_id=npc_id,
            importance=0.8,
            urgency=0.6,
            deadline=datetime.now() + timedelta(days=1),
        )

        profit_goal.add_step(
            GoalStep(
                description="Set up shop in main hall",
                action_required=Action("Set up", "prepare", {"location": "main_hall"}),
                time_estimate=0.5,
            )
        )

        profit_goal.add_step(
            GoalStep(
                description="Attract customers",
                action_required=Action(
                    "Advertise", "speak", {"dialogue": "Fine goods for sale!"}
                ),
                time_estimate=1.0,
            )
        )

        profit_goal.add_step(
            GoalStep(
                description="Make sales",
                action_required=Action("Trade", "trade", {}),
                time_estimate=4.0,
                difficulty=0.6,
            )
        )

        goals.append(profit_goal)

        # Find new suppliers
        supplier_goal = Goal(
            id=f"{npc_id}_goal_supplier_{random.randint(1000, 9999)}",
            name="Find New Supplier",
            description="Establish new trade connection",
            type=GoalType.LONG_TERM,
            category=GoalCategory.PROFESSIONAL,
            owner_id=npc_id,
            importance=0.6,
            urgency=0.3,
        )

        supplier_goal.add_step(
            GoalStep(
                description="Network with other merchants",
                action_required=Action("Network", "social", {"target": "merchants"}),
                time_estimate=2.0,
            )
        )

        goals.append(supplier_goal)

        return goals

    @staticmethod
    def _create_guard_goals(npc_id: str) -> List[Goal]:
        """Create guard-specific goals."""
        goals = []

        # Maintain order
        order_goal = Goal(
            id=f"{npc_id}_goal_order_{random.randint(1000, 9999)}",
            name="Maintain Order",
            description="Keep the peace in the tavern",
            type=GoalType.SHORT_TERM,
            category=GoalCategory.PROFESSIONAL,
            owner_id=npc_id,
            importance=0.9,
            urgency=0.7,
        )

        order_goal.add_step(
            GoalStep(
                description="Patrol main areas",
                action_required=Action("Patrol", "patrol", {"route": "standard"}),
                time_estimate=2.0,
            )
        )

        order_goal.add_step(
            GoalStep(
                description="Check for troublemakers",
                action_required=Action(
                    "Investigate", "observe", {"target": "suspicious_activity"}
                ),
                time_estimate=1.0,
            )
        )

        goals.append(order_goal)

        return goals

    @staticmethod
    def _create_bartender_goals(npc_id: str) -> List[Goal]:
        """Create bartender-specific goals."""
        goals = []

        # Serve customers
        serve_goal = Goal(
            id=f"{npc_id}_goal_serve_{random.randint(1000, 9999)}",
            name="Serve Customers",
            description="Keep customers happy and served",
            type=GoalType.SHORT_TERM,
            category=GoalCategory.PROFESSIONAL,
            owner_id=npc_id,
            importance=0.9,
            urgency=0.8,
        )

        serve_goal.add_step(
            GoalStep(
                description="Stay at bar",
                action_required=Action("Man bar", "work", {"location": "bar_area"}),
                time_estimate=4.0,
            )
        )

        serve_goal.add_step(
            GoalStep(
                description="Serve drinks",
                action_required=Action("Serve", "serve", {"item": "drinks"}),
                time_estimate=0.1,
                difficulty=0.2,
            )
        )

        goals.append(serve_goal)

        # Gather information
        info_goal = Goal(
            id=f"{npc_id}_goal_info_{random.randint(1000, 9999)}",
            name="Gather Information",
            description="Learn what's happening in town",
            type=GoalType.LONG_TERM,
            category=GoalCategory.KNOWLEDGE,
            owner_id=npc_id,
            importance=0.5,
            urgency=0.2,
        )

        info_goal.add_step(
            GoalStep(
                description="Listen to conversations",
                action_required=Action("Eavesdrop", "observe", {"subtle": True}),
                time_estimate=2.0,
            )
        )

        goals.append(info_goal)

        return goals

    @staticmethod
    def _create_social_goal(npc_id: str) -> Goal:
        """Create social interaction goal."""
        goal = Goal(
            id=f"{npc_id}_goal_social_{random.randint(1000, 9999)}",
            name="Make Friends",
            description="Build positive relationships",
            type=GoalType.LONG_TERM,
            category=GoalCategory.SOCIAL,
            owner_id=npc_id,
            importance=0.6,
            urgency=0.3,
        )

        goal.add_step(
            GoalStep(
                description="Engage in friendly conversation",
                action_required=Action("Chat", "social", {"tone": "friendly"}),
                time_estimate=0.5,
            )
        )

        goal.add_step(
            GoalStep(
                description="Share a drink or meal",
                action_required=Action("Share", "social", {"activity": "drink"}),
                resources_needed={"gold": 10},
                time_estimate=1.0,
            )
        )

        return goal

    @staticmethod
    def _create_wealth_goal(npc_id: str) -> Goal:
        """Create wealth accumulation goal."""
        goal = Goal(
            id=f"{npc_id}_goal_wealth_{random.randint(1000, 9999)}",
            name="Accumulate Wealth",
            description="Build personal fortune",
            type=GoalType.LIFE_GOAL,
            category=GoalCategory.FINANCIAL,
            owner_id=npc_id,
            importance=0.8,
            urgency=0.2,
        )

        goal.add_step(
            GoalStep(
                description="Find profitable opportunities",
                action_required=Action("Seek opportunity", "investigate", {}),
                time_estimate=3.0,
                difficulty=0.7,
            )
        )

        goal.add_step(
            GoalStep(
                description="Execute profitable plan",
                action_required=Action("Execute", "custom", {}),
                time_estimate=10.0,
                difficulty=0.8,
            )
        )

        return goal

    @staticmethod
    def _create_dominance_goal(npc_id: str) -> Goal:
        """Create dominance/power goal."""
        goal = Goal(
            id=f"{npc_id}_goal_dominance_{random.randint(1000, 9999)}",
            name="Assert Dominance",
            description="Establish position of power",
            type=GoalType.LONG_TERM,
            category=GoalCategory.POWER,
            owner_id=npc_id,
            importance=0.7,
            urgency=0.4,
        )

        goal.add_step(
            GoalStep(
                description="Challenge rivals",
                action_required=Action("Challenge", "confront", {}),
                time_estimate=0.5,
                difficulty=0.6,
            )
        )

        goal.add_step(
            GoalStep(
                description="Build reputation",
                action_required=Action("Intimidate", "social", {"tone": "dominant"}),
                time_estimate=2.0,
            )
        )

        return goal

    @staticmethod
    def _create_revenge_goal(npc_id: str, target: Optional[str]) -> Goal:
        """Create revenge goal."""
        goal = Goal(
            id=f"{npc_id}_goal_revenge_{random.randint(1000, 9999)}",
            name="Get Revenge",
            description=f"Get revenge on {target or 'enemy'}",
            type=GoalType.LONG_TERM,
            category=GoalCategory.REVENGE,
            owner_id=npc_id,
            importance=0.9,
            urgency=0.5,
        )

        goal.add_step(
            GoalStep(
                description="Gather information on target",
                action_required=Action(
                    "Investigate", "investigate", {"target": target or "enemy"}
                ),
                time_estimate=5.0,
                difficulty=0.6,
            )
        )

        goal.add_step(
            GoalStep(
                description="Find weakness",
                action_required=Action("Analyze", "observe", {}),
                time_estimate=3.0,
                difficulty=0.7,
            )
        )

        goal.add_step(
            GoalStep(
                description="Execute revenge",
                action_required=Action("Strike", "custom", {}),
                time_estimate=1.0,
                difficulty=0.8,
            )
        )

        return goal


class NPCAgency:
    """Manages NPC autonomous decision-making and goal pursuit."""

    def __init__(self, npc_id: str, psychology: NPCPsychology):
        self.npc_id = npc_id
        self.psychology = psychology
        self.goals: List[Goal] = []
        self.completed_goals: List[Goal] = []
        self.abandoned_goals: List[Goal] = []

        # Decision-making parameters
        self.risk_tolerance: float = 0.5
        self.planning_horizon: float = 0.5  # How far ahead they plan
        self.adaptability: float = 0.5  # How well they adjust

        # Resource tracking
        self.resources: Dict[str, Any] = {
            "gold": 0,
            "energy": 1.0,
            "time": 24.0,  # Hours per day
            "social_capital": 0.5,
        }

        # Initialize based on personality
        self._initialize_from_personality()

    def _initialize_from_personality(self) -> None:
        """Set agency parameters based on personality."""
        if self.psychology.base_personality == Personality.AGGRESSIVE:
            self.risk_tolerance = 0.8
            self.planning_horizon = 0.3  # Short-term focus
        elif self.psychology.base_personality == Personality.SHY:
            self.risk_tolerance = 0.2
            self.adaptability = 0.3
        elif self.psychology.base_personality == Personality.AMBITIOUS:
            self.planning_horizon = 0.9  # Long-term planner
            self.risk_tolerance = 0.6

    def add_goal(self, goal: Goal) -> None:
        """Add a new goal."""
        # Check for conflicts
        for existing_goal in self.goals:
            if existing_goal.id in goal.conflicts_with:
                # Must choose between conflicting goals
                if goal.importance > existing_goal.importance:
                    self.abandon_goal(existing_goal.id)
                else:
                    return  # Don't add conflicting lower priority goal

        self.goals.append(goal)
        self._prioritize_goals()

    def abandon_goal(self, goal_id: str) -> None:
        """Abandon a goal."""
        for i, goal in enumerate(self.goals):
            if goal.id == goal_id:
                goal.status = GoalStatus.ABANDONED
                self.abandoned_goals.append(goal)
                self.goals.pop(i)
                break

    def _prioritize_goals(self) -> None:
        """Sort goals by priority."""
        context = {"resources": self.resources}
        self.goals.sort(key=lambda g: g.calculate_priority(context), reverse=True)

    def select_action(self, context: Dict[str, Any]) -> Optional[Action]:
        """Select next action based on goals."""
        # Update goal priorities
        self._prioritize_goals()

        # Try each goal in priority order
        for goal in self.goals:
            if not goal.is_achievable():
                self.abandon_goal(goal.id)
                continue

            # Get current step
            current_step = goal.get_current_step()
            if current_step and current_step.can_attempt(self.resources):
                # Check if conditions are met
                conditions_met = all(
                    condition.evaluate(context) for condition in current_step.conditions
                )

                if conditions_met:
                    return current_step.action_required

        return None

    def execute_step(self, goal_id: str, step_index: int, success: bool) -> None:
        """Record execution of a goal step."""
        for goal in self.goals:
            if goal.id == goal_id:
                if success:
                    goal.complete_step(step_index)

                    # Check if goal completed
                    if goal.status == GoalStatus.COMPLETED:
                        self.completed_goals.append(goal)
                        self.goals.remove(goal)

                        # Check for enabled goals
                        self._check_enabled_goals(goal)
                else:
                    # Failed attempt
                    step = goal.steps[step_index]
                    if step.attempts > 3:
                        # Too many failures, find alternative
                        self._find_alternative_approach(goal, step)
                break

    def _check_enabled_goals(self, completed_goal: Goal) -> None:
        """Check if completing a goal enables others."""
        # Remove from prerequisites of other goals
        for goal in self.goals:
            if completed_goal.id in goal.prerequisites:
                goal.prerequisites.remove(completed_goal.id)

    def _find_alternative_approach(self, goal: Goal, failed_step: GoalStep) -> None:
        """Find alternative way to achieve goal."""
        # Simple implementation - mark goal as blocked
        goal.blockers.append(f"Failed step: {failed_step.description}")
        goal.status = GoalStatus.BLOCKED

        # In a more complex system, would generate alternative steps

    def update_resources(self, resource: str, amount: float) -> None:
        """Update available resources."""
        if resource in self.resources:
            self.resources[resource] += amount

            # Check if any blocked goals can proceed
            for goal in self.goals:
                if goal.status == GoalStatus.BLOCKED:
                    # Check if resource was blocking
                    required = goal.get_resource_requirements()
                    if all(
                        self.resources.get(r, 0) >= amt for r, amt in required.items()
                    ):
                        goal.status = GoalStatus.ACTIVE
                        goal.blockers = [
                            b for b in goal.blockers if "resource" not in b.lower()
                        ]

    def evaluate_goal_progress(self) -> Dict[str, Any]:
        """Evaluate progress on all goals."""
        active_goals = [g for g in self.goals if g.status == GoalStatus.ACTIVE]

        return {
            "total_goals": len(self.goals),
            "active_goals": len(active_goals),
            "completed_goals": len(self.completed_goals),
            "abandoned_goals": len(self.abandoned_goals),
            "average_progress": sum(g.progress for g in self.goals)
            / max(len(self.goals), 1),
            "blocked_goals": len(
                [g for g in self.goals if g.status == GoalStatus.BLOCKED]
            ),
        }

    def generate_new_goals(self, context: Dict[str, Any]) -> List[Goal]:
        """Generate new goals based on current situation."""
        # Don't overload with goals
        if len(self.goals) >= 5:
            return []

        npc_data = {
            "id": self.npc_id,
            "occupation": context.get("occupation", "patron"),
        }

        # Generate potential goals
        potential_goals = GoalGenerator.generate_goals_for_npc(
            npc_data, self.psychology, context
        )

        # Filter out conflicting or duplicate goals
        new_goals = []
        for potential in potential_goals:
            # Check if similar goal exists
            similar = any(
                g.category == potential.category and g.type == potential.type
                for g in self.goals
            )

            if not similar:
                new_goals.append(potential)

        return new_goals[:2]  # Max 2 new goals at once


class GoalManager:
    """Manager for NPC goals system"""

    def __init__(self):
        self.npc_goals: Dict[str, List[Goal]] = {}
        self.completed_goals: Dict[str, List[Goal]] = {}

    def initialize_npc_goals(self, npc_id: str, npc: Any) -> None:
        """Initialize goals for an NPC"""
        if npc_id not in self.npc_goals:
            # Create basic goals based on NPC type
            basic_goal = Goal(
                id=f"{npc_id}_basic",
                name="Basic Activities",
                description=f"Basic activities for {npc_id}",
                category=GoalCategory.SOCIAL,
                type=GoalType.SHORT_TERM,
                owner_id=npc_id,
                importance=0.5,
                urgency=0.3,
            )
            self.npc_goals[npc_id] = [basic_goal]

    def get_current_goal(self, npc_id: str) -> Optional[Goal]:
        """Get the current active goal for an NPC"""
        goals = self.npc_goals.get(npc_id, [])
        if goals:
            # Return highest importance incomplete goal
            active_goals = [g for g in goals if g.status != GoalStatus.COMPLETED]
            if active_goals:
                return max(active_goals, key=lambda g: g.importance)
        return None

    def update_all_goals(self, elapsed_time: float) -> None:
        """Update all NPC goals with time progression"""
        for npc_id, goals in self.npc_goals.items():
            for goal in goals:
                if goal.status != GoalStatus.COMPLETED:
                    # Update goal progress (simplified)
                    goal.progress = min(1.0, goal.progress + elapsed_time / 3600)
                    if goal.progress >= 1.0:
                        goal.status = GoalStatus.COMPLETED
                        if npc_id not in self.completed_goals:
                            self.completed_goals[npc_id] = []
                        self.completed_goals[npc_id].append(goal)

    def get_goal_dialogue(self, npc_id: str, goal: Goal) -> Optional[str]:
        """Get dialogue related to an NPC's current goal"""
        if goal.category == GoalCategory.SOCIAL:
            return f"I've been thinking about {goal.description.lower()}"
        elif goal.category == GoalCategory.ECONOMIC:
            return f"Business has been on my mind lately - {goal.description.lower()}"
        elif goal.category == GoalCategory.PERSONAL:
            return "There's something personal I need to take care of"
        return None
