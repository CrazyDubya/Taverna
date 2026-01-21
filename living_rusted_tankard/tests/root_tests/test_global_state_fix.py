#!/usr/bin/env python3
"""
Simple test to verify the global state issue is fixed.
"""

import sys
import os

# Add the project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'living_rusted_tankard'))

def test_no_global_state():
    """Test that AI players don't use global state."""
    print("Testing AI Player global state removal...")
    
    from core.ai_player import AIPlayerPersonality
    from core.ai_player_manager import AIPlayerManager
    
    # Create manager
    manager = AIPlayerManager()
    
    # Create two AI player sessions
    session1 = manager.create_session(
        personality=AIPlayerPersonality.CURIOUS_EXPLORER,
        name="Explorer"
    )
    session2 = manager.create_session(
        personality=AIPlayerPersonality.CAUTIOUS_MERCHANT,
        name="Merchant"
    )
    
    # Test 1: Different instances
    assert session1.ai_player is not session2.ai_player, "AI players should be different instances"
    print("✅ Test 1 passed: AI players are separate instances")
    
    # Test 2: Different session IDs
    assert session1.session_id != session2.session_id, "Session IDs should be different"
    print("✅ Test 2 passed: Session IDs are unique")
    
    # Test 3: Different personalities
    assert session1.ai_player.personality != session2.ai_player.personality, "Personalities should be different"
    print("✅ Test 3 passed: Personalities are separate")
    
    # Test 4: Game state isolation
    test_state1 = {"gold": 100, "player": "Explorer"}
    test_state2 = {"gold": 50, "player": "Merchant"}
    
    session1.ai_player.update_game_state(test_state1)
    session2.ai_player.update_game_state(test_state2)
    
    assert session1.ai_player.game_state["gold"] == 100, "Explorer should have 100 gold"
    assert session2.ai_player.game_state["gold"] == 50, "Merchant should have 50 gold"
    assert session1.ai_player.game_state["player"] == "Explorer", "Explorer should have correct name"
    assert session2.ai_player.game_state["player"] == "Merchant", "Merchant should have correct name"
    print("✅ Test 4 passed: Game state is isolated between sessions")
    
    # Test 5: Action history isolation
    session1.ai_player.record_action("look around", "exploring")
    session2.ai_player.record_action("check inventory", "assessing")
    
    player1_commands = [a.command for a in session1.ai_player.action_history]
    player2_commands = [a.command for a in session2.ai_player.action_history]
    
    assert "look around" in player1_commands, "Explorer should have 'look around' action"
    assert "check inventory" in player2_commands, "Merchant should have 'check inventory' action"
    assert "check inventory" not in player1_commands, "Explorer should not have Merchant's actions"
    assert "look around" not in player2_commands, "Merchant should not have Explorer's actions"
    print("✅ Test 5 passed: Action history is isolated")
    
    # Test 6: Session cleanup
    session_id = session1.session_id
    result = manager.deactivate_session(session_id)
    assert result is True, "Session deactivation should succeed"
    
    retrieved = manager.get_session(session_id)
    assert retrieved is None, "Deactivated session should not be retrievable"
    print("✅ Test 6 passed: Session cleanup works")
    
    print("\n🎉 All tests passed! Global state issue is fixed.")
    print("AI Players now use proper session isolation.")

def test_import_structure():
    """Test that imports work correctly."""
    print("\nTesting import structure...")
    
    try:
        from core.ai_player import AIPlayer, AIPlayerPersonality
        print("✅ Can import AIPlayer and AIPlayerPersonality")
        
        from core.ai_player_manager import AIPlayerManager, get_ai_player_manager
        print("✅ Can import AIPlayerManager")
        
        # Test that no global functions exist in ai_player module
        import core.ai_player as ai_module
        
        # These should NOT exist anymore
        assert not hasattr(ai_module, 'get_ai_player'), "get_ai_player should be removed"
        assert not hasattr(ai_module, 'set_ai_player_personality'), "set_ai_player_personality should be removed"
        assert not hasattr(ai_module, '_ai_player'), "_ai_player global should be removed"
        print("✅ Global state functions/variables removed")
        
        print("✅ Import structure is clean")
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        raise

if __name__ == "__main__":
    try:
        test_import_structure()
        test_no_global_state()
        print("\n🟢 SUCCESS: All tests passed! Global state issue is resolved.")
    except Exception as e:
        print(f"\n🔴 FAILURE: {e}")
        sys.exit(1)