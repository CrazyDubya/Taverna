"""
LLM Game Master for The Living Rusted Tankard.

This module implements an LLM-powered game master that can interpret
natural language inputs, convert them to game commands, and generate
rich narrative responses using Ollama's long-gemma model.
"""
import json
import logging
import os
import re
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
        """Convert to the format expected by the LLM API."""
        return {"role": self.role, "content": self.content}


class LLMGameMaster:
    """LLM-powered game master for interpreting and responding to natural language inputs."""

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "long-gemma:latest"):
        """Initialize the LLM Game Master using Ollama.
        
        Args:
            ollama_url: URL of the Ollama server
            model: Model name to use (default: long-gemma:latest)
        """
        self.ollama_url = ollama_url
        self.model = model
        self.conversation_histories: Dict[str, List[LLMChatMessage]] = {}
        self.current_conversations: Dict[str, Dict[str, Any]] = {}  # Track active conversations by session
        
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

CONVERSATION OPTIONS FEATURE:
When the player talks to an NPC, always end your response with 3-5 conversation options presented as a numbered list.
These should be short phrases (5-7 words each) that represent what the player might want to say next.
Format these at the end of your response like this:

[Options:
1. Ask about local rumors
2. Order a drink
3. Inquire about available rooms
4. Bid farewell]

The options should be contextually appropriate based on:
- Which NPC they're talking to (barkeep offers drinks, merchants offer goods, etc.)
- The current conversation topic
- The player's situation (do they have money, are they injured, etc.)
- Potential story hooks or quests that could be activated

The game world centers around The Rusted Tankard, a lively tavern with:
- A main taproom with a bar, tables, and a fireplace
- Rooms available for rent upstairs (2 gold per night)
- A cellar with mysterious noises
- Various NPCs including Old Tom (barkeeper), Sally (regular patron), and others
- A notice board with quests/bounties
- Rumors of strange happenings in the area

The tavern serves:
- Ale (1 gold)
- Mead (2 gold)
- Wine (3 gold)
- Stew of the day (2 gold)
- Bread and cheese (1 gold)
- Mystery meat pie (3 gold)

IMPORTANT: Your goal is to make the game fun and accessible even when the player doesn't use exact command syntax.
Help guide them toward the right commands without breaking immersion.

