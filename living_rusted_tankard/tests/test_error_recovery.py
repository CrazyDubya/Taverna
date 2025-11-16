"""Test error recovery mechanisms."""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from tests.fixtures import clean_game_state, mock_llm_service
from tests.utils.assertion_helpers import assert_performance_within_limits

from core.error_recovery import (
    ErrorRecoveryManager,
    ErrorSeverity,
    RecoveryStrategy,
    GameStateCorruptionError,
    LLMConnectionError,
    PerformanceError,
)


class TestErrorRecoveryManager:
    """Test the error recovery manager."""

    def test_error_recovery_manager_initialization(self):
        """Test error recovery manager initializes correctly."""
        recovery_manager = ErrorRecoveryManager()

        assert recovery_manager is not None
        assert hasattr(recovery_manager, "error_history")
        assert hasattr(recovery_manager, "recovery_strategies")
        assert len(recovery_manager.error_history) == 0

    def test_error_severity_classification(self):
        """Test error severity is classified correctly."""
        recovery_manager = ErrorRecoveryManager()

        # Test critical error
        critical_error = GameStateCorruptionError("State corrupted")
        severity = recovery_manager.classify_error(critical_error)
        assert severity == ErrorSeverity.CRITICAL

        # Test warning error
        warning_error = PerformanceError("Slow operation")
        severity = recovery_manager.classify_error(warning_error)
        assert severity == ErrorSeverity.WARNING

        # Test recoverable error
        recoverable_error = LLMConnectionError("Connection timeout")
        severity = recovery_manager.classify_error(recoverable_error)
        assert severity == ErrorSeverity.RECOVERABLE

    def test_recovery_strategy_selection(self):
        """Test appropriate recovery strategy is selected."""
        recovery_manager = ErrorRecoveryManager()

        # Critical error should trigger restore strategy
        critical_error = GameStateCorruptionError("State corrupted")
        strategy = recovery_manager.select_recovery_strategy(critical_error)
        assert strategy == RecoveryStrategy.RESTORE_FROM_BACKUP

        # LLM error should trigger fallback strategy
        llm_error = LLMConnectionError("Connection failed")
        strategy = recovery_manager.select_recovery_strategy(llm_error)
        assert strategy == RecoveryStrategy.USE_FALLBACK

        # Performance error should trigger optimization
        perf_error = PerformanceError("Memory usage high")
        strategy = recovery_manager.select_recovery_strategy(perf_error)
        assert strategy == RecoveryStrategy.OPTIMIZE_PERFORMANCE

    @pytest.mark.asyncio
    async def test_error_recovery_execution(self, clean_game_state):
        """Test error recovery is executed correctly."""
        recovery_manager = ErrorRecoveryManager()

        # Mock recovery actions
        recovery_manager.restore_from_backup = Mock(return_value=True)
        recovery_manager.use_fallback_response = Mock(return_value="Fallback response")
        recovery_manager.optimize_performance = Mock(return_value=True)

        # Test critical error recovery
        critical_error = GameStateCorruptionError("State corrupted")
        result = await recovery_manager.recover_from_error(
            critical_error, clean_game_state
        )

        assert result.success is True
        assert result.strategy == RecoveryStrategy.RESTORE_FROM_BACKUP
        recovery_manager.restore_from_backup.assert_called_once()

    def test_error_history_tracking(self):
        """Test error history is tracked correctly."""
        recovery_manager = ErrorRecoveryManager()

        # Add some errors
        error1 = LLMConnectionError("First error")
        error2 = PerformanceError("Second error")

        recovery_manager.log_error(error1)
        recovery_manager.log_error(error2)

        assert len(recovery_manager.error_history) == 2
        assert recovery_manager.error_history[0].error_type == "LLMConnectionError"
        assert recovery_manager.error_history[1].error_type == "PerformanceError"

    def test_error_pattern_detection(self):
        """Test detection of error patterns."""
        recovery_manager = ErrorRecoveryManager()

        # Add repeated errors
        for i in range(5):
            error = LLMConnectionError(f"Connection error {i}")
            recovery_manager.log_error(error)

        # Check pattern detection
        pattern = recovery_manager.detect_error_pattern()
        assert pattern is not None
        assert pattern.error_type == "LLMConnectionError"
        assert pattern.frequency >= 5
        assert pattern.severity == ErrorSeverity.RECOVERABLE

    def test_graceful_degradation(self, clean_game_state):
        """Test graceful degradation during errors."""
        recovery_manager = ErrorRecoveryManager()

        # Simulate system overload
        with patch("core.error_recovery.system_resources") as mock_resources:
            mock_resources.cpu_usage = 95.0
            mock_resources.memory_usage = 90.0

            degradation_plan = recovery_manager.create_degradation_plan(
                clean_game_state
            )

            assert degradation_plan is not None
            assert "disable_non_essential" in degradation_plan.actions
            assert "reduce_llm_calls" in degradation_plan.actions
            assert degradation_plan.severity == ErrorSeverity.WARNING


