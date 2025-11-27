"""
Health Monitoring Implementation for µACP

Provides comprehensive health monitoring, self-healing, and performance profiling
for lightweight AI agent communications.
"""

import time
import asyncio
import psutil
import threading
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "HEALTHY"       # All systems operational
    WARNING = "WARNING"        # Some issues detected
    CRITICAL = "CRITICAL"      # Critical issues, immediate attention needed
    UNKNOWN = "UNKNOWN"        # Status cannot be determined


class CheckType(Enum):
    """Types of health checks."""
    SYSTEM = "SYSTEM"          # System-level checks (CPU, memory, disk)
    NETWORK = "NETWORK"        # Network connectivity checks
    SERVICE = "SERVICE"        # Service-specific checks
    CUSTOM = "CUSTOM"          # Custom application checks


@dataclass
class HealthCheck:
    """A health check definition."""
    check_id: str
    name: str
    description: str
    check_type: CheckType
    check_func: Callable
    timeout: float = 30.0
    interval: float = 60.0
    critical: bool = False
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheckResult:
    """Result of a health check execution."""
    check_id: str
    timestamp: float
    status: HealthStatus
    response_time: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int
    load_average: Optional[float] = None


@dataclass
class PerformanceProfile:
    """Performance profiling information."""
    operation_name: str
    total_calls: int
    total_time: float
    average_time: float
    min_time: float
    max_time: float
    success_count: int
    failure_count: int
    last_call: Optional[float] = None


