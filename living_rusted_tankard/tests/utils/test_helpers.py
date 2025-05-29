"""General test helper utilities."""
import asyncio
import json
import tempfile
import os
from typing import Any, Dict, List, Optional, Callable
from unittest.mock import Mock, patch
from contextlib import contextmanager, asynccontextmanager


def create_test_config(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a test configuration with optional overrides."""
    default_config = {
        'database_url': ':memory:',
        'llm_model': 'test-model',
        'max_retries': 3,
        'timeout_seconds': 30,
        'debug_mode': True,
        'api_base_url': 'http://localhost:8000',
        'session_timeout': 3600
    }
    
    if overrides:
        default_config.update(overrides)
    
    return default_config


@contextmanager
def temporary_file(content: str = "", suffix: str = ".txt"):
    """Create a temporary file with content."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        yield tmp_file_path
    finally:
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@contextmanager
def temporary_directory():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


def wait_for_condition(condition: Callable[[], bool], timeout: float = 5.0, interval: float = 0.1) -> bool:
    """Wait for a condition to become true within timeout."""
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition():
            return True
        time.sleep(interval)
    
    return False


async def wait_for_async_condition(condition: Callable[[], bool], timeout: float = 5.0, interval: float = 0.1) -> bool:
    """Async version of wait_for_condition."""
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        if condition():
            return True
        await asyncio.sleep(interval)
    
    return False


def create_mock_response(status_code: int = 200, json_data: Dict = None, text: str = ""):
    """Create a mock HTTP response."""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    mock_response.text = text
    mock_response.raise_for_status = Mock()
    
    if status_code >= 400:
        from requests.exceptions import HTTPError
        mock_response.raise_for_status.side_effect = HTTPError(f"HTTP {status_code}")
    
    return mock_response


def assert_eventually(assertion_func: Callable, timeout: float = 5.0, interval: float = 0.1):
    """Assert that a condition eventually becomes true."""
    def condition():
        try:
            assertion_func()
            return True
        except AssertionError:
            return False
    
    if not wait_for_condition(condition, timeout, interval):
        assertion_func()  # Run one last time to get the actual assertion error


class EventCollector:
    """Collect events for testing event-driven systems."""
    
    def __init__(self):
        self.events = []
        self.event_filters = {}
    
    def collect_event(self, event_type: str, event_data: Any):
        """Collect an event."""
        self.events.append({
            'type': event_type,
            'data': event_data,
            'timestamp': asyncio.get_event_loop().time()
        })
    
    def get_events(self, event_type: str = None) -> List[Dict]:
        """Get collected events, optionally filtered by type."""
        if event_type:
            return [e for e in self.events if e['type'] == event_type]
        return self.events.copy()
    
    def clear_events(self):
        """Clear all collected events."""
        self.events.clear()
    
    def wait_for_event(self, event_type: str, timeout: float = 5.0) -> Optional[Dict]:
        """Wait for a specific event type to occur."""
        def has_event():
            return any(e['type'] == event_type for e in self.events)
        
        if wait_for_condition(has_event, timeout):
            matching_events = self.get_events(event_type)
            return matching_events[-1] if matching_events else None
        
        return None
    
    def assert_event_occurred(self, event_type: str, count: int = 1):
        """Assert that an event occurred the expected number of times."""
        matching_events = self.get_events(event_type)
        assert len(matching_events) == count, \
            f"Expected {count} events of type '{event_type}', got {len(matching_events)}"
    
    def assert_event_sequence(self, expected_sequence: List[str]):
        """Assert that events occurred in a specific sequence."""
        actual_sequence = [e['type'] for e in self.events]
        assert actual_sequence == expected_sequence, \
            f"Expected event sequence {expected_sequence}, got {actual_sequence}"


class AsyncTestHelper:
    """Helper for async testing scenarios."""
    
    @staticmethod
    async def run_concurrent_operations(operations: List[Callable], max_concurrent: int = 10):
        """Run operations concurrently with limited concurrency."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(op):
            async with semaphore:
                if asyncio.iscoroutinefunction(op):
                    return await op()
                else:
                    return op()
        
        return await asyncio.gather(*[run_with_semaphore(op) for op in operations], return_exceptions=True)
    
    @staticmethod
    @asynccontextmanager
    async def timeout_context(timeout_seconds: float):
        """Context manager for async operations with timeout."""
        try:
            async with asyncio.timeout(timeout_seconds):
                yield
        except asyncio.TimeoutError:
            raise AssertionError(f"Operation timed out after {timeout_seconds} seconds")
    
    @staticmethod
    async def wait_for_tasks_completion(timeout: float = 5.0):
        """Wait for all pending async tasks to complete."""
        pending_tasks = [task for task in asyncio.all_tasks() if not task.done()]
        
        if pending_tasks:
            try:
                await asyncio.wait_for(asyncio.gather(*pending_tasks, return_exceptions=True), timeout=timeout)
            except asyncio.TimeoutError:
                # Cancel remaining tasks
                for task in pending_tasks:
                    if not task.done():
                        task.cancel()
                raise AssertionError(f"Some async tasks did not complete within {timeout} seconds")


def create_test_data_file(data: Dict, file_format: str = "json") -> str:
    """Create a temporary file with test data."""
    if file_format == "json":
        content = json.dumps(data, indent=2)
        suffix = ".json"
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    with temporary_file(content, suffix) as file_path:
        return file_path


def assert_dict_subset(subset: Dict, full_dict: Dict, strict: bool = False):
    """Assert that subset is contained within full_dict."""
    for key, value in subset.items():
        assert key in full_dict, f"Key '{key}' not found in full dictionary"
        
        if isinstance(value, dict) and isinstance(full_dict[key], dict):
            assert_dict_subset(value, full_dict[key], strict)
        else:
            assert full_dict[key] == value, f"Value mismatch for key '{key}': expected {value}, got {full_dict[key]}"
    
    if strict:
        assert set(subset.keys()) == set(full_dict.keys()), \
            f"Dictionary keys don't match exactly. Expected {set(subset.keys())}, got {set(full_dict.keys())}"


def generate_test_ids(prefix: str = "test", count: int = 5) -> List[str]:
    """Generate unique test IDs."""
    import uuid
    return [f"{prefix}_{uuid.uuid4().hex[:8]}" for _ in range(count)]