"""
µACP UDP Transport Implementation

Provides UDP-based peer-to-peer transport for µACP agents.
Supports broadcast for discovery and connectionless communication.
"""

import asyncio
import socket
import struct
from typing import Tuple, Optional
from .transport_base import UACPTransport


class UDPTransport(UACPTransport):
    """
    UDP-based P2P transport implementation.
    
    Features:
    - Connectionless peer-to-peer communication
    - Broadcast support for discovery
    - Multicast support for pub/sub
    - Asynchronous non-blocking I/O
    - Ephemeral port support
    """
    
    def __init__(self):
        """Initialize UDP transport."""
        self._socket: Optional[socket.socket] = None
        self._host: str = ""
        self._port: int = 0
        self._running: bool = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    async def bind(self, host: str, port: int) -> bool:
        """
        Bind UDP socket to local address.
        
        Args:
            host: Host address (e.g., "0.0.0.0" for all interfaces)
            port: Port number (0 for ephemeral)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create UDP socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Enable address reuse
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to address
            self._socket.bind((host, port))
            
            # Set non-blocking mode
            self._socket.setblocking(False)
            
            # Get actual bound address (important for ephemeral ports)
            addr = self._socket.getsockname()
            self._host = addr[0] if addr[0] != "0.0.0.0" else "127.0.0.1"
            self._port = addr[1]
            
            # Store event loop for async operations
            self._loop = asyncio.get_event_loop()
            
            self._running = True
            
            return True
            
        except Exception as e:
            print(f"Failed to bind UDP transport to {host}:{port}: {e}")
            if self._socket:
                self._socket.close()
                self._socket = None
            return False
    
    async def send_to_peer(self, data: bytes, peer_host: str, peer_port: int) -> bool:
        """
        Send data to a peer via UDP.
        
        Args:
            data: Binary data to send
            peer_host: Peer's host address
            peer_port: Peer's port number
            
        Returns:
            True if successful, False otherwise
        """
        if not self._socket or not self._running:
            return False
        
        try:
            # Send datagram to peer
            self._socket.sendto(data, (peer_host, peer_port))
            return True
            
        except Exception as e:
            print(f"Failed to send to {peer_host}:{peer_port}: {e}")
            return False
    
    async def receive_from_peer(self, timeout_ms: int) -> Tuple[bytes, str, int]:
        """
        Receive data from any peer.
        
        Args:
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Tuple of (data, sender_host, sender_port)
            Returns (b"", "", 0) on timeout
            
        Raises:
            RuntimeError: If socket not bound
        """
        if not self._socket or not self._running:
            raise RuntimeError("Transport not bound or not running")
        
        if not self._loop:
            raise RuntimeError("Event loop not initialized")
        
        try:
            # Convert timeout to seconds
            timeout_sec = timeout_ms / 1000.0
            
            # Use asyncio with timeout
            data, addr = await asyncio.wait_for(
                self._loop.sock_recvfrom(self._socket, 65536),
                timeout=timeout_sec
            )
            
            return data, addr[0], addr[1]
            
        except asyncio.TimeoutError:
            # Return empty on timeout
            return b"", "", 0
            
        except Exception as e:
            raise RuntimeError(f"Receive error: {e}")
    
    async def enable_broadcast(self) -> bool:
        """
        Enable broadcast for discovery.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._socket:
            return False
        
        try:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            return True
            
        except Exception as e:
            print(f"Failed to enable broadcast: {e}")
            return False
    
    async def enable_multicast(self, group: str, port: int) -> bool:
        """
        Enable multicast group membership.
        
        Args:
            group: Multicast group address (e.g., "224.0.0.1")
            port: Multicast port
            
        Returns:
            True if successful, False otherwise
        """
        if not self._socket:
            return False
        
        try:
            # Join multicast group
            mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            # Enable multicast loopback
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
            
            return True
            
        except Exception as e:
            print(f"Failed to enable multicast for {group}:{port}: {e}")
            return False
    
    def close(self) -> None:
        """
        Close socket and cleanup resources.
        """
        self._running = False
        
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            finally:
                self._socket = None
        
        self._host = ""
        self._port = 0
        self._loop = None
    
    def get_local_port(self) -> int:
        """
        Get bound local port.
        
        Returns:
            Port number (0 if not bound)
        """
        return self._port
    
    def is_bound(self) -> bool:
        """
        Check if transport is bound and ready.
        
        Returns:
            True if bound, False otherwise
        """
        return self._running and self._socket is not None and self._port > 0
    
    def get_local_address(self) -> Tuple[str, int]:
        """
        Get local address (host and port).
        
        Returns:
            Tuple of (host, port)
        """
        return self._host, self._port
    
    def set_timeout(self, timeout_ms: int) -> None:
        """
        Set socket timeout (for compatibility).
        
        Args:
            timeout_ms: Timeout in milliseconds
            
        Note:
            With async I/O, timeout is handled in receive_from_peer().
            This method is provided for compatibility but may not be used.
        """
        if self._socket:
            try:
                self._socket.settimeout(timeout_ms / 1000.0)
            except Exception as e:
                print(f"Failed to set timeout: {e}")
