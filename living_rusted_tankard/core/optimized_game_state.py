"""
Performance-optimized GameState with integrated optimizations.

This extends the DatabaseGameState with performance optimizations for:
- Efficient NPC management with caching
- Selective snapshot creation
- Optimized event processing
- Memory usage optimization
"""
from typing import Dict, Any, Optional, List, Set
import time
import logging
from collections import deque

from .db_game_state import DatabaseGameState
from .performance_optimizations import PerformanceOptimizer, PerformanceMetrics

logger = logging.getLogger(__name__)

class OptimizedGameState(DatabaseGameState):
    """
    Performance-optimized GameState with built-in optimizations.
    
    This class extends DatabaseGameState with:
    - Cached NPC presence tracking
    - Selective snapshot generation
    - Optimized event processing
    - Performance monitoring
    """
    
    def __init__(self, data_dir: str = "data", session_id: Optional[str] = None, db_id: Optional[str] = None):
        """Initialize optimized game state."""
        # Initialize optimization components first
        self._performance_metrics = PerformanceMetrics()
        
        # Optimized NPC tracking
        self._present_npcs_cache: Dict[str, Any] = {}
        self._present_npcs_set: Set[str] = set()
        self._npc_cache_timestamp: float = 0.0
        self._npc_cache_ttl: float = 0.5  # 0.5 second cache
        
        # Optimized snapshot management
        self._snapshot_cache: Optional[Dict[str, Any]] = None
        self._snapshot_timestamp: float = 0.0
        self._snapshot_ttl: float = 1.0  # 1 second cache
        self._snapshot_dirty: bool = True
        
        # Event processing optimization
        self._event_batch: List[Dict[str, Any]] = []
        self._event_batch_size: int = 5
        self._last_event_process: float = 0.0
        
        # Now initialize parent (this will call _add_event)
        super().__init__(data_dir, session_id, db_id)
        
        # Performance optimization components (after parent init)
        self._performance_optimizer = PerformanceOptimizer(self)
        
        # Apply optimizations
        self._apply_optimizations()
        
        logger.debug("OptimizedGameState initialized with performance optimizations")
    
    def _apply_optimizations(self):
        """Apply all performance optimizations."""
        try:
            self._performance_optimizer.optimize_game_state()
            logger.debug("Performance optimizations applied successfully")
        except Exception as e:
            logger.error(f"Error applying performance optimizations: {e}")
    
    def update(self, delta_override: Optional[float] = None) -> None:
        """Optimized update method with performance tracking."""
        start_time = time.time()
        
        # Call parent update
        super().update(delta_override)
        
        # Process any pending events in batch
        self._process_event_batch()
        
        # Mark snapshot as dirty
        self._snapshot_dirty = True
        
        # Invalidate NPC cache
        self._invalidate_npc_cache()
        
        # Track performance
        self._performance_metrics.npc_update_time = time.time() - start_time
        
        self.mark_dirty()  # Mark for database save
    
    def get_present_npcs_optimized(self) -> List[Any]:
        """Get present NPCs with caching optimization."""
        current_time = time.time()
        
        # Check cache validity
        if (self._present_npcs_cache and 
            current_time - self._npc_cache_timestamp < self._npc_cache_ttl):
            self._performance_metrics.cache_hits += 1
            return list(self._present_npcs_cache.values())
        
        # Cache miss - rebuild cache
        self._performance_metrics.cache_misses += 1
        start_time = time.time()
        
        # Get fresh NPC data
        present_npcs = super()._present_npcs if hasattr(super(), '_present_npcs') else {}
        if not present_npcs and hasattr(self, 'npc_manager'):
            try:
                npcs_list = self.npc_manager.get_present_npcs()
                present_npcs = {npc.id: npc for npc in npcs_list}
            except Exception as e:
                logger.error(f"Error getting present NPCs: {e}")
                present_npcs = {}
        
        # Update cache
        self._present_npcs_cache = present_npcs.copy()
        self._present_npcs_set = set(present_npcs.keys())
        self._npc_cache_timestamp = current_time
        
        # Track performance
        self._performance_metrics.npc_update_time += time.time() - start_time
        
        return list(present_npcs.values())
    
    def is_npc_present(self, npc_id: str) -> bool:
        """Fast check if NPC is present using cached set."""
        current_time = time.time()
        
        # Update cache if needed
        if current_time - self._npc_cache_timestamp >= self._npc_cache_ttl:
            self.get_present_npcs_optimized()  # This updates the cache
        
        return npc_id in self._present_npcs_set
    
    def _invalidate_npc_cache(self):
        """Invalidate the NPC presence cache."""
        self._npc_cache_timestamp = 0.0
        self._present_npcs_cache.clear()
        self._present_npcs_set.clear()
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Get optimized game state snapshot with caching."""
        current_time = time.time()
        
        # Check cache validity
        if (not self._snapshot_dirty and 
            self._snapshot_cache and 
            current_time - self._snapshot_timestamp < self._snapshot_ttl):
            return self._snapshot_cache.copy()
        
        # Create new snapshot
        start_time = time.time()
        snapshot = self._create_optimized_snapshot()
        
        # Update cache
        self._snapshot_cache = snapshot
        self._snapshot_timestamp = current_time
        self._snapshot_dirty = False
        
        # Track performance
        self._performance_metrics.snapshot_time = time.time() - start_time
        
        return snapshot.copy()
    
    def _create_optimized_snapshot(self) -> Dict[str, Any]:
        """Create optimized snapshot with minimal data."""
        try:
            # Get basic snapshot from parent
            snapshot = super().get_state_snapshot() if hasattr(super(), 'get_state_snapshot') else {}
            
            # Optimize present NPCs data
            present_npcs = self.get_present_npcs_optimized()
            snapshot['present_npcs'] = [
                {
                    'id': npc.id,
                    'name': npc.name,
                    'description': npc.description[:100] if hasattr(npc, 'description') else ''
                }
                for npc in present_npcs[:10]  # Limit to 10 NPCs max
            ]
            
            # Optimize events (only recent, important ones)
            if hasattr(self, 'events') and self.events:
                recent_events = list(self.events)[-5:]  # Last 5 events only
                snapshot['recent_events'] = [
                    {
                        'type': event.event_type,
                        'message': event.message[:100]  # Truncate long messages
                    }
                    for event in recent_events
                    if event.event_type in ['success', 'error', 'warning', 'quest']
                ]
            
            # Add performance metrics
            snapshot['performance'] = {
                'cache_hit_rate': self._get_cache_hit_rate(),
                'optimizations_active': True
            }
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error creating optimized snapshot: {e}")
            return {'error': 'snapshot_creation_failed'}
    
    def _add_event(self, message: str, event_type: str = "info", data: Optional[Dict] = None) -> None:
        """Optimized event addition with batching."""
        # Call parent method for compatibility
        super()._add_event(message, event_type, data)
        
        # Add to batch for processing
        self._event_batch.append({
            'message': message,
            'type': event_type,
            'data': data or {},
            'timestamp': time.time()
        })
        
        # Process batch if full or enough time has passed
        current_time = time.time()
        if (len(self._event_batch) >= self._event_batch_size or 
            current_time - self._last_event_process > 1.0):  # 1 second
            self._process_event_batch()
    
    def _process_event_batch(self):
        """Process batched events efficiently."""
        if not self._event_batch:
            return
        
        start_time = time.time()
        
        # Group events by type for efficient processing
        npc_events = []
        important_events = []
        
        for event in self._event_batch:
            if 'npc' in event['type'].lower():
                npc_events.append(event)
            elif event['type'] in ['success', 'error', 'warning', 'quest']:
                important_events.append(event)
        
        # Process NPC events (invalidate cache if needed)
        if npc_events:
            self._invalidate_npc_cache()
            self._snapshot_dirty = True
        
        # Process important events (mark snapshot dirty)
        if important_events:
            self._snapshot_dirty = True
        
        # Clear batch
        self._event_batch.clear()
        self._last_event_process = time.time()
        
        # Track performance
        self._performance_metrics.event_processing_time += time.time() - start_time
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """Optimized command processing with performance tracking."""
        start_time = time.time()
        
        # Process command normally
        result = super().process_command(command)
        
        # Mark caches as potentially dirty
        self._snapshot_dirty = True
        
        # Process any pending events
        self._process_event_batch()
        
        # Add performance info to result if in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            result['performance'] = {
                'processing_time': time.time() - start_time,
                'cache_hit_rate': self._get_cache_hit_rate()
            }
        
        return result
    
    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate for performance monitoring."""
        total_requests = self._performance_metrics.cache_hits + self._performance_metrics.cache_misses
        if total_requests == 0:
            return 0.0
        return self._performance_metrics.cache_hits / total_requests
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        return {
            'cache_performance': {
                'hit_rate': self._get_cache_hit_rate(),
                'total_hits': self._performance_metrics.cache_hits,
                'total_misses': self._performance_metrics.cache_misses
            },
            'timing_metrics': {
                'npc_update_time': self._performance_metrics.npc_update_time,
                'snapshot_time': self._performance_metrics.snapshot_time,
                'event_processing_time': self._performance_metrics.event_processing_time
            },
            'cache_status': {
                'npc_cache_size': len(self._present_npcs_cache),
                'snapshot_cached': self._snapshot_cache is not None,
                'event_batch_size': len(self._event_batch)
            },
            'optimization_status': {
                'optimizations_applied': hasattr(self, '_performance_optimizer'),
                'cache_ttl': {
                    'npc_cache': self._npc_cache_ttl,
                    'snapshot_cache': self._snapshot_ttl
                }
            }
        }
    
    def reset_performance_metrics(self):
        """Reset performance metrics for fresh tracking."""
        self._performance_metrics.reset()
        logger.debug("Performance metrics reset")
    
    def optimize_memory_usage(self):
        """Optimize memory usage by clearing unnecessary caches."""
        # Clear old caches
        self._present_npcs_cache.clear()
        self._present_npcs_set.clear()
        self._snapshot_cache = None
        self._event_batch.clear()
        
        # Force garbage collection of weak references
        if hasattr(self, '_performance_optimizer'):
            # Clear optimizer caches
            self._performance_optimizer.metrics.reset()
        
        logger.debug("Memory usage optimized")

# Factory function for easy creation
def create_optimized_game_state(data_dir: str = "data", session_id: Optional[str] = None) -> OptimizedGameState:
    """Create an optimized game state instance."""
    return OptimizedGameState(data_dir=data_dir, session_id=session_id)

# Backwards compatibility
PerformanceGameState = OptimizedGameState