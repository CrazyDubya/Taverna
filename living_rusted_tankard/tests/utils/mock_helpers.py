"""Mock helpers for testing."""
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Any, Dict, List, Optional, Callable, Union
from contextlib import contextmanager


class MockLLMService:
    """Mock LLM service for testing."""
    
    def __init__(self):
        self.call_history = []
        self.response_queue = []
        self.default_response = {"response": "Default mock response", "confidence": 0.8}
        self.should_fail = False
        self.failure_message = "Mock LLM failure"
    
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Mock LLM response generation."""
        self.call_history.append({
            'prompt': prompt,
            'kwargs': kwargs,
            'timestamp': asyncio.get_event_loop().time()
        })
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        if self.response_queue:
            return self.response_queue.pop(0)
        
        return self.default_response.copy()
    
    def queue_response(self, response: Dict[str, Any]):
        """Queue a specific response for the next call."""
        self.response_queue.append(response)
    
    def set_failure_mode(self, should_fail: bool, message: str = "Mock failure"):
        """Configure the mock to fail."""
        self.should_fail = should_fail
        self.failure_message = message
    
    def get_call_count(self) -> int:
        """Get number of times the service was called."""
        return len(self.call_history)
    
    def get_last_call(self) -> Optional[Dict]:
        """Get the last call made to the service."""
        return self.call_history[-1] if self.call_history else None
    
    def clear_history(self):
        """Clear call history."""
        self.call_history.clear()


class MockDatabaseSession:
    """Mock database session for testing."""
    
    def __init__(self):
        self.data_store = {}
        self.call_history = []
        self.should_fail = False
        self.failure_message = "Mock database failure"
        self.transaction_active = False
    
    def __enter__(self):
        self.transaction_active = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.transaction_active = False
    
    def save_game_state(self, session_id: str, game_state: Dict) -> bool:
        """Mock save game state."""
        self.call_history.append(('save_game_state', session_id, game_state))
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.data_store[f"game_state_{session_id}"] = game_state
        return True
    
    def load_game_state(self, session_id: str) -> Optional[Dict]:
        """Mock load game state."""
        self.call_history.append(('load_game_state', session_id))
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        return self.data_store.get(f"game_state_{session_id}")
    
    def save_player(self, player_data: Dict) -> bool:
        """Mock save player."""
        self.call_history.append(('save_player', player_data))
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        player_id = player_data.get('id') or player_data.get('name')
        self.data_store[f"player_{player_id}"] = player_data
        return True
    
    def get_player(self, player_id: str) -> Optional[Dict]:
        """Mock get player."""
        self.call_history.append(('get_player', player_id))
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        return self.data_store.get(f"player_{player_id}")
    
    def set_failure_mode(self, should_fail: bool, message: str = "Mock database failure"):
        """Configure the mock to fail."""
        self.should_fail = should_fail
        self.failure_message = message
    
    def clear_data(self):
        """Clear all stored data."""
        self.data_store.clear()
        self.call_history.clear()


class MockEventBus:
    """Mock event bus for testing."""
    
    def __init__(self):
        self.published_events = []
        self.subscribers = {}
        self.should_fail = False
    
    def publish(self, event_type: str, event_data: Any):
        """Mock publish event."""
        self.published_events.append({
            'type': event_type,
            'data': event_data,
            'timestamp': asyncio.get_event_loop().time()
        })
        
        if self.should_fail:
            raise Exception("Mock event bus failure")
        
        # Notify subscribers
        for callback in self.subscribers.get(event_type, []):
            try:
                callback(event_data)
            except Exception:
                pass  # Ignore subscriber errors in mock
    
    def subscribe(self, event_type: str, callback: Callable):
        """Mock subscribe to event."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def get_published_events(self, event_type: str = None) -> List[Dict]:
        """Get published events, optionally filtered by type."""
        if event_type:
            return [e for e in self.published_events if e['type'] == event_type]
        return self.published_events.copy()
    
    def clear_events(self):
        """Clear published events."""
        self.published_events.clear()


@contextmanager
def mock_llm_service(responses: List[Dict] = None, should_fail: bool = False):
    """Context manager to mock LLM service."""
    mock_service = MockLLMService()
    
    if responses:
        for response in responses:
            mock_service.queue_response(response)
    
    if should_fail:
        mock_service.set_failure_mode(True)
    
    with patch('core.llm.narrator.LLMService', return_value=mock_service):
        yield mock_service


