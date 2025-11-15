"""LLM-based command parser with regex fallback."""

import re
import json
import logging
from typing import Dict, Any, Optional, TypedDict, Literal
from dataclasses import dataclass
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Types
class Command(TypedDict):
    action: str
    target: Optional[str]
    extras: Dict[str, Any]


@dataclass
class GameSnapshot:
    """Current game state snapshot for context."""

    location: str
    time_of_day: str
    visible_objects: list[str]
    visible_npcs: list[str]
    player_state: Dict[str, Any]


class Parser:
    def __init__(self, use_llm: bool = True, llm_endpoint: str = "http://localhost:11434", model: str = "long-gemma"):
        self.use_llm = use_llm
        self.llm_endpoint = llm_endpoint
        self.llm_model = model  # Engine uses long-gemma by default

        # Define basic command patterns for fallback
        self.command_patterns = {
            "look": [
                (r"^look(?: at| around)?$", "look", "room"),
                (r"^look at (\w+)$", "look", None),
                (r"^examine (\w+)$", "examine", None),
            ],
            "go": [
                (r"^go to (\w+)$", "go", None),
                (r"^walk to (\w+)$", "go", None),
                (r"^enter (\w+)$", "enter", None),
            ],
            "talk": [
                (r"^talk to (\w+)$", "talk", None),
                (r"^speak with (\w+)$", "talk", None),
                (r"^ask (\w+) about (\w+)$", "ask", None),
            ],
            "interact": [
                (r"^take (\w+)$", "take", None),
                (r"^get (\w+)$", "take", None),
                (r"^use (\w+)(?: on (\w+))?$", "use", None),
            ],
            "meta": [
                (r"^inventory$", "inventory", None),
                (r"^help$", "help", None),
                (r"^quit$", "quit", None),
                (r"^exit$", "quit", None),
            ],
        }

    def parse(self, text: str, snapshot: GameSnapshot) -> Command:
        """
        Parse player input into a structured command.
        First tries LLM, falls back to regex.
        """
        if not text.strip():
            return self._create_command("wait")

        if self.use_llm:
            try:
                return self._parse_with_llm(text, snapshot)
            except Exception as e:
                logger.warning(f"LLM parsing failed: {e}. Falling back to regex.")

        return self._parse_with_regex(text)

    def _parse_with_llm(self, text: str, snapshot: GameSnapshot) -> Command:
        """Parse input using the Ollama LLM API."""
        prompt = self._build_llm_prompt(text, snapshot)

        try:
            logger.debug(f"Sending LLM request for: '{text}'")
            response = requests.post(
                f"{self.llm_endpoint}/api/generate",
                json={"model": self.llm_model, "prompt": prompt, "format": "json", "stream": False},
                timeout=45,  # Enhanced prompt needs more processing time
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"LLM raw response: {result}")

            # Parse the LLM response
            command_data = json.loads(result.get("response", "{}"))
            logger.debug(f"Parsed command data: {command_data}")
            return self._validate_command(command_data)

        except (requests.RequestException, json.JSONDecodeError) as e:
            logger.error(f"LLM API error for '{text}': {e}")
            logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
            raise Exception("Failed to parse with LLM") from e

    def _build_llm_prompt(self, text: str, snapshot: GameSnapshot) -> str:
        """Construct the enhanced prompt for the long-Gemma LLM with comprehensive context."""

        # Build NPC context
        npc_context = ""
        if snapshot.visible_npcs:
            npc_context = f"\nNPCs Present: {', '.join(snapshot.visible_npcs)}"
            npc_context += "\n  Available interactions: 'interact <npc_name> talk'"
        else:
            npc_context = "\nNPCs Present: None (try 'wait' or 'move' to find NPCs)"

        # Build inventory context
        inventory_context = ""
        if snapshot.visible_objects:
            inventory_context = f"\nPlayer Inventory: {', '.join(snapshot.visible_objects)}"
        else:
            inventory_context = "\nPlayer Inventory: Empty"

        # Build player state context
        player_context = f"""
Player Status:
  Gold: {snapshot.player_state.get('gold', 0)}
  Energy: {snapshot.player_state.get('energy', 100)}%
  Tiredness: {snapshot.player_state.get('tiredness', 0)}%"""

        return f"""You are the command parser for "The Living Rusted Tankard" medieval fantasy tavern game.

CURRENT GAME CONTEXT:
📍 Location: {snapshot.location}
🕰️ Time: {snapshot.time_of_day}
💰 Player Gold: {snapshot.player_state.get('gold', 0)}
⚡ Player Energy: {snapshot.player_state.get('energy', 100)}%{npc_context}{inventory_context}

PLAYER INPUT TO PARSE: "{text}"

COMMAND UNDERSTANDING RULES:
Your job is to translate natural language into precise game commands that the engine understands.

CORE COMMAND MAPPINGS:
🗣️ Social/Communication:
- "talk to [person]" / "speak with [person]" / "hey [person]" → "interact [person] talk"
- "ask [person] about [topic]" → "interact [person] talk" (with topic in extras)

🚶 Movement/Exploration:
- "go to [place]" / "move to [place]" / "head to [place]" / "walk to [place]" → "move [place]"
- "go [direction]" / "head [direction]" → "move [direction]"

👁️ Observation/Information:
- "look around" / "look" / "examine room" / "tell me about this place" → "look"
- "look at [object]" / "examine [object]" → "look [object]"
- "what time is it" / "check time" / "current time" → "status"
- "where am I" / "what's my location" → "look"

🎒 Inventory/Status:
- "check my inventory" / "what do I have" / "show inventory" → "inventory"
- "check my status" / "how am I doing" / "my condition" → "status"

💰 Commerce/Economics:
- "buy [item]" / "purchase [item]" / "I want to buy [item]" / "get me [item]" → "buy [item]"
- "what can I buy" / "show items" / "what's for sale" → "look" (contextual)

💼 Work/Jobs:
- "jobs" / "what work is available" / "show me jobs" / "I'm looking for work" → "jobs"
- "work [job_name]" / "do [job_name]" → "work [job_name]"

📋 Information Systems:
- "read notice board" / "check board" / "what's on the board" → "read notice board"
- "bounties" / "quests" / "missions" → "read notice board"

⏰ Time Management:
- "wait" / "pass time" / "rest a bit" → "wait"
- "wait [number]" / "wait [number] hours" → "wait [number]"
- "sleep" / "rest" / "take a nap" → "sleep"

❓ Help/Assistance:
- "help" / "commands" / "what can I do" / "how do I play" → "help"

CONTEXT-AWARE PARSING:
{f"🚫 No NPCs present - suggest 'wait' or 'move' for social commands" if not snapshot.visible_npcs else f"👥 NPCs available: {', '.join(snapshot.visible_npcs)}"}

RESPONSE FORMAT:
Return ONLY valid JSON in this exact format:
{{
    "action": "command_verb",
    "target": "target_object_or_person",
    "extras": {{"additional_parameters": "if_needed"}}
}}

CRITICAL EXAMPLES:
Input: "talk to the bartender" → {{"action": "interact", "target": "bartender", "extras": {{"interaction": "talk"}}}}
Input: "I want to buy some ale" → {{"action": "buy", "target": "ale", "extras": {{}}}}
Input: "what time is it?" → {{"action": "status", "target": "", "extras": {{}}}}
Input: "go upstairs" → {{"action": "move", "target": "upstairs", "extras": {{}}}}
Input: "check my inventory" → {{"action": "inventory", "target": "", "extras": {{}}}}
Input: "hey there, what's going on?" → {{"action": "look", "target": "", "extras": {{}}}}

Parse the player input with full understanding of context and intent."""

    def _parse_with_regex(self, text: str) -> Command:
        """Fallback to regex-based command parsing."""
        text = text.lower().strip()

        # Check each command category
        for category, patterns in self.command_patterns.items():
            for pattern, action, default_target in patterns:
                match = re.match(pattern, text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    target = groups[0] if groups and groups[0] else default_target
                    return self._create_command(action, target)

        # Default to a generic action if no pattern matches
        return self._create_command("unknown", text)

    def _create_command(self, action: str, target: Optional[str] = None, **extras) -> Command:
        """Create a properly formatted command dictionary."""
        return {"action": action, "target": target, "extras": extras or {}}

    def _validate_command(self, data: dict) -> Command:
        """Validate and normalize the command structure."""
        if not isinstance(data, dict):
            raise ValueError("Command must be a dictionary")

        action = str(data.get("action", "")).lower()
        if not action:
            raise ValueError("Command must have an 'action'")

        target = str(data["target"]).lower() if "target" in data and data["target"] is not None else None
        extras = {k: v for k, v in data.get("extras", {}).items() if v is not None}

        return self._create_command(action, target, **extras)


# Example usage
if __name__ == "__main__":
    # Test with a sample snapshot
    snapshot = GameSnapshot(
        location="tavern_main",
        time_of_day="evening",
        visible_objects=["bar", "tables", "door", "bulletin_board"],
        visible_npcs=["bartender", "merchant", "stranger"],
        player_state={"gold": 50, "has_room": False},
    )

    parser = Parser(use_llm=False)  # Test with regex fallback first

    test_inputs = [
        "look around",
        "go to the bar",
        "talk to the bartender",
        "ask about rumors",
        "take the key",
        "use key on door",
        "what time is it?",
    ]

    for text in test_inputs:
        command = parser.parse(text, snapshot)
        print(f"Input: {text}")
        print(f"  → {json.dumps(command, indent=2)}\n")
