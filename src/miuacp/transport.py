"""
µACP Transport Layer Implementation

Provides UDP/TCP transport with:
- Connection management
- Network discovery
- Reliability mechanisms
- Connection pooling
"""

import asyncio
import socket
import struct
import time
import threading
from typing import Dict, List, Optional, Callable, Union, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from .protocol import UACPMessage, UACPHeader, UACPVerb


class TransportType(Enum):
    """Transport protocol types."""
    UDP = "udp"
    TCP = "tcp"
    UDP_MULTICAST = "udp_multicast"


@dataclass
class TransportConfig:
    """Transport configuration."""
    transport_type: TransportType = TransportType.UDP
    host: str = "0.0.0.0"
    port: int = 8888
    multicast_group: Optional[str] = None
    tcp_keepalive: bool = True
    tcp_nodelay: bool = True
    connection_timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    max_connections: int = 100
    buffer_size: int = 8192


@dataclass
class ConnectionInfo:
    """Connection information."""
    host: str
    port: int
    transport_type: TransportType
    socket: socket.socket
    last_activity: float
    message_count: int = 0
    error_count: int = 0
    is_connected: bool = True


class UACPTransport:
    """µACP transport layer implementation."""
    
    def __init__(self, config: TransportConfig):
        self.config = config
        self.connections: Dict[str, ConnectionInfo] = {}
        self.listeners: Dict[str, asyncio.Task] = {}
        self.message_handlers: List[Callable] = []
        self.connection_handlers: List[Callable] = []
        self.running = False
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'connections_active': 0,
            'connection_errors': 0,
            'network_errors': 0
        }
    
    async def start(self):
        """Start the transport layer."""
        if self.running:
            return
        
        self.running = True
        
        # Start listeners based on transport type
        if self.config.transport_type == TransportType.UDP:
            await self._start_udp_listener()
        elif self.config.transport_type == TransportType.TCP:
            await self._start_tcp_listener()
        elif self.config.transport_type == TransportType.UDP_MULTICAST:
            await self._start_multicast_listener()
        
        # Start background tasks
        asyncio.create_task(self._connection_monitor())
        asyncio.create_task(self._stats_reporter())
        
        print(f"µACP Transport started on {self.config.host}:{self.config.port} ({self.config.transport_type.value})")
    
    async def stop(self):
        """Stop the transport layer."""
        if not self.running:
            return
        
        self.running = False
        
        # Stop all listeners
        for task in self.listeners.values():
            task.cancel()
        
        # Close all connections
        for conn in self.connections.values():
            conn.socket.close()
        
        self.connections.clear()
        self.listeners.clear()
        
        print("µACP Transport stopped")
    
    async def _start_udp_listener(self):
        """Start UDP listener."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.config.host, self.config.port))
            sock.settimeout(1.0)
            
            task = asyncio.create_task(self._udp_receive_loop(sock))
            self.listeners['udp'] = task
            
        except Exception as e:
            print(f"Failed to start UDP listener: {e}")
            raise
    
    async def _start_tcp_listener(self):
        """Start TCP listener."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.config.host, self.config.port))
            sock.listen(self.config.max_connections)
            sock.settimeout(1.0)
            
            task = asyncio.create_task(self._tcp_accept_loop(sock))
            self.listeners['tcp'] = task
            
        except Exception as e:
            print(f"Failed to start TCP listener: {e}")
            raise
    
    async def _start_multicast_listener(self):
        """Start UDP multicast listener."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.config.port))
            
            # Join multicast group
            if self.config.multicast_group:
                mreq = struct.pack("4sl", socket.inet_aton(self.config.multicast_group), socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            sock.settimeout(1.0)
            
            task = asyncio.create_task(self._udp_receive_loop(sock))
            self.listeners['multicast'] = task
            
        except Exception as e:
            print(f"Failed to start multicast listener: {e}")
            raise
    
    async def _udp_receive_loop(self, sock: socket.socket):
        """UDP receive loop."""
        while self.running:
            try:
                data, addr = sock.recvfrom(self.config.buffer_size)
                host, port = addr
                
                # Parse message
                try:
                    message = UACPMessage.unpack(data)
                    await self._handle_message(message, host, port)
                    self.stats['messages_received'] += 1
                except Exception as e:
                    print(f"Failed to parse UDP message from {host}:{port}: {e}")
                    self.stats['network_errors'] += 1
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"UDP receive error: {e}")
                    self.stats['network_errors'] += 1
                    await asyncio.sleep(1.0)
    
    async def _tcp_accept_loop(self, sock: socket.socket):
        """TCP accept loop."""
        while self.running:
            try:
                client_sock, addr = sock.accept()
                host, port = addr
                
                # Configure client socket
                client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                if self.config.tcp_keepalive:
                    client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                
                # Start client handler
                asyncio.create_task(self._tcp_client_handler(client_sock, host, port))
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"TCP accept error: {e}")
                    await asyncio.sleep(1.0)
    
    async def _tcp_client_handler(self, client_sock: socket.socket, host: str, port: int):
        """Handle TCP client connection."""
        connection_key = f"{host}:{port}"
        
        try:
            # Create connection info
            conn_info = ConnectionInfo(
                host=host,
                port=port,
                transport_type=TransportType.TCP,
                socket=client_sock,
                last_activity=time.time()
            )
            
            self.connections[connection_key] = conn_info
            self.stats['connections_active'] += 1
            
            # Call connection handlers
            for handler in self.connection_handlers:
                try:
                    await handler(conn_info, 'connected')
                except Exception as e:
                    print(f"Connection handler error: {e}")
            
            # Receive loop
            while self.running and conn_info.is_connected:
                try:
                    data = client_sock.recv(self.config.buffer_size)
                    if not data:
                        break
                    
                    # Parse message
                    try:
                        message = UACPMessage.unpack(data)
                        await self._handle_message(message, host, port)
                        conn_info.message_count += 1
                        conn_info.last_activity = time.time()
                        self.stats['messages_received'] += 1
                    except Exception as e:
                        print(f"Failed to parse TCP message: {e}")
                        conn_info.error_count += 1
                        self.stats['network_errors'] += 1
                
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"TCP client receive error: {e}")
                    break
            
        except Exception as e:
            print(f"TCP client handler error: {e}")
            conn_info.error_count += 1
            self.stats['connection_errors'] += 1
        
        finally:
            # Cleanup
            if connection_key in self.connections:
                del self.connections[connection_key]
                self.stats['connections_active'] -= 1
            
            client_sock.close()
            
            # Call disconnection handlers
            for handler in self.connection_handlers:
                try:
                    await handler(conn_info, 'disconnected')
                except Exception as e:
                    print(f"Disconnection handler error: {e}")
    
    async def _handle_message(self, message: UACPMessage, host: str, port: int):
        """Handle incoming message."""
        for handler in self.message_handlers:
            try:
                await handler(message, host, port)
            except Exception as e:
                print(f"Message handler error: {e}")
    
    async def send_message(self, host: str, port: int, message: UACPMessage, 
                          transport_type: Optional[TransportType] = None) -> bool:
        """Send message to remote host."""
        transport = transport_type or self.config.transport_type
        
        try:
            if transport == TransportType.UDP:
                return await self._send_udp(host, port, message)
            elif transport == TransportType.TCP:
                return await self._send_tcp(host, port, message)
            else:
                print(f"Unsupported transport type: {transport}")
                return False
                
        except Exception as e:
            print(f"Send error to {host}:{port}: {e}")
            self.stats['network_errors'] += 1
            return False
    
    async def _send_udp(self, host: str, port: int, message: UACPMessage) -> bool:
        """Send message via UDP."""
        try:
            # Create temporary socket for sending
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5.0)
            
            data = message.pack()
            sock.sendto(data, (host, port))
            sock.close()
            
            self.stats['messages_sent'] += 1
            return True
            
        except Exception as e:
            print(f"UDP send error: {e}")
            return False
    
    async def _send_tcp(self, host: str, port: int, message: UACPMessage) -> bool:
        """Send message via TCP."""
        connection_key = f"{host}:{port}"
        
        try:
            # Check if connection exists
            if connection_key not in self.connections:
                # Create new connection
                if not await self._create_tcp_connection(host, port):
                    return False
            
            conn_info = self.connections[connection_key]
            
            # Send message
            data = message.pack()
            conn_info.socket.send(data)
            
            conn_info.message_count += 1
            conn_info.last_activity = time.time()
            self.stats['messages_sent'] += 1
            
            return True
            
        except Exception as e:
            print(f"TCP send error: {e}")
            # Mark connection as failed
            if connection_key in self.connections:
                self.connections[connection_key].is_connected = False
            return False
    
    async def _create_tcp_connection(self, host: str, port: int) -> bool:
        """Create TCP connection."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.connection_timeout)
            sock.connect((host, port))
            
            # Configure socket
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            if self.config.tcp_keepalive:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            # Create connection info
            conn_info = ConnectionInfo(
                host=host,
                port=port,
                transport_type=TransportType.TCP,
                socket=sock,
                last_activity=time.time()
            )
            
            connection_key = f"{host}:{port}"
            self.connections[connection_key] = conn_info
            self.stats['connections_active'] += 1
            
            return True
            
        except Exception as e:
            print(f"Failed to create TCP connection to {host}:{port}: {e}")
            self.stats['connection_errors'] += 1
            return False
    
    async def _connection_monitor(self):
        """Monitor connection health."""
        while self.running:
            try:
                current_time = time.time()
                expired_connections = []
                
                for key, conn in self.connections.items():
                    # Check connection timeout
                    if current_time - conn.last_activity > self.config.connection_timeout:
                        expired_connections.append(key)
                    # Check TCP connection health
                    elif conn.transport_type == TransportType.TCP:
                        try:
                            # Send keepalive
                            conn.socket.send(b'')
                        except:
                            expired_connections.append(key)
                
                # Remove expired connections
                for key in expired_connections:
                    conn = self.connections[key]
                    conn.socket.close()
                    del self.connections[key]
                    self.stats['connections_active'] -= 1
                
                await asyncio.sleep(10.0)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Connection monitor error: {e}")
                await asyncio.sleep(5.0)
    
    async def _stats_reporter(self):
        """Report transport statistics."""
        while self.running:
            try:
                print(f"\nTransport Stats: {self.stats['connections_active']} connections, "
                      f"{self.stats['messages_sent']} sent, {self.stats['messages_received']} received")
                await asyncio.sleep(30.0)  # Report every 30 seconds
                
            except Exception as e:
                print(f"Stats reporter error: {e}")
                await asyncio.sleep(30.0)
    
    def add_message_handler(self, handler: Callable):
        """Add message handler."""
        self.message_handlers.append(handler)
    
    def add_connection_handler(self, handler: Callable):
        """Add connection handler."""
        self.connection_handlers.append(handler)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get connection information."""
        connections = []
        for key, conn in self.connections.items():
            connections.append({
                'key': key,
                'host': conn.host,
                'port': conn.port,
                'transport': conn.transport_type.value,
                'messages': conn.message_count,
                'errors': conn.error_count,
                'last_activity': conn.last_activity,
                'connected': conn.is_connected
            })
        return connections
    
    def get_stats(self) -> Dict[str, Any]:
        """Get transport statistics."""
        return self.stats.copy()
