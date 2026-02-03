"""
µACP P2P Agent Implementation

Provides symmetric peer-to-peer agent with:
- Direct peer communication (no client/server distinction)
- Transport abstraction (UDP, TCP, etc.)
- Peer discovery and registry
- Message and topic-based routing
- Asyncio-based architecture
"""

import asyncio
import time
import uuid
import cbor2
from typing import Dict, List, Optional, Callable, Union, Any, Tuple
from dataclasses import dataclass, field
from .protocol import (
    UACPProtocol, UACPMessage, UACPHeader, UACPOption, 
    UACPOptionType, UACPVerb, UACPContentType
)
from .transport_base import UACPTransport
from .udp_transport import UDPTransport


@dataclass
class PeerInfo:
    """Information about a discovered peer."""
    host: str
    port: int
    agent_id: str = ""
    last_seen: float = field(default_factory=time.time)
    
    def is_alive(self, timeout: float = 60.0) -> bool:
        """Check if peer is still alive based on last seen time."""
        return (time.time() - self.last_seen) < timeout


@dataclass
class UACPCapability:
    """Agent capability definition."""
    name: str
    description: str
    topics: List[str]
    input_format: str
    output_format: str


@dataclass
class UACPAgentInfo:
    """Agent information for discovery."""
    agent_id: str
    name: str
    capabilities: List[UACPCapability]
    topics: List[str]
    content_types: List[UACPContentType]
    max_block_size: int = 1024