class HealthMonitor:
    """
    Comprehensive health monitoring system for lightweight AI agents.
    
    Provides:
    - System health monitoring
    - Custom health checks
    - Performance profiling
    - Self-healing capabilities
    - Health status aggregation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Health checks
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_results: Dict[str, List[HealthCheckResult]] = defaultdict(list)
        
        # System monitoring
        self.system_metrics: List[SystemMetrics] = []
        self.max_metrics_history = self.config.get('max_metrics_history', 1000)
        
        # Performance profiling
        self.performance_profiles: Dict[str, PerformanceProfile] = {}
        
        # Health status
        self.overall_health = HealthStatus.UNKNOWN
        self.last_health_update = time.time()
        
        # Background tasks
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._system_monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Initialize default system checks
        self._initialize_default_checks()
    
    def _initialize_default_checks(self):
        """Initialize default system health checks."""
        # CPU usage check
        self.add_health_check_by_params(
            check_id="system_cpu",
            name="CPU Usage",
            description="Monitor CPU usage",
            check_type=CheckType.SYSTEM,
            check_func=self._check_cpu_usage,
            interval=30.0,
            critical=True
        )
        
        # Memory usage check
        self.add_health_check_by_params(
            check_id="system_memory",
            name="Memory Usage",
            description="Monitor memory usage",
            check_type=CheckType.SYSTEM,
            check_func=self._check_memory_usage,
            interval=30.0,
            critical=True
        )
        
        # Disk usage check
        self.add_health_check_by_params(
            check_id="system_disk",
            name="Disk Usage",
            description="Monitor disk usage",
            check_type=CheckType.SYSTEM,
            check_func=self._check_disk_usage,
            interval=60.0,
            critical=False
        )
    
    async def start(self):
        """Start the health monitoring system."""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._health_monitor_loop())
        self._system_monitor_task = asyncio.create_task(self._system_monitor_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the health monitoring system."""
        self._running = False
        
        # Cancel background tasks
        for task in [self._monitor_task, self._system_monitor_task, self._cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    def add_health_check(self, check: HealthCheck):
        """Add a health check to the monitor."""
        self.health_checks[check.check_id] = check
    
    def add_health_check_by_params(self, check_id: str, name: str, description: str,
                                  check_type: CheckType, check_func: Callable,
                                  timeout: float = 30.0, interval: float = 60.0,
                                  critical: bool = False, dependencies: List[str] = None,
                                  metadata: Dict[str, Any] = None):
        """Add a health check using individual parameters."""
        check = HealthCheck(
            check_id=check_id,
            name=name,
            description=description,
            check_type=check_type,
            check_func=check_func,
            timeout=timeout,
            interval=interval,
            critical=critical,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        self.health_checks[check_id] = check
    
    def remove_health_check(self, check_id: str):
        """Remove a health check from the monitor."""
        if check_id in self.health_checks:
            del self.health_checks[check_id]
    
    async def run_health_check(self, check_id: str) -> Optional[HealthCheckResult]:
        """Run a specific health check."""
        if check_id not in self.health_checks:
            return None
        
        check = self.health_checks[check_id]
        start_time = time.time()
        
        try:
            # Run the check with timeout
            if asyncio.iscoroutinefunction(check.check_func):
                result = await asyncio.wait_for(check.check_func(), timeout=check.timeout)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, check.check_func),
                    timeout=check.timeout
                )
            
            response_time = time.time() - start_time
            
            # Create result
            check_result = HealthCheckResult(
                check_id=check_id,
                timestamp=time.time(),
                status=HealthStatus.HEALTHY if result else HealthStatus.CRITICAL,
                response_time=response_time,
                message="Check completed successfully" if result else "Check failed",
                details={'result': result}
            )
            
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            check_result = HealthCheckResult(
                check_id=check_id,
                timestamp=time.time(),
                status=HealthStatus.CRITICAL,
                response_time=response_time,
                message="Check timed out",
                error="Timeout"
            )
        except Exception as e:
            response_time = time.time() - start_time
            check_result = HealthCheckResult(
                check_id=check_id,
                timestamp=time.time(),
                status=HealthStatus.CRITICAL,
                response_time=response_time,
                message=f"Check failed with error: {str(e)}",
                error=str(e)
            )
        
        # Store result
        self.check_results[check_id].append(check_result)
        
        # Keep only recent results
        if len(self.check_results[check_id]) > 100:
            self.check_results[check_id] = self.check_results[check_id][-50:]
        
        return check_result
    
    async def run_all_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks."""
        results = {}
        
        # Run checks in parallel
        tasks = []
        for check_id in self.health_checks:
            tasks.append(self.run_health_check(check_id))
        
        if tasks:
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(completed_results):
                if isinstance(result, Exception):
                    check_id = list(self.health_checks.keys())[i]
                    results[check_id] = HealthCheckResult(
                        check_id=check_id,
                        timestamp=time.time(),
                        status=HealthStatus.CRITICAL,
                        response_time=0.0,
                        message=f"Check failed with exception: {str(result)}",
                        error=str(result)
                    )
                elif result:
                    results[result.check_id] = result
        
        # Update overall health
        self._update_overall_health()
        
        return results
    
    def _update_overall_health(self):
        """Update the overall health status."""
        if not self.check_results:
            self.overall_health = HealthStatus.UNKNOWN
            return
        
        # Get latest results for each check
        latest_results = {}
        for check_id, results in self.check_results.items():
            if results:
                latest_results[check_id] = results[-1]
        
        if not latest_results:
            self.overall_health = HealthStatus.UNKNOWN
            return
        
        # Count statuses
        status_counts = defaultdict(int)
        for result in latest_results.values():
            status_counts[result.status] += 1
        
        # Determine overall health
        if status_counts[HealthStatus.CRITICAL] > 0:
            self.overall_health = HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > 0:
            self.overall_health = HealthStatus.WARNING
        else:
            self.overall_health = HealthStatus.HEALTHY
        
        self.last_health_update = time.time()
    
    async def _health_monitor_loop(self):
        """Background loop for running health checks."""
        while self._running:
            try:
                await self.run_all_health_checks()
                
                # Wait for next check cycle
                await asyncio.sleep(60.0)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in health monitor loop: {e}")
                await asyncio.sleep(10.0)  # Wait before retrying
    
    async def _system_monitor_loop(self):
        """Background loop for system monitoring."""
        while self._running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(10.0)  # Collect every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in system monitor loop: {e}")
                await asyncio.sleep(30.0)  # Wait before retrying
    
    async def _cleanup_loop(self):
        """Background loop for cleanup tasks."""
        while self._running:
            try:
                await asyncio.sleep(300.0)  # Cleanup every 5 minutes
                self._cleanup_old_data()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_stats = {
                'bytes_sent': network_io.bytes_sent,
                'bytes_recv': network_io.bytes_recv,
                'packets_sent': network_io.packets_sent,
                'packets_recv': network_io.packets_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix-like systems)
            load_average = None
            try:
                load_average = psutil.getloadavg()[0]
            except AttributeError:
                pass  # Not available on Windows
            
            # Create metrics
            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available=memory_available,
                disk_usage_percent=disk_usage_percent,
                network_io=network_stats,
                process_count=process_count,
                load_average=load_average
            )
            
            self.system_metrics.append(metrics)
            
            # Keep only recent metrics
            if len(self.system_metrics) > self.max_metrics_history:
                self.system_metrics = self.system_metrics[-self.max_metrics_history:]
                
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old health check results and metrics."""
        now = time.time()
        cutoff_time = now - 3600  # Keep last hour
        
        # Clean up old check results
        for check_id in list(self.check_results.keys()):
            self.check_results[check_id] = [
                result for result in self.check_results[check_id]
                if result.timestamp > cutoff_time
            ]
            
            # Remove empty check results
            if not self.check_results[check_id]:
                del self.check_results[check_id]
        
        # Clean up old system metrics
        self.system_metrics = [
            metrics for metrics in self.system_metrics
            if metrics.timestamp > cutoff_time
        ]
    
    # Default health check implementations
    def _check_cpu_usage(self) -> bool:
        """Check if CPU usage is within acceptable limits."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            return cpu_percent < 90.0  # Alert if CPU > 90%
        except Exception:
            return False
    
    def _check_memory_usage(self) -> bool:
        """Check if memory usage is within acceptable limits."""
        try:
            memory = psutil.virtual_memory()
            return memory.percent < 85.0  # Alert if memory > 85%
        except Exception:
            return False
    
    def _check_disk_usage(self) -> bool:
        """Check if disk usage is within acceptable limits."""
        try:
            disk = psutil.disk_usage('/')
            return disk.percent < 90.0  # Alert if disk > 90%
        except Exception:
            return False
    
    # Performance profiling methods
    def start_profiling(self, operation_name: str):
        """Start profiling an operation."""
        if operation_name not in self.performance_profiles:
            self.performance_profiles[operation_name] = PerformanceProfile(
                operation_name=operation_name,
                total_calls=0,
                total_time=0.0,
                average_time=0.0,
                min_time=float('inf'),
                max_time=0.0,
                success_count=0,
                failure_count=0
            )
        
        return time.time()
    
    def end_profiling(self, operation_name: str, start_time: float, success: bool = True):
        """End profiling an operation."""
        if operation_name not in self.performance_profiles:
            return
        
        profile = self.performance_profiles[operation_name]
        execution_time = time.time() - start_time
        
        # Update profile
        profile.total_calls += 1
        profile.total_time += execution_time
        profile.average_time = profile.total_time / profile.total_calls
        profile.min_time = min(profile.min_time, execution_time)
        profile.max_time = max(profile.max_time, execution_time)
        profile.last_call = time.time()
        
        if success:
            profile.success_count += 1
        else:
            profile.failure_count += 1
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        return {
            'overall_health': self.overall_health.value,
            'last_update': self.last_health_update,
            'health_checks': {
                check_id: {
                    'name': check.name,
                    'description': check.description,
                    'type': check.check_type.value,
                    'critical': check.critical,
                    'interval': check.interval,
                    'timeout': check.timeout,
                    'latest_result': self.check_results[check_id][-1].__dict__ if self.check_results[check_id] else None
                }
                for check_id, check in self.health_checks.items()
            },
            'system_metrics': {
                'current': self.system_metrics[-1].__dict__ if self.system_metrics else None,
                'history_count': len(self.system_metrics)
            },
            'performance_profiles': {
                name: profile.__dict__
                for name, profile in self.performance_profiles.items()
            }
        }
    
    def get_system_metrics(self, duration_minutes: int = 60) -> List[SystemMetrics]:
        """Get system metrics for the specified duration."""
        if not self.system_metrics:
            return []
        
        cutoff_time = time.time() - (duration_minutes * 60)
        return [
            metrics for metrics in self.system_metrics
            if metrics.timestamp > cutoff_time
        ]
    
    def get_performance_profile(self, operation_name: str) -> Optional[PerformanceProfile]:
        """Get performance profile for a specific operation."""
        return self.performance_profiles.get(operation_name)