If the player's input appears to be selecting one of the conversation options you previously offered (they might use the number or repeat part of the option text), respond as if they chose that option.
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
        
        # If this is an assistant message that contains conversation options,
        # update the current conversation state
        if message.role == "assistant" and "[Options:" in message.content:
            self._update_conversation_state(session_id, message.content)
    
    def _update_conversation_state(self, session_id: str, content: str) -> None:
        """Update the conversation state with options provided by the LLM.
        
        Args:
            session_id: The session ID
            content: The message content
        """
        # Extract conversation options
        if "[Options:" not in content:
            return
            
        # Initialize conversation state for this session if it doesn't exist
        if session_id not in self.current_conversations:
            self.current_conversations[session_id] = {
                "talking_to": None,
                "options": [],
                "last_updated": time.time()
            }
            
        # Extract the options
        options_part = content.split("[Options:")[1]
        if "]" in options_part:
            options_part = options_part.split("]")[0]
            
        options = []
        for line in options_part.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
                
            # Extract option number and text
            if re.match(r"^\d+\.\s+", line):
                option_text = re.sub(r"^\d+\.\s+", "", line)
                options.append(option_text)
                
        # Update the conversation state
        self.current_conversations[session_id]["options"] = options
        self.current_conversations[session_id]["last_updated"] = time.time()
        
        # Try to determine who the player is talking to
        talking_to = None
        message_lower = content.lower()
        possible_npcs = ["old tom", "barkeep", "bartender", "sally", "patron"]
        
        for npc in possible_npcs:
            if npc in message_lower:
                talking_to = npc
                break
                
        if talking_to:
            self.current_conversations[session_id]["talking_to"] = talking_to

    def process_input(self, user_input: str, game_state, session_id: str) -> Tuple[str, Optional[str]]:
        """Process a user input using the Ollama LLM.
        
        Args:
            user_input: The user's input text
            game_state: The current GameState object
            session_id: The session ID for tracking conversation
            
        Returns:
            Tuple of (narrative_response, command_to_execute)
            The command_to_execute may be None if no specific command was identified
        """
        # Try simple command matching for basic commands
        user_input_lower = user_input.lower().strip()
        if user_input_lower in ['help', '?']:
            return game_state._generate_help_text(), 'help'
        elif user_input_lower in ['look', 'l']:
            # Provide more detailed description for basic look command
            tavern_description = """
            You find yourself in The Rusted Tankard, a warm and inviting tavern with weathered wooden beams overhead. 
            
            The main room is filled with sturdy oak tables and chairs, most occupied by locals and travelers alike. A large stone fireplace dominates one wall, casting flickering shadows across the room. The crackling fire provides both warmth and light, making the tavern feel cozy despite its size.
            
            To your right is the bar counter, polished smooth by years of use. Behind it stands Old Tom, the barkeep, arranging mugs and bottles. Several patrons lean against the counter, engaged in conversation or simply enjoying their drinks.
            
            On the far wall, you notice a wooden notice board covered with various papers - announcements, bounties, and job postings. Beside it, a narrow staircase leads to the upper floor where rooms are available for rent.
            
            The air is filled with the aroma of hearty stew, freshly baked bread, and the distinct smell of ale. The ambient noise is a pleasant mixture of conversation, occasional laughter, and the soft notes of someone strumming a lute in the corner.
            """
            return tavern_description.strip(), 'look'
        elif user_input_lower in ['inventory', 'i', 'inv']:
            return "Let me check what you're carrying...", 'inventory'
        elif user_input_lower in ['status', 'stats']:
            return "Let me tell you about your current condition...", 'status'
        elif user_input_lower in ['talk', 'speak']:
            # Handle talk command with no target
            npc_list = "You look around and see who you could talk to:\n\n"
            if hasattr(game_state, 'npc_manager'):
                present_npcs = game_state.npc_manager.get_present_npcs()
                if present_npcs:
                    for npc in present_npcs:
                        npc_list += f"- {npc.name}, {npc.description}\n"
                else:
                    npc_list += "There doesn't seem to be anyone interesting to talk to right now."
            else:
                npc_list += "- Old Tom, the barkeep with a mysterious past\n"
                npc_list += "- Sally, a regular patron who always seems to be here\n"
            
            return npc_list, 'talk'
        
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
        
        # Create the full prompt with system instructions, context, and history
        messages = []
        
        # Add system prompt as the first message
        messages.append({
            "role": "system", 
            "content": f"{self.system_prompt}\n\nCURRENT GAME STATE:\n{context_str}"
        })
        
        # Add conversation history
        for msg in history[-MAX_HISTORY_LENGTH:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Add the current user message
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Generate a response from Ollama
            api_url = f"{self.ollama_url}/api/chat"
            
            data = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            logger.info(f"Sending request to Ollama at {api_url}")
            response = requests.post(api_url, json=data)
            response.raise_for_status()
            
            logger.debug(f"Ollama response: {response.text}")
            response_data = response.json()
            
            if "message" in response_data and "content" in response_data["message"]:
                llm_response = response_data["message"]["content"]
            else:
                raise ValueError("Unexpected response format from Ollama")
            
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
            logger.error(f"Error generating Ollama response: {e}", exc_info=True)
            # Fallback response
            
            # If this was just a simple command we missed, try to guess it
            if len(user_input_lower.split()) <= 2:
                # Check for common command patterns
                if any(word in user_input_lower for word in ['talk', 'speak', 'chat']):
                    return "I think you want to talk to someone. You can use 'talk' followed by the person's name.", 'talk'
                elif any(word in user_input_lower for word in ['buy', 'purchase']):
                    return "I think you want to buy something. You can use 'buy' followed by the item name.", 'buy'
                elif any(word in user_input_lower for word in ['rest', 'sleep']):
                    return "I think you want to rest. You can use the 'rest' command.", 'rest'
            
            return f"I'm having trouble connecting to the Ollama server at {self.ollama_url}. Please ensure it's running with the {self.model} model. Try using a direct command like 'look' or 'inventory'.", None