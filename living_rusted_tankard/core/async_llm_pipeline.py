"""
Enhanced Asynchronous LLM Pipeline for The Living Rusted Tankard.

This module provides non-blocking LLM processing with:
- Queue-based request processing to prevent UI blocking
- Response caching for similar interactions
- Background processing capabilities
- Graceful degradation with fallback responses
- Integration with existing LLM systems

Integrates with:
- async_llm_optimization.py (existing async foundation)
- enhanced_llm_game_master.py (enhanced LLM features)
- api.py (FastAPI endpoints)
"""

import asyncio
import logging
import time
import uuid
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

from .async_llm_optimization import AsyncLLMOptimizer
from .enhanced_llm_game_master import EnhancedLLMGameMaster

logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Priority levels for LLM requests."""

    LOW = 1  # Background processing, pre-generation
    NORMAL = 2  # Standard user interactions
    HIGH = 3  # Interactive conversations, real-time responses
    URGENT = 4  # Error recovery, critical system responses


@dataclass
class LLMRequest:
    """Represents a queued LLM request."""

    id: str
    session_id: str
    user_input: str
    game_state: Any
    priority: RequestPriority
    created_at: float
    callback: Optional[Callable[[str, Optional[str], List[Dict]], None]] = None
    context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = time.time()


@dataclass
class LLMResponse:
    """Response from LLM processing."""

    request_id: str
    session_id: str
    content: str
    command: Optional[str] = None
    actions: List[Dict[str, Any]] = None
    was_cached: bool = False
    was_fallback: bool = False
    processing_time: float = 0.0
    error: Optional[str] = None


class ResponseCache:
    """Cache for LLM responses to reduce redundant calls."""

    def __init__(self, max_size: int = 500, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _generate_cache_key(self, user_input: str, game_context: str) -> str:
        """Generate cache key for input and context."""
        import hashlib

        combined = f"{user_input.lower().strip()}|{game_context}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get(self, user_input: str, game_context: str) -> Optional[str]:
        """Get cached response if available and valid."""
        cache_key = self._generate_cache_key(user_input, game_context)

        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry["timestamp"] <= self.ttl_seconds:
                entry["hits"] += 1
                logger.debug(f"Response cache hit for input: {user_input[:50]}...")
                return entry["response"]
            else:
                # Expired, remove
                del self.cache[cache_key]

        return None

    def set(self, user_input: str, game_context: str, response: str) -> None:
        """Cache a response."""
        cache_key = self._generate_cache_key(user_input, game_context)

        # Evict old entries if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[cache_key] = {"response": response, "timestamp": time.time(), "hits": 0}
        logger.debug(f"Cached response for input: {user_input[:50]}...")

    def _evict_oldest(self) -> None:
        """Remove oldest cache entries."""
        if not self.cache:
            return

        # Sort by timestamp and remove oldest 25%
        sorted_items = sorted(self.cache.items(), key=lambda x: x[1]["timestamp"])

        evict_count = max(1, len(sorted_items) // 4)
        for i in range(evict_count):
            del self.cache[sorted_items[i][0]]

        logger.debug(f"Evicted {evict_count} old response cache entries")


class FallbackResponseGenerator:
    """Generate fallback responses when LLM is unavailable."""

    GENERAL_RESPONSES = [
        "The tavern keeper nods thoughtfully, considering your words.",
        "There's a moment of quiet contemplation in the tavern.",
        "The atmosphere in the tavern shifts slightly as people process your statement.",
        "Your words hang in the air for a moment as the tavern continues its rhythm.",
        "The warmth of the tavern seems to acknowledge your presence.",
    ]

    CONVERSATION_RESPONSES = {
        "hello": "A friendly nod greets you in return.",
        "talk": "The conversation takes on a natural flow.",
        "buy": "The transaction proceeds smoothly.",
        "look": "You take in the familiar sights of the tavern.",
        "help": "You sense that assistance would be available if needed.",
    }

    def generate_fallback(self, user_input: str, context: Optional[Dict] = None) -> str:
        """Generate contextual fallback response."""
        import random

        user_lower = user_input.lower().strip()

        # Check for specific command patterns
        for keyword, response in self.CONVERSATION_RESPONSES.items():
            if keyword in user_lower:
                return response

        # Add time context if available
        time_context = ""
        if context and "current_time" in context:
            time_context = f" The {context['current_time'].lower()} atmosphere adds to the moment."

        base_response = random.choice(self.GENERAL_RESPONSES)
        return base_response + time_context


class AsyncLLMPipeline:
    """Enhanced asynchronous LLM processing pipeline."""

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "long-gemma:latest"):
        self.ollama_url = ollama_url
        self.model = model

        # Core components
        self.async_optimizer = AsyncLLMOptimizer(ollama_url, model)
        self.enhanced_llm = EnhancedLLMGameMaster(ollama_url, model)
        self.response_cache = ResponseCache()
        self.fallback_generator = FallbackResponseGenerator()

        # Request queue with priority handling
        self.request_queue: asyncio.PriorityQueue = None
        self.active_requests: Dict[str, LLMRequest] = {}
        self.processing_task: Optional[asyncio.Task] = None

        # Thread safety
        self._lock = threading.RLock()
        self._stats_lock = threading.Lock()

        # Statistics and monitoring (protected by _stats_lock)
        self._stats = {
            "total_requests": 0,
            "cached_responses": 0,
            "fallback_responses": 0,
            "successful_responses": 0,
            "failed_requests": 0,
            "average_processing_time": 0.0,
            "queue_size": 0,
        }

        # Background task management
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.is_running = False

    def _add_active_request(self, request_id: str, request: LLMRequest) -> None:
        """Thread-safe method to add an active request."""
        with self._lock:
            self.active_requests[request_id] = request

    def _remove_active_request(self, request_id: str) -> Optional[LLMRequest]:
        """Thread-safe method to remove an active request."""
        with self._lock:
            return self.active_requests.pop(request_id, None)

    def _get_active_request(self, request_id: str) -> Optional[LLMRequest]:
        """Thread-safe method to get an active request."""
        with self._lock:
            return self.active_requests.get(request_id)

    def _update_stats(self, **kwargs) -> None:
        """Thread-safe method to update statistics."""
        with self._stats_lock:
            for key, value in kwargs.items():
                if key in self._stats:
                    if key == "average_processing_time":
                        # Special handling for average
                        old_avg = self._stats[key]
                        total = self._stats["total_requests"]
                        if total > 1:
                            self._stats[key] = ((old_avg * (total - 1)) + value) / total
                        else:
                            self._stats[key] = value
                    else:
                        self._stats[key] += value if isinstance(value, (int, float)) else 1

    def get_stats(self) -> Dict[str, Any]:
        """Thread-safe method to get current statistics."""
        with self._stats_lock:
            stats_copy = self._stats.copy()
            # Add current queue size
            if self.request_queue:
                stats_copy["queue_size"] = self.request_queue.qsize()
            return stats_copy

    async def start(self) -> None:
        """Start the async pipeline."""
        if self.is_running:
            return

        self.request_queue = asyncio.PriorityQueue()
        self.is_running = True

        # Start background processing task
        self.processing_task = asyncio.create_task(self._process_requests())
        logger.info("Async LLM Pipeline started")

    async def stop(self) -> None:
        """Stop the async pipeline and clean up resources."""
        self.is_running = False

        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

        # Clean up active requests
        with self._lock:
            active_count = len(self.active_requests)
            self.active_requests.clear()
            if active_count > 0:
                logger.info(f"Cleaned up {active_count} active requests")

        # Close external resources
        await self.async_optimizer.close()

        # Shutdown thread pool with timeout
        self.executor.shutdown(wait=True)

        logger.info("Async LLM Pipeline stopped")

    async def process_request_async(
        self, user_input: str, game_state: Any, session_id: str, priority: RequestPriority = RequestPriority.NORMAL
    ) -> str:
        """Process a request asynchronously and return request ID for tracking."""
        if not self.is_running:
            await self.start()

        request_id = str(uuid.uuid4())
        request = LLMRequest(
            id=request_id,
            session_id=session_id,
            user_input=user_input,
            game_state=game_state,
            priority=priority,
            created_at=time.time(),
        )

        # Check cache first
        try:
            from .time_display import get_time_context_for_llm

            time_context = get_time_context_for_llm(game_state.clock.current_time_hours)
            cached_response = self.response_cache.get(user_input, time_context)

            if cached_response:
                self._update_stats(cached_responses=1)
                return cached_response
        except Exception as e:
            logger.debug(f"Error checking cache: {e}")

        # Queue the request
        # Priority queue uses (priority, item) tuples, lower numbers = higher priority
        priority_value = 5 - priority.value  # Invert so URGENT=1, HIGH=2, etc.
        await self.request_queue.put((priority_value, time.time(), request))

        self._add_active_request(request_id, request)
        self._update_stats(total_requests=1)

        return request_id

    async def get_response(self, request_id: str, timeout: float = 30.0) -> Optional[LLMResponse]:
        """Get the response for a request (blocking until ready or timeout)."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if request_id not in self.active_requests:
                # Request completed, check if we have a response
                # In a full implementation, we'd store completed responses
                # For now, we'll return None to indicate completion
                return None

            await asyncio.sleep(0.1)

        # Timeout - generate fallback
        request = self._get_active_request(request_id)
        if request:
            fallback_content = self.fallback_generator.generate_fallback(
                request.user_input, {"current_time": "evening"}  # Could get from game_state
            )

            # Clean up
            self._remove_active_request(request_id)

            self._update_stats(fallback_responses=1)

            return LLMResponse(
                request_id=request_id,
                session_id=request.session_id,
                content=fallback_content,
                was_fallback=True,
                processing_time=timeout,
            )

        return None

    def process_request_sync(
        self, user_input: str, game_state: Any, session_id: str
    ) -> Tuple[str, Optional[str], List[Dict[str, Any]]]:
        """Synchronous wrapper for backward compatibility with existing API."""
        try:
            # Check cache first
            from .time_display import get_time_context_for_llm

            time_context = get_time_context_for_llm(game_state.clock.current_time_hours)
            cached_response = self.response_cache.get(user_input, time_context)

            if cached_response:
                self._update_stats(cached_responses=1)
                return cached_response, None, []

            # Fall back to enhanced LLM for synchronous processing
            start_time = time.time()
            response, command, actions = self.enhanced_llm.process_input(user_input, game_state, session_id)
            processing_time = time.time() - start_time

            # Cache the response
            self.response_cache.set(user_input, time_context, response)

            # Update stats
            self._update_stats(successful_responses=1)
            self._update_average_processing_time(processing_time)

            return response, command, actions

        except Exception as e:
            logger.error(f"Error in sync LLM processing: {e}")
            self._update_stats(failed_requests=1)

            # Use comprehensive error recovery system
            try:
                from .error_recovery import handle_llm_error

                # Get game time context if available
                game_context = {}
                try:
                    from .time_display import get_time_context_for_llm

                    time_context = get_time_context_for_llm(game_state.clock.current_time_hours)
                    game_context["current_time"] = time_context
                except Exception:
                    game_context["current_time"] = "evening"

                # Get NPC context if available
                try:
                    present_npcs = game_state.get_present_npcs()
                    game_context["present_npcs"] = [npc.name for npc in present_npcs]
                except Exception:
                    game_context["present_npcs"] = []

                response, command, actions = handle_llm_error(e, session_id, user_input, game_context)

                self._update_stats(fallback_responses=1)
                return response, command, actions

            except ImportError:
                # Fallback to basic fallback response
                fallback_response = self.fallback_generator.generate_fallback(user_input, {"current_time": "evening"})

                self._update_stats(fallback_responses=1)
                return fallback_response, None, []

    async def _process_requests(self) -> None:
        """Background task to process queued requests."""
        while self.is_running:
            try:
                # Get request from queue with timeout
                try:
                    priority, timestamp, request = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Process the request
                await self._handle_request(request)

                # Mark task as done
                self.request_queue.task_done()

            except Exception as e:
                logger.error(f"Error in request processing loop: {e}")
                await asyncio.sleep(1.0)

    async def _handle_request(self, request: LLMRequest) -> None:
        """Handle a single request asynchronously."""
        start_time = time.time()

        try:
            # Use the enhanced LLM in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            response, command, actions = await loop.run_in_executor(
                self.executor,
                self.enhanced_llm.process_input,
                request.user_input,
                request.game_state,
                request.session_id,
            )

            processing_time = time.time() - start_time

            # Cache the response
            try:
                from .time_display import get_time_context_for_llm

                time_context = get_time_context_for_llm(request.game_state.clock.current_time_hours)
                self.response_cache.set(request.user_input, time_context, response)
            except Exception as e:
                logger.debug(f"Error caching response: {e}")

            # Auto-create memory for significant interactions
            try:
                from .memory import add_session_memory, MemoryImportance

                # Create memory based on interaction type
                memory_content = f"Player: {request.user_input[:100]}... Response: {response[:100]}..."
                importance = MemoryImportance.NORMAL

                # Adjust importance based on content
                if command or (actions and len(actions) > 0):
                    importance = MemoryImportance.HIGH  # Commands and actions are more important
                elif any(word in request.user_input.lower() for word in ["hello", "hi", "greet"]):
                    importance = MemoryImportance.TRIVIAL

                add_session_memory(request.session_id, memory_content, importance)

            except Exception as e:
                logger.debug(f"Error creating auto-memory: {e}")

            # Call callback if provided
            if request.callback:
                request.callback(response, command, actions or [])

            self._update_stats(successful_responses=1)
            self._update_average_processing_time(processing_time)

        except Exception as e:
            logger.error(f"Error processing request {request.id}: {e}")

            # Generate fallback response
            fallback_response = self.fallback_generator.generate_fallback(request.user_input, request.context)

            if request.callback:
                request.callback(fallback_response, None, [])

            self._update_stats(failed_requests=1)
            self._update_stats(fallback_responses=1)

        finally:
            # Clean up
            self._remove_active_request(request.id)

    def _update_average_processing_time(self, processing_time: float) -> None:
        """Update average processing time statistic (thread-safe)."""
        self._update_stats(average_processing_time=processing_time)

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics (thread-safe)."""
        # Use the thread-safe method from the parent class
        stats = super().get_stats()

        # Add additional pipeline-specific stats
        with self._lock:
            stats["active_requests"] = len(self.active_requests)

        stats["cache_size"] = len(self.response_cache.cache)

        # Calculate cache hit rate
        total_requests = stats["total_requests"]
        if total_requests > 0:
            stats["cache_hit_rate"] = stats["cached_responses"] / total_requests
        else:
            stats["cache_hit_rate"] = 0.0

        return stats

    def is_healthy(self) -> bool:
        """Check if the pipeline is healthy."""
        try:
            if not self.is_running:
                return False

            # Check if we're not overwhelmed
            queue_size = self.request_queue.qsize() if self.request_queue else 0
            if queue_size > 50:  # Arbitrary threshold
                return False

            # Check error rate
            stats = self.get_stats()
            total = stats["total_requests"]
            if total > 10:  # Only check after some requests
                error_rate = stats["failed_requests"] / total
                if error_rate > 0.5:  # More than 50% errors
                    return False

            return True

        except Exception:
            return False


# Global pipeline instance for easy access
_pipeline_instance: Optional[AsyncLLMPipeline] = None


def get_pipeline() -> AsyncLLMPipeline:
    """Get the global pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = AsyncLLMPipeline()
    return _pipeline_instance


