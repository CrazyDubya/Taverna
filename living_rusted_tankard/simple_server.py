#!/usr/bin/env python3
"""
Simplified server for The Living Rusted Tankard
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(title="The Living Rusted Tankard")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple HTML interface
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>The Living Rusted Tankard</title>
    <style>
        body {
            background-color: #1a1a1a;
            color: #e0e0e0;
            font-family: 'Courier New', monospace;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }
        h1 { color: #d4af37; }
        #game-output {
            background-color: #2a2a2a;
            border: 1px solid #444;
            padding: 20px;
            margin: 20px 0;
            min-height: 300px;
            white-space: pre-wrap;
        }
        #command-input {
            width: 100%;
            padding: 10px;
            background-color: #2a2a2a;
            color: #e0e0e0;
            border: 1px solid #444;
            font-family: inherit;
        }
        button {
            background-color: #d4af37;
            color: #1a1a1a;
            border: none;
            padding: 10px 20px;
            margin: 10px 0;
            cursor: pointer;
        }
        button:hover { background-color: #b8941f; }
    </style>
</head>
<body>
    <h1>🍺 The Living Rusted Tankard</h1>
    <p>A text-based RPG where time moves forward and choices matter...</p>

    <div id="game-output">Welcome to The Rusted Tankard!
Type 'help' for commands.

You are in the common area of the Rusted Tankard tavern.
The room is dimly lit by lanterns and a fire crackling in a stone hearth.

Available commands: look, wait, help, quit
</div>

    <input type="text" id="command-input" placeholder="Enter command..." autofocus>
    <button onclick="sendCommand()">Send</button>
    <button onclick="clearOutput()">Clear</button>

    <script>
        let gameState = null;

        async function sendCommand() {
            const input = document.getElementById('command-input');
            const output = document.getElementById('game-output');
            const command = input.value.trim();

            if (!command) return;

            output.textContent += '\\n> ' + command + '\\n';
            input.value = '';

            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: command })
                });

                const data = await response.json();
                output.textContent += data.output + '\\n';
                output.scrollTop = output.scrollHeight;

            } catch (error) {
                output.textContent += 'Error: ' + error.message + '\\n';
            }
        }

        function clearOutput() {
            document.getElementById('game-output').textContent = 'Game output cleared.\\n';
        }

        document.getElementById('command-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendCommand();
        });
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the game interface"""
    return HTML_CONTENT


@app.post("/api/command")
async def process_command(request_data: dict):
    """Process game commands"""
    command = request_data.get("command", "").strip()

    # Simple command responses for testing
    responses = {
        "look": "You are in the common area of the Rusted Tankard tavern. The room is dimly lit by lanterns and a fire crackling in a stone hearth. Wooden tables and chairs are scattered around.",
        "help": "Available commands: look, wait, help, inventory, quit",
        "wait": "Time passes... It is now evening.",
        "inventory": "You have 20 gold coins and some basic supplies.",
        "quit": "Thanks for playing The Living Rusted Tankard!",
    }

    output = responses.get(command.lower(), f"You {command}. Nothing happens.")

    return {"output": output, "success": True}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "message": "Server is running"}


if __name__ == "__main__":
    print("🚀 Starting The Living Rusted Tankard (Simple Mode)")
    print("📍 Open http://localhost:8080 in your browser")
    print("Press Ctrl+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=8080)
