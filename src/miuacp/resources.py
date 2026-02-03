"""
µACP Resource Binding State Management

This module handles all resource binding state including:
- File descriptors / socket handles
- DMA buffers (on NICs)
- Hardware crypto contexts (accelerator state)
- Persistent storage handles (flash / database)
"""

import asyncio
import time
import uuid
import os
import socket
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque


class ResourceType(Enum):
    """Resource types."""
    FILE_DESCRIPTOR = "file_descriptor"
    SOCKET = "socket"
    DMA_BUFFER = "dma_buffer"
    CRYPTO_CONTEXT = "crypto_context"
    STORAGE_HANDLE = "storage_handle"
    MEMORY_BUFFER = "memory_buffer"


class ResourceState(Enum):
    """Resource states."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    RESERVED = "reserved"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class ResourceHandle:
    """Resource handle information."""
    resource_id: str
    resource_type: ResourceType
    state: ResourceState
    created: float
    last_used: float
    descriptor: Any  # File descriptor, socket, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    cleanup_callback: Optional[Callable] = None


@dataclass
class SocketResource:
    """Socket resource information."""
    socket_id: str
    socket_type: int  # socket.SOCK_STREAM, socket.SOCK_DGRAM, etc.
    family: int       # socket.AF_INET, socket.AF_INET6, etc.
    local_address: Optional[Tuple[str, int]] = None
    remote_address: Optional[Tuple[str, int]] = None
    blocking: bool = True
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DMABuffer:
    """DMA buffer information."""
    buffer_id: str
    size: int
    address: int  # Physical address
    device_id: str
    virtual_address: Optional[int] = None
    flags: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CryptoContext:
    """Hardware crypto context."""
    context_id: str
    algorithm: str
    key_size: int
    device_id: str
    session_id: str
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StorageHandle:
    """Persistent storage handle."""
    handle_id: str
    storage_type: str  # "file", "database", "flash", etc.
    path: str
    mode: str = "r"
    size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class UACPResources:
    """µACP resource binding state management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Resource handles
        self.resources: Dict[str, ResourceHandle] = {}
        self.type_resources: Dict[ResourceType, Set[str]] = defaultdict(set)
        
        # Socket resources
        self.sockets: Dict[str, SocketResource] = {}
        self.socket_handles: Dict[str, str] = {}  # socket -> resource_id
        
        # DMA buffers
        self.dma_buffers: Dict[str, DMABuffer] = {}
        self.device_buffers: Dict[str, Set[str]] = defaultdict(set)
        
        # Crypto contexts
        self.crypto_contexts: Dict[str, CryptoContext] = {}
        self.device_crypto: Dict[str, Set[str]] = defaultdict(set)
        
        # Storage handles
        self.storage_handles: Dict[str, StorageHandle] = {}
        self.path_handles: Dict[str, str] = {}  # path -> handle_id
        
        # Configuration
        self.max_resources = self.config.get('max_resources', 10000)
        self.max_sockets = self.config.get('max_sockets', 1000)
        self.max_dma_buffers = self.config.get('max_dma_buffers', 100)
        self.max_crypto_contexts = self.config.get('max_crypto_contexts', 100)
        self.max_storage_handles = self.config.get('max_storage_handles', 1000)
        
        self.resource_timeout = self.config.get('resource_timeout', 3600.0)  # 1 hour
        self.cleanup_interval = self.config.get('cleanup_interval', 300.0)  # 5 minutes
        
        # State tracking
        self.last_cleanup = time.time()
        self.stats = {
            'resources_created': 0,
            'resources_closed': 0,
            'sockets_created': 0,
            'dma_buffers_allocated': 0,
            'crypto_contexts_created': 0,
            'storage_handles_opened': 0
        }
        
        # Background tasks
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the resource manager."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the resource manager."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clean up all resources
        self._cleanup_all_resources()
    
    # === Resource Handle Management ===
    
    def create_resource(self, resource_type: ResourceType, descriptor: Any,
                        cleanup_callback: Optional[Callable] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new resource handle."""
        if len(self.resources) >= self.max_resources:
            # Remove oldest resource
            oldest = min(self.resources.values(), key=lambda r: r.created)
            self._remove_resource(oldest.resource_id)
        
        resource_id = str(uuid.uuid4())
        now = time.time()
        
        resource = ResourceHandle(
            resource_id=resource_id,
            resource_type=resource_type,
            state=ResourceState.AVAILABLE,
            created=now,
            last_used=now,
            descriptor=descriptor,
            cleanup_callback=cleanup_callback,
            metadata=metadata or {}
        )
        
        self.resources[resource_id] = resource
        self.type_resources[resource_type].add(resource_id)
        
        self.stats['resources_created'] += 1
        return resource_id
    
    def get_resource(self, resource_id: str) -> Optional[ResourceHandle]:
        """Get resource by ID."""
        return self.resources.get(resource_id)
    
    def update_resource_state(self, resource_id: str, new_state: ResourceState) -> bool:
        """Update resource state."""
        if resource_id in self.resources:
            resource = self.resources[resource_id]
            resource.state = new_state
            resource.last_used = time.time()
            return True
        return False
    
    def close_resource(self, resource_id: str) -> bool:
        """Close a resource."""
        return self._remove_resource(resource_id)
    
    def _remove_resource(self, resource_id: str) -> bool:
        """Remove a resource."""
        if resource_id in self.resources:
            resource = self.resources[resource_id]
            
            # Call cleanup callback if available
            if resource.cleanup_callback:
                try:
                    resource.cleanup_callback(resource.descriptor)
                except Exception as e:
                    print(f"Error in resource cleanup callback: {e}")
            
            # Remove from type index
            self.type_resources[resource.resource_type].discard(resource_id)
            
            del self.resources[resource_id]
            self.stats['resources_closed'] += 1
            return True
        
        return False
    
    def get_resources_by_type(self, resource_type: ResourceType) -> List[ResourceHandle]:
        """Get all resources of a specific type."""
        resource_ids = self.type_resources.get(resource_type, set())
        return [self.resources[resource_id] for resource_id in resource_ids 
                if resource_id in self.resources]
    
    # === Socket Resource Management ===
    
    def create_socket(self, socket_type: int, family: int = socket.AF_INET,
                      blocking: bool = True, timeout: Optional[float] = None) -> str:
        """Create a new socket resource."""
        if len(self.sockets) >= self.max_sockets:
            # Remove oldest socket
            oldest = min(self.sockets.values(), key=lambda s: s.created)
            self._remove_socket(oldest.socket_id)
        
        try:
            sock = socket.socket(family, socket_type)
            sock.setblocking(blocking)
            if timeout is not None:
                sock.settimeout(timeout)
        except Exception as e:
            raise RuntimeError(f"Failed to create socket: {e}")
        
        socket_id = str(uuid.uuid4())
        now = time.time()
        
        socket_resource = SocketResource(
            socket_id=socket_id,
            socket_type=socket_type,
            family=family,
            blocking=blocking,
            timeout=timeout
        )
        
        self.sockets[socket_id] = socket_resource
        self.socket_handles[sock] = socket_id
        
        # Create resource handle
        resource_id = self.create_resource(
            ResourceType.SOCKET,
            sock,
            cleanup_callback=self._cleanup_socket,
            metadata={'socket_id': socket_id}
        )
        
        self.stats['sockets_created'] += 1
        return socket_id
    
    def bind_socket(self, socket_id: str, address: Tuple[str, int]) -> bool:
        """Bind a socket to an address."""
        if socket_id in self.sockets:
            socket_resource = self.sockets[socket_id]
            
            # Find the actual socket object
            sock = None
            for s, sid in self.socket_handles.items():
                if sid == socket_id:
                    sock = s
                    break
            
            if sock:
                try:
                    sock.bind(address)
                    socket_resource.local_address = address
                    return True
                except Exception as e:
                    print(f"Failed to bind socket: {e}")
        
        return False
    
    def connect_socket(self, socket_id: str, address: Tuple[str, int]) -> bool:
        """Connect a socket to a remote address."""
        if socket_id in self.sockets:
            socket_resource = self.sockets[socket_id]
            
            # Find the actual socket object
            sock = None
            for s, sid in self.socket_handles.items():
                if sid == socket_id:
                    sock = s
                    break
            
            if sock:
                try:
                    sock.connect(address)
                    socket_resource.remote_address = address
                    return True
                except Exception as e:
                    print(f"Failed to connect socket: {e}")
        
        return False
    
    def _remove_socket(self, socket_id: str) -> bool:
        """Remove a socket resource."""
        if socket_id in self.sockets:
            socket_resource = self.sockets[socket_id]
            
            # Find and close the actual socket
            sock_to_remove = None
            for sock, sid in self.socket_handles.items():
                if sid == socket_id:
                    sock_to_remove = sock
                    break
            
            if sock_to_remove:
                try:
                    sock_to_remove.close()
                except Exception:
                    pass
                del self.socket_handles[sock_to_remove]
            
            del self.sockets[socket_id]
            return True
        
        return False
    
    def _cleanup_socket(self, sock: socket.socket):
        """Cleanup callback for socket resources."""
        try:
            sock.close()
        except Exception:
            pass
    
    # === DMA Buffer Management ===
    
    def allocate_dma_buffer(self, size: int, device_id: str, flags: int = 0) -> str:
        """Allocate a DMA buffer."""
        if len(self.dma_buffers) >= self.max_dma_buffers:
            # Remove oldest buffer
            oldest = min(self.dma_buffers.values(), key=lambda b: b.created)
            self._remove_dma_buffer(oldest.buffer_id)
        
        buffer_id = str(uuid.uuid4())
        now = time.time()
        
        # Simulate DMA buffer allocation
        # In a real implementation, this would use hardware-specific APIs
        dma_buffer = DMABuffer(
            buffer_id=buffer_id,
            size=size,
            address=hash(f"{device_id}_{buffer_id}") % 0x100000000,  # Simulated physical address
            device_id=device_id,
            flags=flags
        )
        
        self.dma_buffers[buffer_id] = dma_buffer
        self.device_buffers[device_id].add(buffer_id)
        
        self.stats['dma_buffers_allocated'] += 1
        return buffer_id
    
    def get_dma_buffer(self, buffer_id: str) -> Optional[DMABuffer]:
        """Get DMA buffer by ID."""
        return self.dma_buffers.get(buffer_id)
    
    def free_dma_buffer(self, buffer_id: str) -> bool:
        """Free a DMA buffer."""
        return self._remove_dma_buffer(buffer_id)
    
    def _remove_dma_buffer(self, buffer_id: str) -> bool:
        """Remove a DMA buffer."""
        if buffer_id in self.dma_buffers:
            dma_buffer = self.dma_buffers[buffer_id]
            
            # Remove from device index
            if dma_buffer.device_id in self.device_buffers:
                self.device_buffers[dma_buffer.device_id].discard(buffer_id)
            
            del self.dma_buffers[buffer_id]
            return True
        
        return False
    
    # === Crypto Context Management ===
    
    def create_crypto_context(self, algorithm: str, key_size: int, device_id: str) -> str:
        """Create a hardware crypto context."""
        if len(self.crypto_contexts) >= self.max_crypto_contexts:
            # Remove oldest context
            oldest = min(self.crypto_contexts.values(), key=lambda c: c.created)
            self._remove_crypto_context(oldest.context_id)
        
        context_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        now = time.time()
        
        crypto_context = CryptoContext(
            context_id=context_id,
            algorithm=algorithm,
            key_size=key_size,
            device_id=device_id,
            session_id=session_id
        )
        
        self.crypto_contexts[context_id] = crypto_context
        self.device_crypto[device_id].add(context_id)
        
        self.stats['crypto_contexts_created'] += 1
        return context_id
    
    def get_crypto_context(self, context_id: str) -> Optional[CryptoContext]:
        """Get crypto context by ID."""
        return self.crypto_contexts.get(context_id)
    
    def destroy_crypto_context(self, context_id: str) -> bool:
        """Destroy a crypto context."""
        return self._remove_crypto_context(context_id)
    
    def _remove_crypto_context(self, context_id: str) -> bool:
        """Remove a crypto context."""
        if context_id in self.crypto_contexts:
            crypto_context = self.crypto_contexts[context_id]
            
            # Remove from device index
            if crypto_context.device_id in self.device_crypto:
                self.device_crypto[crypto_context.device_id].discard(context_id)
            
            del self.crypto_contexts[context_id]
            return True
        
        return False
    
    # === Storage Handle Management ===
    
    def open_storage(self, storage_type: str, path: str, mode: str = "r") -> str:
        """Open a storage handle."""
        if len(self.storage_handles) >= self.max_storage_handles:
            # Remove oldest handle
            oldest = min(self.storage_handles.values(), key=lambda h: h.created)
            self._remove_storage_handle(oldest.handle_id)
        
        handle_id = str(uuid.uuid4())
        now = time.time()
        
        # Get file size if it's a file
        size = None
        if storage_type == "file" and os.path.exists(path):
            try:
                size = os.path.getsize(path)
            except Exception:
                pass
        
        storage_handle = StorageHandle(
            handle_id=handle_id,
            storage_type=storage_type,
            path=path,
            mode=mode,
            size=size
        )
        
        self.storage_handles[handle_id] = storage_handle
        self.path_handles[path] = handle_id
        
        self.stats['storage_handles_opened'] += 1
        return handle_id
    
    def get_storage_handle(self, handle_id: str) -> Optional[StorageHandle]:
        """Get storage handle by ID."""
        return self.storage_handles.get(handle_id)
    
    def close_storage(self, handle_id: str) -> bool:
        """Close a storage handle."""
        return self._remove_storage_handle(handle_id)
    
    def _remove_storage_handle(self, handle_id: str) -> bool:
        """Remove a storage handle."""
        if handle_id in self.storage_handles:
            storage_handle = self.storage_handles[handle_id]
            
            # Remove from path index
            if storage_handle.path in self.path_handles:
                del self.path_handles[storage_handle.path]
            
            del self.storage_handles[handle_id]
            return True
        
        return False
    
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
    
    def _cleanup_expired(self):
        """Clean up expired resources."""
        now = time.time()
        
        # Clean up expired resources
        expired_resources = [
            resource_id for resource_id, resource in self.resources.items()
            if now - resource.last_used > self.resource_timeout
        ]
        
        for resource_id in expired_resources:
            self._remove_resource(resource_id)
        
        self.last_cleanup = now
    
    def _cleanup_all_resources(self):
        """Clean up all resources on shutdown."""
        # Close all sockets
        for socket_id in list(self.sockets.keys()):
            self._remove_socket(socket_id)
        
        # Free all DMA buffers
        for buffer_id in list(self.dma_buffers.keys()):
            self._remove_dma_buffer(buffer_id)
        
        # Destroy all crypto contexts
        for context_id in list(self.crypto_contexts.keys()):
            self._remove_crypto_context(context_id)
        
        # Close all storage handles
        for handle_id in list(self.storage_handles.keys()):
            self._remove_storage_handle(handle_id)
        
        # Close all resource handles
        for resource_id in list(self.resources.keys()):
            self._remove_resource(resource_id)
    
    # === Statistics and Export ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get resource statistics."""
        return {
            **self.stats,
            'current_resources': len(self.resources),
            'current_sockets': len(self.sockets),
            'current_dma_buffers': len(self.dma_buffers),
            'current_crypto_contexts': len(self.crypto_contexts),
            'current_storage_handles': len(self.storage_handles),
            'last_cleanup': self.last_cleanup
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export current resource state."""
        return {
            'resources': {
                resource_id: {
                    'type': resource.resource_type.value,
                    'state': resource.state.value,
                    'created': resource.created,
                    'last_used': resource.last_used
                }
                for resource_id, resource in self.resources.items()
            },
            'sockets': {
                socket_id: {
                    'socket_type': socket_resource.socket_type,
                    'family': socket_resource.family,
                    'local_address': socket_resource.local_address,
                    'remote_address': socket_resource.remote_address
                }
                for socket_id, socket_resource in self.sockets.items()
            },
            'dma_buffers': {
                buffer_id: {
                    'size': buffer.size,
                    'device_id': buffer.device_id,
                    'flags': buffer.flags
                }
                for buffer_id, buffer in self.dma_buffers.items()
            },
            'crypto_contexts': {
                context_id: {
                    'algorithm': context.algorithm,
                    'key_size': context.key_size,
                    'device_id': context.device_id
                }
                for context_id, context in self.crypto_contexts.items()
            },
            'storage_handles': {
                handle_id: {
                    'storage_type': handle.storage_type,
                    'path': handle.path,
                    'mode': handle.mode,
                    'size': handle.size
                }
                for handle_id, handle in self.storage_handles.items()
            },
            'stats': self.get_stats()
        }
