"""
Dynamic Quest Generation System.
Creates meaningful quests and objectives that emerge naturally from player actions and world state.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
import random
import time
import logging
from .story_threads import StoryThread, ThreadStage, ThreadCondition, ThreadType, ThreadPriority, ThreadStatus

logger = logging.getLogger(__name__)


class QuestType(Enum):
    """Types of dynamically generated quests."""

    FETCH = "fetch"  # Bring item A to person B
    DELIVERY = "delivery"  # Take message/item from A to B
    INVESTIGATION = "investigation"  # Gather information about X
    PROTECTION = "protection"  # Keep someone/something safe
    MEDIATION = "mediation"  # Resolve conflict between parties
    COLLECTION = "collection"  # Gather multiple items/information
    ESCORT = "escort"  # Safely guide someone somewhere
    REVENGE = "revenge"  # Help someone get justice/revenge
    RESCUE = "rescue"  # Save someone from danger
    DISCOVERY = "discovery"  # Find something lost/hidden
    CONSTRUCTION = "construction"  # Help build/create something
    TEACHING = "teaching"  # Learn or teach a skill
    ROMANCE = "romance"  # Help with romantic situation
    TRADE = "trade"  # Facilitate business deal
    MYSTERY = "mystery"  # Solve a puzzle or mystery


class QuestUrgency(Enum):
    """How urgent a quest is."""

    LEISURELY = "leisurely"  # No time pressure
    CASUAL = "casual"  # Mild time pressure
    MODERATE = "moderate"  # Some urgency
    URGENT = "urgent"  # Time-sensitive
    CRITICAL = "critical"  # Must be done immediately


@dataclass
class QuestReward:
    """Rewards for completing a quest."""

    gold: int = 0
    items: List[str] = field(default_factory=list)
    reputation_boost: float = 0.0
    relationship_boost: Dict[str, float] = field(default_factory=dict)  # NPC ID -> boost
    special_rewards: List[str] = field(default_factory=list)  # Unique rewards

    def get_description(self) -> str:
        """Get a human-readable description of the rewards."""
        parts = []
        if self.gold > 0:
            parts.append(f"{self.gold} gold")
        if self.items:
            parts.append(f"items: {', '.join(self.items)}")
        if self.reputation_boost > 0:
            parts.append("improved reputation")
        if self.relationship_boost:
            parts.append("stronger relationships")
        if self.special_rewards:
            parts.append(f"special: {', '.join(self.special_rewards)}")

        return "; ".join(parts) if parts else "the satisfaction of helping"


@dataclass
class QuestObjective:
    """A specific objective within a quest."""

    objective_id: str
    description: str
    completed: bool = False
    optional: bool = False

    # Completion conditions
    required_actions: List[str] = field(default_factory=list)
    required_items: List[str] = field(default_factory=list)
    required_location: Optional[str] = None
    required_npc_interaction: Optional[str] = None
    custom_condition: Optional[str] = None  # Custom condition description

    # Progress tracking
    current_progress: int = 0
    required_progress: int = 1

    def get_progress_description(self) -> str:
        """Get a description of current progress."""
        if self.completed:
            return "✓ Completed"
        elif self.required_progress > 1:
            return f"({self.current_progress}/{self.required_progress})"
        else:
            return "○ Pending"


class DynamicQuest:
    """A dynamically generated quest with adaptive objectives."""

    def __init__(self, quest_id: str, title: str, quest_type: QuestType, description: str, giver_npc_id: str):
        self.quest_id = quest_id
        self.title = title
        self.quest_type = quest_type
        self.description = description
        self.giver_npc_id = giver_npc_id

        # Quest state
        self.status = "available"  # available, active, completed, failed, expired
        self.objectives: List[QuestObjective] = []
        self.current_objective_index = 0

        # Quest metadata
        self.urgency = QuestUrgency.CASUAL
        self.difficulty = 1.0  # 0.5 = easy, 1.0 = normal, 2.0 = hard
        self.estimated_duration_hours = 2.0
        self.rewards = QuestReward()

        # Timing
        self.created_at = time.time()
        self.accepted_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.expires_at: Optional[float] = None

        # Context and relationships
        self.involved_npcs: Set[str] = {giver_npc_id}
        self.required_locations: Set[str] = set()
        self.tags: Set[str] = set()

        # Dynamic adaptation
        self.adaptation_triggers: List[str] = []  # Conditions that modify quest
        self.backup_objectives: List[QuestObjective] = []  # Alternative paths

        # Player interaction
        self.player_interest_score = 0.0  # How interested player seems
        self.acceptance_probability = 0.7  # Likelihood player will accept

    def add_objective(self, objective: QuestObjective, is_backup: bool = False) -> None:
        """Add an objective to the quest."""
        if is_backup:
            self.backup_objectives.append(objective)
        else:
            self.objectives.append(objective)

            # Update quest metadata based on objective
            if objective.required_location:
                self.required_locations.add(objective.required_location)
            if objective.required_npc_interaction:
                self.involved_npcs.add(objective.required_npc_interaction)

    def get_current_objective(self) -> Optional[QuestObjective]:
        """Get the current active objective."""
        if 0 <= self.current_objective_index < len(self.objectives):
            return self.objectives[self.current_objective_index]
        return None

    def complete_current_objective(self) -> bool:
        """Mark current objective as complete and advance."""
        current_obj = self.get_current_objective()
        if current_obj and not current_obj.completed:
            current_obj.completed = True
            self.current_objective_index += 1

            # Check if quest is complete
            if self.current_objective_index >= len(self.objectives):
                self.status = "completed"
                self.completed_at = time.time()
                return True

        return False

    def update_objective_progress(self, action_description: str, game_state: Any) -> bool:
        """Update objective progress based on player action."""
        current_obj = self.get_current_objective()
        if not current_obj or current_obj.completed:
            return False

        progress_made = False

        # Check if action matches required actions
        for required_action in current_obj.required_actions:
            if required_action.lower() in action_description.lower():
                current_obj.current_progress += 1
                progress_made = True
                break

        # Check if progress requirement is met
        if current_obj.current_progress >= current_obj.required_progress:
            return self.complete_current_objective()

        return progress_made

    def adapt_to_player_behavior(self, player_action: str, success: bool) -> None:
        """Adapt quest based on player behavior."""
        if not success:
            # Player failed - maybe make it easier or provide alternative
            if self.difficulty > 0.5:
                self.difficulty *= 0.9  # Slightly easier

            # Consider adding backup objectives
            if self.backup_objectives and random.random() < 0.3:
                backup_obj = random.choice(self.backup_objectives)
                self.objectives.insert(self.current_objective_index + 1, backup_obj)
                self.backup_objectives.remove(backup_obj)

        else:
            # Player succeeded - track engagement
            if "quest" in player_action.lower() or self.quest_id in player_action:
                self.player_interest_score += 0.1

    def check_expiration(self) -> bool:
        """Check if quest has expired."""
        if self.expires_at and time.time() > self.expires_at:
            if self.status in ["available", "active"]:
                self.status = "expired"
                return True
        return False

    def get_quest_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the quest."""
        current_obj = self.get_current_objective()

        return {
            "quest_id": self.quest_id,
            "title": self.title,
            "type": self.quest_type.value,
            "description": self.description,
            "status": self.status,
            "giver": self.giver_npc_id,
            "urgency": self.urgency.value,
            "difficulty": self.difficulty,
            "current_objective": current_obj.description if current_obj else None,
            "objective_progress": current_obj.get_progress_description() if current_obj else None,
            "total_objectives": len(self.objectives),
            "completed_objectives": len([obj for obj in self.objectives if obj.completed]),
            "rewards": self.rewards.get_description(),
            "estimated_time": f"{self.estimated_duration_hours:.1f} hours",
            "involved_npcs": list(self.involved_npcs),
            "required_locations": list(self.required_locations),
            "age_hours": (time.time() - self.created_at) / 3600.0,
        }


