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

## Troubleshooting

1. **Server won't start**: Check if port 8000 is available
2. **AI not responding**: Ensure Ollama is running with gemma2:2b model
3. **Session not found**: Session IDs expire after inactivity
4. **Web interface issues**: Try refreshing or use `--demo` mode

## Integration

The observer integrates with:
- **Ollama**: For gemma2:2b LLM inference
- **FastAPI**: Web server and REST API
- **Server-Sent Events**: Real-time streaming
- **Game State**: Direct integration with game logic