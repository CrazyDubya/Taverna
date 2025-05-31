"""
NPC personal schedules and routines system.
Makes NPCs feel alive by having them follow realistic daily patterns.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, time
import random
import logging

logger = logging.getLogger(__name__)


class ActivityType(Enum):
    """Types of activities NPCs can perform."""
    WORKING = "working"
    SLEEPING = "sleeping"
    EATING = "eating"
    SOCIALIZING = "socializing"
    SHOPPING = "shopping"
    TRAVELING = "traveling"
    PERSONAL_TIME = "personal_time"
    MAINTENANCE = "maintenance"  # Cleaning, repairs, etc.
    WORSHIP = "worship"
    EXERCISE = "exercise"
    STUDY = "study"
    ENTERTAINMENT = "entertainment"


@dataclass
class ScheduleActivity:
    """A scheduled activity for an NPC."""
    activity_type: ActivityType
    start_hour: float  # 24-hour format, can include minutes as decimals
    duration_hours: float
    location: str
    description: str
    priority: int = 5  # 1-10, higher = more important
    flexibility: float = 0.1  # How much the timing can vary (0.0-1.0)
    prerequisites: List[str] = field(default_factory=list)  # Conditions that must be met
    interruption_resistance: float = 0.5  # How hard it is to interrupt this activity
    
    def get_end_hour(self) -> float:
        """Get the hour this activity ends."""
        end = self.start_hour + self.duration_hours
        return end if end < 24 else end - 24
    
    def is_active_at_hour(self, hour: float) -> bool:
        """Check if this activity is active at the given hour."""
        start = self.start_hour
        end = self.get_end_hour()
        
        # Handle activities that cross midnight
        if end < start:
            return hour >= start or hour <= end
        else:
            return start <= hour <= end
    
    def can_be_interrupted_for(self, reason: str, urgency: float) -> bool:
        """Check if this activity can be interrupted for a reason."""
        # Higher urgency or lower resistance makes interruption more likely
        threshold = self.interruption_resistance
        
        # Some activities are harder to interrupt
        if self.activity_type in [ActivityType.SLEEPING, ActivityType.WORSHIP]:
            threshold += 0.3
        elif self.activity_type == ActivityType.WORKING:
            threshold += 0.1
        
        return urgency > threshold


class NPCSchedule:
    """Daily schedule for an NPC."""
    
    def __init__(self, npc_id: str, npc_name: str, profession: str):
        self.npc_id = npc_id
        self.npc_name = npc_name
        self.profession = profession
        self.activities: List[ScheduleActivity] = []
        self.schedule_variations: Dict[str, List[ScheduleActivity]] = {}  # Special day schedules
        self.current_activity: Optional[ScheduleActivity] = None
        self.last_schedule_check: float = 0
        
        # Personal preferences that affect schedule
        self.wake_up_time: float = 6.0  # Default wake up at 6 AM
        self.sleep_time: float = 22.0  # Default sleep at 10 PM
        self.meal_times: List[float] = [7.0, 12.0, 18.0]  # Breakfast, lunch, dinner
        self.work_efficiency_peak: float = 10.0  # Hour when most productive
        
        # Schedule flexibility
        self.punctuality: float = 0.8  # How strictly they follow schedule (0.0-1.0)
        self.spontaneity: float = 0.2  # How likely to deviate for interesting opportunities
        
    def add_activity(self, activity: ScheduleActivity) -> None:
        """Add an activity to the schedule."""
        self.activities.append(activity)
        # Sort activities by start time for easier processing
        self.activities.sort(key=lambda a: a.start_hour)
        logger.debug(f"{self.npc_name} added activity: {activity.description} at {activity.start_hour:02.1f}")
    
    def get_current_activity(self, current_hour: float) -> Optional[ScheduleActivity]:
        """Get the activity the NPC should be doing now."""
        for activity in self.activities:
            if activity.is_active_at_hour(current_hour):
                return activity
        return None
    
    def get_next_activity(self, current_hour: float) -> Optional[ScheduleActivity]:
        """Get the next scheduled activity."""
        # Find activities that start after current hour
        upcoming = [a for a in self.activities if a.start_hour > current_hour]
        if upcoming:
            return min(upcoming, key=lambda a: a.start_hour)
        
        # If no activities today, get first activity of next day
        if self.activities:
            return min(self.activities, key=lambda a: a.start_hour)
        
        return None
    
    def is_available_for_interaction(self, current_hour: float, interaction_urgency: float = 0.5) -> Tuple[bool, str]:
        """Check if NPC is available for player interaction."""
        current_activity = self.get_current_activity(current_hour)
        
        if not current_activity:
            return True, "free time"
        
        # Check if current activity can be interrupted
        if current_activity.can_be_interrupted_for("player_interaction", interaction_urgency):
            return True, f"can pause {current_activity.activity_type.value}"
        
        # Not available - provide reason and time estimate
        next_free_time = self.get_next_free_time(current_hour)
        if next_free_time:
            time_until_free = next_free_time - current_hour
            if time_until_free < 0:
                time_until_free += 24  # Next day
            
            hours = int(time_until_free)
            minutes = int((time_until_free % 1) * 60)
            
            if hours == 0:
                time_desc = f"{minutes} minutes"
            else:
                time_desc = f"{hours} hours and {minutes} minutes"
            
            return False, f"busy {current_activity.activity_type.value}, free in {time_desc}"
        else:
            return False, f"busy {current_activity.activity_type.value}"
    
    def get_next_free_time(self, current_hour: float) -> Optional[float]:
        """Get the next time the NPC will be free."""
        # Find current activity end time
        current_activity = self.get_current_activity(current_hour)
        if not current_activity:
            return current_hour  # Already free
        
        end_time = current_activity.get_end_hour()
        
        # Check if there's a gap before the next activity
        next_activity = self.get_next_activity(end_time)
        if not next_activity:
            return end_time  # Free after current activity
        
        # If next activity starts immediately, find the next gap
        if next_activity.start_hour <= end_time + 0.1:  # Small buffer
            return self.get_next_free_time(next_activity.get_end_hour())
        else:
            return end_time
    
    def get_schedule_description(self, current_hour: float) -> str:
        """Get a description of what the NPC is doing and their schedule."""
        current_activity = self.get_current_activity(current_hour)
        
        if current_activity:
            end_time = current_activity.get_end_hour()
            description = f"{self.npc_name} is currently {current_activity.description}"
            
            if end_time != current_hour:
                end_time_str = f"{int(end_time):02d}:{int((end_time % 1) * 60):02d}"
                description += f" until {end_time_str}"
            
            return description
        else:
            next_activity = self.get_next_activity(current_hour)
            if next_activity:
                start_time_str = f"{int(next_activity.start_hour):02d}:{int((next_activity.start_hour % 1) * 60):02d}"
                return f"{self.npc_name} is taking a break. Next: {next_activity.description} at {start_time_str}"
            else:
                return f"{self.npc_name} has no scheduled activities right now"
    
    def adjust_for_world_event(self, event_type: str, event_data: Dict[str, Any]) -> List[str]:
        """Adjust schedule based on world events. Returns list of changes made."""
        changes = []
        
        if event_type == "festival":
            # Add entertainment activity during festival
            festival_activity = ScheduleActivity(
                activity_type=ActivityType.ENTERTAINMENT,
                start_hour=19.0,  # 7 PM
                duration_hours=3.0,
                location="town_square",
                description="attending the festival",
                priority=8,
                flexibility=0.3
            )
            self.add_activity(festival_activity)
            changes.append("added festival attendance")
        
        elif event_type == "emergency":
            # Cancel non-essential activities during emergency
            location = event_data.get("location", "")
            if location in [a.location for a in self.activities]:
                essential_types = {ActivityType.SLEEPING, ActivityType.EATING}
                non_essential = [a for a in self.activities 
                               if a.activity_type not in essential_types and a.location == location]
                
                for activity in non_essential:
                    self.activities.remove(activity)
                    changes.append(f"cancelled {activity.description} due to emergency")
        
        elif event_type == "merchant_arrival":
            # Merchants might extend shopping hours
            if "merchant" in self.profession.lower():
                work_activities = [a for a in self.activities if a.activity_type == ActivityType.WORKING]
                for activity in work_activities:
                    activity.duration_hours += 2.0
                    changes.append("extended work hours for merchant arrival")
        
        return changes


def create_schedule_for_profession(npc_id: str, npc_name: str, profession: str) -> NPCSchedule:
    """Create a realistic schedule based on NPC's profession."""
    schedule = NPCSchedule(npc_id, npc_name, profession)
    
    if profession.lower() in ["bartender", "innkeeper"]:
        # Bartenders work evening/night shift
        schedule.wake_up_time = 10.0  # 10 AM
        schedule.sleep_time = 2.0     # 2 AM
        schedule.meal_times = [10.5, 15.0, 20.0]
        
        # Work shift
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.WORKING,
            start_hour=17.0,  # 5 PM
            duration_hours=8.0,
            location="tavern_main",
            description="serving customers and managing the bar",
            priority=9,
            interruption_resistance=0.3  # Can talk while working
        ))
        
        # Preparation time
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.MAINTENANCE,
            start_hour=15.0,  # 3 PM
            duration_hours=1.5,
            location="tavern_main",
            description="cleaning and preparing the tavern",
            priority=7,
            interruption_resistance=0.4
        ))
        
    elif profession.lower() in ["merchant", "trader", "shopkeeper"]:
        # Merchants have regular daytime hours
        schedule.wake_up_time = 6.0   # 6 AM
        schedule.sleep_time = 22.0    # 10 PM
        
        # Shop hours
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.WORKING,
            start_hour=8.0,   # 8 AM
            duration_hours=10.0,
            location="merchant_stall",
            description="managing the shop and serving customers",
            priority=9,
            interruption_resistance=0.2  # Easy to interrupt for customers
        ))
        
        # Inventory management
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.MAINTENANCE,
            start_hour=7.0,   # 7 AM
            duration_hours=1.0,
            location="merchant_stall",
            description="organizing inventory and checking supplies",
            priority=6,
            interruption_resistance=0.6
        ))
        
        # Market research/shopping
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.SHOPPING,
            start_hour=19.0,  # 7 PM
            duration_hours=1.0,
            location="market",
            description="checking competitor prices and buying supplies",
            priority=5,
            interruption_resistance=0.4
        ))
        
    elif profession.lower() in ["blacksmith", "craftsman"]:
        # Craftsmen start early
        schedule.wake_up_time = 5.0   # 5 AM
        schedule.sleep_time = 21.0    # 9 PM
        
        # Work hours (split for lunch break)
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.WORKING,
            start_hour=6.0,   # 6 AM
            duration_hours=5.0,
            location="smithy",
            description="forging and crafting",
            priority=9,
            interruption_resistance=0.7  # Hard to interrupt when focused
        ))
        
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.WORKING,
            start_hour=13.0,  # 1 PM
            duration_hours=5.0,
            location="smithy",
            description="forging and crafting",
            priority=9,
            interruption_resistance=0.7
        ))
        
        # Maintenance
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.MAINTENANCE,
            start_hour=18.0,  # 6 PM
            duration_hours=1.0,
            location="smithy",
            description="maintaining tools and organizing workspace",
            priority=6,
            interruption_resistance=0.5
        ))
        
    elif profession.lower() in ["guard", "soldier"]:
        # Guards work in shifts
        shift_start = random.choice([6.0, 14.0, 22.0])  # 6 AM, 2 PM, or 10 PM shift
        
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.WORKING,
            start_hour=shift_start,
            duration_hours=8.0,
            location="guard_post",
            description="patrolling and maintaining security",
            priority=10,
            interruption_resistance=0.4  # Can be interrupted for security matters
        ))
        
        # Training
        training_time = (shift_start - 2.0) % 24
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.EXERCISE,
            start_hour=training_time,
            duration_hours=1.0,
            location="training_grounds",
            description="weapon practice and physical training",
            priority=7,
            interruption_resistance=0.6
        ))
    
    # Add common activities for all NPCs
    
    # Sleep
    sleep_duration = 8.0
    schedule.add_activity(ScheduleActivity(
        activity_type=ActivityType.SLEEPING,
        start_hour=schedule.sleep_time,
        duration_hours=sleep_duration,
        location="home",
        description="sleeping",
        priority=10,
        interruption_resistance=0.9
    ))
    
    # Meals
    for i, meal_time in enumerate(schedule.meal_times):
        meal_names = ["eating breakfast", "eating lunch", "eating dinner"]
        meal_duration = 0.5 if i == 0 else 1.0  # Breakfast is shorter
        
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.EATING,
            start_hour=meal_time,
            duration_hours=meal_duration,
            location="home" if i != 1 else "tavern_main",  # Lunch might be at tavern
            description=meal_names[i],
            priority=8,
            interruption_resistance=0.3
        ))
    
    # Personal time
    personal_time = (schedule.sleep_time - 2.0) % 24
    schedule.add_activity(ScheduleActivity(
        activity_type=ActivityType.PERSONAL_TIME,
        start_hour=personal_time,
        duration_hours=1.5,
        location="home",
        description="relaxing and tending to personal matters",
        priority=4,
        interruption_resistance=0.2,
        flexibility=0.4
    ))
    
    # Social time (random chance)
    if random.random() < 0.7:  # 70% chance of having social time
        social_time = random.uniform(18.0, 21.0)
        schedule.add_activity(ScheduleActivity(
            activity_type=ActivityType.SOCIALIZING,
            start_hour=social_time,
            duration_hours=1.0,
            location="tavern_main",
            description="socializing with friends and neighbors",
            priority=3,
            interruption_resistance=0.1,
            flexibility=0.5
        ))
    
    return schedule


