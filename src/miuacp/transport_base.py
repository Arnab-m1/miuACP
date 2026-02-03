"""
µACP Transport Abstraction Layer

Provides an abstract interface for transport implementations, enabling
peer-to-peer communication with different protocols (UDP, TCP, etc).

This allows agents to communicate symmetrically without client/server distinction.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional


class UACPTransport(ABC):
    """
    Abstract base class for µACP transport implementations.
    
    Defines the interface for peer-to-peer communication transports.
    All transports must implement these methods to enable symmetric
    agent-to-agent communication.
    """
    
    @abstractmethod
    async def bind(self, host: str, port: int) -> bool:
        """
        Bind transport to local address.
        
        Args:
            host: Host address to bind to (e.g., "0.0.0.0" for all interfaces)
            port: Port number (0 for ephemeral port assignment)
            
        Returns:
            True if bind successful, False otherwise
            
        Note:
            If port is 0, the OS will assign an ephemeral port.
            Use get_local_port() to retrieve the actual port.
        """
        pass
    
    @abstractmethod
    async def send_to_peer(self, data: bytes, peer_host: str, peer_port: int) -> bool:
        """
        Send data to a peer.
        
        Args:
            data: Binary data to send
            peer_host: Peer's host address
            peer_port: Peer's port number
            
        Returns:
            True if send successful, False otherwise
            
        Note:
            This is a direct send - no connection establishment required.
            The transport handles all protocol-specific details.
        """
        pass
    
    @abstractmethod
    async def receive_from_peer(self, timeout_ms: int) -> Tuple[bytes, str, int]:
        """
        Receive data from any peer.
        
        Args:
            timeout_ms: Timeout in milliseconds (0 for non-blocking)
            
        Returns:
            Tuple of (data, sender_host, sender_port)
            Returns (b"", "", 0) on timeout
            
        Raises:
            RuntimeError: If transport not bound or other error
            
        Note:
            This receives from ANY peer, not just a specific one.
            The caller learns the sender from the return value.
        """
        pass
    
    @abstractmethod
    async def enable_broadcast(self) -> bool:
        """
        Enable broadcast capability for discovery.
        
        Returns:
            True if broadcast enabled, False otherwise
            
        Note:
            Required for sending to broadcast addresses (e.g., 255.255.255.255)
            Used for peer discovery in local networks.
        """
        pass
    
    @abstractmethod
    async def enable_multicast(self, group: str, port: int) -> bool:
        """
        Enable multicast for topic-based pub/sub.
        
        Args:
            group: Multicast group address (e.g., "224.0.0.1")
            port: Multicast port
            
        Returns:
            True if multicast enabled, False otherwise
            
        Note:
            Allows efficient one-to-many communication for topics.
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        Close transport and release resources.
        
        Must be called to properly cleanup sockets and other resources.
        After closing, the transport cannot be used again.
        """
        pass
    
    @abstractmethod
    def get_local_port(self) -> int:
        """
        Get the actual bound local port.
        
        Returns:
            Port number (may be ephemeral if bind() was called with port=0)
            
        Note:
            Should be called after bind() to get the actual port,
            especially when using ephemeral port assignment.
        """
        pass
    
    def is_bound(self) -> bool:
        """
        Check if transport is bound and ready.
        
        Returns:
            True if bound, False otherwise
            
        Note:
            This is a convenience method. Implementations should override
            if they have a more efficient way to check binding status.
        """
        return self.get_local_port() > 0
