# LLM Parser for The Living Rusted Tankard

This module handles the conversion of natural language player input into structured game commands using a local Ollama LLM.

## Overview

The parser takes natural language input from the player and converts it into a structured command that the game can understand. It uses a local Ollama instance with the `long-gemma` model by default.

## Components

- `ollama_client.py`: Client for interacting with the Ollama API
- `parser.py`: Main parser logic and integration with the game
- `schemas.py`: Pydantic models for command validation
- `prompts/parser_prompt.md`: Template for the LLM prompt

## Usage

### Prerequisites

1. Install Ollama: https://ollama.ai/
2. Pull the model: `ollama pull long-gemma`
3. Start the Ollama server: `ollama serve`

### Testing the Parser

Run the interactive test script:

```bash
python scripts/test_parser.py
```

### Example

```python
from core.llm.parser import parse

# Sample game state
game_state = {
    "time": "14:30",
    "location": "The Rusted Tankard",
    "npcs": ["Gene", "Marlene"],
    "items": ["mug", "chair"],
    "gold": 50,
    "has_room": False
}

# Parse player input
result = await parse("talk to gene about the key", game_state)
print(result)
```

## Configuration

Set the following environment variables if needed:

- `OLLAMA_HOST`: URL of the Ollama server (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: Model to use (default: `long-gemma`)

## Testing

Run the test suite:

```bash
pytest tests/test_llm_parser_integration.py -v
```

## Adding New Commands

1. Update `ActionType` in `schemas.py`
2. Add examples to `prompts/parser_prompt.md`
3. Add test cases to `tests/test_llm_parser_integration.py`
