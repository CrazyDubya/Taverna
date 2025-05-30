#!/usr/bin/env python3
"""
AI Observer that connects to the web game with full LLM integration
"""
import asyncio
import json
import requests
import time
import random

class AIWebPlayer:
    def __init__(self, name="Gemma", personality="curious_explorer"):
        self.name = name
        self.personality = personality
        self.session_id = None
        self.action_count = 0
        
    async def play_game(self, max_actions=20):
        """Watch AI play the web game"""
        print(f"🤖 {self.name} starts playing The Living Rusted Tankard")
        print("=" * 50)
        
        # Start with looking around
        await self.send_command("look around")
        
        # AI decision patterns based on personality
        actions = [
            "approach the notice board",
            "read notice board", 
            "talk to barkeeper",
            "order a drink",
            "gamble 5",
            "check inventory",
            "talk to someone",
            "examine the fireplace",
            "look for rumors",
            "ask about bounties",
            "gamble 10",
            "wait 1",
            "rest",
            "look around again"
        ]
        
        for i in range(max_actions):
            self.action_count += 1
            
            # Wait between actions (like a real player)
            await asyncio.sleep(random.uniform(2, 5))
            
            # Pick an action
            if i < len(actions):
                action = actions[i]
            else:
                action = random.choice([
                    "gamble 10", "talk", "drink", "look", "wait 1",
                    "check bounties", "inventory"
                ])
            
            print(f"\n🎬 Action #{self.action_count}: {action}")
            print("-" * 30)
            
            await self.send_command(action)
            
        print(f"\n✅ {self.name} finished playing after {max_actions} actions!")
    
    async def send_command(self, command):
        """Send command to web game"""
        try:
            url = f"http://localhost:8888/game"
            params = {
                'session': self.session_id or 'ai_player',
                'cmd': command
            }
            
            print(f"💭 {self.name} thinks: '{command}'")
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # Store session ID
            if not self.session_id:
                self.session_id = data.get('session_id', 'ai_player')
            
            # Display response
            game_response = data.get('response', 'No response')
            ai_used = data.get('ai_used', 'unknown')
            
            print(f"🎮 Game responds ({ai_used}):")
            print(f"   {game_response[:200]}{'...' if len(game_response) > 200 else ''}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            return None

async def main():
    print("🍺 AI Web Observer for The Living Rusted Tankard")
    print("🤖 Watching AI play the web version with full LLM integration")
    print("📍 Game should be running at http://localhost:8888")
    print()
    
    # Check if game is running
    try:
        response = requests.get("http://localhost:8888/", timeout=5)
        if response.status_code == 200:
            print("✅ Game server is running!")
        else:
            print("❌ Game server not responding")
            return
    except:
        print("❌ Cannot connect to game server at localhost:8888")
        print("   Make sure the game server is running first")
        return
    
    # Create AI player
    ai = AIWebPlayer("Gemma the Explorer", "curious_explorer")
    
    print(f"\n👁️  Watching {ai.name} play...")
    print("Press Ctrl+C to stop\n")
    
    try:
        await ai.play_game(max_actions=15)
    except KeyboardInterrupt:
        print(f"\n👋 Stopped watching {ai.name}")

if __name__ == "__main__":
    asyncio.run(main())