async def initialize_pipeline() -> None:
    """Initialize the global pipeline."""
    pipeline = get_pipeline()
    await pipeline.start()


async def shutdown_pipeline() -> None:
    """Shutdown the global pipeline."""
    global _pipeline_instance
    if _pipeline_instance:
        await _pipeline_instance.stop()
        _pipeline_instance = None


# Convenience functions for integration
def process_llm_request_sync(
    user_input: str, game_state: Any, session_id: str
) -> Tuple[str, Optional[str], List[Dict[str, Any]]]:
    """Process LLM request synchronously with caching and fallback."""
    pipeline = get_pipeline()
    return pipeline.process_request_sync(user_input, game_state, session_id)


async def process_llm_request_async(
    user_input: str, game_state: Any, session_id: str, priority: RequestPriority = RequestPriority.NORMAL
) -> str:
    """Process LLM request asynchronously and return request ID."""
    pipeline = get_pipeline()
    return await pipeline.process_request_async(user_input, game_state, session_id, priority)


if __name__ == "__main__":
    # Test the pipeline
    import asyncio

    async def test_pipeline():
        pipeline = AsyncLLMPipeline()
        await pipeline.start()

        print("Pipeline started")
        print(f"Pipeline healthy: {pipeline.is_healthy()}")
        print(f"Stats: {pipeline.get_stats()}")

        await pipeline.stop()
        print("Pipeline stopped")

    asyncio.run(test_pipeline())
