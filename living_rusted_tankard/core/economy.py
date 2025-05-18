from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List, Union, Any
import random
from enum import Enum
from pydantic import BaseModel, Field, validator
from .items import Item, TAVERN_ITEMS


class TransactionResult(BaseModel):
    """Result of an economic transaction."""
    success: bool
    amount: int
    message: str
    new_balance: int
    items_gained: List[Item] = Field(default_factory=list)


class Economy:
    """Handles all economic activities in the game."""
    
    def __init__(self, base_gold: int = 100):
        """Initialize the economy system."""
        self.base_gold = base_gold
        self.gambling_odds = 0.4  # Base chance to win a gamble
        self.side_jobs = self._initialize_side_jobs()
        self.economic_events = self._initialize_economic_events()
        self.current_event: Optional[Dict[str, Any]] = None
        self.event_duration = 0
        
    def _initialize_side_jobs(self) -> Dict[str, dict]:
        """Initialize all available side jobs."""
        return {
            "clean_tables": {
                "name": "Clean Tables",
                "base_reward": 5,
                "tiredness_cost": 0.2,
                "description": "Wipe down tables and clean up after patrons.",
                "possible_items": ["bread"]
            },
            "wash_dishes": {
                "name": "Wash Dishes",
                "base_reward": 8,
                "tiredness_cost": 0.3,
                "description": "Spend time washing dishes in the kitchen.",
                "possible_items": ["bread", "stew"]
            },
            "tend_bar": {
                "name": "Tend Bar",
                "base_reward": 12,
                "tiredness_cost": 0.4,
                "description": "Help serve drinks to customers.",
                "required_energy": 0.5,
                "possible_items": ["ale"]
            },
            "entertain": {
                "name": "Entertain Patrons",
                "base_reward": 15,
                "tiredness_cost": 0.5,
                "description": "Tell stories or play music for the crowd.",
                "required_energy": 0.7,
                "possible_items": ["ale", "stew"]
            },
            "bouncer": {
                "name": "Bouncer Duty",
                "base_reward": 25,
                "tiredness_cost": 0.6,
                "description": "Keep the peace and handle rowdy patrons.",
                "required_energy": 0.8,
                "risk": 0.3,  # Chance of getting injured
                "possible_items": ["ale"]
            },
            "run_errands": {
                "name": "Run Errands",
                "base_reward": 18,
                "tiredness_cost": 0.4,
                "description": "Deliver messages or goods around town.",
                "required_energy": 0.6,
                "possible_items": ["bread", "stew"]
            },
            "collect_debts": {
                "name": "Collect Debts",
                "base_reward": 30,
                "tiredness_cost": 0.7,
                "description": "Help collect outstanding debts from patrons.",
                "required_energy": 0.8,
                "risk": 0.4,
                "possible_items": ["ale", "stew"]
            }
        }
    
    def _initialize_economic_events(self) -> Dict[str, dict]:
        """Initialize possible economic events."""
        return {
            "busy_night": {
                "name": "Busy Night",
                "description": "The tavern is packed tonight! Higher tips and more customers.",
                "modifiers": {
                    "gambling_odds": 0.1,  # Better gambling odds
                    "job_rewards": 1.5,     # Higher tips
                    "duration": 6            # Hours the event lasts
                }
            },
            "slow_day": {
                "name": "Slow Day",
                "description": "Business is slow today. Fewer customers and lower tips.",
                "modifiers": {
                    "gambling_odds": -0.1,
                    "job_rewards": 0.7,
                    "duration": 8
                }
            },
            "merchant_visit": {
                "name": "Merchant Visit",
                "description": "A traveling merchant is visiting, offering rare items for sale.",
                "modifiers": {
                    "item_prices": 0.8,  # Discount on items
                    "duration": 12
                }
            }
        }
    
    def update_economic_events(self, hours_passed: int = 1) -> Optional[Dict[str, Any]]:
        """Update economic events and potentially trigger new ones."""
        if self.current_event:
            self.event_duration -= hours_passed
            if self.event_duration <= 0:
                self.current_event = None
                return {"message": f"The {self.current_event['name']} event has ended."}
        elif random.random() < 0.1:  # 10% chance to trigger an event
            event_id = random.choice(list(self.economic_events.keys()))
            self.current_event = self.economic_events[event_id]
            self.event_duration = self.current_event["modifiers"].get("duration", 6)
            return {
                "message": f"Event: {self.current_event['name']} - {self.current_event['description']}"
            }
        return None
    
    def get_current_event_modifiers(self) -> Dict[str, float]:
        """Get modifiers from the current economic event."""
        if not self.current_event:
            return {}
        return self.current_event["modifiers"]
    
    def can_afford(self, player_gold: int, amount: int) -> bool:
        """Check if player can afford an amount."""
        return player_gold >= amount
    
    def add_gold(self, player_gold: int, amount: int, items: Optional[List[Item]] = None) -> TransactionResult:
        """Add gold and/or items to player's inventory."""
        if amount < 0:
            return TransactionResult(
                success=False,
                amount=0,
                message="Cannot add negative gold.",
                new_balance=player_gold,
                items_gained=[]
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
            success=True,
            amount=amount,
            message=message,
            new_balance=new_balance,
            items_gained=items_gained
        )
    
    def spend_gold(self, player_gold: int, amount: int) -> TransactionResult:
        """Deduct gold from player's total if they can afford it."""
        if amount < 0:
            return TransactionResult(
                success=False,
                amount=0,
                message="Cannot spend negative gold.",
                new_balance=player_gold,
                items_gained=[]
            )
            
        if not self.can_afford(player_gold, amount):
            return TransactionResult(
                success=False,
                amount=0,
                message="Not enough gold.",
                new_balance=player_gold,
                items_gained=[]
            )
            
        new_balance = player_gold - amount
        return TransactionResult(
            success=True,
            amount=amount,
            message=f"Spent {amount} gold.",
            new_balance=new_balance,
            items_gained=[]
        )
    
    def gamble(self, player_gold: int, amount: int, npc_skill: float = 0.0) -> TransactionResult:
        """Handle gambling mechanics."""
        if amount <= 0:
            return TransactionResult(
                success=False,
                amount=0,
                message="Must gamble a positive amount.",
                new_balance=player_gold,
                items_gained=[]
            )
            
        if not self.can_afford(player_gold, amount):
            return TransactionResult(
                success=False,
                amount=0,
                message="Not enough gold to gamble.",
                new_balance=player_gold,
                items_gained=[]
            )
        
        # Adjust odds based on NPC skill and current event
        event_modifiers = self.get_current_event_modifiers()
        event_bonus = event_modifiers.get("gambling_odds", 0.0)
        adjusted_odds = max(0.1, min(0.9, self.gambling_odds - npc_skill * 0.1 + event_bonus))
        
        if random.random() < adjusted_odds:
            # Win double or nothing
            winnings = amount * 2
            return self.add_gold(
                player_gold,
                winnings,
                message=f"You won {winnings} gold!"
            )
        else:
            return TransactionResult(
                success=True,
                amount=-amount,
                message=f"Lost {amount} gold.",
                new_balance=player_gold - amount,
                items_gained=[]
            )
    
    def get_available_jobs(self, player_energy: float = 1.0) -> List[dict]:
        """Get list of jobs player can perform based on their energy."""
        return [
            job for job_id, job in self.side_jobs.items()
            if job.get("required_energy", 0) <= player_energy
        ]
    
    def _get_random_item_reward(self, job_id: str) -> Optional[Item]:
        """Get a random item reward for completing a job."""
        job = self.side_jobs.get(job_id, {})
        possible_items = job.get("possible_items", [])
        
        if not possible_items or random.random() > 0.3:  # 30% chance for item drop
            return None
            
        item_id = random.choice(possible_items)
        return TAVERN_ITEMS.get(item_id)
    
    def perform_job(self, job_id: str, player_energy: float) -> dict:
        """Perform a side job and return results."""
        if job_id not in self.side_jobs:
            return {
                "success": False,
                "message": "No such job exists.",
                "reward": 0,
                "tiredness": 0,
                "items": []
            }
            
        job = self.side_jobs[job_id]
        
        if job.get("required_energy", 0) > player_energy:
            return {
                "success": False,
                "message": "Not enough energy for this job.",
                "reward": 0,
                "tiredness": 0,
                "items": []
            }
        
        # Calculate reward with some randomness and event modifiers
        event_modifiers = self.get_current_event_modifiers()
        reward_multiplier = event_modifiers.get("job_rewards", 1.0)
        base_reward = job["base_reward"]
        
        # More experienced players might get better rewards
        reward = max(1, int(base_reward * random.uniform(0.8, 1.2) * reward_multiplier))
        tiredness = job["tiredness_cost"]
        
        # Get potential item reward
        item_reward = self._get_random_item_reward(job_id)
        items_gained = [item_reward] if item_reward else []
        
        # Handle job-specific outcomes (e.g., risk of injury)
        if job_id == "bouncer" and random.random() < job.get("risk", 0):
            reward = max(1, reward // 2)
            tiredness *= 1.5
            message = f"Got injured while working as a bouncer! Earned {reward} gold but feel exhausted."
        else:
            message = f"Earned {reward} gold from {job['name'].lower()}."
            if item_reward:
                message += f" Also received: {item_reward.name}!"
        
        return {
            "success": True,
            "message": message,
            "reward": reward,
            "tiredness": tiredness,
            "items": items_gained
        }
    
    def get_item_price(self, item_id: str) -> Optional[int]:
        """Get the current price of an item, considering any active events."""
        item = TAVERN_ITEMS.get(item_id)
        if not item:
            return None
            
        event_modifiers = self.get_current_event_modifiers()
        price_multiplier = event_modifiers.get("item_prices", 1.0)
        
        return max(1, int(item.base_price * price_multiplier))
