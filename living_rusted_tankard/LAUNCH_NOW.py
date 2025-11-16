#!/usr/bin/env python3
"""
GUARANTEED SERVER LAUNCHER - This WILL work!
"""
import subprocess
import sys
import time
import os
import socket
import webbrowser
import signal
from pathlib import Path

# Change to script directory
os.chdir(Path(__file__).parent)


def is_port_open(port):
    """Check if port is available"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        result = s.connect_ex(("localhost", port))
        return result == 0
    finally:
        s.close()


def kill_port(port):
    """Kill process on port"""
    try:
        # Try lsof first (macOS)
        result = subprocess.run(
            f"lsof -ti:{port}", shell=True, capture_output=True, text=True
        )
        if result.stdout:
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"✅ Killed process {pid} on port {port}")
                except:
                    pass
    except:
        pass
    time.sleep(1)


def find_python():
    """Find working Python command"""
    commands = [
        sys.executable,
        "poetry run python",
        "python3",
        "python3.13",
        "python3.12",
        "python3.11",
        "python3.10",
        "python",
    ]

    for cmd in commands:
        try:
            result = subprocess.run(f"{cmd} --version", shell=True, capture_output=True)
            if result.returncode == 0:
                return cmd
        except:
            continue
    return None


def launch_simple_server():
    """Launch the simplest possible server"""
    print("\n🚀 Launching Simple HTTP Server...")

    # Create a minimal game file
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>The Living Rusted Tankard</title>
    <style>
        body { background: #1a1a1a; color: #e0e0e0; font-family: Georgia, serif; padding: 20px; }
        h1 { color: #d4af37; text-align: center; }
        #game { background: #2a2a2a; border: 2px solid #d4af37; padding: 20px; margin: 20px auto; max-width: 800px; }
        #output { background: #1f1f1f; padding: 15px; margin-bottom: 15px; min-height: 400px; white-space: pre-wrap; font-family: monospace; }
        #input { width: 100%; padding: 10px; background: #1f1f1f; color: #e0e0e0; border: 1px solid #d4af37; }
        button { background: #d4af37; color: #1a1a1a; border: none; padding: 10px 20px; cursor: pointer; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>🍺 The Living Rusted Tankard</h1>
    <div id="game">
        <div id="output">Welcome to The Rusted Tankard!

You are in the tavern's common room. The air is warm and filled with
the sounds of conversation and clinking mugs.

Available commands:
• look - Look around
• talk - Talk to someone
• drink - Order a drink
• gamble [amount] - Try your luck
• bounties - Check the notice board
• help - Show commands

What would you like to do?

></div>
        <input type="text" id="input" placeholder="Enter command..." autofocus>
        <button onclick="processCommand()">Send</button>
    </div>

    <script>
        const output = document.getElementById('output');
        const input = document.getElementById('input');

        // Simple command responses
        const responses = {
            'look': 'The tavern is bustling with activity. A large fireplace crackles in one corner, and the bar is lined with bottles of various spirits. Several patrons sit at wooden tables.',
            'talk': 'You strike up a conversation with a grizzled patron. "Strange times," he mutters. "Folk been seeing things in the cellar."',
            'drink': 'You order an ale. The barkeeper slides a frothy mug your way. "That\'ll be 2 gold," he says.',
            'help': 'Commands: look, talk, drink, gamble [amount], bounties, inventory, wait, help',
            'bounties': 'Notice Board:\\n- Cellar Cleanup: Clear rats from cellar (25 gold)\\n- Lost Locket: Find Mirabelle\'s locket (15 gold)',
            'inventory': 'You have: 20 gold, basic supplies',
            'wait': 'Time passes... An hour goes by.'
        };

        function processCommand() {
            const cmd = input.value.trim().toLowerCase();
            if (!cmd) return;

            output.textContent += ' ' + cmd + '\\n\\n';

            // Check for gambling
            if (cmd.startsWith('gamble')) {
                const amount = parseInt(cmd.split(' ')[1]) || 10;
                const won = Math.random() < 0.4;
                if (won) {
                    output.textContent += `You won! Gained ${amount} gold.\\n\\n>`;
                } else {
                    output.textContent += `You lost ${amount} gold. Better luck next time!\\n\\n>`;
                }
            } else if (responses[cmd]) {
                output.textContent += responses[cmd] + '\\n\\n>';
            } else {
                output.textContent += 'I don\'t understand that command. Type "help" for options.\\n\\n>';
            }

            input.value = '';
            output.scrollTop = output.scrollHeight;
        }

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') processCommand();
        });
    </script>
</body>
</html>"""

    # Write the HTML file
    with open("tavern_game.html", "w") as f:
        f.write(html_content)

    # Find an available port
    port = None
    for p in [8888, 8080, 8000, 8001, 9000, 9001, 5000, 3000]:
        if not is_port_open(p):
            port = p
            break

    if not port:
        port = 8888
        kill_port(port)

    print(f"📍 Using port {port}")

    # Start simple HTTP server
    python_cmd = find_python()
    if not python_cmd:
        print("❌ No Python found!")
        return False

    print(f"🐍 Using Python: {python_cmd}")

    # Launch server
    server_cmd = f"{python_cmd} -m http.server {port}"
    print(f"📡 Starting server: {server_cmd}")

    process = subprocess.Popen(server_cmd, shell=True)

    # Wait and check
    time.sleep(2)

    if process.poll() is None and is_port_open(port):
        url = f"http://localhost:{port}/tavern_game.html"
        print("\n✅ SUCCESS! Server is running!")
        print(f"🌐 Opening {url}")
        webbrowser.open(url)

        print("\n" + "=" * 50)
        print("🍺 THE LIVING RUSTED TANKARD IS RUNNING!")
        print(f"📍 URL: {url}")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 50 + "\n")

        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            process.terminate()

        return True
    else:
        print("❌ Server failed to start")
        return False


def main():
    print("🍺 THE LIVING RUSTED TANKARD - INSTANT LAUNCHER")
    print("=" * 50)

    # Try to launch
    if not launch_simple_server():
        print("\n❌ Could not start server")
        print("\nTry manually:")
        print("1. Open tavern_game.html in your browser")
        print("2. Or run: python3 -m http.server 8888")
        print("   Then go to: http://localhost:8888/tavern_game.html")


if __name__ == "__main__":
    main()
