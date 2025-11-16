#!/usr/bin/env python3
"""
AI Observer Web Interface - Watch AI play in real-time through a web GUI
"""
import asyncio
import json
import time
import random
import threading
from typing import Dict, List
import requests
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs

PORT = 8889  # Different port from main game


class AIPlayer:
    def __init__(self, name="Gemma", personality="curious_explorer"):
        self.name = name
        self.personality = personality
        self.session_id = f"ai_{random.randint(1000, 9999)}"
        self.actions = []
        self.is_playing = False
        self.current_action = ""
        self.game_state = {}

    def add_action(self, command, response, ai_type="llm"):
        """Add an action to the history"""
        self.actions.append(
            {
                "timestamp": time.time(),
                "command": command,
                "response": response,
                "ai_type": ai_type,
            }
        )
        # Keep only last 20 actions
        if len(self.actions) > 20:
            self.actions = self.actions[-20:]

    async def send_command(self, command):
        """Send command to the game"""
        try:
            self.current_action = command
            url = "http://localhost:8888/game"
            params = {"session": self.session_id, "cmd": command}

            response = requests.get(url, params=params, timeout=15)
            data = response.json()

            game_response = data.get("response", "No response")
            ai_used = data.get("ai_used", "unknown")

            self.add_action(command, game_response, ai_used)
            self.current_action = ""

            return data

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.add_action(command, error_msg, "error")
            self.current_action = ""
            return None


# Global AI player
ai_player = AIPlayer()


async def ai_play_loop():
    """Main AI playing loop"""
    actions = [
        "look around",
        "approach the notice board",
        "read notice board",
        "talk to barkeeper",
        "order a drink",
        "check inventory",
        "gamble 5",
        "talk to patrons",
        "examine fireplace",
        "ask about rumors",
        "gamble 10",
        "check bounties",
        "wait 1",
        "rest",
        "look around",
    ]

    ai_player.is_playing = True

    for i, action in enumerate(actions):
        if not ai_player.is_playing:
            break

        await ai_player.send_command(action)
        await asyncio.sleep(random.uniform(3, 7))  # Wait between actions

    # Continue with random actions
    random_actions = ["gamble 10", "talk", "drink", "look", "wait 1", "inventory"]

    while ai_player.is_playing:
        action = random.choice(random_actions)
        await ai_player.send_command(action)
        await asyncio.sleep(random.uniform(4, 8))


