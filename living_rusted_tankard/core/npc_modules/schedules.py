"""NPC scheduling and routine management."""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum

from .behavioral_rules import BehaviorRule, Action, Condition, ConditionType, BehaviorPriority


class ActivityType(Enum):
    """Types of scheduled activities."""

    WORK = "work"
    EAT = "eat"
    SLEEP = "sleep"
    SOCIAL = "social"
    PERSONAL = "personal"
    LEISURE = "leisure"
    WORSHIP = "worship"
    TRAINING = "training"
    PATROL = "patrol"
    CUSTOM = "custom"


class DayType(Enum):
    """Types of days that affect schedules."""

    NORMAL = "normal"
    HOLIDAY = "holiday"
    MARKET = "market"
    FESTIVAL = "festival"
    REST = "rest"


@dataclass
class ScheduleBlock:
    """A block of time in a schedule."""

    start_time: time
    end_time: time
    activity: ActivityType
    location: str
    description: str
    priority: int = 5  # 1-10, higher = more important
    flexible: bool = False  # Can be shifted if needed
    interruptible: bool = True
    energy_cost: float = 0.1

    def duration_minutes(self) -> int:
        """Get duration in minutes."""
        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt = datetime.combine(datetime.today(), self.end_time)

        # Handle day wrap
        if end_dt < start_dt:
            end_dt += timedelta(days=1)

        return int((end_dt - start_dt).total_seconds() / 60)

    def contains_time(self, check_time: time) -> bool:
        """Check if a time falls within this block."""
        if self.start_time <= self.end_time:
            return self.start_time <= check_time < self.end_time
        else:  # Wraps midnight
            return check_time >= self.start_time or check_time < self.end_time


@dataclass
class ScheduleVariation:
    """A variation from normal schedule."""

    condition: Condition
    replacement_blocks: List[ScheduleBlock]
    description: str


