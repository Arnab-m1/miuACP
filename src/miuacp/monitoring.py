"""
µACP Monitoring and Debugging Tools

Provides:
- Real-time metrics collection
- Health monitoring
- Performance analysis
- Debug logging
- Alerting system
- Dashboard data
"""

import asyncio
import time
import json
import logging
import threading
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime, timedelta
import psutil
import statistics


class MetricType(Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertLevel(Enum):
    """Alert levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Metric data structure."""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: float
    labels: Dict[str, str] = None
    description: str = ""


@dataclass
class Alert:
    """Alert data structure."""
    level: AlertLevel
    message: str
    timestamp: float
    source: str
    details: Dict[str, Any] = None
    acknowledged: bool = False


@dataclass
class HealthStatus:
    """Health status structure."""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: float
    details: Dict[str, Any] = None
    last_check: float = 0


class MetricsCollector:
    """Collects and manages metrics."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        
        # System metrics
        self.system_metrics = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'disk_usage': 0.0,
            'network_io': {'bytes_sent': 0, 'bytes_recv': 0}
        }
        
        # Start system monitoring
        self._start_system_monitoring()
    
    def _start_system_monitoring(self):
        """Start system metrics collection."""
        def collect_system_metrics():
            while True:
                try:
                    # CPU usage
                    self.system_metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
                    
                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.system_metrics['memory_percent'] = memory.percent
                    
                    # Disk usage
                    disk = psutil.disk_usage('/')
                    self.system_metrics['disk_usage'] = disk.percent
                    
                    # Network I/O
                    network = psutil.net_io_counters()
                    self.system_metrics['network_io'] = {
                        'bytes_sent': network.bytes_sent,
                        'bytes_recv': network.bytes_recv
                    }
                    
                    # Record metrics
                    self.record_gauge('system.cpu_percent', self.system_metrics['cpu_percent'])
                    self.record_gauge('system.memory_percent', self.system_metrics['memory_percent'])
                    self.record_gauge('system.disk_usage', self.system_metrics['disk_usage'])
                    self.record_gauge('system.network.bytes_sent', self.system_metrics['network_io']['bytes_sent'])
                    self.record_gauge('system.network.bytes_recv', self.system_metrics['network_io']['bytes_recv'])
                    
                    time.sleep(5)  # Collect every 5 seconds
                    
                except Exception as e:
                    print(f"System metrics collection error: {e}")
                    time.sleep(10)
        
        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()
    
    def record_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Record a counter metric."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.COUNTER,
            timestamp=time.time(),
            labels=labels or {}
        )
        
        self.metrics[name].append(metric)
        self.counters[name] += value
    
    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge metric."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            timestamp=time.time(),
            labels=labels or {}
        )
        
        self.metrics[name].append(metric)
        self.gauges[name] = value
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            timestamp=time.time(),
            labels=labels or {}
        )
        
        self.metrics[name].append(metric)
        self.histograms[name].append(value)
        
        # Keep only recent values
        if len(self.histograms[name]) > self.max_history:
            self.histograms[name] = self.histograms[name][-self.max_history:]
    
    def get_metric(self, name: str, window: int = 300) -> List[Metric]:
        """Get metrics for a specific name within a time window."""
        current_time = time.time()
        window_start = current_time - window
        
        if name not in self.metrics:
            return []
        
        return [
            metric for metric in self.metrics[name]
            if metric.timestamp >= window_start
        ]
    
    def get_counter_value(self, name: str) -> int:
        """Get current counter value."""
        return self.counters.get(name, 0)
    
    def get_gauge_value(self, name: str) -> float:
        """Get current gauge value."""
        return self.gauges.get(name, 0.0)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics."""
        values = self.histograms.get(name, [])
        if not values:
            return {}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'stddev': statistics.stdev(values) if len(values) > 1 else 0.0
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics summary."""
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histograms': {name: self.get_histogram_stats(name) for name in self.histograms},
            'system': self.system_metrics
        }


class HealthMonitor:
    """Monitors system health."""
    
    def __init__(self):
        self.health_status: Dict[str, HealthStatus] = {}
        self.health_checks: Dict[str, Callable] = {}
        self.check_interval = 30  # seconds
        
        # Start health monitoring
        self._start_health_monitoring()
    
    def _start_health_monitoring(self):
        """Start health monitoring loop."""
        def health_check_loop():
            while True:
                try:
                    self._run_health_checks()
                    time.sleep(self.check_interval)
                except Exception as e:
                    print(f"Health monitoring error: {e}")
                    time.sleep(10)
        
        thread = threading.Thread(target=health_check_loop, daemon=True)
        thread.start()
    
    def add_health_check(self, name: str, check_func: Callable):
        """Add a health check function."""
        self.health_checks[name] = check_func
    
    def _run_health_checks(self):
        """Run all health checks."""
        current_time = time.time()
        
        for name, check_func in self.health_checks.items():
            try:
                result = check_func()
                
                if isinstance(result, dict):
                    status = result.get('status', 'unknown')
                    details = result.get('details', {})
                else:
                    status = 'healthy' if result else 'unhealthy'
                    details = {}
                
                self.health_status[name] = HealthStatus(
                    component=name,
                    status=status,
                    timestamp=current_time,
                    details=details,
                    last_check=current_time
                )
                
            except Exception as e:
                self.health_status[name] = HealthStatus(
                    component=name,
                    status='unhealthy',
                    timestamp=current_time,
                    details={'error': str(e)},
                    last_check=current_time
                )
    
    def get_health_status(self, component: str = None) -> Union[HealthStatus, Dict[str, HealthStatus]]:
        """Get health status."""
        if component:
            return self.health_status.get(component)
        return dict(self.health_status)
    
    def is_healthy(self, component: str = None) -> bool:
        """Check if component(s) are healthy."""
        if component:
            status = self.health_status.get(component)
            return status and status.status == 'healthy'
        
        return all(
            status.status == 'healthy'
            for status in self.health_status.values()
        )


class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable] = []
        self.max_alerts = 1000
        
        # Alert thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage': 90.0,
            'error_rate': 0.1
        }
    
    def add_alert(self, level: AlertLevel, message: str, source: str, details: Dict[str, Any] = None):
        """Add a new alert."""
        alert = Alert(
            level=level,
            message=message,
            timestamp=time.time(),
            source=source,
            details=details or {}
        )
        
        self.alerts.append(alert)
        
        # Limit alert history
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"Alert handler error: {e}")
    
    def add_alert_handler(self, handler: Callable):
        """Add an alert handler."""
        self.alert_handlers.append(handler)
    
    def acknowledge_alert(self, alert_index: int):
        """Acknowledge an alert."""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index].acknowledged = True
    
    def get_active_alerts(self, level: AlertLevel = None) -> List[Alert]:
        """Get active (unacknowledged) alerts."""
        alerts = [alert for alert in self.alerts if not alert.acknowledged]
        
        if level:
            alerts = [alert for alert in alerts if alert.level == level]
        
        return alerts
    
    def get_alerts_by_source(self, source: str) -> List[Alert]:
        """Get alerts by source."""
        return [alert for alert in self.alerts if alert.source == source]
    
    def clear_old_alerts(self, max_age_hours: int = 24):
        """Clear old alerts."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        self.alerts = [
            alert for alert in self.alerts
            if alert.timestamp > cutoff_time
        ]


