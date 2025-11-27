"""
µACP Resource & Congestion Control

Implements:
- Congestion handling with exponential backoff
- Rate limiting with token bucket algorithm
- Fairness mechanisms for multi-agent systems
- Resource management and flow control
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque


class CongestionState(Enum):
    """Congestion states."""
    NORMAL = "normal"
    CONGESTED = "congested"
    SEVERE = "severe"
    RECOVERING = "recovering"


class RateLimitPolicy(Enum):
    """Rate limiting policies."""
    DROP = "drop"           # Drop messages when limit exceeded
    QUEUE = "queue"         # Queue messages for later processing
    NACK = "nack"           # Send NACK when limit exceeded
    THROTTLE = "throttle"   # Throttle sending rate


@dataclass
class CongestionMetrics:
    """Congestion control metrics."""
    message_rate: float = 0.0          # Messages per second
    drop_rate: float = 0.0             # Dropped messages per second
    retry_rate: float = 0.0            # Retries per second
    avg_latency: float = 0.0           # Average latency in seconds
    queue_depth: int = 0               # Current queue depth
    congestion_level: float = 0.0      # 0.0 = no congestion, 1.0 = severe
    timestamp: float = field(default_factory=time.time)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    max_messages_per_second: int = 1000
    burst_size: int = 100              # Maximum burst allowance
    policy: RateLimitPolicy = RateLimitPolicy.THROTTLE
    window_size: float = 1.0           # Time window in seconds
    fairness_enabled: bool = True
    per_agent_limits: bool = True      # Separate limits per agent


class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate                # Tokens per second
        self.capacity = capacity        # Maximum tokens
        self.tokens = capacity          # Current tokens
        self.last_update = time.time()
    
    def consume(self, tokens: int) -> bool:
        """Consume tokens if available."""
        now = time.time()
        
        # Add tokens based on time passed
        time_passed = now - self.last_update
        new_tokens = time_passed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now
        
        # Check if we can consume requested tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_available_tokens(self) -> float:
        """Get currently available tokens."""
        now = time.time()
        time_passed = now - self.last_update
        new_tokens = time_passed * self.rate
        return min(self.capacity, self.tokens + new_tokens)


class UACPCongestionControl:
    """µACP congestion control implementation."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.congestion_state = CongestionState.NORMAL
        self.metrics = CongestionMetrics()
        
        # Rate limiting
        self.global_bucket = TokenBucket(
            config.max_messages_per_second,
            config.burst_size
        )
        self.agent_buckets: Dict[str, TokenBucket] = {}
        
        # Congestion control
        self.congestion_window = 1000  # Initial window size
        self.min_window = 100          # Minimum window size
        self.max_window = 10000        # Maximum window size
        self.slow_start_threshold = 5000
        
        # Fairness tracking
        self.agent_message_counts: Dict[str, int] = defaultdict(int)
        self.agent_last_reset = time.time()
        self.fairness_window = 10.0    # Reset counters every 10 seconds
        
        # Statistics
        self.message_history: deque = deque(maxlen=1000)
        self.drop_history: deque = deque(maxlen=1000)
        self.retry_history: deque = deque(maxlen=1000)
        
        # Callbacks
        self.congestion_handlers: List[Callable] = []
        self.rate_limit_handlers: List[Callable] = []
    
    def add_congestion_handler(self, handler: Callable):
        """Add congestion state change handler."""
        self.congestion_handlers.append(handler)
    
    def add_rate_limit_handler(self, handler: Callable):
        """Add rate limit exceeded handler."""
        self.rate_limit_handlers.append(handler)
    
    def can_send_message(self, agent_id: str = None) -> bool:
        """Check if message can be sent."""
        # Check global rate limit
        if not self.global_bucket.consume(1):
            return False
        
        # Check per-agent rate limit if enabled
        if self.config.per_agent_limits and agent_id:
            if agent_id not in self.agent_buckets:
                # Create bucket for new agent
                self.agent_buckets[agent_id] = TokenBucket(
                    self.config.max_messages_per_second // 10,  # Per-agent limit
                    self.config.burst_size // 10
                )
            
            if not self.agent_buckets[agent_id].consume(1):
                return False
        
        return True
    
    def record_message_sent(self, agent_id: str = None, latency: float = None):
        """Record that a message was sent."""
        now = time.time()
        
        # Update message history
        self.message_history.append({
            'timestamp': now,
            'agent_id': agent_id,
            'latency': latency
        })
        
        # Update agent message counts for fairness
        if agent_id:
            self.agent_message_counts[agent_id] += 1
        
        # Update metrics
        self._update_metrics()
        
        # Check for fairness reset
        if now - self.agent_last_reset > self.fairness_window:
            self._reset_fairness_counters()
    
    def record_message_dropped(self, agent_id: str = None, reason: str = ""):
        """Record that a message was dropped."""
        now = time.time()
        
        self.drop_history.append({
            'timestamp': now,
            'agent_id': agent_id,
            'reason': reason
        })
        
        self._update_metrics()
    
    def record_retry(self, agent_id: str = None, attempt: int = 1):
        """Record a retry attempt."""
        now = time.time()
        
        self.retry_history.append({
            'timestamp': now,
            'agent_id': agent_id,
            'attempt': attempt
        })
        
        self._update_metrics()
    
    def calculate_backoff(self, attempt_count: int) -> float:
        """Calculate exponential backoff delay."""
        # Exponential backoff like CoAP RFC 7252
        base_delay = 1.0  # Base delay in seconds
        max_delay = 60.0  # Maximum delay in seconds
        
        delay = min(base_delay * (2 ** attempt_count), max_delay)
        
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0.8, 1.2)
        
        return delay * jitter
    
    def handle_congestion(self, message_rate: float, queue_depth: int) -> Dict[str, Any]:
        """Handle congestion detection and response."""
        response = {
            'action': 'none',
            'congestion_level': 0.0,
            'window_adjustment': 0,
            'rate_adjustment': 1.0
        }
        
        # Calculate congestion level (0.0 to 1.0)
        target_rate = self.config.max_messages_per_second
        rate_ratio = message_rate / target_rate if target_rate > 0 else 0
        
        queue_ratio = queue_depth / self.config.burst_size if self.config.burst_size > 0 else 0
        
        congestion_level = max(rate_ratio, queue_ratio)
        self.metrics.congestion_level = congestion_level
        
        # Determine congestion state
        old_state = self.congestion_state
        
        if congestion_level < 0.7:
            self.congestion_state = CongestionState.NORMAL
        elif congestion_level < 0.9:
            self.congestion_state = CongestionState.CONGESTED
        elif congestion_level < 1.0:
            self.congestion_state = CongestionState.SEVERE
        else:
            self.congestion_state = CongestionState.SEVERE
        
        # State change notification
        if old_state != self.congestion_state:
            self._notify_congestion_handlers(old_state, self.congestion_state)
        
        # Apply congestion control based on state
        if self.congestion_state == CongestionState.NORMAL:
            # Normal operation - increase window if possible
            if self.congestion_window < self.slow_start_threshold:
                # Slow start phase
                self.congestion_window = min(
                    self.congestion_window * 2,
                    self.slow_start_threshold
                )
            else:
                # Congestion avoidance phase
                self.congestion_window = min(
                    self.congestion_window + 1,
                    self.max_window
                )
            
            response['action'] = 'increase_window'
            response['window_adjustment'] = 1
        
        elif self.congestion_state == CongestionState.CONGESTED:
            # Congested - reduce window
            self.congestion_window = max(
                self.congestion_window // 2,
                self.min_window
            )
            
            response['action'] = 'reduce_window'
            response['window_adjustment'] = -1
            response['rate_adjustment'] = 0.8
        
        elif self.congestion_state == CongestionState.SEVERE:
            # Severe congestion - aggressive reduction
            self.congestion_window = self.min_window
            self.slow_start_threshold = self.congestion_window // 2
            
            response['action'] = 'reset_window'
            response['window_adjustment'] = -self.congestion_window
            response['rate_adjustment'] = 0.5
        
        return response
    
    def get_fairness_score(self, agent_id: str) -> float:
        """Calculate fairness score for an agent (0.0 = fair, 1.0 = unfair)."""
        if not self.agent_message_counts:
            return 0.0
        
        total_messages = sum(self.agent_message_counts.values())
        if total_messages == 0:
            return 0.0
        
        agent_messages = self.agent_message_counts.get(agent_id, 0)
        fair_share = total_messages / len(self.agent_message_counts)
        
        if fair_share == 0:
            return 0.0
        
        # Calculate deviation from fair share
        deviation = abs(agent_messages - fair_share) / fair_share
        return min(deviation, 1.0)
    
    def should_throttle_agent(self, agent_id: str) -> bool:
        """Determine if an agent should be throttled for fairness."""
        if not self.config.fairness_enabled:
            return False
        
        fairness_score = self.get_fairness_score(agent_id)
        return fairness_score > 0.3  # Throttle if more than 30% unfair
    
    def get_congestion_summary(self) -> Dict[str, Any]:
        """Get comprehensive congestion control summary."""
        summary = {
            'congestion_state': self.congestion_state.value,
            'congestion_level': self.metrics.congestion_level,
            'congestion_window': self.congestion_window,
            'slow_start_threshold': self.slow_start_threshold,
            'metrics': {
                'message_rate': self.metrics.message_rate,
                'drop_rate': self.metrics.drop_rate,
                'retry_rate': self.metrics.retry_rate,
                'avg_latency': self.metrics.avg_latency,
                'queue_depth': self.metrics.queue_depth
            },
            'rate_limiting': {
                'global_tokens': self.global_bucket.get_available_tokens(),
                'global_capacity': self.global_bucket.capacity,
                'global_rate': self.global_bucket.rate,
                'agent_buckets': len(self.agent_buckets)
            },
            'fairness': {
                'total_agents': len(self.agent_message_counts),
                'fairness_window': self.fairness_window,
                'agent_counts': dict(self.agent_message_counts)
            },
            'statistics': {
                'total_messages': len(self.message_history),
                'total_drops': len(self.drop_history),
                'total_retries': len(self.retry_history)
            }
        }
        
        return summary
    
    def _update_metrics(self):
        """Update congestion metrics."""
        now = time.time()
        
        # Calculate message rate
        if len(self.message_history) > 1:
            time_span = now - self.message_history[0]['timestamp']
            if time_span > 0:
                self.metrics.message_rate = len(self.message_history) / time_span
        
        # Calculate drop rate
        if len(self.drop_history) > 1:
            time_span = now - self.drop_history[0]['timestamp']
            if time_span > 0:
                self.metrics.drop_rate = len(self.drop_history) / time_span
        
        # Calculate retry rate
        if len(self.retry_history) > 1:
            time_span = now - self.retry_history[0]['timestamp']
            if time_span > 0:
                self.metrics.retry_rate = len(self.retry_history) / time_span
        
        # Calculate average latency
        latencies = [msg['latency'] for msg in self.message_history if msg['latency'] is not None]
        if latencies:
            self.metrics.avg_latency = sum(latencies) / len(latencies)
        
        # Update timestamp
        self.metrics.timestamp = now
    
    def _reset_fairness_counters(self):
        """Reset fairness counters."""
        self.agent_message_counts.clear()
        self.agent_last_reset = time.time()
    
    def _notify_congestion_handlers(self, old_state: CongestionState, new_state: CongestionState):
        """Notify congestion state change handlers."""
        for handler in self.congestion_handlers:
            try:
                handler(old_state, new_state, self.metrics)
            except Exception as e:
                print(f"❌ Congestion handler error: {e}")
    
    def _notify_rate_limit_handlers(self, agent_id: str, message_count: int):
        """Notify rate limit exceeded handlers."""
        for handler in self.rate_limit_handlers:
            try:
                handler(agent_id, message_count, self.config)
            except Exception as e:
                print(f"❌ Rate limit handler error: {e}")