class ScheduleManager:
    """Manages schedules for all NPCs."""
    
    def __init__(self):
        self.schedules: Dict[str, NPCSchedule] = {}
        self.world_events_affecting_schedules: List[Tuple[str, Dict[str, Any]]] = []
    
    def get_or_create_schedule(self, npc_id: str, npc_name: str, profession: str) -> NPCSchedule:
        """Get existing schedule or create new one."""
        if npc_id not in self.schedules:
            self.schedules[npc_id] = create_schedule_for_profession(npc_id, npc_name, profession)
            logger.info(f"Created schedule for {npc_name} ({profession})")
        
        return self.schedules[npc_id]
    
    def update_all_schedules(self, current_hour: float) -> Dict[str, str]:
        """Update all NPC schedules and return status descriptions."""
        statuses = {}
        
        for npc_id, schedule in self.schedules.items():
            schedule.current_activity = schedule.get_current_activity(current_hour)
            statuses[npc_id] = schedule.get_schedule_description(current_hour)
        
        return statuses
    
    def apply_world_event_to_schedules(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Apply a world event to all schedules."""
        all_changes = {}
        
        for npc_id, schedule in self.schedules.items():
            changes = schedule.adjust_for_world_event(event_type, event_data)
            if changes:
                all_changes[npc_id] = changes
        
        # Track this event
        self.world_events_affecting_schedules.append((event_type, event_data))
        
        return all_changes
    
    def get_npc_availability(self, npc_id: str, current_hour: float, 
                           interaction_urgency: float = 0.5) -> Tuple[bool, str]:
        """Check if an NPC is available for interaction."""
        if npc_id in self.schedules:
            return self.schedules[npc_id].is_available_for_interaction(current_hour, interaction_urgency)
        return True, "no schedule information"
    
    def get_schedule_summary(self, current_hour: float) -> Dict[str, str]:
        """Get current activity summary for all NPCs."""
        return {
            npc_id: schedule.get_schedule_description(current_hour)
            for npc_id, schedule in self.schedules.items()
        }