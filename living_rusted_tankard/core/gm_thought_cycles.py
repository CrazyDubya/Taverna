"""
Game Master Hidden Thought Cycles
Allows the GM to periodically collect thoughts and plan future events behind the scenes.
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import requests

logger = logging.getLogger(__name__)


class GMThoughtPriority(Enum):
    IMMEDIATE = "immediate"  # Respond to player actions
    IMPORTANT = "important"  # Major story/event planning
    BACKGROUND = "background"  # World building/atmosphere


@dataclass
class GMThought:
    """A thought or plan the GM is considering."""

    id: str
    priority: GMThoughtPriority
    content: str
    context: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    executed: bool = False
    planned_execution_time: Optional[float] = None


@dataclass
class GameContext:
    """Current game context for GM analysis."""

    player_actions: List[str]
    current_events: List[str]
    npc_states: Dict[str, Any]
    world_state: Dict[str, Any]
    player_progress: Dict[str, Any]
    time_in_game: float
    recent_player_behavior: str


class GMThoughtEngine:
    """Hidden GM system that thinks about the game state and plans events."""

    def __init__(
        self, llm_endpoint: str = "http://localhost:11434", model: str = "long-gemma", thought_interval: int = 30
    ):  # Think every 30 seconds
        self.llm_endpoint = llm_endpoint
        self.model = model
        self.thought_interval = thought_interval
        self.thoughts: List[GMThought] = []
        self.is_running = False
        self.last_thought_time = 0
        self._thought_task: Optional[asyncio.Task] = None

    async def start_thinking(self):
        """Start the GM's background thinking process."""
        if self.is_running:
            return

        self.is_running = True
        self._thought_task = asyncio.create_task(self._thinking_loop())
        logger.info("🧠 GM Hidden Thought Engine started")

    async def stop_thinking(self):
        """Stop the GM's thinking process."""
        self.is_running = False
        if self._thought_task:
            self._thought_task.cancel()
            try:
                await self._thought_task
            except asyncio.CancelledError:
                pass
        logger.info("🧠 GM Hidden Thought Engine stopped")

    async def _thinking_loop(self):
        """Main thinking loop that runs in background."""
        while self.is_running:
            try:
                await asyncio.sleep(self.thought_interval)
                if time.time() - self.last_thought_time >= self.thought_interval:
                    await self._execute_thought_cycle()
                    self.last_thought_time = time.time()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"GM thinking cycle error: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def _execute_thought_cycle(self):
        """Execute a single GM thought cycle."""
        logger.debug("🤔 GM executing hidden thought cycle...")

        # This would be called with current game context
        # For now, we'll create a mock context
        context = GameContext(
            player_actions=["look", "jobs", "read notice board"],
            current_events=["tavern_busy", "evening_crowd"],
            npc_states={"gene_bartender": {"mood": "friendly", "busy": False}},
            world_state={"time": "evening", "weather": "clear"},
            player_progress={"gold": 40, "completed_bounties": 0},
            time_in_game=120.0,
            recent_player_behavior="exploring_and_job_seeking",
        )

        thought = await self._generate_gm_thought(context)
        if thought:
            self.thoughts.append(thought)
            logger.debug(f"💭 GM thought: {thought.content[:100]}...")

            # Execute immediate thoughts
            if thought.priority == GMThoughtPriority.IMMEDIATE:
                await self._execute_thought(thought)

    async def _generate_gm_thought(self, context: GameContext) -> Optional[GMThought]:
        """Generate a GM thought based on current game context."""

        prompt = f"""You are the Game Master for "The Living Rusted Tankard" tavern game.
This is a HIDDEN thinking cycle - the player cannot see this.

CURRENT GAME SITUATION:
Recent Player Actions: {', '.join(context.player_actions[-5:])}
Player Behavior Pattern: {context.recent_player_behavior}
Game Time: {context.time_in_game} minutes
Current Events: {', '.join(context.current_events)}
Player Progress: {json.dumps(context.player_progress)}

NPC STATES:
{json.dumps(context.npc_states, indent=2)}

WORLD STATE:
{json.dumps(context.world_state, indent=2)}

🧠 GM THINKING GOALS:
1. Plan interesting events for the future
2. Consider how NPCs should react to player behavior
3. Think about story progression opportunities
4. Plan atmosphere changes or world events
5. Consider what the player might need or want

💭 THOUGHT TYPES:
- IMMEDIATE: React to recent player actions (spawn NPC, trigger event)
- IMPORTANT: Plan major story beats or character moments
- BACKGROUND: Develop world atmosphere, NPC personalities

Generate ONE specific, actionable thought as JSON:
{{
  "priority": "immediate|important|background",
  "content": "What you're thinking about doing",
  "action_type": "spawn_npc|trigger_event|modify_atmosphere|plan_story|update_npc",
  "details": {{"specific": "implementation details"}},
  "reasoning": "Why this is important now"
}}

Focus on making the world feel alive and responsive to the player."""

        try:
            response = requests.post(
                f"{self.llm_endpoint}/api/generate",
                json={"model": self.model, "prompt": prompt, "format": "json", "stream": False},
                timeout=20,
            )
            response.raise_for_status()
            result = response.json()

            thought_data = json.loads(result.get("response", "{}"))

            return GMThought(
                id=f"gm_thought_{time.time()}",
                priority=GMThoughtPriority(thought_data.get("priority", "background")),
                content=thought_data.get("content", "GM thinks about the game state"),
                context={
                    "action_type": thought_data.get("action_type"),
                    "details": thought_data.get("details", {}),
                    "reasoning": thought_data.get("reasoning"),
                    "game_context": context.__dict__,
                },
            )

        except Exception as e:
            logger.debug(f"GM thought generation failed: {e}")
            return None

    async def _execute_thought(self, thought: GMThought):
        """Execute a GM thought (trigger events, spawn NPCs, etc.)."""
        logger.info(f"🎭 GM executing thought: {thought.content}")

        action_type = thought.context.get("action_type")
        details = thought.context.get("details", {})

        # This would integrate with the actual game systems
        if action_type == "spawn_npc":
            logger.info(f"🔮 GM plans to spawn NPC: {details}")
        elif action_type == "trigger_event":
            logger.info(f"⚡ GM plans to trigger event: {details}")
        elif action_type == "modify_atmosphere":
            logger.info(f"🌟 GM plans atmosphere change: {details}")
        elif action_type == "plan_story":
            logger.info(f"📖 GM plans story development: {details}")
        elif action_type == "update_npc":
            logger.info(f"👥 GM plans NPC update: {details}")

        thought.executed = True

    def get_recent_thoughts(self, limit: int = 5) -> List[GMThought]:
        """Get the most recent GM thoughts."""
        return sorted(self.thoughts, key=lambda t: t.created_at, reverse=True)[:limit]

    def get_pending_thoughts(self) -> List[GMThought]:
        """Get thoughts that haven't been executed yet."""
        return [t for t in self.thoughts if not t.executed]

    def add_manual_thought(self, content: str, priority: GMThoughtPriority = GMThoughtPriority.BACKGROUND):
        """Manually add a thought for the GM to consider."""
        thought = GMThought(
            id=f"manual_{time.time()}",
            priority=priority,
            content=content,
            context={"manual": True, "created_by": "system"},
        )
        self.thoughts.append(thought)
        logger.info(f"💭 Manual GM thought added: {content}")


# Example integration note for game_state.py:
#
# class GameState:
#     def __init__(self, ...):
#         self.gm_thoughts = GMThoughtEngine()
#
#     async def start_gm_thinking(self):
#         await self.gm_thoughts.start_thinking()
#
#     def _provide_gm_context(self) -> GameContext:
#         return GameContext(
#             player_actions=self.recent_commands[-10:],
#             current_events=self.active_global_events,
#             npc_states={npc.id: npc.get_state() for npc in self.npc_manager.npcs},
#             world_state={
#                 'time': str(self.clock.get_current_time()),
#                 'location': self.room_manager.current_room.id
#             },
#             player_progress={
#                 'gold': self.player.gold,
#                 'energy': self.player.energy,
#                 'bounties': len(self.player.active_bounty_ids)
#             },
#             time_in_game=self.clock.get_current_time().total_hours,
#             recent_player_behavior=self._analyze_player_behavior()
#         )
