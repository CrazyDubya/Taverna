from typing import Dict, Optional, List, Any
import random
from pydantic import BaseModel, Field, validator
from .items import Item, TAVERN_ITEMS


class TransactionResult(BaseModel):
    """Result of an economic transaction."""

    success: bool
    amount: int
    message: str
    new_balance: int
    items_gained: List[Item] = Field(default_factory=list)


class Economy(BaseModel):
    """Handles all economic activities in the game."""

    base_gold: int = 100  # Can be part of initial config, but also saveable if it can change
    gambling_odds: float = 0.4  # Base chance to win a gamble, saveable

    # State to be serialized
    current_event_id: Optional[str] = None
    event_duration: float = 0.0

    class Config:
        # Allow setting attributes that aren't fields
        extra = "allow"

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._side_jobs = self._initialize_side_jobs()
        self._economic_events = self._initialize_economic_events()
        self._reconstruct_current_event()

    @validator("current_event_id", always=True)
    def _reconstruct_current_event_validator(cls, v, values):
        # This validator runs after the object is created in v1
        return v

    def _reconstruct_current_event(self):
        if self.current_event_id and self.current_event_id in self._economic_events:
            self._current_event_data = self._economic_events[self.current_event_id]
        else:
            self._current_event_data = None

    # Make side_jobs and economic_events accessible if needed by other parts of the code
    # These are read-only properties for the definitions.
    @property
    def side_jobs(self) -> Dict[str, dict]:
        return self._side_jobs

    @property
    def economic_events(self) -> Dict[str, dict]:
        return self._economic_events

    @property
    def current_event(self) -> Optional[Dict[str, Any]]:  # Keep the original property for easy access
        return self._current_event_data

    def _initialize_side_jobs(self) -> Dict[str, dict]:
        """Initialize all available side jobs."""
        # These definitions are static
        return {
            "clean_tables": {
                "name": "Clean Tables",
                "base_reward": 5,
                "tiredness_cost": 0.2,
                "description": "Wipe down tables and clean up after patrons.",
                "possible_items": ["bread"],
            },
            "wash_dishes": {
                "name": "Wash Dishes",
                "base_reward": 8,
                "tiredness_cost": 0.3,
                "description": "Spend time washing dishes in the kitchen.",
                "possible_items": ["bread", "stew"],
            },
            "tend_bar": {
                "name": "Tend Bar",
                "base_reward": 12,
                "tiredness_cost": 0.4,
                "description": "Help serve drinks to customers.",
                "required_energy": 0.5,
                "possible_items": ["ale"],
            },
            "entertain": {
                "name": "Entertain Patrons",
                "base_reward": 15,
                "tiredness_cost": 0.5,
                "description": "Tell stories or play music for the crowd.",
                "required_energy": 0.7,
                "possible_items": ["ale", "stew"],
            },
            "bouncer": {
                "name": "Bouncer Duty",
                "base_reward": 25,
                "tiredness_cost": 0.6,
                "description": "Keep the peace and handle rowdy patrons.",
                "required_energy": 0.8,
                "risk": 0.3,  # Chance of getting injured
                "possible_items": ["ale"],
            },
            "run_errands": {
                "name": "Run Errands",
                "base_reward": 18,
                "tiredness_cost": 0.4,
                "description": "Deliver messages or goods around town.",
                "required_energy": 0.6,
                "possible_items": ["bread", "stew"],
            },
            "collect_debts": {
                "name": "Collect Debts",
                "base_reward": 30,
                "tiredness_cost": 0.7,
                "description": "Help collect outstanding debts from patrons.",
                "required_energy": 0.8,
                "risk": 0.4,
                "possible_items": ["ale", "stew"],
            },
        }

    def _initialize_economic_events(self) -> Dict[str, dict]:
        """Initialize possible economic events."""
        return {
            "busy_night": {
                "name": "Busy Night",
                "description": "The tavern is packed tonight! Higher tips and more customers.",
                "modifiers": {
                    "gambling_odds": 0.1,  # Better gambling odds
                    "job_rewards": 1.5,  # Higher tips
                    "duration": 6,  # Hours the event lasts
                },
            },
            "slow_day": {
                "name": "Slow Day",
                "description": "Business is slow today. Fewer customers and lower tips.",
                "modifiers": {"gambling_odds": -0.1, "job_rewards": 0.7, "duration": 8},
            },
            "merchant_visit": {
                "name": "Merchant Visit",
                "description": "A traveling merchant is visiting, offering rare items for sale.",
                "modifiers": {"item_prices": 0.8, "duration": 12},  # Discount on items
            },
        }

    def update_economic_events(
        self, hours_passed: float = 1.0
    ) -> Optional[Dict[str, Any]]:  # hours_passed can be float
        """Update economic events and potentially trigger new ones."""
        if self._current_event_data:
            self.event_duration -= hours_passed
            if self.event_duration <= 0:
                event_name = self._current_event_data.get("name", "Unknown")
                self._current_event_data = None
                self.current_event_id = None
                self.event_duration = 0
                return {"message": f"The {event_name} event has ended."}
        elif random.random() < 0.1:  # 10% chance to trigger an event
            if not self._economic_events:  # Ensure definitions are loaded
                return None
            self.current_event_id = random.choice(list(self._economic_events.keys()))
            self._current_event_data = self._economic_events[self.current_event_id]
            self.event_duration = self._current_event_data["modifiers"].get("duration", 6)
            return {"message": f"Event: {self._current_event_data['name']} - {self._current_event_data['description']}"}
        return None

    def get_current_event_modifiers(self) -> Dict[str, float]:
        """Get modifiers from the current economic event."""
        if not self._current_event_data:
            return {}
        return self._current_event_data.get("modifiers", {})

    def can_afford(self, player_gold: int, amount: int) -> bool:
        """Check if player can afford an amount."""
        return player_gold >= amount

    def add_gold(self, player_gold: int, amount: int, items: Optional[List[Item]] = None) -> TransactionResult:
        """Add gold and/or items to player's inventory."""
        if amount < 0:
            return TransactionResult(
                success=False, amount=0, message="Cannot add negative gold.", new_balance=player_gold, items_gained=[]
            )

        new_balance = player_gold + amount
        items_gained = items or []

        item_messages = []
        if items_gained:
            item_names = ", ".join(item.name for item in items_gained)
            item_messages.append(f"Received: {item_names}")

        message = f"Gained {amount} gold."
        if item_messages:
            message = f"{message} {' '.join(item_messages)}"

        return TransactionResult(
            success=True, amount=amount, message=message, new_balance=new_balance, items_gained=items_gained
        )

    def spend_gold(self, player_gold: int, amount: int) -> TransactionResult:
        """Deduct gold from player's total if they can afford it."""
        if amount < 0:
            return TransactionResult(
                success=False, amount=0, message="Cannot spend negative gold.", new_balance=player_gold, items_gained=[]
            )

        if not self.can_afford(player_gold, amount):
            return TransactionResult(
                success=False, amount=0, message="Not enough gold.", new_balance=player_gold, items_gained=[]
            )

        new_balance = player_gold - amount
        return TransactionResult(
            success=True, amount=amount, message=f"Spent {amount} gold.", new_balance=new_balance, items_gained=[]
        )

    def gamble(self, player_gold: int, amount: int, npc_skill: float = 0.0) -> TransactionResult:
        """Handle gambling mechanics."""
        if amount <= 0:
            return TransactionResult(
                success=False,
                amount=0,
                message="Must gamble a positive amount.",
                new_balance=player_gold,
                items_gained=[],
            )

        if not self.can_afford(player_gold, amount):
            return TransactionResult(
                success=False, amount=0, message="Not enough gold to gamble.", new_balance=player_gold, items_gained=[]
            )

        # Adjust odds based on NPC skill and current event
        event_modifiers = self.get_current_event_modifiers()
        event_bonus = event_modifiers.get("gambling_odds", 0.0)
        adjusted_odds = max(0.1, min(0.9, self.gambling_odds - npc_skill * 0.1 + event_bonus))

        if random.random() < adjusted_odds:
            # Win double or nothing (net gain is just the amount since you get back your bet plus winnings)
            return TransactionResult(
                success=True,
                amount=amount,
                message=f"You won {amount * 2} gold!",
                new_balance=player_gold + amount,
                items_gained=[],
            )
        else:
            return TransactionResult(
                success=True,
                amount=-amount,
                message=f"Lost {amount} gold.",
                new_balance=player_gold - amount,
                items_gained=[],
            )

    def get_available_jobs(self, player_energy: float = 1.0) -> List[dict]:
        """Get list of jobs player can perform based on their energy."""
        # Use the property self.side_jobs to access _side_jobs
        return [
            job_data
            for job_id, job_data in self.side_jobs.items()
            if job_data.get("required_energy", 0) <= player_energy
        ]

    def _get_random_item_reward(self, job_id: str) -> Optional[Item]:
        """Get a random item reward for completing a job."""
        job_details = self.side_jobs.get(job_id, {})  # Use property
        possible_items_list = job_details.get("possible_items", [])

        if not possible_items_list or random.random() > 0.3:  # 30% chance for item drop
            return None

        item_id_reward = random.choice(possible_items_list)  # Renamed variable
        return TAVERN_ITEMS.get(item_id_reward)

    def perform_job(self, job_id: str, player_energy: float) -> dict:
        """Perform a side job and return results."""
        if job_id not in self.side_jobs:  # Use property
            return {"success": False, "message": "No such job exists.", "reward": 0, "tiredness": 0, "items": []}

        job_details = self.side_jobs[job_id]  # Use property, renamed variable

        if job_details.get("required_energy", 0) > player_energy:
            return {
                "success": False,
                "message": "Not enough energy for this job.",
                "reward": 0,
                "tiredness": 0,
                "items": [],
            }

        # Calculate reward with some randomness and event modifiers
        current_event_modifiers = self.get_current_event_modifiers()  # Renamed variable
        reward_multiplier = current_event_modifiers.get("job_rewards", 1.0)
        base_reward = job_details["base_reward"]

        # More experienced players might get better rewards
        reward = max(1, int(base_reward * random.uniform(0.8, 1.2) * reward_multiplier))
        tiredness = job_details["tiredness_cost"]

        # Get potential item reward
        item_reward_obj = self._get_random_item_reward(job_id)  # Renamed variable
        items_gained = [item_reward_obj] if item_reward_obj else []

        # Handle job-specific outcomes (e.g., risk of injury)
        if job_id == "bouncer" and random.random() < job_details.get("risk", 0):
            reward = max(1, reward // 2)
            tiredness *= 1.5
            message = f"Got injured while working as a bouncer! Earned {reward} gold but feel exhausted."
        else:
            message = f"Earned {reward} gold from {job_details['name'].lower()}."
            if item_reward_obj:
                message += f" Also received: {item_reward_obj.name}!"

        return {"success": True, "message": message, "reward": reward, "tiredness": tiredness, "items": items_gained}

    def get_item_price(
        self, item_id: str, game_state: Optional[Any] = None
    ) -> Optional[int]:  # Keep Any for game_state to avoid circular import if type hint is GameState
        """Get the current price of an item, considering any active events and temporary merchant stock.

        Args:
            item_id: The ID of the item.
            game_state: Optional GameState instance to check for travelling merchant items.
        """
        item_def: Optional[Item] = TAVERN_ITEMS.get(item_id)  # All item definitions should be in TAVERN_ITEMS

        # Check availability if game_state and merchant are relevant
        # Standard availability check - might be more complex in a full system
        _is_available_normally = item_id in TAVERN_ITEMS  # noqa: F841 - reserved for future use

        if game_state and game_state.travelling_merchant_active:
            if item_id in game_state.travelling_merchant_temporary_items:
                pass

        if not item_def:  # If the item definition itself doesn't exist
            return None

        # If the item is neither normally available (e.g. if TAVERN_ITEMS were for a specific shop)
        # NOR available via merchant, then it can't be priced/bought.
        # However, TAVERN_ITEMS is global, so this check is more about if it's *currently offered*.
        # For now, if it has a definition in TAVERN_ITEMS, and is either normally sold or via merchant, it's priceable.
        # The main check for "is it sold right now" should be in _handle_buy.
        # get_item_price just needs to find its base definition if it *could* be sold.

        event_modifiers = self.get_current_event_modifiers()
        price_multiplier = event_modifiers.get("item_prices", 1.0)

        return max(1, int(item_def.base_price * price_multiplier))
