"""Ollama API client for The Living Rusted Tankard."""
import json
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with the Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize the Ollama client.
        
        Args:
            base_url: Base URL of the Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient()
        
    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        format: str = "json",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a completion using the Ollama API.
        
        Args:
            model: The model to use (e.g., "long-gemma")
            prompt: The prompt to send to the model
            system: Optional system message to set the context
            format: Response format (default: "json")
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            The parsed JSON response from the API
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "format": format,
            **kwargs
        }
        
        if system:
            payload["system"] = system
            
        try:
            logger.debug(f"Sending request to Ollama: {payload}")
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            # The response comes as a series of JSON objects, one per token
            full_response = ""
            for line in response.text.splitlines():
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        full_response += chunk.get("response", "")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Ollama response: {line}")
                        raise ValueError(f"Invalid JSON response from Ollama: {line}") from e
            
            # Process the final response based on the requested format
            if format == "json":
                try:
                    return json.loads(full_response)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse final response as JSON: {full_response}")
                    raise ValueError(f"Response is not valid JSON: {full_response}") from e
            else: # Includes "text" or any other format specified that isn't explicitly "json"
                return full_response # Return the raw accumulated string
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API request failed with status {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama API: {e}")
            raise
            
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Singleton instance
ollama_client = OllamaClient()
