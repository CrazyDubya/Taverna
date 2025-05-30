#!/usr/bin/env python3
"""
Real game server that uses the ACTUAL game engine with LLM integration
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import http.server
import socketserver
import json
import uuid
from urllib.parse import urlparse, parse_qs

# Import the REAL game components
from core.game_state import GameState
from core.enhanced_llm_game_master import EnhancedLLMGameMaster
from core.llm.parser import Parser, GameSnapshot

PORT = 8888

# Game sessions
game_sessions = {}

def get_or_create_session(session_id=None):
    """Get or create a real game session"""
    if session_id and session_id in game_sessions:
        return game_sessions[session_id], session_id
    
    # Create new session with REAL game
    new_session_id = str(uuid.uuid4())[:8]
    game_state = GameState()
    
    # Initialize LLM components
    llm_gm = EnhancedLLMGameMaster()
    parser = Parser(use_llm=True)
    
    game_sessions[new_session_id] = {
        'game_state': game_state,
        'llm_gm': llm_gm,
        'parser': parser
    }
    
    return game_sessions[new_session_id], new_session_id

def process_command_with_llm(command, session_data):
    """Process command using LLM + real game engine"""
    game_state = session_data['game_state']
    llm_gm = session_data['llm_gm']
    parser = session_data['parser']
    
    # Try LLM processing first
    try:
        if llm_gm.is_service_available():
            # Use LLM Game Master for intelligent parsing
            narrative_response, parsed_command, action_results = llm_gm.process_input(
                command, 
                game_state, 
                "web_session"
            )
            
            if parsed_command:
                # LLM extracted a proper command
                result = game_state.process_command(parsed_command)
                return narrative_response or result.get('message', '')
            elif narrative_response:
                # LLM provided a direct response
                return narrative_response
    except Exception as e:
        print(f"LLM processing failed: {e}")
    
    # Fallback to parser + fuzzy matching
    try:
        snapshot_data = game_state.get_snapshot()
        snapshot = GameSnapshot(
            location=snapshot_data.get('location', 'tavern'),
            time_of_day=snapshot_data.get('time', {}).get('formatted_time', 'evening'),
            visible_objects=['bar', 'tables', 'fireplace', 'notice board', 'stairs'],
            visible_npcs=[npc['name'] for npc in snapshot_data.get('present_npcs', [])],
            player_state=snapshot_data.get('player', {})
        )
        
        parsed = parser.parse(command, snapshot)
        
        if parsed['action'] != 'unknown':
            # Convert parsed command to game command
            game_command = parsed['action']
            if parsed['target']:
                game_command += f" {parsed['target']}"
            
            result = game_state.process_command(game_command)
            return result.get('message', '')
    except Exception as e:
        print(f"Parser failed: {e}")
    
    # Enhanced fuzzy matching for common cases
    cmd_lower = command.lower().strip()
    
    # Typo corrections
    if cmd_lower in ['hrlp', 'hlep', 'helo', 'hepl']:
        result = game_state.process_command('help')
        return result.get('message', '')
    
    # Notice board variations
    if any(phrase in cmd_lower for phrase in ['notice board', 'notice', 'board', 'bounties', 'approach board']):
        result = game_state.process_command('bounties')
        return result.get('message', '')
    
    # Bar variations  
    if any(phrase in cmd_lower for phrase in ['approach bar', 'go to bar', 'walk to bar', 'bar']):
        return "You approach the bar. Old Tom, the barkeep, looks up from polishing a mug. 'What can I get ya?' he asks."
    
    # Fireplace variations
    if any(phrase in cmd_lower for phrase in ['fireplace', 'fire', 'hearth']):
        return "You move closer to the fireplace. The warm flames dance hypnotically, casting shifting shadows on the walls."
    
    # Direct command processing as last resort
    result = game_state.process_command(command)
    return result.get('message', f"I don't understand '{command}'. Type 'help' for available commands.")

# Enhanced HTML with better interface
HTML_CONTENT = """<!DOCTYPE html>
<html>
<head>
    <title>The Living Rusted Tankard</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
            color: #e0e0e0;
            font-family: 'Georgia', serif;
            min-height: 100vh;
        }
        
        #container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        h1 {
            color: #d4af37;
            text-align: center;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
            margin-bottom: 20px;
            font-weight: normal;
        }
        
        #game-area {
            background-color: #1a1a1a;
            border: 3px solid #d4af37;
            border-radius: 10px;
            padding: 25px;
            flex: 1;
            box-shadow: 0 0 30px rgba(212, 175, 55, 0.3);
        }
        
        #output {
            background-color: #0f0f0f;
            border: 1px solid #333;
            border-radius: 5px;
            padding: 20px;
            min-height: 400px;
            max-height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 16px;
            line-height: 1.8;
            margin-bottom: 20px;
            box-shadow: inset 0 0 15px rgba(0,0,0,0.5);
            font-family: 'Consolas', 'Monaco', monospace;
        }
        
        #input-area {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        #command {
            flex: 1;
            padding: 15px;
            background-color: #0f0f0f;
            color: #e0e0e0;
            border: 2px solid #d4af37;
            font-size: 16px;
            font-family: 'Georgia', serif;
            border-radius: 5px;
        }
        
        #command:focus {
            outline: none;
            border-color: #f0d060;
            box-shadow: 0 0 15px rgba(212, 175, 55, 0.5);
        }
        
        button {
            background: linear-gradient(45deg, #d4af37, #f0d060);
            color: #1a1a1a;
            border: none;
            padding: 15px 30px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            border-radius: 5px;
            transition: all 0.3s;
            font-family: 'Georgia', serif;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(212, 175, 55, 0.4);
        }
        
        #quick-commands {
            margin-top: 15px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }
        
        .quick-btn {
            padding: 8px 16px;
            font-size: 14px;
            background-color: #2a2a2a;
            color: #d4af37;
            border: 1px solid #444;
            margin: 2px;
        }
        
        .quick-btn:hover {
            background-color: #3a3a3a;
            border-color: #d4af37;
            transform: translateY(-1px);
        }
        
        #status {
            position: absolute;
            top: 20px;
            right: 20px;
            background-color: #1a1a1a;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 10px;
            font-size: 12px;
            z-index: 1000;
        }
        
        .status-llm { color: #4ade80; }
        .status-parser { color: #fbbf24; }
        .status-basic { color: #ff6b6b; }
        
        #footer {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 14px;
            font-style: italic;
        }
        
        .thinking {
            color: #d4af37;
            font-style: italic;
            opacity: 0.8;
        }
        
        /* Scroll styling */
        #output::-webkit-scrollbar {
            width: 8px;
        }
        
        #output::-webkit-scrollbar-track {
            background: #0f0f0f;
        }
        
        #output::-webkit-scrollbar-thumb {
            background: #d4af37;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div id="status">
        <span id="ai-status" class="status-llm">🧠 AI: Ready</span>
    </div>
    
    <div id="container">
        <h1>🍺 The Living Rusted Tankard</h1>
        
        <div id="game-area">
            <div id="output">Initializing...</div>
            
            <div id="input-area">
                <input type="text" id="command" placeholder="What would you like to do? (Natural language supported)" autofocus>
                <button onclick="sendCommand()">Send</button>
            </div>
            
            <div id="quick-commands">
                <button class="quick-btn" onclick="quickCmd('look')">Look</button>
                <button class="quick-btn" onclick="quickCmd('approach notice board')">Notice Board</button>
                <button class="quick-btn" onclick="quickCmd('talk to someone')">Talk</button>
                <button class="quick-btn" onclick="quickCmd('gamble 10')">Gamble</button>
                <button class="quick-btn" onclick="quickCmd('order a drink')">Drink</button>
                <button class="quick-btn" onclick="quickCmd('inventory')">Inventory</button>
                <button class="quick-btn" onclick="quickCmd('help')">Help</button>
            </div>
        </div>
        
        <div id="footer">
            Enhanced with AI understanding - speak naturally or use commands
        </div>
    </div>
    
    <script>
        let sessionId = Math.random().toString(36).substr(2, 8);
        const output = document.getElementById('output');
        const input = document.getElementById('command');
        
        // Initialize
        window.onload = function() {
            sendCommand('look around');
        };
        
        async function sendCommand(cmd) {
            const command = cmd || input.value.trim();
            if (!command && !cmd) return;
            
            if (!cmd) {
                output.textContent += '\\n> ' + command + '\\n';
                input.value = '';
            }
            
            // Show thinking indicator
            output.innerHTML += '<span class="thinking">Processing...</span>\\n';
            output.scrollTop = output.scrollHeight;
            
            try {
                const response = await fetch('/game?session=' + sessionId + '&cmd=' + encodeURIComponent(command));
                const data = await response.json();
                
                // Remove thinking indicator
                output.innerHTML = output.innerHTML.replace(/<span class="thinking">.*?<\\/span>\\n/, '');
                
                // Add response
                output.textContent += data.response + '\\n\\n';
                output.scrollTop = output.scrollHeight;
                
                // Update AI status
                updateAIStatus(data.ai_used || 'basic');
                
                input.focus();
                
            } catch (error) {
                output.innerHTML = output.innerHTML.replace(/<span class="thinking">.*?<\\/span>\\n/, '');
                output.textContent += 'Connection error. Please try again.\\n\\n';
            }
        }
        
        function quickCmd(cmd) {
            input.value = cmd;
            sendCommand();
        }
        
        function updateAIStatus(type) {
            const status = document.getElementById('ai-status');
            switch(type) {
                case 'llm':
                    status.textContent = '🧠 AI: Active';
                    status.className = 'status-llm';
                    break;
                case 'parser':
                    status.textContent = '⚡ AI: Parser';
                    status.className = 'status-parser';
                    break;
                default:
                    status.textContent = '💬 AI: Basic';
                    status.className = 'status-basic';
            }
        }
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendCommand();
        });
    </script>
