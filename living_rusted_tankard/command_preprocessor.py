#!/usr/bin/env python3
"""Command preprocessor to fix common issues before processing."""

import re
from typing import Tuple, Dict, List

class CommandPreprocessor:
    """Preprocess commands to fix common issues and improve success rate."""
    
    def __init__(self):
        # Common misspellings and corrections
        self.corrections = {
            'gambl': 'gamble',
            'gmable': 'gamble',
            'gmabl': 'gamble',
            'inv': 'inventory',
            'inven': 'inventory',
            'stat': 'status',
            'stats': 'status',
            'hlep': 'help',
            'halp': 'help',
            'mve': 'move',
            'mvoe': 'move',
            'wiat': 'wait',
            'waitt': 'wait',
            'bounty': 'bounties',  # Common singular/plural confusion
            'job': 'jobs',
            'game': 'games',
            'npc': 'npcs',
            'cmd': 'commands',
            'cmds': 'commands',
            'quit': 'quit',
            'exit': 'quit',
            'leave': 'quit'
        }
        
        # Room name mappings (common mistakes)
        self.room_corrections = {
            'upstair': 'upstairs',
            'downstair': 'downstairs',
            'celler': 'cellar',
            'seller': 'cellar',
            'main': 'tavern_main',
            'bar': 'tavern_main',
            'hall': 'tavern_main',
            'room': 'room_1A',  # Default to first room
            'kitchen': 'tavern_main',  # Redirect to main area
            'outside': 'tavern_main'   # Can't go outside
        }
        
        # Item name corrections
        self.item_corrections = {
            'beer': 'ale',
            'drink': 'ale',
            'food': 'bread',
            'weapon': 'dagger',  # If we add weapons later
            'potion': 'ale',     # Closest thing we have
            'sword': 'dagger'    # If we add weapons
        }
        
        # Amount adjustments
        self.safe_amounts = {
            'gamble': (1, 20),    # Min and max safe gambling
            'wait': (0.5, 12),    # Reasonable wait times
            'sleep': (1, 8)       # Reasonable sleep times
        }
    
    def preprocess(self, command: str) -> str:
        """Preprocess command to fix common issues."""
        
        command = command.lower().strip()
        
        # Step 1: Fix common misspellings
        parts = command.split()
        if parts:
            # Check main command
            main_cmd = parts[0]
            if main_cmd in self.corrections:
                parts[0] = self.corrections[main_cmd]
            
            # Rejoin
            command = ' '.join(parts)
        
        # Step 2: Fix specific command types
        if command.startswith('move '):
            command = self._fix_move_command(command)
        elif command.startswith('buy ') or command.startswith('use '):
            command = self._fix_item_command(command)
        elif command.startswith('gamble ') or command.startswith('wait ') or command.startswith('sleep '):
            command = self._fix_amount_command(command)
        elif command.startswith('interact '):
            command = self._fix_interact_command(command)
        
        # Step 3: Handle common patterns
        command = self._fix_common_patterns(command)
        
        return command
    
    def _fix_move_command(self, command: str) -> str:
        """Fix move commands with room name corrections."""
        parts = command.split()
        if len(parts) >= 2:
            room = parts[1]
            if room in self.room_corrections:
                parts[1] = self.room_corrections[room]
                return ' '.join(parts)
        return command
    
    def _fix_item_command(self, command: str) -> str:
        """Fix buy/use commands with item corrections."""
        parts = command.split()
        if len(parts) >= 2:
            item = parts[1]
            if item in self.item_corrections:
                parts[1] = self.item_corrections[item]
                return ' '.join(parts)
        return command
    
    def _fix_amount_command(self, command: str) -> str:
        """Fix commands with amounts to ensure safe values."""
        parts = command.split()
        if len(parts) >= 2:
            cmd = parts[0]
            try:
                amount = float(parts[1])
                if cmd in self.safe_amounts:
                    min_amt, max_amt = self.safe_amounts[cmd]
                    if amount < min_amt:
                        parts[1] = str(min_amt)
                    elif amount > max_amt:
                        parts[1] = str(max_amt)
                    return ' '.join(parts)
            except ValueError:
                # Not a valid number, leave it alone
                pass
        return command
    
    def _fix_interact_command(self, command: str) -> str:
        """Fix interact commands."""
        # Common pattern: "interact with X" -> "interact X talk"
        command = command.replace('interact with ', 'interact ')
        
        # Add default action if missing
        parts = command.split()
        if len(parts) == 2:  # Just "interact npc"
            return f"{command} talk"
        
        return command
    
    def _fix_common_patterns(self, command: str) -> str:
        """Fix other common patterns."""
        
        # "go to X" -> "move X"
        command = re.sub(r'^go to (\w+)', r'move \1', command)
        command = re.sub(r'^go (\w+)', r'move \1', command)
        
        # "look at X" -> "look"
        command = re.sub(r'^look at.*', 'look', command)
        
        # "talk to X" -> "interact X talk"
        command = re.sub(r'^talk to (\w+)', r'interact \1 talk', command)
        
        # "check X" patterns
        if command.startswith('check '):
            if 'invent' in command:
                return 'inventory'
            elif 'stat' in command:
                return 'status'
            elif 'time' in command:
                return 'look'  # Time is shown in look
        
        return command

def test_preprocessor():
    """Test the preprocessor with common mistakes."""
    
    pp = CommandPreprocessor()
    
    test_cases = [
        # Misspellings
        ("gambl 10", "gamble 10"),
        ("hlep", "help"),
        ("mve upstair", "move upstairs"),
        
        # Room corrections
        ("move kitchen", "move tavern_main"),
        ("move celler", "move cellar"),
        
        # Item corrections
        ("buy beer", "buy ale"),
        ("use potion", "use ale"),
        
        # Amount safety
        ("gamble 1000", "gamble 20"),
        ("wait 100", "wait 12"),
        
        # Pattern fixes
        ("go to cellar", "move cellar"),
        ("talk to bartender", "interact bartender talk"),
        ("check inventory", "inventory"),
        
        # Interact fixes
        ("interact with npc", "interact npc talk"),
        ("interact bartender", "interact bartender talk")
    ]
    
    print("🔧 COMMAND PREPROCESSOR TEST")
    print("============================\n")
    
    all_passed = True
    for input_cmd, expected in test_cases:
        result = pp.preprocess(input_cmd)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_cmd}' -> '{result}' (expected: '{expected}')")
        if result != expected:
            all_passed = False
    
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")
    
    return all_passed

if __name__ == "__main__":
    test_preprocessor()