class ResourceManager:
    """Resource management for µACP agents."""
    
    def __init__(self):
        self.resource_limits: Dict[str, int] = {
            'max_connections': 1000,
            'max_memory_mb': 512,
            'max_cpu_percent': 80,
            'max_disk_mb': 1024,
            'max_bandwidth_mbps': 100
        }
        
        self.current_usage: Dict[str, float] = {
            'connections': 0,
            'memory_mb': 0,
            'cpu_percent': 0,
            'disk_mb': 0,
            'bandwidth_mbps': 0
        }
        
        self.resource_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.usage_history: deque = deque(maxlen=1000)
    
    def add_resource_handler(self, resource: str, handler: Callable):
        """Add handler for resource limit exceeded."""
        self.resource_handlers[resource].append(handler)
    
    def check_resource_available(self, resource: str, amount: float) -> bool:
        """Check if resource is available."""
        if resource not in self.resource_limits:
            return True
        
        limit = self.resource_limits[resource]
        current = self.current_usage.get(resource, 0)
        
        return (current + amount) <= limit
    
    def allocate_resource(self, resource: str, amount: float) -> bool:
        """Allocate resource if available."""
        if not self.check_resource_available(resource, amount):
            self._notify_resource_handlers(resource, amount, 'allocation_failed')
            return False
        
        self.current_usage[resource] += amount
        self._record_usage(resource, amount, 'allocated')
        return True
    
    def release_resource(self, resource: str, amount: float):
        """Release allocated resource."""
        if resource in self.current_usage:
            self.current_usage[resource] = max(0, self.current_usage[resource] - amount)
            self._record_usage(resource, -amount, 'released')
    
    def get_resource_utilization(self, resource: str) -> float:
        """Get resource utilization percentage."""
        if resource not in self.resource_limits:
            return 0.0
        
        limit = self.resource_limits[resource]
        current = self.current_usage.get(resource, 0)
        
        return (current / limit) * 100 if limit > 0 else 0
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get comprehensive resource usage summary."""
        summary = {
            'limits': self.resource_limits.copy(),
            'current_usage': self.current_usage.copy(),
            'utilization': {},
            'history': {
                'total_records': len(self.usage_history),
                'recent_activity': list(self.usage_history)[-10:] if self.usage_history else []
            }
        }
        
        # Calculate utilization for each resource
        for resource in self.resource_limits:
            summary['utilization'][resource] = self.get_resource_utilization(resource)
        
        return summary
    
    def _record_usage(self, resource: str, amount: float, action: str):
        """Record resource usage."""
        record = {
            'timestamp': time.time(),
            'resource': resource,
            'amount': amount,
            'action': action,
            'current_total': self.current_usage.get(resource, 0)
        }
        
        self.usage_history.append(record)
    
    def _notify_resource_handlers(self, resource: str, amount: float, reason: str):
        """Notify resource limit handlers."""
        for handler in self.resource_handlers[resource]:
            try:
                handler(resource, amount, reason, self.current_usage.get(resource, 0))
            except Exception as e:
                print(f"❌ Resource handler error: {e}")


# Global instances
default_congestion_control = UACPCongestionControl(RateLimitConfig())
default_resource_manager = ResourceManager()


def get_congestion_control(config: RateLimitConfig = None) -> UACPCongestionControl:
    """Get congestion control instance."""
    if config is None:
        return default_congestion_control
    
    return UACPCongestionControl(config)


def get_resource_manager() -> ResourceManager:
    """Get resource manager instance."""
    return default_resource_manager


def calculate_backoff(attempt_count: int) -> float:
    """Calculate exponential backoff delay."""
    return default_congestion_control.calculate_backoff(attempt_count)
