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
    def __init__(self, use_llm: bool = True, llm_endpoint: str = "http://localhost:11434"):
        self.use_llm = use_llm
        self.llm_endpoint = llm_endpoint
        self.llm_model = "long-gemma"
        
        # Define basic command patterns for fallback
        self.command_patterns = {
            'look': [
                (r'^look(?: at| around)?$', 'look', 'room'),
                (r'^look at (\w+)$', 'look', None),
                (r'^examine (\w+)$', 'examine', None),
            ],
            'go': [
                (r'^go to (\w+)$', 'go', None),
                (r'^walk to (\w+)$', 'go', None),
                (r'^enter (\w+)$', 'enter', None),
            ],
            'talk': [
                (r'^talk to (\w+)$', 'talk', None),
                (r'^speak with (\w+)$', 'talk', None),
                (r'^ask (\w+) about (\w+)$', 'ask', None),
            ],
            'interact': [
                (r'^take (\w+)$', 'take', None),
                (r'^get (\w+)$', 'take', None),
                (r'^use (\w+)(?: on (\w+))?$', 'use', None),
            ],
            'meta': [
                (r'^inventory$', 'inventory', None),
                (r'^help$', 'help', None),
                (r'^quit$', 'quit', None),
                (r'^exit$', 'quit', None),
            ],
        }
    
    def parse(self, text: str, snapshot: GameSnapshot) -> Command:
        """
        Parse player input into a structured command.
        First tries LLM, falls back to regex.
        """
        if not text.strip():
            return self._create_command('wait')
        
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
            response = requests.post(
                f"{self.llm_endpoint}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False
                },
                timeout=1  # Reduce timeout to fail fast and avoid blocking
            )
            response.raise_for_status()
            result = response.json()
            
            # Parse the LLM response
            command_data = json.loads(result.get('response', '{}'))
            return self._validate_command(command_data)
            
        except (requests.RequestException, json.JSONDecodeError) as e:
            logger.error(f"LLM API error: {e}")
            raise Exception("Failed to parse with LLM") from e
    
    def _build_llm_prompt(self, text: str, snapshot: GameSnapshot) -> str:
        """Construct the prompt for the LLM."""
        return f"""
        Parse the following player input into a structured command.
        
        Current Location: {snapshot.location}
        Time: {snapshot.time_of_day}
        Visible Objects: {', '.join(snapshot.visible_objects)}
        Visible NPCs: {', '.join(snapshot.visible_npcs)}
        Player State: {json.dumps(snapshot.player_state, indent=2)}
        
        Input: "{text}"
        
        Respond with a JSON object containing:
        {{
            "action": "verb",  // one of: look, go, take, use, talk, ask, etc.
            "target": "noun",  // the primary target of the action
            "extras": {{}}      // any additional parameters
        }}
        
        Example 1:
        Input: "look at the bar"
        Response: {{"action": "look", "target": "bar", "extras": {{}}}}
        
        Example 2:
        Input: "ask the bartender about rumors"
        Response: {{"action": "ask", "target": "bartender", "extras": {{"topic": "rumors"}}}}
        
        Example 3:
        Input: "go to the door"
        Response: {{"action": "go", "target": "door", "extras": {{}}}}
        
        Now parse this input:
        "{text}"
        """
    
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
        return self._create_command('unknown', text)
    
    def _create_command(self, action: str, target: Optional[str] = None, **extras) -> Command:
        """Create a properly formatted command dictionary."""
        return {
            'action': action,
            'target': target,
            'extras': extras or {}
        }
    
    def _validate_command(self, data: dict) -> Command:
        """Validate and normalize the command structure."""
        if not isinstance(data, dict):
            raise ValueError("Command must be a dictionary")
        
        action = str(data.get('action', '')).lower()
        if not action:
            raise ValueError("Command must have an 'action'")
            
        target = str(data['target']).lower() if 'target' in data and data['target'] is not None else None
        extras = {k: v for k, v in data.get('extras', {}).items() if v is not None}
        
        return self._create_command(action, target, **extras)

# Example usage
if __name__ == "__main__":
    # Test with a sample snapshot
    snapshot = GameSnapshot(
        location="tavern_main",
        time_of_day="evening",
        visible_objects=["bar", "tables", "door", "bulletin_board"],
        visible_npcs=["bartender", "merchant", "stranger"],
        player_state={"gold": 50, "has_room": False}
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
