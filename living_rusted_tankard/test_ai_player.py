#!/usr/bin/env python3
"""
Test script for AI Player functionality.
"""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000"

def test_ai_player():
    print("🤖 Testing AI Player System")
    print("="*50)
    
    # Test 1: List personalities
    print("\n1. Testing personalities endpoint...")
    response = requests.get(f"{BASE_URL}/ai-player/personalities")
    if response.status_code == 200:
        personalities = response.json()["personalities"]
        print(f"✅ Found {len(personalities)} personalities:")
        for p in personalities:
            print(f"   - {p['name']}: {p['style']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        return
    
    # Test 2: Start AI player
    print("\n2. Starting AI player...")
    config = {
        "personality": "curious_explorer",
        "name": "Gemma",
        "thinking_speed": 1.0
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/ai-player/start",
            json=config,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result["session_id"]
            print(f"✅ AI player started: {session_id[:8]}...")
            print(f"   Name: {result['ai_player']['name']}")
            print(f"   Personality: {result['ai_player']['personality']}")
        else:
            print(f"❌ Failed to start: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Exception: {e}")
        return
    
    # Test 3: Generate an action
    print("\n3. Generating AI action...")
    try:
        response = requests.post(
            f"{BASE_URL}/ai-player/action/{session_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Action generated: '{result['action']}'")
            print(f"   Result: {result['result'][:100]}...")
        else:
            print(f"❌ Failed to generate action: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Check status
    print("\n4. Checking AI player status...")
    try:
        response = requests.get(f"{BASE_URL}/ai-player/status/{session_id}")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ AI player status:")
            print(f"   Actions taken: {status['ai_player']['action_count']}")
            print(f"   Is active: {status['ai_player']['is_active']}")
        else:
            print(f"❌ Failed to get status: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print(f"\n🎉 AI Player test completed!")
    print(f"🌐 Visit http://127.0.0.1:8000/ai-demo to see the interactive demo!")

if __name__ == "__main__":
    test_ai_player()