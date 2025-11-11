# AI Player Observer

Launch and passively observe the AI character interact with The Living Rusted Tankard game.

## Quick Start

```bash
# Start new AI session and observe
python launch_ai_observer.py --new

# Continue existing session
python launch_ai_observer.py --continue-session SESSION_ID

# Launch web interface only
python launch_ai_observer.py --web

# Run simple terminal demo (no server needed)
python launch_ai_observer.py --demo
```

## Available Options

### New Session
```bash
# Default curious explorer personality
python launch_ai_observer.py --new

# Specific personality and name
python launch_ai_observer.py --new --personality "curious_explorer" --name "Gemma"

# List available personalities
python launch_ai_observer.py --list-personalities
```

### Continue Session
```bash
# Resume watching an existing AI session
python launch_ai_observer.py --continue-session abc12345

# Get session ID from web interface or previous terminal output
```

### Web Interface
```bash
# Open web demo interface
python launch_ai_observer.py --web

# Then visit: http://localhost:8000/ai-demo
```

### Simple Demo
```bash
# Quick terminal demo (no web server)
python launch_ai_observer.py --demo
```

## What You'll See

When observing an AI player, you'll see:

- 💭 **Thinking**: AI is processing the game state
- ⚡ **Generating**: AI is deciding what to do
- 🔤 **Typing**: Real-time character typing effect
- ✨ **Action**: Final command the AI chose
- ⚙️ **Executing**: AI performs the action
- 📝 **Response**: Game's reaction to the action
- 💰 **Status**: Gold, location, and other stats

## Example Output

```
🎬 Action #1 - 14:30:25
----------------------------------------
💭 Gemma is thinking...
⚡ Gemma is deciding what to do...
🔤 Typing: look around the tavern
✨ Final action: look around the tavern
⚙️ Gemma performs: look around the tavern
📝 Game response:
The Living Rusted Tankard is alive with activity...
💰 Gold: 20 | 📍 Location: tavern
✅ Action completed

⏸️ Waiting 3 seconds before next action...
```

## Controls

- **Ctrl+C**: Stop observing and shut down
- **Web Interface**: Visit http://localhost:8000/ai-demo for visual interface
- **Session ID**: Save session IDs to continue later

## Personalities Available

- `curious_explorer`: Eager to explore and investigate
- `social_butterfly`: Loves talking to NPCs and socializing  
- `shrewd_trader`: Focuses on commerce and profit
- `tavern_regular`: Comfortable hanging around the tavern

## Configuration

The AI observer supports several environment variables for customizing server startup and retry behavior:

### Environment Variables

- **SERVER_URL** (default: `http://localhost:8000`)  
  Base URL of the game server

- **HEALTH_ENDPOINT** (default: `/health`)  
  Path to the server health check endpoint

- **MAX_WAIT_SECONDS** (default: `60`)  
  Maximum time in seconds to wait for server to become healthy

- **AI_SESSION_RETRIES** (default: `3`)  
  Number of times to retry starting AI session on 5xx errors

- **AI_SESSION_RETRY_INTERVAL** (default: `5`)  
  Initial interval in seconds between retries (uses exponential backoff)

### Example Usage with Custom Configuration

```bash
# Wait longer for server startup
MAX_WAIT_SECONDS=120 ./ai-observer-global.sh --new

# Use custom server URL
SERVER_URL=http://localhost:3000 ./ai-observer-global.sh --new

# More aggressive retries
AI_SESSION_RETRIES=5 AI_SESSION_RETRY_INTERVAL=3 ./ai-observer-global.sh --new
```

## Troubleshooting

1. **Server won't start**: Check if port 8000 is available
2. **AI not responding**: Ensure Ollama is running with gemma2:2b model
3. **Session not found**: Session IDs expire after inactivity
4. **Web interface issues**: Try refreshing or use `--demo` mode
5. **AI session fails with HTTP 500**: 
   - The server may still be initializing (DB migrations, background tasks)
   - The observer will automatically retry with exponential backoff
   - Check logs at `living_rusted_tankard/logs/ai-session-diagnostics.log`
   - Increase `MAX_WAIT_SECONDS` if server takes longer to initialize
6. **Server health check timeouts**: 
   - Verify the health endpoint is accessible: `curl http://localhost:8000/health`
   - Check server logs at `living_rusted_tankard/logs/server.log`
   - Use the standalone helper: `scripts/wait_for_server.sh`

## Helper Scripts

### wait_for_server.sh

A standalone script to check server readiness. Useful for CI/CD pipelines, testing, or debugging.

```bash
# Basic usage
./scripts/wait_for_server.sh

# Custom configuration
./scripts/wait_for_server.sh --url http://localhost:3000 --max-wait 120

# Show help
./scripts/wait_for_server.sh --help

# Use in your own scripts
source scripts/wait_for_server.sh
wait_for_server && echo "Server is ready!"
```

## Integration

The observer integrates with:
- **Ollama**: For gemma2:2b LLM inference
- **FastAPI**: Web server and REST API
- **Server-Sent Events**: Real-time streaming
- **Game State**: Direct integration with game logic