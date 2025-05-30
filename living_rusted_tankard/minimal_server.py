#!/usr/bin/env python3
"""
Minimal web server for The Living Rusted Tankard using only standard library
"""
import http.server
import socketserver
import json
import os
from urllib.parse import urlparse, parse_qs

PORT = 8888

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>The Living Rusted Tankard</title>
    <style>
        body {
            background-color: #1a1a1a;
            color: #e0e0e0;
            font-family: monospace;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }
        h1 { color: #d4af37; text-align: center; }
        #output {
            background-color: #2a2a2a;
            border: 2px solid #d4af37;
            padding: 20px;
            margin: 20px 0;
            min-height: 400px;
            white-space: pre-wrap;
            font-size: 14px;
            line-height: 1.6;
        }
        #input-area {
            display: flex;
            gap: 10px;
        }
        #command {
            flex: 1;
            padding: 10px;
            background-color: #2a2a2a;
            color: #e0e0e0;
            border: 1px solid #d4af37;
            font-family: monospace;
            font-size: 14px;
        }
        button {
            background-color: #d4af37;
            color: #1a1a1a;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover { background-color: #b8941f; }
        .info { color: #888; font-size: 12px; text-align: center; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>🍺 The Living Rusted Tankard</h1>
    <div id="output">Welcome to The Rusted Tankard!

You are in the common area of the tavern. The room is dimly lit by 
lanterns and a fire crackling in a stone hearth. Wooden tables and 
chairs are scattered around, some occupied by patrons.

Type 'help' for a list of commands.

></div>
    <div id="input-area">
        <input type="text" id="command" placeholder="Enter command..." autofocus>
        <button onclick="sendCommand()">Send</button>
    </div>
    <div class="info">A text-based RPG where time moves forward and choices matter...</div>
    
    <script>
        const output = document.getElementById('output');
        const input = document.getElementById('command');
        
        function sendCommand() {
            const cmd = input.value.trim();
            if (!cmd) return;
            
            output.textContent += ' ' + cmd + '\\n';
            input.value = '';
            
            // Process command
            fetch('/cmd?command=' + encodeURIComponent(cmd))
                .then(r => r.text())
                .then(text => {
                    output.textContent += text + '\\n\\n>';
                    output.scrollTop = output.scrollHeight;
                })
                .catch(err => {
                    output.textContent += 'Error: ' + err + '\\n\\n>';
                });
        }
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendCommand();
        });
    </script>
</body>
</html>"""

class GameHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/':
            # Serve the HTML page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
            
        elif parsed.path == '/cmd':
            # Handle game commands
            params = parse_qs(parsed.query)
            command = params.get('command', [''])[0].lower()
            
            # Simple game logic
            if command == 'help':
                response = """Available commands:
  look    - Look around the current location
  wait    - Wait for time to pass
  talk    - Talk to someone in the tavern
  drink   - Order a drink at the bar
  rest    - Rest for a while
  help    - Show this help message"""
            
            elif command == 'look':
                response = """The Rusted Tankard's common room stretches before you. 
Rough wooden tables are scattered throughout, their surfaces marked 
by years of use. A large stone fireplace dominates one wall, casting 
dancing shadows across the room. The bar runs along another wall, 
bottles gleaming in the firelight. A few patrons nurse their drinks 
in the corners."""
            
            elif command == 'wait':
                response = "Time passes... An hour goes by. The tavern grows slightly busier."
            
            elif command == 'talk':
                response = """You strike up a conversation with a grizzled patron.
"Aye, strange times these days," he mutters into his ale. "Folk 
been seein' things in the cellar. Old Tom won't go down there 
no more." He takes another swig and turns away."""
            
            elif command == 'drink':
                response = """You approach the bar and order an ale.
The barkeeper slides a frothy mug your way. "That'll be 2 gold," 
he says. The ale is surprisingly good - malty with a hint of honey."""
            
            elif command == 'rest':
                response = """You find a quiet corner and rest for a while.
Your fatigue eases somewhat. Time passes peacefully."""
            
            else:
                response = f"You try to {command}, but nothing happens."
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(response.encode())
            
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        # Suppress standard logging
        pass

def main():
    print(f"🍺 Starting The Living Rusted Tankard (Minimal Server)")
    print(f"📍 Server running at http://localhost:{PORT}")
    print(f"🌐 Open this URL in your web browser")
    print(f"Press Ctrl+C to stop\n")
    
    with socketserver.TCPServer(("", PORT), GameHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()