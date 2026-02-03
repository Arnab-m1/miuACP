"""
µACP Server Implementation

Provides server-side functionality for:
- Receiving messages from clients
- Handling different verb types
- Managing subscriptions and conversations
- Responding to requests
"""

import asyncio
import socket
import time
import cbor2
import uuid
from typing import Dict, List, Optional, Callable, Union, Any, Tuple
from dataclasses import dataclass
from .protocol import (
    UACPProtocol, UACPMessage, UACPHeader, UACPOption, 
    UACPOptionType, UACPVerb, UACPContentType
)


@dataclass
class UACPSubscription:
    """Active subscription to a topic."""
    topic: str
    client_host: str
    client_port: int
    qos: int
    timestamp: float
    conversation_id: Optional[str] = None


@dataclass
class UACPConversation:
    """Multi-turn conversation context."""
    conversation_id: str
    topic: str
    client_host: str
    client_port: int
    state: Dict[str, Any]
    created_at: float
    last_activity: float


class UACPServer:
    """µACP server for handling agent communications."""
    
    def __init__(self, 
                 host: str = "0.0.0.0",
                 port: int = 8888,
                 max_connections: int = 100,
                 subscription_timeout: float = 3600.0):  # 1 hour
        
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.subscription_timeout = subscription_timeout
        
        # Server state
        self.running = False
        self.socket: Optional[socket.socket] = None
        
        # Message handlers
        self.message_handlers: Dict[UACPVerb, List[Callable]] = {
            verb: [] for verb in UACPVerb
        }
        
        # Subscriptions and conversations
        self.subscriptions: Dict[str, List[UACPSubscription]] = {}  # topic -> subscriptions
        self.conversations: Dict[str, UACPConversation] = {}  # conv_id -> conversation
        
        # Statistics
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'subscriptions_active': 0,
            'conversations_active': 0,
            'errors': 0
        }
        
        # Message ID counter
        self.message_id_counter = 0
    
    def next_message_id(self) -> int:
        """Get next unique message ID."""
        self.message_id_counter += 1
        return self.message_id_counter
    
    def add_message_handler(self, verb: UACPVerb, handler: Callable):
        """Add message handler for specific verb."""
        self.message_handlers[verb].append(handler)
    
    async def start(self):
        """Start the server."""
        if self.running:
            return
        
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.socket.settimeout(1.0)  # 1 second timeout for non-blocking
            
            self.running = True
            print(f"µACP Server started on {self.host}:{self.port}")
            
            # Start background tasks
            asyncio.create_task(self._receive_loop())
            asyncio.create_task(self._cleanup_loop())
            
        except Exception as e:
            print(f"Failed to start server: {e}")
            self.stats['errors'] += 1
            raise
    
    async def stop(self):
        """Stop the server."""
        if not self.running:
            return
        
        self.running = False
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        print("µACP Server stopped")
    
    async def _receive_loop(self):
        """Main receive loop for incoming messages."""
        while self.running:
            try:
                # Receive data
                data, addr = self.socket.recvfrom(1024)
                client_host, client_port = addr
                
                # Parse message
                try:
                    message = UACPMessage.unpack(data)
                except Exception as e:
                    print(f"Failed to parse message from {client_host}:{client_port}: {e}")
                    self.stats['errors'] += 1
                    continue
                
                # Update statistics
                self.stats['messages_received'] += 1
                
                # Handle message based on verb
                await self._handle_message(message, client_host, client_port)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Receive error: {e}")
                    self.stats['errors'] += 1
    
    async def _handle_message(self, message: UACPMessage, client_host: str, client_port: int):
        """Handle incoming message based on verb type."""
        try:
            # Call registered handlers
            handlers = self.message_handlers.get(message.header.verb, [])
            for handler in handlers:
                try:
                    await handler(message, client_host, client_port)
                except Exception as e:
                    print(f"Handler error: {e}")
                    self.stats['errors'] += 1
            
            # Handle specific verb types
            if message.header.verb == UACPVerb.PING:
                await self._handle_ping(message, client_host, client_port)
            elif message.header.verb == UACPVerb.TELL:
                await self._handle_tell(message, client_host, client_port)
            elif message.header.verb == UACPVerb.ASK:
                await self._handle_ask(message, client_host, client_port)
            elif message.header.verb == UACPVerb.OBSERVE:
                await self._handle_observe(message, client_host, client_port)
                
        except Exception as e:
            print(f"Message handling error: {e}")
            self.stats['errors'] += 1
    
    async def _handle_ping(self, message: UACPMessage, client_host: str, client_port: int):
        """Handle PING message."""
        # Send PING response
        response = UACPProtocol.create_response(message, code=0)
        await self._send_response(response, client_host, client_port)
    
    async def _handle_tell(self, message: UACPMessage, client_host: str, client_port: int):
        """Handle TELL message (inform)."""
        topic = UACPProtocol.get_topic(message)
        conversation_id = UACPProtocol.get_conversation_id(message)
        
        if topic:
            # Notify subscribers
            await self._notify_subscribers(topic, message, conversation_id)
            
            # Send acknowledgment
            response = UACPProtocol.create_response(message, code=0)
            await self._send_response(response, client_host, client_port)
    
    async def _handle_ask(self, message: UACPMessage, client_host: str, client_port: int):
        """Handle ASK message (request)."""
        topic = UACPProtocol.get_topic(message)
        conversation_id = UACPProtocol.get_conversation_id(message)
        
        if topic:
            # Process request and generate response
            response_data = await self._process_request(topic, message.payload, conversation_id)
            
            # Send response
            response = UACPProtocol.create_response(message, code=0, payload=response_data)
            await self._send_response(response, client_host, client_port)
    
    async def _handle_observe(self, message: UACPMessage, client_host: str, client_port: int):
        """Handle OBSERVE message (subscribe)."""
        topic = UACPProtocol.get_topic(message)
        conversation_id = UACPProtocol.get_conversation_id(message)
        
        if topic:
            # Create subscription
            subscription = UACPSubscription(
                topic=topic,
                client_host=client_host,
                client_port=client_port,
                qos=message.header.qos,
                timestamp=time.time(),
                conversation_id=conversation_id
            )
            
            # Add to subscriptions
            if topic not in self.subscriptions:
                self.subscriptions[topic] = []
            self.subscriptions[topic].append(subscription)
            
            # Update statistics
            self.stats['subscriptions_active'] += 1
            
            # Send acknowledgment
            response = UACPProtocol.create_response(message, code=0)
            await self._send_response(response, client_host, client_port)
    
    async def _notify_subscribers(self, topic: str, message: UACPMessage, conversation_id: Optional[str]):
        """Notify all subscribers of a topic."""
        if topic not in self.subscriptions:
            return
        
        # Find matching subscriptions
        matching_subscriptions = []
        for subscription in self.subscriptions[topic]:
            # Check if subscription matches conversation
            if conversation_id is None or subscription.conversation_id == conversation_id:
                matching_subscriptions.append(subscription)
        
        # Send notifications
        for subscription in matching_subscriptions:
            try:
                # Create notification message
                notification = UACPMessage(
                    header=UACPHeader(
                        version=1,
                        verb=UACPVerb.TELL,
                        qos=subscription.qos,
                        code=0,
                        msg_id=self.next_message_id(),
                        opts_count=2
                    ),
                    options=[
                        UACPOption(UACPOptionType.TOPIC_PATH, topic),
                        UACPOption(UACPOptionType.CONVERSATION_ID, conversation_id or "")
                    ],
                    payload=message.payload
                )
                
                await self._send_response(notification, subscription.client_host, subscription.client_port)
                
            except Exception as e:
                print(f"Failed to notify subscriber {subscription.client_host}:{subscription.client_port}: {e}")
    
    async def _process_request(self, topic: str, payload: Optional[bytes], conversation_id: Optional[str]) -> Optional[bytes]:
        """Process request and generate response."""
        # This is a placeholder - implement your business logic here
        # You can override this method or use message handlers
        
        # For now, return a simple acknowledgment
        response = {
            "status": "processed",
            "topic": topic,
            "timestamp": time.time()
        }
        
        if conversation_id:
            response["conversation_id"] = conversation_id
        
        return cbor2.dumps(response)
    
    async def _send_response(self, message: UACPMessage, host: str, port: int):
        """Send response to client."""
        try:
            data = message.pack()
            self.socket.sendto(data, (host, port))
            self.stats['messages_sent'] += 1
        except Exception as e:
            print(f"Failed to send response to {host}:{port}: {e}")
            self.stats['errors'] += 1
    
    async def _cleanup_loop(self):
        """Background task for cleaning up expired subscriptions and conversations."""
        while self.running:
            try:
                current_time = time.time()
                
                # Clean up expired subscriptions
                for topic in list(self.subscriptions.keys()):
                    active_subscriptions = []
                    for subscription in self.subscriptions[topic]:
                        if current_time - subscription.timestamp < self.subscription_timeout:
                            active_subscriptions.append(subscription)
                        else:
                            self.stats['subscriptions_active'] -= 1
                    
                    if active_subscriptions:
                        self.subscriptions[topic] = active_subscriptions
                    else:
                        del self.subscriptions[topic]
                
                # Clean up expired conversations (older than 24 hours)
                conversation_timeout = 86400.0  # 24 hours
                expired_conversations = []
                for conv_id, conversation in self.conversations.items():
                    if current_time - conversation.last_activity > conversation_timeout:
                        expired_conversations.append(conv_id)
                
                for conv_id in expired_conversations:
                    del self.conversations[conv_id]
                    self.stats['conversations_active'] -= 1
                
                # Wait before next cleanup
                await asyncio.sleep(60.0)  # Clean up every minute
                
            except Exception as e:
                print(f"Cleanup error: {e}")
                await asyncio.sleep(60.0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return self.stats.copy()
    
    def get_subscription_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get information about active subscriptions."""
        info = {}
        for topic, subscriptions in self.subscriptions.items():
            info[topic] = []
            for sub in subscriptions:
                info[topic].append({
                    'client': f"{sub.client_host}:{sub.client_port}",
                    'qos': sub.qos,
                    'age': time.time() - sub.timestamp,
                    'conversation_id': sub.conversation_id
                })
        return info
    
    def get_conversation_info(self) -> List[Dict[str, Any]]:
        """Get information about active conversations."""
        conversations = []
        current_time = time.time()
        for conv_id, conv in self.conversations.items():
            conversations.append({
                'conversation_id': conv_id,
                'topic': conv.topic,
                'client': f"{conv.client_host}:{conv.client_port}",
                'age': current_time - conv.created_at,
                'last_activity': current_time - conv.last_activity,
                'state_keys': list(conv.state.keys())
            })
        return conversations
