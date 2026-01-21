"""
GameState module - Refactored for better maintainability.

This module is being refactored from a single monolithic file into
smaller, focused modules. During the refactoring process, the original
GameState class remains in the parent directory.

TODO: Gradually migrate GameState functionality to these modules:
- player_manager.py: Player state, inventory, items
- npc_manager.py: NPC tracking, spawning, interactions  
- event_manager.py: Event processing, observers, updates
- world_manager.py: World state, atmosphere, areas
- persistence.py: Database, caching, snapshots

See README.md for full refactoring plan.
"""

# For now, import from parent to maintain backward compatibility
# This will be replaced as we migrate functionality

__all__ = []

# Future exports will be added here as modules are created
