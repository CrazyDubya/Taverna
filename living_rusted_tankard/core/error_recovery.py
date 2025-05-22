"""
Comprehensive Error Recovery System for The Living Rusted Tankard.

This module provides robust error handling and graceful degradation:
- Fallback response generation for LLM failures
- Service health monitoring and automatic recovery
- Error classification and appropriate responses
- System resilience during external service outages

Integrates with:
- async_llm_pipeline.py (LLM processing)
- enhanced_llm_game_master.py (LLM calls)
- api.py (HTTP endpoints)
- memory.py (error context tracking)
"""

import logging
import time
import random
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import traceback

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = 1          # Minor issues, continue normally
    MEDIUM = 2       # Notable issues, use fallbacks
    HIGH = 3         # Significant issues, limited functionality
    CRITICAL = 4     # System issues, emergency responses only


class ErrorCategory(Enum):
    """Categories of errors for appropriate handling."""
    NETWORK = "network"           # Connection issues
    LLM_SERVICE = "llm_service"   # LLM API problems
    PARSING = "parsing"           # Response parsing issues
    GAME_STATE = "game_state"     # Game state corruption
    MEMORY = "memory"             # Memory system issues
    AUTHENTICATION = "auth"       # Auth/session issues
    UNKNOWN = "unknown"           # Uncategorized errors


@dataclass
class ErrorContext:
    """Context information for error handling."""
    error_type: str
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: float
    session_id: Optional[str] = None
    user_input: Optional[str] = None
    game_state_snapshot: Optional[Dict] = None
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False


