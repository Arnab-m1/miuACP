"""
Enhanced Error Recovery Implementation for µACP

Provides robust error recovery mechanisms, retry strategies, and failure handling
for lightweight AI agent communications.
"""

import time
import asyncio
import random
from typing import Optional, Dict, Any, List, Callable, TypeVar, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps


class RetryStrategy(Enum):
    """Retry strategies for error recovery."""
    IMMEDIATE = "IMMEDIATE"           # Retry immediately
    LINEAR_BACKOFF = "LINEAR_BACKOFF" # Linear delay increase
    EXPONENTIAL_BACKOFF = "EXPONENTIAL_BACKOFF" # Exponential delay increase
    FIBONACCI_BACKOFF = "FIBONACCI_BACKOFF" # Fibonacci sequence delay
    RANDOM_BACKOFF = "RANDOM_BACKOFF" # Random delay with jitter


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "LOW"           # Non-critical, can retry
    MEDIUM = "MEDIUM"     # Moderate impact, limited retries
    HIGH = "HIGH"         # High impact, aggressive retries
    CRITICAL = "CRITICAL" # Critical, immediate fallback


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter_factor: float = 0.1
    exponential_base: float = 2.0
    linear_increment: float = 1.0
    fibonacci_sequence: List[int] = field(default_factory=lambda: [1, 1, 2, 3, 5, 8, 13, 21, 34, 55])


@dataclass
class ErrorContext:
    """Context information for error handling."""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    timestamp: float
    attempt_count: int
    operation_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAction:
    """A recovery action to be executed."""
    action_id: str
    action_type: str
    description: str
    execute_func: Callable
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RetryManager:
    """
    Manages retry logic and backoff strategies for error recovery.
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.retry_history: List[ErrorContext] = []
        self.successful_recoveries = 0
        self.failed_recoveries = 0
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a specific retry attempt."""
        if attempt <= 0:
            return 0.0
        
        if self.config.strategy == RetryStrategy.IMMEDIATE:
            return 0.0
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay + (attempt - 1) * self.config.linear_increment
        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        elif self.config.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            if attempt <= len(self.config.fibonacci_sequence):
                delay = self.config.base_delay * self.config.fibonacci_sequence[attempt - 1]
            else:
                delay = self.config.base_delay * self.config.fibonacci_sequence[-1]
        elif self.config.strategy == RetryStrategy.RANDOM_BACKOFF:
            delay = self.config.base_delay * (1 + random.random() * self.config.jitter_factor)
        else:
            delay = self.config.base_delay
        
        # Apply jitter for non-immediate strategies
        if self.config.strategy != RetryStrategy.IMMEDIATE:
            jitter = random.uniform(1 - self.config.jitter_factor, 1 + self.config.jitter_factor)
            delay *= jitter
        
        return min(delay, self.config.max_delay)
    
    def should_retry(self, attempt: int, error_context: ErrorContext) -> bool:
        """Determine if a retry should be attempted."""
        if attempt >= self.config.max_attempts:
            return False
        
        # Don't retry critical errors immediately
        if error_context.severity == ErrorSeverity.CRITICAL and attempt == 0:
            return False
        
        # Always retry low severity errors
        if error_context.severity == ErrorSeverity.LOW:
            return True
        
        # Medium severity: limited retries
        if error_context.severity == ErrorSeverity.MEDIUM:
            return attempt < 2
        
        # High severity: more retries
        if error_context.severity == ErrorSeverity.HIGH:
            return attempt < self.config.max_attempts
        
        return False
    
    def record_error(self, error_context: ErrorContext):
        """Record an error for analysis."""
        self.retry_history.append(error_context)
        
        # Keep only recent history
        if len(self.retry_history) > 1000:
            self.retry_history = self.retry_history[-500:]
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get retry statistics and performance metrics."""
        total_errors = len(self.retry_history)
        if total_errors == 0:
            return {
                'total_errors': 0,
                'successful_recoveries': 0,
                'failed_recoveries': 0,
                'recovery_rate': 0.0,
                'average_attempts': 0.0
            }
        
        # Calculate recovery rate
        recovery_rate = self.successful_recoveries / total_errors if total_errors > 0 else 0.0
        
        # Calculate average attempts
        total_attempts = sum(ec.attempt_count for ec in self.retry_history)
        average_attempts = total_attempts / total_errors if total_errors > 0 else 0.0
        
        # Error distribution by severity
        severity_distribution = {}
        for severity in ErrorSeverity:
            count = sum(1 for ec in self.retry_history if ec.severity == severity)
            severity_distribution[severity.value] = count
        
        return {
            'total_errors': total_errors,
            'successful_recoveries': self.successful_recoveries,
            'failed_recoveries': self.failed_recoveries,
            'recovery_rate': recovery_rate,
            'average_attempts': average_attempts,
            'severity_distribution': severity_distribution,
            'retry_config': {
                'max_attempts': self.config.max_attempts,
                'strategy': self.config.strategy.value,
                'base_delay': self.config.base_delay,
                'max_delay': self.config.max_delay
            }
        }


class ErrorRecoveryManager:
    """
    Manages error recovery actions and fallback strategies.
    """
    
    def __init__(self):
        self.recovery_actions: Dict[str, RecoveryAction] = {}
        self.action_execution_history: List[Dict[str, Any]] = []
        self.fallback_strategies: Dict[str, List[str]] = {}
        self.error_handlers: Dict[str, Callable] = {}
    
    def register_recovery_action(self, action: RecoveryAction):
        """Register a recovery action."""
        self.recovery_actions[action.action_id] = action
    
    def register_error_handler(self, error_type: str, handler: Callable):
        """Register an error handler for a specific error type."""
        self.error_handlers[error_type] = handler
    
    def register_fallback_strategy(self, operation: str, fallback_actions: List[str]):
        """Register fallback actions for an operation."""
        self.fallback_strategies[operation] = fallback_actions
    
    async def execute_recovery_action(self, action_id: str, context: Dict[str, Any] = None) -> bool:
        """Execute a specific recovery action."""
        if action_id not in self.recovery_actions:
            return False
        
        action = self.recovery_actions[action_id]
        context = context or {}
        
        try:
            # Check dependencies
            for dep_id in action.dependencies:
                if not await self.execute_recovery_action(dep_id, context):
                    print(f"Dependency {dep_id} failed for action {action_id}")
                    return False
            
            # Execute the action
            start_time = time.time()
            result = await action.execute_func(context) if asyncio.iscoroutinefunction(action.execute_func) else action.execute_func(context)
            execution_time = time.time() - start_time
            
            # Record execution
            execution_record = {
                'action_id': action_id,
                'timestamp': time.time(),
                'success': bool(result),
                'execution_time': execution_time,
                'context': context
            }
            self.action_execution_history.append(execution_record)
            
            return bool(result)
            
        except Exception as e:
            print(f"Error executing recovery action {action_id}: {e}")
            
            # Record failed execution
            execution_record = {
                'action_id': action_id,
                'timestamp': time.time(),
                'success': False,
                'execution_time': 0.0,
                'context': context,
                'error': str(e)
            }
            self.action_execution_history.append(execution_record)
            
            return False
    
    async def execute_fallback_strategy(self, operation: str, context: Dict[str, Any] = None) -> bool:
        """Execute fallback strategy for an operation."""
        if operation not in self.fallback_strategies:
            return False
        
        fallback_actions = self.fallback_strategies[operation]
        context = context or {}
        
        for action_id in fallback_actions:
            if await self.execute_recovery_action(action_id, context):
                return True
        
        return False
    
    def handle_error(self, error: Exception, operation: str, context: Dict[str, Any] = None) -> bool:
        """Handle an error using registered error handlers."""
        error_type = type(error).__name__
        context = context or {}
        
        if error_type in self.error_handlers:
            try:
                handler = self.error_handlers[error_type]
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(error, operation, context))
                else:
                    handler(error, operation, context)
                return True
            except Exception as e:
                print(f"Error in error handler for {error_type}: {e}")
        
        return False
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery action statistics."""
        total_executions = len(self.action_execution_history)
        successful_executions = sum(1 for record in self.action_execution_history if record['success'])
        
        return {
            'total_actions': len(self.recovery_actions),
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': successful_executions / total_executions if total_executions > 0 else 0.0,
            'registered_actions': list(self.recovery_actions.keys()),
            'fallback_strategies': list(self.fallback_strategies.keys()),
            'error_handlers': list(self.error_handlers.keys())
        }


