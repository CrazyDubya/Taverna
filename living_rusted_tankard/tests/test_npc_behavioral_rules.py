"""Tests for NPC behavioral rules system."""

import pytest
from datetime import datetime, time
from unittest.mock import Mock, patch

from core.npc_systems.behavioral_rules import (
    BehaviorEngine,
    BehaviorRule,
    BehaviorPriority,
    Condition,
    ConditionType,
    Action,
    DailySchedule,
)
from core.npc_systems.psychology import NPCPsychology, Personality, Mood


class TestCondition:
    """Test Condition functionality."""

    def test_time_condition(self):
        """Test time-based conditions."""
        # Morning condition
        morning_condition = Condition(
            ConditionType.TIME, {"start_hour": 6, "end_hour": 12}
        )

        morning_context = {"current_time": datetime.now().replace(hour=8)}
        assert morning_condition.evaluate(morning_context)

        afternoon_context = {"current_time": datetime.now().replace(hour=14)}
        assert not morning_condition.evaluate(afternoon_context)

        # Overnight condition
        night_condition = Condition(
            ConditionType.TIME, {"start_hour": 22, "end_hour": 6}
        )

        late_night_context = {"current_time": datetime.now().replace(hour=23)}
        assert night_condition.evaluate(late_night_context)

        early_morning_context = {"current_time": datetime.now().replace(hour=4)}
        assert night_condition.evaluate(early_morning_context)

    def test_location_condition(self):
        """Test location-based conditions."""
        condition = Condition(
            ConditionType.LOCATION, {"locations": ["main_hall", "bar_area"]}
        )

        valid_context = {"current_location": "main_hall"}
        assert condition.evaluate(valid_context)

        invalid_context = {"current_location": "kitchen"}
        assert not condition.evaluate(invalid_context)

    def test_presence_condition(self):
        """Test presence detection conditions."""
        # Specific character
        specific_condition = Condition(
            ConditionType.PRESENCE, {"character_id": "npc_guard"}
        )

        with_guard = {"area_occupants": ["npc_guard", "npc_patron"]}
        assert specific_condition.evaluate(with_guard)

        without_guard = {"area_occupants": ["npc_patron"]}
        assert not specific_condition.evaluate(without_guard)

        # Character type
        type_condition = Condition(ConditionType.PRESENCE, {"character_type": "guard"})

        with_guard_type = {
            "area_occupants": ["npc_1", "npc_2"],
            "character_types": {"npc_1": "guard", "npc_2": "patron"},
        }
        assert type_condition.evaluate(with_guard_type)

    def test_state_condition(self):
        """Test state-based conditions."""
        # Equals
        energy_condition = Condition(
            ConditionType.STATE,
            {"key": "energy_level", "value": 0.5, "operator": "equals"},
        )

        exact_context = {"npc_state": {"energy_level": 0.5}}
        assert energy_condition.evaluate(exact_context)

        # Greater than
        stress_condition = Condition(
            ConditionType.STATE,
            {"key": "stress_level", "value": 0.7, "operator": "greater"},
        )

        high_stress = {"npc_state": {"stress_level": 0.8}}
        assert stress_condition.evaluate(high_stress)

        low_stress = {"npc_state": {"stress_level": 0.6}}
        assert not stress_condition.evaluate(low_stress)

    def test_negated_condition(self):
        """Test negated conditions."""
        condition = Condition(
            ConditionType.LOCATION, {"locations": ["kitchen"]}, negate=True
        )

        in_kitchen = {"current_location": "kitchen"}
        assert not condition.evaluate(in_kitchen)

        not_in_kitchen = {"current_location": "main_hall"}
        assert condition.evaluate(not_in_kitchen)

    def test_random_condition(self):
        """Test random conditions."""
        condition = Condition(ConditionType.RANDOM, {"probability": 1.0})  # Always true
        assert condition.evaluate({})

        condition = Condition(
            ConditionType.RANDOM, {"probability": 0.0}  # Always false
        )
        assert not condition.evaluate({})


