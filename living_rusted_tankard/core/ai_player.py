"""
AI Player system for The Living Rusted Tankard.
Uses Ollama with gemma2:2b to create an autonomous character that players can watch.
"""

import asyncio
import json
import time
import random
from typing import Dict, Any, Optional, AsyncGenerator, List
import requests
import aiohttp
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

def get_available_ollama_models(ollama_url: str = "http://localhost:11434") -> List[str]:
    """Get list of available models from Ollama."""
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        return [model['name'] for model in data.get('models', [])]
    except Exception as e:
        logger.warning(f"Failed to get Ollama models: {e}")
        return ["gemma2:2b", "long-gemma"]  # Fallback defaults

class AIPlayerPersonality(Enum):
    CURIOUS_EXPLORER = "curious_explorer"
    CAUTIOUS_MERCHANT = "cautious_merchant" 
    SOCIAL_BUTTERFLY = "social_butterfly"
    MYSTERIOUS_WANDERER = "mysterious_wanderer"

@dataclass
class AIPlayerAction:
    command: str
    reasoning: str
    personality_trait: str
    timestamp: float

class AIPlayer:
    """An autonomous AI player that interacts with the game world."""
    
    def __init__(self, 
                 name: str = "Gemma",
                 personality: AIPlayerPersonality = AIPlayerPersonality.CURIOUS_EXPLORER,
                 ollama_url: str = "http://localhost:11434",
                 model: str = "gemma2:2b"):
        self.name = name
        self.personality = personality
        self.ollama_url = ollama_url
        
        # Validate model availability and set defaults
        available_models = get_available_ollama_models(ollama_url)
        if model in available_models:
            self.model = model
        elif "gemma2:2b" in available_models:
            self.model = "gemma2:2b"  # Default fallback
            logger.info(f"Requested model '{model}' not available, using gemma2:2b")
        elif available_models:
            self.model = available_models[0]  # Use first available
            logger.info(f"Using first available model: {self.model}")
        else:
            self.model = model  # Keep original if can't check
            logger.warning(f"Could not verify model availability, using: {model}")
        self.session_id = None
        self.action_history: List[AIPlayerAction] = []
        self.game_state = {}
        self.is_active = False
        self.thinking_delay = 2.0  # Seconds to "think" before acting
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Personality-based behavior patterns with VALID game commands
        self.personality_traits = {
            AIPlayerPersonality.CURIOUS_EXPLORER: {
                "preferred_commands": ["look", "read notice board", "interact", "jobs", "status", "inventory"],
                "interaction_style": "eager and inquisitive",
                "decision_pattern": "always chooses the most interesting option",
                "greeting": f"Hello! I'm {name}, a curious traveler always seeking new adventures!",
                "example_commands": [
                    "look",
                    "read notice board", 
                    "interact gene_bartender talk",
                    "jobs",
                    "accept bounty bounty_rats_001",
                    "inventory"
                ]
            },
            AIPlayerPersonality.CAUTIOUS_MERCHANT: {
                "preferred_commands": ["status", "inventory", "buy", "jobs", "work"],
                "interaction_style": "careful and business-minded", 
                "decision_pattern": "evaluates cost-benefit before acting",
                "greeting": f"Greetings. I am {name}, a merchant who values careful planning and good deals.",
                "example_commands": [
                    "status",
                    "inventory", 
                    "jobs",
                    "interact gene_bartender talk",
                    "buy ale",
                    "work clean_tables"
                ]
            },
            AIPlayerPersonality.SOCIAL_BUTTERFLY: {
                "preferred_commands": ["interact", "read notice board", "look", "jobs"],
                "interaction_style": "friendly and talkative",
                "decision_pattern": "prioritizes social interactions and relationships",
                "greeting": f"Hi there! I'm {name}! I love meeting new people and hearing their stories!",
                "example_commands": [
                    "interact gene_bartender talk",
                    "read notice board",
                    "look",
                    "jobs",
                    "help"
                ]
            },
            AIPlayerPersonality.MYSTERIOUS_WANDERER: {
                "preferred_commands": ["look", "wait", "status", "read notice board"],
                "interaction_style": "cryptic and thoughtful",
                "decision_pattern": "takes time to observe before acting",
                "greeting": f"I am {name}... a wanderer seeking truths hidden in shadow and flame.",
                "example_commands": [
                    "look",
                    "wait",
                    "status",
                    "read notice board",
                    "interact gene_bartender talk"
                ]
            }
        }
    
    def get_personality_context(self) -> str:
        """Get personality-specific context for LLM prompts."""
        traits = self.personality_traits[self.personality]
        return f"""
You are {self.name}, an AI character in The Living Rusted Tankard tavern game.

PERSONALITY: {self.personality.value}
- Style: {traits['interaction_style']}
- Decision Pattern: {traits['decision_pattern']}
- Preferred Actions: {', '.join(traits['preferred_commands'])}

CURRENT SITUATION:
- You are in a medieval fantasy tavern
- You can interact with NPCs, examine objects, buy items, etc.
- Your goal is to explore and engage with the world authentically
- Act naturally according to your personality

VALID GAME COMMANDS:
Use ONLY these exact command formats:
- "look" - Look around current room
- "status" - Check your status  
- "inventory" - Check your items
- "read notice board" - Read the notice board
- "interact gene_bartender talk" - Talk to Gene the bartender
- "interact <npc_id> talk" - Talk to NPCs (use their ID)
- "jobs" - See available work
- "work clean_tables" - Work cleaning tables job
- "work wash_dishes" - Work washing dishes job
- "buy <item>" - Buy items from vendors
- "accept bounty <bounty_id>" - Accept bounties from notice board
- "move <location>" - Move to different areas
- "help" - Get help with commands

EXAMPLE COMMANDS FOR YOUR PERSONALITY:
{chr(10).join(f'- "{cmd}"' for cmd in traits.get('example_commands', []))}

BEHAVIORAL GUIDELINES:
- Avoid repeating the same command consecutively
- After gathering information (jobs, bounties), take ACTION:
  * Accept a bounty with "accept bounty bounty_rats_001"
  * Try working with "work clean_tables" 
  * Talk to NPCs with "interact gene_bartender talk"
- Don't just observe - participate! Work jobs, accept bounties, talk to people
- Mix 2-3 information commands with 1-2 action commands
- Be decisive and try new things

RESPONSE FORMAT:
Respond with ONLY ONE valid command from the list above. Choose something different from your recent actions.
"""

    async def generate_action_stream(self, game_context: str) -> AsyncGenerator[str, None]:
        """Generate an action using LLM with streaming response and proper resource cleanup."""
        try:
            personality_context = self.get_personality_context()
            
            prompt = f"""{personality_context}

CURRENT GAME STATE:
{game_context}

RECENT ACTIONS:
{self._get_recent_actions_summary()}

What do you want to do next?"""

            # Get session with proper resource management
            session = await self._get_session()
            
            # Stream the LLM response using aiohttp with proper cleanup
            async with session.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "max_tokens": 50
                    }
                }
            ) as response:
                if response.status != 200:
                    yield "look around"
                    return
                
                generated_text = ""
                async for line in response.content:
                    if line:
                        try:
                            line_text = line.decode('utf-8').strip()
                            if line_text:
                                chunk = json.loads(line_text)
                                if 'response' in chunk:
                                    token = chunk['response']
                                    generated_text += token
                                    yield token
                                if chunk.get('done', False):
                                    break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                
                # Clean up the generated command
                if not generated_text.strip():
                    yield "look around"
                
        except Exception as e:
            logger.error(f"Error generating AI action: {e}")
            yield "look around"
    
    async def generate_action(self, game_context: str) -> str:
        """Generate a complete action using LLM with proper resource cleanup."""
        try:
            personality_context = self.get_personality_context()
            
            prompt = f"""{personality_context}

CURRENT GAME STATE:
{game_context}

RECENT ACTIONS:
{self._get_recent_actions_summary()}

What do you want to do next?"""

            # Get session with proper resource management
            session = await self._get_session()
            
            async with session.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "top_p": 0.9,
                        "max_tokens": 50
                    }
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    action = result.get('response', '').strip()
                    
                    # Clean up the action - remove quotes, extra text
                    action = action.replace('"', '').replace("'", '').strip()
                    
                    # Take only the first line if multiple lines
                    action = action.split('\n')[0].strip()
                    
                    if not action:
                        action = "look around"
                    
                    return action
                else:
                    logger.error(f"LLM request failed: {response.status}")
                    return "look around"
                
        except Exception as e:
            logger.error(f"Error generating AI action: {e}")
            return "look around"
    
    def _get_recent_actions_summary(self) -> str:
        """Get a summary of recent actions for context."""
        if not self.action_history:
            return "This is your first action in the tavern."
        
        recent = self.action_history[-3:]  # Last 3 actions
        summary = []
        for action in recent:
            summary.append(f"- {action.command} ({action.reasoning})")
        
        return "Recent actions:\n" + "\n".join(summary)
    
    def record_action(self, command: str, reasoning: str = ""):
        """Record an action taken by the AI player."""
        action = AIPlayerAction(
            command=command,
            reasoning=reasoning,
            personality_trait=self.personality.value,
            timestamp=time.time()
        )
        self.action_history.append(action)
        
        # Keep only last 10 actions
        if len(self.action_history) > 10:
            self.action_history = self.action_history[-10:]
    
    def update_game_state(self, new_state: Dict[str, Any]):
        """Update the AI player's understanding of the game state."""
        self.game_state = new_state
    
    def get_game_context(self) -> str:
        """Format current game state for LLM context."""
        if not self.game_state:
            return "You have just entered the tavern and are getting your bearings."
        
        context_parts = []
        
        # Time and location
        if 'formatted_time' in self.game_state:
            context_parts.append(f"Time: {self.game_state['formatted_time']}")
        if 'location' in self.game_state:
            context_parts.append(f"Location: {self.game_state['location']}")
        
        # Player status
        if 'player' in self.game_state:
            player = self.game_state['player']
            if 'gold' in player:
                context_parts.append(f"Your gold: {player['gold']}")
            if 'inventory' in player and player['inventory']:
                items = [item['name'] for item in player['inventory']]
                context_parts.append(f"Your items: {', '.join(items)}")
        
        # NPCs present
        if 'present_npcs' in self.game_state and self.game_state['present_npcs']:
            npcs = [npc['name'] for npc in self.game_state['present_npcs']]
            context_parts.append(f"People here: {', '.join(npcs)}")
        
        # Board notes
        if 'board_notes' in self.game_state and self.game_state['board_notes']:
            context_parts.append(f"Notice board has {len(self.game_state['board_notes'])} notices")
        
        return "\n".join(context_parts) if context_parts else "You are in the tavern."
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an HTTP session with proper resource management."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def close(self):
        """Clean up HTTP session resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.close()

# Global state removed - use AIPlayerManager for session management
# See ai_player_manager.py for proper session-based AI player management