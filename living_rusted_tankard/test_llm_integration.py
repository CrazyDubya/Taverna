#!/usr/bin/env python3
"""Test the LLM natural language integration."""

from core.game_state import GameState
import logging

# Enable debug logging to see LLM parsing
logging.basicConfig(level=logging.INFO)

def test_natural_language():
    """Test natural language understanding."""
    print("🧙 TESTING LLM NATURAL LANGUAGE UNDERSTANDING")
    print("============================================\n")
    
    game = GameState()
    
    # Natural language test cases
    test_commands = [
        # Conversation
        "talk to the bartender",
        "ask bartender about rumors",
        "hey barkeep, what's new?",
        
        # Movement  
        "go to the cellar",
        "head upstairs",
        "walk to the bar",
        
        # Actions
        "look around",
        "check my inventory", 
        "examine the room",
        
        # Shopping
        "I want to buy a drink",
        "order some ale",
        "get me some food",
        
        # Questions
        "where am I?",
        "what time is it?",
        "who's here?",
        
        # Complex
        "I'm looking for work",
        "where's the bathroom?",
        "tell me about this place"
    ]
    
    success_count = 0
    
    for cmd in test_commands:
        print(f"\n📝 Input: '{cmd}'")
        
        try:
            result = game.process_command(cmd)
            
            if result['success']:
                print(f"✅ Success: {result['message'][:100]}...")
                success_count += 1
            else:
                print(f"❌ Failed: {result['message']}")
                
        except Exception as e:
            print(f"🔥 Error: {e}")
    
    print(f"\n📊 RESULTS:")
    print(f"Success rate: {success_count}/{len(test_commands)} ({success_count/len(test_commands)*100:.1f}%)")
    
    # Test specific functionality
    print("\n🎯 TESTING SPECIFIC SCENARIOS:")
    
    # Test 1: Natural conversation
    print("\n1. Natural conversation:")
    result = game.process_command("hey bartender, how's business?")
    print(f"   Response: {result.get('message', 'No response')[:150]}...")
    
    # Test 2: Complex request
    print("\n2. Complex request:")
    result = game.process_command("I'm tired and looking for a place to rest")
    print(f"   Response: {result.get('message', 'No response')[:150]}...")
    
    # Test 3: Ambiguous input
    print("\n3. Ambiguous input:")
    result = game.process_command("what's that smell?")
    print(f"   Response: {result.get('message', 'No response')[:150]}...")

def check_llm_status():
    """Check if LLM is actually running."""
    print("\n🔍 CHECKING LLM STATUS:")
    
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✅ Ollama is running")
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            if models:
                print(f"   Available models: {', '.join(models)}")
            else:
                print("   ⚠️  No models installed. Run: ollama pull gemma2:2b")
        else:
            print("❌ Ollama responded but with error")
    except:
        print("❌ Ollama is not running. Start it with: ollama serve")
        print("   The game will fall back to regex parsing")

if __name__ == "__main__":
    check_llm_status()
    print("\n" + "="*50 + "\n")
    test_natural_language()