class ContextualFallbackGenerator:
    """Generate contextual fallback responses based on game state and situation."""
    
    def __init__(self):
        self.response_templates = {
            ErrorCategory.NETWORK: {
                ErrorSeverity.LOW: [
                    "There's a brief moment of static in the air, but the conversation continues.",
                    "A passing cloud seems to momentarily affect the tavern's atmosphere.",
                    "The tavern's energy shifts slightly before returning to normal."
                ],
                ErrorSeverity.MEDIUM: [
                    "The mystical forces that govern the tavern seem temporarily disrupted.",
                    "Magic in the area feels unstable for a moment, affecting communication.",
                    "The tavern's ancient enchantments flicker briefly before stabilizing."
                ],
                ErrorSeverity.HIGH: [
                    "A powerful magical disturbance affects the entire tavern temporarily.",
                    "The connection to the tavern's mystical essence is temporarily severed.",
                    "All communication in the tavern becomes muffled and unclear."
                ]
            },
            ErrorCategory.LLM_SERVICE: {
                ErrorSeverity.LOW: [
                    "The storyteller takes a moment to collect their thoughts.",
                    "There's a contemplative pause as the situation unfolds.",
                    "The tavern's atmosphere grows thoughtful and reflective."
                ],
                ErrorSeverity.MEDIUM: [
                    "The tavern's resident storyteller seems lost in thought.",
                    "A mystical silence falls over the tavern as forces realign.",
                    "The narrative threads seem tangled, requiring careful consideration."
                ],
                ErrorSeverity.HIGH: [
                    "The tavern's mystical narrator has temporarily withdrawn.",
                    "Ancient forces that guide the tavern's stories are consulting the fates.",
                    "The storytelling spirits are gathering their power for a grand return."
                ]
            },
            ErrorCategory.GAME_STATE: {
                ErrorSeverity.MEDIUM: [
                    "Reality shifts slightly as the tavern's magic readjusts itself.",
                    "The fabric of the tavern's existence ripples and then settles.",
                    "Something feels different, but the tavern's warmth remains constant."
                ],
                ErrorSeverity.HIGH: [
                    "The tavern experiences a temporal hiccup, but quickly stabilizes.",
                    "Magic surges through the tavern, resetting some of its properties.",
                    "The tavern's enchantments are reweaving themselves."
                ]
            }
        }
        
        # Time-based contextual responses
        self.time_contexts = {
            "morning": "The morning light filters through the windows as",
            "midday": "In the bright midday atmosphere,",
            "afternoon": "As the afternoon settles over the tavern,",
            "evening": "In the warm evening glow,",
            "night": "Under the gentle night lighting,",
            "deep_night": "In the quiet hours of deep night,"
        }
        
        # NPC-aware responses
        self.npc_contexts = {
            "barkeep": "Gene the bartender continues polishing mugs, maintaining the tavern's rhythm.",
            "patron": "The other patrons continue their conversations, keeping the tavern lively.",
            "merchant": "Merchants in the corner continue discussing their wares.",
            "bard": "A bard in the corner strums a gentle melody to fill the silence.",
            "guard": "The tavern guard maintains watchful attention to the surroundings."
        }
    
    def generate_fallback(
        self, 
        error_context: ErrorContext,
        game_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate an appropriate fallback response based on error and game context."""
        
        # Get base response from templates
        category_templates = self.response_templates.get(
            error_context.category, 
            self.response_templates[ErrorCategory.NETWORK]
        )
        severity_responses = category_templates.get(
            error_context.severity,
            category_templates[ErrorSeverity.MEDIUM]
        )
        
        base_response = random.choice(severity_responses)
        
        # Add contextual elements
        contextual_response = self._add_context(base_response, game_context)
        
        # Add recovery guidance for higher severity errors
        if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            recovery_guidance = self._get_recovery_guidance(error_context)
            if recovery_guidance:
                contextual_response += f" {recovery_guidance}"
        
        return contextual_response
    
    def _add_context(self, base_response: str, game_context: Optional[Dict[str, Any]]) -> str:
        """Add game context to the base response."""
        if not game_context:
            return base_response
        
        # Add time context
        if "current_time" in game_context:
            time_str = game_context["current_time"].lower()
            for time_key, time_prefix in self.time_contexts.items():
                if time_key in time_str:
                    return f"{time_prefix} {base_response.lower()}"
        
        # Add NPC context
        if "present_npcs" in game_context and game_context["present_npcs"]:
            npc_count = len(game_context["present_npcs"])
            if npc_count > 0:
                npc_addition = random.choice(list(self.npc_contexts.values()))
                return f"{base_response} {npc_addition}"
        
        return base_response
    
    def _get_recovery_guidance(self, error_context: ErrorContext) -> Optional[str]:
        """Get recovery guidance for severe errors."""
        if error_context.category == ErrorCategory.NETWORK:
            return "The tavern will restore full functionality once the connection stabilizes."
        elif error_context.category == ErrorCategory.LLM_SERVICE:
            return "Normal storytelling will resume shortly."
        elif error_context.category == ErrorCategory.GAME_STATE:
            return "The tavern's reality is reconstructing itself and will be fully stable soon."
        
        return None


class ErrorClassifier:
    """Classify errors to determine appropriate handling strategy."""
    
    def __init__(self):
        self.classification_rules = {
            # Network-related errors
            "connection": (ErrorCategory.NETWORK, ErrorSeverity.HIGH),
            "timeout": (ErrorCategory.NETWORK, ErrorSeverity.MEDIUM),
            "refused": (ErrorCategory.NETWORK, ErrorSeverity.HIGH),
            "unreachable": (ErrorCategory.NETWORK, ErrorSeverity.CRITICAL),
            
            # LLM service errors
            "ollama": (ErrorCategory.LLM_SERVICE, ErrorSeverity.HIGH),
            "model": (ErrorCategory.LLM_SERVICE, ErrorSeverity.HIGH),
            "response": (ErrorCategory.LLM_SERVICE, ErrorSeverity.MEDIUM),
            "parsing": (ErrorCategory.PARSING, ErrorSeverity.MEDIUM),
            
            # Game state errors
            "game_state": (ErrorCategory.GAME_STATE, ErrorSeverity.HIGH),
            "serialization": (ErrorCategory.GAME_STATE, ErrorSeverity.MEDIUM),
            "snapshot": (ErrorCategory.GAME_STATE, ErrorSeverity.MEDIUM),
            
            # Memory errors
            "memory": (ErrorCategory.MEMORY, ErrorSeverity.LOW),
            "cache": (ErrorCategory.MEMORY, ErrorSeverity.LOW),
            
            # Authentication errors
            "session": (ErrorCategory.AUTHENTICATION, ErrorSeverity.MEDIUM),
            "unauthorized": (ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
        }
    
    def classify_error(self, error: Exception, context: Optional[str] = None) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Classify an error and determine its severity."""
        error_message = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Check error message against classification rules
        for keyword, (category, severity) in self.classification_rules.items():
            if keyword in error_message or keyword in error_type:
                return category, severity
        
        # Check context if provided
        if context:
            context_lower = context.lower()
            for keyword, (category, severity) in self.classification_rules.items():
                if keyword in context_lower:
                    return category, severity
        
        # Default classification
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM


class SystemHealthMonitor:
    """Monitor system health and trigger recovery actions."""
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.health_thresholds = {
            "error_rate_1min": 0.1,     # Max 10% error rate in 1 minute
            "error_rate_5min": 0.05,    # Max 5% error rate in 5 minutes
            "critical_errors_1min": 3,  # Max 3 critical errors in 1 minute
            "consecutive_failures": 5    # Max 5 consecutive failures
        }
        self.consecutive_failures = 0
        self.last_success_time = time.time()
    
    def record_error(self, error_context: ErrorContext) -> None:
        """Record an error for health monitoring."""
        self.error_history.append(error_context)
        
        # Update consecutive failure count
        if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.consecutive_failures += 1
        
        # Clean old error history (keep last hour)
        cutoff_time = time.time() - 3600  # 1 hour ago
        self.error_history = [
            err for err in self.error_history 
            if err.timestamp > cutoff_time
        ]
    
    def record_success(self) -> None:
        """Record a successful operation."""
        self.consecutive_failures = 0
        self.last_success_time = time.time()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status."""
        current_time = time.time()
        
        # Calculate error rates
        errors_1min = [
            err for err in self.error_history 
            if current_time - err.timestamp <= 60
        ]
        errors_5min = [
            err for err in self.error_history 
            if current_time - err.timestamp <= 300
        ]
        
        # Count critical errors
        critical_errors_1min = len([
            err for err in errors_1min 
            if err.severity == ErrorSeverity.CRITICAL
        ])
        
        # Calculate health score (0-1, where 1 is healthy)
        health_score = 1.0
        
        # Penalize for high error rates
        if len(errors_1min) > 6:  # More than 6 errors per minute
            health_score -= 0.3
        if len(errors_5min) > 15:  # More than 15 errors per 5 minutes
            health_score -= 0.2
        
        # Penalize for critical errors
        health_score -= min(0.3, critical_errors_1min * 0.1)
        
        # Penalize for consecutive failures
        health_score -= min(0.4, self.consecutive_failures * 0.08)
        
        health_score = max(0.0, health_score)
        
        return {
            "health_score": health_score,
            "is_healthy": health_score > 0.7,
            "consecutive_failures": self.consecutive_failures,
            "errors_last_1min": len(errors_1min),
            "errors_last_5min": len(errors_5min),
            "critical_errors_1min": critical_errors_1min,
            "last_success_seconds_ago": current_time - self.last_success_time,
            "total_errors_recorded": len(self.error_history)
        }


class ErrorRecoverySystem:
    """Comprehensive error recovery and resilience system."""
    
    def __init__(self):
        self.classifier = ErrorClassifier()
        self.fallback_generator = ContextualFallbackGenerator()
        self.health_monitor = SystemHealthMonitor()
        
        # Recovery strategies
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {
            ErrorCategory.NETWORK: self._recover_network_error,
            ErrorCategory.LLM_SERVICE: self._recover_llm_error,
            ErrorCategory.GAME_STATE: self._recover_game_state_error,
            ErrorCategory.MEMORY: self._recover_memory_error,
            ErrorCategory.PARSING: self._recover_parsing_error,
        }
    
    def handle_error(
        self,
        error: Exception,
        session_id: Optional[str] = None,
        user_input: Optional[str] = None,
        game_context: Optional[Dict[str, Any]] = None,
        operation_context: Optional[str] = None
    ) -> Tuple[str, bool]:
        """Handle an error and return appropriate response and recovery status.
        
        Returns:
            Tuple of (response_text, recovery_successful)
        """
        
        # Classify the error
        category, severity = self.classifier.classify_error(error, operation_context)
        
        # Create error context
        error_context = ErrorContext(
            error_type=type(error).__name__,
            severity=severity,
            category=category,
            timestamp=time.time(),
            session_id=session_id,
            user_input=user_input,
            game_state_snapshot=game_context,
            stack_trace=traceback.format_exc() if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
        )
        
        # Record error for health monitoring
        self.health_monitor.record_error(error_context)
        
        # Attempt recovery
        recovery_successful = False
        if category in self.recovery_strategies:
            try:
                recovery_successful = self.recovery_strategies[category](error_context)
                error_context.recovery_attempted = True
                error_context.recovery_successful = recovery_successful
            except Exception as recovery_error:
                logger.error(f"Recovery strategy failed: {recovery_error}")
        
        # Generate fallback response
        fallback_response = self.fallback_generator.generate_fallback(
            error_context, 
            game_context
        )
        
        # Log error with appropriate level
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error in session {session_id}: {error}")
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error in session {session_id}: {error}")
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error in session {session_id}: {error}")
        else:
            logger.debug(f"Low severity error in session {session_id}: {error}")
        
        return fallback_response, recovery_successful
    
    def _recover_network_error(self, error_context: ErrorContext) -> bool:
        """Attempt recovery from network errors."""
        # For network errors, we can't do much except wait and retry
        # But we can provide guidance for future attempts
        logger.info("Network error detected, system will auto-retry on next request")
        return False  # Can't immediately recover, but not a permanent failure
    
    def _recover_llm_error(self, error_context: ErrorContext) -> bool:
        """Attempt recovery from LLM service errors."""
        # Could implement LLM service restart logic here
        # For now, just log and allow system to retry
        logger.info("LLM service error detected, switching to fallback mode")
        return False
    
    def _recover_game_state_error(self, error_context: ErrorContext) -> bool:
        """Attempt recovery from game state errors."""
        # Could implement game state restoration logic here
        logger.warning("Game state error detected, may require state restoration")
        return False
    
    def _recover_memory_error(self, error_context: ErrorContext) -> bool:
        """Attempt recovery from memory system errors."""
        # Memory errors are usually not critical to gameplay
        logger.info("Memory system error detected, continuing with reduced memory functionality")
        return True  # Memory errors don't stop the game
    
    def _recover_parsing_error(self, error_context: ErrorContext) -> bool:
        """Attempt recovery from parsing errors."""
        # Parsing errors usually just affect one response
        logger.info("Response parsing error detected, using fallback response")
        return True  # Parsing errors are recoverable
    
    def record_successful_operation(self) -> None:
        """Record a successful operation for health monitoring."""
        self.health_monitor.record_success()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status."""
        return self.health_monitor.get_system_health()


# Global error recovery system instance
_error_recovery: Optional[ErrorRecoverySystem] = None


def get_error_recovery_system() -> ErrorRecoverySystem:
    """Get the global error recovery system instance."""
    global _error_recovery
    if _error_recovery is None:
        _error_recovery = ErrorRecoverySystem()
    return _error_recovery


def handle_llm_error(
    error: Exception,
    session_id: Optional[str] = None,
    user_input: Optional[str] = None,
    game_context: Optional[Dict[str, Any]] = None
) -> Tuple[str, Optional[str], List[Dict[str, Any]]]:
    """Convenience function to handle LLM errors and return standard response format."""
    recovery_system = get_error_recovery_system()
    
    fallback_response, recovery_successful = recovery_system.handle_error(
        error, session_id, user_input, game_context, "LLM processing"
    )
    
    # Return in the standard LLM response format
    return fallback_response, None, []


def record_successful_llm_operation() -> None:
    """Record a successful LLM operation."""
    recovery_system = get_error_recovery_system()
    recovery_system.record_successful_operation()


if __name__ == "__main__":
    # Test the error recovery system
    print("=== Error Recovery System Test ===")
    
    recovery_system = ErrorRecoverySystem()
    
    # Test error classification
    test_errors = [
        ConnectionError("Connection refused"),
        TimeoutError("Request timed out"),
        ValueError("Invalid model response"),
        Exception("Unknown error")
    ]
    
    for error in test_errors:
        category, severity = recovery_system.classifier.classify_error(error)
        print(f"Error: {error} -> Category: {category.value}, Severity: {severity.name}")
    
    # Test error handling
    fallback, recovered = recovery_system.handle_error(
        ConnectionError("Connection refused"),
        session_id="test-session",
        user_input="look around",
        game_context={"current_time": "Evening Bell", "present_npcs": ["Gene"]}
    )
    
    print(f"Fallback response: {fallback}")
    print(f"Recovery successful: {recovered}")
    
    # Test system health
    health = recovery_system.get_system_health()
    print(f"System health: {health}")
    
    print("✅ Error recovery system test completed")