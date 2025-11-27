"""
µACP Protocol Bridges

Provides bridges to:
- MQTT (Message Queuing Telemetry Transport)
- CoAP (Constrained Application Protocol)
- MCP (Model Context Protocol)

Enables seamless integration with existing IoT and agent systems.
"""

import asyncio
import json
import aiocoap
import time
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass
from enum import Enum
from .protocol import UACPMessage, UACPHeader, UACPOption, UACPOptionType, UACPVerb, UACPContentType
from .transport import UACPTransport, TransportConfig


class BridgeType(Enum):
    """Bridge types."""
    MQTT = "mqtt"
    COAP = "coap"
    MCP = "mcp"


@dataclass
class BridgeConfig:
    """Bridge configuration."""
    bridge_type: BridgeType
    enabled: bool = True
    host: str = "localhost"
    port: int = 1883  # Default MQTT port
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    topics: List[str] = None
    qos: int = 1
    keepalive: int = 60
    tls_enabled: bool = False
    tls_ca_cert: Optional[str] = None


class UACPBridge:
    """Base class for protocol bridges."""
    
    def __init__(self, config: BridgeConfig, uacp_transport: UACPTransport):
        self.config = config
        self.uacp_transport = uacp_transport
        self.running = False
        self.message_handlers: List[Callable] = []
        
    async def start(self):
        """Start the bridge."""
        if self.running:
            return
        
        self.running = True
        await self._start_bridge()
        print(f"µACP {self.config.bridge_type.value.upper()} bridge started")
    
    async def stop(self):
        """Stop the bridge."""
        if not self.running:
            return
        
        self.running = False
        await self._stop_bridge()
        print(f"µACP {self.config.bridge_type.value.upper()} bridge stopped")
    
    async def _start_bridge(self):
        """Start the specific bridge implementation."""
        raise NotImplementedError
    
    async def _stop_bridge(self):
        """Stop the specific bridge implementation."""
        raise NotImplementedError
    
    def add_message_handler(self, handler: Callable):
        """Add message handler."""
        self.message_handlers.append(handler)
    
    async def _handle_uacp_message(self, message: UACPMessage, source: str):
        """Handle incoming µACP message from bridge."""
        for handler in self.message_handlers:
            try:
                await handler(message, source)
            except Exception as e:
                print(f"Bridge message handler error: {e}")