def retry_on_error(retry_config: Optional[RetryConfig] = None, 
                   error_types: Optional[List[type]] = None,
                   operation_name: Optional[str] = None):
    """
    Decorator for automatic retry on errors.
    
    Usage:
        @retry_on_error(RetryConfig(max_attempts=3))
        async def unreliable_function():
            # Function that might fail
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            config = retry_config or RetryConfig()
            retry_manager = RetryManager(config)
            
            last_error = None
            for attempt in range(config.max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record successful recovery if this was a retry
                    if attempt > 0:
                        retry_manager.successful_recoveries += 1
                    
                    return result
                    
                except Exception as e:
                    last_error = e
                    
                    # Check if we should retry
                    if not retry_manager.should_retry(attempt, ErrorContext(
                        error_type=type(e).__name__,
                        error_message=str(e),
                        severity=ErrorSeverity.MEDIUM,
                        timestamp=time.time(),
                        attempt_count=attempt,
                        operation_name=operation_name or func.__name__
                    )):
                        break
                    
                    # Calculate delay and wait
                    delay = retry_manager.calculate_delay(attempt)
                    if delay > 0:
                        await asyncio.sleep(delay)
            
            # All retries exhausted
            retry_manager.failed_recoveries += 1
            raise last_error
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            config = retry_config or RetryConfig()
            retry_manager = RetryManager(config)
            
            last_error = None
            for attempt in range(config.max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # Record successful recovery if this was a retry
                    if attempt > 0:
                        retry_manager.successful_recoveries += 1
                    
                    return result
                    
                except Exception as e:
                    last_error = e
                    
                    # Check if we should retry
                    if not retry_manager.should_retry(attempt, ErrorContext(
                        error_type=type(e).__name__,
                        error_message=str(e),
                        severity=ErrorSeverity.MEDIUM,
                        timestamp=time.time(),
                        attempt_count=attempt,
                        operation_name=operation_name or func.__name__
                    )):
                        break
                    
                    # Calculate delay and wait
                    delay = retry_manager.calculate_delay(attempt)
                    if delay > 0:
                        time.sleep(delay)
            
            # All retries exhausted
            retry_manager.failed_recoveries += 1
            raise last_error
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RobustnessManager:
    """
    Main manager for all robustness features.
    
    Integrates circuit breakers, adaptive timeouts, resource pooling,
    and error recovery into a unified system.
    """
    
    def __init__(self):
        self.retry_manager = RetryManager()
        self.error_recovery_manager = ErrorRecoveryManager()
        self._running = False
    
    async def start(self):
        """Start the robustness manager."""
        self._running = True
    
    async def stop(self):
        """Stop the robustness manager."""
        self._running = False
    
    def get_robustness_statistics(self) -> Dict[str, Any]:
        """Get comprehensive robustness statistics."""
        return {
            'retry_statistics': self.retry_manager.get_retry_statistics(),
            'recovery_statistics': self.error_recovery_manager.get_recovery_statistics()
        }