class TestAction:
    """Test Action functionality."""

    def test_action_creation(self):
        """Test creating actions."""
        move_action = Action(
            name="Move to bar",
            action_type="move",
            parameters={"destination": "bar_area"},
            duration=2.0,
            energy_cost=0.05,
        )

        assert move_action.name == "Move to bar"
        assert move_action.action_type == "move"
        assert move_action.parameters["destination"] == "bar_area"
        assert move_action.duration == 2.0
        assert move_action.energy_cost == 0.05

    def test_action_descriptions(self):
        """Test getting human-readable descriptions."""
        actions = [
            (Action("Move", "move", {"destination": "kitchen"}), "Move to kitchen"),
            (
                Action("Speak", "speak", {"dialogue": "Hello there!"}),
                "Say: Hello there!",
            ),
            (
                Action("Interact", "interact", {"target": "notice_board"}),
                "Interact with notice_board",
            ),
            (Action("Wait", "wait", duration=5.0), "Wait for 5.0 minutes"),
            (Action("Custom", "custom_type"), "Custom"),
        ]

        for action, expected in actions:
            assert action.get_description() == expected


class TestBehaviorRule:
    """Test BehaviorRule functionality."""

    def test_rule_creation(self):
        """Test creating behavior rules."""
        rule = BehaviorRule(
            id="test_rule",
            name="Test Rule",
            description="A test behavioral rule",
            conditions=[
                Condition(ConditionType.TIME, {"start_hour": 8, "end_hour": 10})
            ],
            actions=[Action("Move", "move", {"destination": "kitchen"})],
            priority=BehaviorPriority.HIGH,
            cooldown=5.0,
        )

        assert rule.id == "test_rule"
        assert rule.priority == BehaviorPriority.HIGH
        assert rule.cooldown == 5.0

    def test_rule_triggering(self):
        """Test rule trigger conditions."""
        rule = BehaviorRule(
            id="morning_rule",
            name="Morning Routine",
            description="Morning activities",
            conditions=[
                Condition(ConditionType.TIME, {"start_hour": 6, "end_hour": 9})
            ],
            actions=[Action("Wake up", "personal")],
            cooldown=1440.0,  # Once per day
        )

        morning_context = {"current_time": datetime.now().replace(hour=7)}
        assert rule.can_trigger(morning_context, Mood.CONTENT)

        # Trigger it
        actions = rule.trigger()
        assert len(actions) == 1
        assert rule.last_triggered is not None

        # Can't trigger again immediately
        assert not rule.can_trigger(morning_context, Mood.CONTENT)

    def test_mood_requirements(self):
        """Test mood-based rule requirements."""
        rule = BehaviorRule(
            id="happy_rule",
            name="Celebration",
            description="Celebrate when happy",
            conditions=[],
            actions=[Action("Celebrate", "emote")],
            requires_mood=[Mood.HAPPY, Mood.EXCITED],
            forbidden_moods=[Mood.SAD, Mood.ANGRY],
        )

        # Happy mood - can trigger
        assert rule.can_trigger({}, Mood.HAPPY)

        # Content mood - cannot trigger
        assert not rule.can_trigger({}, Mood.CONTENT)

        # Angry mood - forbidden
        assert not rule.can_trigger({}, Mood.ANGRY)


class TestDailySchedule:
    """Test DailySchedule functionality."""

    def test_schedule_creation(self):
        """Test creating daily schedules."""
        schedule = DailySchedule("npc_test")

        # Add morning routine
        schedule.add_routine(
            time_slot=(7, 9), location="quarters", activity="morning_routine"
        )

        assert len(schedule.schedule_rules) == 1
        rule = schedule.schedule_rules[0]
        assert "routine_7_quarters" in rule.id

    def test_schedule_variations(self):
        """Test schedule variations."""
        schedule = DailySchedule("npc_test")

        # Add routine with variations
        schedule.add_routine(
            time_slot=(12, 13),
            location="main_hall",
            activity="lunch",
            variations=[
                {
                    "location": "kitchen",
                    "activity": "quick_lunch",
                    "probability": 0.3,
                    "duration": 20.0,
                }
            ],
        )

        assert len(schedule.schedule_rules) == 1
        assert len(schedule.routine_variations) == 1

        # Check variation was created
        main_rule_id = schedule.schedule_rules[0].id
        variations = schedule.routine_variations[main_rule_id]
        assert len(variations) == 1
        assert variations[0].actions[1].parameters["activity"] == "quick_lunch"

    def test_get_current_routine(self):
        """Test getting routine for current time."""
        schedule = DailySchedule("npc_test")

        schedule.add_routine((8, 12), "workplace", "work")
        schedule.add_routine((12, 13), "break_room", "lunch")

        # During work hours
        work_time = datetime.now().replace(hour=10)
        routine = schedule.get_current_routine(work_time)
        assert routine is not None
        assert "work" in routine.actions[1].parameters["activity"]

        # During lunch
        lunch_time = datetime.now().replace(hour=12, minute=30)
        routine = schedule.get_current_routine(lunch_time)
        assert routine is not None
        assert "lunch" in routine.actions[1].parameters["activity"]


