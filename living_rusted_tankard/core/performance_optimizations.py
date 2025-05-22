"""
Performance optimizations for The Living Rusted Tankard.

This module implements optimizations for:
1. NPC Management - Cached present NPCs set for faster lookups
2. Snapshot Efficiency - Selective snapshotting to reduce overhead
3. Event Processing - Optimized event handling patterns
4. Memory Management - Reduced object creation and garbage collection
"""
import time
import weakref
from typing import Dict, List, Set, Optional, Any, TYPE_CHECKING
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache

if TYPE_CHECKING:
    from .game_state import GameState
    from .npc import NPC

@dataclass
class PerformanceMetrics:
    """Track performance metrics for optimization monitoring."""
    npc_update_time: float = 0.0
    snapshot_time: float = 0.0
    event_processing_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def reset(self):
        """Reset all metrics."""
        self.npc_update_time = 0.0
        self.snapshot_time = 0.0
        self.event_processing_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0

class OptimizedNPCManager:
    """
    Optimized NPC management with cached present NPCs and efficient updates.
    """
    
    def __init__(self, game_state: 'GameState'):
        self.game_state = weakref.ref(game_state)
        self._present_npcs_cache: Dict[str, 'NPC'] = {}
        self._present_npcs_set: Set[str] = set()
        self._last_update_time: float = 0.0
        self._cache_valid: bool = False
        self._update_threshold: float = 0.1  # Update cache every 0.1 seconds minimum
        
    def get_present_npcs_optimized(self) -> Dict[str, 'NPC']:
        """Get present NPCs with optimized caching."""
        current_time = time.time()
        
        # Check if cache needs update
        if (not self._cache_valid or 
            current_time - self._last_update_time >= self._update_threshold):
            self._update_present_npcs_cache()
            self._last_update_time = current_time
            self._cache_valid = True
        
        return self._present_npcs_cache.copy()
    
    def get_present_npcs_set(self) -> Set[str]:
        """Get set of present NPC IDs for fast membership testing."""
        if not self._cache_valid:
            self._update_present_npcs_cache()
        return self._present_npcs_set.copy()
    
    def _update_present_npcs_cache(self):
        """Update the present NPCs cache efficiently."""
        gs = self.game_state()
        if not gs or not hasattr(gs, 'npc_manager'):
            return
        
        # Clear old cache
        self._present_npcs_cache.clear()
        self._present_npcs_set.clear()
        
        # Rebuild cache
        for npc in gs.npc_manager.get_present_npcs():
            self._present_npcs_cache[npc.id] = npc
            self._present_npcs_set.add(npc.id)
    
    def invalidate_cache(self):
        """Invalidate the present NPCs cache."""
        self._cache_valid = False
    
    def is_npc_present(self, npc_id: str) -> bool:
        """Fast check if NPC is present."""
        if not self._cache_valid:
            self._update_present_npcs_cache()
        return npc_id in self._present_npcs_set

