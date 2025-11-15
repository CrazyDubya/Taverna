"""
Dynamic personality traits system for NPCs.
Makes each NPC unique with distinct personality quirks that affect all interactions.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import random
import time
import logging

logger = logging.getLogger(__name__)


class PersonalityTrait(Enum):
    """Core personality traits that define NPC behavior."""

    # Social traits
    EXTROVERTED = "extroverted"
    INTROVERTED = "introverted"
    EMPATHETIC = "empathetic"
    ALOOF = "aloof"
    GOSSIPY = "gossipy"
    SECRETIVE = "secretive"

    # Emotional traits
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    HOT_TEMPERED = "hot_tempered"
    PATIENT = "patient"
    ANXIOUS = "anxious"
    CONFIDENT = "confident"

    # Work ethic traits
    HARDWORKING = "hardworking"
    LAZY = "lazy"
    PERFECTIONIST = "perfectionist"
    CARELESS = "careless"
    AMBITIOUS = "ambitious"
    CONTENT = "content"

    # Moral traits
    HONEST = "honest"
    DECEPTIVE = "deceptive"
    GENEROUS = "generous"
    GREEDY = "greedy"
    LOYAL = "loyal"
    OPPORTUNISTIC = "opportunistic"

    # Intellectual traits
    CURIOUS = "curious"
    INCURIOUS = "incurious"
    WISE = "wise"
    NAIVE = "naive"
    CREATIVE = "creative"
    CONVENTIONAL = "conventional"


@dataclass
class TraitExpression:
    """How a personality trait manifests in behavior."""

    trait: PersonalityTrait
    intensity: float  # 0.0 to 1.0
    triggers: List[str]  # Situations that activate this trait
    dialogue_modifiers: Dict[str, str]  # How it affects speech
    behavior_tendencies: Dict[str, float]  # Probability modifiers for actions
    last_expressed: Optional[float] = None  # When it was last prominently displayed

    def is_active_in_situation(self, situation: str) -> bool:
        """Check if this trait would be expressed in current situation."""
        return any(trigger.lower() in situation.lower() for trigger in self.triggers)

    def get_dialogue_flavor(self, base_message: str, situation: str) -> str:
        """Add personality flavor to dialogue based on trait."""
        if not self.is_active_in_situation(situation):
            return base_message

        # Apply dialogue modifiers based on trait
        modified = base_message

        for modifier_type, modification in self.dialogue_modifiers.items():
            if modifier_type == "prefix" and random.random() < self.intensity:
                modified = f"{modification} {modified}"
            elif modifier_type == "suffix" and random.random() < self.intensity:
                modified = f"{modified} {modification}"
            elif modifier_type == "tone" and random.random() < self.intensity:
                # Modify the tone/style of the entire message
                modified = self._apply_tone_modification(modified, modification)

        return modified

    def _apply_tone_modification(self, message: str, tone: str) -> str:
        """Apply tonal modifications to the message."""
        if tone == "enthusiastic":
            return message.replace(".", "!").replace("I ", "I really ")
        elif tone == "cautious":
            return message.replace(".", "...").replace("I think", "I'm not sure, but I think")
        elif tone == "gruff":
            return message.replace("Hello", "Hmph").replace("please", "")
        elif tone == "flowery":
            return message.replace("good", "wonderful").replace("I think", "In my humble opinion")
        else:
            return message


class PersonalityProfile:
    """Complete personality profile for an NPC."""

    def __init__(self, npc_id: str, npc_name: str):
        self.npc_id = npc_id
        self.npc_name = npc_name
        self.traits: Dict[PersonalityTrait, TraitExpression] = {}
        self.core_values: List[str] = []
        self.quirks: List[str] = []
        self.fears: List[str] = []
        self.desires: List[str] = []
        self.backstory_elements: Dict[str, str] = {}

        # Dynamic personality state
        self.personality_stability: float = 0.8  # How consistent personality is
        self.current_personality_shift: float = 0.0  # Temporary personality changes

    def add_trait(
        self,
        trait: PersonalityTrait,
        intensity: float,
        triggers: List[str],
        dialogue_mods: Dict[str, str],
        behavior_mods: Dict[str, float],
    ) -> None:
        """Add a personality trait with its expressions."""
        self.traits[trait] = TraitExpression(
            trait=trait,
            intensity=intensity,
            triggers=triggers,
            dialogue_modifiers=dialogue_mods,
            behavior_tendencies=behavior_mods,
        )
        logger.info(f"{self.npc_name} gained trait: {trait.value} (intensity: {intensity})")

    def get_active_traits(self, situation: str) -> List[TraitExpression]:
        """Get traits that would be active in the current situation."""
        active = []
        for trait_expr in self.traits.values():
            if trait_expr.is_active_in_situation(situation):
                active.append(trait_expr)

        # Sort by intensity - strongest traits first
        return sorted(active, key=lambda t: t.intensity, reverse=True)

    def modify_dialogue(self, base_message: str, situation: str) -> str:
        """Apply personality-based modifications to dialogue."""
        active_traits = self.get_active_traits(situation)

        modified = base_message

        # Apply modifications from active traits (strongest first)
        for trait_expr in active_traits[:3]:  # Limit to top 3 traits to avoid over-modification
            modified = trait_expr.get_dialogue_flavor(modified, situation)

            # Mark trait as recently expressed
            trait_expr.last_expressed = time.time()

        return modified

    def get_behavior_tendency(self, action_type: str) -> float:
        """Get the likelihood modifier for a type of action."""
        base_tendency = 0.5

        for trait_expr in self.traits.values():
            if action_type in trait_expr.behavior_tendencies:
                base_tendency += trait_expr.behavior_tendencies[action_type] * trait_expr.intensity

        return max(0.0, min(1.0, base_tendency))

    def get_personality_summary(self) -> str:
        """Get a human-readable personality summary."""
        if not self.traits:
            return f"{self.npc_name} has an unremarkable personality."

        dominant_traits = sorted(self.traits.values(), key=lambda t: t.intensity, reverse=True)[:3]

        trait_descriptions = []
        for trait_expr in dominant_traits:
            intensity_desc = (
                "very" if trait_expr.intensity > 0.7 else "somewhat" if trait_expr.intensity > 0.4 else "mildly"
            )
            trait_descriptions.append(f"{intensity_desc} {trait_expr.trait.value}")

        traits_text = ", ".join(trait_descriptions)

        summary = f"{self.npc_name} is {traits_text}."

        if self.core_values:
            summary += f" They value {', '.join(self.core_values[:2])}."

        if self.quirks:
            summary += f" Notable quirk: {random.choice(self.quirks)}"

        return summary

    def react_to_world_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personality-based reaction to world events."""
        reactions = {}

        # Check how each trait would react
        for trait, trait_expr in self.traits.items():
            if trait == PersonalityTrait.ANXIOUS and event_type in ["theft", "conflict", "danger"]:
                reactions["stress_increase"] = trait_expr.intensity * 0.5
                reactions["concern_level"] = "high"
            elif trait == PersonalityTrait.OPTIMISTIC and event_type in ["good_news", "celebration"]:
                reactions["mood_boost"] = trait_expr.intensity * 0.3
            elif trait == PersonalityTrait.GOSSIPY and event_type in ["scandal", "rumor"]:
                reactions["wants_to_share"] = True
                reactions["gossip_intensity"] = trait_expr.intensity
            elif trait == PersonalityTrait.GENEROUS and event_type == "charity_drive":
                reactions["donation_likelihood"] = trait_expr.intensity

        return reactions