class QuestTemplate:
    """Template for generating similar quests with variations."""

    def __init__(
        self, template_id: str, quest_type: QuestType, title_templates: List[str], description_templates: List[str]
    ):
        self.template_id = template_id
        self.quest_type = quest_type
        self.title_templates = title_templates
        self.description_templates = description_templates
        self.objective_templates: List[Dict[str, Any]] = []
        self.reward_templates: List[QuestReward] = []

        # Generation parameters
        self.min_objectives = 1
        self.max_objectives = 3
        self.urgency_weights = {urgency: 1.0 for urgency in QuestUrgency}
        self.difficulty_range = (0.5, 1.5)

        # Context requirements
        self.required_npc_types: List[str] = []  # Types of NPCs that can give this quest
        self.required_world_conditions: List[str] = []
        self.prohibited_conditions: List[str] = []

    def generate_quest(self, context: Dict[str, Any]) -> Optional[DynamicQuest]:
        """Generate a quest from this template using current context."""
        # Check if conditions are met
        if not self._can_generate_in_context(context):
            return None

        # Select quest giver
        giver_npc_id = self._select_quest_giver(context)
        if not giver_npc_id:
            return None

        # Generate quest details
        quest_id = f"quest_{self.template_id}_{int(time.time())}"
        title = self._generate_title(context)
        description = self._generate_description(context)

        quest = DynamicQuest(quest_id, title, self.quest_type, description, giver_npc_id)

        # Generate objectives
        num_objectives = random.randint(self.min_objectives, self.max_objectives)
        for i in range(num_objectives):
            objective = self._generate_objective(i, context)
            if objective:
                quest.add_objective(objective)

        # Set quest properties
        quest.urgency = self._select_urgency()
        quest.difficulty = random.uniform(*self.difficulty_range)
        quest.rewards = self._generate_rewards(quest.difficulty, context)
        quest.estimated_duration_hours = self._estimate_duration(quest)

        # Set expiration if urgent
        if quest.urgency in [QuestUrgency.URGENT, QuestUrgency.CRITICAL]:
            urgency_hours = {QuestUrgency.URGENT: 48.0, QuestUrgency.CRITICAL: 24.0}
            quest.expires_at = time.time() + (urgency_hours[quest.urgency] * 3600)

        return quest

    def _can_generate_in_context(self, context: Dict[str, Any]) -> bool:
        """Check if this template can generate a quest in the current context."""
        # Check required world conditions
        world_state = context.get("world_state", {})
        for condition in self.required_world_conditions:
            if not world_state.get(condition, False):
                return False

        # Check prohibited conditions
        for condition in self.prohibited_conditions:
            if world_state.get(condition, False):
                return False

        return True

    def _select_quest_giver(self, context: Dict[str, Any]) -> Optional[str]:
        """Select an appropriate NPC to give this quest."""
        available_npcs = context.get("available_npcs", [])

        if self.required_npc_types:
            # Filter by NPC type/profession
            suitable_npcs = []
            for npc_data in available_npcs:
                npc_type = npc_data.get("profession", "").lower()
                if any(req_type in npc_type for req_type in self.required_npc_types):
                    suitable_npcs.append(npc_data["id"])

            if suitable_npcs:
                return random.choice(suitable_npcs)
        else:
            # Any NPC can give this quest
            if available_npcs:
                return random.choice(available_npcs)["id"]

        return None

    def _generate_title(self, context: Dict[str, Any]) -> str:
        """Generate a quest title."""
        template = random.choice(self.title_templates)

        # Replace placeholders
        replacements = self._get_context_replacements(context)
        for placeholder, value in replacements.items():
            template = template.replace(f"{{{placeholder}}}", str(value))

        return template

    def _generate_description(self, context: Dict[str, Any]) -> str:
        """Generate a quest description."""
        template = random.choice(self.description_templates)

        # Replace placeholders
        replacements = self._get_context_replacements(context)
        for placeholder, value in replacements.items():
            template = template.replace(f"{{{placeholder}}}", str(value))

        return template

    def _get_context_replacements(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Get placeholder replacements from context."""
        replacements = {}

        # Add common replacements
        replacements["item"] = random.choice(["rare book", "family heirloom", "special ingredient", "lost letter"])
        replacements["location"] = random.choice(["the forest", "the market", "the old ruins", "the distant village"])
        replacements["person"] = random.choice(["my cousin", "an old friend", "a traveling merchant", "my relative"])
        replacements["problem"] = random.choice(["bandits", "wild animals", "strange occurrences", "missing supplies"])

        # Add context-specific replacements
        if "player_reputation" in context:
            rep_level = context["player_reputation"]
            if rep_level > 0.5:
                replacements["reputation_comment"] = "You seem trustworthy"
            else:
                replacements["reputation_comment"] = "I hope I can trust you"

        return replacements

    def _generate_objective(self, index: int, context: Dict[str, Any]) -> Optional[QuestObjective]:
        """Generate an objective for the quest."""
        if index >= len(self.objective_templates):
            return None

        template = self.objective_templates[index]

        objective_id = f"obj_{index}_{int(time.time())}"
        description = template.get("description", f"Complete objective {index + 1}")

        objective = QuestObjective(
            objective_id=objective_id,
            description=description,
            optional=template.get("optional", False),
            required_actions=template.get("required_actions", []),
            required_items=template.get("required_items", []),
            required_location=template.get("required_location"),
            required_npc_interaction=template.get("required_npc_interaction"),
            required_progress=template.get("required_progress", 1),
        )

        return objective

    def _select_urgency(self) -> QuestUrgency:
        """Select quest urgency based on weights."""
        urgencies = list(self.urgency_weights.keys())
        weights = list(self.urgency_weights.values())
        return random.choices(urgencies, weights=weights)[0]

    def _generate_rewards(self, difficulty: float, context: Dict[str, Any]) -> QuestReward:
        """Generate appropriate rewards for the quest."""
        if self.reward_templates:
            base_reward = random.choice(self.reward_templates)
        else:
            base_reward = QuestReward()

        # Scale rewards by difficulty
        reward = QuestReward(
            gold=int(base_reward.gold * difficulty),
            items=base_reward.items.copy(),
            reputation_boost=base_reward.reputation_boost * difficulty,
            relationship_boost=base_reward.relationship_boost.copy(),
            special_rewards=base_reward.special_rewards.copy(),
        )

        # Add baseline rewards if none specified
        if reward.gold == 0:
            reward.gold = random.randint(10, 50) * int(difficulty)

        if reward.reputation_boost == 0:
            reward.reputation_boost = 0.1 * difficulty

        return reward

    def _estimate_duration(self, quest: DynamicQuest) -> float:
        """Estimate how long the quest will take."""
        base_duration = len(quest.objectives) * 30  # 30 minutes per objective

        # Adjust for difficulty
        duration_minutes = base_duration * quest.difficulty

        # Adjust for quest type
        type_modifiers = {
            QuestType.FETCH: 0.8,
            QuestType.DELIVERY: 0.9,
            QuestType.INVESTIGATION: 1.5,
            QuestType.MYSTERY: 2.0,
            QuestType.COLLECTION: 1.3,
        }

        modifier = type_modifiers.get(quest.quest_type, 1.0)
        duration_minutes *= modifier

        return duration_minutes / 60.0  # Convert to hours


class DynamicQuestGenerator:
    """Main quest generation system."""

    def __init__(self):
        self.templates: Dict[str, QuestTemplate] = {}
        self.active_quests: Dict[str, DynamicQuest] = {}
        self.completed_quests: Dict[str, DynamicQuest] = {}

        # Generation parameters
        self.max_active_quests = 5
        self.quest_generation_cooldown = 3600.0  # 1 hour between generations
        self.last_generation_time = 0.0

        # Statistics
        self.total_quests_generated = 0
        self.total_quests_completed = 0
        self.player_quest_preferences: Dict[QuestType, float] = {}

        # Initialize default templates
        self._initialize_default_templates()

    def _initialize_default_templates(self):
        """Initialize default quest templates."""

        # Fetch quest template
        fetch_template = QuestTemplate(
            template_id="fetch_item",
            quest_type=QuestType.FETCH,
            title_templates=["Retrieve the {item}", "Find My Lost {item}", "The Missing {item}"],
            description_templates=[
                "I lost my {item} somewhere in {location}. Could you help me find it?",
                "My precious {item} went missing. I think it might be in {location}.",
                "I need someone to retrieve my {item} from {location}. It's very important to me.",
            ],
        )

        fetch_template.objective_templates = [
            {
                "description": "Search for the missing item",
                "required_actions": ["search", "investigate", "look"],
                "required_progress": 1,
            },
            {
                "description": "Return the item to its owner",
                "required_actions": ["return", "give", "deliver"],
                "required_progress": 1,
            },
        ]

        fetch_template.reward_templates = [QuestReward(gold=25, reputation_boost=0.1)]

        self.add_template(fetch_template)

        # Delivery quest template
        delivery_template = QuestTemplate(
            template_id="delivery_message",
            quest_type=QuestType.DELIVERY,
            title_templates=["Message for {person}", "Urgent Delivery", "Important News"],
            description_templates=[
                "I need you to deliver this message to {person} in {location}.",
                "This is urgent news that must reach {person} quickly.",
                "Please take this to {person} - they're waiting for it.",
            ],
        )

        delivery_template.objective_templates = [
            {
                "description": "Deliver the message",
                "required_actions": ["deliver", "give", "talk"],
                "required_progress": 1,
            }
        ]

        delivery_template.reward_templates = [QuestReward(gold=15, reputation_boost=0.05)]

        delivery_template.urgency_weights = {
            QuestUrgency.LEISURELY: 0.2,
            QuestUrgency.CASUAL: 0.3,
            QuestUrgency.MODERATE: 0.3,
            QuestUrgency.URGENT: 0.2,
        }

        self.add_template(delivery_template)

        # Investigation quest template
        investigation_template = QuestTemplate(
            template_id="investigate_mystery",
            quest_type=QuestType.INVESTIGATION,
            title_templates=["Strange Happenings", "Investigate the Mystery", "Unusual Events"],
            description_templates=[
                "There have been strange occurrences around {location}. Could you investigate?",
                "Something odd is happening and I need someone to look into it.",
                "People are reporting {problem} near {location}. Can you find out what's going on?",
            ],
        )

        investigation_template.objective_templates = [
            {
                "description": "Gather information about the mystery",
                "required_actions": ["ask", "investigate", "talk"],
                "required_progress": 3,
            },
            {
                "description": "Visit the location of the strange events",
                "required_actions": ["visit", "go", "explore"],
                "required_progress": 1,
            },
            {
                "description": "Report your findings",
                "required_actions": ["report", "tell", "explain"],
                "required_progress": 1,
            },
        ]

        investigation_template.reward_templates = [
            QuestReward(gold=40, reputation_boost=0.2, special_rewards=["local knowledge"])
        ]

        investigation_template.difficulty_range = (1.0, 2.0)

        self.add_template(investigation_template)

        # Mediation quest template
        mediation_template = QuestTemplate(
            template_id="resolve_conflict",
            quest_type=QuestType.MEDIATION,
            title_templates=["Peaceful Resolution", "Settle the Dispute", "Mediate the Conflict"],
            description_templates=[
                "There's a disagreement between me and another person. Could you help us find a solution?",
                "I'm having a conflict with someone and need a neutral party to help resolve it.",
                "This dispute has gone on too long. We need someone to mediate.",
            ],
        )

        mediation_template.objective_templates = [
            {
                "description": "Listen to both sides of the conflict",
                "required_actions": ["talk", "listen", "ask"],
                "required_progress": 2,
            },
            {
                "description": "Propose a fair solution",
                "required_actions": ["suggest", "propose", "mediate"],
                "required_progress": 1,
            },
        ]

        mediation_template.reward_templates = [
            QuestReward(gold=30, reputation_boost=0.15, relationship_boost={"all_involved": 0.2})
        ]

        self.add_template(mediation_template)

    def add_template(self, template: QuestTemplate) -> None:
        """Add a quest template to the generator."""
        self.templates[template.template_id] = template
        logger.debug(f"Added quest template: {template.template_id}")

    def update(self, game_state: Any) -> List[str]:
        """Update the quest system and generate new quests if appropriate."""
        notifications = []

        # Update existing quests
        for quest in list(self.active_quests.values()):
            if quest.check_expiration():
                notifications.append(f"Quest '{quest.title}' has expired!")
                self._move_to_completed(quest)

        # Generate new quests if conditions are right
        if self._should_generate_new_quest(game_state):
            new_quest = self._generate_quest_for_context(game_state)
            if new_quest:
                self.active_quests[new_quest.quest_id] = new_quest
                notifications.append(f"New quest available: '{new_quest.title}' from {new_quest.giver_npc_id}")
                self.total_quests_generated += 1
                self.last_generation_time = time.time()

        return notifications

    def _should_generate_new_quest(self, game_state: Any) -> bool:
        """Determine if a new quest should be generated."""
        # Check cooldown
        if time.time() - self.last_generation_time < self.quest_generation_cooldown:
            return False

        # Check if we have room for more quests
        if len(self.active_quests) >= self.max_active_quests:
            return False

        # Check if player seems engaged (has completed recent quests)
        recent_completions = len(
            [
                q
                for q in self.completed_quests.values()
                if q.completed_at and (time.time() - q.completed_at) < 86400  # Last 24 hours
            ]
        )

        # More likely to generate if player is active
        base_probability = 0.3 + (recent_completions * 0.1)

        return random.random() < base_probability

    def _generate_quest_for_context(self, game_state: Any) -> Optional[DynamicQuest]:
        """Generate a quest appropriate for the current game context."""
        context = self._build_generation_context(game_state)

        # Try each template in random order
        template_ids = list(self.templates.keys())
        random.shuffle(template_ids)

        for template_id in template_ids:
            template = self.templates[template_id]
            quest = template.generate_quest(context)
            if quest:
                return quest

        return None

    def _build_generation_context(self, game_state: Any) -> Dict[str, Any]:
        """Build context information for quest generation."""
        context = {}

        # Player information
        if hasattr(game_state, "player"):
            context["player_gold"] = getattr(game_state.player, "gold", 0)
            context["player_level"] = getattr(game_state.player, "level", 1)

        # World state
        context["world_state"] = {}
        if hasattr(game_state, "clock"):
            hour = game_state.clock.get_current_time().total_hours % 24
            context["world_state"]["is_daytime"] = 6 <= hour <= 20

        # Available NPCs
        context["available_npcs"] = []
        if hasattr(game_state, "npc_manager"):
            for npc_id, npc in game_state.npc_manager.npcs.items():
                context["available_npcs"].append(
                    {"id": npc_id, "name": npc.name, "profession": getattr(npc, "profession", "unknown")}
                )

        # Player reputation
        if hasattr(game_state, "reputation_network"):
            rep_summary = game_state.reputation_network.get_overall_reputation_summary()
            context["player_reputation"] = rep_summary["overall_score"]

        return context

    def process_player_action(self, action_description: str, game_state: Any) -> List[str]:
        """Process a player action and update relevant quests."""
        notifications = []

        for quest in self.active_quests.values():
            if quest.status == "active":
                if quest.update_objective_progress(action_description, game_state):
                    current_obj = quest.get_current_objective()
                    if current_obj and current_obj.completed:
                        notifications.append(f"Quest objective completed: {current_obj.description}")

                    if quest.status == "completed":
                        notifications.append(f"Quest completed: {quest.title}!")
                        self._complete_quest(quest, game_state)

                quest.adapt_to_player_behavior(action_description, True)

        return notifications

    def _complete_quest(self, quest: DynamicQuest, game_state: Any) -> None:
        """Handle quest completion, including rewards."""
        # Give rewards
        self._give_quest_rewards(quest, game_state)

        # Update statistics
        self.total_quests_completed += 1
        quest_type = quest.quest_type
        if quest_type in self.player_quest_preferences:
            self.player_quest_preferences[quest_type] += 0.1
        else:
            self.player_quest_preferences[quest_type] = 0.1

        # Move to completed quests
        self._move_to_completed(quest)

    def _give_quest_rewards(self, quest: DynamicQuest, game_state: Any) -> None:
        """Give the player rewards for completing a quest."""
        rewards = quest.rewards

        # Give gold
        if rewards.gold > 0 and hasattr(game_state, "player"):
            game_state.player.gold += rewards.gold

        # Give reputation boost
        if rewards.reputation_boost > 0 and hasattr(game_state, "reputation_network"):
            game_state.reputation_network.record_player_action(
                "quest_completion",
                "completed",
                [quest.giver_npc_id],
                {"quest_title": quest.title, "witnessed_directly": True},
            )

        # Give relationship boosts
        if rewards.relationship_boost and hasattr(game_state, "character_memory_manager"):
            for npc_id, boost in rewards.relationship_boost.items():
                if npc_id == "all_involved":
                    for involved_npc in quest.involved_npcs:
                        memory = game_state.character_memory_manager.get_memory(involved_npc)
                        if memory:
                            memory.improve_relationship(boost)
                else:
                    memory = game_state.character_memory_manager.get_memory(npc_id)
                    if memory:
                        memory.improve_relationship(boost)

    def _move_to_completed(self, quest: DynamicQuest) -> None:
        """Move a quest from active to completed."""
        if quest.quest_id in self.active_quests:
            del self.active_quests[quest.quest_id]
        self.completed_quests[quest.quest_id] = quest

    def get_available_quests(self) -> List[Dict[str, Any]]:
        """Get all quests available to the player."""
        return [quest.get_quest_summary() for quest in self.active_quests.values() if quest.status == "available"]

    def get_active_quests(self) -> List[Dict[str, Any]]:
        """Get all active quests."""
        return [quest.get_quest_summary() for quest in self.active_quests.values() if quest.status == "active"]

    def accept_quest(self, quest_id: str) -> bool:
        """Mark a quest as accepted by the player."""
        if quest_id in self.active_quests:
            quest = self.active_quests[quest_id]
            if quest.status == "available":
                quest.status = "active"
                quest.accepted_at = time.time()
                return True
        return False

    def get_generator_statistics(self) -> Dict[str, Any]:
        """Get statistics about the quest generator."""
        return {
            "total_generated": self.total_quests_generated,
            "total_completed": self.total_quests_completed,
            "active_quests": len(self.active_quests),
            "available_templates": len(self.templates),
            "completion_rate": (self.total_quests_completed / max(1, self.total_quests_generated)) * 100,
            "player_preferences": dict(self.player_quest_preferences),
            "most_popular_quest_type": max(
                self.player_quest_preferences.items(), key=lambda x: x[1], default=(None, 0)
            )[0],
        }
