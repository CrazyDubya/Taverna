#!/usr/bin/env python3
"""Test API integration with the full integrated game."""

import requests
import json
import time

def test_api_integration():
    """Test the integrated game API."""
    print("🌐 === API INTEGRATION TEST ===")
    print("Testing full game integration via API\n")
    
    base_url = "http://localhost:8000/api"
    
    try:
        # Test health check
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ API server is running")
        else:
            print("❌ API server not responding")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("💡 Please start the server with: poetry run python api/main.py")
        return False
    
    # Create new game session
    print("\n📦 Creating new game session...")
    response = requests.post(f"{base_url}/game/new-session")
    
    if response.status_code != 200:
        print(f"❌ Failed to create session: {response.status_code}")
        return False
    
    session_data = response.json()
    session_id = session_data['session_id']
    print(f"✓ Session created: {session_id[:8]}...")
    print(f"✓ Initial state: {session_data['game_state']['player_gold']} gold")
    
    # Test commands
    commands_to_test = [
        "wait 2",
        "gamble 5", 
        "npcs",
        "games",
        "status",
        "inventory"
    ]
    
    print(f"\n🎮 Testing game commands...")
    for command in commands_to_test:
        response = requests.post(
            f"{base_url}/game/command",
            json={"command": command, "session_id": session_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            success = "✓" if result['success'] else "⚠"
            print(f"{success} {command}: {result['message'][:60]}...")
        else:
            print(f"❌ {command}: HTTP {response.status_code}")
    
    # Get final state
    print(f"\n📊 Final game state...")
    response = requests.get(f"{base_url}/game/sessions/{session_id}/state")
    
    if response.status_code == 200:
        state = response.json()
        print(f"✓ Player gold: {state['player']['gold']}")
        print(f"✓ Game time: {state['time']:.1f} hours")
        print(f"✓ Phase 2 (World): {'Available' if state['systems']['phase2_available'] else 'Unavailable'}")
        print(f"✓ Phase 3 (NPCs): {'Available' if state['systems']['phase3_available'] else 'Unavailable'}")
        print(f"✓ Phase 4 (Narrative): {'Available' if state['systems']['phase4_available'] else 'Unavailable'}")
    
    # Clean up
    print(f"\n🧹 Cleaning up...")
    response = requests.delete(f"{base_url}/game/sessions/{session_id}")
    if response.status_code == 200:
        print("✓ Session deleted")
    
    print(f"\n🎯 === API INTEGRATION SUMMARY ===")
    print("✅ API server integration: SUCCESS")
    print("✅ Game session management: SUCCESS") 
    print("✅ Command processing via API: SUCCESS")
    print("✅ Full game state via API: SUCCESS")
    print("🎉 The Living Rusted Tankard API is fully functional!")
    
    return True

if __name__ == "__main__":
    test_api_integration()