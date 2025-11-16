"""
Sleep and tiredness mechanics for The Living Rusted Tankard.
Handles player fatigue, sleep, and the no-sleep meta-quest.
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class TirednessState:
    """Tracks player's tiredness and sleep status"""

    tiredness: float = 0.0
    last_sleep_time: float = 0.0
    rest_immune: bool = False
    no_sleep_quest_unlocked: bool = False
    has_ever_rented_room: bool = False


class SleepMechanics:
    """Handles sleep and tiredness mechanics"""

    TIREDNESS_PER_ACTION = 0.5
    TIREDNESS_PER_HOUR = 0.1
    MAX_TIREDNESS = 10.0
    META_QUEST_HOURS = 48.0

    def __init__(self, game_clock):
        self.clock = game_clock
        self.state = TirednessState()

    def on_action(self):
        """Called after each player action"""
        if not self.state.rest_immune:
            self.state.tiredness = min(
                self.state.tiredness + self.TIREDNESS_PER_ACTION, self.MAX_TIREDNESS
            )

    def on_time_update(self, delta_hours):
        """Called when game time advances"""
        if not self.state.rest_immune:
            self.state.tiredness = min(
                self.state.tiredness + (delta_hours * self.TIREDNESS_PER_HOUR),
                self.MAX_TIREDNESS,
            )

    def can_sleep(self) -> bool:
        """Check if player can sleep"""
        return self.state.has_ever_rented_room or not self.state.rest_immune

    def attempt_sleep(self, hours: float) -> Dict[str, Any]:
        """Attempt to sleep for given hours"""
        if not self.can_sleep():
            return {
                "message": "You find yourself unable to sleep, as if something is keeping you awake...",
                "time_advanced": 0,
                "state_update": asdict(self.state),
            }

        self.state.tiredness = max(0, self.state.tiredness - hours)
        self.state.last_sleep_time = self.clock.current_time
        return {
            "message": f"You sleep for {hours} hours, feeling refreshed.",
            "time_advanced": hours,
            "state_update": asdict(self.state),
        }

    def check_meta_quest_trigger(self, action: str) -> Optional[Dict[str, Any]]:
        """Check if meta-quest should be triggered"""
        if (
            self.clock.current_time >= self.META_QUEST_HOURS
            and not self.state.has_ever_rented_room
            and action == "inquire_sleep"
            and not self.state.rest_immune
        ):
            self.state.rest_immune = True
            self.state.no_sleep_quest_unlocked = True
            return {
                "message": (
                    "As you wonder why you can't sleep, you notice something strange... "
                    "The shadows in the corner seem darker than they should be."
                ),
                "state_update": asdict(self.state),
            }
        return None

    def get_fatigue_description(self) -> str:
        """Get description based on tiredness level"""
        if self.state.tiredness < 3:
            return "You feel well-rested."
        elif self.state.tiredness < 6:
            return "You're starting to feel tired."
        elif self.state.tiredness < 9:
            return "You're quite tired and could use some rest."
        else:
            return "You're exhausted and can barely keep your eyes open."
