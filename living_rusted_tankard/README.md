# The Living Rusted Tankard

A text-based RPG where time moves forward and choices matter. You find yourself in a mysterious tavern called The Rusted Tankard, where the front door never opens. Time moves forward, characters come and go, and your decisions shape the story.

## Features

- **Time System**: The game world progresses in real-time, with events and characters following their own schedules
- **Player State**: Track your character's gold, inventory, and status effects
- **NPC System**: Interact with characters who come and go on their own schedules
- **Economy**: Gamble and work to earn gold
- **Room System**: Rent a room to rest, but at what cost?
- **Meta Quest**: Discover the secret of why you can't leave... if you dare

## Quick Start

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

## Game Commands

- `status` - Show your current status and present NPCs
- `gamble <amount> [npc_id]` - Gamble some gold
- `rest [hours]` - Rest for a number of hours (default: 8)
- `rent` - Rent a room for the night (10 gold)
- `quit` - Exit the game

## Project Structure

```
living_rusted_tankard/
├── core/              # Core game logic and state management
├── models/            # Data models and schemas
├── tests/             # Unit and integration tests
├── cli.py             # Command-line interface
├── run.py             # Main entry point
├── pyproject.toml     # Project configuration
└── README.md          # This file
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
- Built with Python 3.x
- Uses modern Python type hints for better code quality
