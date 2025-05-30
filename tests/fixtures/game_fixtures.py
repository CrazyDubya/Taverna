"""
Game state and core component fixtures.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any, Optional

# Import core components (with error handling for missing dependencies)
try:
    from core.game_state import GameState
    from core.clock import GameClock
    from core.player import PlayerState, Inventory
    from core.room import RoomManager
    from core.economy import Economy
    from core.npc import NPCManager
    from core.bounties import BountyManager
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False


@pytest.fixture
def clean_game_state():
    """Create a completely fresh game state for isolated testing."""
    if not CORE_AVAILABLE:
        pytest.skip("Core modules not available")
    
    return GameState()


@pytest.fixture
def game_state_with_player():
    """Create a game state with a basic test player."""
    if not CORE_AVAILABLE:
        pytest.skip("Core modules not available")
    
    game_state = GameState()
    # Initialize player with basic setup
    game_state.player.gold = 20  # Starting gold
    game_state.player.tiredness = 0
    game_state.player.energy = 100
    return game_state


@pytest.fixture
def rich_player_game_state():
    """Create a game state with a wealthy player for testing purchases."""
    if not CORE_AVAILABLE:
        pytest.skip("Core modules not available")
    
    game_state = GameState()
    game_state.player.gold = 1000  # Rich player
    game_state.player.tiredness = 0
    game_state.player.energy = 100
    return game_state


@pytest.fixture
def tired_player_game_state():
    """Create a game state with a tired player for testing sleep mechanics."""
    if not CORE_AVAILABLE:
        pytest.skip("Core modules not available")
    
    game_state = GameState()
    game_state.player.gold = 20
    game_state.player.tiredness = 80  # Very tired
    game_state.player.energy = 20    # Low energy
    return game_state


@pytest.fixture
def time_controlled_game_state():
    """Create a game state with controllable time for testing time-based mechanics."""
    if not CORE_AVAILABLE:
        pytest.skip("Core modules not available")
    
    game_state = GameState()
    
    # Mock the clock for time control
    with patch.object(game_state.clock, 'get_current_time_hours') as mock_time:
        mock_time.return_value = 12.0  # Start at noon
        yield game_state, mock_time


@pytest.fixture
def populated_game_state():
    """Create a game state with NPCs, items, and bounties for complex testing."""
    if not CORE_AVAILABLE:
        pytest.skip("Core modules not available")
    
    game_state = GameState()
    
    # Add some test items to inventory
    test_items = ["bread", "ale", "rusty_sword"]
    for item in test_items:
        if hasattr(game_state.player, 'inventory'):
            game_state.player.inventory.add_item(item, 1)
    
    # Add some test NPCs (this will depend on how NPCs are loaded)
    # This might need adjustment based on actual NPC system
    if hasattr(game_state, 'npc_manager'):
        # Force some NPCs to be present for testing
        game_state.npc_manager.force_npc_presence("gene_bartender")
    
    return game_state


@pytest.fixture
def mock_llm_service():
    """Mock the LLM service for testing without external dependencies."""
    mock_responses = {
        "default": "look around",
        "social": "talk to bartender",
        "economic": "check inventory",
        "exploration": "read notice board"
    }
    
    def mock_generate_response(prompt: str, **kwargs) -> str:
        """Generate a mock response based on prompt content."""
        prompt_lower = prompt.lower()
        if "social" in prompt_lower or "talk" in prompt_lower:
            return mock_responses["social"]
        elif "gold" in prompt_lower or "inventory" in prompt_lower:
            return mock_responses["economic"]
        elif "look" in prompt_lower or "explore" in prompt_lower:
            return mock_responses["exploration"]
        else:
            return mock_responses["default"]
    
    with patch('core.llm.ollama_client.OllamaClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.generate.side_effect = lambda model, prompt, **kwargs: {
            "response": mock_generate_response(prompt, **kwargs)
        }
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_database():
    """Mock database operations for testing without database dependencies."""
    class MockDatabase:
        def __init__(self):
            self.data = {}
            self.calls = []
        
        def save(self, key: str, data: Any) -> bool:
            self.calls.append(("save", key, data))
            self.data[key] = data
            return True
        
        def load(self, key: str) -> Optional[Any]:
            self.calls.append(("load", key))
            return self.data.get(key)
        
        def delete(self, key: str) -> bool:
            self.calls.append(("delete", key))
            return self.data.pop(key, None) is not None
        
        def clear(self):
            self.data.clear()
            self.calls.clear()
    
    return MockDatabase()


@pytest.fixture
def isolated_test_environment():
    """Create a completely isolated test environment with all dependencies mocked."""
    mocks = {}
    
    # Mock external services
    with patch('requests.post') as mock_requests, \
         patch('aiohttp.ClientSession') as mock_aiohttp, \
         patch('sqlite3.connect') as mock_sqlite:
        
        # Configure request mocks
        mock_requests.return_value.status_code = 200
        mock_requests.return_value.json.return_value = {"response": "look around"}
        
        # Configure aiohttp mocks
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"response": "look around"}
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_aiohttp.return_value = mock_session
        
        # Configure database mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_sqlite.return_value = mock_conn
        
        mocks['requests'] = mock_requests
        mocks['aiohttp'] = mock_aiohttp
        mocks['sqlite'] = mock_sqlite
        mocks['db_connection'] = mock_conn
        mocks['db_cursor'] = mock_cursor
        
        yield mocks


@pytest.fixture
def performance_test_environment():
    """Create an environment for performance testing with timing utilities."""
    import time
    
    class PerformanceTracker:
        def __init__(self):
            self.timings = {}
            self.start_times = {}
        
        def start_timer(self, name: str):
            self.start_times[name] = time.perf_counter()
        
        def end_timer(self, name: str) -> float:
            if name not in self.start_times:
                raise ValueError(f"Timer '{name}' was not started")
            
            duration = time.perf_counter() - self.start_times[name]
            self.timings[name] = duration
            del self.start_times[name]
            return duration
        
        def get_timing(self, name: str) -> Optional[float]:
            return self.timings.get(name)
        
        def assert_timing_under(self, name: str, max_seconds: float):
            timing = self.get_timing(name)
            if timing is None:
                raise ValueError(f"No timing recorded for '{name}'")
            assert timing < max_seconds, f"Operation '{name}' took {timing:.3f}s, expected < {max_seconds}s"
    
    return PerformanceTracker()


@pytest.fixture(scope="session")
def test_data_directory(tmp_path_factory):
    """Create a temporary directory for test data files."""
    return tmp_path_factory.mktemp("test_data")


@pytest.fixture
def mock_config():
    """Provide mock configuration for testing."""
    return {
        "starting_gold": 20,
        "max_tiredness": 100,
        "max_energy": 100,
        "room_rent_cost": 10,
        "chest_cost": 5,
        "job_cooldown_seconds": 10,
        "llm_timeout": 30,
        "cache_ttl": 300
    }