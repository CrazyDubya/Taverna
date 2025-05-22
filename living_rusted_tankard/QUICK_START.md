# Quick Start - AI Player Observer

## Ready to Use Commands

### 1. Start New AI Session (Recommended for first time)
```bash
cd /Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard
python3 launch_ai_observer.py --new
```

**What happens:**
- Starts FastAPI server on localhost:8000
- Creates new AI character named "Gemma" with curious_explorer personality
- Begins streaming AI actions in real-time
- You'll see the AI think, type, and interact with the game
- Press Ctrl+C to stop

### 2. Continue Existing Session  
```bash
python3 launch_ai_observer.py --continue-session [SESSION_ID]
```

**When to use:** If you stopped observing and want to resume the same AI character

### 3. Web Interface Only
```bash
python3 launch_ai_observer.py --web
```

**What happens:**
- Starts server and opens web browser to http://localhost:8000/ai-demo
- Visual interface for watching AI characters
- Can manage multiple AI sessions

### 4. Simple Demo (No Server)
```bash
python3 launch_ai_observer.py --demo
```

**What happens:**
- Quick terminal demo showing AI in action
- No web server needed
- Limited to 10 actions then stops

## Expected Output

When observing, you'll see:

```
🎬 Action #1 - 14:30:25
----------------------------------------
💭 Gemma is thinking...
⚡ Gemma is deciding what to do...
🔤 Typing: look around the tavern
✨ Final action: look around the tavern
⚙️ Gemma performs: look around the tavern
📝 Game response:
The Living Rusted Tankard buzzes with activity. Patrons chat over meals...
💰 Gold: 20 | 📍 Location: tavern
✅ Action completed

⏸️ Waiting 3 seconds before next action...
```

## Customization Options

```bash
# Custom AI name and personality
python3 launch_ai_observer.py --new --name "MyAI" --personality "social_butterfly"

# List available personalities
python3 launch_ai_observer.py --list-personalities
```

## Requirements Check

Before running, ensure:

1. **Ollama is running** with gemma2:2b model:
   ```bash
   ollama run gemma2:2b
   ```

2. **Python dependencies installed** (should already be set up)

3. **Port 8000 available** (or change in script if needed)

## Troubleshooting

- **"Server failed to start"**: Port 8000 might be in use
- **"AI not responding"**: Check if Ollama is running with gemma2:2b
- **"Session not found"**: Sessions expire after inactivity
- **Web interface issues**: Try the --demo mode instead

## What the AI Does

The AI character will autonomously:
- Explore the tavern environment
- Talk to NPCs and other characters  
- Buy items, play games, work jobs
- Make decisions based on its personality
- React to game events and other players

You simply observe - no input needed from you!