"""
µACP Formal Protocol Layering

Implements the three-layer architecture:
1. Transport Binding Layer (UDP, DTLS, WebSocket, QUIC)
2. Message Layer (verbs, header, options)
3. Semantic Layer (agent actions, state machines)
"""

import asyncio
import ssl
import websockets
from typing import Dict, List, Optional, Callable, Any, Union, Protocol
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from .protocol import UACPMessage, UACPHeader, UACPOption, UACPOptionType, UACPVerb


class LayerType(Enum):
    """Protocol layer types."""
    TRANSPORT = "transport"
    MESSAGE = "message"
    SEMANTIC = "semantic"


class TransportBinding(Enum):
    """Transport binding types."""
    UDP = "udp"
    UDP_DTLS = "udp_dtls"
    TCP = "tcp"
    TCP_TLS = "tcp_tls"
    WEBSOCKET = "websocket"
    QUIC = "quic"


@dataclass
class LayerConfig:
    """Configuration for protocol layers."""
    layer_type: LayerType
    transport_binding: Optional[TransportBinding] = None
    security_profile: Optional[str] = None
    max_message_size: int = 65535
    timeout: float = 30.0


class UACPLayer(ABC):
    """Abstract base class for protocol layers."""
    
    def __init__(self, config: LayerConfig):
        self.config = config
        self.upper_layer: Optional['UACPLayer'] = None
        self.lower_layer: Optional['UACPLayer'] = None
        self.message_handlers: List[Callable] = []
    
    def set_upper_layer(self, layer: 'UACPLayer'):
        """Set the layer above this one."""
        self.upper_layer = layer
        if layer:
            layer.lower_layer = self
    
    def set_lower_layer(self, layer: 'UACPLayer'):
        """Set the layer below this one."""
        self.lower_layer = layer
        if layer:
            layer.upper_layer = self
    
    def add_message_handler(self, handler: Callable):
        """Add message handler for this layer."""
        self.message_handlers.append(handler)
    
    @abstractmethod
    async def send_message(self, message: Any, destination: Any) -> bool:
        """Send message to destination."""
        pass
    
    @abstractmethod
    async def receive_message(self, message: Any, source: Any):
        """Receive message from source."""
        pass
    
    async def pass_to_upper(self, message: Any, source: Any):
        """Pass message to upper layer."""
        if self.upper_layer:
            await self.upper_layer.receive_message(message, source)
    
    async def pass_to_lower(self, message: Any, destination: Any):
        """Pass message to lower layer."""
        if self.lower_layer:
            await self.lower_layer.send_message(message, destination)