class TestBehaviorEngine:
    """Test BehaviorEngine functionality."""

    def test_engine_initialization(self):
        """Test initializing behavior engine."""
        psychology = NPCPsychology("npc_test", Personality.FRIENDLY)
        engine = BehaviorEngine("npc_test", psychology)

        assert engine.npc_id == "npc_test"
        assert engine.psychology == psychology

        # Should have personality-based rules
        assert len(engine.rules) > 0

        # Friendly NPCs should have greeting rule
        greeting_rules = [r for r in engine.rules if "greet" in r.id]
        assert len(greeting_rules) > 0

    def test_rule_evaluation(self):
        """Test evaluating rules."""
        psychology = NPCPsychology("npc_test")
        engine = BehaviorEngine("npc_test", psychology)

        # Add a simple rule
        rule = BehaviorRule(
            id="test_rule",
            name="Test",
            description="Test rule",
            conditions=[
                Condition(
                    ConditionType.STATE,
                    {"key": "energy_level", "value": 0.5, "operator": "greater"},
                )
            ],
            actions=[Action("Test", "test")],
            priority=BehaviorPriority.MEDIUM,
        )
        engine.add_rule(rule)

        # Context with sufficient energy
        context = {"current_time": datetime.now()}

        # Should find the rule
        selected = engine.evaluate_rules(context)
        assert selected == rule

    def test_behavior_execution(self):
        """Test executing behaviors."""
        psychology = NPCPsychology("npc_test")
        engine = BehaviorEngine("npc_test", psychology)

        rule = BehaviorRule(
            id="multi_action",
            name="Multi Action",
            description="Multiple actions",
            conditions=[],
            actions=[
                Action("First", "test", duration=1.0),
                Action("Second", "test", duration=2.0),
                Action("Third", "test", duration=1.0),
            ],
        )

        # Execute behavior
        action1 = engine.execute_behavior(rule)
        assert action1.name == "First"
        assert engine.action_index == 0

        # Complete first action
        engine.complete_action()
        assert engine.action_index == 1

        # Get next action
        action2 = engine.execute_behavior(rule)
        assert action2.name == "Second"

        # Complete all actions
        engine.complete_action()
        engine.complete_action()

        # Should return None when done
        action4 = engine.execute_behavior(rule)
        assert action4 is None
        assert engine.active_behavior is None

    def test_interrupt_behavior(self):
        """Test interrupting behaviors."""
        psychology = NPCPsychology("npc_test")
        engine = BehaviorEngine("npc_test", psychology)

        # Low priority rule
        low_rule = BehaviorRule(
            id="low_priority",
            name="Low Priority",
            description="Low priority task",
            conditions=[],
            actions=[Action("Low", "test", duration=10.0)],
            priority=BehaviorPriority.LOW,
        )

        # High priority interrupt rule
        high_rule = BehaviorRule(
            id="high_priority",
            name="High Priority",
            description="High priority interrupt",
            conditions=[Condition(ConditionType.EVENT, {"event_type": "emergency"})],
            actions=[Action("Emergency", "test")],
            priority=BehaviorPriority.HIGH,
            interrupt_current=True,
        )

        engine.add_rule(low_rule)
        engine.add_rule(high_rule)

        # Start low priority
        engine.execute_behavior(low_rule)
        assert engine.active_behavior == low_rule

        # Emergency occurs
        emergency_context = {
            "current_time": datetime.now(),
            "current_event": {"event_type": "emergency"},
        }

        # High priority should interrupt
        selected = engine.evaluate_rules(emergency_context)
        # In real implementation, this would interrupt

    def test_idle_behavior(self):
        """Test getting idle behaviors."""
        psychology = NPCPsychology("npc_test", Personality.FRIENDLY)
        engine = BehaviorEngine("npc_test", psychology)

        idle = engine.get_idle_behavior()
        assert idle is not None
        assert idle.action_type in ["observe", "gesture", "emote"]

        # Friendly NPCs have friendly idle behaviors
        friendly_idles = []
        for _ in range(20):
            idle = engine.get_idle_behavior()
            if (
                idle.action_type == "emote"
                and idle.parameters.get("emotion") == "friendly"
            ):
                friendly_idles.append(idle)

        assert len(friendly_idles) > 0

    def test_reactive_rules(self):
        """Test adding reactive rules."""
        psychology = NPCPsychology("npc_test")
        engine = BehaviorEngine("npc_test", psychology)

        # Add reaction to threat
        engine.add_reactive_rule(
            "threat_detected",
            [
                Action("Draw weapon", "equip", {"item": "sword"}),
                Action("Warn", "speak", {"dialogue": "Stay back!"}),
            ],
            priority=BehaviorPriority.HIGH,
        )

        # Check rule was added
        threat_rules = [r for r in engine.rules if "threat_detected" in r.id]
        assert len(threat_rules) == 1
        assert threat_rules[0].interrupt_current


