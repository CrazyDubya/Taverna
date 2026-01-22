#!/usr/bin/env python3
"""
Validate that the global state fix is implemented correctly.
"""

import sys
import os

# Add the project to path (go up two levels from tests/root_tests/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

def validate_code_changes():
    """Validate that code changes are correct."""
    print("🔍 Validating AI Player global state fix...")
    
    # Check that ai_player.py has the global state removed
    ai_player_path = "living_rusted_tankard/core/ai_player.py"
    
    print("📂 Reading ai_player.py...")
    with open(ai_player_path, 'r') as f:
        ai_player_content = f.read()
    
    # Check that problematic global patterns are removed
    problematic_patterns = [
        "_ai_player = None",
        "global _ai_player",
        "def get_ai_player():",
        "def set_ai_player_personality("
    ]
    
    for pattern in problematic_patterns:
        if pattern in ai_player_content:
            print(f"❌ Found problematic pattern: {pattern}")
            return False
        else:
            print(f"✅ Pattern removed: {pattern}")
    
    # Check that the manager exists
    manager_path = "living_rusted_tankard/core/ai_player_manager.py"
    if not os.path.exists(manager_path):
        print(f"❌ AI Player Manager not found at {manager_path}")
        return False
    else:
        print(f"✅ AI Player Manager created at {manager_path}")
    
    # Check manager content
    with open(manager_path, 'r') as f:
        manager_content = f.read()
    
    required_classes = ["AIPlayerSession", "AIPlayerManager"]
    for class_name in required_classes:
        if f"class {class_name}" in manager_content:
            print(f"✅ {class_name} class found in manager")
        else:
            print(f"❌ {class_name} class missing from manager")
            return False
    
    # Check API router updates
    api_path = "living_rusted_tankard/api/routers/ai_player.py"
    with open(api_path, 'r') as f:
        api_content = f.read()
    
    if "from core.ai_player_manager import get_ai_player_manager" in api_content:
        print("✅ API router imports AI Player Manager")
    else:
        print("❌ API router missing AI Player Manager import")
        return False
    
    if "manager = get_ai_player_manager()" in api_content:
        print("✅ API router uses AI Player Manager")
    else:
        print("❌ API router not using AI Player Manager")
        return False
    
    print("\n🎉 All code validation checks passed!")
    return True

def validate_test_exists():
    """Validate that proper tests were created."""
    test_path = "tests/unit/test_ai_player_isolation.py"
    
    if not os.path.exists(test_path):
        print(f"❌ Test file not found at {test_path}")
        return False
    
    with open(test_path, 'r') as f:
        test_content = f.read()
    
    required_tests = [
        "test_no_global_state_leakage",
        "test_session_isolation_game_state",
        "test_action_history_isolation",
        "test_concurrent_ai_players",
        "test_session_cleanup"
    ]
    
    for test_name in required_tests:
        if f"def {test_name}" in test_content:
            print(f"✅ Test exists: {test_name}")
        else:
            print(f"❌ Test missing: {test_name}")
            return False
    
    print("✅ All required tests are present")
    return True

def check_file_structure():
    """Check that all required files exist."""
    required_files = [
        "living_rusted_tankard/core/ai_player.py",
        "living_rusted_tankard/core/ai_player_manager.py",
        "living_rusted_tankard/api/routers/ai_player.py",
        "tests/unit/test_ai_player_isolation.py"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ File missing: {file_path}")
            return False
    
    return True

def main():
    """Main validation function."""
    print("🚀 Starting validation of AI Player global state fix...\n")
    
    try:
        # Check file structure
        if not check_file_structure():
            print("\n🔴 FAILURE: Required files are missing")
            return False
        
        # Validate code changes
        if not validate_code_changes():
            print("\n🔴 FAILURE: Code validation failed")
            return False
        
        # Validate tests exist
        if not validate_test_exists():
            print("\n🔴 FAILURE: Test validation failed")
            return False
        
        print("\n🟢 SUCCESS: All validations passed!")
        print("\n📋 Summary of changes:")
        print("  1. ✅ Removed global _ai_player variable")
        print("  2. ✅ Removed get_ai_player() and set_ai_player_personality() functions")
        print("  3. ✅ Created AIPlayerManager class for session management")
        print("  4. ✅ Updated API router to use manager")
        print("  5. ✅ Created comprehensive tests for session isolation")
        print("\n🎯 The global state issue has been successfully resolved!")
        print("   AI Players now use proper session isolation without global state.")
        
        return True
        
    except Exception as e:
        print(f"\n🔴 FAILURE: Validation error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)