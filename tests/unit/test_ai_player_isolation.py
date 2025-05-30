"""
Tests for AI Player session isolation and global state removal.

This test suite verifies that the AI Player system properly isolates
sessions and doesn't rely on global state.
"""

import pytest
from unittest.mock import Mock, patch
from core.ai_player import AIPlayer, AIPlayerPersonality
from core.ai_player_manager import AIPlayerManager, get_ai_player_manager


class TestAIPlayerIsolation:
    """Test AI Player session isolation."""
    
    def setup_method(self):
        """Set up fresh manager for each test."""
        self.manager = AIPlayerManager()
    
    def test_no_global_state_leakage(self):
        """Verify AI players don't share global state."""
        # Create two AI players with different personalities
        session1 = self.manager.create_session(
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            name="Explorer"
        )
        session2 = self.manager.create_session(
            personality=AIPlayerPersonality.CAUTIOUS_MERCHANT,
            name="Merchant"
        )
        
        # Verify they are completely separate instances
        assert session1.ai_player is not session2.ai_player
        assert session1.session_id != session2.session_id
        assert session1.ai_player.name != session2.ai_player.name
        assert session1.ai_player.personality != session2.ai_player.personality
    
    def test_session_isolation_game_state(self):
        """Verify game state updates don't affect other sessions."""
        session1 = self.manager.create_session(
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            name="Player1"
        )
        session2 = self.manager.create_session(
            personality=AIPlayerPersonality.CAUTIOUS_MERCHANT,
            name="Player2"
        )
        
        # Update game state for one player
        test_state1 = {"gold": 100, "location": "tavern", "player": "Player1"}
        test_state2 = {"gold": 50, "location": "inn", "player": "Player2"}
        
        session1.ai_player.update_game_state(test_state1)
        session2.ai_player.update_game_state(test_state2)
        
        # Verify states remain separate
        assert session1.ai_player.game_state["gold"] == 100
        assert session2.ai_player.game_state["gold"] == 50
        assert session1.ai_player.game_state["player"] == "Player1"
        assert session2.ai_player.game_state["player"] == "Player2"
    
    def test_action_history_isolation(self):
        """Verify action histories don't cross-contaminate."""
        session1 = self.manager.create_session(
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            name="Player1"
        )
        session2 = self.manager.create_session(
            personality=AIPlayerPersonality.CAUTIOUS_MERCHANT,
            name="Player2"
        )
        
        # Record different actions for each player
        session1.ai_player.record_action("look around", "exploring")
        session1.ai_player.record_action("talk to bartender", "gathering info")
        
        session2.ai_player.record_action("check inventory", "assessing resources")
        session2.ai_player.record_action("count gold", "financial planning")
        
        # Verify histories are separate
        assert len(session1.ai_player.action_history) == 2
        assert len(session2.ai_player.action_history) == 2
        
        assert session1.ai_player.action_history[0].command == "look around"
        assert session2.ai_player.action_history[0].command == "check inventory"
        
        # Verify no cross-contamination
        player1_commands = [a.command for a in session1.ai_player.action_history]
        player2_commands = [a.command for a in session2.ai_player.action_history]
        
        assert "check inventory" not in player1_commands
        assert "look around" not in player2_commands
    
    def test_concurrent_ai_players(self):
        """Test multiple AI players can exist concurrently."""
        sessions = []
        
        # Create 5 different AI players
        personalities = list(AIPlayerPersonality)
        for i, personality in enumerate(personalities):
            session = self.manager.create_session(
                personality=personality,
                name=f"Player{i}"
            )
            sessions.append(session)
        
        # Verify all sessions are active and unique
        assert len(sessions) == len(personalities)
        
        session_ids = {s.session_id for s in sessions}
        assert len(session_ids) == len(personalities)  # All unique
        
        # Verify manager tracks all sessions
        active_sessions = self.manager.list_active_sessions()
        assert len(active_sessions) == len(personalities)
    
    def test_session_cleanup(self):
        """Test proper session cleanup."""
        # Create a session
        session = self.manager.create_session(
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            name="TestPlayer"
        )
        session_id = session.session_id
        
        # Verify session exists
        assert self.manager.get_session(session_id) is not None
        
        # Deactivate session
        result = self.manager.deactivate_session(session_id)
        assert result is True
        
        # Verify session is deactivated
        retrieved_session = self.manager.get_session(session_id)
        assert retrieved_session is None  # Should return None for inactive sessions
    
    def test_memory_cleanup_prevents_leaks(self):
        """Test that old sessions are cleaned up to prevent memory leaks."""
        # Create and deactivate a session
        session = self.manager.create_session(
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            name="TestPlayer"
        )
        session_id = session.session_id
        
        # Manually mark as old (simulate time passage)
        import datetime
        session.last_activity = datetime.datetime.now() - datetime.timedelta(hours=2)
        session.deactivate()
        
        # Run cleanup
        cleaned_count = self.manager.cleanup_inactive_sessions()
        
        # Verify session was cleaned up
        assert cleaned_count >= 1
        assert session_id not in self.manager._sessions
    
    def test_personality_affects_behavior(self):
        """Test that different personalities generate different behaviors."""
        explorer = self.manager.create_session(
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            name="Explorer"
        )
        merchant = self.manager.create_session(
            personality=AIPlayerPersonality.CAUTIOUS_MERCHANT,
            name="Merchant"
        )
        
        # Get personality contexts
        explorer_context = explorer.ai_player.get_personality_context()
        merchant_context = merchant.ai_player.get_personality_context()
        
        # Verify contexts are different
        assert explorer_context != merchant_context
        
        # Verify personality-specific traits
        assert "curious" in explorer_context.lower() or "explore" in explorer_context.lower()
        assert "cautious" in merchant_context.lower() or "merchant" in merchant_context.lower()
    
    def test_manager_singleton_behavior(self):
        """Test that the global manager is properly singleton."""
        manager1 = get_ai_player_manager()
        manager2 = get_ai_player_manager()
        
        # Should be the same instance
        assert manager1 is manager2
        
        # Create session in one manager
        session = manager1.create_session(
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            name="TestPlayer"
        )
        
        # Should be accessible from the other
        retrieved = manager2.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id