class MQTTBridge(UACPBridge):
    """MQTT to µACP bridge."""
    
    def __init__(self, config: BridgeConfig, uacp_transport: UACPTransport):
        super().__init__(config, uacp_transport)
        self.mqtt_client = None
        self.topic_mappings: Dict[str, str] = {}
        
        # Initialize topic mappings
        if config.topics:
            for topic in config.topics:
                # Map MQTT topics to µACP topics
                uacp_topic = f"/mqtt/{topic.replace('+', '*').replace('#', '#')}"
                self.topic_mappings[topic] = uacp_topic
    
    async def _start_bridge(self):
        """Start MQTT bridge."""
        try:
            # Try to import paho-mqtt
            import paho.mqtt.client as mqtt
            
            # Create MQTT client
            self.mqtt_client = mqtt.Client(
                client_id=self.config.client_id or f"uacp_bridge_{int(time.time())}",
                clean_session=True
            )
            
            # Set callbacks
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_message = self._on_mqtt_message
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            
            # Set credentials if provided
            if self.config.username and self.config.password:
                self.mqtt_client.username_pw_set(self.config.username, self.config.password)
            
            # Set TLS if enabled
            if self.config.tls_enabled and self.config.tls_ca_cert:
                self.mqtt_client.tls_set(self.config.tls_ca_cert)
            
            # Connect to MQTT broker
            self.mqtt_client.connect(self.config.host, self.config.port, self.config.keepalive)
            
            # Start loop in background
            asyncio.create_task(self._mqtt_loop())
            
        except ImportError:
            print("paho-mqtt not installed. Install with: pip install paho-mqtt")
            self.running = False
        except Exception as e:
            print(f"Failed to start MQTT bridge: {e}")
            self.running = False
    
    async def _stop_bridge(self):
        """Stop MQTT bridge."""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            self.mqtt_client = None
    
    async def _mqtt_loop(self):
        """MQTT event loop."""
        if self.mqtt_client:
            self.mqtt_client.loop_start()
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback."""
        print(f"MQTT bridge connected with result code {rc}")
        
        # Subscribe to topics
        if self.config.topics:
            for topic in self.config.topics:
                client.subscribe(topic, self.config.qos)
                print(f"Subscribed to MQTT topic: {topic}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback."""
        try:
            # Convert MQTT message to µACP
            uacp_message = self._mqtt_to_uacp(msg)
            
            # Handle in async context
            asyncio.create_task(self._handle_uacp_message(uacp_message, f"mqtt:{msg.topic}"))
            
        except Exception as e:
            print(f"Failed to convert MQTT message: {e}")
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback."""
        print(f"MQTT bridge disconnected with result code {rc}")
    
    def _mqtt_to_uacp(self, mqtt_msg) -> UACPMessage:
        """Convert MQTT message to µACP message."""
        # Parse MQTT payload
        try:
            payload = json.loads(mqtt_msg.payload.decode())
        except:
            payload = mqtt_msg.payload.decode()
        
        # Map MQTT topic to µACP topic
        uacp_topic = self.topic_mappings.get(mqtt_msg.topic, f"/mqtt/{mqtt_msg.topic}")
        
        # Create µACP message
        message = UACPMessage(
            header=UACPHeader(
                version=1,
                verb=UACPVerb.TELL,  # MQTT pub/sub maps to TELL
                qos=min(mqtt_msg.qos, 2),  # Map QoS levels
                code=0,  # OK
                message_id=int(time.time() * 1000) % (2**24),
                options_count=2
            ),
            options=[
                UACPOption(
                    type=UACPOptionType.TOPIC_PATH,
                    value=uacp_topic.encode()
                ),
                UACPOption(
                    type=UACPOptionType.CONTENT_TYPE,
                    value=UACPContentType.JSON.value.to_bytes(1, 'big')
                )
            ],
            payload=json.dumps(payload).encode()
        )
        
        return message
    
    async def publish_uacp_message(self, message: UACPMessage, mqtt_topic: str):
        """Publish µACP message to MQTT."""
        if not self.mqtt_client or not self.running:
            return False
        
        try:
            # Convert µACP message to MQTT
            mqtt_payload = self._uacp_to_mqtt(message)
            
            # Publish to MQTT
            result = self.mqtt_client.publish(
                mqtt_topic,
                mqtt_payload,
                qos=self.config.qos
            )
            
            return result.rc == 0
            
        except Exception as e:
            print(f"Failed to publish to MQTT: {e}")
            return False
    
    def _uacp_to_mqtt(self, uacp_message: UACPMessage) -> str:
        """Convert µACP message to MQTT payload."""
        # Extract topic
        topic = ""
        for option in uacp_message.options:
            if option.type == UACPOptionType.TOPIC_PATH:
                topic = option.value.decode()
                break
        
        # Remove /mqtt prefix if present
        if topic.startswith("/mqtt/"):
            topic = topic[6:]
        
        # Create MQTT payload
        payload = {
            "source": "uacp",
            "topic": topic,
            "verb": uacp_message.header.verb.name,
            "qos": uacp_message.header.qos,
            "message_id": uacp_message.header.message_id,
            "data": uacp_message.payload.decode() if uacp_message.payload else None
        }
        
        return json.dumps(payload)


class CoAPBridge(UACPBridge):
    """CoAP to µACP bridge."""
    
    def __init__(self, config: BridgeConfig, uacp_transport: UACPTransport):
        super().__init__(config, uacp_transport)
        self.coap_server = None
        self.resource_handlers: Dict[str, Callable] = {}
        
    async def _start_bridge(self):
        """Start CoAP bridge."""
        try:
            # Try to import aiocoap
            import aiocoap
            
            # Create CoAP context
            context = await aiocoap.Context.create_client_context()
            
            # Start CoAP server
            self.coap_server = await aiocoap.Context.create_server_context(
                self._coap_request_handler
            )
            
            print(f"CoAP bridge started on {self.config.host}:{self.config.port}")
            
        except ImportError:
            print("aiocoap not installed. Install with: pip install aiocoap")
            self.running = False
        except Exception as e:
            print(f"Failed to start CoAP bridge: {e}")
            self.running = False
    
    async def _stop_bridge(self):
        """Stop CoAP bridge."""
        if self.coap_server:
            await self.coap_server.shutdown()
            self.coap_server = None
    
    async def _coap_request_handler(self, request):
        """Handle CoAP request."""
        try:
            # Convert CoAP request to µACP
            uacp_message = self._coap_to_uacp(request)
            
            # Handle in async context
            asyncio.create_task(self._handle_uacp_message(uacp_message, f"coap:{request.opt.uri_path}"))
            
            # Return CoAP response
            return aiocoap.Message(
                code=aiocoap.CoAPResponse.CONTENT,
                payload=b"OK"
            )
            
        except Exception as e:
            print(f"Failed to handle CoAP request: {e}")
            return aiocoap.Message(code=aiocoap.CoAPResponse.INTERNAL_SERVER_ERROR)
    
    def _coap_to_uacp(self, coap_request) -> UACPMessage:
        """Convert CoAP request to µACP message."""
        # Determine verb based on CoAP method
        if coap_request.code.is_request():
            if coap_request.code == aiocoap.CoAPRequest.GET:
                verb = UACPVerb.ASK
            elif coap_request.code == aiocoap.CoAPRequest.POST:
                verb = UACPVerb.TELL
            elif coap_request.code == aiocoap.CoAPRequest.PUT:
                verb = UACPVerb.TELL
            elif coap_request.code == aiocoap.CoAPRequest.DELETE:
                verb = UACPVerb.TELL
            else:
                verb = UACPVerb.TELL
        else:
            verb = UACPVerb.TELL
        
        # Create topic from URI path
        topic = "/" + "/".join(coap_request.opt.uri_path)
        
        # Create µACP message
        message = UACPMessage(
            header=UACPHeader(
                version=1,
                verb=verb,
                qos=0,  # CoAP doesn't have QoS
                code=0,
                message_id=int(time.time() * 1000) % (2**24),
                options_count=2
            ),
            options=[
                UACPOption(
                    type=UACPOptionType.TOPIC_PATH,
                    value=topic.encode()
                ),
                UACPOption(
                    type=UACPOptionType.CONTENT_TYPE,
                    value=UACPContentType.CBOR.value.to_bytes(1, 'big')
                )
            ],
            payload=coap_request.payload
        )
        
        return message
    
    async def send_coap_request(self, method: str, uri: str, payload: bytes = None):
        """Send CoAP request."""
        if not self.coap_server or not self.running:
            return False
        
        try:
            import aiocoap
            
            # Create CoAP request
            request = aiocoap.Message(
                code=getattr(aiocoap.CoAPRequest, method.upper()),
                uri=uri,
                payload=payload or b""
            )
            
            # Send request
            response = await self.coap_server.request(request).response
            
            return response.code.is_successful()
            
        except Exception as e:
            print(f"Failed to send CoAP request: {e}")
            return False


class MCPBridge(UACPBridge):
    """MCP to µACP bridge."""
    
    def __init__(self, config: BridgeConfig, uacp_transport: UACPTransport):
        super().__init__(config, uacp_transport)
        self.mcp_client = None
        self.tool_handlers: Dict[str, Callable] = {}
        
    async def _start_bridge(self):
        """Start MCP bridge."""
        try:
            # Try to import MCP client
            import mcp.client as mcp_client
            
            # Create MCP client
            self.mcp_client = mcp_client.Client(
                server_url=f"ws://{self.config.host}:{self.config.port}"
            )
            
            # Connect to MCP server
            await self.mcp_client.connect()
            
            # Start MCP message handler
            asyncio.create_task(self._mcp_message_handler())
            
            print(f"MCP bridge started and connected to {self.config.host}:{self.config.port}")
            
        except ImportError:
            print("MCP client not installed. Install with: pip install mcp")
            self.running = False
        except Exception as e:
            print(f"Failed to start MCP bridge: {e}")
            self.running = False
    
    async def _stop_bridge(self):
        """Stop MCP bridge."""
        if self.mcp_client:
            await self.mcp_client.disconnect()
            self.mcp_client = None
    
    async def _mcp_message_handler(self):
        """Handle MCP messages."""
        if not self.mcp_client:
            return
        
        try:
            async for message in self.mcp_client.messages():
                # Convert MCP message to µACP
                uacp_message = self._mcp_to_uacp(message)
                
                # Handle in async context
                asyncio.create_task(self._handle_uacp_message(uacp_message, f"mcp:{message.get('id', 'unknown')}"))
                
        except Exception as e:
            print(f"MCP message handler error: {e}")
    
    def _mcp_to_uacp(self, mcp_message: Dict[str, Any]) -> UACPMessage:
        """Convert MCP message to µACP message."""
        # Determine verb based on MCP method
        method = mcp_message.get('method', 'unknown')
        if method == 'tools/call':
            verb = UACPVerb.ASK
        elif method == 'notifications/notify':
            verb = UACPVerb.TELL
        else:
            verb = UACPVerb.TELL
        
        # Create topic from MCP method
        topic = f"/mcp/{method.replace('/', '/')}"
        
        # Create µACP message
        message = UACPMessage(
            header=UACPHeader(
                version=1,
                verb=verb,
                qos=1,  # MCP has reliability
                code=0,
                message_id=int(time.time() * 1000) % (2**24),
                options_count=2
            ),
            options=[
                UACPOption(
                    type=UACPOptionType.TOPIC_PATH,
                    value=topic.encode()
                ),
                UACPOption(
                    type=UACPOptionType.CONTENT_TYPE,
                    value=UACPContentType.JSON.value.to_bytes(1, 'big')
                )
            ],
            payload=json.dumps(mcp_message).encode()
        )
        
        return message
    
    async def send_mcp_message(self, method: str, params: Dict[str, Any] = None):
        """Send MCP message."""
        if not self.mcp_client or not self.running:
            return False
        
        try:
            # Create MCP message
            message = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": method,
                "params": params or {}
            }
            
            # Send message
            await self.mcp_client.send_message(message)
            return True
            
        except Exception as e:
            print(f"Failed to send MCP message: {e}")
            return False


class BridgeManager:
    """Manages all protocol bridges."""
    
    def __init__(self, uacp_transport: UACPTransport):
        self.uacp_transport = uacp_transport
        self.bridges: Dict[BridgeType, UACPBridge] = {}
        self.running = False
    
    def add_bridge(self, bridge: UACPBridge):
        """Add a bridge."""
        self.bridges[bridge.config.bridge_type] = bridge
    
    async def start_all(self):
        """Start all bridges."""
        if self.running:
            return
        
        self.running = True
        
        for bridge in self.bridges.values():
            if bridge.config.enabled:
                await bridge.start()
    
    async def stop_all(self):
        """Stop all bridges."""
        if not self.running:
            return
        
        self.running = False
        
        for bridge in self.bridges.values():
            await bridge.stop()
    
    def get_bridge(self, bridge_type: BridgeType) -> Optional[UACPBridge]:
        """Get bridge by type."""
        return self.bridges.get(bridge_type)
    
    def get_bridge_stats(self) -> Dict[str, Any]:
        """Get statistics from all bridges."""
        stats = {}
        for bridge_type, bridge in self.bridges.items():
            stats[bridge_type.value] = {
                'enabled': bridge.config.enabled,
                'running': bridge.running,
                'config': {
                    'host': bridge.config.host,
                    'port': bridge.config.port,
                    'tls_enabled': bridge.config.tls_enabled
                }
            }
        return stats