class DebugLogger:
    """Enhanced logging for debugging."""
    
    def __init__(self, name: str = "uacp", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Create file handler
        file_handler = logging.FileHandler(f"{name}.log")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Performance tracking
        self.performance_log: Dict[str, List[float]] = defaultdict(list)
    
    def log_performance(self, operation: str, duration: float):
        """Log performance metrics."""
        self.performance_log[operation].append(duration)
        
        # Keep only recent measurements
        if len(self.performance_log[operation]) > 100:
            self.performance_log[operation] = self.performance_log[operation][-100:]
        
        self.logger.info(f"Performance: {operation} took {duration:.4f}s")
    
    def get_performance_stats(self, operation: str) -> Dict[str, float]:
        """Get performance statistics for an operation."""
        durations = self.performance_log.get(operation, [])
        if not durations:
            return {}
        
        return {
            'count': len(durations),
            'min': min(durations),
            'max': max(durations),
            'mean': statistics.mean(durations),
            'median': statistics.median(durations),
            'stddev': statistics.stdev(durations) if len(durations) > 1 else 0.0
        }
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)


class UACPMonitoring:
    """Main monitoring system for µACP."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.metrics = MetricsCollector()
        self.health = HealthMonitor()
        self.alerts = AlertManager()
        self.logger = DebugLogger()
        
        # Add default health checks
        self._setup_default_health_checks()
        
        # Performance tracking
        self.start_time = time.time()
        self.operation_timers: Dict[str, float] = {}
    
    def _setup_default_health_checks(self):
        """Setup default health checks."""
        # System health checks
        self.health.add_health_check('system', self._check_system_health)
        self.health.add_health_check('memory', self._check_memory_health)
        self.health.add_health_check('disk', self._check_disk_health)
        self.health.add_health_check('network', self._check_network_health)
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check system health."""
        cpu_percent = self.metrics.get_gauge_value('system.cpu_percent')
        memory_percent = self.metrics.get_gauge_value('system.memory_percent')
        
        if cpu_percent > self.alerts.thresholds['cpu_percent']:
            self.alerts.add_alert(
                AlertLevel.WARNING,
                f"High CPU usage: {cpu_percent:.1f}%",
                'system'
            )
        
        if memory_percent > self.alerts.thresholds['memory_percent']:
            self.alerts.add_alert(
                AlertLevel.WARNING,
                f"High memory usage: {memory_percent:.1f}%",
                'system'
            )
        
        return {
            'status': 'healthy' if cpu_percent < 90 and memory_percent < 95 else 'degraded',
            'details': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent
            }
        }
    
    def _check_memory_health(self) -> Dict[str, Any]:
        """Check memory health."""
        memory_percent = self.metrics.get_gauge_value('system.memory_percent')
        
        if memory_percent > self.alerts.thresholds['memory_percent']:
            self.alerts.add_alert(
                AlertLevel.WARNING,
                f"High memory usage: {memory_percent:.1f}%",
                'memory'
            )
        
        return {
            'status': 'healthy' if memory_percent < 95 else 'degraded',
            'details': {'memory_percent': memory_percent}
        }
    
    def _check_disk_health(self) -> Dict[str, Any]:
        """Check disk health."""
        disk_usage = self.metrics.get_gauge_value('system.disk_usage')
        
        if disk_usage > self.alerts.thresholds['disk_usage']:
            self.alerts.add_alert(
                AlertLevel.WARNING,
                f"High disk usage: {disk_usage:.1f}%",
                'disk'
            )
        
        return {
            'status': 'healthy' if disk_usage < 95 else 'degraded',
            'details': {'disk_usage': disk_usage}
        }
    
    def _check_network_health(self) -> Dict[str, Any]:
        """Check network health."""
        bytes_sent = self.metrics.get_gauge_value('system.network.bytes_sent')
        bytes_recv = self.metrics.get_gauge_value('system.network.bytes_recv')
        
        return {
            'status': 'healthy',
            'details': {
                'bytes_sent': bytes_sent,
                'bytes_recv': bytes_recv
            }
        }
    
    def start_operation_timer(self, operation: str):
        """Start timing an operation."""
        self.operation_timers[operation] = time.time()
    
    def stop_operation_timer(self, operation: str):
        """Stop timing an operation and log performance."""
        if operation in self.operation_timers:
            duration = time.time() - self.operation_timers[operation]
            self.metrics.record_histogram(f'operation.{operation}.duration', duration)
            self.logger.log_performance(operation, duration)
            del self.operation_timers[operation]
    
    def record_message_metric(self, message_type: str, size: int, success: bool):
        """Record message-related metrics."""
        self.metrics.record_counter(f'message.{message_type}.total')
        self.metrics.record_histogram(f'message.{message_type}.size', size)
        
        if success:
            self.metrics.record_counter(f'message.{message_type}.success')
        else:
            self.metrics.record_counter(f'message.{message_type}.error')
    
    def record_connection_metric(self, connection_type: str, event: str):
        """Record connection-related metrics."""
        self.metrics.record_counter(f'connection.{connection_type}.{event}')
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        return {
            'uptime': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'health': self.health.get_health_status(),
            'metrics': self.metrics.get_all_metrics(),
            'alerts': {
                'total': len(self.alerts.alerts),
                'active': len(self.alerts.get_active_alerts()),
                'by_level': {
                    level.value: len(self.alerts.get_active_alerts(level))
                    for level in AlertLevel
                }
            },
            'performance': {
                operation: self.logger.get_performance_stats(operation)
                for operation in self.logger.performance_log
            }
        }
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format."""
        data = self.get_dashboard_data()
        
        if format.lower() == 'json':
            return json.dumps(data, indent=2, default=str)
        elif format.lower() == 'prometheus':
            return self._export_prometheus(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_prometheus(self, data: Dict[str, Any]) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # System metrics
        for metric_name, value in data['metrics']['gauges'].items():
            lines.append(f'# HELP {metric_name} {metric_name}')
            lines.append(f'# TYPE {metric_name} gauge')
            lines.append(f'{metric_name} {value}')
        
        # Counter metrics
        for metric_name, value in data['metrics']['counters'].items():
            lines.append(f'# HELP {metric_name} {metric_name}')
            lines.append(f'# TYPE {metric_name} counter')
            lines.append(f'{metric_name} {value}')
        
        return '\n'.join(lines)
