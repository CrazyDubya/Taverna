#!/usr/bin/env python3
"""
Simple AI Player Demo - Watch an AI character play the game.
"""

import asyncio
import time
from core.ai_player import AIPlayer, AIPlayerPersonality
from core.game_state import GameState

async def run_ai_demo():
    print("🤖 Simple AI Player Demo - The Living Rusted Tankard")
    print("="*60)
    
    # Create AI player with curious explorer personality
    ai_player = AIPlayer(
        name="Gemma", 
        personality=AIPlayerPersonality.CURIOUS_EXPLORER,
        model="gemma2:2b"
    )
    
    # Create game state
    game_state = GameState()
    
    print(f"\n🎭 AI Character: {ai_player.name}")
    print(f"📋 Personality: {ai_player.personality.value}")
    print(f"🎯 Style: {ai_player.personality_traits[ai_player.personality]['interaction_style']}")
    
    # Show initial game state
    print(f"\n🏰 Initial Game State:")
    snapshot = game_state.get_snapshot()
    ai_player.update_game_state(snapshot)
    print(f"   Time: {snapshot.get('formatted_time', 'Morning')}")
    print(f"   Location: {snapshot.get('location', 'tavern')}")
    print(f"   Gold: {snapshot.get('player', {}).get('gold', 0)} gp")
    
    # Show welcome message if available
    if hasattr(game_state, 'events') and game_state.events:
        welcome_msg = game_state.events[0].message
        print(f"\n📜 Welcome Message:")
        print(f"   {welcome_msg[:100]}...")
    
    print(f"\n🎮 Starting AI interaction...\n")
    
    # Run several AI actions
    for i in range(5):
        print(f"{'='*40}")
        print(f"🤖 AI Turn {i+1}")
        print(f"{'='*40}")
        
        # AI thinks about what to do
        print(f"💭 {ai_player.name} is thinking...")
        await asyncio.sleep(1)  # Thinking delay
        
        # Generate action
        game_context = ai_player.get_game_context()
        print(f"📊 Game Context: {game_context}")
        
        print(f"🎯 Generating action...")
        action = await ai_player.generate_action(game_context)
        print(f"✨ AI Decision: '{action}'")
        
        # Show streaming effect
        print(f"⌨️  {ai_player.name} types: ", end="", flush=True)
        for char in action:
            print(char, end="", flush=True)
            await asyncio.sleep(0.05)  # Typing effect
        print()  # New line
        
        # Execute the action
        print(f"⚡ Executing command...")
        result = game_state.process_command(action)
        
        # Show result
        print(f"📝 Game Response:")
        print(f"   {result.get('message', 'No response')}")
        
        # Update AI player's understanding
        new_snapshot = game_state.get_snapshot()
        ai_player.update_game_state(new_snapshot)
        ai_player.record_action(action, f"Turn {i+1} action")
        
        # Show updated game state
        if 'player' in new_snapshot:
            player = new_snapshot['player']
            print(f"💰 Updated Status:")
            print(f"   Gold: {player.get('gold', 0)} gp")
            if 'inventory' in player and player['inventory']:
                items = [item['name'] for item in player['inventory']]
                print(f"   Items: {', '.join(items)}")
        
        print(f"\n⏱️  Waiting before next action...\n")
        await asyncio.sleep(2)  # Wait between actions
    
    print(f"🎉 AI Demo completed!")
    print(f"\n📈 AI Statistics:")
    print(f"   Total actions: {len(ai_player.action_history)}")
    print(f"   Personality: {ai_player.personality.value}")
    print(f"   Final game time: {ai_player.game_state.get('formatted_time', 'Unknown')}")
    
    print(f"\n🌐 For the full interactive demo, visit: http://127.0.0.1:8000/ai-demo")

if __name__ == "__main__":
    asyncio.run(run_ai_demo())