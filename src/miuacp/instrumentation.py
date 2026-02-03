"""
µACP Instrumentation & Control State Management

This module handles all instrumentation and control state including:
- Logging buffers
- Metrics counters (bytes sent, dropped packets, retries)
- Debug/trace contexts
- Policy enforcement hooks (rate limiting, quota)
"""

import asyncio
import time
import uuid
import json
import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading
import queue


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class PolicyType(Enum):
    """Policy types."""
    RATE_LIMIT = "rate_limit"
    QUOTA = "quota"
    ACCESS_CONTROL = "access_control"
    THROTTLING = "throttling"
    FILTERING = "filtering"


@dataclass
class LogEntry:
    """Log entry information."""
    entry_id: str
    timestamp: float
    level: LogLevel
    source: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Metric:
    """Metric information."""
    metric_id: str
    name: str
    metric_type: MetricType
    value: Union[int, float]
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    unit: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceContext:
    """Trace context for distributed tracing."""
    trace_id: str
    span_id: str
    operation: str
    source: str
    created: float
    start_time: float
    parent_span_id: Optional[str] = None
    end_time: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyRule:
    """Policy rule for enforcement."""
    rule_id: str
    policy_type: PolicyType
    name: str
    description: str
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    priority: int = 0
    enabled: bool = True
    created: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Quota:
    """Quota information."""
    quota_id: str
    resource: str
    limit: int
    used: int
    reset_interval: float
    last_reset: float
    created: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class UACPInstrumentation:
    """µACP instrumentation and control state management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Logging
        self.log_buffer: deque = deque(maxlen=self.config.get('max_log_entries', 10000))
        self.log_levels: Dict[str, LogLevel] = defaultdict(lambda: LogLevel.INFO)
        self.log_sources: Set[str] = set()
        
        # Metrics
        self.metrics: Dict[str, Metric] = {}
        self.metric_counters: Dict[str, int] = defaultdict(int)
        self.metric_gauges: Dict[str, float] = defaultdict(float)
        self.metric_histograms: Dict[str, List[float]] = defaultdict(list)
        self.metric_summaries: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Tracing
        self.trace_contexts: Dict[str, TraceContext] = {}
        self.active_traces: Dict[str, str] = {}  # span_id -> trace_id
        self.trace_buffer: deque = deque(maxlen=self.config.get('max_trace_entries', 1000))
        
        # Policies
        self.policies: Dict[str, PolicyRule] = {}
        self.policy_enforcement: Dict[str, bool] = defaultdict(lambda: True)
        self.policy_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Quotas
        self.quotas: Dict[str, Quota] = {}
        self.resource_quotas: Dict[str, str] = {}  # resource -> quota_id
        
        # Configuration
        self.max_log_entries = self.config.get('max_log_entries', 10000)
        self.max_metrics = self.config.get('max_metrics', 10000)
        self.max_traces = self.config.get('max_traces', 1000)
        self.max_policies = self.config.get('max_policies', 100)
        self.max_quotas = self.config.get('max_quotas', 100)
        
        self.log_retention = self.config.get('log_retention', 3600.0)  # 1 hour
        self.metric_retention = self.config.get('metric_retention', 86400.0)  # 24 hours
        self.trace_retention = self.config.get('trace_retention', 3600.0)  # 1 hour
        
        # State tracking
        self.last_cleanup = time.time()
        self.cleanup_interval = 60.0
        self.stats = {
            'log_entries_created': 0,
            'metrics_updated': 0,
            'traces_created': 0,
            'policies_evaluated': 0,
            'quotas_enforced': 0,
            'policy_violations': 0
        }
        
        # Background tasks
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        self._metric_export_task: Optional[asyncio.Task] = None
        
        # Threading
        self._lock = threading.RLock()
        self._log_queue = queue.Queue(maxsize=1000)
        self._metric_queue = queue.Queue(maxsize=1000)
        
        # Initialize default metrics
        self._init_default_metrics()
    
    async def start(self):
        """Start the instrumentation manager."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._metric_export_task = asyncio.create_task(self._metric_export_loop())
        
        # Start background threads
        self._start_background_threads()
    
    async def stop(self):
        """Stop the instrumentation manager."""
        self._running = False
        
        for task in [self._cleanup_task, self._metric_export_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Stop background threads
        self._stop_background_threads()
    
    def _start_background_threads(self):
        """Start background processing threads."""
        self._log_thread = threading.Thread(target=self._log_processor, daemon=True)
        self._metric_thread = threading.Thread(target=self._metric_processor, daemon=True)
        
        self._log_thread.start()
        self._metric_thread.start()
    
    def _stop_background_threads(self):
        """Stop background processing threads."""
        if hasattr(self, '_log_thread'):
            self._log_thread.join(timeout=1.0)
        if hasattr(self, '_metric_thread'):
            self._metric_thread.join(timeout=1.0)
    
    # === Logging Management ===
    
    def log(self, level: LogLevel, source: str, message: str,
            context: Optional[Dict[str, Any]] = None,
            tags: Optional[Dict[str, str]] = None) -> str:
        """Create a log entry."""
        entry_id = str(uuid.uuid4())
        now = time.time()
        
        log_entry = LogEntry(
            entry_id=entry_id,
            timestamp=now,
            level=level,
            source=source,
            message=message,
            context=context or {},
            tags=tags or {}
        )
        
        # Add to queue for background processing
        try:
            self._log_queue.put_nowait(log_entry)
        except queue.Full:
            # Queue full, drop oldest entry
            try:
                self._log_queue.get_nowait()
                self._log_queue.put_nowait(log_entry)
            except queue.Empty:
                pass
        
        self.log_sources.add(source)
        return entry_id
    
    def debug(self, source: str, message: str, **kwargs) -> str:
        """Log debug message."""
        return self.log(LogLevel.DEBUG, source, message, **kwargs)
    
    def info(self, source: str, message: str, **kwargs) -> str:
        """Log info message."""
        return self.log(LogLevel.INFO, source, message, **kwargs)
    
    def warning(self, source: str, message: str, **kwargs) -> str:
        """Log warning message."""
        return self.log(LogLevel.WARNING, source, message, **kwargs)
    
    def error(self, source: str, message: str, **kwargs) -> str:
        """Log error message."""
        return self.log(LogLevel.ERROR, source, message, **kwargs)
    
    def critical(self, source: str, message: str, **kwargs) -> str:
        """Log critical message."""
        return self.log(LogLevel.CRITICAL, source, message, **kwargs)
    
    def set_log_level(self, source: str, level: LogLevel) -> None:
        """Set log level for a source."""
        self.log_levels[source] = level
    
    def get_logs(self, level: Optional[LogLevel] = None, source: Optional[str] = None,
                 limit: Optional[int] = None) -> List[LogEntry]:
        """Get logs with optional filtering."""
        with self._lock:
            logs = list(self.log_buffer)
            
            if level:
                logs = [log for log in logs if log.level == level]
            
            if source:
                logs = [log for log in logs if log.source == source]
            
            if limit:
                logs = logs[-limit:]
            
            return logs
    
    def _log_processor(self):
        """Background log processor thread."""
        while self._running:
            try:
                log_entry = self._log_queue.get(timeout=1.0)
                
                with self._lock:
                    # Check log level
                    if log_entry.level.value >= self.log_levels[log_entry.source].value:
                        self.log_buffer.append(log_entry)
                        self.stats['log_entries_created'] += 1
                        
                        # Also log to standard logging if configured
                        if self.config.get('enable_std_logging', False):
                            logger = logging.getLogger(log_entry.source)
                            log_method = getattr(logger, log_entry.level.value, logger.info)
                            log_method(log_entry.message, extra=log_entry.context)
                
                self._log_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in log processor: {e}")
    
    # === Metrics Management ===
    
    def _init_default_metrics(self):
        """Initialize default metrics."""
        now = time.time()
        
        # System metrics
        self._create_metric("system.uptime", MetricType.GAUGE, time.time() - now, "System uptime in seconds")
        self._create_metric("system.memory.used", MetricType.GAUGE, 0, "Memory usage in bytes")
        self._create_metric("system.memory.total", MetricType.GAUGE, 0, "Total memory in bytes")
        self._create_metric("system.cpu.usage", MetricType.GAUGE, 0, "CPU usage percentage")
        
        # Network metrics
        self._create_metric("network.bytes.sent", MetricType.COUNTER, 0, "Total bytes sent")
        self._create_metric("network.bytes.received", MetricType.COUNTER, 0, "Total bytes received")
        self._create_metric("network.packets.sent", MetricType.COUNTER, 0, "Total packets sent")
        self._create_metric("network.packets.received", MetricType.COUNTER, 0, "Total packets received")
        self._create_metric("network.packets.dropped", MetricType.COUNTER, 0, "Total packets dropped")
        
        # Message metrics
        self._create_metric("messages.sent", MetricType.COUNTER, 0, "Total messages sent")
        self._create_metric("messages.received", MetricType.COUNTER, 0, "Total messages received")
        self._create_metric("messages.retries", MetricType.COUNTER, 0, "Total message retries")
        self._create_metric("messages.failed", MetricType.COUNTER, 0, "Total failed messages")
        
        # Latency metrics
        self._create_metric("latency.request_response", MetricType.HISTOGRAM, [], "Request-response latency")
        self._create_metric("latency.processing", MetricType.HISTOGRAM, [], "Message processing latency")
    
    def _create_metric(self, name: str, metric_type: MetricType, value: Any, description: str = "") -> str:
        """Create a new metric."""
        metric_id = str(uuid.uuid4())
        now = time.time()
        
        metric = Metric(
            metric_id=metric_id,
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=now,
            description=description
        )
        
        self.metrics[metric_id] = metric
        
        # Initialize storage based on type
        if metric_type == MetricType.COUNTER:
            self.metric_counters[name] = 0
        elif metric_type == MetricType.GAUGE:
            self.metric_gauges[name] = 0.0
        elif metric_type == MetricType.HISTOGRAM:
            self.metric_histograms[name] = []
        elif metric_type == MetricType.SUMMARY:
            self.metric_summaries[name] = {'count': 0, 'sum': 0.0, 'min': float('inf'), 'max': float('-inf')}
        
        return metric_id
    
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            if name in self.metric_counters:
                self.metric_counters[name] += value
                self.stats['metrics_updated'] += 1
                
                # Update metric timestamp
                for metric in self.metrics.values():
                    if metric.name == name:
                        metric.timestamp = time.time()
                        metric.labels.update(labels or {})
                        break
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        with self._lock:
            if name in self.metric_gauges:
                self.metric_gauges[name] = value
                self.stats['metrics_updated'] += 1
                
                # Update metric timestamp
                for metric in self.metrics.values():
                    if metric.name == name:
                        metric.timestamp = time.time()
                        metric.value = value
                        metric.labels.update(labels or {})
                        break
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a value in a histogram metric."""
        with self._lock:
            if name in self.metric_histograms:
                self.metric_histograms[name].append(value)
                
                # Keep only recent values
                if len(self.metric_histograms[name]) > 1000:
                    self.metric_histograms[name] = self.metric_histograms[name][-1000:]
                
                self.stats['metrics_updated'] += 1
                
                # Update metric timestamp
                for metric in self.metrics.values():
                    if metric.name == name:
                        metric.timestamp = time.time()
                        metric.value = self.metric_histograms[name]
                        metric.labels.update(labels or {})
                        break
    
    def update_summary(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Update a summary metric."""
        with self._lock:
            if name in self.metric_summaries:
                summary = self.metric_summaries[name]
                summary['count'] += 1
                summary['sum'] += value
                summary['min'] = min(summary['min'], value)
                summary['max'] = max(summary['max'], value)
                
                self.stats['metrics_updated'] += 1
                
                # Update metric timestamp
                for metric in self.metrics.values():
                    if metric.name == name:
                        metric.timestamp = time.time()
                        metric.value = summary
                        metric.labels.update(labels or {})
                        break
    
    def get_metric(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metric value by name."""
        with self._lock:
            if name in self.metric_counters:
                return {'type': 'counter', 'value': self.metric_counters[name]}
            elif name in self.metric_gauges:
                return {'type': 'gauge', 'value': self.metric_gauges[name]}
            elif name in self.metric_histograms:
                values = self.metric_histograms[name]
                if values:
                    return {
                        'type': 'histogram',
                        'count': len(values),
                        'min': min(values),
                        'max': max(values),
                        'mean': sum(values) / len(values),
                        'values': values[-100:]  # Last 100 values
                    }
            elif name in self.metric_summaries:
                return {'type': 'summary', 'value': self.metric_summaries[name]}
        
        return None
    
    def _metric_processor(self):
        """Background metric processor thread."""
        while self._running:
            try:
                metric_update = self._metric_queue.get(timeout=1.0)
                # Process metric updates if needed
                self._metric_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in metric processor: {e}")
    
    # === Tracing Management ===
    
    def start_trace(self, operation: str, source: str, parent_span_id: Optional[str] = None,
                   tags: Optional[Dict[str, str]] = None) -> str:
        """Start a new trace."""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        now = time.time()
        
        trace_context = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            created=now,
            start_time=now,
            operation=operation,
            source=source,
            tags=tags or {}
        )
        
        with self._lock:
            self.trace_contexts[span_id] = trace_context
            self.active_traces[span_id] = trace_id
            self.trace_buffer.append(trace_context)
            self.stats['traces_created'] += 1
        
        return span_id
    
    def end_trace(self, span_id: str, tags: Optional[Dict[str, str]] = None) -> bool:
        """End a trace."""
        with self._lock:
            if span_id in self.trace_contexts:
                trace_context = self.trace_contexts[span_id]
                trace_context.end_time = time.time()
                
                if tags:
                    trace_context.tags.update(tags)
                
                # Remove from active traces
                if span_id in self.active_traces:
                    del self.active_traces[span_id]
                
                return True
        
        return False
    
    def add_trace_event(self, span_id: str, event_name: str, event_data: Optional[Dict[str, Any]] = None) -> bool:
        """Add an event to a trace."""
        with self._lock:
            if span_id in self.trace_contexts:
                trace_context = self.trace_contexts[span_id]
                event = {
                    'name': event_name,
                    'timestamp': time.time(),
                    'data': event_data or {}
                }
                trace_context.events.append(event)
                return True
        
        return False
    
    def get_trace(self, span_id: str) -> Optional[TraceContext]:
        """Get trace context by span ID."""
        return self.trace_contexts.get(span_id)
    
    def get_active_traces(self) -> List[TraceContext]:
        """Get all active traces."""
        with self._lock:
            return [self.trace_contexts[span_id] for span_id in self.active_traces.values()]
    
    # === Policy Management ===
    
    def add_policy(self, policy_type: PolicyType, name: str, description: str,
                   conditions: Dict[str, Any], actions: List[Dict[str, Any]],
                   priority: int = 0) -> str:
        """Add a new policy rule."""
        if len(self.policies) >= self.max_policies:
            # Remove lowest priority policy
            lowest_priority = max(self.policies.values(), key=lambda p: p.priority)
            del self.policies[lowest_priority.rule_id]
        
        rule_id = str(uuid.uuid4())
        now = time.time()
        
        policy = PolicyRule(
            rule_id=rule_id,
            policy_type=policy_type,
            name=name,
            description=description,
            conditions=conditions,
            actions=actions,
            priority=priority,
            created=now
        )
        
        self.policies[rule_id] = policy
        return rule_id
    
    def evaluate_policy(self, policy_type: PolicyType, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate policies of a specific type."""
        with self._lock:
            applicable_policies = [
                policy for policy in self.policies.values()
                if policy.policy_type == policy_type and policy.enabled
            ]
            
            # Sort by priority (lower number = higher priority)
            applicable_policies.sort(key=lambda p: p.priority)
            
            result = {
                'allowed': True,
                'actions': [],
                'violations': [],
                'evaluated_policies': []
            }
            
            for policy in applicable_policies:
                self.stats['policies_evaluated'] += 1
                
                # Simple condition evaluation (could be extended with expression engine)
                if self._evaluate_conditions(policy.conditions, context):
                    result['actions'].extend(policy.actions)
                    result['evaluated_policies'].append({
                        'rule_id': policy.rule_id,
                        'name': policy.name,
                        'result': 'matched'
                    })
                else:
                    result['evaluated_policies'].append({
                        'rule_id': policy.rule_id,
                        'name': policy.name,
                        'result': 'not_matched'
                    })
            
            # Store policy evaluation result
            evaluation_id = str(uuid.uuid4())
            self.policy_results[evaluation_id] = [result]
            
            return result
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate policy conditions against context."""
        # Simple condition evaluation - could be extended with expression engine
        for key, expected_value in conditions.items():
            if key not in context:
                return False
            
            actual_value = context[key]
            
            if isinstance(expected_value, dict):
                if 'min' in expected_value and actual_value < expected_value['min']:
                    return False
                if 'max' in expected_value and actual_value > expected_value['max']:
                    return False
                if 'equals' in expected_value and actual_value != expected_value['equals']:
                    return False
            elif actual_value != expected_value:
                return False
        
        return True
    
    def enable_policy(self, rule_id: str) -> bool:
        """Enable a policy rule."""
        if rule_id in self.policies:
            self.policies[rule_id].enabled = True
            return True
        return False
    
    def disable_policy(self, rule_id: str) -> bool:
        """Disable a policy rule."""
        if rule_id in self.policies:
            self.policies[rule_id].enabled = False
            return True
        return False
    
    # === Quota Management ===
    
    def create_quota(self, resource: str, limit: int, reset_interval: float) -> str:
        """Create a new quota."""
        if len(self.quotas) >= self.max_quotas:
            # Remove oldest quota
            oldest = min(self.quotas.values(), key=lambda q: q.created)
            del self.quotas[oldest.quota_id]
            if oldest.resource in self.resource_quotas:
                del self.resource_quotas[oldest.resource]
        
        quota_id = str(uuid.uuid4())
        now = time.time()
        
        quota = Quota(
            quota_id=quota_id,
            resource=resource,
            limit=limit,
            used=0,
            reset_interval=reset_interval,
            last_reset=now,
            created=now
        )
        
        self.quotas[quota_id] = quota
        self.resource_quotas[resource] = quota_id
        
        return quota_id
    
    def check_quota(self, resource: str, amount: int = 1) -> bool:
        """Check if quota allows the requested amount."""
        with self._lock:
            if resource in self.resource_quotas:
                quota_id = self.resource_quotas[resource]
                quota = self.quotas[quota_id]
                
                # Check if quota needs reset
                now = time.time()
                if now - quota.last_reset >= quota.reset_interval:
                    quota.used = 0
                    quota.last_reset = now
                
                if quota.used + amount <= quota.limit:
                    quota.used += amount
                    self.stats['quotas_enforced'] += 1
                    return True
                else:
                    self.stats['policy_violations'] += 1
                    return False
        
        return True  # No quota defined, allow
    
    def get_quota_status(self, resource: str) -> Optional[Dict[str, Any]]:
        """Get quota status for a resource."""
        if resource in self.resource_quotas:
            quota_id = self.resource_quotas[resource]
            quota = self.quotas[quota_id]
            
            return {
                'limit': quota.limit,
                'used': quota.used,
                'remaining': quota.limit - quota.used,
                'reset_interval': quota.reset_interval,
                'last_reset': quota.last_reset
            }
        
        return None
    
    # === Background Tasks ===
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
    
    async def _metric_export_loop(self):
        """Background metric export loop."""
        while self._running:
            try:
                await asyncio.sleep(60.0)  # Export every minute
                self._export_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in metric export loop: {e}")
    
    def _cleanup_expired(self):
        """Clean up expired entries."""
        now = time.time()
        
        # Clean up expired logs
        expired_logs = [
            i for i, log_entry in enumerate(self.log_buffer)
            if now - log_entry.timestamp > self.log_retention
        ]
        
        for i in reversed(expired_logs):
            del self.log_buffer[i]
        
        # Clean up expired metrics
        expired_metrics = [
            metric_id for metric_id, metric in self.metrics.items()
            if now - metric.timestamp > self.metric_retention
        ]
        
        for metric_id in expired_metrics:
            del self.metrics[metric_id]
        
        # Clean up expired traces
        expired_traces = [
            span_id for span_id, trace in self.trace_contexts.items()
            if trace.end_time and now - trace.end_time > self.trace_retention
        ]
        
        for span_id in expired_traces:
            del self.trace_contexts[span_id]
        
        self.last_cleanup = now
    
    def _export_metrics(self):
        """Export metrics to external systems."""
        # This could export to Prometheus, InfluxDB, etc.
        # For now, just log the current metrics
        with self._lock:
            for name, value in self.metric_counters.items():
                self.info("metrics", f"Counter {name}: {value}")
            
            for name, value in self.metric_gauges.items():
                self.info("metrics", f"Gauge {name}: {value}")
    
    # === Statistics and Export ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get instrumentation statistics."""
        return {
            **self.stats,
            'current_logs': len(self.log_buffer),
            'current_metrics': len(self.metrics),
            'current_traces': len(self.trace_contexts),
            'active_traces': len(self.active_traces),
            'current_policies': len(self.policies),
            'current_quotas': len(self.quotas),
            'last_cleanup': self.last_cleanup
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export current instrumentation state."""
        return {
            'logs': {
                'recent_entries': [
                    {
                        'timestamp': log.timestamp,
                        'level': log.level.value,
                        'source': log.source,
                        'message': log.message
                    }
                    for log in list(self.log_buffer)[-100:]  # Last 100 entries
                ]
            },
            'metrics': {
                'counters': dict(self.metric_counters),
                'gauges': dict(self.metric_gauges),
                'histograms': {
                    name: {
                        'count': len(values),
                        'min': min(values) if values else 0,
                        'max': max(values) if values else 0,
                        'mean': sum(values) / len(values) if values else 0
                    }
                    for name, values in self.metric_histograms.items()
                }
            },
            'traces': {
                'active_count': len(self.active_traces),
                'total_count': len(self.trace_contexts)
            },
            'policies': {
                'total_count': len(self.policies),
                'enabled_count': len([p for p in self.policies.values() if p.enabled])
            },
            'quotas': {
                quota_id: {
                    'resource': quota.resource,
                    'limit': quota.limit,
                    'used': quota.used,
                    'remaining': quota.limit - quota.used
                }
                for quota_id, quota in self.quotas.items()
            },
            'stats': self.get_stats()
        }

