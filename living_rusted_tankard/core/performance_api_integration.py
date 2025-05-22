"""
API integration for performance optimizations.

This module provides endpoints and utilities for monitoring and managing
performance optimizations in the game system.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import time
import logging

from .optimized_game_state import OptimizedGameState

logger = logging.getLogger(__name__)

# Create router for performance endpoints
performance_router = APIRouter(prefix="/performance", tags=["performance"])

# Store performance-enabled sessions
optimized_sessions: Dict[str, OptimizedGameState] = {}

@performance_router.get("/metrics/{session_id}")
async def get_performance_metrics(session_id: str) -> Dict[str, Any]:
    """Get performance metrics for a specific session."""
    if session_id not in optimized_sessions:
        raise HTTPException(status_code=404, detail="Session not found or not optimized")
    
    game_state = optimized_sessions[session_id]
    return game_state.get_performance_metrics()

@performance_router.post("/optimize/{session_id}")
async def enable_optimizations(session_id: str) -> Dict[str, Any]:
    """Enable performance optimizations for a session."""
    # This would typically convert an existing session to optimized
    # For now, we'll create a new optimized session
    try:
        optimized_game_state = OptimizedGameState(session_id=session_id)
        optimized_sessions[session_id] = optimized_game_state
        
        return {
            "status": "success",
            "message": "Performance optimizations enabled",
            "session_id": session_id,
            "optimizations": [
                "NPC caching",
                "Snapshot optimization", 
                "Event batching",
                "Memory optimization"
            ]
        }
    except Exception as e:
        logger.error(f"Error enabling optimizations for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enable optimizations: {str(e)}")

@performance_router.delete("/optimize/{session_id}")
async def disable_optimizations(session_id: str) -> Dict[str, Any]:
    """Disable performance optimizations for a session."""
    if session_id in optimized_sessions:
        # Clean up optimized session
        game_state = optimized_sessions[session_id]
        game_state.optimize_memory_usage()
        del optimized_sessions[session_id]
        
        return {
            "status": "success",
            "message": "Performance optimizations disabled",
            "session_id": session_id
        }
    else:
        raise HTTPException(status_code=404, detail="Optimized session not found")

@performance_router.get("/status")
async def get_performance_status() -> Dict[str, Any]:
    """Get overall performance optimization status."""
    total_optimized = len(optimized_sessions)
    
    # Aggregate metrics from all optimized sessions
    total_cache_hits = 0
    total_cache_misses = 0
    avg_cache_hit_rate = 0.0
    
    if total_optimized > 0:
        hit_rates = []
        for game_state in optimized_sessions.values():
            try:
                metrics = game_state.get_performance_metrics()
                cache_perf = metrics.get("cache_performance", {})
                total_cache_hits += cache_perf.get("total_hits", 0)
                total_cache_misses += cache_perf.get("total_misses", 0)
                hit_rates.append(cache_perf.get("hit_rate", 0.0))
            except Exception as e:
                logger.warning(f"Error getting metrics from session: {e}")
        
        if hit_rates:
            avg_cache_hit_rate = sum(hit_rates) / len(hit_rates)
    
    return {
        "total_optimized_sessions": total_optimized,
        "aggregate_metrics": {
            "total_cache_hits": total_cache_hits,
            "total_cache_misses": total_cache_misses,
            "average_cache_hit_rate": avg_cache_hit_rate
        },
        "optimization_features": [
            "NPC presence caching",
            "Selective snapshot generation",
            "Batched event processing",
            "Memory usage optimization"
        ]
    }

@performance_router.post("/benchmark")
async def run_performance_benchmark() -> Dict[str, Any]:
    """Run a performance benchmark comparing optimized vs non-optimized operations."""
    try:
        # Create test instances
        optimized_gs = OptimizedGameState()
        
        # Benchmark snapshot creation
        snapshot_times = []
        for i in range(10):
            start_time = time.time()
            _ = optimized_gs.get_snapshot()
            snapshot_times.append(time.time() - start_time)
        
        # Benchmark NPC operations
        npc_times = []
        for i in range(20):
            start_time = time.time()
            _ = optimized_gs.get_present_npcs_optimized()
            npc_times.append(time.time() - start_time)
        
        # Clean up
        optimized_gs.optimize_memory_usage()
        
        return {
            "benchmark_results": {
                "snapshot_operations": {
                    "average_time_ms": sum(snapshot_times) / len(snapshot_times) * 1000,
                    "min_time_ms": min(snapshot_times) * 1000,
                    "max_time_ms": max(snapshot_times) * 1000,
                    "total_operations": len(snapshot_times)
                },
                "npc_operations": {
                    "average_time_ms": sum(npc_times) / len(npc_times) * 1000,
                    "min_time_ms": min(npc_times) * 1000,
                    "max_time_ms": max(npc_times) * 1000,
                    "total_operations": len(npc_times)
                }
            },
            "test_timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error running performance benchmark: {e}")
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")

@performance_router.post("/memory/optimize")
async def optimize_all_memory() -> Dict[str, Any]:
    """Optimize memory usage for all optimized sessions."""
    optimized_count = 0
    errors = []
    
    for session_id, game_state in optimized_sessions.items():
        try:
            game_state.optimize_memory_usage()
            optimized_count += 1
        except Exception as e:
            errors.append(f"Session {session_id}: {str(e)}")
    
    return {
        "status": "completed",
        "optimized_sessions": optimized_count,
        "total_sessions": len(optimized_sessions),
        "errors": errors
    }

# Utility functions for integration
def get_optimized_game_state(session_id: str) -> Optional[OptimizedGameState]:
    """Get optimized game state for a session if it exists."""
    return optimized_sessions.get(session_id)

def create_optimized_session(session_id: str, data_dir: str = "data") -> OptimizedGameState:
    """Create and register an optimized game state session."""
    game_state = OptimizedGameState(data_dir=data_dir, session_id=session_id)
    optimized_sessions[session_id] = game_state
    return game_state

def cleanup_optimized_sessions():
    """Clean up all optimized sessions and free memory."""
    for game_state in optimized_sessions.values():
        try:
            game_state.optimize_memory_usage()
        except Exception as e:
            logger.warning(f"Error cleaning up optimized session: {e}")
    
    optimized_sessions.clear()
    logger.info("All optimized sessions cleaned up")

# Performance monitoring decorator
def track_performance(func):
    """Decorator to track performance of API endpoints."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            processing_time = time.time() - start_time
            
            # Add performance info if result is a dict
            if isinstance(result, dict):
                result['_performance'] = {
                    'processing_time_ms': processing_time * 1000,
                    'optimized': True
                }
            
            return result
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Performance tracked error in {func.__name__}: {e} (took {processing_time:.4f}s)")
            raise
    
    return wrapper