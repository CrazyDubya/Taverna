"""Command handlers for economy-related actions."""

from typing import Dict, Any, Optional


def handle_gamble(
    args: str, economy, npc: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Handle the gamble command.

    Args:
        args: Command arguments (wager amount)
        economy: EconomyMechanics instance
        npc: Optional NPC data for flavor text

    Returns:
        Dict with result and message
    """
    if not args:
        return {
            "success": False,
            "message": "How much would you like to wager?",
            "gold_change": 0,
        }

    try:
        wager = int(args)
        if wager <= 0:
            raise ValueError("Wager must be positive")

        # Check if player can afford the wager
        if not economy.can_afford(wager):
            return {
                "success": False,
                "message": "You don't have enough gold for that wager.",
                "gold_change": 0,
            }

        # Process the gamble and return the result
        # The economy.gamble method handles all the gold calculations
        return economy.gamble(wager, npc)

    except ValueError:
        return {
            "success": False,
            "message": "Please enter a valid positive number for your wager.",
            "gold_change": 0,
        }


def handle_earn_tip(economy) -> Dict[str, Any]:
    """
    Handle the earn_tip command.

    Args:
        economy: EconomyMechanics instance

    Returns:
        Dict with result and message
    """
    return economy.earn_tip()