class OptimizedSnapshotManager:
    """
    Optimized snapshot management with selective updates and caching.
    """
    
    def __init__(self, game_state: 'GameState'):
        self.game_state = weakref.ref(game_state)
        self._snapshot_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0.0
        self._cache_ttl: float = 1.0  # Cache snapshots for 1 second
        self._last_state_hash: Optional[str] = None
        
    def create_snapshot_optimized(self, force_update: bool = False) -> Dict[str, Any]:
        """Create optimized snapshot with caching."""
        current_time = time.time()
        
        # Check if cached snapshot is still valid
        if (not force_update and 
            self._snapshot_cache and 
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._snapshot_cache.copy()
        
        # Create new snapshot
        gs = self.game_state()
        if not gs:
            return {}
        
        start_time = time.time()
        snapshot = self._create_minimal_snapshot(gs)
        
        # Cache the snapshot
        self._snapshot_cache = snapshot
        self._cache_timestamp = current_time
        
        # Track performance
        if hasattr(gs, '_performance_metrics'):
            gs._performance_metrics.snapshot_time = time.time() - start_time
        
        return snapshot.copy()
    
    def _create_minimal_snapshot(self, game_state: 'GameState') -> Dict[str, Any]:
        """Create minimal snapshot with only essential data."""
        snapshot = {
            'timestamp': time.time(),
            'game_time': getattr(game_state.clock, 'current_time_hours', 0),
            'player': self._get_player_snapshot(game_state),
            'location': 'tavern',  # Simplified for now
        }
        
        # Only include NPCs if there are any present
        if hasattr(game_state, '_present_npcs') and game_state._present_npcs:
            snapshot['present_npcs'] = [
                {
                    'id': npc.id,
                    'name': npc.name,
                    'description': npc.description[:100]  # Truncate descriptions
                }
                for npc in game_state._present_npcs.values()
            ]
        else:
            snapshot['present_npcs'] = []
        
        return snapshot
    
    def _get_player_snapshot(self, game_state: 'GameState') -> Dict[str, Any]:
        """Get minimal player state snapshot."""
        player = game_state.player
        return {
            'gold': getattr(player, 'gold', 0),
            'has_room': getattr(player, 'has_room', False),
            'tiredness': round(getattr(player, 'tiredness', 0), 2),
            'item_count': len(getattr(player.inventory, 'items', {})) if hasattr(player, 'inventory') else 0
        }
    
    def invalidate_snapshot_cache(self):
        """Invalidate the snapshot cache."""
        self._snapshot_cache = None

class OptimizedEventProcessor:
    """
    Optimized event processing with batching and filtering.
    """
    
    def __init__(self, game_state: 'GameState'):
        self.game_state = weakref.ref(game_state)
        self._event_batch: List[Dict[str, Any]] = []
        self._batch_size: int = 10
        self._last_process_time: float = 0.0
        self._process_interval: float = 0.1  # Process events every 0.1 seconds
        
    def add_event_optimized(self, event_type: str, data: Dict[str, Any]):
        """Add event to optimized processing queue."""
        self._event_batch.append({
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        })
        
        # Process batch if it's full or enough time has passed
        current_time = time.time()
        if (len(self._event_batch) >= self._batch_size or 
            current_time - self._last_process_time >= self._process_interval):
            self._process_event_batch()
    
    def _process_event_batch(self):
        """Process batched events efficiently."""
        if not self._event_batch:
            return
        
        gs = self.game_state()
        if not gs:
            return
        
        start_time = time.time()
        
        # Group events by type for batch processing
        events_by_type = defaultdict(list)
        for event in self._event_batch:
            events_by_type[event['type']].append(event)
        
        # Process each event type in batch
        for event_type, events in events_by_type.items():
            self._process_event_type_batch(event_type, events)
        
        # Clear processed events
        self._event_batch.clear()
        self._last_process_time = time.time()
        
        # Track performance
        if hasattr(gs, '_performance_metrics'):
            gs._performance_metrics.event_processing_time = time.time() - start_time
    
    def _process_event_type_batch(self, event_type: str, events: List[Dict[str, Any]]):
        """Process a batch of events of the same type."""
        gs = self.game_state()
        if not gs:
            return
        
        # Different processing strategies for different event types
        if event_type == 'npc_presence_change':
            # Batch NPC presence updates
            for event in events:
                if hasattr(gs, 'optimized_npc_manager'):
                    gs.optimized_npc_manager.invalidate_cache()
        
        elif event_type == 'player_state_change':
            # Batch player state updates
            for event in events:
                if hasattr(gs, 'optimized_snapshot_manager'):
                    gs.optimized_snapshot_manager.invalidate_snapshot_cache()
        
        # Add other event types as needed

class PerformanceOptimizer:
    """
    Main performance optimizer that coordinates all optimizations.
    """
    
    def __init__(self, game_state: 'GameState'):
        self.game_state = weakref.ref(game_state)
        self.metrics = PerformanceMetrics()
        
        # Initialize optimized managers
        self.npc_manager = OptimizedNPCManager(game_state)
        self.snapshot_manager = OptimizedSnapshotManager(game_state)
        self.event_processor = OptimizedEventProcessor(game_state)
        
        # Optimization settings
        self.optimize_npc_updates = True
        self.optimize_snapshots = True
        self.optimize_events = True
        
    def optimize_game_state(self) -> Dict[str, Any]:
        """Apply all optimizations to the game state."""
        optimization_results = {
            'npcs_optimized': False,
            'snapshots_optimized': False,
            'events_optimized': False,
            'metrics': {}
        }
        
        gs = self.game_state()
        if not gs:
            return optimization_results
        
        try:
            # Optimize NPC management
            if self.optimize_npc_updates:
                self._optimize_npc_management(gs)
                optimization_results['npcs_optimized'] = True
            
            # Optimize snapshot creation
            if self.optimize_snapshots:
                self._optimize_snapshot_creation(gs)
                optimization_results['snapshots_optimized'] = True
            
            # Optimize event processing
            if self.optimize_events:
                self._optimize_event_processing(gs)
                optimization_results['events_optimized'] = True
            
            # Collect metrics
            optimization_results['metrics'] = {
                'npc_update_time': self.metrics.npc_update_time,
                'snapshot_time': self.metrics.snapshot_time,
                'event_processing_time': self.metrics.event_processing_time,
                'cache_hits': self.metrics.cache_hits,
                'cache_misses': self.metrics.cache_misses
            }
            
        except Exception as e:
            optimization_results['error'] = str(e)
        
        return optimization_results
    
    def _optimize_npc_management(self, game_state: 'GameState'):
        """Optimize NPC management."""
        # Add optimized NPC manager to game state
        if not hasattr(game_state, 'optimized_npc_manager'):
            game_state.optimized_npc_manager = self.npc_manager
        
        # Override frequently called methods with optimized versions
        original_get_present_npcs = game_state.npc_manager.get_present_npcs
        
        def optimized_get_present_npcs():
            present_npcs_dict = self.npc_manager.get_present_npcs_optimized()
            return list(present_npcs_dict.values())
        
        game_state.npc_manager.get_present_npcs = optimized_get_present_npcs
    
    def _optimize_snapshot_creation(self, game_state: 'GameState'):
        """Optimize snapshot creation."""
        if not hasattr(game_state, 'optimized_snapshot_manager'):
            game_state.optimized_snapshot_manager = self.snapshot_manager
        
        # Override get_snapshot method
        original_get_snapshot = getattr(game_state, 'get_snapshot', None)
        
        def optimized_get_snapshot():
            return self.snapshot_manager.create_snapshot_optimized()
        
        game_state.get_snapshot = optimized_get_snapshot
    
    def _optimize_event_processing(self, game_state: 'GameState'):
        """Optimize event processing."""
        if not hasattr(game_state, 'optimized_event_processor'):
            game_state.optimized_event_processor = self.event_processor
        
        # Override _add_event method
        original_add_event = getattr(game_state, '_add_event', None)
        
        def optimized_add_event(message: str, event_type: str = "info", data: Optional[Dict] = None):
            # Call original method for compatibility
            if original_add_event:
                original_add_event(message, event_type, data)
            
            # Add to optimized processor
            self.event_processor.add_event_optimized(event_type, data or {})
        
        game_state._add_event = optimized_add_event
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            'metrics': {
                'npc_update_time': self.metrics.npc_update_time,
                'snapshot_time': self.metrics.snapshot_time,
                'event_processing_time': self.metrics.event_processing_time,
                'cache_hits': self.metrics.cache_hits,
                'cache_misses': self.metrics.cache_misses,
                'cache_hit_rate': self.metrics.cache_hits / max(1, self.metrics.cache_hits + self.metrics.cache_misses)
            },
            'optimizations': {
                'npc_management': self.optimize_npc_updates,
                'snapshot_creation': self.optimize_snapshots,
                'event_processing': self.optimize_events
            },
            'memory_usage': self._get_memory_usage()
        }
    
    def _get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics."""
        gs = self.game_state()
        if not gs:
            return {}
        
        return {
            'present_npcs_cache_size': len(getattr(self.npc_manager, '_present_npcs_cache', {})),
            'snapshot_cache_size': 1 if getattr(self.snapshot_manager, '_snapshot_cache', None) else 0,
            'event_batch_size': len(getattr(self.event_processor, '_event_batch', [])),
            'total_npcs': len(getattr(gs.npc_manager, 'npcs', {})) if hasattr(gs, 'npc_manager') else 0,
            'total_events': len(getattr(gs, 'events', [])) if hasattr(gs, 'events') else 0
        }

# Utility functions for easy integration
def optimize_game_state(game_state: 'GameState') -> PerformanceOptimizer:
    """Create and apply performance optimizations to a game state."""
    optimizer = PerformanceOptimizer(game_state)
    optimizer.optimize_game_state()
    return optimizer

@lru_cache(maxsize=128)
def get_npc_interaction_cache(npc_id: str, interaction_type: str) -> str:
    """Cache NPC interaction results for faster lookups."""
    # This would be populated by the actual interaction system
    return f"cached_interaction_{npc_id}_{interaction_type}"