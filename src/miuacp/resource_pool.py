"""
Resource Pooling Implementation for µACP

Provides efficient resource management and pooling for lightweight AI agent communications.
"""

import time
import asyncio
from typing import Optional, Dict, Any, List, Callable, Generic, TypeVar, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class PoolState(Enum):
    """Resource pool states."""
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    OVERFLOW = "OVERFLOW"


class ResourceType(Enum):
    """Types of resources that can be pooled."""
    CONNECTION = "CONNECTION"
    MEMORY_BUFFER = "MEMORY_BUFFER"
    THREAD = "THREAD"
    SOCKET = "SOCKET"
    CRYPTO_CONTEXT = "CRYPTO_CONTEXT"
    STORAGE_HANDLE = "STORAGE_HANDLE"


T = TypeVar('T')


@dataclass
class PoolConfig:
    """Configuration for resource pool."""
    min_size: int = 5
    max_size: int = 100
    initial_size: int = 10
    acquire_timeout: float = 30.0
    health_check_interval: float = 60.0
    cleanup_interval: float = 300.0
    max_idle_time: float = 600.0  # 10 minutes
    enable_metrics: bool = True


@dataclass
class PoolMetrics:
    """Metrics for resource pool monitoring."""
    total_created: int = 0
    total_acquired: int = 0
    total_released: int = 0
    total_destroyed: int = 0
    current_available: int = 0
    current_in_use: int = 0
    current_total: int = 0
    acquire_wait_time: float = 0.0
    last_health_check: Optional[float] = None
    health_status: PoolState = PoolState.HEALTHY


