"""Behavioral rules engine for NPCs."""

from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
from datetime import datetime, time

from .psychology import NPCPsychology, Personality, Mood, MotivationType


class BehaviorPriority(Enum):
    """Priority levels for behaviors."""
    CRITICAL = 5  # Life-threatening situations
    HIGH = 4      # Important goals
    MEDIUM = 3    # Regular activities
    LOW = 2       # Optional actions
    IDLE = 1      # Default behaviors


class ConditionType(Enum):
    """Types of conditions that trigger behaviors."""
    TIME = "time"
    LOCATION = "location"
    PRESENCE = "presence"
    ABSENCE = "absence"
    EVENT = "event"
    STATE = "state"
    RELATIONSHIP = "relationship"
    RANDOM = "random"


@dataclass
class Condition:
    """A condition that must be met for a behavior."""
    type: ConditionType
    parameters: Dict[str, Any]
    negate: bool = False  # If True, condition must NOT be met
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate if condition is met."""
        result = self._check_condition(context)
        return not result if self.negate else result
    
    def _check_condition(self, context: Dict[str, Any]) -> bool:
        """Check specific condition type."""
        if self.type == ConditionType.TIME:
            current_time = context.get("current_time")
            if not current_time:
                return False
            
            start_hour = self.parameters.get("start_hour", 0)
            end_hour = self.parameters.get("end_hour", 24)
            
            if start_hour <= end_hour:
                return start_hour <= current_time.hour < end_hour
            else:  # Wraps around midnight
                return current_time.hour >= start_hour or current_time.hour < end_hour
        
        elif self.type == ConditionType.LOCATION:
            current_location = context.get("current_location")
            target_locations = self.parameters.get("locations", [])
            return current_location in target_locations
        
        elif self.type == ConditionType.PRESENCE:
            area_occupants = context.get("area_occupants", [])
            required_presence = self.parameters.get("character_id")
            character_type = self.parameters.get("character_type")
            
            if required_presence:
                return required_presence in area_occupants
            elif character_type:
                # Check for any character of type (e.g., "guard", "patron")
                for occupant in area_occupants:
                    if context.get("character_types", {}).get(occupant) == character_type:
                        return True
            return False
        
        elif self.type == ConditionType.STATE:
            npc_state = context.get("npc_state", {})
            state_key = self.parameters.get("key")
            state_value = self.parameters.get("value")
            operator = self.parameters.get("operator", "equals")
            
            if not state_key:
                return False
            
            actual_value = npc_state.get(state_key)
            
            if operator == "equals":
                return actual_value == state_value
            elif operator == "greater":
                return actual_value > state_value
            elif operator == "less":
                return actual_value < state_value
            elif operator == "contains":
                return state_value in actual_value if hasattr(actual_value, "__contains__") else False
        
        elif self.type == ConditionType.RANDOM:
            probability = self.parameters.get("probability", 0.5)
            return random.random() < probability
        
        return False


@dataclass
class Action:
    """An action that can be performed."""
    name: str
    action_type: str  # "move", "speak", "interact", "wait", etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0  # In game minutes
    energy_cost: float = 0.0
    
    def get_description(self) -> str:
        """Get human-readable description of action."""
        if self.action_type == "move":
            return f"Move to {self.parameters.get('destination', 'somewhere')}"
        elif self.action_type == "speak":
            return f"Say: {self.parameters.get('dialogue', '...')}"
        elif self.action_type == "interact":
            return f"Interact with {self.parameters.get('target', 'something')}"
        elif self.action_type == "wait":
            return f"Wait for {self.duration} minutes"
        else:
            return self.name


@dataclass
class BehaviorRule:
    """A rule that defines NPC behavior."""
    id: str
    name: str
    description: str
    conditions: List[Condition]
    actions: List[Action]
    priority: BehaviorPriority = BehaviorPriority.MEDIUM
    cooldown: float = 0.0  # Minutes before rule can trigger again
    last_triggered: Optional[datetime] = None
    requires_mood: Optional[List[Mood]] = None
    forbidden_moods: Optional[List[Mood]] = None
    interrupt_current: bool = False  # Can interrupt ongoing behavior
    
    def can_trigger(self, context: Dict[str, Any], current_mood: Mood) -> bool:
        """Check if rule can be triggered."""
        # Check cooldown
        if self.last_triggered and self.cooldown > 0:
            time_passed = (datetime.now() - self.last_triggered).total_seconds() / 60
            if time_passed < self.cooldown:
                return False
        
        # Check mood requirements
        if self.requires_mood and current_mood not in self.requires_mood:
            return False
        
        if self.forbidden_moods and current_mood in self.forbidden_moods:
            return False
        
        # Check all conditions
        for condition in self.conditions:
            if not condition.evaluate(context):
                return False
        
        return True
    
    def trigger(self) -> List[Action]:
        """Trigger the rule and return actions."""
        self.last_triggered = datetime.now()
        return self.actions.copy()


class DailySchedule:
    """Manages an NPC's daily routine."""
    
    def __init__(self, npc_id: str):
        self.npc_id = npc_id
        self.schedule_rules: List[BehaviorRule] = []
        self.routine_variations: Dict[str, List[BehaviorRule]] = {}
        
    def add_routine(self, time_slot: Tuple[int, int], location: str, 
                   activity: str, variations: Optional[List[Dict[str, Any]]] = None) -> None:
        """Add a routine activity."""
        start_hour, end_hour = time_slot
        
        # Create main routine rule
        routine_rule = BehaviorRule(
            id=f"{self.npc_id}_routine_{start_hour}_{location}",
            name=f"{activity} at {location}",
            description=f"Regular {activity} routine",
            conditions=[
                Condition(
                    type=ConditionType.TIME,
                    parameters={"start_hour": start_hour, "end_hour": end_hour}
                )
            ],
            actions=[
                Action(
                    name=f"Go to {location}",
                    action_type="move",
                    parameters={"destination": location},
                    duration=5.0
                ),
                Action(
                    name=activity,
                    action_type="activity",
                    parameters={"activity": activity},
                    duration=(end_hour - start_hour) * 60.0
                )
            ],
            priority=BehaviorPriority.MEDIUM
        )
        
        self.schedule_rules.append(routine_rule)
        
        # Add variations if provided
        if variations:
            variation_rules = []
            for i, var in enumerate(variations):
                var_rule = BehaviorRule(
                    id=f"{routine_rule.id}_var_{i}",
                    name=f"{var.get('activity', activity)} at {var.get('location', location)}",
                    description=f"Variation of {activity} routine",
                    conditions=routine_rule.conditions + [
                        Condition(
                            type=ConditionType.RANDOM,
                            parameters={"probability": var.get('probability', 0.3)}
                        )
                    ],
                    actions=[
                        Action(
                            name=f"Go to {var.get('location', location)}",
                            action_type="move",
                            parameters={"destination": var.get('location', location)},
                            duration=5.0
                        ),
                        Action(
                            name=var.get('activity', activity),
                            action_type="activity",
                            parameters={"activity": var.get('activity', activity)},
                            duration=var.get('duration', 30.0)
                        )
                    ],
                    priority=BehaviorPriority.MEDIUM
                )
                variation_rules.append(var_rule)
            
            self.routine_variations[routine_rule.id] = variation_rules
    
    def get_current_routine(self, current_time: datetime) -> Optional[BehaviorRule]:
        """Get the routine for current time."""
        context = {"current_time": current_time}
        
        for rule in self.schedule_rules:
            # Check variations first
            if rule.id in self.routine_variations:
                for var in self.routine_variations[rule.id]:
                    if var.can_trigger(context, Mood.CONTENT):
                        return var
            
            # Check main routine
            if rule.can_trigger(context, Mood.CONTENT):
                return rule
        
        return None


