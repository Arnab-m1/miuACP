"""
Circuit Breaker Pattern Implementation for µACP

Provides robust failure handling and recovery mechanisms for lightweight AI agent communications.
"""

import time
import asyncio
from enum import Enum
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 3
    monitoring_window: float = 300.0  # 5 minutes
    enable_metrics: bool = True


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_opens: int = 0
    circuit_closes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    current_failure_count: int = 0
    current_success_count: int = 0


class CircuitBreaker:
    """
    Circuit Breaker implementation for robust failure handling.
    
    Implements the circuit breaker pattern to prevent cascading failures
    and provide automatic recovery mechanisms.
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()
        self.metrics = CircuitBreakerMetrics()
        
        # Background tasks
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the circuit breaker monitoring."""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """Stop the circuit breaker monitoring."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    def is_available(self) -> bool:
        """Check if the circuit is available for requests."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (time.time() - self.last_state_change) > self.config.recovery_timeout:
                self._transition_to_half_open()
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record a successful operation."""
        self.success_count += 1
        self.failure_count = 0
        self.last_success_time = time.time()
        
        # Update metrics
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        self.metrics.current_success_count += 1
        self.metrics.current_failure_count = 0
        
        # Check if we should close the circuit
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
    
    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.success_count = 0
        self.last_failure_time = time.time()
        
        # Update metrics
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.metrics.current_failure_count += 1
        self.metrics.current_success_count = 0
        
        # Check if we should open the circuit
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state opens the circuit
            self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition circuit to OPEN state."""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            self.metrics.circuit_opens += 1
    
    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state."""
        if self.state != CircuitState.HALF_OPEN:
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = time.time()
            self.failure_count = 0
            self.success_count = 0
    
    def _transition_to_closed(self):
        """Transition circuit to CLOSED state."""
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()
            self.failure_count = 0
            self.success_count = 0
            self.metrics.circuit_closes += 1
    
    async def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                await asyncio.sleep(10.0)  # Check every 10 seconds
                self._cleanup_old_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in circuit breaker monitor: {e}")
    
    def _cleanup_old_metrics(self):
        """Clean up old metrics outside the monitoring window."""
        now = time.time()
        window_start = now - self.config.monitoring_window
        
        # Reset counters if outside monitoring window
        if (self.last_failure_time and self.last_failure_time < window_start):
            self.metrics.current_failure_count = 0
        
        if (self.last_success_time and self.last_success_time < window_start):
            self.metrics.current_success_count = 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status."""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time,
            'last_state_change': self.last_state_change,
            'is_available': self.is_available(),
            'metrics': {
                'total_requests': self.metrics.total_requests,
                'successful_requests': self.metrics.successful_requests,
                'failed_requests': self.metrics.failed_requests,
                'circuit_opens': self.metrics.circuit_opens,
                'circuit_closes': self.metrics.circuit_closes,
                'current_failure_count': self.metrics.current_failure_count,
                'current_success_count': self.metrics.current_success_count
            }
        }
    
    def reset(self):
        """Reset the circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different destinations/services.
    """
    
    def __init__(self, default_config: Optional[CircuitBreakerConfig] = None):
        self.default_config = default_config or CircuitBreakerConfig()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._running = False
    
    async def start(self):
        """Start all circuit breakers."""
        self._running = True
        for cb in self.circuit_breakers.values():
            await cb.start()
    
    async def stop(self):
        """Stop all circuit breakers."""
        self._running = False
        for cb in self.circuit_breakers.values():
            await cb.stop()
    
    def get_circuit_breaker(self, destination: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a destination."""
        if destination not in self.circuit_breakers:
            self.circuit_breakers[destination] = CircuitBreaker(self.default_config)
            if self._running:
                asyncio.create_task(self.circuit_breakers[destination].start())
        
        return self.circuit_breakers[destination]
    
    def is_destination_available(self, destination: str) -> bool:
        """Check if a destination is available."""
        cb = self.get_circuit_breaker(destination)
        return cb.is_available()
    
    def record_success(self, destination: str):
        """Record success for a destination."""
        cb = self.get_circuit_breaker(destination)
        cb.record_success()
    
    def record_failure(self, destination: str):
        """Record failure for a destination."""
        cb = self.get_circuit_breaker(destination)
        cb.record_failure()
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        return {
            dest: cb.get_status() 
            for dest, cb in self.circuit_breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers."""
        for cb in self.circuit_breakers.values():
            cb.reset()
