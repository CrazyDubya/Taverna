"""
Enhanced LLM Game Master with improved error handling, context optimization, and graceful fallbacks.

This module extends the original LLM Game Master with:
- Robust error handling for network issues and timeouts
- Context optimization to avoid redundancy and reduce token usage
- Local-first approach with graceful fallbacks when LLM is unavailable
- Connection health monitoring and retry logic
- Context caching and intelligent context management
"""

import logging
import re
import requests
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading

from .narrative_actions import NarrativeActionProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
MAX_HISTORY_LENGTH = 10
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.0
CONTEXT_CACHE_TTL = 300  # 5 minutes
MAX_CONTEXT_SIZE = 2000  # characters


@dataclass
class LLMChatMessage:
    """Represents a single message in the conversation history."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: float = None
    token_count: Optional[int] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        # Rough token estimation (4 chars per token average)
        if self.token_count is None:
            self.token_count = len(self.content) // 4

    def to_dict(self) -> Dict[str, str]:
        """Convert to the format expected by the LLM API."""
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """Structured response from LLM with metadata."""

    content: str
    command: Optional[str] = None
    actions: List[Dict[str, Any]] = None
    was_fallback: bool = False
    response_time: float = 0.0
    token_usage: Optional[int] = None


class ConnectionHealthMonitor:
    """Monitor LLM service health and provide connection status."""

    def __init__(self, ollama_url: str, model: str):
        self.ollama_url = ollama_url
        self.model = model
        self.is_healthy = True
        self.last_check = 0
        self.consecutive_failures = 0
        self.check_interval = 60  # seconds
        self._lock = threading.Lock()

    def check_health(self) -> bool:
        """Check if the LLM service is healthy."""
        with self._lock:
            current_time = time.time()
            if current_time - self.last_check < self.check_interval:
                return self.is_healthy

            self.last_check = current_time
            try:
                # Quick health check
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                response.raise_for_status()

                # Check if our model is available
                tags_data = response.json()
                available_models = [model["name"] for model in tags_data.get("models", [])]
                model_available = any(self.model in model_name for model_name in available_models)

                if model_available:
                    self.is_healthy = True
                    self.consecutive_failures = 0
                    logger.debug(f"LLM health check passed - {self.model} available")
                else:
                    logger.warning(f"Model {self.model} not found in available models: {available_models}")
                    self.is_healthy = False

            except Exception as e:
                self.consecutive_failures += 1
                self.is_healthy = False
                logger.warning(f"LLM health check failed ({self.consecutive_failures} consecutive): {e}")

            return self.is_healthy


class ContextOptimizer:
    """Optimize context to reduce token usage while maintaining quality."""

    def __init__(self):
        self.context_cache = {}
        self.cache_timestamps = {}

    def optimize_context(self, context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Optimize context to reduce redundancy and token usage."""
        optimized = {}

        # Always include essential information
        optimized["current_time"] = context.get("current_time", "Unknown")

        # Optimize player information (only include changed/relevant data)
        player = context.get("player", {})
        optimized["player"] = {
            "gold": player.get("gold", 0),
            "has_room": player.get("has_room", False),
            "tiredness": f"{int(player.get('tiredness', 0) * 100)}%",
        }

        # Only include inventory if it has items
        inventory = player.get("inventory", [])
        if inventory:
            # Summarize inventory instead of full details
            optimized["player"]["inventory_summary"] = f"{len(inventory)} items"

        # Optimize NPC information (only present and relevant NPCs)
        present_npcs = context.get("present_npcs", [])
        if present_npcs:
            optimized["present_npcs"] = [
                {"name": npc["name"], "id": npc["id"]} for npc in present_npcs[:3]  # Limit to 3 most relevant
            ]

        # Only include recent, important events
        recent_events = context.get("recent_events", [])
        if recent_events:
            important_events = [
                event
                for event in recent_events[-3:]  # Last 3 events only
                if event.get("type") in ["success", "error", "quest", "warning"]
            ]
            if important_events:
                optimized["recent_events"] = important_events

        return optimized

    def get_context_summary(self, context: Dict[str, Any]) -> str:
        """Create a concise context summary string."""
        summary_parts = []

        # Time and location
        summary_parts.append(f"Time: {context.get('current_time', 'Unknown')}")

        # Player status
        player = context.get("player", {})
        gold = player.get("gold", 0)
        tiredness = player.get("tiredness", "0%")
        summary_parts.append(f"Player: {gold} gold, {tiredness} tired")

        # NPCs present
        npcs = context.get("present_npcs", [])
        if npcs:
            npc_names = [npc["name"] for npc in npcs[:2]]
            summary_parts.append(f"Present: {', '.join(npc_names)}")

        return " | ".join(summary_parts)


