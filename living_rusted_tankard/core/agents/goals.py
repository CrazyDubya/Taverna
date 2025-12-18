"""
Goals and Planning System for Deep Agents.

Implements:
- Goal hierarchy (desires in BDI)
- Action planning (intentions in BDI)
- Means-end reasoning
- Plan execution and monitoring

Goals are what agents want to achieve.
Plans are how they intend to achieve them.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import time


class GoalStatus(Enum):
    """Status of a goal."""

    PENDING = "pending"  # Not yet pursued
    ACTIVE = "active"  # Currently being pursued
    ACHIEVED = "achieved"  # Successfully completed
    FAILED = "failed"  # Could not be achieved
    ABANDONED = "abandoned"  # Given up on
    BLOCKED = "blocked"  # Cannot pursue due to preconditions


class GoalType(Enum):
    """Types of goals."""

    SURVIVAL = "survival"  # Maintain life and health
    ACHIEVEMENT = "achievement"  # Accomplish something
    MAINTENANCE = "maintenance"  # Keep something in desired state
    SOCIAL = "social"  # Relationship or social goal
    EXPLORATION = "exploration"  # Learn or discover
    AVOIDANCE = "avoidance"  # Prevent something


@dataclass
class Goal:
    """
    A desired state or outcome.

    Goals have:
    - Description (what to achieve)
    - Priority (how important, 0.0-1.0)
    - Success condition (how to know it's achieved)
    - Deadline (optional time constraint)
    - Motivating needs/drives
    """

    goal_id: str
    description: str
    goal_type: GoalType

    priority: float = 0.5  # 0.0-1.0, how important
    status: GoalStatus = GoalStatus.PENDING

    # Success condition (callable that returns True when achieved)
    # For now, we'll use a simple string description
    success_condition: str = ""

    # Optional deadline (game time)
    deadline: Optional[float] = None

    # What motivated this goal (need types or drive names)
    motivated_by: List[str] = field(default_factory=list)

    # Parent goal (if this is a subgoal)
    parent_goal_id: Optional[str] = None

    # Subgoals required to achieve this
    subgoals: List[str] = field(default_factory=list)  # goal_ids

    # Metadata
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    # Progress tracking
    progress: float = 0.0  # 0.0-1.0

    def activate(self) -> None:
        """Mark goal as actively being pursued."""
        if self.status == GoalStatus.PENDING:
            self.status = GoalStatus.ACTIVE
            self.started_at = time.time()

    def achieve(self) -> None:
        """Mark goal as achieved."""
        self.status = GoalStatus.ACHIEVED
        self.completed_at = time.time()
        self.progress = 1.0

    def fail(self) -> None:
        """Mark goal as failed."""
        self.status = GoalStatus.FAILED
        self.completed_at = time.time()

    def abandon(self) -> None:
        """Mark goal as abandoned."""
        self.status = GoalStatus.ABANDONED
        self.completed_at = time.time()

    def block(self) -> None:
        """Mark goal as blocked."""
        self.status = GoalStatus.BLOCKED

    def is_active(self) -> bool:
        """Check if goal is currently being pursued."""
        return self.status == GoalStatus.ACTIVE

    def is_complete(self) -> bool:
        """Check if goal is done (achieved, failed, or abandoned)."""
        return self.status in [
            GoalStatus.ACHIEVED,
            GoalStatus.FAILED,
            GoalStatus.ABANDONED,
        ]

    def is_overdue(self, current_time: float) -> bool:
        """Check if goal has passed its deadline."""
        if self.deadline is None:
            return False
        return current_time > self.deadline

    def get_urgency(self, current_time: float) -> float:
        """
        Calculate urgency (0.0-1.0).

        Based on priority and deadline proximity.
        """
        urgency = self.priority

        if self.deadline is not None:
            time_remaining = self.deadline - current_time
            if time_remaining <= 0:
                return 1.0  # Overdue = maximum urgency

            # Increase urgency as deadline approaches
            # Assume deadline in hours, urgency increases in last 24 hours
            if time_remaining < 24:
                deadline_factor = 1.0 - (time_remaining / 24.0)
                urgency = max(urgency, deadline_factor)

        return min(1.0, urgency)

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "goal_type": self.goal_type.value,
            "priority": self.priority,
            "status": self.status.value,
            "success_condition": self.success_condition,
            "deadline": self.deadline,
            "motivated_by": self.motivated_by,
            "parent_goal_id": self.parent_goal_id,
            "subgoals": self.subgoals,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Goal":
        """Deserialize from saved data."""
        data["goal_type"] = GoalType(data["goal_type"])
        data["status"] = GoalStatus(data["status"])
        return cls(**data)

    def __repr__(self) -> str:
        return (
            f"Goal({self.goal_type.value}, "
            f"'{self.description}', "
            f"priority={self.priority:.2f}, "
            f"status={self.status.value})"
        )


@dataclass
class Action:
    """
    A single action that can be performed.

    Actions are the primitives of plans.
    """

    action_id: str
    command: str  # The actual command to execute in game
    description: str  # Human-readable description

    # Prerequisites for this action
    preconditions: List[str] = field(default_factory=list)

    # Expected outcomes
    expected_effects: List[str] = field(default_factory=list)

    # Cost (time, resources, risk)
    estimated_time: float = 1.0  # Hours
    resource_cost: Dict[str, float] = field(default_factory=dict)  # resource -> amount
    risk_level: float = 0.0  # 0.0-1.0

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "action_id": self.action_id,
            "command": self.command,
            "description": self.description,
            "preconditions": self.preconditions,
            "expected_effects": self.expected_effects,
            "estimated_time": self.estimated_time,
            "resource_cost": self.resource_cost,
            "risk_level": self.risk_level,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Action":
        """Deserialize from saved data."""
        return cls(**data)


@dataclass
class Plan:
    """
    A sequence of actions to achieve a goal.

    Plans are intentions in BDI architecture.
    """

    plan_id: str
    goal_id: str  # Which goal this plan is for
    actions: List[Action] = field(default_factory=list)

    # Plan metadata
    created_at: float = field(default_factory=time.time)
    confidence: float = 0.5  # 0.0-1.0, confidence this plan will work

    # Execution state
    current_action_index: int = 0
    is_executing: bool = False

    def get_next_action(self) -> Optional[Action]:
        """Get the next action to execute."""
        if self.current_action_index < len(self.actions):
            return self.actions[self.current_action_index]
        return None

    def advance(self) -> None:
        """Move to the next action in the plan."""
        self.current_action_index += 1

    def is_complete(self) -> bool:
        """Check if all actions have been executed."""
        return self.current_action_index >= len(self.actions)

    def get_progress(self) -> float:
        """Get progress through plan (0.0-1.0)."""
        if not self.actions:
            return 0.0
        return self.current_action_index / len(self.actions)

    def get_total_cost(self) -> Dict[str, float]:
        """Calculate total resource cost of plan."""
        total_cost = {}
        for action in self.actions:
            for resource, amount in action.resource_cost.items():
                total_cost[resource] = total_cost.get(resource, 0.0) + amount
        return total_cost

    def get_estimated_time(self) -> float:
        """Calculate total estimated time for plan."""
        return sum(action.estimated_time for action in self.actions)

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "plan_id": self.plan_id,
            "goal_id": self.goal_id,
            "actions": [a.to_dict() for a in self.actions],
            "created_at": self.created_at,
            "confidence": self.confidence,
            "current_action_index": self.current_action_index,
            "is_executing": self.is_executing,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Plan":
        """Deserialize from saved data."""
        data["actions"] = [Action.from_dict(a) for a in data.get("actions", [])]
        return cls(**data)

    def __repr__(self) -> str:
        return (
            f"Plan({len(self.actions)} actions, "
            f"progress={self.get_progress():.0%}, "
            f"confidence={self.confidence:.2f})"
        )


@dataclass
class GoalHierarchy:
    """
    Manages all goals and their relationships.

    Handles:
    - Goal creation and prioritization
    - Goal decomposition into subgoals
    - Goal selection for pursuit
    - Goal monitoring and updates
    """

    goals: Dict[str, Goal] = field(default_factory=dict)  # goal_id -> Goal
    plans: Dict[str, Plan] = field(default_factory=dict)  # plan_id -> Plan

    # Current active goal and plan
    active_goal_id: Optional[str] = None
    active_plan_id: Optional[str] = None

    def add_goal(
        self,
        description: str,
        goal_type: GoalType,
        priority: float = 0.5,
        success_condition: str = "",
        deadline: Optional[float] = None,
        motivated_by: Optional[List[str]] = None,
        parent_goal_id: Optional[str] = None,
    ) -> Goal:
        """Add a new goal."""
        import hashlib

        goal_id = hashlib.md5(f"{description}:{time.time()}".encode()).hexdigest()[:16]

        goal = Goal(
            goal_id=goal_id,
            description=description,
            goal_type=goal_type,
            priority=priority,
            success_condition=success_condition,
            deadline=deadline,
            motivated_by=motivated_by or [],
            parent_goal_id=parent_goal_id,
        )

        self.goals[goal_id] = goal

        # If this has a parent, add to parent's subgoals
        if parent_goal_id and parent_goal_id in self.goals:
            self.goals[parent_goal_id].subgoals.append(goal_id)

        return goal

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a specific goal."""
        return self.goals.get(goal_id)

    def get_active_goal(self) -> Optional[Goal]:
        """Get the currently active goal."""
        if self.active_goal_id:
            return self.goals.get(self.active_goal_id)
        return None

    def get_active_plan(self) -> Optional[Plan]:
        """Get the currently executing plan."""
        if self.active_plan_id:
            return self.plans.get(self.active_plan_id)
        return None

    def select_goal_to_pursue(self, current_time: float) -> Optional[Goal]:
        """
        Select which goal to pursue next.

        Uses deliberation based on:
        - Goal urgency (priority + deadline)
        - Goal feasibility
        - Resource availability
        """
        # Get all pending or active goals
        candidates = [
            goal
            for goal in self.goals.values()
            if goal.status in [GoalStatus.PENDING, GoalStatus.ACTIVE]
            and not goal.is_overdue(current_time)
        ]

        if not candidates:
            return None

        # Score each goal by urgency
        scored_goals = [
            (goal, goal.get_urgency(current_time)) for goal in candidates
        ]

        # Sort by urgency (descending)
        scored_goals.sort(key=lambda x: x[1], reverse=True)

        # Return highest urgency goal
        return scored_goals[0][0] if scored_goals else None

    def set_active_goal(self, goal_id: str) -> None:
        """Set a goal as active."""
        if goal_id in self.goals:
            goal = self.goals[goal_id]
            goal.activate()
            self.active_goal_id = goal_id

    def add_plan(self, goal_id: str, actions: List[Action], confidence: float = 0.5) -> Plan:
        """Add a plan for a goal."""
        import hashlib

        plan_id = hashlib.md5(f"{goal_id}:{time.time()}".encode()).hexdigest()[:16]

        plan = Plan(
            plan_id=plan_id, goal_id=goal_id, actions=actions, confidence=confidence
        )

        self.plans[plan_id] = plan
        return plan

    def set_active_plan(self, plan_id: str) -> None:
        """Set a plan as actively executing."""
        if plan_id in self.plans:
            self.plans[plan_id].is_executing = True
            self.active_plan_id = plan_id

    def get_next_action(self) -> Optional[Action]:
        """Get the next action from the active plan."""
        plan = self.get_active_plan()
        if plan:
            return plan.get_next_action()
        return None

    def advance_plan(self) -> None:
        """Move to the next action in the active plan."""
        plan = self.get_active_plan()
        if plan:
            plan.advance()

            # If plan is complete, mark goal as achieved
            if plan.is_complete():
                goal = self.get_goal(plan.goal_id)
                if goal:
                    goal.achieve()

                self.active_plan_id = None
                self.active_goal_id = None

    def get_goal_summary(self) -> Dict[str, Any]:
        """Get summary of goal state."""
        total = len(self.goals)
        by_status = {}
        for goal in self.goals.values():
            status = goal.status.value
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_goals": total,
            "by_status": by_status,
            "active_goal": self.active_goal_id,
            "active_plan": self.active_plan_id,
        }

    def to_dict(self) -> Dict:
        """Serialize for saving."""
        return {
            "goals": {gid: goal.to_dict() for gid, goal in self.goals.items()},
            "plans": {pid: plan.to_dict() for pid, plan in self.plans.items()},
            "active_goal_id": self.active_goal_id,
            "active_plan_id": self.active_plan_id,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "GoalHierarchy":
        """Deserialize from saved data."""
        goals = {gid: Goal.from_dict(gdata) for gid, gdata in data.get("goals", {}).items()}
        plans = {pid: Plan.from_dict(pdata) for pid, pdata in data.get("plans", {}).items()}

        return cls(
            goals=goals,
            plans=plans,
            active_goal_id=data.get("active_goal_id"),
            active_plan_id=data.get("active_plan_id"),
        )

    def __repr__(self) -> str:
        summary = self.get_goal_summary()
        return f"GoalHierarchy({summary['total_goals']} goals, {summary['by_status']})"