class BehaviorEngine:
    """Manages behavioral rules for NPCs."""
    
    def __init__(self, npc_id: str, psychology: NPCPsychology):
        self.npc_id = npc_id
        self.psychology = psychology
        self.rules: List[BehaviorRule] = []
        self.active_behavior: Optional[BehaviorRule] = None
        self.current_actions: List[Action] = []
        self.action_index: int = 0
        self.daily_schedule = DailySchedule(npc_id)
        
        # Initialize default rules based on personality
        self._initialize_personality_rules()
    
    def _initialize_personality_rules(self) -> None:
        """Create default rules based on personality."""
        if self.psychology.base_personality == Personality.FRIENDLY:
            # Friendly NPCs greet newcomers
            self.add_rule(BehaviorRule(
                id=f"{self.npc_id}_greet_newcomer",
                name="Greet Newcomer",
                description="Greet new arrivals warmly",
                conditions=[
                    Condition(
                        type=ConditionType.EVENT,
                        parameters={"event_type": "character_arrived"}
                    ),
                    Condition(
                        type=ConditionType.STATE,
                        parameters={"key": "energy_level", "value": 0.3, "operator": "greater"}
                    )
                ],
                actions=[
                    Action(
                        name="Turn to newcomer",
                        action_type="face",
                        parameters={"target": "newcomer"}
                    ),
                    Action(
                        name="Greet warmly",
                        action_type="speak",
                        parameters={"dialogue": "Welcome, friend! Come, warm yourself by the fire!"},
                        duration=0.5
                    )
                ],
                priority=BehaviorPriority.LOW,
                cooldown=5.0
            ))
        
        elif self.psychology.base_personality == Personality.SUSPICIOUS:
            # Suspicious NPCs watch strangers
            self.add_rule(BehaviorRule(
                id=f"{self.npc_id}_watch_stranger",
                name="Watch Stranger",
                description="Keep an eye on unfamiliar faces",
                conditions=[
                    Condition(
                        type=ConditionType.PRESENCE,
                        parameters={"character_type": "stranger"}
                    ),
                    Condition(
                        type=ConditionType.STATE,
                        parameters={"key": "relationship_trust", "value": 0.3, "operator": "less"}
                    )
                ],
                actions=[
                    Action(
                        name="Watch carefully",
                        action_type="observe",
                        parameters={"target": "stranger", "subtle": True},
                        duration=10.0
                    ),
                    Action(
                        name="Move to better vantage",
                        action_type="move",
                        parameters={"destination": "corner_table"},
                        duration=2.0
                    )
                ],
                priority=BehaviorPriority.MEDIUM,
                forbidden_moods=[Mood.HAPPY, Mood.CONTENT]
            ))
    
    def add_rule(self, rule: BehaviorRule) -> None:
        """Add a behavioral rule."""
        self.rules.append(rule)
        # Sort by priority
        self.rules.sort(key=lambda r: r.priority.value, reverse=True)
    
    def evaluate_rules(self, context: Dict[str, Any]) -> Optional[BehaviorRule]:
        """Evaluate all rules and return highest priority applicable rule."""
        # Add NPC state to context
        context["npc_state"] = {
            "energy_level": self.psychology.energy_level,
            "stress_level": self.psychology.stress_level,
            "intoxication": self.psychology.intoxication
        }
        
        current_mood = self.psychology.current_mood
        
        # Check for interrupt conditions
        for rule in self.rules:
            if rule.interrupt_current and rule.can_trigger(context, current_mood):
                if self.active_behavior and rule.priority.value > self.active_behavior.priority.value:
                    return rule
        
        # If already executing behavior, continue unless done
        if self.active_behavior and self.current_actions:
            return None
        
        # Find highest priority rule that can trigger
        for rule in self.rules:
            if rule.can_trigger(context, current_mood):
                return rule
        
        # Check daily schedule as fallback
        current_time = context.get("current_time", datetime.now())
        routine = self.daily_schedule.get_current_routine(current_time)
        if routine and routine.can_trigger(context, current_mood):
            return routine
        
        return None
    
    def execute_behavior(self, rule: BehaviorRule) -> Optional[Action]:
        """Execute a behavior rule."""
        if rule != self.active_behavior:
            # New behavior
            self.active_behavior = rule
            self.current_actions = rule.trigger()
            self.action_index = 0
        
        # Get current action
        if self.action_index < len(self.current_actions):
            action = self.current_actions[self.action_index]
            return action
        else:
            # Behavior complete
            self.active_behavior = None
            self.current_actions = []
            self.action_index = 0
            return None
    
    def complete_action(self) -> None:
        """Mark current action as complete."""
        self.action_index += 1
        
        # Update NPC state based on action
        if self.action_index <= len(self.current_actions):
            completed_action = self.current_actions[self.action_index - 1]
            
            # Apply energy cost
            self.psychology.energy_level = max(0.0, 
                self.psychology.energy_level - completed_action.energy_cost)
    
    def get_idle_behavior(self) -> Action:
        """Get a default idle behavior."""
        idle_behaviors = [
            Action("Look around", "observe", {"target": "surroundings"}, duration=2.0),
            Action("Adjust clothing", "gesture", {"type": "fidget"}, duration=1.0),
            Action("Sigh", "emote", {"emotion": "bored"}, duration=0.5),
            Action("Shift position", "gesture", {"type": "shift"}, duration=1.0)
        ]
        
        # Personality-based idle behaviors
        if self.psychology.base_personality == Personality.FRIENDLY:
            idle_behaviors.extend([
                Action("Smile at someone", "emote", {"emotion": "friendly"}, duration=1.0),
                Action("Wave to acquaintance", "gesture", {"type": "wave"}, duration=1.0)
            ])
        elif self.psychology.base_personality == Personality.SUSPICIOUS:
            idle_behaviors.extend([
                Action("Check exits", "observe", {"target": "exits"}, duration=2.0),
                Action("Watch crowd", "observe", {"target": "crowd", "subtle": True}, duration=3.0)
            ])
        
        return random.choice(idle_behaviors)
    
    def add_reactive_rule(self, trigger_event: str, response_actions: List[Action],
                         conditions: Optional[List[Condition]] = None,
                         priority: BehaviorPriority = BehaviorPriority.HIGH) -> None:
        """Add a rule that reacts to specific events."""
        rule_conditions = [
            Condition(
                type=ConditionType.EVENT,
                parameters={"event_type": trigger_event}
            )
        ]
        
        if conditions:
            rule_conditions.extend(conditions)
        
        rule = BehaviorRule(
            id=f"{self.npc_id}_react_{trigger_event}",
            name=f"React to {trigger_event}",
            description=f"Response to {trigger_event} event",
            conditions=rule_conditions,
            actions=response_actions,
            priority=priority,
            interrupt_current=priority.value >= BehaviorPriority.HIGH.value
        )
        
        self.add_rule(rule)
    
    def get_behavior_description(self) -> str:
        """Get description of current behavior."""
        if self.active_behavior and self.current_actions and self.action_index < len(self.current_actions):
            current_action = self.current_actions[self.action_index]
            return f"{self.active_behavior.name}: {current_action.get_description()}"
        else:
            return "Idle"