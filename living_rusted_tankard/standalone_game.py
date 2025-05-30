#!/usr/bin/env python3
"""
Standalone Living Rusted Tankard - Full Game Experience
No external dependencies required!
"""
import http.server
import socketserver
import json
import random
import time
from urllib.parse import urlparse, parse_qs
import threading

PORT = 8888

# Game state storage
game_sessions = {}

class GameSession:
    def __init__(self):
        self.gold = 20
        self.tiredness = 0
        self.inventory = {"bread": 1, "ale": 1}
        self.location = "tavern_main"
        self.has_room = False
        self.time_hours = 18.0  # 6 PM start
        self.npcs_present = ["Old Tom (Barkeep)", "Mirabelle", "Gruff Patron"]
        self.active_bounties = []
        self.completed_bounties = []
        
    def get_time_string(self):
        hour = int(self.time_hours % 24)
        if hour < 6: return "Deep night"
        elif hour < 12: return "Morning"
        elif hour < 18: return "Afternoon"
        else: return "Evening"
    
    def advance_time(self, hours=0.5):
        self.time_hours += hours
        self.tiredness += hours * 0.1
        if self.tiredness > 1.0:
            self.tiredness = 1.0
            
    def process_command(self, command):
        cmd = command.lower().strip()
        self.advance_time(0.25)  # Each action takes 15 minutes
        
        # LOOK command with rich descriptions
        if cmd in ['look', 'l', 'look around']:
            return self.look_around()
            
        # TALK command
        elif cmd.startswith('talk') or cmd.startswith('speak'):
            return self.talk_to_npc()
            
        # GAMBLING
        elif cmd.startswith('gamble') or cmd.startswith('bet'):
            return self.gamble(cmd)
            
        # DRINK
        elif cmd in ['drink', 'order drink', 'buy drink', 'get ale']:
            return self.order_drink()
            
        # BOUNTIES
        elif cmd in ['bounties', 'read notice board', 'notice board', 'check bounties']:
            return self.show_bounties()
            
        # ACCEPT BOUNTY
        elif cmd.startswith('accept bounty'):
            return self.accept_bounty(cmd)
            
        # INVENTORY
        elif cmd in ['inventory', 'inv', 'i']:
            return self.show_inventory()
            
        # STATUS
        elif cmd in ['status', 'stats']:
            return self.show_status()
            
        # WAIT
        elif cmd.startswith('wait'):
            return self.wait(cmd)
            
        # HELP
        elif cmd in ['help', 'h', '?']:
            return self.show_help()
            
        # WORK/JOBS
        elif cmd in ['jobs', 'work', 'available jobs']:
            return self.show_jobs()
            
        # DO JOB
        elif cmd.startswith('work') and len(cmd.split()) > 1:
            return self.do_job(cmd)
            
        # REST
        elif cmd in ['rest', 'sleep']:
            return self.rest()
            
        # Natural language fallbacks
        elif 'bar' in cmd and ('go' in cmd or 'walk' in cmd or 'approach' in cmd):
            return "You approach the bar. Old Tom nods at you while polishing a tankard. The wooden bar is worn smooth by countless elbows, and bottles of various spirits line the shelves behind."
            
        elif 'fireplace' in cmd or 'fire' in cmd:
            return "You move closer to the fireplace. The warmth is welcome after the chill outside. The stones are blackened with age, and you can see faces in the dancing flames. A few patrons sit nearby, warming their hands."
            
        else:
            return f"You try to {cmd}, but aren't sure how. Type 'help' for available commands."
    
    def look_around(self):
        desc = f"""The Rusted Tankard - {self.get_time_string()}

You stand in the heart of The Rusted Tankard, a tavern that has weathered centuries of storms, 
celebrations, and secrets. The main room sprawls before you, its low-beamed ceiling darkened 
by years of pipe smoke and cooking fires.

The massive stone FIREPLACE dominates the eastern wall, its flames casting dancing shadows across 
worn wooden tables where patrons huddle over their drinks. The ancient BAR runs along the northern 
wall, its surface scarred by countless mugs and etched with the initials of long-dead regulars.

A NOTICE BOARD near the entrance is covered with parchments - bounties, jobs, and mysterious requests. 
The wooden STAIRS in the corner lead up to the guest rooms, creaking with every footstep.

Present here: {', '.join(self.npcs_present)}

The air is thick with the scent of roasted meat, spilled ale, and burning oak. You can hear 
the low murmur of conversation, punctuated by occasional laughter or the clink of coins on wood."""
        
        if self.tiredness > 0.7:
            desc += "\n\nYou feel exhausted. Perhaps you should rest soon."
        elif self.tiredness > 0.4:
            desc += "\n\nYou're starting to feel tired."
            
        return desc
    
    def talk_to_npc(self):
        if not self.npcs_present:
            return "There's no one here to talk to right now."
            
        npc = random.choice(self.npcs_present)
        
        responses = {
            "Old Tom (Barkeep)": [
                "Old Tom leans across the bar, his weathered face creasing into a knowing smile. 'Been keepin' this place for nigh on forty years. Seen all sorts come through that door. You look like you might have a story or two yourself.'",
                "The barkeep pauses in his glass-polishing. 'If you're lookin' for work, I could use help with the cellar. Rats the size of cats down there, I swear it. Check the notice board if you're interested.'",
                "'Ah, you want to know about the tankard?' Old Tom gestures to the sign. 'Legend says it belonged to a dwarf lord, centuries past. The rust ain't rust at all - it's dried dragon's blood. Course, that's just a tale to bring in customers.' He winks."
            ],
            "Mirabelle": [
                "Mirabelle looks up from her drink, tears in her eyes. 'Oh, I'm sorry. It's just... I've lost my mother's locket. Silver, with a blue stone. I think I dropped it near the fireplace, but I've looked everywhere.'",
                "The young woman manages a sad smile. 'I've posted a bounty for my locket. It's not much, but it's all I can afford. That locket means everything to me.'",
                "'This place has so many memories,' Mirabelle says softly. 'My parents met here, you know. Right at that table by the window.'"
            ],
            "Gruff Patron": [
                "'What you lookin' at?' the patron growls, then softens. 'Ah, don't mind me. Lost a fair bit at dice tonight. If you're smart, you'll stay away from the gambling.'",
                "The man takes a long pull from his mug. 'Been strange happenings lately. Folks disappearing, weird sounds from the cellar. Mark my words, something ain't right in this town.'",
                "'You new here? Word of advice - don't trust everyone you meet. This tavern attracts all sorts, and not all of 'em honest folk.'"
            ]
        }
        
        return random.choice(responses.get(npc, ["They nod at you but seem uninterested in conversation."]))
    
    def gamble(self, cmd):
        parts = cmd.split()
        try:
            amount = int(parts[1]) if len(parts) > 1 else 10
        except:
            amount = 10
            
        if amount > self.gold:
            return f"You don't have {amount} gold to gamble. You only have {self.gold} gold."
            
        if amount <= 0:
            return "You need to bet at least 1 gold."
            
        # Dice game
        player_roll = random.randint(1, 6) + random.randint(1, 6)
        house_roll = random.randint(1, 6) + random.randint(1, 6)
        
        if player_roll > house_roll:
            self.gold += amount
            return f"""You shake the dice in your hand and let them fly across the worn table.
Your roll: {player_roll}
House roll: {house_roll}

The crowd cheers! You won {amount} gold!
You now have {self.gold} gold."""
        else:
            self.gold -= amount
            return f"""You shake the dice in your hand and let them fly across the worn table.
Your roll: {player_roll}
House roll: {house_roll}

The house wins. You lost {amount} gold.
You now have {self.gold} gold."""
    
    def order_drink(self):
        if self.gold < 2:
            return "You don't have enough gold for a drink. Ale costs 2 gold."
            
        self.gold -= 2
        self.tiredness -= 0.1
        if self.tiredness < 0:
            self.tiredness = 0
            
        self.inventory["ale"] = self.inventory.get("ale", 0) + 1
        
        return f"""Old Tom fills a pewter mug with foaming ale and slides it across the bar.
"That'll be 2 gold," he says.

The ale is rich and malty, with hints of honey and herbs. You feel refreshed.
You now have {self.gold} gold."""
    
    def show_bounties(self):
        return """NOTICE BOARD - Active Bounties:

1. CELLAR CLEANUP (ID: rats_001)
   Posted by: Old Tom
   Task: Clear the giant rats from the tavern cellar
   Reward: 25 gold
   "They're eating all my supplies! Please help!"

2. LOST LOCKET (ID: locket_001)
   Posted by: Mirabelle
   Task: Find a silver locket with blue stone, lost near fireplace
   Reward: 15 gold + Ale Token
   "It was my mother's. Please, I'll give anything to have it back."

3. MYSTERIOUS SOUNDS (ID: sounds_001)
   Posted by: Town Guard
   Task: Investigate strange noises coming from the old warehouse
   Reward: 40 gold
   "Experienced adventurers only. May be dangerous."

Type 'accept bounty [id]' to accept a bounty."""
    
    def accept_bounty(self, cmd):
        bounty_id = cmd.replace('accept bounty', '').strip()
        
        if not bounty_id:
            return "Which bounty would you like to accept? Use: accept bounty [id]"
            
        if bounty_id in ['rats_001', 'locket_001', 'sounds_001']:
            if bounty_id not in self.active_bounties:
                self.active_bounties.append(bounty_id)
                return f"You've accepted the bounty: {bounty_id}. Good luck!"
            else:
                return "You've already accepted this bounty."
        else:
            return "Invalid bounty ID. Check the notice board for available bounties."
    
    def show_inventory(self):
        inv_text = "Your inventory:\\n"
        inv_text += f"Gold: {self.gold}\\n"
        for item, count in self.inventory.items():
            inv_text += f"{item.title()}: {count}\\n"
        return inv_text
    
    def show_status(self):
        return f"""Character Status:
Gold: {self.gold}
Tiredness: {int(self.tiredness * 100)}%
Location: The Rusted Tankard
Time: {self.get_time_string()} (Hour {int(self.time_hours % 24)})
Room: {'Rented' if self.has_room else 'None'}
Active Bounties: {len(self.active_bounties)}"""
    
    def wait(self, cmd):
        try:
            hours = float(cmd.split()[1]) if len(cmd.split()) > 1 else 1
        except:
            hours = 1
            
        self.advance_time(hours)
        return f"You wait for {hours} hour(s). Time passes...\\n\\nIt is now {self.get_time_string()}."
    
    def show_help(self):
        return """Available Commands:

BASIC ACTIONS:
  look / l          - Look around the current location
  talk              - Talk to someone in the tavern  
  inventory / i     - Check your inventory
  status            - View your character status
  wait [hours]      - Wait for time to pass
  help              - Show this help

TAVERN ACTIVITIES:
  drink             - Order an ale (2 gold)
  gamble [amount]   - Play dice (default: 10 gold)
  rest              - Rest to reduce tiredness

WORK & BOUNTIES:
  bounties          - Check the notice board
  accept bounty [id]- Accept a specific bounty
  jobs              - See available work
  work [job]        - Do a specific job

EXPLORATION:
  go to [place]     - Move to a location (bar, fireplace, etc.)
  examine [object]  - Look at something specific

The game understands many variations of these commands. Try natural phrases!"""
    
    def show_jobs(self):
        return """Available Jobs at the Tavern:

1. WASH DISHES (easy)
   Pay: 5 gold
   Time: 1 hour
   "Help out in the kitchen"

2. SERVE TABLES (medium)  
   Pay: 8 gold
   Time: 2 hours
   "Serve drinks to patrons"

3. CLEAN ROOMS (medium)
   Pay: 10 gold
   Time: 2 hours
   "Clean the guest rooms upstairs"

4. NIGHT WATCH (hard)
   Pay: 15 gold
   Time: 4 hours
   "Keep watch through the night"

Type 'work [job name]' to start working."""
    
    def do_job(self, cmd):
        job = cmd.replace('work', '').strip().lower()
        
        jobs = {
            'dishes': (5, 1, 0.2),
            'wash dishes': (5, 1, 0.2),
            'tables': (8, 2, 0.3),
            'serve tables': (8, 2, 0.3),
            'rooms': (10, 2, 0.3),
            'clean rooms': (10, 2, 0.3),
            'watch': (15, 4, 0.5),
            'night watch': (15, 4, 0.5)
        }
        
        if job in jobs:
            pay, hours, fatigue = jobs[job]
            self.gold += pay
            self.advance_time(hours)
            self.tiredness += fatigue
            
            return f"You work hard for {hours} hours and earn {pay} gold.\\nYou now have {self.gold} gold.\\nYou're feeling {'very ' if self.tiredness > 0.7 else ''}tired."
        else:
            return "That's not a valid job. Type 'jobs' to see available work."
    
    def rest(self):
        if self.has_room:
            self.tiredness = 0
            self.advance_time(8)
            return "You head to your room and sleep soundly for 8 hours. You feel completely refreshed!"
        else:
            self.tiredness *= 0.5
            self.advance_time(2)
            return "You find a quiet corner and rest for a couple hours. You feel somewhat better, but a proper bed would be nice."

