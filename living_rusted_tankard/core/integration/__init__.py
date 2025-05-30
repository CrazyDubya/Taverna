"""
Master Integration Module

This module connects all phase implementations to the core game systems.
Without this integration, the phase work exists but doesn't affect gameplay.
"""

from .phase_integration import PhaseIntegration
from .game_state_enhanced import EnhancedGameState

__all__ = ['PhaseIntegration', 'EnhancedGameState']