class TestSpecificErrorTypes:
    """Test specific error type handling."""

    def test_game_state_corruption_error(self):
        """Test game state corruption error handling."""
        error = GameStateCorruptionError(
            message="Player state invalid",
            corrupted_fields=["player.gold", "player.inventory"],
            recovery_hint="restore_from_backup",
        )

        assert error.message == "Player state invalid"
        assert "player.gold" in error.corrupted_fields
        assert error.recovery_hint == "restore_from_backup"
        assert error.severity == ErrorSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_llm_connection_error(self):
        """Test LLM connection error handling."""
        error = LLMConnectionError(
            message="Ollama connection timeout",
            retry_count=3,
            last_successful_call=1234567890,
        )

        assert error.message == "Ollama connection timeout"
        assert error.retry_count == 3
        assert error.can_retry() is True
        assert error.severity == ErrorSeverity.RECOVERABLE

    def test_performance_error(self):
        """Test performance error handling."""
        error = PerformanceError(
            message="Turn processing too slow",
            metric_name="turn_processing_time",
            current_value=150.0,
            threshold=100.0,
        )

        assert error.message == "Turn processing too slow"
        assert error.metric_name == "turn_processing_time"
        assert error.current_value == 150.0
        assert error.threshold == 100.0
        assert error.severity == ErrorSeverity.WARNING


class TestRecoveryStrategies:
    """Test specific recovery strategies."""

    @pytest.mark.asyncio
    async def test_restore_from_backup_strategy(self, clean_game_state):
        """Test restore from backup strategy."""
        recovery_manager = ErrorRecoveryManager()

        # Mock backup system
        with patch("core.error_recovery.BackupManager") as mock_backup:
            mock_backup.get_latest_backup.return_value = clean_game_state
            mock_backup.restore_backup.return_value = True

            result = await recovery_manager.restore_from_backup(clean_game_state)

            assert result is True
            mock_backup.get_latest_backup.assert_called_once()
            mock_backup.restore_backup.assert_called_once()

    @pytest.mark.asyncio
    async def test_use_fallback_strategy(self):
        """Test use fallback strategy."""
        recovery_manager = ErrorRecoveryManager()

        # Test LLM fallback
        fallback_response = recovery_manager.use_fallback_response(
            context="player_action", action="look around"
        )

        assert fallback_response is not None
        assert isinstance(fallback_response, str)
        assert len(fallback_response) > 0

    def test_optimize_performance_strategy(self, clean_game_state):
        """Test optimize performance strategy."""
        recovery_manager = ErrorRecoveryManager()

        # Mock performance optimization
        with patch("core.error_recovery.PerformanceOptimizer") as mock_optimizer:
            mock_optimizer.clear_caches.return_value = True
            mock_optimizer.reduce_memory_usage.return_value = True

            result = recovery_manager.optimize_performance(clean_game_state)

            assert result is True
            mock_optimizer.clear_caches.assert_called_once()


class TestErrorRecoveryIntegration:
    """Test error recovery integration with game systems."""

    @pytest.mark.asyncio
    async def test_game_state_error_integration(self, clean_game_state):
        """Test error recovery integrates with game state."""
        recovery_manager = ErrorRecoveryManager()

        # Simulate game state error
        with patch.object(clean_game_state, "validate") as mock_validate:
            mock_validate.side_effect = GameStateCorruptionError("Invalid state")

            # Recovery should be triggered
            result = await recovery_manager.handle_game_state_error(clean_game_state)

            assert result.success is True
            assert result.strategy == RecoveryStrategy.RESTORE_FROM_BACKUP

    @pytest.mark.asyncio
    async def test_llm_error_integration(self, mock_llm_service):
        """Test error recovery integrates with LLM system."""
        recovery_manager = ErrorRecoveryManager()

        # Simulate LLM failure
        mock_llm_service.set_failure_mode(True, "Connection timeout")

        # Recovery should provide fallback
        result = await recovery_manager.handle_llm_error(
            context="narration", original_prompt="Describe the tavern"
        )

        assert result.success is True
        assert result.fallback_response is not None
        assert len(result.fallback_response) > 0

    def test_performance_error_integration(self, clean_game_state):
        """Test error recovery integrates with performance monitoring."""
        recovery_manager = ErrorRecoveryManager()

        # Simulate performance issue
        with patch("core.error_recovery.get_system_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "cpu_usage": 95.0,
                "memory_usage": 85.0,
                "turn_processing_time": 200.0,
            }

            # Recovery should optimize performance
            result = recovery_manager.handle_performance_error(clean_game_state)

            assert result.success is True
            assert result.optimization_applied is True


class TestErrorRecoveryConfiguration:
    """Test error recovery configuration and settings."""

    def test_recovery_thresholds(self):
        """Test recovery thresholds are configurable."""
        recovery_manager = ErrorRecoveryManager()

        # Test default thresholds
        assert recovery_manager.cpu_threshold == 90.0
        assert recovery_manager.memory_threshold == 80.0
        assert recovery_manager.response_time_threshold == 100.0

        # Test threshold modification
        recovery_manager.set_thresholds(
            cpu_threshold=95.0, memory_threshold=85.0, response_time_threshold=150.0
        )

        assert recovery_manager.cpu_threshold == 95.0
        assert recovery_manager.memory_threshold == 85.0
        assert recovery_manager.response_time_threshold == 150.0

    def test_recovery_strategy_configuration(self):
        """Test recovery strategies can be configured."""
        recovery_manager = ErrorRecoveryManager()

        # Test strategy registration
        custom_strategy = Mock()
        recovery_manager.register_strategy("custom_strategy", custom_strategy)

        assert "custom_strategy" in recovery_manager.recovery_strategies
        assert (
            recovery_manager.recovery_strategies["custom_strategy"] == custom_strategy
        )

    def test_error_recovery_disabled(self, clean_game_state):
        """Test error recovery can be disabled."""
        recovery_manager = ErrorRecoveryManager(enabled=False)

        # Errors should not trigger recovery
        error = LLMConnectionError("Test error")
        result = recovery_manager.handle_error(error, clean_game_state)

        assert result.recovery_attempted is False
        assert result.original_error == error
