"""
µACP Client Implementation

Provides client-side functionality for:
- Sending messages to agents
- Managing connections and retransmissions
- Handling responses and timeouts
- Connection pooling and reliability
"""

import asyncio
import socket
import time
import uuid
from typing import Dict, List, Optional, Callable, Union, Any, Tuple
from dataclasses import dataclass
from .protocol import (
    UACPProtocol, UACPMessage, UACPHeader, UACPOption, 
    UACPOptionType, UACPVerb, UACPContentType
)


@dataclass
class UACPConnection:
    """µACP connection to a remote agent."""
    host: str
    port: int
    socket: socket.socket
    last_activity: float
    message_id_counter: int = 0
    
    def next_message_id(self) -> int:
        """Get next unique message ID."""
        self.message_id_counter += 1
        return self.message_id_counter


@dataclass
class UACPRequest:
    """Pending request waiting for response."""
    message: UACPMessage
    timestamp: float
    timeout: float
    future: asyncio.Future
    retries: int = 0


class UACPClient:
    """µACP client for communicating with agents."""
    
    def __init__(self, 
                 default_timeout: float = 30.0,
                 max_retries: int = 3,
                 connection_pool_size: int = 10):
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.connection_pool_size = connection_pool_size
        
        # Connection management
        self.connections: Dict[str, UACPConnection] = {}
        self.pending_requests: Dict[int, UACPRequest] = {}
        
        # Event handlers
        self.message_handlers: Dict[UACPVerb, List[Callable]] = {
            verb: [] for verb in UACPVerb
        }
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'requests_timeout': 0,
            'connection_errors': 0
        }
    
    async def connect(self, host: str, port: int) -> bool:
        """Connect to a remote agent."""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5.0)  # 5 second connection timeout
            
            # Test connection with PING
            ping_msg = UACPProtocol.create_ping(1)
            sock.sendto(ping_msg.pack(), (host, port))
            
            # Wait for response
            try:
                sock.settimeout(2.0)
                data, addr = sock.recvfrom(1024)
                response = UACPMessage.unpack(data)
                
                if response.header.verb == UACPVerb.PING and response.header.code == 0:
                    # Connection successful
                    connection = UACPConnection(
                        host=host,
                        port=port,
                        socket=sock,
                        last_activity=time.time()
                    )
                    
                    connection_key = f"{host}:{port}"
                    self.connections[connection_key] = connection
                    
                    # Start background task for receiving responses
                    asyncio.create_task(self._receive_loop(connection))
                    
                    return True
                else:
                    sock.close()
                    return False
                    
            except socket.timeout:
                sock.close()
                return False
                
        except Exception as e:
            self.stats['connection_errors'] += 1
            print(f"Connection error to {host}:{port}: {e}")
            return False
    
    async def disconnect(self, host: str, port: int) -> bool:
        """Disconnect from a remote agent."""
        connection_key = f"{host}:{port}"
        if connection_key in self.connections:
            connection = self.connections[connection_key]
            connection.socket.close()
            del self.connections[connection_key]
            return True
        return False
    
    async def send_message(self, host: str, port: int, message: UACPMessage) -> bool:
        """Send a message to a remote agent."""
        connection_key = f"{host}:{port}"
        if connection_key not in self.connections:
            # Try to connect first
            if not await self.connect(host, port):
                return False
        
        connection = self.connections[connection_key]
        
        try:
            # Pack and send message
            data = message.pack()
            connection.socket.sendto(data, (host, port))
            
            # Update connection activity
            connection.last_activity = time.time()
            
            # Update statistics
            self.stats['messages_sent'] += 1
            
            return True
            
        except Exception as e:
            print(f"Send error to {host}:{port}: {e}")
            return False
    
    async def ping(self, host: str, port: int, qos: int = 0) -> bool:
        """Send PING message to check liveness."""
        connection_key = f"{host}:{port}"
        if connection_key not in self.connections:
            if not await self.connect(host, port):
                return False
        
        connection = self.connections[connection_key]
        message = UACPProtocol.create_ping(connection.next_message_id(), qos)
        
        return await self.send_message(host, port, message)
    
    async def tell(self, host: str, port: int, topic: str, data: Union[bytes, str, dict],
                  qos: int = 0, conv_id: Optional[str] = None) -> bool:
        """Send TELL message (inform)."""
        connection_key = f"{host}:{port}"
        if connection_key not in self.connections:
            if not await self.connect(host, port):
                return False
        
        connection = self.connections[connection_key]
        message = UACPProtocol.create_tell(
            connection.next_message_id(), topic, data, qos, conv_id
        )
        
        return await self.send_message(host, port, message)
    
    async def ask(self, host: str, port: int, topic: str, data: Union[bytes, str, dict],
                 qos: int = 1, conv_id: Optional[str] = None, timeout: Optional[float] = None) -> Optional[UACPMessage]:
        """Send ASK message and wait for response."""
        connection_key = f"{host}:{port}"
        if connection_key not in self.connections:
            if not await self.connect(host, port):
                return None
        
        connection = self.connections[connection_key]
        message = UACPProtocol.create_ask(
            connection.next_message_id(), topic, data, qos, conv_id
        )
        
        # Create future for response
        future = asyncio.Future()
        request = UACPRequest(
            message=message,
            timestamp=time.time(),
            timeout=timeout or self.default_timeout,
            future=future
        )
        
        # Store pending request
        self.pending_requests[message.header.msg_id] = request
        
        # Send message
        if not await self.send_message(host, port, message):
            del self.pending_requests[message.header.msg_id]
            return None
        
        try:
            # Wait for response
            response = await asyncio.wait_for(future, timeout=request.timeout)
            return response
        except asyncio.TimeoutError:
            # Handle timeout
            if request.retries < self.max_retries:
                # Retry with exponential backoff
                request.retries += 1
                request.timeout *= 2
                return await self.ask(host, port, topic, data, qos, conv_id, request.timeout)
            else:
                # Max retries exceeded
                self.stats['requests_timeout'] += 1
                del self.pending_requests[message.header.msg_id]
                return None
        finally:
            # Clean up
            if message.header.msg_id in self.pending_requests:
                del self.pending_requests[message.header.msg_id]
    
    async def observe(self, host: str, port: int, topic: str, qos: int = 1) -> bool:
        """Send OBSERVE message (subscribe)."""
        connection_key = f"{host}:{port}"
        if connection_key not in self.connections:
            if not await self.connect(host, port):
                return False
        
        connection = self.connections[connection_key]
        message = UACPProtocol.create_observe(
            connection.next_message_id(), topic, qos
        )
        
        return await self.send_message(host, port, message)
    
    def add_message_handler(self, verb: UACPVerb, handler: Callable):
        """Add message handler for specific verb."""
        self.message_handlers[verb].append(handler)
    
    async def _receive_loop(self, connection: UACPConnection):
        """Background task for receiving messages from a connection."""
        while True:
            try:
                # Receive data
                data, addr = connection.socket.recvfrom(1024)
                
                # Parse message
                message = UACPMessage.unpack(data)
                
                # Update connection activity
                connection.last_activity = time.time()
                
                # Update statistics
                self.stats['messages_received'] += 1
                
                # Check if this is a response to a pending request
                if message.header.verb in [UACPVerb.ASK, UACPVerb.TELL]:
                    # Look for correlation ID
                    corr_option = UACPProtocol.get_option(message, UACPOptionType.CORRELATION_ID)
                    if corr_option:
                        corr_id = int.from_bytes(corr_option.value, 'big')
                        if corr_id in self.pending_requests:
                            request = self.pending_requests[corr_id]
                            if not request.future.done():
                                request.future.set_result(message)
                
                # Call message handlers
                for handler in self.message_handlers.get(message.header.verb, []):
                    try:
                        await handler(message, connection.host, connection.port)
                    except Exception as e:
                        print(f"Handler error: {e}")
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Receive error: {e}")
                break
        
        # Clean up connection
        connection.socket.close()
        connection_key = f"{connection.host}:{connection.port}"
        if connection_key in self.connections:
            del self.connections[connection_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return self.stats.copy()
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about active connections."""
        connections = []
        for key, conn in self.connections.items():
            connections.append({
                'host': conn.host,
                'port': conn.port,
                'last_activity': conn.last_activity,
                'message_count': conn.message_id_counter
            })
        return connections
    
    async def close(self):
        """Close all connections and cleanup."""
        for connection_key in list(self.connections.keys()):
            host, port = connection_key.split(':')
            await self.disconnect(host, int(port))
        
        # Cancel pending requests
        for request in self.pending_requests.values():
            if not request.future.done():
                request.future.cancel()
        
        self.pending_requests.clear()
