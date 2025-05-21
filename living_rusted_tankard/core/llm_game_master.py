"""
LLM Game Master for The Living Rusted Tankard.

This module implements an LLM-powered game master that can interpret
natural language inputs, convert them to game commands, and generate
rich narrative responses.
"""
import json
import logging
import os
import requests
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Number of recent messages to include in the conversation context
MAX_HISTORY_LENGTH = 10

@dataclass
class LLMChatMessage:
    """Represents a single message in the conversation history."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self) -> Dict[str, str]:
        """Convert to the format expected by Claude API."""
        return {"role": self.role, "content": self.content}


class LLMGameMaster:
    """LLM-powered game master for interpreting and responding to natural language inputs."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        """Initialize the LLM Game Master.
        
        Args:
            api_key: API key for Claude (or None to use environment variable)
            model: Model name to use
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("No ANTHROPIC_API_KEY provided or found in environment variables. LLM functionality will be limited.")
        
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.conversation_histories: Dict[str, List[LLMChatMessage]] = {}
        
        # Default system prompt
        self.system_prompt = self._get_default_system_prompt()
        
    def _get_default_system_prompt(self) -> str:
        """Create the default system prompt for the LLM."""
        return """
You are the Game Master for "The Living Rusted Tankard", a text-based fantasy RPG set in a medieval tavern.
Your role is to interpret player inputs, convert them to game commands when appropriate, and provide rich,
immersive responses that maintain the atmosphere of a cozy but slightly mysterious fantasy tavern.

The game has a specific set of commands that control game mechanics:
- look - Examine surroundings
- status - Check player status
- inventory - View carried items
- talk [npc] - Speak to an NPC
- buy [item] - Purchase an item
- use [item] - Use an item
- rest - Recover energy
- work - Find employment
- time - Check current time
- help - Show available commands

When a player inputs a message:
1. If their input clearly maps to a game command, execute it and enhance the response with narrative detail.
2. If their input is ambiguous, try to determine their intent and suggest appropriate game commands.
3. If their input is conversational, respond in character as a helpful tavern keeper or guide.
4. NEVER respond with just "I don't understand that command" - always provide guidance toward valid interactions.
5. Maintain the medieval fantasy atmosphere in all responses.
6. Keep your responses relatively concise (2-3 paragraphs maximum).

The game world centers around The Rusted Tankard, a lively tavern with:
- A main taproom with a bar, tables, and a fireplace
- Rooms available for rent upstairs
- A cellar with mysterious noises
- Various NPCs including Gene (bartender), Serena (waitress), and others
- A notice board with quests/bounties
- Rumors of strange happenings in the area

IMPORTANT: Your goal is to make the game fun and accessible even when the player doesn't use exact command syntax.
Help guide them toward the right commands without breaking immersion.
"""

    def _build_game_context(self, game_state) -> Dict[str, Any]:
        """Build a detailed context object from the current game state.
        
        Args:
            game_state: The current GameState object
            
        Returns:
            Dict containing relevant game context information
        """
        # Get information about present NPCs
        present_npcs = []
        if hasattr(game_state, 'npc_manager'):
            try:
                for npc in game_state.npc_manager.get_present_npcs():
                    present_npcs.append({
                        "id": npc.id,
                        "name": npc.name,
                        "description": npc.description
                    })
            except Exception as e:
                logger.error(f"Error getting present NPCs: {e}")
        
        # Get player inventory
        inventory = []
        if hasattr(game_state, 'player') and hasattr(game_state.player, 'inventory'):
            try:
                inventory_items = game_state.player.inventory.list_items_for_display()
                inventory = inventory_items if inventory_items else []
            except Exception as e:
                logger.error(f"Error getting inventory: {e}")
        
        # Format time
        try:
            time_str = game_state.clock.get_formatted_time()
        except:
            time_str = "Unknown time"
        
        # Create the context dictionary
        context = {
            "current_time": time_str,
            "player": {
                "gold": game_state.player.gold,
                "has_room": game_state.player.has_room,
                "tiredness": game_state.player.tiredness,
                "inventory": inventory
            },
            "present_npcs": present_npcs,
            "recent_events": [],
        }
        
        # Add recent events from game_state if available
        if hasattr(game_state, 'events'):
            try:
                recent_events = list(game_state.events)[-5:]
                context["recent_events"] = [
                    {"message": event.message, "type": event.event_type}
                    for event in recent_events
                ]
            except Exception as e:
                logger.error(f"Error getting recent events: {e}")
        
        return context

    def get_conversation_history(self, session_id: str) -> List[LLMChatMessage]:
        """Get the conversation history for a session.
        
        Args:
            session_id: The session ID to get history for
            
        Returns:
            List of LLMChatMessage objects
        """
        if session_id not in self.conversation_histories:
            self.conversation_histories[session_id] = []
        return self.conversation_histories[session_id]

    def add_to_history(self, session_id: str, message: LLMChatMessage) -> None:
        """Add a message to the conversation history.
        
        Args:
            session_id: The session ID to add history for
            message: The message to add
        """
        if session_id not in self.conversation_histories:
            self.conversation_histories[session_id] = []
        
        history = self.conversation_histories[session_id]
        history.append(message)
        
        # Trim history if it's too long
        if len(history) > MAX_HISTORY_LENGTH:
            self.conversation_histories[session_id] = history[-MAX_HISTORY_LENGTH:]

    def process_input(self, user_input: str, game_state, session_id: str) -> Tuple[str, Optional[str]]:
        """Process a user input using the LLM.
        
        Args:
            user_input: The user's input text
            game_state: The current GameState object
            session_id: The session ID for tracking conversation
            
        Returns:
            Tuple of (narrative_response, command_to_execute)
            The command_to_execute may be None if no specific command was identified
        """
        # Check if we have an API key before making any requests
        if not self.api_key:
            # Simple fallback when no API key is available
            if user_input.lower().strip() in ['help', '?']:
                return game_state._generate_help_text(), 'help'
            return "I need an API key to function properly. Please set the ANTHROPIC_API_KEY environment variable.", None
        
        # Build the context object with game state
        context = self._build_game_context(game_state)
        
        # Get the conversation history
        history = self.get_conversation_history(session_id)
        
        # Add the user's message to history
        self.add_to_history(
            session_id, 
            LLMChatMessage(role="user", content=user_input)
        )
        
        # Create a human-readable context string
        context_str = json.dumps(context, indent=2)
        
        # Add context and instructions to the system prompt
        enhanced_prompt = f"""
{self.system_prompt}

CURRENT GAME STATE:
{context_str}

Based on the user's input, determine if it maps to a specific game command. If so, include the command in your response
in the format: [COMMAND: command_name arg1 arg2] at the very beginning of your response.

For example, if the user says "I want to see what items I have", you would respond with:
[COMMAND: inventory] You check your belongings...

If the user says "Talk to the bartender", you would respond with:
[COMMAND: talk gene_bartender] You approach the bartender...

Only include a command if you're confident it matches the user's intent. Otherwise, provide a helpful response
that guides them toward valid commands without explicitly telling them what to type.
"""
        
        # Convert history to the format expected by Claude API
        formatted_history = [msg.to_dict() for msg in history[-MAX_HISTORY_LENGTH:]]
        
        try:
            # Generate a response from the LLM
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            data = {
                "model": self.model,
                "system": enhanced_prompt,
                "messages": formatted_history + [{"role": "user", "content": user_input}],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            llm_response = response.json()["content"][0]["text"]
            
            # Extract command if present
            command_to_execute = None
            narrative_response = llm_response
            
            # Check for command format [COMMAND: xyz]
            if "[COMMAND:" in llm_response:
                command_start = llm_response.find("[COMMAND:") + 9
                command_end = llm_response.find("]", command_start)
                if command_end > command_start:
                    command_to_execute = llm_response[command_start:command_end].strip()
                    # Remove the command part from the narrative response
                    narrative_response = llm_response[command_end + 1:].strip()
            
            # Add the assistant's response to history
            self.add_to_history(
                session_id, 
                LLMChatMessage(role="assistant", content=narrative_response)
            )
            
            return narrative_response, command_to_execute
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Fallback response
            return f"I'm having trouble processing your request. Please try again with a clearer command. Error: {str(e)}", None