class TestAIPlayerErrorHandling:
    """Test error handling in AI Player system."""
    
    def setup_method(self):
        """Set up fresh manager for each test."""
        self.manager = AIPlayerManager()
    
    def test_duplicate_session_id_error(self):
        """Test that duplicate session IDs are rejected."""
        session_id = "test-session-123"
        
        # Create first session
        self.manager.create_session(
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            session_id=session_id
        )
        
        # Attempt to create duplicate should fail
        with pytest.raises(ValueError, match="Session .* already exists"):
            self.manager.create_session(
                personality=AIPlayerPersonality.CAUTIOUS_MERCHANT,
                session_id=session_id
            )
    
    def test_nonexistent_session_handling(self):
        """Test graceful handling of nonexistent sessions."""
        # Try to get nonexistent session
        result = self.manager.get_session("nonexistent-session")
        assert result is None
        
        # Try to deactivate nonexistent session
        result = self.manager.deactivate_session("nonexistent-session")
        assert result is False
    
    @patch('core.ai_player.requests.post')
    def test_llm_failure_isolation(self, mock_post):
        """Test that LLM failures in one session don't affect others."""
        # Set up mock to fail for one request and succeed for another
        mock_post.side_effect = [
            Exception("LLM service down"),  # First request fails
            Mock(status_code=200, json=lambda: {"response": "look around"})  # Second succeeds
        ]
        
        session1 = self.manager.create_session(
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            name="Player1"
        )
        session2 = self.manager.create_session(
            personality=AIPlayerPersonality.CAUTIOUS_MERCHANT,
            name="Player2"
        )
        
        # First player's action should fail gracefully
        import asyncio
        
        async def test_actions():
            action1 = await session1.ai_player.generate_action("test context")
            action2 = await session2.ai_player.generate_action("test context")
            
            # Both should return fallback actions, not crash
            assert action1 is not None
            assert action2 is not None
            
            # Sessions should remain independent
            assert session1.ai_player.session_id != session2.ai_player.session_id
        
        # Run the async test
        asyncio.run(test_actions())


if __name__ == "__main__":
    pytest.main([__file__])