class TransportLayer(UACPLayer):
    """Transport binding layer implementation."""
    
    def __init__(self, config: LayerConfig):
        super().__init__(config)
        self.transport_binding = config.transport_binding
        self.connections: Dict[str, Any] = {}
        self.running = False
        
        # Initialize transport based on binding
        self._init_transport()
    
    def _init_transport(self):
        """Initialize transport based on binding type."""
        if self.transport_binding == TransportBinding.UDP:
            self._init_udp()
        elif self.transport_binding == TransportBinding.UDP_DTLS:
            self._init_udp_dtls()
        elif self.transport_binding == TransportBinding.TCP:
            self._init_tcp()
        elif self.transport_binding == TransportBinding.TCP_TLS:
            self._init_tcp_tls()
        elif self.transport_binding == TransportBinding.WEBSOCKET:
            self._init_websocket()
        elif self.transport_binding == TransportBinding.QUIC:
            self._init_quic()
    
    def _init_udp(self):
        """Initialize UDP transport."""
        import socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def _init_udp_dtls(self):
        """Initialize UDP with DTLS."""
        try:
            import ssl
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        except ImportError:
            print("DTLS not available, falling back to UDP")
            self._init_udp()
    
    def _init_tcp(self):
        """Initialize TCP transport."""
        import socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def _init_tcp_tls(self):
        """Initialize TCP with TLS."""
        try:
            import ssl
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        except ImportError:
            print("TLS not available, falling back to TCP")
            self._init_tcp()
    
    def _init_websocket(self):
        """Initialize WebSocket transport."""
        try:
            import websockets
            self.websocket_library = websockets
        except ImportError:
            print("WebSocket not available")
            self.transport_binding = TransportBinding.TCP
    
    def _init_quic(self):
        """Initialize QUIC transport."""
        try:
            # QUIC implementation would go here
            # For now, fall back to TCP
            print("QUIC not available, falling back to TCP")
            self.transport_binding = TransportBinding.TCP
            self._init_tcp()
        except ImportError:
            print("QUIC not available, falling back to TCP")
            self.transport_binding = TransportBinding.TCP
            self._init_tcp()
    
    async def start(self):
        """Start the transport layer."""
        self.running = True
        
        if self.transport_binding in [TransportBinding.UDP, TransportBinding.UDP_DTLS]:
            await self._start_udp_listener()
        elif self.transport_binding in [TransportBinding.TCP, TransportBinding.TCP_TLS]:
            await self._start_tcp_listener()
        elif self.transport_binding == TransportBinding.WEBSOCKET:
            await self._start_websocket_listener()
    
    async def stop(self):
        """Stop the transport layer."""
        self.running = False
        
        if hasattr(self, 'socket'):
            self.socket.close()
    
    async def _start_udp_listener(self):
        """Start UDP listener."""
        # Implementation would go here
        pass
    
    async def _start_tcp_listener(self):
        """Start TCP listener."""
        # Implementation would go here
        pass
    
    async def _start_websocket_listener(self):
        """Start WebSocket listener."""
        # Implementation would go here
        pass
    
    async def send_message(self, message: UACPMessage, destination: Any) -> bool:
        """Send message via transport layer."""
        try:
            # Serialize message
            data = message.pack()
            
            # Send via appropriate transport
            if self.transport_binding == TransportBinding.UDP:
                return await self._send_udp(data, destination)
            elif self.transport_binding == TransportBinding.TCP:
                return await self._send_tcp(data, destination)
            elif self.transport_binding == TransportBinding.WEBSOCKET:
                return await self._send_websocket(data, destination)
            else:
                return False
                
        except Exception as e:
            print(f"Transport send error: {e}")
            return False
    
    async def receive_message(self, message: bytes, source: Any):
        """Receive message from transport layer."""
        try:
            # Deserialize message
            uacp_message = UACPMessage.unpack(message)
            
            # Pass to upper layer
            await self.pass_to_upper(uacp_message, source)
            
        except Exception as e:
            print(f"Transport receive error: {e}")
    
    async def _send_udp(self, data: bytes, destination: Any) -> bool:
        """Send via UDP."""
        try:
            self.socket.sendto(data, destination)
            return True
        except Exception as e:
            print(f"UDP send error: {e}")
            return False
    
    async def _send_tcp(self, data: bytes, destination: Any) -> bool:
        """Send via TCP."""
        try:
            # Implementation would go here
            return True
        except Exception as e:
            print(f"TCP send error: {e}")
            return False
    
    async def _send_websocket(self, data: bytes, destination: Any) -> bool:
        """Send via WebSocket."""
        try:
            # Implementation would go here
            return True
        except Exception as e:
            print(f"WebSocket send error: {e}")
            return False


class MessageLayer(UACPLayer):
    """Message layer implementation."""
    
    def __init__(self, config: LayerConfig):
        super().__init__(config)
        self.message_handlers: List[Callable] = []
        self.option_handlers: Dict[int, Callable] = {}
    
    async def send_message(self, message: UACPMessage, destination: Any) -> bool:
        """Send message via message layer."""
        try:
            # Validate message
            if not self._validate_message(message):
                return False
            
            # Process options
            message = await self._process_outgoing_options(message)
            
            # Pass to lower layer
            await self.pass_to_lower(message, destination)
            return True
            
        except Exception as e:
            print(f"Message layer send error: {e}")
            return False
    
    async def receive_message(self, message: UACPMessage, source: Any):
        """Receive message in message layer."""
        try:
            # Validate message
            if not self._validate_message(message):
                return
            
            # Process incoming options
            message = await self._process_incoming_options(message)
            
            # Pass to upper layer
            await self.pass_to_upper(message, source)
            
        except Exception as e:
            print(f"Message layer receive error: {e}")
    
    def _validate_message(self, message: UACPMessage) -> bool:
        """Validate message structure."""
        try:
            # Check header validity
            if not message.header:
                return False
            
            # Check options count
            if len(message.options) != message.header.options_count:
                return False
            
            # Check payload size
            if message.payload and len(message.payload) > self.config.max_message_size:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def _process_outgoing_options(self, message: UACPMessage) -> UACPMessage:
        """Process options for outgoing messages."""
        # Add default options if needed
        # Process critical options
        return message
    
    async def _process_incoming_options(self, message: UACPMessage) -> UACPMessage:
        """Process options for incoming messages."""
        # Validate critical options
        # Process elective options
        return message


