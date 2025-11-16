#!/usr/bin/env python3
"""
Enhanced server with full LLM integration for natural language understanding
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import Dict, Any, Optional
import json

# Import core game components
from core.game_state import GameState
from core.enhanced_llm_game_master import EnhancedLLMGameMaster
from core.llm.parser import Parser, GameSnapshot

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="The Living Rusted Tankard - Enhanced")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Game state and LLM components
game_sessions: Dict[str, Dict[str, Any]] = {}

# Enhanced HTML with better UI
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>The Living Rusted Tankard - Enhanced</title>
    <style>
        body {
            background-color: #1a1a1a;
            color: #e0e0e0;
            font-family: 'Georgia', serif;
            padding: 20px;
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            color: #d4af37;
            text-align: center;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        #game-container {
            background-color: #2a2a2a;
            border: 3px solid #d4af37;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
        }
        #output {
            background-color: #1f1f1f;
            border: 1px solid #444;
            padding: 20px;
            margin-bottom: 20px;
            min-height: 400px;
            max-height: 600px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 16px;
            line-height: 1.8;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        #input-area {
            display: flex;
            gap: 10px;
        }
        #command {
            flex: 1;
            padding: 12px;
            background-color: #1f1f1f;
            color: #e0e0e0;
            border: 2px solid #d4af37;
            font-size: 16px;
            font-family: 'Georgia', serif;
            border-radius: 5px;
        }
        #command:focus {
            outline: none;
            border-color: #f0d060;
            box-shadow: 0 0 5px rgba(212, 175, 55, 0.5);
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
            transform: translateY(-2px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
        .info {
            color: #888;
            font-size: 14px;
            text-align: center;
            margin-top: 20px;
            font-style: italic;
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
        #status {
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 5px 10px;
            background-color: #2a2a2a;
            border: 1px solid #444;
            border-radius: 5px;
            font-size: 12px;
        }
        .status-ok { color: #4ade80; }
        .status-error { color: #ff6b6b; }
    </style>
</head>
<body>
    <div id="status">
        <span id="llm-status" class="status-ok">LLM: Connected</span>
    </div>

    <h1>🍺 The Living Rusted Tankard</h1>

    <div id="game-container">
        <div id="output">Welcome to The Rusted Tankard!

You stand at the entrance of The Rusted Tankard, a centuries-old tavern that has served as a haven for travelers, adventurers, and locals alike. The weathered wooden sign above the door creaks gently in the evening breeze, depicting a tankard with a peculiar rust-colored patina.

As you push open the heavy oak door, the warmth and sounds of the tavern wash over you. The air is thick with the aroma of roasted meats, fresh bread, and the distinctive scent of the tavern's famous spiced ale.

What would you like to do? You can speak naturally - try "I'd like to look around the tavern" or "I walk up to the bar and order a drink" or anything else you can imagine!

></div>
        <div id="input-area">
            <input type="text" id="command" placeholder="What would you like to do?" autofocus>
            <button onclick="sendCommand()">Send</button>
        </div>
    </div>

    <div class="info">
        A text-based RPG with natural language understanding. Speak naturally - the tavern understands!<br>
        <small>Powered by LLM narrative engine and emergent gameplay systems</small>
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
            output.innerHTML += ' ' + escapeHtml(command) + '\\n';
            output.innerHTML += '<span class="thinking">The tavern considers your words...</span>\\n';
            input.value = '';
            output.scrollTop = output.scrollHeight;

            try {
                const response = await fetch('/api/command', {
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

                // Add response
                output.innerHTML += data.message + '\\n\\n>';
                output.scrollTop = output.scrollHeight;

                // Update LLM status
                updateStatus(data.llm_used);

            } catch (error) {
                output.innerHTML = output.innerHTML.replace(/<span class="thinking">.*?<\\/span>\\n/, '');
                output.innerHTML += '<span class="error">Error: ' + error.message + '</span>\\n\\n>';
            } finally {
                isProcessing = false;
            }
        }

        function updateStatus(llmUsed) {
            const status = document.getElementById('llm-status');
            if (llmUsed) {
                status.textContent = 'LLM: Connected';
                status.className = 'status-ok';
            } else {
                status.textContent = 'LLM: Fallback Mode';
                status.className = 'status-error';
            }
        }

        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }

        document.getElementById('command').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !isProcessing) sendCommand();
        });
    </script>
</body>
</html>
"""


def get_or_create_session(
    session_id: Optional[str] = None,
) -> tuple[GameState, EnhancedLLMGameMaster, Parser, str]:
    """Get or create a game session with all components."""
    import uuid

    if session_id and session_id in game_sessions:
        session = game_sessions[session_id]
        return session["game_state"], session["llm_gm"], session["parser"], session_id

    # Create new session
    new_session_id = str(uuid.uuid4())
    game_state = GameState()
    llm_gm = EnhancedLLMGameMaster()
    parser = Parser(use_llm=True)

    game_sessions[new_session_id] = {
        "game_state": game_state,
        "llm_gm": llm_gm,
        "parser": parser,
        "created_at": time.time(),
    }

    logger.info(f"Created new session: {new_session_id}")
    return game_state, llm_gm, parser, new_session_id


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the enhanced game interface."""
    return HTML_CONTENT


@app.post("/api/command")
async def process_command(request: Request):
    """Process natural language commands with full LLM integration."""
    try:
        data = await request.json()
        command = data.get("command", "").strip()
        session_id = data.get("session_id")

        # Get or create session
        game_state, llm_gm, parser, session_id = get_or_create_session(session_id)

        # Create game snapshot for parser context
        snapshot_data = game_state.get_snapshot()
        snapshot = GameSnapshot(
            location=snapshot_data.get("location", "tavern"),
            time_of_day=snapshot_data.get("time", {}).get("formatted_time", "evening"),
            visible_objects=snapshot_data.get(
                "visible_objects", ["bar", "tables", "fireplace"]
            ),
            visible_npcs=[npc["name"] for npc in snapshot_data.get("present_npcs", [])],
            player_state=snapshot_data.get("player", {}),
        )

        # Process through LLM Game Master for narrative understanding
        narrative_response, parsed_command, action_results = llm_gm.process_input(
            command, game_state, session_id
        )

        # If LLM provided a specific command, execute it
        if parsed_command:
            result = game_state.process_command(parsed_command)
            message = narrative_response or result.get("message", "")
        else:
            # Try parsing with the parser as fallback
            try:
                parsed = parser.parse(command, snapshot)
                if parsed["action"] != "unknown":
                    # Convert parsed command to game command
                    game_command = f"{parsed['action']}"
                    if parsed["target"]:
                        game_command += f" {parsed['target']}"

                    result = game_state.process_command(game_command)
                    message = narrative_response or result.get("message", "")
                else:
                    # Use narrative response for unknown actions
                    message = narrative_response or "I don't understand that command."
            except:
                message = narrative_response or "I don't understand that command."

        # Check if LLM was used
        llm_used = llm_gm.is_service_available()

        return {
            "message": message,
            "session_id": session_id,
            "llm_used": llm_used,
            "game_state": game_state.get_snapshot(),
        }

    except Exception as e:
        logger.error(f"Error processing command: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "sessions": len(game_sessions)}


if __name__ == "__main__":
    import time

    print("🍺 Starting The Living Rusted Tankard (Enhanced Edition)")
    print("🧠 With full LLM natural language understanding!")
    print("📍 Open http://localhost:8080 in your browser")
    print("Press Ctrl+C to stop\n")

    # Import time module for the game
    import time

    uvicorn.run(app, host="0.0.0.0", port=8080)
