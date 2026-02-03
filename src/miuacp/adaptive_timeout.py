"""
Adaptive Timeout Implementation for µACP

Provides intelligent timeout management that adapts to network conditions
and success rates for lightweight AI agent communications.
"""

import time
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TimeoutStrategy(Enum):
    """Timeout adjustment strategies."""
    LINEAR = "LINEAR"           # Linear adjustment
    EXPONENTIAL = "EXPONENTIAL" # Exponential backoff
    ADAPTIVE = "ADAPTIVE"       # Adaptive based on success rate
    HYBRID = "HYBRID"          # Combination of strategies


@dataclass
class TimeoutConfig:
    """Configuration for adaptive timeout."""
    base_timeout: float = 30.0
    min_timeout: float = 1.0
    max_timeout: float = 300.0
    success_rate_threshold: float = 0.8
    failure_rate_threshold: float = 0.2
    adjustment_factor: float = 1.5
    decay_factor: float = 0.9
    history_size: int = 100
    strategy: TimeoutStrategy = TimeoutStrategy.HYBRID


@dataclass
class TimeoutHistory:
    """History of timeout operations for analysis."""
    timestamp: float
    timeout_value: float
    success: bool
    response_time: float
    network_latency: Optional[float] = None


class AdaptiveTimeout:
    """
    Adaptive timeout management that adjusts timeouts based on:
    - Success/failure rates
    - Network conditions
    - Response times
    - Historical performance
    """
    
    def __init__(self, config: Optional[TimeoutConfig] = None):
        self.config = config or TimeoutConfig()
        self.current_timeout = self.config.base_timeout
        self.history: List[TimeoutHistory] = []
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = time.time()
        self.adjustment_interval = 60.0  # Adjust every minute
        
        # Background tasks
        self._running = False
        self._adjustment_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the adaptive timeout management."""
        if self._running:
            return
        
        self._running = True
        self._adjustment_task = asyncio.create_task(self._adjustment_loop())
    
    async def stop(self):
        """Stop the adaptive timeout management."""
        self._running = False
        if self._adjustment_task:
            self._adjustment_task.cancel()
            try:
                await self._adjustment_task
            except asyncio.CancelledError:
                pass
    
    def get_timeout(self) -> float:
        """Get the current adaptive timeout value."""
        return self.current_timeout
    
    def record_operation(self, timeout_used: float, success: bool, 
                        response_time: float, network_latency: Optional[float] = None):
        """Record the result of an operation for timeout adjustment."""
        now = time.time()
        
        # Create history entry
        history_entry = TimeoutHistory(
            timestamp=now,
            timeout_value=timeout_used,
            success=success,
            response_time=response_time,
            network_latency=network_latency
        )
        
        # Add to history
        self.history.append(history_entry)
        
        # Maintain history size
        if len(self.history) > self.config.history_size:
            self.history.pop(0)
        
        # Update counters
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # Trigger adjustment if needed
        if now - self.last_adjustment > self.adjustment_interval:
            self._adjust_timeout()
            self.last_adjustment = now
    
    def _adjust_timeout(self):
        """Adjust timeout based on current strategy and performance."""
        if self.config.strategy == TimeoutStrategy.LINEAR:
            self._linear_adjustment()
        elif self.config.strategy == TimeoutStrategy.EXPONENTIAL:
            self._exponential_adjustment()
        elif self.config.strategy == TimeoutStrategy.ADAPTIVE:
            self._adaptive_adjustment()
        elif self.config.strategy == TimeoutStrategy.HYBRID:
            self._hybrid_adjustment()
    
    def _linear_adjustment(self):
        """Linear timeout adjustment based on success rate."""
        total_ops = self.success_count + self.failure_count
        if total_ops == 0:
            return
        
        success_rate = self.success_count / total_ops
        
        if success_rate < self.config.success_rate_threshold:
            # Increase timeout linearly
            self.current_timeout = min(
                self.current_timeout * self.config.adjustment_factor,
                self.config.max_timeout
            )
        elif success_rate > self.config.success_rate_threshold:
            # Decrease timeout linearly
            self.current_timeout = max(
                self.current_timeout * self.config.decay_factor,
                self.config.min_timeout
            )
    
    def _exponential_adjustment(self):
        """Exponential timeout adjustment based on recent failures."""
        recent_failures = sum(1 for h in self.history[-10:] if not h.success)
        
        if recent_failures > 3:
            # Exponential backoff
            self.current_timeout = min(
                self.current_timeout * 2.0,
                self.config.max_timeout
            )
        elif recent_failures == 0:
            # Exponential decay
            self.current_timeout = max(
                self.current_timeout * 0.5,
                self.config.min_timeout
            )
    
    def _adaptive_adjustment(self):
        """Adaptive adjustment based on response time analysis."""
        if len(self.history) < 10:
            return
        
        # Calculate average response time for successful operations
        successful_ops = [h for h in self.history if h.success]
        if not successful_ops:
            return
        
        avg_response_time = sum(h.response_time for h in successful_ops) / len(successful_ops)
        
        # Adjust based on response time vs timeout ratio
        response_timeout_ratio = avg_response_time / self.current_timeout
        
        if response_timeout_ratio > 0.8:
            # Response time is close to timeout, increase it
            self.current_timeout = min(
                self.current_timeout * 1.2,
                self.config.max_timeout
            )
        elif response_timeout_ratio < 0.3:
            # Response time is much lower than timeout, decrease it
            self.current_timeout = max(
                self.current_timeout * 0.8,
                self.config.min_timeout
            )
    
    def _hybrid_adjustment(self):
        """Combination of multiple adjustment strategies."""
        # Use adaptive adjustment as primary
        self._adaptive_adjustment()
        
        # Apply exponential adjustment for extreme cases
        recent_failures = sum(1 for h in self.history[-5:] if not h.success)
        if recent_failures >= 4:
            self._exponential_adjustment()
        
        # Apply linear adjustment for gradual changes
        self._linear_adjustment()
    
    async def _adjustment_loop(self):
        """Background loop for periodic timeout adjustments."""
        while self._running:
            try:
                await asyncio.sleep(30.0)  # Check every 30 seconds
                self._adjust_timeout()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in adaptive timeout adjustment: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get timeout statistics and performance metrics."""
        total_ops = self.success_count + self.failure_count
        success_rate = self.success_count / total_ops if total_ops > 0 else 0.0
        
        # Calculate average response time
        avg_response_time = 0.0
        if self.history:
            avg_response_time = sum(h.response_time for h in self.history) / len(self.history)
        
        # Calculate timeout efficiency
        timeout_efficiency = 0.0
        if self.history:
            efficient_timeouts = sum(1 for h in self.history 
                                   if h.response_time < h.timeout_value * 0.8)
            timeout_efficiency = efficient_timeouts / len(self.history)
        
        return {
            'current_timeout': self.current_timeout,
            'base_timeout': self.config.base_timeout,
            'min_timeout': self.config.min_timeout,
            'max_timeout': self.config.max_timeout,
            'total_operations': total_ops,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': success_rate,
            'average_response_time': avg_response_time,
            'timeout_efficiency': timeout_efficiency,
            'history_size': len(self.history),
            'strategy': self.config.strategy.value,
            'last_adjustment': self.last_adjustment
        }
    
    def reset(self):
        """Reset the adaptive timeout to base configuration."""
        self.current_timeout = self.config.base_timeout
        self.history.clear()
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = time.time()
    
    def set_strategy(self, strategy: TimeoutStrategy):
        """Change the timeout adjustment strategy."""
        self.config.strategy = strategy
    
    def update_config(self, **kwargs):
        """Update timeout configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Ensure current timeout is within new bounds
        self.current_timeout = max(
            min(self.current_timeout, self.config.max_timeout),
            self.config.min_timeout
        )


class TimeoutManager:
    """
    Manages multiple adaptive timeouts for different operations/services.
    """
    
    def __init__(self, default_config: Optional[TimeoutConfig] = None):
        self.default_config = default_config or TimeoutConfig()
        self.timeouts: Dict[str, AdaptiveTimeout] = {}
        self._running = False
    
    async def start(self):
        """Start all timeout managers."""
        self._running = True
        for timeout in self.timeouts.values():
            await timeout.start()
    
    async def stop(self):
        """Stop all timeout managers."""
        self._running = False
        for timeout in self.timeouts.values():
            await timeout.stop()
    
    def get_timeout(self, operation: str) -> AdaptiveTimeout:
        """Get or create an adaptive timeout for an operation."""
        if operation not in self.timeouts:
            self.timeouts[operation] = AdaptiveTimeout(self.default_config)
            if self._running:
                asyncio.create_task(self.timeouts[operation].start())
        
        return self.timeouts[operation]
    
    def get_timeout_value(self, operation: str) -> float:
        """Get the current timeout value for an operation."""
        timeout = self.get_timeout(operation)
        return timeout.get_timeout()
    
    def record_operation(self, operation: str, timeout_used: float, 
                        success: bool, response_time: float, 
                        network_latency: Optional[float] = None):
        """Record operation result for timeout adjustment."""
        timeout = self.get_timeout(operation)
        timeout.record_operation(timeout_used, success, response_time, network_latency)
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all timeouts."""
        return {
            op: timeout.get_statistics() 
            for op, timeout in self.timeouts.items()
        }
    
    def reset_all(self):
        """Reset all timeouts."""
        for timeout in self.timeouts.values():
            timeout.reset()