class EnhancedLLMGameMaster:
    """Enhanced LLM-powered game master with robust error handling and optimization."""

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "long-gemma:latest"):
        """Initialize the Enhanced LLM Game Master."""
        self.ollama_url = ollama_url
        self.model = model
        self.conversation_histories: Dict[str, List[LLMChatMessage]] = {}
        self.current_conversations: Dict[str, Dict[str, Any]] = {}
        self.session_memories: Dict[str, List[Dict[str, Any]]] = {}

        # Enhanced components
        self.health_monitor = ConnectionHealthMonitor(ollama_url, model)
        self.context_optimizer = ContextOptimizer()
        self.action_processor = NarrativeActionProcessor()

        # Configure robust HTTP session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # System prompt
        self.system_prompt = self._get_enhanced_system_prompt()

        # Fallback responses
        self.fallback_responses = self._initialize_fallback_responses()

        logger.info(f"Enhanced LLM Game Master initialized - {ollama_url} with {model}")

    def _get_enhanced_system_prompt(self) -> str:
        """Enhanced system prompt with better instructions."""
        return """You are the Game Master for "The Living Rusted Tankard", a text-based fantasy RPG.

CORE BEHAVIOR:
- Provide rich, immersive responses in 1-2 paragraphs
- Always suggest valid game actions when input is unclear
- Use action tags to integrate story with mechanics
- Maintain medieval fantasy atmosphere
- Never respond with just "I don't understand"

AVAILABLE COMMANDS: look, status, inventory, talk [npc], buy [item], use [item], rest, work, time, help

NARRATIVE ACTIONS (use these to trigger mechanics):
- [COMMAND: buy item_name] - Execute game commands
- [QUEST_START: quest_id description=text] - Begin quests
- [QUEST_PROGRESS: quest_id completion=X/Y] - Update progress
- [QUEST_COMPLETE: quest_id reward=amount] - Complete quests
- [REPUTATION: npc_id +/-value reason=text] - Change relationships
- [ITEM_GIVE: item_id quantity=X reason=text] - Give items
- [EVENT_TRIGGER: event_name delay=time] - Trigger events

CONVERSATION OPTIONS:
When talking to NPCs, always end with 3-5 numbered options in this format:
[Options: 1. Ask about local rumors 2. Order a drink 3. Inquire about rooms 4. Bid farewell]

Be concise but atmospheric. Focus on advancing the story and providing clear player choices."""

    def _initialize_fallback_responses(self) -> Dict[str, str]:
        """Initialize fallback responses for when LLM is unavailable."""
        return {
            "look": "You find yourself in the warm, dimly lit common room of The Rusted Tankard. The familiar crackle of the fireplace and murmur of conversation fills the air. Try 'status' to check your condition or 'talk' to interact with someone nearby.",
            "status": "You take a moment to assess your situation in the tavern. You can check your 'inventory', 'look' around, or 'talk' to someone nearby.",
            "inventory": "You check your belongings. Use 'buy [item]' to purchase something or 'use [item]' to use what you have.",
            "talk": "You look around for someone to talk to. The barkeeper is usually available, or you might find other patrons to chat with. Try 'talk barkeeper' or look around first.",
            "buy": "You consider making a purchase. The barkeeper offers various drinks and food. Try 'buy ale' or 'look' to see what's available.",
            "help": "Available commands: look, status, inventory, talk [person], buy [item], use [item], rest, work, time. The Rusted Tankard is your base - explore and interact!",
            "default": "The tavern atmosphere is welcoming despite the mysterious circumstances. Try 'help' for available commands, 'look' to examine your surroundings, or 'talk barkeeper' to get oriented.",
        }

    def is_service_available(self) -> bool:
        """Check if the LLM service is currently available."""
        return self.health_monitor.check_health()

    def get_fallback_response(
        self, user_input: str, session_id: str = None, game_context: Optional[Dict] = None
    ) -> LLMResponse:
        """Generate fallback response when LLM is unavailable using enhanced error recovery."""
        try:
            from .error_recovery import handle_llm_error

            # Create a simulated LLM unavailable error
            llm_error = Exception("LLM service unavailable")

            enhanced_response, command, actions = handle_llm_error(llm_error, session_id, user_input, game_context)

            return LLMResponse(content=enhanced_response, command=command, actions=actions or [], was_fallback=True)

        except ImportError:
            # Fallback to basic responses
            user_input_lower = user_input.lower().strip()

            # Try to match to a known command
            for command in ["look", "status", "inventory", "talk", "buy", "help"]:
                if command in user_input_lower:
                    response_text = self.fallback_responses.get(command, self.fallback_responses["default"])
                    return LLMResponse(
                        content=response_text,
                        command=command if command in ["look", "status", "inventory"] else None,
                        was_fallback=True,
                    )

            # Default fallback
            return LLMResponse(
                content=self.fallback_responses["default"]
                + f" (The mystical connection seems unstable - tried to interpret: '{user_input}')",
                was_fallback=True,
            )

    def _build_optimized_context(self, game_state, session_id: str) -> str:
        """Build optimized context string to reduce token usage."""
        try:
            # Build full context
            full_context = self._build_game_context(game_state)

            # Optimize context
            optimized_context = self.context_optimizer.optimize_context(full_context, session_id)

            # Convert to concise string
            context_summary = self.context_optimizer.get_context_summary(optimized_context)

            return f"GAME STATE: {context_summary}"

        except Exception as e:
            logger.error(f"Error building context: {e}")
            return "GAME STATE: Tavern environment active"

    def _build_game_context(self, game_state) -> Dict[str, Any]:
        """Build detailed context from game state (original method)."""
        present_npcs = []
        if hasattr(game_state, "npc_manager"):
            try:
                for npc in game_state.npc_manager.get_present_npcs():
                    present_npcs.append({"id": npc.id, "name": npc.name, "description": npc.description})
            except Exception as e:
                logger.error(f"Error getting present NPCs: {e}")

        inventory = []
        if hasattr(game_state, "player") and hasattr(game_state.player, "inventory"):
            try:
                inventory_items = game_state.player.inventory.list_items_for_display()
                inventory = inventory_items if inventory_items else []
            except Exception as e:
                logger.error(f"Error getting inventory: {e}")

        try:
            time_str = game_state.clock.get_formatted_time()
        except (AttributeError, TypeError) as e:
            logger.debug(f"Could not get formatted time: {e}")
            time_str = "Unknown time"

        context = {
            "current_time": time_str,
            "player": {
                "gold": getattr(game_state.player, "gold", 0),
                "has_room": getattr(game_state.player, "has_room", False),
                "tiredness": getattr(game_state.player, "tiredness", 0),
                "inventory": inventory,
            },
            "present_npcs": present_npcs,
            "recent_events": [],
        }

        if hasattr(game_state, "events"):
            try:
                recent_events = list(game_state.events)[-5:]
                context["recent_events"] = [
                    {"message": event.message, "type": event.event_type} for event in recent_events
                ]
            except Exception as e:
                logger.error(f"Error getting recent events: {e}")

        return context

    def process_input(
        self, user_input: str, game_state, session_id: str
    ) -> Tuple[str, Optional[str], List[Dict[str, Any]]]:
        """Process user input with enhanced error handling and fallbacks."""
        start_time = time.time()

        # Check service availability first
        if not self.is_service_available():
            logger.warning("LLM service unavailable, using fallback response")

            # Build game context for enhanced fallback
            game_context = {}
            try:
                from .time_display import get_time_context_for_llm

                game_context["current_time"] = get_time_context_for_llm(game_state.clock.current_time_hours)
                present_npcs = game_state.get_present_npcs()
                game_context["present_npcs"] = [npc.name for npc in present_npcs]
            except Exception:
                game_context = {"current_time": "evening", "present_npcs": []}

            fallback = self.get_fallback_response(user_input, session_id, game_context)
            return fallback.content, fallback.command, fallback.actions or []

        user_input.lower().strip()

        # Build optimized context
        context_str = self._build_optimized_context(game_state, session_id)

        # Get conversation history with optimization
        history = self.get_conversation_history(session_id)
        optimized_history = self._optimize_conversation_history(history)

        # Prepare messages
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add context
        messages.append({"role": "system", "content": context_str})

        # Add optimized conversation history
        messages.extend([msg.to_dict() for msg in optimized_history])

        # Add enhanced memory context
        try:
            from .memory import get_memory_context_for_llm

            memory_context = get_memory_context_for_llm(session_id, user_input)
            if memory_context:
                messages.append({"role": "system", "content": f"MEMORY: {memory_context}"})
        except ImportError:
            # Fallback to basic session memories
            if session_id in self.session_memories:
                recent_memories = self.session_memories[session_id][-3:]  # Last 3 memories
                if recent_memories:
                    memory_text = " | ".join([mem.get("content", "") for mem in recent_memories])
                    messages.append({"role": "system", "content": f"MEMORY: {memory_text}"})

        # Add current user input
        messages.append({"role": "user", "content": user_input})

        try:
            response = self._make_llm_request(messages, session_id)

            # Process successful response
            response.response_time = time.time() - start_time

            # Add to conversation history
            self.add_to_history(session_id, LLMChatMessage(role="user", content=user_input))
            self.add_to_history(session_id, LLMChatMessage(role="assistant", content=response.content))

            return response.content, response.command, response.actions or []

        except Exception as e:
            logger.error(f"LLM request failed: {e}", exc_info=True)

            # Intelligent fallback based on input with game context
            game_context = {}
            try:
                from .time_display import get_time_context_for_llm

                game_context["current_time"] = get_time_context_for_llm(game_state.clock.current_time_hours)
                present_npcs = game_state.get_present_npcs()
                game_context["present_npcs"] = [npc.name for npc in present_npcs]
            except Exception:
                game_context = {"current_time": "evening", "present_npcs": []}

            fallback = self.get_fallback_response(user_input, session_id, game_context)
            fallback.response_time = time.time() - start_time

            return fallback.content, fallback.command, fallback.actions or []

    def _make_llm_request(self, messages: List[Dict], session_id: str) -> LLMResponse:
        """Make request to LLM with robust error handling."""
        api_url = f"{self.ollama_url}/api/chat"

        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 400,  # Limit response length
            },
        }

        logger.debug(f"Making LLM request to {api_url}")

        try:
            response = self.session.post(api_url, json=data, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()

            response_data = response.json()

            if "message" not in response_data or "content" not in response_data["message"]:
                raise ValueError("Invalid response format from LLM")

            llm_response = response_data["message"]["content"]

            # Process response
            llm_response = self._extract_memories_from_response(llm_response, session_id)

            # Extract and process narrative actions
            actions = self.action_processor.extract_actions(llm_response)
            action_results = []
            if actions:
                # Note: In a real implementation, game_state would be passed here
                # action_results = self.action_processor.process_actions(actions, game_state, session_id)
                llm_response = self.action_processor.clean_text(llm_response)

            # Extract command if present
            command_to_execute = None
            if "[COMMAND:" in llm_response:
                command_start = llm_response.find("[COMMAND:") + 9
                command_end = llm_response.find("]", command_start)
                if command_end > command_start:
                    command_to_execute = llm_response[command_start:command_end].strip()
                    llm_response = llm_response[command_end + 1 :].strip()

            return LLMResponse(
                content=llm_response, command=command_to_execute, actions=action_results, was_fallback=False
            )

        except requests.Timeout:
            logger.error("LLM request timed out")
            raise Exception("Request timed out")
        except requests.ConnectionError:
            logger.error("Failed to connect to LLM service")
            raise Exception("Connection failed")
        except requests.HTTPError as e:
            logger.error(f"HTTP error from LLM service: {e}")
            raise Exception(f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in LLM request: {e}")
            raise

    def _optimize_conversation_history(self, history: List[LLMChatMessage]) -> List[LLMChatMessage]:
        """Optimize conversation history to reduce token usage."""
        if not history:
            return []

        # Keep recent important messages
        optimized = []
        total_tokens = 0
        max_tokens = 1000  # Token budget for history

        # Always include the most recent messages
        for msg in reversed(history[-MAX_HISTORY_LENGTH:]):
            if total_tokens + msg.token_count <= max_tokens:
                optimized.insert(0, msg)
                total_tokens += msg.token_count
            else:
                break

        return optimized

    def _extract_memories_from_response(self, response: str, session_id: str) -> str:
        """Extract and store memories from LLM response using enhanced memory system."""
        memory_pattern = r"\[MEMORY:\s*([^\]]+)\]"
        memories = re.findall(memory_pattern, response)

        if memories:
            try:
                from .memory import add_session_memory, MemoryImportance

                for memory in memories:
                    memory_content = memory.strip()

                    # Determine importance based on content keywords
                    importance = MemoryImportance.NORMAL
                    if any(
                        word in memory_content.lower()
                        for word in ["quest", "mission", "important", "secret", "discovery"]
                    ):
                        importance = MemoryImportance.HIGH
                    elif any(word in memory_content.lower() for word in ["greeting", "hello", "small talk"]):
                        importance = MemoryImportance.TRIVIAL
                    elif any(word in memory_content.lower() for word in ["buy", "purchase", "trade", "gold"]):
                        importance = MemoryImportance.LOW

                    # Add to enhanced memory system
                    add_session_memory(session_id, memory_content, importance)

            except ImportError:
                # Fallback to basic memory system
                if session_id not in self.session_memories:
                    self.session_memories[session_id] = []

                for memory in memories:
                    memory_entry = {"content": memory.strip(), "timestamp": time.time()}
                    self.session_memories[session_id].append(memory_entry)

                    # Limit memory storage
                    if len(self.session_memories[session_id]) > 20:
                        self.session_memories[session_id] = self.session_memories[session_id][-15:]

            # Remove memory tags from response
            response = re.sub(memory_pattern, "", response).strip()

        return response

    def get_conversation_history(self, session_id: str) -> List[LLMChatMessage]:
        """Get conversation history for a session."""
        if session_id not in self.conversation_histories:
            self.conversation_histories[session_id] = []
        return self.conversation_histories[session_id]

    def add_to_history(self, session_id: str, message: LLMChatMessage) -> None:
        """Add message to conversation history."""
        if session_id not in self.conversation_histories:
            self.conversation_histories[session_id] = []

        history = self.conversation_histories[session_id]
        history.append(message)

        # Trim history if too long
        if len(history) > MAX_HISTORY_LENGTH * 2:
            self.conversation_histories[session_id] = history[-MAX_HISTORY_LENGTH:]

    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status information."""
        return {
            "is_healthy": self.health_monitor.is_healthy,
            "consecutive_failures": self.health_monitor.consecutive_failures,
            "last_check": self.health_monitor.last_check,
            "model": self.model,
            "ollama_url": self.ollama_url,
        }


# Backwards compatibility
LLMGameMaster = EnhancedLLMGameMaster