class SemanticLayer(UACPLayer):
    """Semantic layer implementation."""
    
    def __init__(self, config: LayerConfig):
        super().__init__(config)
        self.verb_handlers: Dict[UACPVerb, Callable] = {}
        self.state_machines: Dict[str, Any] = {}
        
        # Initialize verb handlers
        self._init_verb_handlers()
    
    def _init_verb_handlers(self):
        """Initialize handlers for each verb."""
        self.verb_handlers[UACPVerb.PING] = self._handle_ping
        self.verb_handlers[UACPVerb.TELL] = self._handle_tell
        self.verb_handlers[UACPVerb.ASK] = self._handle_ask
        self.verb_handlers[UACPVerb.OBSERVE] = self._handle_observe
    
    async def send_message(self, message: UACPMessage, destination: Any) -> bool:
        """Send message via semantic layer."""
        try:
            # Apply semantic rules
            message = await self._apply_semantic_rules(message)
            
            # Pass to lower layer
            await self.pass_to_lower(message, destination)
            return True
            
        except Exception as e:
            print(f"Semantic layer send error: {e}")
            return False
    
    async def receive_message(self, message: UACPMessage, source: Any):
        """Receive message in semantic layer."""
        try:
            # Route to appropriate verb handler
            verb = message.header.verb
            if verb in self.verb_handlers:
                await self.verb_handlers[verb](message, source)
            else:
                print(f"Unknown verb: {verb}")
            
        except Exception as e:
            print(f"Semantic layer receive error: {e}")
    
    async def _apply_semantic_rules(self, message: UACPMessage) -> UACPMessage:
        """Apply semantic rules to message."""
        # Apply conversation rules
        # Apply QoS rules
        # Apply security rules
        return message
    
    async def _handle_ping(self, message: UACPMessage, source: Any):
        """Handle PING verb."""
        # Implement PING semantics
        pass
    
    async def _handle_tell(self, message: UACPMessage, source: Any):
        """Handle TELL verb."""
        # Implement TELL semantics
        pass
    
    async def _handle_ask(self, message: UACPMessage, source: Any):
        """Handle ASK verb."""
        # Implement ASK semantics
        pass
    
    async def _handle_observe(self, message: UACPMessage, source: Any):
        """Handle OBSERVE verb."""
        # Implement OBSERVE semantics
        pass


class UACPLayerStack:
    """Complete µACP protocol layer stack."""
    
    def __init__(self, config: LayerConfig):
        self.config = config
        
        # Create layers
        self.transport_layer = TransportLayer(config)
        self.message_layer = MessageLayer(config)
        self.semantic_layer = SemanticLayer(config)
        
        # Connect layers
        self.transport_layer.set_upper_layer(self.message_layer)
        self.message_layer.set_upper_layer(self.semantic_layer)
        self.semantic_layer.set_lower_layer(self.message_layer)
        self.message_layer.set_lower_layer(self.transport_layer)
    
    async def start(self):
        """Start all layers."""
        await self.transport_layer.start()
    
    async def stop(self):
        """Stop all layers."""
        await self.transport_layer.stop()
    
    async def send_message(self, message: UACPMessage, destination: Any) -> bool:
        """Send message through the layer stack."""
        return await self.semantic_layer.send_message(message, destination)
    
    def add_semantic_handler(self, verb: UACPVerb, handler: Callable):
        """Add handler for semantic layer."""
        self.semantic_layer.verb_handlers[verb] = handler
