from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, Set
from pydantic import BaseModel, Field as PydanticField
import random

from .items import Item, Inventory, InventoryItem  # Added InventoryItem


class ActiveEffect(BaseModel):
    effect_id: str
    stat_affected: str
    modifier: Any
    expiry_time: float


class PlayerState(BaseModel):
    player_id: str = "default_player"
    name: str = "Player"
    gold: int = 40
    has_room: bool = False
    room_id: Optional[str] = None
    tiredness: float = 0.0
    energy: float = 1.0

    resolve: int = PydanticField(
        default=5, description="Player's mental fortitude or willpower."
    )
    max_stamina: int = PydanticField(default=100, description="Maximum stamina.")
    current_stamina: int = PydanticField(
        default=100, description="Current stamina, can be temporarily boosted."
    )

    rest_immune: bool = False
    _no_sleep_quest_unlocked: bool = False
    _no_sleep_quest_locked: bool = False

    inventory: Inventory = PydanticField(default_factory=Inventory)
    # Storage inventory will use the same Inventory model structure
    storage_inventory: Inventory = PydanticField(default_factory=Inventory)

    flags: Dict[str, Any] = PydanticField(default_factory=dict)
    reputation: Dict[str, int] = PydanticField(default_factory=dict)

    active_bounty_ids: Set[str] = PydanticField(default_factory=set)
    completed_bounty_ids: Set[str] = PydanticField(default_factory=set)

    last_ate: float = 0.0
    last_drank: float = 0.0

    active_effects: List[ActiveEffect] = PydanticField(default_factory=list)

    @property
    def id(self) -> str:
        return self.player_id

    @property
    def no_sleep_quest_unlocked(self) -> bool:
        return self._no_sleep_quest_unlocked and not self._no_sleep_quest_locked

    @no_sleep_quest_unlocked.setter
    def no_sleep_quest_unlocked(self, value: bool) -> None:
        if not self._no_sleep_quest_locked:
            self._no_sleep_quest_unlocked = bool(value)

    def lock_no_sleep_quest(self) -> None:
        self._no_sleep_quest_locked = True
        self._no_sleep_quest_unlocked = False

    class Config:
        arbitrary_types_allowed = True

    def can_afford(self, amount: int) -> bool:
        if not isinstance(amount, (int, float)) or amount <= 0:
            return False
        return self.gold >= amount

    def add_gold(self, amount: int) -> tuple[bool, str]:
        if not isinstance(amount, (int, float)) or amount <= 0:
            return False, "Amount must be a positive number"
        self.gold += amount
        return True, f"Added {amount} gold. New total: {self.gold}"

    def spend_gold(self, amount: int) -> tuple[bool, str]:
        if not isinstance(amount, (int, float)) or amount <= 0:
            return False, "Amount must be a positive number"
        if self.gold < amount:
            return False, f"Not enough gold. Needed: {amount}, Have: {self.gold}"
        self.gold -= amount
        return True, f"Spent {amount} gold. Remaining: {self.gold}"

    def update_tiredness(self, amount: float, clock: Optional[Any] = None) -> None:
        self.tiredness = max(0.0, min(1.0, self.tiredness + amount))

    def ask_about_sleep(self) -> str:
        if self.no_sleep_quest_unlocked:
            return "You've already unlocked the no-sleep quest!"
        if self.tiredness >= 0.8:
            self.no_sleep_quest_unlocked = True
            return (
                "You feel an unusual energy despite your exhaustion. "
                "You've unlocked the No-Sleep Challenge quest!"
            )
        return "You're feeling a bit tired, but nothing unusual."

    def _update_hunger_thirst(self, game_time: float) -> None:
        hours_since_ate = game_time - self.last_ate
        hours_since_drank = game_time - self.last_drank
        if hours_since_ate > 6:
            self.energy = max(0.0, self.energy - 0.05)
        if hours_since_drank > 4:
            self.energy = max(0.0, self.energy - 0.1)

    def add_effect(
        self,
        effect_id: str,
        stat_affected: str,
        modifier: Any,
        duration_hours: float,
        current_game_time: float,
    ):
        expiry_time = current_game_time + duration_hours

        if effect_id == "mystery_brew_random_effect":
            possible_effects = [
                {
                    "id_suffix": "temp_resolve_boost",
                    "stat": "resolve",
                    "mod": 1,
                    "dur": 0.25,
                },
                {
                    "id_suffix": "temp_resolve_drain",
                    "stat": "resolve",
                    "mod": -1,
                    "dur": 0.25,
                },
                {
                    "id_suffix": "temp_stamina_boost",
                    "stat": "current_stamina",
                    "mod": 10,
                    "dur": 0.25,
                },
                {
                    "id_suffix": "temp_stamina_drain",
                    "stat": "current_stamina",
                    "mod": -10,
                    "dur": 0.25,
                },
                {
                    "id_suffix": "temp_happiness_boost",
                    "stat": "happiness",
                    "mod": 0.2,
                    "dur": 0.25,
                },
            ]
            chosen_effect_details = random.choice(possible_effects)
            effect_id = f"mystery_brew_{chosen_effect_details['id_suffix']}"
            stat_affected = chosen_effect_details["stat"]
            modifier = chosen_effect_details["mod"]
            expiry_time = current_game_time + chosen_effect_details["dur"]

        self.active_effects = [
            eff for eff in self.active_effects if eff.effect_id != effect_id
        ]
        new_effect = ActiveEffect(
            effect_id=effect_id,
            stat_affected=stat_affected,
            modifier=modifier,
            expiry_time=expiry_time,
        )
        self.active_effects.append(new_effect)

        if duration_hours <= 0.01:
            if stat_affected == "heal":
                setattr(
                    self,
                    "current_stamina",
                    min(self.get_stat("max_stamina"), self.current_stamina + modifier),
                )
            self.active_effects = [
                eff for eff in self.active_effects if eff.effect_id != effect_id
            ]

    def update_effects(self, current_game_time: float):
        self.active_effects = [
            effect
            for effect in self.active_effects
            if effect.expiry_time > current_game_time
        ]
        base_energy = 1.0 - self.tiredness
        energy_modifier = self.get_stat_modifier("energy")
        self.energy = max(0.0, min(1.0, base_energy + energy_modifier))
        self.current_stamina = min(self.current_stamina, self.get_stat("max_stamina"))

    def get_stat_modifier(self, stat_name: str) -> Any:
        total_modifier = 0
        if stat_name in [
            "resolve",
            "max_stamina",
            "current_stamina",
            "happiness",
            "luck_modifier",
            "hunger_reduction",
            "heal",
            "courage",
            "inebriation",
            "energy",
        ]:
            for effect in self.active_effects:
                if effect.stat_affected == stat_name:
                    if isinstance(effect.modifier, (int, float)):
                        total_modifier += effect.modifier
        return total_modifier

    def get_stat(self, stat_name: str) -> Any:
        base_value = getattr(self, stat_name, 0)
        modifier = self.get_stat_modifier(stat_name)

        if stat_name == "current_stamina":
            calculated_value = base_value + modifier
            return min(calculated_value, self.get_stat("max_stamina"))
        if stat_name == "energy":
            return max(0.0, min(1.0, base_value + modifier))
        if isinstance(base_value, (int, float)):
            return base_value + modifier
        return base_value

    def get_status_effects(self) -> List[str]:
        display_effects = []
        if self.tiredness > 0.8:
            display_effects.append("Exhausted")
        elif self.tiredness > 0.5:
            display_effects.append("Tired")
        if self.energy < 0.3:
            display_effects.append("Drained")
        elif self.energy < 0.6:
            display_effects.append("Fatigued")
        if self.rest_immune:
            display_effects.append("Sleepless")

        for effect in self.active_effects:
            effect_name = (
                effect.effect_id.replace("_from_", " (").replace("_", " ").title() + ")"
                if "_from_" in effect.effect_id
                else effect.effect_id.replace("_", " ").title()
            )
            display_effects.append(
                f"{effect_name} ({effect.modifier:+g} to {effect.stat_affected})"
            )

        return display_effects if display_effects else ["Feeling normal."]

    def consume_item_and_apply_effects(
        self, item: Item, current_game_time: float
    ) -> bool:
        if not self.inventory.has_item(item.id):
            return False

        if item.effects:
            for effect_key, effect_value in item.effects.items():  # type: ignore
                if effect_key == "duration_hours":
                    continue
                if effect_key == "random_effect" and effect_value is True:
                    self.add_effect(
                        effect_id=f"{item.id}_random_effect",
                        stat_affected="random",
                        modifier=True,
                        duration_hours=item.effects.get("duration_hours", 0.25),
                        current_game_time=current_game_time,
                    )  # type: ignore
                else:
                    self.add_effect(
                        effect_id=f"{item.id}_{effect_key}",
                        stat_affected=effect_key,
                        modifier=effect_value,
                        duration_hours=item.effects.get("duration_hours", 0),
                        current_game_time=current_game_time,
                    )  # type: ignore

        if item.item_type == "food":
            self.last_ate = current_game_time
        elif item.item_type == "drink":
            self.last_drank = current_game_time

        success, _ = self.inventory.remove_item(item.id, 1)
        return success

    def add_xp(self, amount: int):
        print(f"DEBUG: Player received {amount} XP.")
        pass

    def has_completed_bounty(self, bounty_id: str) -> bool:
        return bounty_id in self.completed_bounty_ids


# Compatibility alias for tests
Player = PlayerState
