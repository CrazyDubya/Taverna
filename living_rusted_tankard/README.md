# The Living Rusted Tankard

A text-based RPG where time moves forward and choices matter. You find yourself in a mysterious tavern called The Rusted Tankard, where the front door never opens. Time moves forward, characters come and go, and your decisions shape the story.

## Features

### Core Gameplay
- **Time System**: The game world progresses in real-time, with events and characters following their own schedules
- **Player State**: Track your character's gold, inventory, and status effects
- **NPC System**: Interact with characters who come and go on their own schedules
- **Economy**: Gamble and work to earn gold
- **Room System**: Rent a room to rest, but at what cost?
- **Meta Quest**: Discover the secret of why you can't leave... if you dare

### Advanced Systems
- **Narrative Actions**: Story choices have real mechanical consequences - purchases affect gold, quests progress, NPCs remember your actions
- **Quest Management**: Dynamic quest system that starts, progresses, and completes based on your narrative choices
- **Memory System**: Persistent storytelling memory that maintains consistency across game sessions
- **Dynamic Descriptions**: Objects and NPCs have facts-based descriptions that balance structure with creative narrative freedom
- **Conversation Options**: Interactive dialogue choices that seamlessly integrate with game mechanics

### Technical Features
- **Natural Language Parser**: Uses Ollama's LLM (long-gemma model) to understand natural language commands
- **Web Interface**: Play through a modern web browser with responsive design
- **Session Management**: Persistent game sessions with automatic save/load functionality

## Prerequisites

- Python 3.8+
- [Poetry](https://python-poetry.org/) for dependency management
- [Ollama](https://ollama.ai/) for the LLM integration

### Setting up Ollama

1. Install Ollama: [https://ollama.ai/](https://ollama.ai/)
2. Pull the model:
   ```bash
   ollama pull long-gemma
   ```
3. Start the Ollama server (if not running):
   ```bash
   ollama serve
   ```

## Quick Start

### Command Line Interface

1. Install Poetry (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install project dependencies:
   ```bash
   poetry install
   ```

3. Run the game:
   ```bash
   poetry run python run.py
   ```

   Or use the installed script:
   ```bash
   poetry run tavern
   ```

### Web Interface

1. Start the web server:
   ```bash
   poetry run python run_api.py
   ```

2. Open your browser to:
   ```
   http://localhost:8001/
   ```

## Game Commands

- `status` - Show your current status and present NPCs
- `inventory` - Display your current items
- `gamble <amount> [npc_id]` - Gamble some gold
- `rest [hours]` - Rest for a number of hours (default: 8)
- `rent` - Rent a room for the night (10 gold)
- `buy <item>` - Purchase items from NPCs
- `talk to <npc>` - Engage in conversation with characters
- `quit` - Exit the game

## How Story Choices Affect Gameplay

The Living Rusted Tankard features a sophisticated narrative-action system where your story choices have real mechanical consequences:

- **Purchases**: When you buy "Old Tom's Surprise" through conversation, your gold decreases and the item appears in your inventory
- **Quest Progression**: Accepting quests, making progress, or completing objectives through dialogue automatically updates your quest log
- **NPC Relations**: Your interactions affect how NPCs view you, changing future dialogue options and story branches
- **World Events**: Major story decisions can trigger events that affect the entire tavern environment

## Project Structure

```
living_rusted_tankard/
├── core/                    # Core game logic and state management
│   ├── narrative_actions.py # Narrative-to-mechanics action system
│   ├── llm_game_master.py   # LLM integration and story generation
│   ├── memory_manager.py    # Persistent storytelling memory
│   └── facts_system.py      # Dynamic object descriptions
├── game/                    # Web interface and templates
├── data/                    # Game data (NPCs, items, locations)
├── models/                  # Data models and schemas
├── tests/                   # Unit and integration tests
├── docs/                    # Documentation
├── run.py                   # CLI entry point
├── run_api.py              # Web server entry point
└── pyproject.toml          # Project configuration
```

## Development

### Setup

1. Clone the repository
2. Install development dependencies:
   ```bash
   poetry install --with dev
   ```
3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

### Running Tests

Run all tests with coverage:
```bash
pytest --cov=core --cov-report=term-missing
```

### Code Quality

Run linter:
```bash
flake8 .
```

Run type checker:
```bash
mypy .
```

Format code:
```bash
black .
isort .
```

### Web Development

The web interface files are located in:
- `living_rusted_tankard/game/templates/game.html` - Main game interface
- `living_rusted_tankard/core/api.py` - FastAPI backend

Start the development server with auto-reload:
```bash
poetry run python run_api.py --reload
```

## Architecture Notes

### Narrative Action System

The game uses embedded action tags in LLM responses to trigger mechanical changes:
- `[COMMAND:buy old_toms_surprise]` - Execute game commands
- `[QUEST_START:find_the_key]` - Begin new quests
- `[ITEM_GIVE:mysterious_key]` - Add items to inventory
- `[REPUTATION:barkeep +1]` - Modify NPC relationships

### Memory System

Persistent memory tracks:
- Important story events and player choices
- Character relationships and reputation
- World state changes and consequences
- Cross-session narrative continuity

## Contributing

1. Create a new branch for your feature or bugfix
2. Write tests for your changes
3. Run tests and ensure they pass
4. Format your code with Black and isort
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Inspired by classic text adventures and interactive fiction
- Built with Python 3.x and FastAPI
- Uses Ollama LLM integration for natural language processing
- Features modern web technologies for the browser interface