@dataclass
class PooledResource(Generic[T]):
    """A resource managed by the pool."""
    resource_id: str
    resource: T
    created_time: float
    last_used_time: float
    use_count: int = 0
    is_healthy: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResourcePool(Generic[T]):
    """
    Generic resource pool for efficient resource management.
    
    Provides:
    - Resource pooling and reuse
    - Health monitoring
    - Automatic cleanup
    - Load balancing
    - Performance metrics
    """
    
    def __init__(self, 
                 resource_factory: Callable[[], T],
                 resource_cleanup: Optional[Callable[[T], None]] = None,
                 resource_health_check: Optional[Callable[[T], bool]] = None,
                 config: Optional[PoolConfig] = None):
        
        self.resource_factory = resource_factory
        self.resource_cleanup = resource_cleanup
        self.resource_health_check = resource_health_check
        self.config = config or PoolConfig()
        
        # Resource storage
        self.available_resources: deque[PooledResource[T]] = deque()
        self.in_use_resources: Dict[str, PooledResource[T]] = {}
        self.all_resources: Dict[str, PooledResource[T]] = {}
        
        # Metrics and state
        self.metrics = PoolMetrics()
        self.state = PoolState.HEALTHY
        self.last_cleanup = time.time()
        
        # Background tasks
        self._running = False
        self._health_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Initialize pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the pool with initial resources."""
        for _ in range(self.config.initial_size):
            self._create_resource()
    
    async def start(self):
        """Start the resource pool management."""
        if self._running:
            return
        
        self._running = True
        self._health_task = asyncio.create_task(self._health_check_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the resource pool management."""
        self._running = False
        
        # Cancel background tasks
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clean up all resources
        self._cleanup_all_resources()
    
    def acquire(self, timeout: Optional[float] = None) -> Optional[T]:
        """Acquire a resource from the pool."""
        start_time = time.time()
        timeout = timeout or self.config.acquire_timeout
        
        # Try to get an available resource
        while time.time() - start_time < timeout:
            if self.available_resources:
                pooled_resource = self.available_resources.popleft()
                
                # Check if resource is still healthy
                if self._is_resource_healthy(pooled_resource):
                    self._mark_resource_in_use(pooled_resource)
                    return pooled_resource.resource
                else:
                    # Resource is unhealthy, destroy it and try again
                    self._destroy_resource(pooled_resource)
                    continue
            
            # No available resources, try to create more
            if len(self.all_resources) < self.config.max_size:
                self._create_resource()
                continue
            
            # Wait a bit before trying again
            time.sleep(0.1)
        
        # Timeout reached
        return None
    
    def release(self, resource: T):
        """Release a resource back to the pool."""
        # Find the pooled resource
        pooled_resource = None
        for pr in self.in_use_resources.values():
            if pr.resource == resource:
                pooled_resource = pr
                break
        
        if not pooled_resource:
            return  # Resource not found in pool
        
        # Update resource state
        pooled_resource.last_used_time = time.time()
        pooled_resource.use_count += 1
        
        # Remove from in-use and add to available
        del self.in_use_resources[pooled_resource.resource_id]
        self.available_resources.append(pooled_resource)
        
        # Update metrics
        self.metrics.total_released += 1
        self.metrics.current_in_use = len(self.in_use_resources)
        self.metrics.current_available = len(self.available_resources)
    
    def _create_resource(self):
        """Create a new resource and add it to the pool."""
        try:
            resource = self.resource_factory()
            resource_id = f"resource_{len(self.all_resources)}_{int(time.time())}"
            
            pooled_resource = PooledResource(
                resource_id=resource_id,
                resource=resource,
                created_time=time.time(),
                last_used_time=time.time()
            )
            
            self.all_resources[resource_id] = pooled_resource
            self.available_resources.append(pooled_resource)
            
            # Update metrics
            self.metrics.total_created += 1
            self.metrics.current_total = len(self.all_resources)
            self.metrics.current_available = len(self.available_resources)
            
        except Exception as e:
            print(f"Failed to create resource: {e}")
    
    def _destroy_resource(self, pooled_resource: PooledResource[T]):
        """Destroy a resource and remove it from the pool."""
        try:
            # Clean up the resource
            if self.resource_cleanup:
                self.resource_cleanup(pooled_resource.resource)
            
            # Remove from all collections
            if pooled_resource.resource_id in self.all_resources:
                del self.all_resources[pooled_resource.resource_id]
            
            if pooled_resource.resource_id in self.in_use_resources:
                del self.in_use_resources[pooled_resource.resource_id]
            
            # Update metrics
            self.metrics.total_destroyed += 1
            self.metrics.current_total = len(self.all_resources)
            self.metrics.current_in_use = len(self.in_use_resources)
            self.metrics.current_available = len(self.available_resources)
            
        except Exception as e:
            print(f"Failed to destroy resource: {e}")
    
    def _mark_resource_in_use(self, pooled_resource: PooledResource[T]):
        """Mark a resource as in use."""
        self.in_use_resources[pooled_resource.resource_id] = pooled_resource
        self.metrics.total_acquired += 1
        self.metrics.current_in_use = len(self.in_use_resources)
        self.metrics.current_available = len(self.available_resources)
    
    def _is_resource_healthy(self, pooled_resource: PooledResource[T]) -> bool:
        """Check if a resource is healthy."""
        if self.resource_health_check:
            try:
                pooled_resource.is_healthy = self.resource_health_check(pooled_resource.resource)
                return pooled_resource.is_healthy
            except Exception:
                pooled_resource.is_healthy = False
                return False
        return True
    
    async def _health_check_loop(self):
        """Background loop for health checking."""
        while self._running:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in health check loop: {e}")
    
    def _perform_health_check(self):
        """Perform health check on all resources."""
        self.metrics.last_health_check = time.time()
        
        # Check available resources
        healthy_count = 0
        total_count = len(self.available_resources)
        
        for pooled_resource in list(self.available_resources):
            if self._is_resource_healthy(pooled_resource):
                healthy_count += 1
            else:
                # Remove unhealthy resource
                self.available_resources.remove(pooled_resource)
                self._destroy_resource(pooled_resource)
        
        # Update health status
        if total_count == 0:
            self.state = PoolState.HEALTHY
        elif healthy_count / total_count < 0.5:
            self.state = PoolState.CRITICAL
        elif healthy_count / total_count < 0.8:
            self.state = PoolState.WARNING
        else:
            self.state = PoolState.HEALTHY
        
        self.metrics.health_status = self.state
        
        # Create new resources if needed
        while (len(self.all_resources) < self.config.min_size and 
               len(self.all_resources) < self.config.max_size):
            self._create_resource()
    
    async def _cleanup_loop(self):
        """Background loop for resource cleanup."""
        while self._running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                self._cleanup_expired_resources()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
    
    def _cleanup_expired_resources(self):
        """Clean up expired resources."""
        now = time.time()
        expired_resources = []
        
        # Check available resources for expiration
        for pooled_resource in self.available_resources:
            if (now - pooled_resource.last_used_time) > self.config.max_idle_time:
                expired_resources.append(pooled_resource)
        
        # Remove expired resources
        for pooled_resource in expired_resources:
            self.available_resources.remove(pooled_resource)
            self._destroy_resource(pooled_resource)
        
        # Update last cleanup time
        self.last_cleanup = now
    
    def _cleanup_all_resources(self):
        """Clean up all resources on shutdown."""
        # Clean up available resources
        for pooled_resource in list(self.available_resources):
            self._destroy_resource(pooled_resource)
        
        # Clean up in-use resources
        for pooled_resource in list(self.in_use_resources.values()):
            self._destroy_resource(pooled_resource)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pool statistics and health information."""
        return {
            'config': {
                'min_size': self.config.min_size,
                'max_size': self.config.max_size,
                'initial_size': self.config.initial_size,
                'acquire_timeout': self.config.acquire_timeout,
                'health_check_interval': self.config.health_check_interval,
                'cleanup_interval': self.config.cleanup_interval,
                'max_idle_time': self.config.max_idle_time
            },
            'metrics': {
                'total_created': self.metrics.total_created,
                'total_acquired': self.metrics.total_acquired,
                'total_released': self.metrics.total_released,
                'total_destroyed': self.metrics.total_destroyed,
                'current_available': self.metrics.current_available,
                'current_in_use': self.metrics.current_in_use,
                'current_total': self.metrics.current_total,
                'last_health_check': self.metrics.last_health_check,
                'health_status': self.metrics.health_status.value
            },
            'state': self.state.value,
            'last_cleanup': self.last_cleanup
        }
    
    def resize(self, new_min_size: int, new_max_size: int):
        """Resize the resource pool."""
        self.config.min_size = max(1, new_min_size)
        self.config.max_size = max(self.config.min_size, new_max_size)
        
        # Ensure current size is within new bounds
        while len(self.all_resources) < self.config.min_size:
            self._create_resource()
        
        # Note: Resources will be cleaned up gradually in cleanup loop
        # if they exceed the new max_size


class PoolManager:
    """
    Manages multiple resource pools for different resource types.
    """
    
    def __init__(self):
        self.pools: Dict[str, ResourcePool] = {}
        self._running = False
    
    async def start(self):
        """Start all resource pools."""
        self._running = True
        for pool in self.pools.values():
            await pool.start()
    
    async def stop(self):
        """Stop all resource pools."""
        self._running = False
        for pool in self.pools.values():
            await pool.stop()
    
    def create_pool(self, name: str, pool: ResourcePool):
        """Create a new resource pool."""
        self.pools[name] = pool
        if self._running:
            asyncio.create_task(pool.start())
    
    def get_pool(self, name: str) -> Optional[ResourcePool]:
        """Get a resource pool by name."""
        return self.pools.get(name)
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools."""
        return {
            name: pool.get_statistics() 
            for name, pool in self.pools.items()
        }
