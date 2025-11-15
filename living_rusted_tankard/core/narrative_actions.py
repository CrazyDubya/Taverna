"""
Narrative Actions System for The Living Rusted Tankard.

This module handles the integration between narrative choices and game mechanics,
allowing story events to trigger quests, reputation changes, item transactions,
world events, and other game state modifications.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Types of narrative actions that can be triggered."""

    COMMAND = "COMMAND"  # Direct game command
    QUEST_START = "QUEST_START"  # Start a new quest
    QUEST_PROGRESS = "QUEST_PROGRESS"  # Progress existing quest
    QUEST_COMPLETE = "QUEST_COMPLETE"  # Complete quest
    REPUTATION = "REPUTATION"  # Change NPC reputation
    NPC_MOOD = "NPC_MOOD"  # Change NPC mood/attitude
    NPC_UNLOCK = "NPC_UNLOCK"  # Unlock new NPC dialogue options
    NPC_ACTION = "NPC_ACTION"  # Trigger NPC to perform action
    EVENT_TRIGGER = "EVENT_TRIGGER"  # Trigger world event
    ENVIRONMENT = "ENVIRONMENT"  # Change environment/location
    PRICE_CHANGE = "PRICE_CHANGE"  # Modify item prices
    ACCESS_GRANT = "ACCESS_GRANT"  # Grant access to areas/features
    ITEM_GIVE = "ITEM_GIVE"  # Give item to player
    ITEM_TAKE = "ITEM_TAKE"  # Take item from player
    STATUS_EFFECT = "STATUS_EFFECT"  # Apply status effect to player
    MEMORY = "MEMORY"  # Create memory (already handled)


@dataclass
class NarrativeAction:
    """Represents an action extracted from narrative text."""

    action_type: ActionType
    parameters: Dict[str, Any]
    raw_text: str


