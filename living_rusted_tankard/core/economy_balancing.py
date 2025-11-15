"""
Economy balancing system for The Living Rusted Tankard.

This module provides:
- Dynamic pricing based on player progression
- Economic balancing algorithms
- Progression-based rewards scaling
- Economic event management
"""

import logging
import math
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProgressionTier(Enum):
    NOVICE = "novice"  # 0-50 gold, new player
    APPRENTICE = "apprentice"  # 51-150 gold
    JOURNEYMAN = "journeyman"  # 151-400 gold
    EXPERT = "expert"  # 401-1000 gold
    MASTER = "master"  # 1000+ gold


@dataclass
class EconomicEvent:
    """Represents an economic event affecting prices."""

    id: str
    name: str
    description: str
    duration_hours: float
    price_modifiers: Dict[str, float]  # item_id -> multiplier
    probability: float = 0.1
    min_tier: ProgressionTier = ProgressionTier.NOVICE
    active_until: Optional[datetime] = None


@dataclass
class PlayerEconomicProfile:
    """Track player's economic activity and progression."""

    total_earned: int = 0
    total_spent: int = 0
    current_gold: int = 0
    transactions_count: int = 0
    largest_purchase: int = 0
    quest_rewards_earned: int = 0
    gambling_net: int = 0
    progression_tier: ProgressionTier = ProgressionTier.NOVICE
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class EconomyBalancer:
    """Manages economic balancing and dynamic pricing."""

    def __init__(self):
        self.base_prices = self._initialize_base_prices()
        self.active_events: List[EconomicEvent] = []
        self.player_profiles: Dict[str, PlayerEconomicProfile] = {}
        self.progression_multipliers = self._initialize_progression_multipliers()
        self.reward_scaling = self._initialize_reward_scaling()

        # Economic events
        self.economic_events = self._initialize_economic_events()

        logger.info("Economy balancer initialized")

    def _initialize_base_prices(self) -> Dict[str, int]:
        """Initialize base prices for items."""
        return {
            # Drinks
            "ale": 2,
            "beer": 3,
            "wine": 5,
            "whiskey": 8,
            "old_toms_surprise": 12,
            "mystery_brew": 15,
            # Food
            "bread": 1,
            "cheese": 2,
            "stew": 4,
            "meat_pie": 6,
            "feast": 15,
            # Supplies
            "torch": 1,
            "rope": 3,
            "lockpick": 5,
            "healing_potion": 25,
            "antidote": 20,
            "traveler_ration": 8,
            # Equipment
            "rusty_dagger": 10,
            "leather_armor": 30,
            "iron_sword": 75,
            "steel_armor": 150,
            "magic_amulet": 200,
            # Services
            "room_basic": 5,
            "room_comfortable": 10,
            "room_luxury": 20,
            "storage_chest": 15,
            "information": 5,
        }

    def _initialize_progression_multipliers(self) -> Dict[ProgressionTier, Dict[str, float]]:
        """Initialize price multipliers based on player progression."""
        return {
            ProgressionTier.NOVICE: {
                "discount": 0.9,  # 10% discount for new players
                "quest_reward": 1.0,
                "work_payment": 1.0,
                "gambling_payout": 1.0,
            },
            ProgressionTier.APPRENTICE: {
                "discount": 1.0,  # Normal prices
                "quest_reward": 1.2,
                "work_payment": 1.1,
                "gambling_payout": 1.0,
            },
            ProgressionTier.JOURNEYMAN: {
                "discount": 1.1,  # 10% price increase
                "quest_reward": 1.5,
                "work_payment": 1.3,
                "gambling_payout": 1.1,
            },
            ProgressionTier.EXPERT: {
                "discount": 1.2,  # 20% price increase
                "quest_reward": 2.0,
                "work_payment": 1.5,
                "gambling_payout": 1.2,
            },
            ProgressionTier.MASTER: {
                "discount": 1.5,  # 50% price increase (luxury prices)
                "quest_reward": 3.0,
                "work_payment": 2.0,
                "gambling_payout": 1.5,
            },
        }

    def _initialize_reward_scaling(self) -> Dict[str, Dict[ProgressionTier, float]]:
        """Initialize reward scaling by activity type."""
        return {
            "quest_completion": {
                ProgressionTier.NOVICE: 1.0,
                ProgressionTier.APPRENTICE: 1.3,
                ProgressionTier.JOURNEYMAN: 1.8,
                ProgressionTier.EXPERT: 2.5,
                ProgressionTier.MASTER: 4.0,
            },
            "work_payment": {
                ProgressionTier.NOVICE: 1.0,
                ProgressionTier.APPRENTICE: 1.2,
                ProgressionTier.JOURNEYMAN: 1.5,
                ProgressionTier.EXPERT: 2.0,
                ProgressionTier.MASTER: 3.0,
            },
            "gambling_win": {
                ProgressionTier.NOVICE: 1.0,
                ProgressionTier.APPRENTICE: 1.1,
                ProgressionTier.JOURNEYMAN: 1.2,
                ProgressionTier.EXPERT: 1.4,
                ProgressionTier.MASTER: 1.6,
            },
        }

    def _initialize_economic_events(self) -> List[EconomicEvent]:
        """Initialize possible economic events."""
        return [
            EconomicEvent(
                id="harvest_festival",
                name="Harvest Festival",
                description="Local harvest brings abundance, food prices drop",
                duration_hours=24.0,
                price_modifiers={"bread": 0.5, "cheese": 0.7, "stew": 0.6},
                probability=0.15,
                min_tier=ProgressionTier.NOVICE,
            ),
            EconomicEvent(
                id="merchant_caravan",
                name="Merchant Caravan Arrives",
                description="Traveling merchants bring exotic goods at premium prices",
                duration_hours=12.0,
                price_modifiers={"magic_amulet": 0.8, "traveler_ration": 1.3},
                probability=0.12,
                min_tier=ProgressionTier.APPRENTICE,
            ),
            EconomicEvent(
                id="ale_shortage",
                name="Ale Shortage",
                description="Supply problems drive up drink prices",
                duration_hours=18.0,
                price_modifiers={"ale": 1.5, "beer": 1.4, "wine": 1.2},
                probability=0.08,
                min_tier=ProgressionTier.NOVICE,
            ),
            EconomicEvent(
                id="blacksmith_special",
                name="Blacksmith's Special Offer",
                description="Local blacksmith offers discounted equipment",
                duration_hours=8.0,
                price_modifiers={"rusty_dagger": 0.7, "iron_sword": 0.8, "steel_armor": 0.85},
                probability=0.10,
                min_tier=ProgressionTier.JOURNEYMAN,
            ),
            EconomicEvent(
                id="tax_collectors",
                name="Tax Collectors Visit",
                description="Heavy taxation increases all prices temporarily",
                duration_hours=6.0,
                price_modifiers={item: 1.25 for item in ["room_basic", "room_comfortable", "room_luxury"]},
                probability=0.05,
                min_tier=ProgressionTier.EXPERT,
            ),
        ]

    def get_player_profile(self, player_id: str) -> PlayerEconomicProfile:
        """Get or create player economic profile."""
        if player_id not in self.player_profiles:
            self.player_profiles[player_id] = PlayerEconomicProfile()
        return self.player_profiles[player_id]

    def update_player_profile(self, player_id: str, gold_change: int, transaction_type: str, amount: int = 0):
        """Update player economic profile."""
        profile = self.get_player_profile(player_id)

        if gold_change > 0:
            profile.total_earned += gold_change
            if transaction_type == "quest":
                profile.quest_rewards_earned += gold_change
            elif transaction_type == "gambling":
                profile.gambling_net += gold_change
        elif gold_change < 0:
            profile.total_spent += abs(gold_change)
            profile.largest_purchase = max(profile.largest_purchase, abs(gold_change))

        profile.current_gold += gold_change
        profile.transactions_count += 1
        profile.last_updated = datetime.now()

        # Update progression tier
        old_tier = profile.progression_tier
        profile.progression_tier = self._calculate_progression_tier(profile)

        # Log tier progression
        if profile.progression_tier != old_tier:
            logger.info(f"Player {player_id} progressed from {old_tier.value} to {profile.progression_tier.value}")

    def _calculate_progression_tier(self, profile: PlayerEconomicProfile) -> ProgressionTier:
        """Calculate player progression tier based on economic activity."""
        # Primary factor: current gold
        gold = profile.current_gold

        # Secondary factors: total earned and quest completion
        total_activity = profile.total_earned + profile.quest_rewards_earned

        if gold >= 1000 or total_activity >= 2000:
            return ProgressionTier.MASTER
        elif gold >= 400 or total_activity >= 800:
            return ProgressionTier.EXPERT
        elif gold >= 150 or total_activity >= 300:
            return ProgressionTier.JOURNEYMAN
        elif gold >= 50 or total_activity >= 100:
            return ProgressionTier.APPRENTICE
        else:
            return ProgressionTier.NOVICE

    def get_item_price(self, item_id: str, player_id: str, quantity: int = 1) -> int:
        """Get dynamic price for an item based on player progression and events."""
        base_price = self.base_prices.get(item_id, 1)
        profile = self.get_player_profile(player_id)

        # Apply progression multiplier
        tier_multipliers = self.progression_multipliers[profile.progression_tier]
        price_multiplier = tier_multipliers.get("discount", 1.0)

        # Apply active economic events
        for event in self.active_events:
            if item_id in event.price_modifiers:
                price_multiplier *= event.price_modifiers[item_id]

        # Apply quantity discount for bulk purchases
        if quantity > 1:
            bulk_discount = 1.0 - min(0.15, (quantity - 1) * 0.02)  # Up to 15% discount
            price_multiplier *= bulk_discount

        final_price = max(1, int(base_price * price_multiplier))
        return final_price * quantity

    def get_reward_amount(self, base_amount: int, reward_type: str, player_id: str) -> int:
        """Calculate scaled reward amount based on player progression."""
        profile = self.get_player_profile(player_id)

        if reward_type in self.reward_scaling:
            multiplier = self.reward_scaling[reward_type][profile.progression_tier]
        else:
            # Default scaling
            tier_multipliers = self.progression_multipliers[profile.progression_tier]
            multiplier = tier_multipliers.get("quest_reward", 1.0)

        return max(1, int(base_amount * multiplier))

    def update_economic_events(self, current_time: datetime, player_tier: ProgressionTier) -> Optional[Dict[str, Any]]:
        """Update active economic events and potentially trigger new ones."""
        # Remove expired events
        self.active_events = [
            event for event in self.active_events if event.active_until and event.active_until > current_time
        ]

        # Chance to trigger new event
        if random.random() < 0.05:  # 5% chance per update
            available_events = [
                event
                for event in self.economic_events
                if event.min_tier.value <= player_tier.value and event.id not in [ae.id for ae in self.active_events]
            ]

            if available_events:
                event_template = random.choice(available_events)
                if random.random() < event_template.probability:
                    # Trigger the event
                    new_event = EconomicEvent(
                        id=event_template.id,
                        name=event_template.name,
                        description=event_template.description,
                        duration_hours=event_template.duration_hours,
                        price_modifiers=event_template.price_modifiers.copy(),
                        active_until=current_time + timedelta(hours=event_template.duration_hours),
                    )

                    self.active_events.append(new_event)

                    return {
                        "event_started": True,
                        "event": {
                            "name": new_event.name,
                            "description": new_event.description,
                            "duration_hours": new_event.duration_hours,
                        },
                    }

        return None

    def get_economic_status(self, player_id: str) -> Dict[str, Any]:
        """Get current economic status for a player."""
        profile = self.get_player_profile(player_id)

        return {
            "progression_tier": profile.progression_tier.value,
            "current_gold": profile.current_gold,
            "total_earned": profile.total_earned,
            "total_spent": profile.total_spent,
            "net_worth": profile.total_earned - profile.total_spent,
            "transaction_count": profile.transactions_count,
            "active_events": [
                {
                    "name": event.name,
                    "description": event.description,
                    "time_remaining": (
                        (event.active_until - datetime.now()).total_seconds() / 3600 if event.active_until else 0
                    ),
                }
                for event in self.active_events
            ],
            "price_modifiers": {
                "tier_discount": self.progression_multipliers[profile.progression_tier]["discount"],
                "quest_reward_multiplier": self.progression_multipliers[profile.progression_tier]["quest_reward"],
                "work_payment_multiplier": self.progression_multipliers[profile.progression_tier]["work_payment"],
            },
        }

    def get_pricing_preview(self, player_id: str, items: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get pricing preview for multiple items."""
        preview = {}

        for item_id in items:
            base_price = self.base_prices.get(item_id, 1)
            current_price = self.get_item_price(item_id, player_id)

            price_factors = []

            # Check progression tier impact
            profile = self.get_player_profile(player_id)
            tier_multiplier = self.progression_multipliers[profile.progression_tier]["discount"]
            if tier_multiplier != 1.0:
                price_factors.append(f"Tier ({profile.progression_tier.value}): {tier_multiplier:.1%}")

            # Check event impacts
            for event in self.active_events:
                if item_id in event.price_modifiers:
                    price_factors.append(f"{event.name}: {event.price_modifiers[item_id]:.1%}")

            preview[item_id] = {
                "base_price": base_price,
                "current_price": current_price,
                "price_change": current_price - base_price,
                "price_change_percent": ((current_price - base_price) / base_price) * 100,
                "factors": price_factors,
            }

        return preview

    def simulate_progression(self, starting_gold: int, activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate economic progression for balancing purposes."""
        simulation_profile = PlayerEconomicProfile(current_gold=starting_gold)

        progression_log = []

        for activity in activities:
            activity_type = activity["type"]
            amount = activity["amount"]

            if activity_type == "earn":
                simulation_profile.total_earned += amount
                simulation_profile.current_gold += amount
            elif activity_type == "spend":
                simulation_profile.total_spent += amount
                simulation_profile.current_gold -= amount
            elif activity_type == "quest":
                reward = self.get_reward_amount(amount, "quest_completion", "simulation")
                simulation_profile.quest_rewards_earned += reward
                simulation_profile.current_gold += reward

            old_tier = simulation_profile.progression_tier
            simulation_profile.progression_tier = self._calculate_progression_tier(simulation_profile)

            if simulation_profile.progression_tier != old_tier:
                progression_log.append(
                    {
                        "activity": activity,
                        "tier_change": f"{old_tier.value} -> {simulation_profile.progression_tier.value}",
                        "gold": simulation_profile.current_gold,
                    }
                )

        return {
            "final_profile": {
                "tier": simulation_profile.progression_tier.value,
                "gold": simulation_profile.current_gold,
                "total_earned": simulation_profile.total_earned,
                "total_spent": simulation_profile.total_spent,
            },
            "progression_log": progression_log,
        }


# Global economy balancer instance
economy_balancer = EconomyBalancer()


# Utility functions for easy integration
def get_balanced_price(item_id: str, player_id: str, quantity: int = 1) -> int:
    """Get balanced price for an item."""
    return economy_balancer.get_item_price(item_id, player_id, quantity)


def get_scaled_reward(base_amount: int, reward_type: str, player_id: str) -> int:
    """Get scaled reward amount."""
    return economy_balancer.get_reward_amount(base_amount, reward_type, player_id)


def update_player_economy(player_id: str, gold_change: int, transaction_type: str, amount: int = 0):
    """Update player economic profile."""
    economy_balancer.update_player_profile(player_id, gold_change, transaction_type, amount)


def get_economic_status(player_id: str) -> Dict[str, Any]:
    """Get player economic status."""
    return economy_balancer.get_economic_status(player_id)


def trigger_economic_update(player_id: str) -> Optional[Dict[str, Any]]:
    """Trigger economic event update."""
    profile = economy_balancer.get_player_profile(player_id)
    return economy_balancer.update_economic_events(datetime.now(), profile.progression_tier)
