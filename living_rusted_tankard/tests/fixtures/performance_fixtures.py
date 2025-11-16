"""Performance testing fixtures and utilities."""
import pytest
import time
import asyncio
import resource
import psutil
import threading
from unittest.mock import Mock, patch
from typing import Dict, List, Any, Callable
from contextlib import contextmanager
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class PerformanceMetrics:
    """Container for performance test results."""

    execution_time: float
    memory_usage: float
    cpu_usage: float
    thread_count: int
    async_tasks: int = 0
    custom_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = {}


@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during test execution."""

    class PerformanceMonitor:
        def __init__(self):
            self.metrics_history = []
            self.thresholds = {
                "max_execution_time": 5.0,  # seconds
                "max_memory_mb": 100,  # MB
                "max_cpu_percent": 80,  # %
                "max_threads": 10,
            }

        @contextmanager
        def measure(self, operation_name: str = "test_operation"):
            """Context manager to measure performance of code block."""
            process = psutil.Process()

            # Initial measurements
            start_time = time.time()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            start_cpu_times = process.cpu_times()
            start_threads = process.num_threads()

            try:
                yield self
            finally:
                # Final measurements
                end_time = time.time()
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                end_cpu_times = process.cpu_times()
                end_threads = process.num_threads()

                # Calculate metrics
                execution_time = end_time - start_time
                memory_usage = end_memory - start_memory
                cpu_usage = (
                    (
                        (end_cpu_times.user + end_cpu_times.system)
                        - (start_cpu_times.user + start_cpu_times.system)
                    )
                    / execution_time
                    * 100
                )
                thread_count = end_threads

                metrics = PerformanceMetrics(
                    execution_time=execution_time,
                    memory_usage=memory_usage,
                    cpu_usage=cpu_usage,
                    thread_count=thread_count,
                )

                self.metrics_history.append(
                    {
                        "operation": operation_name,
                        "metrics": metrics,
                        "timestamp": end_time,
                    }
                )

        def assert_performance_thresholds(
            self, custom_thresholds: Dict[str, float] = None
        ):
            """Assert that latest metrics meet performance thresholds."""
            if not self.metrics_history:
                return

            thresholds = self.thresholds.copy()
            if custom_thresholds:
                thresholds.update(custom_thresholds)

            latest = self.metrics_history[-1]["metrics"]

            assert (
                latest.execution_time <= thresholds["max_execution_time"]
            ), f"Execution time {latest.execution_time:.2f}s exceeds threshold {thresholds['max_execution_time']}s"

            assert (
                latest.memory_usage <= thresholds["max_memory_mb"]
            ), f"Memory usage {latest.memory_usage:.2f}MB exceeds threshold {thresholds['max_memory_mb']}MB"

            assert (
                latest.cpu_usage <= thresholds["max_cpu_percent"]
            ), f"CPU usage {latest.cpu_usage:.1f}% exceeds threshold {thresholds['max_cpu_percent']}%"

            assert (
                latest.thread_count <= thresholds["max_threads"]
            ), f"Thread count {latest.thread_count} exceeds threshold {thresholds['max_threads']}"

        def get_metrics_summary(self):
            """Get summary of all collected metrics."""
            if not self.metrics_history:
                return {}

            execution_times = [
                m["metrics"].execution_time for m in self.metrics_history
            ]
            memory_usages = [m["metrics"].memory_usage for m in self.metrics_history]

            return {
                "total_operations": len(self.metrics_history),
                "avg_execution_time": sum(execution_times) / len(execution_times),
                "max_execution_time": max(execution_times),
                "avg_memory_usage": sum(memory_usages) / len(memory_usages),
                "max_memory_usage": max(memory_usages),
                "operations": [m["operation"] for m in self.metrics_history],
            }

    return PerformanceMonitor()


@pytest.fixture
def async_performance_monitor():
    """Monitor performance for async operations."""

    class AsyncPerformanceMonitor:
        def __init__(self):
            self.task_metrics = defaultdict(list)
            self.active_tasks = {}

        @contextmanager
        def measure_async_operation(self, operation_name: str):
            """Measure async operation performance."""
            start_time = time.time()
            task_count_before = len(asyncio.all_tasks())

            try:
                yield self
            finally:
                end_time = time.time()
                task_count_after = len(asyncio.all_tasks())

                metrics = {
                    "execution_time": end_time - start_time,
                    "tasks_created": task_count_after - task_count_before,
                    "timestamp": end_time,
                }

                self.task_metrics[operation_name].append(metrics)

        async def measure_concurrent_operations(
            self, operations: List[Callable], operation_name: str
        ):
            """Measure performance of concurrent async operations."""
            start_time = time.time()

            # Execute all operations concurrently
            results = await asyncio.gather(
                *[op() for op in operations], return_exceptions=True
            )

            end_time = time.time()

            metrics = {
                "total_execution_time": end_time - start_time,
                "operation_count": len(operations),
                "success_count": len(
                    [r for r in results if not isinstance(r, Exception)]
                ),
                "error_count": len([r for r in results if isinstance(r, Exception)]),
                "avg_time_per_operation": (end_time - start_time) / len(operations),
            }

            self.task_metrics[operation_name].append(metrics)
            return results

        def get_async_summary(self):
            """Get summary of async performance metrics."""
            summary = {}
            for operation, metrics_list in self.task_metrics.items():
                if metrics_list:
                    execution_times = [m.get("execution_time", 0) for m in metrics_list]
                    summary[operation] = {
                        "call_count": len(metrics_list),
                        "avg_execution_time": sum(execution_times)
                        / len(execution_times)
                        if execution_times
                        else 0,
                        "max_execution_time": max(execution_times)
                        if execution_times
                        else 0,
                        "total_execution_time": sum(execution_times),
                    }
            return summary

    return AsyncPerformanceMonitor()


@pytest.fixture
def load_test_generator():
    """Generate load testing scenarios."""

    class LoadTestGenerator:
        def __init__(self):
            self.scenarios = {}

        def create_user_load(self, concurrent_users: int, operations_per_user: int):
            """Create a user load testing scenario."""

            def user_simulation():
                operations = []
                for i in range(operations_per_user):
                    # Simulate various user operations
                    operations.append(
                        lambda: time.sleep(0.1)
                    )  # Simulate processing time
                return operations

            return [user_simulation() for _ in range(concurrent_users)]

        def create_api_load(self, requests_per_second: int, duration_seconds: int):
            """Create API load testing scenario."""
            total_requests = requests_per_second * duration_seconds
            interval = 1.0 / requests_per_second

            async def api_request_simulator():
                # Simulate API request processing
                await asyncio.sleep(0.05)  # Simulate network/processing delay
                return {"status": "success", "timestamp": time.time()}

            async def load_scenario():
                tasks = []
                for i in range(total_requests):
                    tasks.append(api_request_simulator())
                    if (i + 1) % requests_per_second == 0:
                        await asyncio.sleep(interval)

                return await asyncio.gather(*tasks, return_exceptions=True)

            return load_scenario

        def create_memory_stress_test(self, memory_mb: int, duration_seconds: int):
            """Create memory stress testing scenario."""

            def memory_stress():
                # Allocate memory in chunks
                chunk_size = 1024 * 1024  # 1MB chunks
                chunks = []
                target_chunks = memory_mb

                start_time = time.time()
                while time.time() - start_time < duration_seconds:
                    if len(chunks) < target_chunks:
                        chunks.append(b"x" * chunk_size)
                    time.sleep(0.1)

                # Cleanup
                del chunks

            return memory_stress

    return LoadTestGenerator()


@pytest.fixture
def performance_regression_detector():
    """Detect performance regressions by comparing with baseline."""

    class RegressionDetector:
        def __init__(self):
            self.baselines = {}
            self.tolerance_percent = 20  # 20% tolerance for regression

        def set_baseline(self, operation_name: str, metrics: PerformanceMetrics):
            """Set baseline performance metrics for an operation."""
            self.baselines[operation_name] = {
                "execution_time": metrics.execution_time,
                "memory_usage": metrics.memory_usage,
                "cpu_usage": metrics.cpu_usage,
            }

        def check_regression(
            self, operation_name: str, current_metrics: PerformanceMetrics
        ):
            """Check if current metrics show regression compared to baseline."""
            if operation_name not in self.baselines:
                # No baseline available, set current as baseline
                self.set_baseline(operation_name, current_metrics)
                return False

            baseline = self.baselines[operation_name]
            regressions = []

            # Check execution time regression
            if current_metrics.execution_time > baseline["execution_time"] * (
                1 + self.tolerance_percent / 100
            ):
                regressions.append(
                    f"Execution time regression: {current_metrics.execution_time:.3f}s vs baseline {baseline['execution_time']:.3f}s"
                )

            # Check memory usage regression
            if current_metrics.memory_usage > baseline["memory_usage"] * (
                1 + self.tolerance_percent / 100
            ):
                regressions.append(
                    f"Memory usage regression: {current_metrics.memory_usage:.1f}MB vs baseline {baseline['memory_usage']:.1f}MB"
                )

            # Check CPU usage regression
            if current_metrics.cpu_usage > baseline["cpu_usage"] * (
                1 + self.tolerance_percent / 100
            ):
                regressions.append(
                    f"CPU usage regression: {current_metrics.cpu_usage:.1f}% vs baseline {baseline['cpu_usage']:.1f}%"
                )

            if regressions:
                raise AssertionError(
                    f"Performance regression detected in {operation_name}: {'; '.join(regressions)}"
                )

            return False

        def update_baseline(self, operation_name: str, metrics: PerformanceMetrics):
            """Update baseline with better performance metrics."""
            if operation_name not in self.baselines:
                self.set_baseline(operation_name, metrics)
                return

            baseline = self.baselines[operation_name]
            updated = False

            # Update if current metrics are better
            if metrics.execution_time < baseline["execution_time"]:
                baseline["execution_time"] = metrics.execution_time
                updated = True

            if metrics.memory_usage < baseline["memory_usage"]:
                baseline["memory_usage"] = metrics.memory_usage
                updated = True

            if metrics.cpu_usage < baseline["cpu_usage"]:
                baseline["cpu_usage"] = metrics.cpu_usage
                updated = True

            return updated

    return RegressionDetector()


@pytest.fixture
def mock_slow_operations():
    """Mock slow operations for performance testing."""

    class SlowOperationMocker:
        def __init__(self):
            self.patches = []

        def mock_slow_llm_call(self, delay_seconds: float = 2.0):
            """Mock LLM calls with artificial delay."""

            async def slow_llm_response(*args, **kwargs):
                await asyncio.sleep(delay_seconds)
                return {
                    "response": "mocked llm response",
                    "processing_time": delay_seconds,
                }

            return slow_llm_response

        def mock_slow_database_query(self, delay_seconds: float = 0.5):
            """Mock slow database operations."""

            def slow_db_query(*args, **kwargs):
                time.sleep(delay_seconds)
                return {"rows": [], "query_time": delay_seconds}

            return slow_db_query

        def mock_slow_network_request(self, delay_seconds: float = 1.0):
            """Mock slow network requests."""

            async def slow_network_call(*args, **kwargs):
                await asyncio.sleep(delay_seconds)
                return {
                    "status": "success",
                    "data": "mocked response",
                    "latency": delay_seconds,
                }

            return slow_network_call

    return SlowOperationMocker()
