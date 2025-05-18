"""Interactive test script for the LLM Parser."""
import asyncio
import json
import logging
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.llm.parser import parse
from core.llm.ollama_client import OllamaClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Sample game state
SAMPLE_GAME_STATE = {
    "time": "14:30",
    "location": "The Rusted Tankard",
    "npcs": ["Gene", "Marlene", "Old Tom"],
    "items": ["mug", "chair", "table", "dice"],
    "gold": 50,
    "has_room": False,
}

async def main():
    """Run the interactive parser test."""
    print("LLM Parser Test Console")
    print("Type 'quit' or 'exit' to quit\n")
    
    # Initialize the Ollama client
    client = OllamaClient(base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    
    try:
        while True:
            # Get user input
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break
                
            if user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                break
                
            if not user_input:
                continue
                
            # Parse the input
            try:
                result = await parse(
                    input_text=user_input,
                    game_state=SAMPLE_GAME_STATE,
                    use_llm=True
                )
                
                # Print the result
                print("\n=== Parser Result ===")
                print(f"Success: {result.success}")
                
                if result.error:
                    print(f"Error: {result.error}")
                    
                if result.command:
                    print("\nParsed Command:")
                    print(f"  Action: {result.command.action}")
                    if result.command.target:
                        print(f"  Target: {result.command.target}")
                    if result.command.subject:
                        print(f"  Subject: {result.command.subject}")
                    if result.command.amount is not None:
                        print(f"  Amount: {result.command.amount}")
                    if result.command.error:
                        print(f"  Error: {result.command.error}")
                
                if result.raw_response:
                    print("\nRaw Response:")
                    print(json.dumps(result.raw_response, indent=2))
                    
            except Exception as e:
                print(f"\nError: {e}")
                logger.exception("Error in parser test")
                
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
