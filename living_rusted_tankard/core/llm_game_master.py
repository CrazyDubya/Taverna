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

from .narrative_actions import NarrativeActionProcessor

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
        self.session_memories: Dict[str, List[Dict[str, Any]]] = {}  # Track important information by session

        # Narrative action processor
        self.action_processor = NarrativeActionProcessor()

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
Format these at the end of your response like this (you can use either format):

Multi-line format:
[Options:
1. Ask about local rumors
2. Order a drink
3. Inquire about available rooms
4. Bid farewell]

OR single-line format:
[Options: 1. Ask about local rumors 2. Order a drink 3. Inquire about available rooms 4. Bid farewell]

NARRATIVE ACTION SYSTEM:
When story events should trigger game mechanics, use action tags to integrate narrative with gameplay.
Place these BEFORE your narrative response so mechanics execute first.

CORE ACTIONS:
- [COMMAND: buy old_toms_surprise] - Direct game commands (buy, sell, use, etc.)
- [QUEST_START: investigate_cellar description=Strange noises need investigation] - Start new quest
- [QUEST_PROGRESS: wolf_problem completion=3/5] - Update quest progress
- [QUEST_COMPLETE: missing_ale reward=50_gold] - Complete quest with reward
- [REPUTATION: old_tom +10 reason=helped_with_problem] - Change NPC reputation
- [ITEM_GIVE: healing_potion quantity=1 reason=reward] - Give item to player
- [EVENT_TRIGGER: tavern_celebration delay=1_hour] - Trigger world event
- [NPC_ACTION: serena approach_player reason=overheard_conversation] - NPC takes action

