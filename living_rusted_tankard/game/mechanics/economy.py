"""Economy and money-related game mechanics."""

import random
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple


@dataclass
class EconomyState:
    """Tracks player's economic state."""

    gold: int = 40
    last_job_time: float = 0.0
    job_cooldown: float = 4.0  # hours


class EconomyMechanics:
    """Handles all economy-related game mechanics."""

    WIN_CHANCE = 0.6  # 60% chance to win
    BASE_TIP = 5
    MAX_TIP_BONUS = 10

    def __init__(self, game_clock):
        self.clock = game_clock
        self.state = EconomyState()

    def can_afford(self, amount: int) -> bool:
        """Check if player can afford an amount."""
        return self.state.gold >= amount

    def add_gold(self, amount: int) -> None:
        """Add gold to player's wallet."""
        self.state.gold = max(0, self.state.gold + amount)

    def gamble(
        self, wager: int, npc: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle a gambling attempt.

        Args:
            wager: Amount of gold to wager
            npc: Optional NPC data for flavor text

        Returns:
            Dict containing result and message
        """
        if not self.can_afford(wager):
            return {
                "success": False,
                "message": "You don't have enough gold for that wager.",
                "gold_change": 0,
            }

        if wager <= 0:
            return {
                "success": False,
                "message": "You must wager a positive amount.",
                "gold_change": 0,
            }

        # Roll for win/loss
        win = random.random() < self.WIN_CHANCE

        # Generate result message
        npc_name = npc.get("name", "the dealer") if npc else "the house"

        if win:
            # On win: player gets their wager back plus equal winnings
            winnings = wager * 2  # Wager back + winnings
            self.state.gold += winnings
            message = f"You won {wager} gold from {npc_name}!"
            gold_change = wager  # Net gain is the wager amount
        else:
            # On loss: player loses their wager
            self.state.gold -= wager
            message = f"You lost {wager} gold to {npc_name}."
            gold_change = -wager  # Net loss is the wager amount
        return {
            "success": True,
            "message": message,
            "gold_change": gold_change,
            "won": win,
        }

    def earn_tip(self) -> Dict[str, Any]:
        """
        Handle earning a tip from a side job.

        Returns:
            Dict containing result and message
        """
        # Check cooldown (skip if last_job_time is 0, which is the initial state)
        time_since_last_job = self.clock.current_time - self.state.last_job_time
        if (
            self.state.last_job_time > 0
            and time_since_last_job < self.state.job_cooldown
        ):
            remaining = self.state.job_cooldown - time_since_last_job
            return {
                "success": False,
                "message": (
                    "You're too tired to work again so soon. "
                    f"Come back in {remaining:.1f} hours."
                ),
                "gold_change": 0,
            }

        # Calculate and award tip
        base = self.BASE_TIP
        bonus = random.randint(0, self.MAX_TIP_BONUS)
        total = base + bonus
        self.state.gold += total
        self.state.last_job_time = self.clock.current_time

        # Generate message
        if bonus > 0:
            msg = f"You earned {base} gold plus a {bonus} gold tip!"
            message = msg
        else:
            message = f"You earned {base} gold."

        return {
            "success": True,
            "message": message,
            "gold_change": total,
            "bonus": bonus,
        }