class NarrativeActionProcessor:
    """Processes narrative actions and applies them to game state."""

    def __init__(self):
        self.action_patterns = {
            ActionType.COMMAND: r"\[COMMAND:\s*([^\]]+)\]",
            ActionType.QUEST_START: r"\[QUEST_START:\s*([^\]]+)\]",
            ActionType.QUEST_PROGRESS: r"\[QUEST_PROGRESS:\s*([^\]]+)\]",
            ActionType.QUEST_COMPLETE: r"\[QUEST_COMPLETE:\s*([^\]]+)\]",
            ActionType.REPUTATION: r"\[REPUTATION:\s*([^\]]+)\]",
            ActionType.NPC_MOOD: r"\[NPC_MOOD:\s*([^\]]+)\]",
            ActionType.NPC_UNLOCK: r"\[NPC_UNLOCK:\s*([^\]]+)\]",
            ActionType.NPC_ACTION: r"\[NPC_ACTION:\s*([^\]]+)\]",
            ActionType.EVENT_TRIGGER: r"\[EVENT_TRIGGER:\s*([^\]]+)\]",
            ActionType.ENVIRONMENT: r"\[ENVIRONMENT:\s*([^\]]+)\]",
            ActionType.PRICE_CHANGE: r"\[PRICE_CHANGE:\s*([^\]]+)\]",
            ActionType.ACCESS_GRANT: r"\[ACCESS_GRANT:\s*([^\]]+)\]",
            ActionType.ITEM_GIVE: r"\[ITEM_GIVE:\s*([^\]]+)\]",
            ActionType.ITEM_TAKE: r"\[ITEM_TAKE:\s*([^\]]+)\]",
            ActionType.STATUS_EFFECT: r"\[STATUS_EFFECT:\s*([^\]]+)\]",
        }

    def extract_actions(self, text: str) -> List[NarrativeAction]:
        """Extract all narrative actions from text."""
        actions = []

        for action_type, pattern in self.action_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    parameters = self._parse_parameters(match)
                    actions.append(NarrativeAction(action_type=action_type, parameters=parameters, raw_text=match))
                except Exception as e:
                    logger.error(f"Error parsing action '{match}': {e}")

        return actions

    def _parse_parameters(self, param_string: str) -> Dict[str, Any]:
        """Parse parameter string into dictionary."""
        params = {}

        # Handle different parameter formats
        # Format 1: "quest_id param1=value1 param2=value2"
        # Format 2: "npc_name +10 reason=helped"
        # Format 3: "item_name quantity=2"

        parts = param_string.strip().split()
        if not parts:
            return params

        # First part is usually the main identifier
        params["target"] = parts[0]

        for part in parts[1:]:
            if "=" in part:
                # Key=value format
                key, value = part.split("=", 1)
                params[key] = self._convert_value(value)
            elif part.startswith("+") or part.startswith("-"):
                # Numeric modifier
                params["modifier"] = int(part)
            else:
                # Additional positional parameter
                if "extra" not in params:
                    params["extra"] = []
                params["extra"].append(part)

        return params

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        # Try to convert to number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Boolean values
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Return as string
        return value

    def clean_text(self, text: str) -> str:
        """Remove action tags from text while preserving formatting."""
        cleaned = text

        for pattern in self.action_patterns.values():
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # Clean up whitespace while preserving line breaks for options
        cleaned = re.sub(r"[ \t]+", " ", cleaned)  # Collapse horizontal whitespace
        cleaned = re.sub(r"\n\s*\n", "\n", cleaned)  # Remove empty lines
        cleaned = cleaned.strip()

        return cleaned

    def process_actions(self, actions: List[NarrativeAction], game_state, session_id: str) -> List[Dict[str, Any]]:
        """Process actions and apply them to game state."""
        results = []

        for action in actions:
            try:
                result = self._process_single_action(action, game_state, session_id)
                if result:
                    results.append(result)
                    logger.info(f"Processed action {action.action_type}: {action.raw_text}")
            except Exception as e:
                logger.error(f"Error processing action {action.action_type} '{action.raw_text}': {e}")

        return results

    def _process_single_action(self, action: NarrativeAction, game_state, session_id: str) -> Optional[Dict[str, Any]]:
        """Process a single narrative action."""

        if action.action_type == ActionType.COMMAND:
            # Execute game command directly
            command = action.parameters.get("target", "").strip()
            if command:
                return game_state.process_command(command)

        elif action.action_type == ActionType.QUEST_START:
            return self._handle_quest_start(action, game_state)

        elif action.action_type == ActionType.REPUTATION:
            return self._handle_reputation_change(action, game_state)

        elif action.action_type == ActionType.ITEM_GIVE:
            return self._handle_item_give(action, game_state)

        elif action.action_type == ActionType.EVENT_TRIGGER:
            return self._handle_event_trigger(action, game_state)

        # Add more action handlers as needed

        return None

    def _handle_quest_start(self, action: NarrativeAction, game_state) -> Dict[str, Any]:
        """Handle quest start action."""
        quest_id = action.parameters.get("target")
        description = action.parameters.get("description", "New quest started")

        # Add quest to player's quest log (if quest system exists)
        # For now, just add an event
        game_state._add_event(f"Quest started: {quest_id}", "quest")

        return {
            "success": True,
            "message": f"New quest: {description}",
            "action_type": "quest_start",
            "quest_id": quest_id,
        }

    def _handle_reputation_change(self, action: NarrativeAction, game_state) -> Dict[str, Any]:
        """Handle reputation change action."""
        npc_name = action.parameters.get("target")
        modifier = action.parameters.get("modifier", 0)
        reason = action.parameters.get("reason", "interaction")

        # For now, just log the reputation change
        # In the future, this could update an NPC relationship system
        game_state._add_event(f"Reputation with {npc_name}: {modifier:+d} ({reason})", "reputation")

        return {
            "success": True,
            "message": f"Reputation change with {npc_name}",
            "action_type": "reputation",
            "npc": npc_name,
            "change": modifier,
        }

    def _handle_item_give(self, action: NarrativeAction, game_state) -> Dict[str, Any]:
        """Handle giving item to player."""
        item_id = action.parameters.get("target")
        quantity = action.parameters.get("quantity", 1)
        reason = action.parameters.get("reason", "reward")

        # Try to add item to inventory
        success, message = game_state.player.inventory.add_item(item_id, quantity)

        if success:
            game_state._add_event(f"Received {quantity}x {item_id} ({reason})", "item_received")
            return {
                "success": True,
                "message": message,
                "action_type": "item_give",
                "item_id": item_id,
                "quantity": quantity,
            }
        else:
            return {"success": False, "message": f"Failed to give item: {message}", "action_type": "item_give"}

    def _handle_event_trigger(self, action: NarrativeAction, game_state) -> Dict[str, Any]:
        """Handle event trigger action."""
        event_name = action.parameters.get("target")
        action.parameters.get("delay", 0)

        # For now, just add an immediate event
        # In the future, this could schedule delayed events
        game_state._add_event(f"Event triggered: {event_name}", "event")

        return {
            "success": True,
            "message": f"Event '{event_name}' triggered",
            "action_type": "event_trigger",
            "event_name": event_name,
        }