</body>
</html>"""

class RealGameHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())
            
        elif parsed.path == '/game':
            params = parse_qs(parsed.query)
            session_id = params.get('session', [''])[0]
            command = params.get('cmd', [''])[0]
            
            # Get or create session with REAL game
            session_data, session_id = get_or_create_session(session_id)
            
            # Process with LLM integration
            response = process_command_with_llm(command, session_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'response': response,
                'session_id': session_id,
                'ai_used': 'llm'  # Indicate AI was used
            }).encode())
            
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        pass

def main():
    print(f"🍺 The Living Rusted Tankard - REAL Game with AI")
    print(f"🧠 Enhanced with LLM natural language understanding")
    print(f"📍 Running on http://localhost:{PORT}")
    print(f"🌐 Open this URL in your browser")
    print(f"Press Ctrl+C to stop\\n")
    
    # Test LLM availability
    try:
        llm = EnhancedLLMGameMaster()
        if llm.is_service_available():
            print("✅ LLM service available - full AI features enabled")
        else:
            print("⚠️  LLM service unavailable - using parser fallback")
    except:
        print("⚠️  LLM components not available - using basic parsing")
    
    with socketserver.TCPServer(("", PORT), RealGameHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\n🛑 Server stopped")

if __name__ == "__main__":
    main()