@contextmanager
def mock_database_session(initial_data: Dict = None, should_fail: bool = False):
    """Context manager to mock database session."""
    mock_session = MockDatabaseSession()
    
    if initial_data:
        mock_session.data_store.update(initial_data)
    
    if should_fail:
        mock_session.set_failure_mode(True)
    
    with patch('core.db.session.DatabaseSession', return_value=mock_session):
        yield mock_session


@contextmanager
def mock_event_bus(should_fail: bool = False):
    """Context manager to mock event bus."""
    mock_bus = MockEventBus()
    
    if should_fail:
        mock_bus.should_fail = True
    
    with patch('core.event_bus.EventBus', return_value=mock_bus):
        yield mock_bus


def create_async_mock(return_value: Any = None, side_effect: Any = None) -> AsyncMock:
    """Create an async mock with specified behavior."""
    mock = AsyncMock()
    
    if return_value is not None:
        mock.return_value = return_value
    
    if side_effect is not None:
        mock.side_effect = side_effect
    
    return mock


def create_mock_npc(name: str = "TestNPC", personality: str = "friendly", location: str = "tavern") -> Mock:
    """Create a mock NPC for testing."""
    mock_npc = Mock()
    mock_npc.name = name
    mock_npc.personality = personality
    mock_npc.location = location
    mock_npc.is_active = True
    mock_npc.conversation_history = []
    
    # Mock methods
    mock_npc.interact = AsyncMock(return_value="Mock NPC interaction")
    mock_npc.get_schedule = Mock(return_value={"morning": "work", "evening": "rest"})
    mock_npc.update_relationship = Mock()
    
    return mock_npc


def create_mock_player(name: str = "TestPlayer", gold: int = 100, health: int = 100) -> Mock:
    """Create a mock player for testing."""
    mock_player = Mock()
    mock_player.name = name
    mock_player.gold = gold
    mock_player.health = health
    mock_player.max_health = 100
    mock_player.experience = 0
    mock_player.level = 1
    mock_player.inventory = []
    
    # Mock methods
    mock_player.add_gold = Mock()
    mock_player.remove_gold = Mock(return_value=True)
    mock_player.heal = Mock()
    mock_player.take_damage = Mock()
    mock_player.add_experience = Mock()
    mock_player.level_up = Mock()
    
    return mock_player


class MockHTTPSession:
    """Mock HTTP session for testing."""
    
    def __init__(self):
        self.request_history = []
        self.response_queue = []
        self.default_response = {"status": "success", "data": {}}
        self.should_fail = False
        self.failure_exception = Exception("Mock HTTP failure")
        self.closed = False
    
    async def get(self, url: str, **kwargs) -> Mock:
        """Mock GET request."""
        return await self._make_request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> Mock:
        """Mock POST request."""
        return await self._make_request("POST", url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> Mock:
        """Mock PUT request."""
        return await self._make_request("PUT", url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> Mock:
        """Mock DELETE request."""
        return await self._make_request("DELETE", url, **kwargs)
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Mock:
        """Internal request handling."""
        self.request_history.append({
            'method': method,
            'url': url,
            'kwargs': kwargs,
            'timestamp': asyncio.get_event_loop().time()
        })
        
        if self.should_fail:
            raise self.failure_exception
        
        if self.response_queue:
            response_data = self.response_queue.pop(0)
        else:
            response_data = self.default_response.copy()
        
        mock_response = Mock()
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.text = AsyncMock(return_value=str(response_data))
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        
        return mock_response
    
    async def close(self):
        """Mock close session."""
        self.closed = True
    
    def queue_response(self, response: Dict):
        """Queue a specific response."""
        self.response_queue.append(response)
    
    def set_failure_mode(self, should_fail: bool, exception: Exception = None):
        """Configure failure mode."""
        self.should_fail = should_fail
        if exception:
            self.failure_exception = exception


@contextmanager
def mock_http_session():
    """Context manager to mock HTTP session."""
    mock_session = MockHTTPSession()
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        yield mock_session


def create_mock_game_state(session_id: str = "test_session") -> Dict[str, Any]:
    """Create a mock game state for testing."""
    return {
        'session_id': session_id,
        'player': {
            'name': 'TestPlayer',
            'gold': 100,
            'health': 100,
            'level': 1
        },
        'npcs': [
            {'name': 'Barkeep', 'location': 'tavern', 'active': True},
            {'name': 'Guard', 'location': 'entrance', 'active': True}
        ],
        'current_location': 'tavern',
        'game_time': {'hour': 12, 'day': 1, 'season': 'spring'},
        'economy': {
            'market_prices': {'ale': 5, 'bread': 3},
            'active_jobs': []
        }
    }