EXAMPLES:
Player accepts quest: [QUEST_START: find_missing_cat description=Find Mrs. Willow's missing cat]
Player helps NPC: [REPUTATION: old_tom +5 reason=bought_drinks] [ITEM_GIVE: discount_token reason=good_customer]
Player completes task: [QUEST_COMPLETE: rat_extermination reward=25_gold] [REPUTATION: barkeep +15 reason=solved_problem]

Use these to create meaningful consequences for player choices that go beyond just conversation.

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

The tavern serves (items available for purchase):
- Ale (2 gold) - house ale, provides happiness
- Stew (3 gold) - hearty meal, reduces hunger
- Bread (1 gold) - simple food, reduces hunger
- Cheese (3 gold) - dairy treat, small hunger reduction
- Whiskey (4 gold) - strong drink, provides courage
- Old Tom's Surprise (3 gold) - mysterious brew with special effects
- Mystery Brew (7 gold) - strange drink with unknown effects
- Healing Potion (25 gold) - restores health
- Traveler's Ration (12 gold) - boosts stamina for journeys

Special/Quest items may also be available from NPCs or special events.

WORKING WITH OBJECT FACTS:
When the player examines objects in the tavern, you'll be provided with key facts about those objects.
Your job is to creatively describe these objects using the facts as a foundation, but with your own unique
narrative style each time. Don't just repeat the facts - weave them into an evocative, atmospheric description.
The facts ensure consistency in the world, but your descriptions bring it to life differently each time.

EXAMPLE:
For this object fact:
{
  "material": "oak",
  "features": ["polished counter", "brass beer tap", "array of bottles", "hanging mugs"],
  "people": ["Old Tom (barkeep)"],
  "notable": "intricate carvings along the edge"
}

BAD RESPONSE (too literal):
"The bar is made of oak with a polished counter. It has a brass beer tap, array of bottles, and hanging mugs.
Old Tom is there. There are intricate carvings along the edge."

GOOD RESPONSE (creative but factually accurate):
"You approach the bar, running your fingers along the smooth oak surface. Years of spilled drinks and countless
elbows have given the counter a rich patina that gleams in the tavern's warm light. Behind it, Old Tom works
with practiced efficiency, drawing amber liquid from a worn brass tap. Your eyes are drawn to the edge of the
counter, where intricate carvings tell stories of heroes and monsters - some you recognize from local legends,
others mysterious and unknown. Overhead, mugs of various sizes hang from hooks, while an impressive collection
of bottles lines the shelves behind the bar, their contents ranging from common ales to exotic spirits."

BALANCE BETWEEN STRUCTURE AND CREATIVITY:
- The game engine tracks concrete game state (inventory, gold, location)
- You provide the narrative flavor, atmosphere, and storytelling
- When describing objects, use the provided facts as a foundation but be creative with details
- Conversations should be dynamic and responsive to player choices
- Try to maintain consistency with previous descriptions while adding fresh details

IMPORTANT: Your goal is to make the game fun and accessible even when the player doesn't use exact command syntax.
Help guide them toward the right commands without breaking immersion.

If the player's input appears to be selecting one of the conversation options you previously offered (they might use the number or repeat part of the option text), respond as if they chose that option.

MEMORY SYSTEM:
You have access to a memory system that tracks important information about the player's interactions and discoveries.
When something significant happens (new information about NPCs, quests accepted, items discovered, relationships formed),
automatically create memory entries by including [MEMORY: description] tags in your response.

Examples of what to remember:
- NPCs sharing personal information or secrets
- Quest details or objectives
- Important story revelations
- Player relationships or reputation changes
- Discoveries about the world or locations

Format: [MEMORY: Learned that Old Tom used to be an adventurer and has connections to mysterious happenings]

These memories will be included in future conversations to maintain consistency.
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
        if hasattr(game_state, "npc_manager"):
            try:
                for npc in game_state.npc_manager.get_present_npcs():
                    present_npcs.append({"id": npc.id, "name": npc.name, "description": npc.description})
            except Exception as e:
                logger.error(f"Error getting present NPCs: {e}")

        # Get player inventory
        inventory = []
        if hasattr(game_state, "player") and hasattr(game_state.player, "inventory"):
            try:
                inventory_items = game_state.player.inventory.list_items_for_display()
                inventory = inventory_items if inventory_items else []
            except Exception as e:
                logger.error(f"Error getting inventory: {e}")

        # Format time
        try:
            time_str = game_state.clock.get_formatted_time()
        except (AttributeError, ValueError) as e:
            logger.warning(f"Could not format time: {e}")
            time_str = "Unknown time"

        # Create the context dictionary
        context = {
            "current_time": time_str,
            "player": {
                "gold": game_state.player.gold,
                "has_room": game_state.player.has_room,
                "tiredness": game_state.player.tiredness,
                "inventory": inventory,
            },
            "present_npcs": present_npcs,
            "recent_events": [],
        }

        # Add recent events from game_state if available
        if hasattr(game_state, "events"):
            try:
                recent_events = list(game_state.events)[-5:]
                context["recent_events"] = [
                    {"message": event.message, "type": event.event_type} for event in recent_events
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
            self.current_conversations[session_id] = {"talking_to": None, "options": [], "last_updated": time.time()}

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

    def add_memory(self, session_id: str, memory_text: str) -> None:
        """Add a memory entry for a session.

        Args:
            session_id: The session ID
            memory_text: The memory to store
        """
        if session_id not in self.session_memories:
            self.session_memories[session_id] = []

        memory_entry = {
            "text": memory_text,
            "timestamp": time.time(),
            "importance": "normal",  # Could be extended to have different importance levels
        }

        self.session_memories[session_id].append(memory_entry)

        # Keep only the most recent 20 memories to avoid context bloat
        if len(self.session_memories[session_id]) > 20:
            self.session_memories[session_id] = self.session_memories[session_id][-20:]

        logger.info(f"Added memory for session {session_id}: {memory_text}")

    def get_memories(self, session_id: str) -> List[str]:
        """Get all memories for a session.

        Args:
            session_id: The session ID

        Returns:
            List of memory texts
        """
        if session_id not in self.session_memories:
            return []

        return [memory["text"] for memory in self.session_memories[session_id]]

    def _extract_memories_from_response(self, response: str, session_id: str) -> str:
        """Extract memory tags from LLM response and store them.

        Args:
            response: The LLM response text
            session_id: The session ID

        Returns:
            The response text with memory tags removed
        """
        # Look for [MEMORY: ...] tags
        import re

        memory_pattern = r"\[MEMORY:\s*([^\]]+)\]"
        memories = re.findall(memory_pattern, response, re.IGNORECASE)

        for memory in memories:
            self.add_memory(session_id, memory.strip())

        # Remove memory tags from the response
        cleaned_response = re.sub(memory_pattern, "", response, flags=re.IGNORECASE)

        # Clean up any double spaces left by removing tags, but preserve newlines for options formatting
        cleaned_response = re.sub(r"[ \t]+", " ", cleaned_response)  # Only collapse horizontal whitespace
        cleaned_response = re.sub(r"\n\s*\n", "\n", cleaned_response)  # Remove empty lines but keep structure
        cleaned_response = cleaned_response.strip()

        return cleaned_response

    def process_input(
        self, user_input: str, game_state, session_id: str
    ) -> Tuple[str, Optional[str], List[Dict[str, Any]]]:
        """Process a user input using the Ollama LLM.

        Args:
            user_input: The user's input text
            game_state: The current GameState object
            session_id: The session ID for tracking conversation

        Returns:
            Tuple of (narrative_response, command_to_execute, action_results)
            The command_to_execute may be None if no specific command was identified
            action_results contains the results of any narrative actions processed
        """
        # Try simple command matching for basic commands
        user_input_lower = user_input.lower().strip()
        if user_input_lower in ["help", "?"]:
            return game_state._generate_help_text(), "help", []
        elif user_input_lower in ["look", "l"]:
            # Provide more detailed description for basic look command
            tavern_description = """
            You find yourself in The Rusted Tankard, a warm and inviting tavern with weathered wooden beams overhead.

            The main room is filled with sturdy oak tables and chairs, most occupied by locals and travelers alike. A large stone fireplace dominates one wall, casting flickering shadows across the room. The crackling fire provides both warmth and light, making the tavern feel cozy despite its size.

            To your right is the bar counter, polished smooth by years of use. Behind it stands Old Tom, the barkeep, arranging mugs and bottles. Several patrons lean against the counter, engaged in conversation or simply enjoying their drinks.

            On the far wall, you notice a wooden notice board covered with various papers - announcements, bounties, and job postings. Beside it, a narrow staircase leads to the upper floor where rooms are available for rent.

            The air is filled with the aroma of hearty stew, freshly baked bread, and the distinct smell of ale. The ambient noise is a pleasant mixture of conversation, occasional laughter, and the soft notes of someone strumming a lute in the corner.
            """
            return tavern_description.strip(), "look", []
        elif user_input_lower.startswith("look ") or user_input_lower.startswith("examine "):
            # Handle looking at specific things
            target = user_input_lower.replace("look ", "").replace("examine ", "").strip()

            # Define key facts about tavern objects - enough to guide the LLM
            # but not so prescriptive that it limits creative freedom
            tavern_object_facts = {
                "bar": {
                    "material": "oak",
                    "features": ["polished counter", "brass beer tap", "array of bottles", "hanging mugs"],
                    "people": ["Old Tom (barkeep)"],
                    "notable": "intricate carvings along the edge",
                },
                "fireplace": {
                    "material": "river stone",
                    "features": ["large hearth", "crackling fire", "mantelpiece with trinkets"],
                    "notable": "rusty dagger mounted on a plaque above",
                },
                "notice board": {
                    "location": "near entrance",
                    "contents": [
                        'wanted poster for "Fingers Fenton" (50 gold)',
                        "notice about wolf problem from Farmer Giles",
                        "advertisement for Widow Tilda's bakery",
                        "request to investigate abandoned mine",
                        "mysterious note with strange symbol",
                    ],
                },
                "stairs": {
                    "material": "oak",
                    "features": ["creaky steps", "polished banister", "sign about room prices"],
                    "leads_to": "upper floor with rooms for rent",
                    "price": "2 gold per night",
                },
                "patrons": {
                    "groups": [
                        "farmers sharing stories",
                        "merchants in discussion",
                        "hooded figure drinking alone",
                        "young locals laughing",
                        "older couple by fireplace",
                    ]
                },
                "old tom": {
                    "appearance": "elderly man with gray hair and beard",
                    "clothing": "white shirt, dark vest, apron",
                    "role": "barkeep",
                    "notable": "efficiency of movement, set of keys on belt",
                },
                "sally": {
                    "appearance": "middle-aged woman with auburn hair in a bun",
                    "clothing": "forest green dress, woolen shawl",
                    "role": "regular patron, widow, farm owner",
                    "notable": "wooden bird pendant, knows everyone in town",
                },
            }

            # Check if we have facts for this target
            if target in tavern_object_facts:
                # Just pass the command to the LLM but include the object facts
                # in the context so it can generate a unique description based on them
                facts = tavern_object_facts[target]

                # Add these facts to the session's conversation context
                # This gives the LLM the core information without prescribing exact wording
                if session_id not in self.current_conversations:
                    self.current_conversations[session_id] = {}

                self.current_conversations[session_id]["examining_object"] = target
                self.current_conversations[session_id]["object_facts"] = facts

                # Let the LLM generate the description - we'll inject the facts into its context
                return None, None, []

            # For other targets, just let the LLM handle it directly
            return None, None, []

        elif user_input_lower in ["inventory", "i", "inv"]:
            return "Let me check what you're carrying...", "inventory", []
        elif user_input_lower in ["status", "stats"]:
            return "Let me tell you about your current condition...", "status", []
        elif user_input_lower in ["talk", "speak"]:
            # Handle talk command with no target
            npc_list = "You look around and see who you could talk to:\n\n"
            if hasattr(game_state, "npc_manager"):
                present_npcs = game_state.npc_manager.get_present_npcs()
                if present_npcs:
                    for npc in present_npcs:
                        npc_list += f"- {npc.name}, {npc.description}\n"
                else:
                    npc_list += "There doesn't seem to be anyone interesting to talk to right now."
            else:
                npc_list += "- Old Tom, the barkeep with a mysterious past\n"
                npc_list += "- Sally, a regular patron who always seems to be here\n"

            return npc_list, "talk", []

        # Build the context object with game state
        context = self._build_game_context(game_state)

        # Get the conversation history
        history = self.get_conversation_history(session_id)

        # Add the user's message to history
        self.add_to_history(session_id, LLMChatMessage(role="user", content=user_input))

        # Create a human-readable context string
        context_str = json.dumps(context, indent=2)

        # Check if the player is examining something specific
        examining_info = ""
        if session_id in self.current_conversations:
            session_context = self.current_conversations[session_id]
            if "examining_object" in session_context and "object_facts" in session_context:
                examining_object = session_context["examining_object"]
                object_facts = session_context["object_facts"]

                # Format the object facts as a string
                facts_str = json.dumps(object_facts, indent=2)
                examining_info = f"\n\nPLAYER IS EXAMINING: {examining_object}\nOBJECT FACTS:\n{facts_str}\n"

                # Clear the examining state after using it
                del session_context["examining_object"]
                del session_context["object_facts"]

        # Add memories to the context
        memories_info = ""
        memories = self.get_memories(session_id)
        if memories:
            memories_str = "\n".join([f"- {memory}" for memory in memories])
            memories_info = f"\n\nIMPORTANT MEMORIES FROM PREVIOUS INTERACTIONS:\n{memories_str}\n"

        # Add information about recent player input to help with command detection
        input_context = ""
        if user_input:
            # Check if this looks like a response to a purchase/transaction offer
            purchase_keywords = ["buy", "purchase", "take it", "i'll try it", "sounds good", "yes", "sure", "okay"]
            reject_keywords = ["no", "pass", "skip", "not interested", "too expensive"]

            user_lower = user_input.lower()

            if any(keyword in user_lower for keyword in purchase_keywords):
                input_context += f"\n\nNOTE: Player input '{user_input}' suggests they want to make a purchase or accept an offer. Consider if this should trigger a game command.\n"
            elif any(keyword in user_lower for keyword in reject_keywords):
                input_context += f"\n\nNOTE: Player input '{user_input}' suggests they are declining an offer.\n"

        # Create the full prompt with system instructions, context, and history
        messages = []

        # Add system prompt as the first message with context, examining info, memories, and input context
        messages.append(
            {
                "role": "system",
                "content": f"{self.system_prompt}\n\nCURRENT GAME STATE:\n{context_str}{examining_info}{memories_info}{input_context}",
            }
        )

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
                "options": {"temperature": 0.7, "top_p": 0.9},
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

            # Extract memories from the response first
            llm_response = self._extract_memories_from_response(llm_response, session_id)

            # Extract and process narrative actions
            actions = self.action_processor.extract_actions(llm_response)
            action_results = []
            if actions:
                action_results = self.action_processor.process_actions(actions, game_state, session_id)
                # Clean the response of action tags
                llm_response = self.action_processor.clean_text(llm_response)

            # Extract command if present (for backward compatibility)
            command_to_execute = None
            narrative_response = llm_response

            # Check for command format [COMMAND: xyz]
            if "[COMMAND:" in llm_response:
                command_start = llm_response.find("[COMMAND:") + 9
                command_end = llm_response.find("]", command_start)
                if command_end > command_start:
                    command_to_execute = llm_response[command_start:command_end].strip()
                    # Remove the command part from the narrative response
                    narrative_response = llm_response[command_end + 1 :].strip()

            # Also try to detect implied commands from examining objects
            # If we're examining an object with known facts, pass that info to the game engine
            elif session_id in self.current_conversations:
                session_context = self.current_conversations[session_id]
                if "examining_object" in session_context:
                    # Extract the command that was used to generate this response
                    examining_object = session_context.get("examining_object")
                    if examining_object:
                        command_to_execute = f"look {examining_object}"
                        # Don't modify the narrative response here - we want the LLM's rich description

            # Add the assistant's response to history
            self.add_to_history(session_id, LLMChatMessage(role="assistant", content=narrative_response))

            return narrative_response, command_to_execute, action_results

        except Exception as e:
            logger.error(f"Error generating Ollama response: {e}", exc_info=True)
            # Fallback response

            # If this was just a simple command we missed, try to guess it
            if len(user_input_lower.split()) <= 2:
                # Check for common command patterns
                if any(word in user_input_lower for word in ["talk", "speak", "chat"]):
                    return (
                        "I think you want to talk to someone. You can use 'talk' followed by the person's name.",
                        "talk",
                        [],
                    )
                elif any(word in user_input_lower for word in ["buy", "purchase"]):
                    return "I think you want to buy something. You can use 'buy' followed by the item name.", "buy", []
                elif any(word in user_input_lower for word in ["rest", "sleep"]):
                    return "I think you want to rest. You can use the 'rest' command.", "rest", []

            return (
                f"I'm having trouble connecting to the Ollama server at {self.ollama_url}. Please ensure it's running with the {self.model} model. Try using a direct command like 'look' or 'inventory'.",
                None,
                [],
            )
