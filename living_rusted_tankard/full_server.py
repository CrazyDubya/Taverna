#!/usr/bin/env python3
"""
Full-featured server for The Living Rusted Tankard
Preserves ALL game features while adding LLM natural language understanding
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import ALL game components
from core.game_state import GameState
from core.enhanced_llm_game_master import EnhancedLLMGameMaster
from core.llm.parser import Parser, GameSnapshot
from core.items import load_item_definitions, ITEM_DEFINITIONS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="The Living Rusted Tankard - Full Experience")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load item definitions
if not ITEM_DEFINITIONS:
    load_item_definitions()

# Session storage
game_sessions: Dict[str, Dict[str, Any]] = {}

# Full-featured HTML interface
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>The Living Rusted Tankard</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #0a0a0a;
            color: #e0e0e0;
            font-family: 'Georgia', serif;
            overflow: hidden;
        }

        #main-container {
            display: flex;
            height: 100vh;
            max-width: 1400px;
            margin: 0 auto;
        }

        #game-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
        }

        #sidebar {
            width: 300px;
            background-color: #1a1a1a;
            border-left: 2px solid #d4af37;
            padding: 20px;
            overflow-y: auto;
        }

        h1 {
            color: #d4af37;
            text-align: center;
            font-size: 2em;
            margin: 10px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        }

        h2 {
            color: #d4af37;
            font-size: 1.2em;
            margin-top: 20px;
            margin-bottom: 10px;
            border-bottom: 1px solid #444;
            padding-bottom: 5px;
        }

        #output {
            flex: 1;
            background-color: #1a1a1a;
            border: 2px solid #d4af37;
            border-radius: 5px;
            padding: 20px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 15px;
            line-height: 1.6;
            margin-bottom: 15px;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        }

        #input-area {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }

        #command {
            flex: 1;
            padding: 12px;
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 2px solid #d4af37;
            font-size: 16px;
            font-family: 'Georgia', serif;
            border-radius: 5px;
        }

        #command:focus {
            outline: none;
            border-color: #f0d060;
            box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
        }

        button {
            background-color: #d4af37;
            color: #1a1a1a;
            border: none;
            padding: 12px 24px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            border-radius: 5px;
            transition: all 0.3s;
        }

        button:hover {
            background-color: #f0d060;
            transform: translateY(-1px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        }

        #quick-commands {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-bottom: 10px;
        }

        .quick-btn {
            background-color: #2a2a2a;
            border: 1px solid #444;
            padding: 5px 10px;
            font-size: 12px;
            color: #d4af37;
        }

        .quick-btn:hover {
            background-color: #3a3a3a;
            border-color: #d4af37;
            transform: none;
        }

        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #333;
        }

        .stat-label {
            color: #999;
        }

        .stat-value {
            color: #d4af37;
            font-weight: bold;
        }

        #status-bar {
            background-color: #1a1a1a;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            font-size: 14px;
        }

        .thinking {
            color: #d4af37;
            font-style: italic;
            opacity: 0.8;
        }

        .error {
            color: #ff6b6b;
            font-weight: bold;
        }

        .success {
            color: #4ade80;
        }

        .warning {
            color: #fbbf24;
        }

        #help-text {
            font-size: 12px;
            color: #666;
            margin-top: 10px;
        }

        .inventory-item {
            padding: 5px;
            margin: 2px 0;
            background-color: #2a2a2a;
            border-radius: 3px;
            font-size: 14px;
        }

        .npc-name {
            color: #60a5fa;
            font-weight: bold;
        }

        #llm-indicator {
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 5px 10px;
            background-color: #2a2a2a;
            border: 1px solid #444;
            border-radius: 5px;
            font-size: 12px;
        }

        .llm-active { color: #4ade80; }
        .llm-fallback { color: #fbbf24; }
        .llm-error { color: #ff6b6b; }
    </style>
</head>
<body>
    <div id="llm-indicator">
        <span id="llm-status" class="llm-active">🧠 AI: Active</span>
    </div>

    <div id="main-container">
        <div id="game-area">
            <h1>🍺 The Living Rusted Tankard</h1>

            <div id="status-bar">
                <span id="time-display">Loading...</span> |
                <span id="location-display">Tavern</span> |
                <span id="gold-display">Gold: 0</span>
            </div>

            <div id="output">Welcome to The Rusted Tankard!

You stand at the entrance of The Rusted Tankard, a centuries-old tavern that has served as a haven for travelers, adventurers, and locals alike. The weathered wooden sign above the door creaks gently in the evening breeze.

As you push open the heavy oak door, warmth and the sounds of tavern life wash over you. The air carries the aroma of roasted meats, fresh bread, and spiced ale.

You can interact naturally - try "I'd like to look around" or use commands like "help" for a full list.

Type 'help' to see all available commands.

></div>

            <div id="quick-commands">
                <button class="quick-btn" onclick="quickCommand('look')">Look</button>
                <button class="quick-btn" onclick="quickCommand('inventory')">Inventory</button>
                <button class="quick-btn" onclick="quickCommand('status')">Status</button>
                <button class="quick-btn" onclick="quickCommand('bounties')">Bounties</button>
                <button class="quick-btn" onclick="quickCommand('games')">Games</button>
                <button class="quick-btn" onclick="quickCommand('jobs')">Jobs</button>
                <button class="quick-btn" onclick="quickCommand('wait 1')">Wait</button>
                <button class="quick-btn" onclick="quickCommand('help')">Help</button>
            </div>

            <div id="input-area">
                <input type="text" id="command" placeholder="What would you like to do? (Natural language or commands)" autofocus>
                <button onclick="sendCommand()">Send</button>
            </div>
        </div>

        <div id="sidebar">
            <h2>📊 Character</h2>
            <div id="player-stats">
                <div class="stat-item">
                    <span class="stat-label">Gold:</span>
                    <span class="stat-value" id="stat-gold">20</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Tiredness:</span>
                    <span class="stat-value" id="stat-tiredness">0%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Room:</span>
                    <span class="stat-value" id="stat-room">None</span>
                </div>
            </div>

            <h2>🎒 Inventory</h2>
            <div id="inventory-list">
                <div class="inventory-item">Loading...</div>
            </div>

            <h2>👥 Present NPCs</h2>
            <div id="npc-list">
                <div>None visible</div>
            </div>

            <h2>🎲 Available Games</h2>
            <div id="games-list">
                <div>• Dice</div>
                <div>• Cards</div>
                <div>• Arm Wrestling</div>
            </div>

            <div id="help-text">
                <h2>💡 Tips</h2>
                <p>• Speak naturally or use commands</p>
                <p>• Try "gamble 10 on dice"</p>
                <p>• Check the notice board for bounties</p>
                <p>• Talk to NPCs for rumors and quests</p>
                <p>• Time passes with your actions</p>
            </div>
        </div>
    </div>

    <script>
        let sessionId = null;
        let isProcessing = false;

        async function sendCommand() {
            if (isProcessing) return;

            const input = document.getElementById('command');
            const output = document.getElementById('output');
            const command = input.value.trim();

            if (!command) return;

            isProcessing = true;
            output.textContent += ' ' + command + '\\n';
            output.innerHTML += '<span class="thinking">Processing...</span>\\n';
            input.value = '';
            output.scrollTop = output.scrollHeight;

            try {
                const response = await fetch('/api/full-command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        command: command,
                        session_id: sessionId
                    })
                });

                const data = await response.json();
                sessionId = data.session_id;

                // Remove thinking message
                output.innerHTML = output.innerHTML.replace(/<span class="thinking">.*?<\\/span>\\n/, '');

                // Add response with proper formatting
                let message = data.message;
                if (data.success === false) {
                    message = '<span class="error">' + message + '</span>';
                }
                output.innerHTML += message + '\\n\\n>';
                output.scrollTop = output.scrollHeight;

                // Update UI
                updateGameState(data.game_state);
                updateLLMStatus(data.llm_used);

            } catch (error) {
                output.innerHTML = output.innerHTML.replace(/<span class="thinking">.*?<\\/span>\\n/, '');
                output.innerHTML += '<span class="error">Connection error: ' + error.message + '</span>\\n\\n>';
            } finally {
                isProcessing = false;
            }
        }

        function quickCommand(cmd) {
            document.getElementById('command').value = cmd;
            sendCommand();
        }

        function updateGameState(state) {
            if (!state) return;

            // Update stats
            if (state.player) {
                document.getElementById('stat-gold').textContent = state.player.gold || 0;
                document.getElementById('stat-tiredness').textContent = Math.round((state.player.tiredness || 0) * 100) + '%';
                document.getElementById('stat-room').textContent = state.player.has_room ? 'Rented' : 'None';
                document.getElementById('gold-display').textContent = 'Gold: ' + (state.player.gold || 0);
            }

            // Update time
            if (state.time) {
                document.getElementById('time-display').textContent = state.time.formatted_time || 'Unknown time';
            }

            // Update location
            if (state.location) {
                document.getElementById('location-display').textContent = state.location;
            }

            // Update inventory
            if (state.player && state.player.inventory) {
                const invList = document.getElementById('inventory-list');
                invList.innerHTML = '';
                for (const [item, details of Object.entries(state.player.inventory)) {
                    const div = document.createElement('div');
                    div.className = 'inventory-item';
                    div.textContent = `${details.name} (${details.quantity})`;
                    invList.appendChild(div);
                }
                if (invList.children.length === 0) {
                    invList.innerHTML = '<div class="inventory-item">Empty</div>';
                }
            }

            // Update NPCs
            if (state.present_npcs) {
                const npcList = document.getElementById('npc-list');
                npcList.innerHTML = '';
                state.present_npcs.forEach(npc => {
                    const div = document.createElement('div');
                    div.innerHTML = '<span class="npc-name">' + npc.name + '</span>';
                    npcList.appendChild(div);
                });
                if (npcList.children.length === 0) {
                    npcList.innerHTML = '<div>None visible</div>';
                }
            }
        }

        function updateLLMStatus(llmUsed) {
            const status = document.getElementById('llm-status');
            if (llmUsed === true) {
                status.textContent = '🧠 AI: Active';
                status.className = 'llm-active';
            } else if (llmUsed === false) {
                status.textContent = '⚡ AI: Fast Mode';
                status.className = 'llm-fallback';
            } else {
                status.textContent = '❌ AI: Error';
                status.className = 'llm-error';
            }
        }

        document.getElementById('command').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !isProcessing) sendCommand();
        });

        // Initial state load
        setTimeout(() => {
            fetch('/api/state/new')
                .then(r => r.json())
                .then(data => {
                    sessionId = data.session_id;
                    updateGameState(data.game_state);
                });
        }, 100);
    </script>
</body>
</html>
"""


