# The Living Rusted Tankard - Web Interface

This document explains how to run and use the web interface for The Living Rusted Tankard, a text-based RPG game set in a fantasy tavern.

## Running the Web Server

To run the web interface, use the `run_api.py` script:

```bash
python run_api.py
```

By default, this will start a web server on port 8001. You can customize the server settings with command-line arguments:

```bash
python run_api.py --host 127.0.0.1 --port 8002 --reload
```

Available options:
- `--host`: The host to bind the server to (default: 0.0.0.0)
- `--port`: The port to run the server on (default: 8001)
- `--reload`: Enable auto-reload on code changes
- `--log-level`: Set the logging level (debug, info, warning, error, critical)

## Accessing the Web Interface

Once the server is running, you can access the web interface by opening your browser and navigating to:

```
http://localhost:8001/
```

Replace `8001` with the port you specified if you changed it.

## API Documentation

The API documentation is available at:

```
http://localhost:8001/docs
```

This provides a Swagger UI interface that lets you explore and test the API endpoints.

## Available API Endpoints

- `GET /`: Main web interface
- `POST /command`: Send a command to the game
- `GET /state/{session_id}`: Get the current game state for a session
- `GET /sessions`: List all active game sessions
- `POST /sessions/{session_id}/reset`: Reset a game session
- `DELETE /sessions/{session_id}`: Delete a game session
- `GET /health`: API health check

## Web Interface Features

- **Session persistence**: The game session is stored in your browser's localStorage
- **Command history**: Use the up/down arrow keys to navigate through command history
- **Responsive design**: Works on both desktop and mobile devices
- **Error handling**: Provides clear feedback for connection or server errors
- **Loading states**: Visual feedback when commands are being processed

## Playing The Game

1. Type commands in the input field at the bottom of the screen
2. Use the up/down arrow keys to cycle through your command history
3. Type `help` to see a list of available commands
4. The right sidebar shows your current status, gold, inventory, and active quests

## Troubleshooting

- If the web interface doesn't connect, check that the server is running and accessible
- If sessions expire unexpectedly, check browser localStorage settings
- If the API returns errors, check the server logs for details

## Development Notes

- The web interface is served directly from the FastAPI application
- Game sessions timeout after 30 minutes of inactivity
- The HTML template is located at `living_rusted_tankard/game/templates/game.html`
- The API implementation is in `living_rusted_tankard/core/api.py`