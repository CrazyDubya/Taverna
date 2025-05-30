"""Core game systems for The Living Rusted Tankard - A tavern management text adventure."""

# Only import the modules that don't cause circular imports
from .clock import GameClock, GameTime
from .game_state import GameState
from .player import PlayerState
from .npc import NPC, NPCManager, NPCType
from .economy import Economy

# Define __all__ to control what's imported with `from core import *`
__all__ = [
    'GameClock', 
    'GameTime',
    'GameState',
    'PlayerState',
    'NPC',
    'NPCManager',
    'NPCType',
    'Economy'
]
