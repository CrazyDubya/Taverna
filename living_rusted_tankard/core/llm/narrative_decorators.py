"""
Narrative Decorators

This module provides decorators for adding caching and other functionality
to narrative generation functions.
"""

from typing import Callable, Any, Dict, TypeVar, cast
from functools import wraps
import logging

from .narrative_cache import NarrativeCache

logger = logging.getLogger(__name__)

# Create a type variable for the decorated function
F = TypeVar("F", bound=Callable[..., str])


def cached_narrative(cache_dir: str = ".narrative_cache") -> Callable[[F], F]:
    """
    Decorator that adds caching to a narrative generation function.

    The decorated function should take a game state dictionary as its first argument
    and return a string (the narrative).

    Args:
        cache_dir: Directory to store cache files

    Returns:
        A decorated function with caching
    """
    cache = NarrativeCache(cache_dir)

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(state: Dict[str, Any], *args: Any, **kwargs: Any) -> str:
            # Check cache first
            cached = cache.get_cached_narrative(state)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached

            # Generate narrative if not in cache
            logger.debug(f"Cache miss for {func.__name__}, generating...")
            narrative = func(state, *args, **kwargs)

            # Cache the result
            cache.cache_narrative(state, narrative)
            return narrative

        return cast(F, wrapper)

    return decorator


def validate_state(required_keys: list = None) -> Callable[[F], F]:
    """
    Decorator that validates the game state dictionary.

    Args:
        required_keys: List of required keys in the state dictionary

    Returns:
        A decorated function with state validation
    """
    if required_keys is None:
        required_keys = []

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(state: Dict[str, Any], *args: Any, **kwargs: Any) -> str:
            if not isinstance(state, dict):
                raise ValueError("State must be a dictionary")

            missing = [key for key in required_keys if key not in state]
            if missing:
                raise ValueError(f"Missing required state keys: {', '.join(missing)}")

            return func(state, *args, **kwargs)

        return cast(F, wrapper)

    return decorator