# HTML Interface
HTML_GAME = """<!DOCTYPE html>
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
            line-height: 1.6;
        }
        
        #container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h1 {
            color: #d4af37;
            text-align: center;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
            margin-bottom: 20px;
        }
        
        #output {
            background-color: #1a1a1a;
            border: 3px solid #d4af37;
            border-radius: 5px;
            padding: 20px;
            min-height: 500px;
            max-height: 600px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 16px;
            margin-bottom: 15px;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
        }
        
        #input-container {
            display: flex;
            gap: 10px;
        }
        
        #command {
            flex: 1;
            padding: 15px;
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
            padding: 15px 30px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            border-radius: 5px;
            transition: all 0.3s;
            font-family: 'Georgia', serif;
        }
        
        button:hover {
            background-color: #f0d060;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.5);
        }
        
        #quick-actions {
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
        }
        
        .quick-btn:hover {
            background-color: #3a3a3a;
            border-color: #d4af37;
            transform: none;
        }
        
        #footer {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 14px;
        }
        
        .highlight {
            color: #d4af37;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div id="container">
        <h1>🍺 The Living Rusted Tankard</h1>
        
        <div id="output">Loading...</div>
        
        <div id="input-container">
            <input type="text" id="command" placeholder="What would you like to do?" autofocus>
            <button onclick="sendCommand()">Send</button>
        </div>
        
        <div id="quick-actions">
            <button class="quick-btn" onclick="quickCmd('look')">Look Around</button>
            <button class="quick-btn" onclick="quickCmd('talk')">Talk</button>
            <button class="quick-btn" onclick="quickCmd('inventory')">Inventory</button>
            <button class="quick-btn" onclick="quickCmd('bounties')">Bounties</button>
            <button class="quick-btn" onclick="quickCmd('gamble 10')">Gamble 10g</button>
            <button class="quick-btn" onclick="quickCmd('drink')">Order Drink</button>
            <button class="quick-btn" onclick="quickCmd('help')">Help</button>
        </div>
        
        <div id="footer">
            A text-based RPG where time moves forward and choices matter
        </div>
    </div>
    
    <script>
        let sessionId = Math.random().toString(36).substr(2, 9);
        const output = document.getElementById('output');
        const input = document.getElementById('command');
        
        // Initialize game
        window.onload = function() {
            sendCommand('look');
        };
        
        async function sendCommand(cmd) {
            const command = cmd || input.value.trim();
            if (!command && !cmd) return;
            
            if (!cmd) {
                output.textContent += '\\n> ' + command + '\\n\\n';
                input.value = '';
            }
            
            try {
                const response = await fetch('/game?session=' + sessionId + '&cmd=' + encodeURIComponent(command));
                const data = await response.json();
                
                output.textContent += data.response + '\\n\\n';
                output.scrollTop = output.scrollHeight;
                
                // Focus back on input
                input.focus();
                
            } catch (error) {
                output.textContent += 'Error: Connection lost. Please refresh the page.\\n\\n';
            }
        }
        
        function quickCmd(cmd) {
            input.value = cmd;
            sendCommand();
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
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_GAME.encode())
            
        elif parsed.path == '/game':
            params = parse_qs(parsed.query)
            session_id = params.get('session', [''])[0]
            command = params.get('cmd', [''])[0]
            
            # Get or create session
            if session_id not in game_sessions:
                game_sessions[session_id] = GameSession()
            
            session = game_sessions[session_id]
            response = session.process_command(command)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'response': response}).encode())
            
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def main():
    print(f"🍺 The Living Rusted Tankard - Standalone Server")
    print(f"📍 Starting on http://localhost:{PORT}")
    print(f"🌐 Open this URL in your browser")
    print(f"Press Ctrl+C to stop\\n")
    
    with socketserver.TCPServer(("", PORT), GameHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\n🛑 Server stopped")

if __name__ == "__main__":
    main()