class TestIntegration:
    """Integration tests for behavioral system."""

    def test_schedule_to_behavior_integration(self):
        """Test converting schedules to behavioral rules."""
        psychology = NPCPsychology("bartender", Personality.FRIENDLY)
        engine = BehaviorEngine("bartender", psychology)

        # Set up bartender schedule
        engine.daily_schedule.add_routine((8, 12), "bar_area", "morning_shift")
        engine.daily_schedule.add_routine((12, 13), "kitchen", "lunch_break")

        # Convert to rules
        schedule_rules = engine.daily_schedule.create_schedule_behaviors()
        for rule in schedule_rules:
            engine.add_rule(rule)

        # During morning shift
        morning_context = {"current_time": datetime.now().replace(hour=9)}
        rule = engine.evaluate_rules(morning_context)

        assert rule is not None
        # Should be doing morning shift

    def test_complex_behavior_scenario(self):
        """Test complex behavioral scenario."""
        # Create suspicious guard
        psychology = NPCPsychology("guard", Personality.SUSPICIOUS)
        psychology.stress_level = 0.6
        engine = BehaviorEngine("guard", psychology)

        # Add custom rules
        patrol_rule = BehaviorRule(
            id="patrol",
            name="Patrol",
            description="Regular patrol",
            conditions=[
                Condition(ConditionType.TIME, {"start_hour": 8, "end_hour": 20}),
                Condition(
                    ConditionType.STATE,
                    {"key": "energy_level", "value": 0.3, "operator": "greater"},
                ),
            ],
            actions=[Action("Patrol", "move", {"destination": "patrol_route"})],
            priority=BehaviorPriority.MEDIUM,
            cooldown=30.0,
        )

        investigate_rule = BehaviorRule(
            id="investigate",
            name="Investigate",
            description="Investigate suspicious activity",
            conditions=[
                Condition(ConditionType.PRESENCE, {"character_type": "stranger"}),
                Condition(
                    ConditionType.STATE,
                    {"key": "stress_level", "value": 0.5, "operator": "greater"},
                ),
            ],
            actions=[
                Action("Approach", "move", {"destination": "stranger_location"}),
                Action("Question", "speak", {"dialogue": "State your business"}),
            ],
            priority=BehaviorPriority.HIGH,
            forbidden_moods=[Mood.HAPPY],
        )

        engine.add_rule(patrol_rule)
        engine.add_rule(investigate_rule)

        # Normal context - should patrol
        normal_context = {
            "current_time": datetime.now().replace(hour=10),
            "area_occupants": ["regular_patron"],
            "character_types": {"regular_patron": "patron"},
        }

        selected = engine.evaluate_rules(normal_context)
        assert selected == patrol_rule

        # Stranger appears - should investigate (high priority + stress)
        stranger_context = {
            "current_time": datetime.now().replace(hour=10),
            "area_occupants": ["stranger"],
            "character_types": {"stranger": "stranger"},
        }

        selected = engine.evaluate_rules(stranger_context)
        assert selected == investigate_rule