class UACPAgent:
    """
    Symmetric P2P µACP Agent.
    
    All agents are equal peers - no client/server distinction.
    Can send to and receive from any peer without "connecting".
    """
    
    def __init__(self,
                 agent_id: Optional[str] = None,
                 name: str = "µACP Agent",
                 host: str = "0.0.0.0",
                 port: int = 0,
                 transport: Optional[UACPTransport] = None,
                 capabilities: Optional[List[UACPCapability]] = None):
        
        # Agent identity
        self.agent_id = agent_id or f"agent:{uuid.uuid4().hex[:8]}"
        self.name = name
        self.host = host
        self.port = port
        
        # Single transport (not client + server!)
        self.transport = transport or UDPTransport()
        
        # Peer registry
        self.peers: Dict[str, PeerInfo] = {}  # "host:port" -> PeerInfo
        
        # Capabilities
        self.capabilities = capabilities or []
        
        # Message handlers (verb-based)
        self.message_handlers: Dict[UACPVerb, List[Callable]] = {
            verb: [] for verb in UACPVerb
        }
        
        # Topic handlers (topic-based with wildcards)
        self.topic_handlers: Dict[str, List[Callable]] = {}
        
        # Agent state
        self.running = False
        self.receiver_task: Optional[asyncio.Task] = None
        self.conversations: Dict[str, Dict[str, Any]] = {}
        
        # Message ID counter
        self._message_id_counter = 0
        self._message_id_lock = asyncio.Lock()
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'peers_discovered': 0,
            'errors': 0
        }
        
        # Pending requests (for ask/response correlation)
        self._pending_requests: Dict[int, asyncio.Future] = {}
    
    async def _next_message_id(self) -> int:
        """Get next unique message ID (thread-safe)."""
        async with self._message_id_lock:
            self._message_id_counter += 1
            return self._message_id_counter
    
    async def start(self) -> bool:
        """
        Start the agent.
        
        Binds transport and starts receiver loop.
        
        Returns:
            True if started successfully
        """
        if self.running:
            return True
        
        try:
            # Bind transport
            if not await self.transport.bind(self.host, self.port):
                return False
            
            # Get actual bound port (may be ephemeral)
            self.port = self.transport.get_local_port()
            
            self.running = True
            
            # Start receiver task
            self.receiver_task = asyncio.create_task(self._receiver_loop())
            
            print(f"µACP Agent '{self.name}' (ID: {self.agent_id}) started on port {self.port}")
            return True
            
        except Exception as e:
            print(f"Failed to start agent: {e}")
            self.stats['errors'] += 1
            return False
    
    async def stop(self):
        """Stop the agent and cleanup resources."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel receiver task
        if self.receiver_task:
            self.receiver_task.cancel()
            try:
                await self.receiver_task
            except asyncio.CancelledError:
                pass
        
        # Close transport
        self.transport.close()
        
        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
        
        print(f"µACP Agent '{self.name}' stopped")
    
    # ========== P2P Communication Methods ==========
    
    async def ping(self, peer_host: str, peer_port: int, qos: int = 0) -> bool:
        """
        Send PING to any peer (no connection needed!).
        
        Args:
            peer_host: Peer's host address
            peer_port: Peer's port
            qos: Quality of service level
            
        Returns:
            True if sent successfully
        """
        msg_id = await self._next_message_id()
        message = UACPProtocol.create_ping(msg_id, qos)
        return await self._send_to_peer(peer_host, peer_port, message)
    
    async def tell(self, peer_host: str, peer_port: int, topic: str, 
                   data: Union[bytes, str, dict], qos: int = 0, 
                   conv_id: Optional[str] = None) -> bool:
        """
        Tell (inform) a peer about something.
        
        Args:
            peer_host: Peer's host
            peer_port: Peer's port
            topic: Topic path
            data: Data to send (bytes, str, or dict)
            qos: Quality of service
            conv_id: Optional conversation ID
            
        Returns:
            True if sent successfully
        """
        msg_id = await self._next_message_id()
        message = UACPProtocol.create_tell(msg_id, topic, data, qos, conv_id)
        return await self._send_to_peer(peer_host, peer_port, message)
    
    async def ask(self, peer_host: str, peer_port: int, topic: str,
                  data: Union[bytes, str, dict], qos: int = 1,
                  conv_id: Optional[str] = None, 
                  timeout: float = 5.0) -> Optional[UACPMessage]:
        """
        Ask a peer for information and wait for response.
        
        Args:
            peer_host: Peer's host
            peer_port: Peer's port
            topic: Topic path
            data: Query data
            qos: Quality of service
            conv_id: Optional conversation ID
            timeout: Response timeout in seconds
            
        Returns:
            Response message or None on timeout
        """
        msg_id = await self._next_message_id()
        message = UACPProtocol.create_ask(msg_id, topic, data, qos, conv_id)
        
        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self._pending_requests[msg_id] = future
        
        try:
            # Send message
            if not await self._send_to_peer(peer_host, peer_port, message):
                del self._pending_requests[msg_id]
                return None
            
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            print(f"Request {msg_id} to {peer_host}:{peer_port} timed out")
            return None
            
        finally:
            # Cleanup
            if msg_id in self._pending_requests:
                del self._pending_requests[msg_id]
    
    async def observe(self, peer_host: str, peer_port: int, topic: str, qos: int = 1) -> bool:
        """
        Subscribe to updates from a peer's topic.
        
        Args:
            peer_host: Peer's host
            peer_port: Peer's port
            topic: Topic to observe
            qos: Quality of service
            
        Returns:
            True if sent successfully
        """
        msg_id = await self._next_message_id()
        message = UACPProtocol.create_observe(msg_id, topic, qos)
        return await self._send_to_peer(peer_host, peer_port, message)
    
    # ========== Peer Discovery ==========
    
    async def discover_peers(self, broadcast_addr: str = "255.255.255.255", 
                           port: int = 8888, timeout: float = 1.0) -> int:
        """
        Discover peers via UDP broadcast.
        
        Args:
            broadcast_addr: Broadcast address
            port: Port to broadcast to
            timeout: Time to wait for responses
            
        Returns:
            Number of peers discovered
        """
        # Enable broadcast
        await self.transport.enable_broadcast()
        
        # Create discovery PING message
        msg_id = await self._next_message_id()
        message = UACPProtocol.create_ping(msg_id)
        
        # Send broadcast
        data = message.pack()
        await self.transport.send_to_peer(data, broadcast_addr, port)
        
        # Wait for responses
        await asyncio.sleep(timeout)
        
        return len(self.peers)
    
    def get_discovered_peers(self) -> List[PeerInfo]:
        """
        Get list of discovered peers.
        
        Returns:
            List of PeerInfo objects
        """
        return list(self.peers.values())
    
    # ========== Message Handlers ==========
    
    def add_message_handler(self, verb: UACPVerb, handler: Callable):
        """
        Add handler for specific verb type.
        
        Args:
            verb: Message verb (PING, TELL, ASK, etc.)
            handler: Async callback(message, sender_host, sender_port)
        """
        if verb not in self.message_handlers:
            self.message_handlers[verb] = []
        self.message_handlers[verb].append(handler)
    
    def add_topic_handler(self, topic_pattern: str, handler: Callable):
        """
        Add handler for topic pattern (supports wildcards).
        
        Args:
            topic_pattern: Topic pattern (e.g., "sensor/#", "*/temperature")
            handler: Async callback(message, sender_host, sender_port)
        """
        if topic_pattern not in self.topic_handlers:
            self.topic_handlers[topic_pattern] = []
        self.topic_handlers[topic_pattern].append(handler)
    
    def add_capability(self, capability: UACPCapability):
        """Add a capability to the agent."""
        self.capabilities.append(capability)
        
        # Auto-register topic handlers for capability topics
        for topic in capability.topics:
            if topic not in self.topic_handlers:
                self.topic_handlers[topic] = []
    
    # ========== Internal Methods ==========
    
    async def _send_to_peer(self, host: str, port: int, message: UACPMessage) -> bool:
        """Send message to any peer."""
        try:
            data = message.pack()
            success = await self.transport.send_to_peer(data, host, port)
            
            if success:
                self.stats['messages_sent'] += 1
                self.stats['bytes_sent'] += len(data)
            
            return success
            
        except Exception as e:
            print(f"Failed to send to {host}:{port}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def _receiver_loop(self):
        """Background receiver loop for ALL incoming messages."""
        while self.running:
            try:
                # Receive from any peer
                data, sender_host, sender_port = await self.transport.receive_from_peer(100)
                
                if not data:
                    continue
                
                # Parse message
                try:
                    message = UACPMessage.unpack(data)
                except Exception as e:
                    print(f"Failed to parse message from {sender_host}:{sender_port}: {e}")
                    self.stats['errors'] += 1
                    continue
                
                # Update statistics
                self.stats['messages_received'] += 1
                self.stats['bytes_received'] += len(data)
                
                # Update peer registry
                peer_key = f"{sender_host}:{sender_port}"
                if peer_key not in self.peers:
                    self.peers[peer_key] = PeerInfo(
                        host=sender_host,
                        port=sender_port,
                        last_seen=time.time()
                    )
                    self.stats['peers_discovered'] += 1
                else:
                    self.peers[peer_key].last_seen = time.time()
                
                # Handle message
                await self._handle_incoming_message(message, sender_host, sender_port)
                
            except Exception as e:
                if self.running:
                    print(f"Receiver error: {e}")
                    self.stats['errors'] += 1
    
    async def _handle_incoming_message(self, message: UACPMessage, 
                                       sender_host: str, sender_port: int):
        """Route incoming message to appropriate handlers."""
        try:
            # Check if this is a response to a pending request
            if message.header.msg_id in self._pending_requests:
                future = self._pending_requests[message.header.msg_id]
                if not future.done():
                    future.set_result(message)
                return
            
            # Call verb-based handlers
            if message.header.verb in self.message_handlers:
                for handler in self.message_handlers[message.header.verb]:
                    try:
                        await handler(message, sender_host, sender_port)
                    except Exception as e:
                        print(f"Verb handler error: {e}")
                        self.stats['errors'] += 1
            
            # Call topic-based handlers
            topic = UACPProtocol.get_topic(message)
            if topic:
                # Direct match
                if topic in self.topic_handlers:
                    for handler in self.topic_handlers[topic]:
                        try:
                            await handler(message, sender_host, sender_port)
                        except Exception as e:
                            print(f"Topic handler error: {e}")
                            self.stats['errors'] += 1
                
                # Wildcard match
                for pattern, handlers in self.topic_handlers.items():
                    if self._topic_matches(topic, pattern):
                        for handler in handlers:
                            try:
                                await handler(message, sender_host, sender_port)
                            except Exception as e:
                                print(f"Topic pattern handler error: {e}")
                                self.stats['errors'] += 1
            
        except Exception as e:
            print(f"Message handling error: {e}")
            self.stats['errors'] += 1
    
    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """
        Check if topic matches pattern with wildcards.
        
        Supports:
        - # : multi-level wildcard (e.g., "sensor/#" matches "sensor/temp/room1")
        - * : single-level wildcard (e.g., "*/temp" matches "sensor1/temp")
        """
        if pattern == topic:
            return True
        
        if '#' in pattern:
            prefix = pattern.split('#')[0]
            return topic.startswith(prefix)
        
        if '*' in pattern:
            pattern_parts = pattern.split('/')
            topic_parts = topic.split('/')
            
            if len(pattern_parts) != len(topic_parts):
                return False
            
            for pp, tp in zip(pattern_parts, topic_parts):
                if pp != '*' and pp != tp:
                    return False
            return True
        
        return False
    
    # ========== Statistics and Info ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            **self.stats,
            'agent_id': self.agent_id,
            'name': self.name,
            'port': self.port,
            'peers': len(self.peers),
            'capabilities': len(self.capabilities),
            'topic_handlers': len(self.topic_handlers)
        }
    
    def get_agent_info(self) -> UACPAgentInfo:
        """Get agent information for discovery."""
        all_topics = []
        for capability in self.capabilities:
            all_topics.extend(capability.topics)
        
        return UACPAgentInfo(
            agent_id=self.agent_id,
            name=self.name,
            capabilities=self.capabilities,
            topics=list(set(all_topics)),
            content_types=[UACPContentType.CBOR, UACPContentType.JSON, UACPContentType.TEXT],
            max_block_size=1024
        )
    
    # ========== Conversation Management ==========
    
    def create_conversation_id(self) -> str:
        """Create a new conversation ID."""
        return f"conv:{uuid.uuid4().hex[:8]}"
    
    def start_conversation(self, topic: str, peer_host: str, peer_port: int) -> str:
        """Start a new conversation."""
        conv_id = self.create_conversation_id()
        
        self.conversations[conv_id] = {
            'topic': topic,
            'peer_host': peer_host,
            'peer_port': peer_port,
            'started_at': time.time(),
            'last_activity': time.time(),
            'state': {}
        }
        
        return conv_id
    
    def end_conversation(self, conv_id: str):
        """End a conversation."""
        if conv_id in self.conversations:
            del self.conversations[conv_id]
    
    def update_conversation_state(self, conv_id: str, key: str, value: Any):
        """Update conversation state."""
        if conv_id in self.conversations:
            self.conversations[conv_id]['state'][key] = value
            self.conversations[conv_id]['last_activity'] = time.time()
    
    def get_conversation_state(self, conv_id: str, key: str) -> Any:
        """Get conversation state."""
        if conv_id in self.conversations:
            return self.conversations[conv_id]['state'].get(key)
        return None
