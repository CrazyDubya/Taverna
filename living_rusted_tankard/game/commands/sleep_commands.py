"""
Sleep-related command handlers for The Living Rusted Tankard.
"""
from typing import Dict, Any
from dataclasses import asdict

def handle_sleep_command(args: str, sleep_mechanics) -> Dict[str, Any]:
    """Handle sleep command"""
    if not args:
        return {
            "message": "Sleep for how long? (e.g., 'sleep 8')",
            "time_advanced": 0
        }
    
    try:
        hours = float(args)
        if hours <= 0:
            return {
                "message": "You can't sleep for zero or negative time.",
                "time_advanced": 0
            }
        
        return sleep_mechanics.attempt_sleep(hours)
        
    except ValueError:
        return {
            "message": "Please enter a valid number of hours.",
            "time_advanced": 0
        }

def handle_inquire_sleep(sleep_mechanics) -> Dict[str, Any]:
    """Handle player inquiring about sleep"""
    meta_trigger = sleep_mechanics.check_meta_quest_trigger("inquire_sleep")
    if meta_trigger:
        return meta_trigger
    
    # Regular response
    hours_awake = sleep_mechanics.clock.current_time - sleep_mechanics.state.last_sleep_time
    if hours_awake > 24:
        message = ("You're not sure why, but you haven't felt the need to sleep "
                  "in a very long time. This doesn't seem normal...")
    else:
        message = sleep_mechanics.get_fatigue_description()
    
    return {
        "message": message,
        "time_advanced": 0,
        "state_update": asdict(sleep_mechanics.state) if hasattr(sleep_mechanics, 'state') else None
    }
