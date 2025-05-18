"""LLM Parser for The Living Rusted Tankard."""
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Pattern, Callable, Union, Tuple

try:
    import requests
except ImportError:
    requests = None
    
from pydantic import BaseModel, Field

# Set up logging
logger = logging.getLogger(__name__)

# Type aliases
Command = Dict[str, Any]

@dataclass
class GameSnapshot:
    """Snapshot of the game state for the parser's context."""
    location: str
    time_of_day: str
    visible_objects: List[str]
    visible_npcs: List[str]
    player_state: Dict[str, Any]

class Command(BaseModel):
    """Structured representation of a parsed command."""
    action: str
    target: Optional[str] = None
    extras: Dict[str, Any] = Field(default_factory=dict)

class Parser:
    """Parser that uses LLM with regex fallback to understand player input."""
    
    def __init__(self, use_llm: bool = True, llm_endpoint: str = None):
        """Initialize the parser.
        
        Args:
            use_llm: Whether to use the LLM for parsing (falls back to regex if False or on error)
            llm_endpoint: URL of the LLM endpoint (if None, uses mock)
        """
        self.use_llm = use_llm
        self.llm_endpoint = llm_endpoint or os.getenv("LLM_ENDPOINT")
        self.compiled_patterns: List[tuple[Pattern, Callable]] = []
        self._load_patterns()
    
    def _load_patterns(self) -> None:
        """Load regex patterns for command parsing."""
        patterns = [
            # Look commands - handle both 'look' and 'look at something'
            (r'^look(?: around| at )?(?: the | at |)(.*)', self._handle_look),
            # Movement - handle 'go north', 'move to north', 'walk to north', or just 'north'
            (r'^(?:go(?: to)? |move to |walk to |)(north|south|east|west|up|down|in|out)', self._handle_movement),
            # Talk to NPC
            (r'^(?:talk to|speak to|chat with|ask) (.+)', self._handle_talk),
            # Default fallback
            (r'^(.+)$', self._handle_unknown)
        ]
        
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), handler)
            for pattern, handler in patterns
        ]
    
    def _handle_look(self, match: re.Match) -> Dict[str, Any]:
        """Handle look commands."""
        try:
            # If there's a group and it has content, use it as the target
            if match.groups() and match.group(1) and match.group(1).strip():
                target = match.group(1).strip()
            else:
                target = 'room'
            return {'action': 'look', 'target': target}
        except Exception as e:
            logger.error(f"Error in _handle_look: {e}")
            return {'action': 'error', 'target': str(e)}
    
    def _handle_movement(self, match: re.Match) -> Dict[str, Any]:
        """Handle movement commands."""
        try:
            direction = match.group(1).lower() if match.groups() else 'unknown'
            return {'action': 'go', 'target': direction}
        except Exception as e:
            logger.error(f"Error in _handle_movement: {e}")
            return {'action': 'error', 'target': str(e)}
    
    def _handle_talk(self, match: re.Match) -> Dict[str, Any]:
        """Handle talk commands."""
        return {'action': 'talk', 'target': match.group(1).strip()}
    
    def _handle_unknown(self, match: re.Match) -> Dict[str, Any]:
        """Handle unknown commands."""
        return {'action': 'unknown', 'target': match.group(0).strip()}
    
    def _parse_with_regex(self, text: str) -> Dict[str, Any]:
        """Parse input using regex patterns."""
        text = text.lower().strip()
        
        # Special case for empty input
        if not text:
            return {'action': 'help', 'target': None}
            
        # Try each pattern in order
        for pattern, handler in self.compiled_patterns:
            match = pattern.fullmatch(text)
            if match:
                return handler(match)
                
        # Should never get here due to catch-all pattern
        return {'action': 'unknown', 'target': text}
    
    def _parse_with_llm(self, text: str, game_state: GameSnapshot) -> Dict[str, Any]:
        """Parse input using the LLM."""
        if not self.llm_endpoint:
            logger.warning("No LLM endpoint configured, falling back to regex")
            return self._parse_with_regex(text)
            
        if requests is None:
            logger.warning("Requests module not available, falling back to regex")
            return self._parse_with_regex(text)
            
        try:
            # Prepare the prompt with game context
            prompt = f"""
            Current location: {game_state.location}
            Time: {game_state.time_of_day}
            Visible objects: {', '.join(game_state.visible_objects)}
            NPCs present: {', '.join(game_state.visible_npcs)}
            Player state: {game_state.player_state}
            
            Player says: "{text}"
            
            Parse the above into a JSON object with 'action' and optional 'target' and 'extras' fields.
            """.strip()
            
            # Call the LLM
            response = requests.post(
                self.llm_endpoint,
                json={"prompt": prompt},
                timeout=5  # 5 second timeout
            )
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            if 'response' in result:
                try:
                    # If the response is a string, parse it as JSON
                    if isinstance(result['response'], str):
                        return json.loads(result['response'])
                    return result['response']
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to parse LLM response: {e}")
                    return self._parse_with_regex(text)
            
            return self._parse_with_regex(text)
            
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return self._parse_with_regex(text)
    
    def parse(self, text: str, game_state: GameSnapshot) -> Dict[str, Any]:
        """Parse player input into a structured command.
        
        Args:
            text: The player's input text
            game_state: Current game state snapshot
            
        Returns:
            Dict with 'action', 'target', and 'extras' keys
        """
        try:
            if self.use_llm:
                return self._parse_with_llm(text, game_state)
            return self._parse_with_regex(text)
        except Exception as e:
            logger.error(f"Error in parse: {e}")
            return {'action': 'error', 'target': str(e)}


# Top-level function for backward compatibility
async def parse(
    input_text: str,
    game_state: Dict[str, Any],
    use_llm: bool = True,
) -> Dict[str, Any]:
    """Parse natural language input into a structured command.
    
    Args:
        input_text: Raw input text from the player
        game_state: Current game state including time, location, etc.
        use_llm: Whether to use the LLM for parsing (default: True)
        
    Returns:
        Dict with 'action', 'target', and 'extras' keys
    """
    if not input_text.strip():
        return {'action': 'help', 'target': None}
    
    try:
        parser = Parser(use_llm=use_llm)
        return parser.parse(input_text, GameSnapshot(**game_state))
    except Exception as e:
        logger.error(f"Error in parse: {e}")
        return {'action': 'error', 'target': str(e)}

def format_command_output(output: Dict[str, Any]) -> str:
    """Format a command output for display to the player."""
    if not output:
        return "No command generated."
    
    parts = [f"Command: {output.get('action')}"]
    if output.get('target'):
        parts.append(f"Target: {output['target']}")
    if output.get('extras'):
        parts.append(f"Extras: {output['extras']}")
    
    return " | ".join(parts)