class NPCSchedule:
    """Manages an NPC's daily and weekly schedules."""

    def __init__(self, npc_id: str, occupation: str = "patron"):
        self.npc_id = npc_id
        self.occupation = occupation

        # Base schedules for different day types
        self.schedules: Dict[DayType, List[ScheduleBlock]] = {day_type: [] for day_type in DayType}

        # Variations based on conditions
        self.variations: List[ScheduleVariation] = []

        # Current schedule state
        self.current_block: Optional[ScheduleBlock] = None
        self.next_block: Optional[ScheduleBlock] = None
        self.deviation_reason: Optional[str] = None

        # Initialize based on occupation
        self._initialize_occupation_schedule()

    def _initialize_occupation_schedule(self) -> None:
        """Create default schedule based on occupation."""
        if self.occupation == "bartender":
            self._create_bartender_schedule()
        elif self.occupation == "guard":
            self._create_guard_schedule()
        elif self.occupation == "merchant":
            self._create_merchant_schedule()
        elif self.occupation == "patron":
            self._create_patron_schedule()
        elif self.occupation == "cook":
            self._create_cook_schedule()
        else:
            self._create_generic_schedule()

    def _create_bartender_schedule(self) -> None:
        """Create schedule for bartender."""
        normal_schedule = [
            ScheduleBlock(
                time(6, 0), time(7, 0), ActivityType.PERSONAL, "quarters", "Morning routine", priority=8, flexible=True
            ),
            ScheduleBlock(
                time(7, 0), time(8, 0), ActivityType.EAT, "kitchen", "Breakfast", priority=7, interruptible=True
            ),
            ScheduleBlock(
                time(8, 0),
                time(12, 0),
                ActivityType.WORK,
                "bar_area",
                "Morning shift - preparing and serving",
                priority=9,
                interruptible=True,
                energy_cost=0.2,
            ),
            ScheduleBlock(time(12, 0), time(13, 0), ActivityType.EAT, "kitchen", "Lunch break", priority=7),
            ScheduleBlock(
                time(13, 0),
                time(18, 0),
                ActivityType.WORK,
                "bar_area",
                "Afternoon shift - busy period",
                priority=10,
                interruptible=False,
                energy_cost=0.3,
            ),
            ScheduleBlock(time(18, 0), time(19, 0), ActivityType.EAT, "kitchen", "Dinner break", priority=7),
            ScheduleBlock(
                time(19, 0),
                time(23, 0),
                ActivityType.WORK,
                "bar_area",
                "Evening shift - peak hours",
                priority=10,
                interruptible=False,
                energy_cost=0.4,
            ),
            ScheduleBlock(time(23, 0), time(23, 30), ActivityType.WORK, "bar_area", "Closing duties", priority=8),
            ScheduleBlock(
                time(23, 30), time(6, 0), ActivityType.SLEEP, "quarters", "Sleep", priority=10, interruptible=False
            ),
        ]

        self.schedules[DayType.NORMAL] = normal_schedule

        # Holiday schedule - tavern is busier
        holiday_schedule = normal_schedule.copy()
        # Extend evening shift
        for block in holiday_schedule:
            if block.activity == ActivityType.WORK and block.start_time == time(19, 0):
                block.end_time = time(1, 0)  # Work until 1 AM
                block.energy_cost = 0.5

        self.schedules[DayType.HOLIDAY] = holiday_schedule

        # Add variations
        self.variations.append(
            ScheduleVariation(
                condition=Condition(ConditionType.STATE, {"key": "tavern_crowded", "value": True}),
                replacement_blocks=[
                    ScheduleBlock(
                        time(12, 0),
                        time(12, 30),
                        ActivityType.EAT,
                        "bar_area",
                        "Quick lunch behind bar",
                        priority=6,
                        flexible=True,
                    )
                ],
                description="Skip proper lunch when tavern is crowded",
            )
        )

    def _create_guard_schedule(self) -> None:
        """Create schedule for guard."""
        normal_schedule = [
            ScheduleBlock(
                time(6, 0),
                time(7, 0),
                ActivityType.PERSONAL,
                "quarters",
                "Morning routine and equipment check",
                priority=8,
            ),
            ScheduleBlock(time(7, 0), time(7, 30), ActivityType.EAT, "kitchen", "Breakfast", priority=7),
            ScheduleBlock(
                time(7, 30),
                time(12, 0),
                ActivityType.PATROL,
                "main_hall",
                "Morning patrol",
                priority=9,
                energy_cost=0.2,
            ),
            ScheduleBlock(time(12, 0), time(13, 0), ActivityType.EAT, "main_hall", "Lunch while watching", priority=7),
            ScheduleBlock(
                time(13, 0),
                time(18, 0),
                ActivityType.PATROL,
                "various",
                "Afternoon rounds",
                priority=9,
                energy_cost=0.25,
            ),
            ScheduleBlock(time(18, 0), time(19, 0), ActivityType.EAT, "kitchen", "Dinner", priority=7),
            ScheduleBlock(
                time(19, 0),
                time(2, 0),
                ActivityType.PATROL,
                "main_hall",
                "Night watch - peak hours",
                priority=10,
                interruptible=False,
                energy_cost=0.3,
            ),
            ScheduleBlock(time(2, 0), time(6, 0), ActivityType.SLEEP, "quarters", "Sleep", priority=10),
        ]

        self.schedules[DayType.NORMAL] = normal_schedule

        # Create rotating patrol locations
        self.variations.append(
            ScheduleVariation(
                condition=Condition(ConditionType.TIME, {"start_hour": 13, "end_hour": 18}),
                replacement_blocks=[
                    ScheduleBlock(
                        time(13, 0), time(14, 0), ActivityType.PATROL, "gambling_den", "Check gambling den", priority=9
                    ),
                    ScheduleBlock(
                        time(14, 0), time(15, 0), ActivityType.PATROL, "wine_cellar", "Check cellars", priority=9
                    ),
                    ScheduleBlock(
                        time(15, 0), time(16, 0), ActivityType.PATROL, "guest_hallway", "Check guest floors", priority=9
                    ),
                    ScheduleBlock(
                        time(16, 0), time(18, 0), ActivityType.PATROL, "main_hall", "Return to main hall", priority=9
                    ),
                ],
                description="Afternoon patrol route",
            )
        )

    def _create_merchant_schedule(self) -> None:
        """Create schedule for merchant."""
        normal_schedule = [
            ScheduleBlock(time(7, 0), time(8, 0), ActivityType.PERSONAL, "guest_room_2", "Morning routine", priority=7),
            ScheduleBlock(
                time(8, 0), time(9, 0), ActivityType.EAT, "main_hall", "Breakfast in common room", priority=7
            ),
            ScheduleBlock(
                time(9, 0),
                time(12, 0),
                ActivityType.WORK,
                "main_hall",
                "Meeting with potential customers",
                priority=8,
                energy_cost=0.15,
            ),
            ScheduleBlock(time(12, 0), time(13, 0), ActivityType.EAT, "main_hall", "Lunch", priority=7),
            ScheduleBlock(
                time(13, 0),
                time(17, 0),
                ActivityType.WORK,
                "private_booth",
                "Private business dealings",
                priority=9,
                energy_cost=0.2,
            ),
            ScheduleBlock(
                time(17, 0),
                time(19, 0),
                ActivityType.SOCIAL,
                "fireplace_nook",
                "Socializing and networking",
                priority=6,
            ),
            ScheduleBlock(time(19, 0), time(20, 0), ActivityType.EAT, "main_hall", "Dinner", priority=7),
            ScheduleBlock(
                time(20, 0),
                time(22, 0),
                ActivityType.LEISURE,
                "gambling_den",
                "Gambling and entertainment",
                priority=5,
                flexible=True,
            ),
            ScheduleBlock(time(22, 0), time(7, 0), ActivityType.SLEEP, "guest_room_2", "Sleep", priority=10),
        ]

        self.schedules[DayType.NORMAL] = normal_schedule

        # Market day schedule
        market_schedule = normal_schedule.copy()
        # Replace morning work with market visit
        market_schedule[2] = ScheduleBlock(
            time(9, 0),
            time(12, 0),
            ActivityType.WORK,
            "courtyard",
            "Visiting market stalls",
            priority=9,
            energy_cost=0.25,
        )

        self.schedules[DayType.MARKET] = market_schedule

    def _create_patron_schedule(self) -> None:
        """Create schedule for regular patron."""
        normal_schedule = [
            ScheduleBlock(
                time(8, 0),
                time(9, 0),
                ActivityType.PERSONAL,
                "guest_room_1",
                "Morning routine",
                priority=6,
                flexible=True,
            ),
            ScheduleBlock(
                time(9, 0), time(10, 0), ActivityType.EAT, "main_hall", "Late breakfast", priority=6, flexible=True
            ),
            ScheduleBlock(
                time(10, 0),
                time(12, 0),
                ActivityType.LEISURE,
                "main_hall",
                "Drinking and chatting",
                priority=4,
                energy_cost=0.05,
            ),
            ScheduleBlock(time(12, 0), time(13, 0), ActivityType.EAT, "main_hall", "Lunch", priority=7),
            ScheduleBlock(
                time(13, 0), time(15, 0), ActivityType.LEISURE, "fireplace_nook", "Afternoon relaxation", priority=3
            ),
            ScheduleBlock(
                time(15, 0), time(18, 0), ActivityType.SOCIAL, "main_hall", "Socializing with other patrons", priority=5
            ),
            ScheduleBlock(time(18, 0), time(19, 0), ActivityType.EAT, "main_hall", "Dinner", priority=7),
            ScheduleBlock(
                time(19, 0),
                time(22, 0),
                ActivityType.LEISURE,
                "main_hall",
                "Evening drinking",
                priority=5,
                energy_cost=0.1,
            ),
            ScheduleBlock(
                time(22, 0),
                time(23, 0),
                ActivityType.LEISURE,
                "gambling_den",
                "Late night gambling",
                priority=4,
                flexible=True,
            ),
            ScheduleBlock(time(23, 0), time(8, 0), ActivityType.SLEEP, "guest_room_1", "Sleep", priority=9),
        ]

        self.schedules[DayType.NORMAL] = normal_schedule

        # Add drinking buddy variation
        self.variations.append(
            ScheduleVariation(
                condition=Condition(ConditionType.PRESENCE, {"character_type": "drinking_buddy"}),
                replacement_blocks=[
                    ScheduleBlock(
                        time(19, 0),
                        time(1, 0),
                        ActivityType.SOCIAL,
                        "main_hall",
                        "Drinking with friends",
                        priority=7,
                        energy_cost=0.2,
                    )
                ],
                description="Extended drinking when friends are present",
            )
        )

    def _create_cook_schedule(self) -> None:
        """Create schedule for cook."""
        normal_schedule = [
            ScheduleBlock(
                time(4, 0), time(5, 0), ActivityType.PERSONAL, "quarters", "Early morning routine", priority=8
            ),
            ScheduleBlock(
                time(5, 0),
                time(7, 0),
                ActivityType.WORK,
                "kitchen",
                "Breakfast preparation",
                priority=10,
                energy_cost=0.2,
            ),
            ScheduleBlock(time(7, 0), time(8, 0), ActivityType.EAT, "kitchen", "Quick breakfast", priority=7),
            ScheduleBlock(
                time(8, 0),
                time(12, 0),
                ActivityType.WORK,
                "kitchen",
                "Lunch preparation and cooking",
                priority=10,
                energy_cost=0.3,
            ),
            ScheduleBlock(time(12, 0), time(13, 0), ActivityType.EAT, "kitchen", "Lunch break", priority=8),
            ScheduleBlock(
                time(13, 0),
                time(14, 0),
                ActivityType.PERSONAL,
                "courtyard",
                "Rest and fresh air",
                priority=5,
                flexible=True,
            ),
            ScheduleBlock(
                time(14, 0),
                time(19, 0),
                ActivityType.WORK,
                "kitchen",
                "Dinner preparation - busiest time",
                priority=10,
                interruptible=False,
                energy_cost=0.4,
            ),
            ScheduleBlock(time(19, 0), time(20, 0), ActivityType.EAT, "kitchen", "Dinner", priority=8),
            ScheduleBlock(time(20, 0), time(21, 0), ActivityType.WORK, "kitchen", "Kitchen cleanup", priority=8),
            ScheduleBlock(time(21, 0), time(4, 0), ActivityType.SLEEP, "quarters", "Sleep", priority=10),
        ]

        self.schedules[DayType.NORMAL] = normal_schedule

    def _create_generic_schedule(self) -> None:
        """Create a generic schedule."""
        normal_schedule = [
            ScheduleBlock(time(7, 0), time(8, 0), ActivityType.PERSONAL, "quarters", "Morning routine", priority=7),
            ScheduleBlock(time(8, 0), time(9, 0), ActivityType.EAT, "main_hall", "Breakfast", priority=7),
            ScheduleBlock(time(9, 0), time(12, 0), ActivityType.WORK, "main_hall", "Work or activities", priority=8),
            ScheduleBlock(time(12, 0), time(13, 0), ActivityType.EAT, "main_hall", "Lunch", priority=7),
            ScheduleBlock(time(13, 0), time(18, 0), ActivityType.WORK, "main_hall", "Afternoon activities", priority=8),
            ScheduleBlock(time(18, 0), time(19, 0), ActivityType.EAT, "main_hall", "Dinner", priority=7),
            ScheduleBlock(
                time(19, 0), time(22, 0), ActivityType.LEISURE, "main_hall", "Evening relaxation", priority=5
            ),
            ScheduleBlock(time(22, 0), time(7, 0), ActivityType.SLEEP, "quarters", "Sleep", priority=10),
        ]

        self.schedules[DayType.NORMAL] = normal_schedule

    def get_schedule_for_day(self, day_type: DayType = DayType.NORMAL) -> List[ScheduleBlock]:
        """Get schedule for specific day type."""
        return self.schedules.get(day_type, self.schedules[DayType.NORMAL])

    def get_current_block(
        self, current_time: datetime, day_type: DayType = DayType.NORMAL, context: Optional[Dict[str, Any]] = None
    ) -> Optional[ScheduleBlock]:
        """Get the schedule block for current time."""
        schedule = self.get_schedule_for_day(day_type)
        current_time_only = current_time.time()

        # Check variations first
        if context:
            for variation in self.variations:
                if variation.condition.evaluate(context):
                    for block in variation.replacement_blocks:
                        if block.contains_time(current_time_only):
                            return block

        # Check normal schedule
        for block in schedule:
            if block.contains_time(current_time_only):
                return block

        return None

    def get_next_block(self, current_time: datetime, day_type: DayType = DayType.NORMAL) -> Optional[ScheduleBlock]:
        """Get the next scheduled block."""
        schedule = self.get_schedule_for_day(day_type)
        current_time_only = current_time.time()

        # Find next block
        next_blocks = []
        for block in schedule:
            if block.start_time > current_time_only:
                next_blocks.append(block)

        if next_blocks:
            return min(next_blocks, key=lambda b: b.start_time)
        else:
            # Next block is tomorrow, return first block
            return schedule[0] if schedule else None

    def should_transition(
        self, current_time: datetime, day_type: DayType = DayType.NORMAL, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[ScheduleBlock]]:
        """Check if it's time to transition to a new activity."""
        current_block = self.get_current_block(current_time, day_type, context)

        if self.current_block != current_block:
            return True, current_block

        return False, None

    def create_schedule_behaviors(self) -> List[BehaviorRule]:
        """Convert schedule into behavioral rules."""
        rules = []

        for day_type, schedule in self.schedules.items():
            for block in schedule:
                # Create rule for each schedule block
                rule = BehaviorRule(
                    id=f"{self.npc_id}_schedule_{block.activity.value}_{block.start_time.hour}",
                    name=f"{block.activity.value} at {block.location}",
                    description=block.description,
                    conditions=[
                        Condition(
                            ConditionType.TIME,
                            {
                                "start_hour": block.start_time.hour,
                                "end_hour": block.end_time.hour if block.end_time.hour > block.start_time.hour else 24,
                            },
                        )
                    ],
                    actions=[
                        Action(
                            name=f"Go to {block.location}",
                            action_type="move",
                            parameters={"destination": block.location},
                            duration=5.0,
                        ),
                        Action(
                            name=block.description,
                            action_type="scheduled_activity",
                            parameters={"activity": block.activity.value, "location": block.location},
                            duration=float(block.duration_minutes()),
                            energy_cost=block.energy_cost,
                        ),
                    ],
                    priority=BehaviorPriority.MEDIUM if block.flexible else BehaviorPriority.HIGH,
                    cooldown=0.0,  # No cooldown for scheduled activities
                )

                rules.append(rule)

        return rules

    def deviate_from_schedule(self, reason: str, duration_minutes: int = 30) -> None:
        """Temporarily deviate from schedule."""
        self.deviation_reason = reason
        # In a real implementation, this would track when to return to schedule

    def get_schedule_summary(self, day_type: DayType = DayType.NORMAL) -> str:
        """Get a human-readable schedule summary."""
        schedule = self.get_schedule_for_day(day_type)

        summary_parts = [f"Schedule for {self.occupation} ({day_type.value} day):"]

        for block in schedule:
            summary_parts.append(
                f"  {block.start_time.strftime('%H:%M')} - "
                f"{block.end_time.strftime('%H:%M')}: "
                f"{block.activity.value} at {block.location}"
            )

        return "\n".join(summary_parts)
