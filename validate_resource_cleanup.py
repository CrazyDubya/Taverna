#!/usr/bin/env python3
"""
Validate resource cleanup improvements.
"""

import sys
import os
import asyncio

# Add the project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'living_rusted_tankard'))

def validate_code_changes():
    """Validate that resource cleanup code is implemented correctly."""
    print("🔍 Validating resource cleanup improvements...")
    
    # Check AI Player file
    ai_player_path = "living_rusted_tankard/core/ai_player.py"
    
    with open(ai_player_path, 'r') as f:
        content = f.read()
    
    # Check for required imports and patterns
    required_patterns = [
        "import aiohttp",
        "self._session: Optional[aiohttp.ClientSession] = None",
        "async def _get_session(self)",
        "async def close(self)",
        "async def __aenter__(self)",
        "async def __aexit__(self",
        "async with session.post(",
        "await self._session.close()"
    ]
    
    for pattern in required_patterns:
        if pattern in content:
            print(f"✅ Found: {pattern}")
        else:
            print(f"❌ Missing: {pattern}")
            return False
    
    # Check that requests is being replaced with aiohttp
    if "requests.post(" in content:
        print("❌ Still using requests.post - should use aiohttp")
        return False
    else:
        print("✅ Removed requests.post usage")
    
    # Check AI Player Manager
    manager_path = "living_rusted_tankard/core/ai_player_manager.py"
    
    with open(manager_path, 'r') as f:
        manager_content = f.read()
    
    manager_patterns = [
        "async def deactivate(self)",
        "await self.ai_player.close()",
        "async def deactivate_session(",
        "await session.deactivate()",
        "async def cleanup_inactive_sessions(",
        "async def clear_all_sessions("
    ]
    
    for pattern in manager_patterns:
        if pattern in manager_content:
            print(f"✅ Manager has: {pattern}")
        else:
            print(f"❌ Manager missing: {pattern}")
            return False
    
    # Check API Router
    api_path = "living_rusted_tankard/api/routers/ai_player.py"
    
    with open(api_path, 'r') as f:
        api_content = f.read()
    
    if "await manager.deactivate_session(session_id)" in api_content:
        print("✅ API router uses async deactivation")
    else:
        print("❌ API router not using async deactivation")
        return False
    
    print("✅ Resource cleanup code validation passed")
    return True

async def test_basic_cleanup():
    """Test basic cleanup functionality with mocks."""
    print("\n🔄 Testing basic resource cleanup...")
    
    # Mock aiohttp to avoid dependency issues
    import sys
    from unittest.mock import MagicMock, AsyncMock
    
    # Create a mock aiohttp module
    mock_aiohttp = MagicMock()
    
    class MockSession:
        def __init__(self, timeout=None):
            self.closed = False
            self.close_called = False
        
        async def close(self):
            self.close_called = True
            self.closed = True
        
        async def post(self, url, json=None):
            return MockResponse()
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    class MockResponse:
        def __init__(self):
            self.status = 200
        
        async def json(self):
            return {"response": "look around"}
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    mock_aiohttp.ClientSession = MockSession
    mock_aiohttp.ClientTimeout = MagicMock
    
    # Replace aiohttp in sys.modules
    sys.modules['aiohttp'] = mock_aiohttp
    
    try:
        from core.ai_player import AIPlayer, AIPlayerPersonality
        
        # Test 1: Basic session cleanup
        ai_player = AIPlayer(
            name="TestAI",
            personality=AIPlayerPersonality.CURIOUS_EXPLORER
        )
        
        # Get session
        session = await ai_player._get_session()
        assert hasattr(session, 'close_called'), "Mock session should have close_called"
        assert not session.closed, "Session should not be closed initially"
        
        # Close
        await ai_player.close()
        assert session.close_called, "Session close should have been called"
        assert session.closed, "Session should be closed"
        print("✅ Basic session cleanup works")
        
        # Test 2: Context manager
        async with AIPlayer(
            name="TestAI2",
            personality=AIPlayerPersonality.CAUTIOUS_MERCHANT
        ) as ai_player2:
            session2 = await ai_player2._get_session()
            assert not session2.closed, "Session should be open in context"
        
        assert session2.close_called, "Session should be closed after context exit"
        print("✅ Context manager cleanup works")
        
        # Test 3: Manager cleanup
        from core.ai_player_manager import AIPlayerManager
        
        manager = AIPlayerManager()
        
        # Create session
        player_session = manager.create_session(
            personality=AIPlayerPersonality.CURIOUS_EXPLORER,
            name="TestAI3"
        )
        
        # Initialize HTTP session
        http_session = await player_session.ai_player._get_session()
        
        # Deactivate
        result = await manager.deactivate_session(player_session.session_id)
        assert result is True, "Deactivation should succeed"
        assert not player_session.is_active, "Session should be inactive"
        assert http_session.close_called, "HTTP session should be closed"
        print("✅ Manager cleanup works")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def check_file_changes():
    """Check that all required files were modified."""
    print("\n📁 Checking file modifications...")
    
    required_files = [
        "living_rusted_tankard/core/ai_player.py",
        "living_rusted_tankard/core/ai_player_manager.py",
        "living_rusted_tankard/api/routers/ai_player.py",
        "tests/unit/test_resource_cleanup.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ File missing: {file_path}")
            return False
        print(f"✅ File exists: {file_path}")
    
    return True

async def main():
    """Main validation function."""
    print("🚀 Starting resource cleanup validation...\n")
    
    try:
        # Check file structure
        if not check_file_changes():
            print("\n🔴 FAILURE: Required files are missing")
            return False
        
        # Validate code changes
        if not validate_code_changes():
            print("\n🔴 FAILURE: Resource cleanup code validation failed")
            return False
        
        # Test basic functionality
        if not await test_basic_cleanup():
            print("\n🔴 FAILURE: Resource cleanup test failed")
            return False
        
        print("\n🟢 SUCCESS: All resource cleanup validations passed!")
        print("\n📋 Summary of changes:")
        print("  1. ✅ Added aiohttp import to AI Player")
        print("  2. ✅ Added session management with _get_session() method")
        print("  3. ✅ Replaced requests.post with aiohttp session.post")
        print("  4. ✅ Added proper async context manager support")
        print("  5. ✅ Added close() method for resource cleanup")
        print("  6. ✅ Updated AI Player Manager for async cleanup")
        print("  7. ✅ Updated API router to handle async deactivation")
        print("  8. ✅ Created comprehensive resource cleanup tests")
        print("\n🎯 Resource cleanup issues have been successfully resolved!")
        print("   HTTP sessions now properly close to prevent resource leaks.")
        
        return True
        
    except Exception as e:
        print(f"\n🔴 FAILURE: Validation error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)