"""
µACP Agent Implementation

Provides a complete agent implementation that combines:
- Client functionality for sending messages
- Server functionality for receiving messages
- Agent identity and capabilities
- Topic-based routing and processing
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Callable, Union, Any, Tuple
from dataclasses import dataclass
from .protocol import (
    UACPProtocol, UACPMessage, UACPHeader, UACPOption, 
    UACPOptionType, UACPVerb, UACPContentType
)
from .client import UACPClient
from .server import UACPServer


@dataclass
class UACPCapability:
    """Agent capability definition."""
    name: str
    description: str
    topics: List[str]  # Topics this capability can handle
    input_format: str   # Expected input format
    output_format: str  # Output format


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
    """Complete µACP agent implementation."""
    
    def __init__(self,
                 agent_id: Optional[str] = None,
                 name: str = "µACP Agent",
                 host: str = "0.0.0.0",
                 port: int = 8888,
                 capabilities: Optional[List[UACPCapability]] = None):
        
        # Agent identity
        self.agent_id = agent_id or f"agent:{uuid.uuid4().hex[:8]}"
        self.name = name
        
        # Capabilities
        self.capabilities = capabilities or []
        self.topic_handlers: Dict[str, List[Callable]] = {}
        self.verb_handlers: Dict[UACPVerb, List[Callable]] = {
            verb: [] for verb in UACPVerb
        }
        
        # Network components
        self.server = UACPServer(host=host, port=port)
        self.client = UACPClient()
        
        # Agent state
        self.running = False
        self.conversations: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'conversations_active': 0,
            'capabilities_used': 0
        }
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message and topic handlers."""
        # Register verb handlers
        self.server.add_message_handler(UACPVerb.PING, self._handle_ping)
        self.server.add_message_handler(UACPVerb.TELL, self._handle_tell)
        self.server.add_message_handler(UACPVerb.ASK, self._handle_ask)
        self.server.add_message_handler(UACPVerb.OBSERVE, self._handle_observe)
        
        # Register client message handlers
        self.client.add_message_handler(UACPVerb.TELL, self._handle_incoming_tell)
        self.client.add_message_handler(UACPVerb.ASK, self._handle_incoming_ask)
    
    def add_capability(self, capability: UACPCapability):
        """Add a capability to the agent."""
        self.capabilities.append(capability)
        
        # Register topic handlers for this capability
        for topic in capability.topics:
            if topic not in self.topic_handlers:
                self.topic_handlers[topic] = []
    
    def add_topic_handler(self, topic: str, handler: Callable):
        """Add a handler for a specific topic."""
        if topic not in self.topic_handlers:
            self.topic_handlers[topic] = []
        self.topic_handlers[topic].append(handler)
    
    def add_verb_handler(self, verb: UACPVerb, handler: Callable):
        """Add a handler for a specific verb."""
        self.verb_handlers[verb].append(handler)
        self.server.add_message_handler(verb, handler)
    
    async def start(self):
        """Start the agent."""
        if self.running:
            return
        
        try:
            # Start server
            await self.server.start()
            
            # Start client
            # (Client doesn't need explicit start)
            
            self.running = True
            print(f"µACP Agent '{self.name}' started on port {self.server.port}")
            
        except Exception as e:
            print(f"Failed to start agent: {e}")
            raise
    
    async def stop(self):
        """Stop the agent."""
        if not self.running:
            return
        
        try:
            # Stop server
            await self.server.stop()
            
            # Close client
            await self.client.close()
            
            self.running = False
            print(f"µACP Agent '{self.name}' stopped")
            
        except Exception as e:
            print(f"Error stopping agent: {e}")
    
    # Message handling methods
    async def _handle_ping(self, message: UACPMessage, client_host: str, client_port: int):
        """Handle incoming PING message."""
        # Call custom handlers
        for handler in self.verb_handlers[UACPVerb.PING]:
            try:
                await handler(message, client_host, client_port)
            except Exception as e:
                print(f"PING handler error: {e}")
        
        # Default response is handled by server
    
    async def _handle_tell(self, message: UACPMessage, client_host: str, client_port: int):
        """Handle incoming TELL message."""
        topic = UACPProtocol.get_topic(message)
        conversation_id = UACPProtocol.get_conversation_id(message)
        
        # Call custom handlers
        for handler in self.verb_handlers[UACPVerb.TELL]:
            try:
                await handler(message, client_host, client_port)
            except Exception as e:
                print(f"TELL handler error: {e}")
        
        # Call topic handlers
        if topic and topic in self.topic_handlers:
            for handler in self.topic_handlers[topic]:
                try:
                    await handler(message, client_host, client_port, topic, conversation_id)
                except Exception as e:
                    print(f"Topic handler error for {topic}: {e}")
        
        # Default response is handled by server
    
    async def _handle_ask(self, message: UACPMessage, client_host: str, client_port: int):
        """Handle incoming ASK message."""
        topic = UACPProtocol.get_topic(message)
        conversation_id = UACPProtocol.get_conversation_id(message)
        
        # Call custom handlers
        for handler in self.verb_handlers[UACPVerb.ASK]:
            try:
                await handler(message, client_host, client_port)
            except Exception as e:
                print(f"ASK handler error: {e}")
        
        # Call topic handlers
        if topic and topic in self.topic_handlers:
            for handler in self.topic_handlers[topic]:
                try:
                    response = await handler(message, client_host, client_port, topic, conversation_id)
                    if response is not None:
                        # Send custom response
                        custom_response = UACPProtocol.create_response(message, code=0, payload=response)
                        await self.server._send_response(custom_response, client_host, client_port)
                        return
                except Exception as e:
                    print(f"Topic handler error for {topic}: {e}")
        
        # Default response is handled by server
    
    async def _handle_observe(self, message: UACPMessage, client_host: str, client_port: int):
        """Handle incoming OBSERVE message."""
        topic = UACPProtocol.get_topic(message)
        conversation_id = UACPProtocol.get_conversation_id(message)
        
        # Call custom handlers
        for handler in self.verb_handlers[UACPVerb.OBSERVE]:
            try:
                await handler(message, client_host, client_port)
            except Exception as e:
                print(f"OBSERVE handler error: {e}")
        
        # Default response is handled by server
    
    async def _handle_incoming_tell(self, message: UACPMessage, client_host: str, client_port: int):
        """Handle TELL message received by client."""
        topic = UACPProtocol.get_topic(message)
        conversation_id = UACPProtocol.get_conversation_id(message)
        
        print(f"Received TELL on topic '{topic}' from {client_host}:{client_port}")
        
        # Call topic handlers
        if topic and topic in self.topic_handlers:
            for handler in self.topic_handlers[topic]:
                try:
                    await handler(message, client_host, client_port, topic, conversation_id)
                except Exception as e:
                    print(f"Topic handler error for {topic}: {e}")
    
    async def _handle_incoming_ask(self, message: UACPMessage, client_host: str, client_port: int):
        """Handle ASK message received by client."""
        topic = UACPProtocol.get_topic(message)
        conversation_id = UACPProtocol.get_conversation_id(message)
        
        print(f"Received ASK on topic '{topic}' from {client_host}:{client_port}")
        
        # Call topic handlers
        if topic and topic in self.topic_handlers:
            for handler in self.topic_handlers[topic]:
                try:
                    response = await handler(message, client_host, client_port, topic, conversation_id)
                    if response is not None:
                        # Send response back
                        response_msg = UACPProtocol.create_response(message, code=0, payload=response)
                        await self.client.send_message(client_host, client_port, response_msg)
                except Exception as e:
                    print(f"Topic handler error for {topic}: {e}")
    
    # Client convenience methods
    async def connect_to_agent(self, host: str, port: int) -> bool:
        """Connect to another agent."""
        return await self.client.connect(host, port)
    
    async def disconnect_from_agent(self, host: str, port: int) -> bool:
        """Disconnect from another agent."""
        return await self.client.disconnect(host, port)
    
    async def ping_agent(self, host: str, port: int, qos: int = 0) -> bool:
        """Ping another agent."""
        return await self.client.ping(host, port, qos)
    
    async def tell_agent(self, host: str, port: int, topic: str, data: Union[bytes, str, dict],
                        qos: int = 0, conv_id: Optional[str] = None) -> bool:
        """Tell another agent something."""
        return await self.client.tell(host, port, topic, data, qos, conv_id)
    
    async def ask_agent(self, host: str, port: int, topic: str, data: Union[bytes, str, dict],
                        qos: int = 1, conv_id: Optional[str] = None, timeout: Optional[float] = None) -> Optional[UACPMessage]:
        """Ask another agent something and wait for response."""
        return await self.client.ask(host, port, topic, data, qos, conv_id, timeout)
    
    async def observe_agent(self, host: str, port: int, topic: str, qos: int = 1) -> bool:
        """Subscribe to updates from another agent."""
        return await self.client.observe(host, port, topic, qos)
    
    # Agent management methods
    def get_agent_info(self) -> UACPAgentInfo:
        """Get agent information for discovery."""
        # Collect all topics from capabilities
        all_topics = []
        for capability in self.capabilities:
            all_topics.extend(capability.topics)
        
        # Remove duplicates
        unique_topics = list(set(all_topics))
        
        return UACPAgentInfo(
            agent_id=self.agent_id,
            name=self.name,
            capabilities=self.capabilities,
            topics=unique_topics,
            content_types=[UACPContentType.CBOR, UACPContentType.JSON, UACPContentType.TEXT],
            max_block_size=1024
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get combined agent statistics."""
        client_stats = self.client.get_stats()
        server_stats = self.server.get_stats()
        
        combined_stats = self.stats.copy()
        combined_stats.update({
            'client': client_stats,
            'server': server_stats,
            'capabilities_count': len(self.capabilities),
            'topics_handled': len(self.topic_handlers),
            'conversations_active': len(self.conversations)
        })
        
        return combined_stats
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about client connections."""
        return self.client.get_connection_info()
    
    def get_subscription_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get information about server subscriptions."""
        return self.server.get_subscription_info()
    
    def get_conversation_info(self) -> List[Dict[str, Any]]:
        """Get information about server conversations."""
        return self.server.get_conversation_info()
    
    # Utility methods
    def create_conversation_id(self) -> str:
        """Create a new conversation ID."""
        return f"conv:{uuid.uuid4().hex[:8]}"
    
    def start_conversation(self, topic: str, client_host: str, client_port: int) -> str:
        """Start a new conversation."""
        conv_id = self.create_conversation_id()
        
        self.conversations[conv_id] = {
            'topic': topic,
            'client_host': client_host,
            'client_port': client_port,
            'started_at': time.time(),
            'last_activity': time.time(),
            'state': {}
        }
        
        self.stats['conversations_active'] += 1
        return conv_id
    
    def end_conversation(self, conv_id: str):
        """End a conversation."""
        if conv_id in self.conversations:
            del self.conversations[conv_id]
            self.stats['conversations_active'] -= 1
    
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
