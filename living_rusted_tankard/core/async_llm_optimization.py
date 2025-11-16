"""
Asynchronous LLM optimization module for better performance.

This module provides:
- Async LLM request handling for better concurrency
- Context caching to reduce repeated API calls
- Request batching for efficiency
- Background health monitoring
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class CachedContext:
    """Cached context entry with TTL."""

    content: str
    timestamp: float
    hash_key: str
    access_count: int = 0


class AsyncContextCache:
    """Asynchronous context cache with TTL and LRU eviction."""

    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, CachedContext] = {}
        self._lock = threading.RLock()

    def _generate_cache_key(self, session_id: str, game_state_hash: str) -> str:
        """Generate cache key from session and game state."""
        return f"{session_id}:{game_state_hash}"

    def _hash_game_state(self, game_state) -> str:
        """Generate hash from game state for caching."""
        try:
            # Create a simplified hash based on key game state elements
            state_elements = [
                str(getattr(game_state.player, "gold", 0)),
                str(getattr(game_state.player, "tiredness", 0)),
                str(getattr(game_state.player, "has_room", False)),
                str(getattr(game_state.clock, "current_time_hours", 0)),
                str(len(getattr(game_state, "events", []))),
            ]

            # Add NPC states
            if hasattr(game_state, "npc_manager"):
                try:
                    present_npcs = game_state.npc_manager.get_present_npcs()
                    state_elements.extend([npc.id for npc in present_npcs])
                except (AttributeError, TypeError) as e:
                    logger.debug(f"Could not get NPC states for hashing: {e}")
                    pass

            combined = "|".join(state_elements)
            return hashlib.md5(combined.encode()).hexdigest()[:16]
        except Exception as e:
            logger.warning(f"Error hashing game state: {e}")
            return str(time.time())[:16]

    def get(self, session_id: str, game_state) -> Optional[str]:
        """Get cached context if available and valid."""
        with self._lock:
            state_hash = self._hash_game_state(game_state)
            cache_key = self._generate_cache_key(session_id, state_hash)

            if cache_key in self.cache:
                cached = self.cache[cache_key]

                # Check TTL
                if time.time() - cached.timestamp <= self.ttl:
                    cached.access_count += 1
                    logger.debug(f"Context cache hit for {session_id}")
                    return cached.content
                else:
                    # Expired, remove from cache
                    del self.cache[cache_key]
                    logger.debug(f"Context cache expired for {session_id}")

            return None

    def set(self, session_id: str, game_state, context: str) -> None:
        """Cache context with TTL."""
        with self._lock:
            state_hash = self._hash_game_state(game_state)
            cache_key = self._generate_cache_key(session_id, state_hash)

            # Evict oldest entries if cache is full
            if len(self.cache) >= self.max_size:
                self._evict_oldest()

            self.cache[cache_key] = CachedContext(
                content=context, timestamp=time.time(), hash_key=state_hash
            )
            logger.debug(f"Context cached for {session_id}")

    def _evict_oldest(self) -> None:
        """Evict oldest cache entries to make room."""
        if not self.cache:
            return

        # Sort by timestamp and remove oldest 25%
        sorted_items = sorted(self.cache.items(), key=lambda x: x[1].timestamp)

        evict_count = max(1, len(sorted_items) // 4)
        for i in range(evict_count):
            del self.cache[sorted_items[i][0]]

        logger.debug(f"Evicted {evict_count} old cache entries")


class AsyncLLMOptimizer:
    """Asynchronous LLM optimization and request handling."""

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "long-gemma:latest",
    ):
        self.ollama_url = ollama_url
        self.model = model
        self.context_cache = AsyncContextCache()
        self.request_stats = defaultdict(int)
        self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def make_async_request(
        self, messages: List[Dict], session_id: str
    ) -> Dict[str, Any]:
        """Make asynchronous request to LLM service."""
        session = await self._get_session()
        api_url = f"{self.ollama_url}/api/chat"

        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 400,
            },
        }

        start_time = time.time()

        try:
            async with session.post(api_url, json=data) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(
                        f"HTTP {response.status}: {await response.text()}"
                    )

                response_data = await response.json()

                if (
                    "message" not in response_data
                    or "content" not in response_data["message"]
                ):
                    raise ValueError("Invalid response format from LLM")

                self.request_stats["successful_requests"] += 1
                self.request_stats["total_response_time"] += time.time() - start_time

                return response_data

        except asyncio.TimeoutError:
            self.request_stats["timeout_errors"] += 1
            raise Exception("Request timed out")
        except aiohttp.ClientError as e:
            self.request_stats["connection_errors"] += 1
            raise Exception(f"Connection error: {e}")
        except Exception as e:
            self.request_stats["other_errors"] += 1
            raise Exception(f"Request error: {e}")

    def get_cached_context(self, session_id: str, game_state) -> Optional[str]:
        """Get cached context if available."""
        return self.context_cache.get(session_id, game_state)

    def cache_context(self, session_id: str, game_state, context: str) -> None:
        """Cache context for future use."""
        self.context_cache.set(session_id, game_state, context)

    def get_stats(self) -> Dict[str, Any]:
        """Get request statistics."""
        stats = dict(self.request_stats)

        # Calculate average response time
        if stats.get("successful_requests", 0) > 0:
            stats["average_response_time"] = (
                stats.get("total_response_time", 0) / stats["successful_requests"]
            )
        else:
            stats["average_response_time"] = 0

        # Add cache stats
        stats["cache_size"] = len(self.context_cache.cache)
        stats["cache_max_size"] = self.context_cache.max_size

        return stats


class BackgroundHealthMonitor:
    """Background health monitoring with async checks."""

    def __init__(self, ollama_url: str, model: str, check_interval: int = 60):
        self.ollama_url = ollama_url
        self.model = model
        self.check_interval = check_interval
        self.is_healthy = True
        self.last_check = 0
        self.consecutive_failures = 0
        self._monitoring_task = None
        self._stop_event = asyncio.Event()

    async def start_monitoring(self):
        """Start background health monitoring."""
        if self._monitoring_task is not None:
            return

        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("Background health monitoring started")

    async def stop_monitoring(self):
        """Stop background health monitoring."""
        if self._monitoring_task is not None:
            self._stop_event.set()
            await self._monitoring_task
            self._monitoring_task = None
            logger.info("Background health monitoring stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                await self._check_health()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_health(self):
        """Perform async health check."""
        self.last_check = time.time()

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status != 200:
                        raise aiohttp.ClientError(f"HTTP {response.status}")

                    data = await response.json()
                    available_models = [
                        model["name"] for model in data.get("models", [])
                    ]
                    model_available = any(
                        self.model in model_name for model_name in available_models
                    )

                    if model_available:
                        self.is_healthy = True
                        self.consecutive_failures = 0
                        logger.debug(f"Health check passed - {self.model} available")
                    else:
                        self.is_healthy = False
                        logger.warning(f"Model {self.model} not available")

        except Exception as e:
            self.consecutive_failures += 1
            self.is_healthy = False
            logger.warning(
                f"Health check failed ({self.consecutive_failures} consecutive): {e}"
            )

    def get_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "is_healthy": self.is_healthy,
            "consecutive_failures": self.consecutive_failures,
            "last_check": self.last_check,
            "check_interval": self.check_interval,
        }


# Utility functions for integration
async def optimize_llm_requests(
    requests: List[Tuple[str, Any]], optimizer: AsyncLLMOptimizer
) -> List[Dict[str, Any]]:
    """Batch process multiple LLM requests for efficiency."""
    tasks = []

    for session_id, messages in requests:
        task = optimizer.make_async_request(messages, session_id)
        tasks.append(task)

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Request {i} failed: {result}")
                processed_results.append({"error": str(result)})
            else:
                processed_results.append(result)

        return processed_results

    except Exception as e:
        logger.error(f"Batch request processing failed: {e}")
        return [{"error": str(e)} for _ in requests]


def create_optimized_llm_manager(
    ollama_url: str = "http://localhost:11434", model: str = "long-gemma:latest"
) -> AsyncLLMOptimizer:
    """Factory function to create optimized LLM manager."""
    return AsyncLLMOptimizer(ollama_url, model)
