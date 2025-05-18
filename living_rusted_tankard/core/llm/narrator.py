"""Narrator module for The Living Rusted Tankard.

This module handles the generation of narrative prose based on the current
game state using a local LLM via Ollama.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from core.llm.ollama_client import ollama_client

# Set up logging
logger = logging.getLogger(__name__)

# Load the narrator prompt template
try:
    with open(Path(__file__).parent / "prompts" / "narrator_prompt.md", "r") as f:
        NARRATOR_PROMPT = f.read()
except Exception as e:
    logger.error(f"Failed to load narrator prompt: {e}")
    NARRATOR_PROMPT = """You are the narrator for a text-based RPG. 
    Provide a vivid, atmospheric description based on the game context in 2-4 paragraphs.
    Write in second-person present tense. Current context: {{context}}"""

class Narrator:
    """Handles narrative generation for the game."""
    
    def __init__(self, model: str = "long-gemma"):
        """Initialize the narrator with the specified LLM model.
        
        Args:
            model: The name of the Ollama model to use for narration.
        """
        self.model = model
        self.cache: Dict[str, str] = {}
    
    async def narrate(
        self, 
        context: Dict[str, Any],
        use_cache: bool = True
    ) -> str:
        """Generate narrative prose based on the current game context.
        
        Args:
            context: A dictionary containing the current game state and context.
            use_cache: Whether to use cached responses for the same context.
            
        Returns:
            A string containing the generated narrative prose.
        """
        try:
            # Create a cache key from the context
            cache_key = json.dumps(context, sort_keys=True)
            
            # Return cached response if available
            if use_cache and cache_key in self.cache:
                logger.debug("Returning cached narration")
                return self.cache[cache_key]
            
            # Format the prompt with the current context
            prompt = NARRATOR_PROMPT.replace(
                "{{context}}", 
                json.dumps(context, indent=2)
            )
            
            logger.debug(f"Generating narration for context: {context}")
            
            # Call the LLM to generate the narration
            response = await ollama_client.generate(
                model=self.model,
                prompt=prompt,
                system="You are a creative narrator for a text-based RPG.",
                temperature=0.7,  # Slightly more creative than the parser
                format="text"
            )
            
            narration = response.get("response", "").strip()
            
            # Cache the response
            if use_cache:
                self.cache[cache_key] = narration
            
            return narration
            
        except Exception as e:
            logger.error(f"Error generating narration: {e}")
            # Fallback narration if LLM fails
            return self._fallback_narration(context)
    
    def _fallback_narration(self, context: Dict[str, Any]) -> str:
        """Generate a fallback narration when the LLM fails.
        
        Args:
            context: The current game context.
            
        Returns:
            A simple fallback narration string.
        """
        location = context.get("location", "the tavern")
        time_of_day = context.get("time", "day")
        
        return (
            f"You find yourself in {location} during {time_of_day}. "
            "The air is thick with the scent of ale and woodsmoke. "
            "The muffled sounds of conversation and clinking glasses "
            "create a lively atmosphere around you."
        )

# Singleton instance
narrator = Narrator()