def get_or_create_session(session_id: Optional[str] = None) -> tuple[GameState, str]:
    """Get existing session or create new one."""
    if session_id and session_id in game_sessions:
        game_sessions[session_id]["last_activity"] = time.time()
        return game_sessions[session_id]["game_state"], session_id

    # Create new session
    new_session_id = str(uuid.uuid4())
    game_state = GameState()

    game_sessions[new_session_id] = {
        "game_state": game_state,
        "created_at": time.time(),
        "last_activity": time.time(),
    }

    logger.info(f"Created new game session: {new_session_id}")
    return game_state, new_session_id


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the full game interface."""
    return HTML_CONTENT


@app.post("/api/full-command")
async def process_full_command(request: Request):
    """Process commands with LLM enhancement but preserve ALL game functionality."""
    try:
        data = await request.json()
        command = data.get("command", "").strip()
        session_id = data.get("session_id")

        # Get or create session
        game_state, session_id = get_or_create_session(session_id)

        # Try LLM processing first for natural language
        llm_used = False
        try:
            llm_gm = EnhancedLLMGameMaster()
            if llm_gm.is_service_available():
                (
                    narrative_response,
                    parsed_command,
                    action_results,
                ) = llm_gm.process_input(command, game_state, session_id)

                # If LLM extracted a specific command, use it
                if parsed_command:
                    command = parsed_command
                    llm_used = True
        except Exception as e:
            logger.debug(f"LLM processing skipped: {e}")

        # Process command through game state (preserves ALL commands)
        result = game_state.process_command(command)

        # If we have a narrative response from LLM, enhance the output
        if llm_used and "narrative_response" in locals() and narrative_response:
            if result.get("success", False):
                result["message"] = narrative_response
            else:
                # Keep error messages but add narrative context
                result["message"] = (
                    result.get("message", "") + "\\n\\n" + narrative_response
                )

        return {
            "message": result.get("message", ""),
            "success": result.get("success", True),
            "session_id": session_id,
            "game_state": game_state.get_snapshot(),
            "llm_used": llm_used,
        }

    except Exception as e:
        logger.error(f"Error processing command: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "message": "An error occurred processing your command.",
            },
        )


@app.get("/api/state/{session_id}")
async def get_state(session_id: str):
    """Get current game state."""
    if session_id == "new":
        game_state, session_id = get_or_create_session()
    else:
        if session_id not in game_sessions:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        game_state = game_sessions[session_id]["game_state"]

    return {"session_id": session_id, "game_state": game_state.get_snapshot()}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "sessions": len(game_sessions),
        "uptime": time.time() - app.state.start_time
        if hasattr(app.state, "start_time")
        else 0,
    }


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    app.state.start_time = time.time()
    logger.info("Full server started with all game features")


if __name__ == "__main__":
    print("🍺 Starting The Living Rusted Tankard - FULL EXPERIENCE")
    print("✨ All features preserved: gambling, bounties, NPCs, jobs, and more!")
    print("🧠 Enhanced with natural language understanding")
    print("📍 Open http://localhost:8080 in your browser")
    print("Press Ctrl+C to stop\\n")

    uvicorn.run(app, host="0.0.0.0", port=8080)