def create_personality_from_profession(npc_id: str, npc_name: str, profession: str) -> PersonalityProfile:
    """Create a personality profile based on NPC's profession."""
    profile = PersonalityProfile(npc_id, npc_name)

    # Base personality on profession with some randomization
    if profession.lower() in ["bartender", "innkeeper"]:
        # Bartenders tend to be social and observant
        profile.add_trait(
            PersonalityTrait.EXTROVERTED,
            0.7,
            triggers=["conversation", "greeting", "social"],
            dialogue_mods={"prefix": "Well now,", "tone": "friendly"},
            behavior_mods={"start_conversation": 0.3, "share_gossip": 0.2},
        )
        profile.add_trait(
            PersonalityTrait.EMPATHETIC,
            0.6,
            triggers=["customer_problem", "emotional_situation"],
            dialogue_mods={"prefix": "I understand,", "tone": "caring"},
            behavior_mods={"offer_help": 0.4, "listen_patiently": 0.3},
        )
        profile.core_values = ["hospitality", "community"]
        profile.quirks = ["always polishing glasses", "remembers everyone's favorite drink"]

    elif profession.lower() in ["merchant", "trader", "shopkeeper"]:
        # Merchants are business-focused and persuasive
        profile.add_trait(
            PersonalityTrait.AMBITIOUS,
            0.8,
            triggers=["business", "negotiation", "money"],
            dialogue_mods={"suffix": "Good for business!", "tone": "persuasive"},
            behavior_mods={"negotiate_price": 0.4, "seek_profit": 0.3},
        )
        profile.add_trait(
            PersonalityTrait.HONEST,
            0.6,
            triggers=["trade", "reputation"],
            dialogue_mods={"prefix": "I'll be straight with you,", "tone": "direct"},
            behavior_mods={"fair_dealing": 0.4, "build_reputation": 0.3},
        )
        profile.core_values = ["fair trade", "prosperity"]
        profile.quirks = ["always calculating profit margins", "hoards rare coins"]

    elif profession.lower() in ["blacksmith", "craftsman"]:
        # Craftsmen are perfectionist and hardworking
        profile.add_trait(
            PersonalityTrait.PERFECTIONIST,
            0.8,
            triggers=["crafting", "quality", "work"],
            dialogue_mods={"suffix": "It must be done right.", "tone": "serious"},
            behavior_mods={"attention_to_detail": 0.5, "refuse_rush_jobs": 0.3},
        )
        profile.add_trait(
            PersonalityTrait.HARDWORKING,
            0.7,
            triggers=["work", "commitment"],
            dialogue_mods={"prefix": "Hard work never killed anyone,", "tone": "determined"},
            behavior_mods={"long_work_hours": 0.4, "take_pride_in_work": 0.5},
        )
        profile.core_values = ["quality craftsmanship", "reliability"]
        profile.quirks = ["hands always stained from work", "judges others by their tools"]

    elif profession.lower() in ["guard", "soldier"]:
        # Guards are loyal and vigilant
        profile.add_trait(
            PersonalityTrait.LOYAL,
            0.8,
            triggers=["duty", "authority", "protection"],
            dialogue_mods={"prefix": "By my oath,", "tone": "formal"},
            behavior_mods={"follow_orders": 0.5, "protect_others": 0.4},
        )
        profile.add_trait(
            PersonalityTrait.CONFIDENT,
            0.6,
            triggers=["confrontation", "leadership"],
            dialogue_mods={"tone": "authoritative"},
            behavior_mods={"take_charge": 0.3, "stand_ground": 0.4},
        )
        profile.core_values = ["duty", "justice"]
        profile.quirks = ["always scanning for threats", "polishes armor obsessively"]

    else:
        # Default personality for unknown professions
        random_traits = [
            (PersonalityTrait.CURIOUS, 0.5, ["new_information", "strangers"]),
            (PersonalityTrait.PATIENT, 0.6, ["waiting", "teaching"]),
            (PersonalityTrait.HONEST, 0.7, ["conversation", "business"]),
        ]

        for trait, intensity, triggers in random_traits:
            profile.add_trait(
                trait,
                intensity + random.uniform(-0.2, 0.2),
                triggers=triggers,
                dialogue_mods={"tone": "neutral"},
                behavior_mods={},
            )

    # Add random secondary traits for uniqueness
    secondary_traits = [
        PersonalityTrait.OPTIMISTIC,
        PersonalityTrait.PESSIMISTIC,
        PersonalityTrait.PATIENT,
        PersonalityTrait.HOT_TEMPERED,
        PersonalityTrait.CURIOUS,
        PersonalityTrait.SECRETIVE,
    ]

    # Add 1-2 random secondary traits
    for _ in range(random.randint(1, 2)):
        trait = random.choice(secondary_traits)
        if trait not in profile.traits:
            intensity = random.uniform(0.3, 0.6)
            profile.add_trait(
                trait, intensity, triggers=["general"], dialogue_mods={"tone": trait.value}, behavior_mods={}
            )

    return profile


