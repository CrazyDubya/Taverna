"""
Tests for resource cleanup in HTTP sessions.

This test suite verifies that HTTP sessions are properly cleaned up
to prevent resource leaks.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock

# Mock aiohttp to avoid dependency issues
import sys
from unittest.mock import MagicMock

# Mock aiohttp module
mock_aiohttp = MagicMock()
mock_aiohttp.ClientSession = MagicMock
mock_aiohttp.ClientTimeout = MagicMock
sys.modules['aiohttp'] = mock_aiohttp


class MockClientSession:
    """Mock aiohttp ClientSession for testing."""
    
    def __init__(self, timeout=None):
        self.closed = False
        self.close_called = False
        self.requests_made = []
    
    async def post(self, url, json=None):
        """Mock post method."""
        self.requests_made.append((url, json))
        return MockResponse()
    
    async def close(self):
        """Mock close method."""
        self.close_called = True
        self.closed = True
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class MockResponse:
    """Mock aiohttp response."""
    
    def __init__(self, status=200, json_data=None):
        self.status = status
        self._json_data = json_data or {"response": "look around"}
    
    async def json(self):
        return self._json_data
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestResourceCleanup:
    """Test resource cleanup in AI Player and related systems."""
    
    @pytest.mark.asyncio
    async def test_ai_player_session_cleanup(self):
        """Test that AI Player properly cleans up HTTP sessions."""
        # Mock aiohttp ClientSession
        mock_session = MockClientSession()
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            # Import here to ensure mock is in place
            sys.path.insert(0, '/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard')
            
            from core.ai_player import AIPlayer, AIPlayerPersonality
            
            # Create AI player
            ai_player = AIPlayer(
                name="TestAI",
                personality=AIPlayerPersonality.CURIOUS_EXPLORER
            )
            
            # Use session
            session = await ai_player._get_session()
            assert session is not None
            assert not session.closed
            
            # Make a request to ensure session is used
            action = await ai_player.generate_action("test context")
            assert action == "look around"  # Default fallback
            
            # Clean up
            await ai_player.close()
            
            # Verify session was closed
            assert session.close_called
            assert session.closed
    
    @pytest.mark.asyncio 
    async def test_ai_player_context_manager(self):
        """Test AI Player as async context manager."""
        mock_session = MockClientSession()
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            sys.path.insert(0, '/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard')
            
            from core.ai_player import AIPlayer, AIPlayerPersonality
            
            # Use as context manager
            async with AIPlayer(
                name="TestAI",
                personality=AIPlayerPersonality.CURIOUS_EXPLORER
            ) as ai_player:
                # Session should be created when needed
                session = await ai_player._get_session()
                assert not session.closed
                
                # Make a request
                await ai_player.generate_action("test context")
            
            # Session should be closed after context manager exit
            assert session.close_called
            assert session.closed
    
    @pytest.mark.asyncio
    async def test_ai_player_manager_cleanup(self):
        """Test that AI Player Manager properly cleans up sessions."""
        mock_session = MockClientSession()
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            sys.path.insert(0, '/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard')
            
            from core.ai_player import AIPlayerPersonality
            from core.ai_player_manager import AIPlayerManager
            
            manager = AIPlayerManager()
            
            # Create a session
            session = manager.create_session(
                personality=AIPlayerPersonality.CURIOUS_EXPLORER,
                name="TestAI"
            )
            
            # Verify session is active
            assert session.is_active
            retrieved = manager.get_session(session.session_id)
            assert retrieved is not None
            
            # Use the AI player to create HTTP session
            await session.ai_player._get_session()
            
            # Deactivate session
            result = await manager.deactivate_session(session.session_id)
            assert result is True
            
            # Verify session is deactivated and cleaned up
            assert not session.is_active
            assert mock_session.close_called
            
            # Should not be retrievable anymore
            retrieved = manager.get_session(session.session_id)
            assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_cleanup_on_exception(self):
        """Test that resources are cleaned up even when exceptions occur."""
        mock_session = MockClientSession()
        
        # Make the session.post method raise an exception
        async def failing_post(*args, **kwargs):
            raise Exception("Network error")
        
        mock_session.post = failing_post
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            sys.path.insert(0, '/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard')
            
            from core.ai_player import AIPlayer, AIPlayerPersonality
            
            ai_player = AIPlayer(
                name="TestAI",
                personality=AIPlayerPersonality.CURIOUS_EXPLORER
            )
            
            # This should handle the exception gracefully
            action = await ai_player.generate_action("test context")
            assert action == "look around"  # Should return fallback
            
            # Clean up
            await ai_player.close()
            
            # Session should still be cleaned up
            assert mock_session.close_called
    
    @pytest.mark.asyncio
    async def test_multiple_sessions_cleanup(self):
        """Test cleanup when multiple sessions exist."""
        sessions = []
        
        def create_mock_session(*args, **kwargs):
            session = MockClientSession()
            sessions.append(session)
            return session
        
        with patch('aiohttp.ClientSession', side_effect=create_mock_session):
            sys.path.insert(0, '/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard')
            
            from core.ai_player import AIPlayerPersonality
            from core.ai_player_manager import AIPlayerManager
            
            manager = AIPlayerManager()
            
            # Create multiple AI player sessions
            player_sessions = []
            for i in range(3):
                session = manager.create_session(
                    personality=AIPlayerPersonality.CURIOUS_EXPLORER,
                    name=f"TestAI-{i}"
                )
                player_sessions.append(session)
                
                # Initialize HTTP session
                await session.ai_player._get_session()
            
            # Verify we have the expected number of sessions
            assert len(sessions) == 3
            assert all(not s.closed for s in sessions)
            
            # Clean up all sessions
            await manager.clear_all_sessions()
            
            # Verify all HTTP sessions were closed
            assert all(s.close_called for s in sessions)
            assert all(s.closed for s in sessions)
            
            # Verify all player sessions are deactivated
            assert all(not ps.is_active for ps in player_sessions)


class TestResourceCleanupPatterns:
    """Test the resource cleanup patterns and best practices."""
    
    def test_cleanup_pattern_structure(self):
        """Test that cleanup methods follow the expected pattern."""
        # This tests the code structure and patterns
        
        # Check AI Player has proper cleanup methods
        sys.path.insert(0, '/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard')
        
        from core.ai_player import AIPlayer
        
        # Verify cleanup methods exist
        assert hasattr(AIPlayer, 'close'), "AIPlayer should have close() method"
        assert hasattr(AIPlayer, '__aenter__'), "AIPlayer should be async context manager"
        assert hasattr(AIPlayer, '__aexit__'), "AIPlayer should be async context manager"
        
        # Check method signatures
        import inspect
        
        close_sig = inspect.signature(AIPlayer.close)
        assert len(close_sig.parameters) == 1, "close() should only take self parameter"
        
        aenter_sig = inspect.signature(AIPlayer.__aenter__)
        assert len(aenter_sig.parameters) == 1, "__aenter__ should only take self parameter"
        
        aexit_sig = inspect.signature(AIPlayer.__aexit__)
        assert len(aexit_sig.parameters) == 4, "__aexit__ should take self + 3 exception parameters"
    
    def test_session_manager_cleanup_pattern(self):
        """Test that session manager follows cleanup patterns."""
        sys.path.insert(0, '/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard')
        
        from core.ai_player_manager import AIPlayerManager, AIPlayerSession
        
        # Verify cleanup methods exist
        assert hasattr(AIPlayerSession, 'deactivate'), "AIPlayerSession should have deactivate() method"
        assert hasattr(AIPlayerManager, 'deactivate_session'), "Manager should have deactivate_session() method"
        assert hasattr(AIPlayerManager, 'cleanup_inactive_sessions'), "Manager should have cleanup method"
        assert hasattr(AIPlayerManager, 'clear_all_sessions'), "Manager should have clear_all_sessions() method"
        
        # Check that methods are async where expected
        import inspect
        
        deactivate_sig = inspect.signature(AIPlayerSession.deactivate)
        assert inspect.iscoroutinefunction(AIPlayerSession.deactivate), "deactivate should be async"
        
        deactivate_session_sig = inspect.signature(AIPlayerManager.deactivate_session)
        assert inspect.iscoroutinefunction(AIPlayerManager.deactivate_session), "deactivate_session should be async"
    
    def test_imports_and_structure(self):
        """Test that required imports are present."""
        # Check that aiohttp is imported
        sys.path.insert(0, '/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard')
        
        # Read the file to check imports
        with open('/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard/core/ai_player.py', 'r') as f:
            content = f.read()
        
        assert 'import aiohttp' in content, "aiohttp should be imported"
        assert 'self._session:' in content, "Should have _session attribute"
        assert 'async def _get_session(' in content, "Should have _get_session method"


if __name__ == "__main__":
    # Run a simple test without pytest
    print("Running resource cleanup tests...")
    
    async def run_tests():
        test_instance = TestResourceCleanup()
        
        try:
            await test_instance.test_ai_player_session_cleanup()
            print("✅ AI Player session cleanup test passed")
            
            await test_instance.test_ai_player_context_manager()
            print("✅ AI Player context manager test passed")
            
            await test_instance.test_cleanup_on_exception()
            print("✅ Cleanup on exception test passed")
            
            print("\n🟢 All resource cleanup tests passed!")
            
        except Exception as e:
            print(f"\n🔴 Test failed: {e}")
            raise
    
    asyncio.run(run_tests())