# Start AI in background thread
def start_ai_background():
    """Start AI in background thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ai_play_loop())


# HTML Interface
HTML_CONTENT = """<!DOCTYPE html>
<html>
<head>
    <title>AI Observer - The Living Rusted Tankard</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
            color: #e0e0e0;
            font-family: 'Georgia', serif;
            min-height: 100vh;
        }

        #header {
            background-color: #1a1a1a;
            border-bottom: 3px solid #d4af37;
            padding: 20px;
            text-align: center;
        }

        h1 {
            color: #d4af37;
            font-size: 2.5em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        }

        #main-container {
            display: flex;
            height: calc(100vh - 120px);
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            gap: 20px;
        }

        #actions-panel {
            flex: 1;
            background-color: #1a1a1a;
            border: 2px solid #d4af37;
            border-radius: 10px;
            padding: 20px;
            overflow-y: auto;
        }

        #status-panel {
            width: 350px;
            background-color: #1a1a1a;
            border: 2px solid #d4af37;
            border-radius: 10px;
            padding: 20px;
        }

        h2 {
            color: #d4af37;
            margin-top: 0;
            border-bottom: 1px solid #444;
            padding-bottom: 10px;
        }

        .action-item {
            background-color: #0f0f0f;
            border-left: 4px solid #d4af37;
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 5px;
            animation: slideIn 0.5s ease-out;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .action-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .action-command {
            font-weight: bold;
            color: #60a5fa;
            font-size: 16px;
        }

        .action-time {
            font-size: 12px;
            color: #888;
        }

        .action-response {
            color: #e0e0e0;
            line-height: 1.6;
            margin-top: 10px;
            max-height: 100px;
            overflow-y: auto;
        }

        .ai-type {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
        }

        .ai-type.llm {
            background-color: #4ade80;
            color: #1a1a1a;
        }

        .ai-type.parser {
            background-color: #fbbf24;
            color: #1a1a1a;
        }

        .ai-type.error {
            background-color: #ff6b6b;
            color: #1a1a1a;
        }

        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #333;
        }

        .status-label {
            color: #999;
        }

        .status-value {
            color: #d4af37;
            font-weight: bold;
        }

        #current-action {
            background-color: #2a2a2a;
            border: 1px solid #d4af37;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
        }

        .thinking {
            color: #d4af37;
            font-style: italic;
        }

        #controls {
            margin-top: 20px;
        }

        button {
            background: linear-gradient(45deg, #d4af37, #f0d060);
            color: #1a1a1a;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            font-weight: bold;
            border-radius: 5px;
            margin: 5px;
            transition: all 0.3s;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(212, 175, 55, 0.4);
        }

        button:disabled {
            background: #666;
            cursor: not-allowed;
            transform: none;
        }

        #footer {
            text-align: center;
            padding: 10px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div id="header">
        <h1>🤖 AI Observer - The Living Rusted Tankard</h1>
        <p>Watch Gemma the Explorer play autonomously</p>
    </div>

    <div id="main-container">
        <div id="actions-panel">
            <h2>🎬 AI Actions Stream</h2>
            <div id="actions-list">
                <div class="action-item">
                    <div class="action-header">
                        <span class="action-command">Initializing...</span>
                        <span class="ai-type llm">SYSTEM</span>
                    </div>
                    <div class="action-response">AI player starting up...</div>
                </div>
            </div>
        </div>

        <div id="status-panel">
            <h2>🤖 AI Status</h2>
            <div id="current-action">
                <div class="thinking">Preparing to start...</div>
            </div>

            <div class="status-item">
                <span class="status-label">AI Name:</span>
                <span class="status-value" id="ai-name">Gemma</span>
            </div>
            <div class="status-item">
                <span class="status-label">Actions Taken:</span>
                <span class="status-value" id="action-count">0</span>
            </div>
            <div class="status-item">
                <span class="status-label">Status:</span>
                <span class="status-value" id="ai-status">Starting</span>
            </div>
            <div class="status-item">
                <span class="status-label">Session ID:</span>
                <span class="status-value" id="session-id">-</span>
            </div>

            <div id="controls">
                <h2>🎛️ Controls</h2>
                <button onclick="startAI()" id="start-btn">Start AI</button>
                <button onclick="stopAI()" id="stop-btn" disabled>Stop AI</button>
                <button onclick="clearActions()">Clear Log</button>
            </div>

            <div id="help">
                <h2>💡 About</h2>
                <p>This interface shows Gemma the AI playing The Living Rusted Tankard autonomously. Watch as she explores, talks to NPCs, gambles, and experiences the full game world.</p>
                <p>The main game runs at <a href="http://localhost:8888" target="_blank">localhost:8888</a></p>
            </div>
        </div>
    </div>

    <div id="footer">
        AI Observer Interface - Real-time AI gameplay monitoring
    </div>

    <script>
        let isMonitoring = false;

        async function fetchAIStatus() {
            try {
                const response = await fetch('/ai-status');
                const data = await response.json();

                document.getElementById('ai-name').textContent = data.name;
                document.getElementById('action-count').textContent = data.actions.length;
                document.getElementById('ai-status').textContent = data.is_playing ? 'Playing' : 'Stopped';
                document.getElementById('session-id').textContent = data.session_id;

                // Update current action
                const currentAction = document.getElementById('current-action');
                if (data.current_action) {
                    currentAction.innerHTML = '<span class="thinking">🤔 Thinking: "' + data.current_action + '"</span>';
                } else {
                    currentAction.innerHTML = '<span class="thinking">💭 Waiting for next action...</span>';
                }

                // Update actions list
                updateActionsList(data.actions);

            } catch (error) {
                console.error('Error fetching AI status:', error);
            }
        }

        function updateActionsList(actions) {
            const actionsList = document.getElementById('actions-list');

            // Add new actions (keep existing ones)
            const currentCount = actionsList.children.length - 1; // -1 for initial message

            for (let i = currentCount; i < actions.length; i++) {
                const action = actions[i];
                const actionDiv = document.createElement('div');
                actionDiv.className = 'action-item';

                const time = new Date(action.timestamp * 1000).toLocaleTimeString();
                const aiTypeClass = action.ai_type === 'llm' ? 'llm' : action.ai_type === 'error' ? 'error' : 'parser';

                actionDiv.innerHTML = `
                    <div class="action-header">
                        <span class="action-command">${action.command}</span>
                        <span class="action-time">${time}</span>
                    </div>
                    <span class="ai-type ${aiTypeClass}">${action.ai_type.toUpperCase()}</span>
                    <div class="action-response">${action.response.substring(0, 300)}${action.response.length > 300 ? '...' : ''}</div>
                `;

                actionsList.appendChild(actionDiv);
            }

            // Auto-scroll to bottom
            actionsList.scrollTop = actionsList.scrollHeight;
        }

        async function startAI() {
            try {
                await fetch('/start-ai', { method: 'POST' });
                document.getElementById('start-btn').disabled = true;
                document.getElementById('stop-btn').disabled = false;
                isMonitoring = true;
            } catch (error) {
                console.error('Error starting AI:', error);
            }
        }

        async function stopAI() {
            try {
                await fetch('/stop-ai', { method: 'POST' });
                document.getElementById('start-btn').disabled = false;
                document.getElementById('stop-btn').disabled = true;
                isMonitoring = false;
            } catch (error) {
                console.error('Error stopping AI:', error);
            }
        }

        function clearActions() {
            const actionsList = document.getElementById('actions-list');
            actionsList.innerHTML = '<div class="action-item"><div class="action-header"><span class="action-command">Log cleared</span><span class="ai-type llm">SYSTEM</span></div><div class="action-response">Action history cleared.</div></div>';
        }

        // Update every 2 seconds
        setInterval(fetchAIStatus, 2000);

        // Initial load
        fetchAIStatus();
    </script>
</body>
</html>"""


class AIObserverHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())

        elif parsed.path == "/ai-status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            response = {
                "name": ai_player.name,
                "session_id": ai_player.session_id,
                "is_playing": ai_player.is_playing,
                "current_action": ai_player.current_action,
                "actions": ai_player.actions,
            }

            self.wfile.write(json.dumps(response).encode())

        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/start-ai":
            if not ai_player.is_playing:
                # Start AI in background thread
                threading.Thread(target=start_ai_background, daemon=True).start()

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode())

        elif parsed.path == "/stop-ai":
            ai_player.is_playing = False

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode())

        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


def main():
    print("🤖 AI Observer Web Interface")
    print(f"📍 Starting on http://localhost:{PORT}")
    print("🎮 Make sure the main game is running on http://localhost:8888")
    print("Press Ctrl+C to stop\n")

    with socketserver.TCPServer(("", PORT), AIObserverHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            ai_player.is_playing = False
            print("\n🛑 AI Observer stopped")


if __name__ == "__main__":
    main()