class PersonalityManager:
    """Manages personality profiles for all NPCs."""

    def __init__(self):
        self.personalities: Dict[str, PersonalityProfile] = {}

    def get_or_create_personality(
        self, npc_id: str, npc_name: str, profession: Optional[str] = None
    ) -> PersonalityProfile:
        """Get existing personality or create new one."""
        if npc_id not in self.personalities:
            if profession:
                self.personalities[npc_id] = create_personality_from_profession(npc_id, npc_name, profession)
            else:
                # Create generic personality
                profile = PersonalityProfile(npc_id, npc_name)
                # Add some random traits
                traits_to_add = random.sample(list(PersonalityTrait), 3)
                for trait in traits_to_add:
                    intensity = random.uniform(0.4, 0.8)
                    profile.add_trait(
                        trait, intensity, triggers=["general"], dialogue_mods={"tone": trait.value}, behavior_mods={}
                    )
                self.personalities[npc_id] = profile

            logger.info(f"Created personality for {npc_name}: {self.personalities[npc_id].get_personality_summary()}")

        return self.personalities[npc_id]

    def modify_dialogue_for_personality(self, npc_id: str, base_message: str, situation: str = "conversation") -> str:
        """Apply personality modifications to NPC dialogue."""
        if npc_id in self.personalities:
            return self.personalities[npc_id].modify_dialogue(base_message, situation)
        return base_message

    def get_behavior_likelihood(self, npc_id: str, action_type: str) -> float:
        """Get likelihood that NPC will perform a certain type of action."""
        if npc_id in self.personalities:
            return self.personalities[npc_id].get_behavior_tendency(action_type)
        return 0.5  # Default neutral likelihood

    def react_to_world_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Get personality-based reactions from all NPCs to a world event."""
        reactions = {}

        for npc_id, personality in self.personalities.items():
            npc_reaction = personality.react_to_world_event(event_type, event_data)
            if npc_reaction:  # Only include NPCs that actually react
                reactions[npc_id] = npc_reaction

        return reactions

    def get_personality_insights(self) -> Dict[str, str]:
        """Get personality summaries for all NPCs."""
        return {npc_id: personality.get_personality_summary() for npc_id, personality in self.personalities.items()}
