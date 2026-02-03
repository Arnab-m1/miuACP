# µACP (Micro Agent Communication Protocol)

[![PyPI version](https://badge.fury.io/py/miuacp.svg)](https://badge.fury.io/py/miuacp)
[![Version](https://img.shields.io/badge/version-2.0.0--p2p-blue.svg)](https://github.com/Arnab-m1/miuACP)
[![Python versions](https://img.shields.io/pypi/pyversions/miuacp.svg)](https://pypi.org/project/miuacp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-16%2F16_passing-brightgreen.svg)]()
[![Architecture](https://img.shields.io/badge/architecture-P2P-orange.svg)]()

**µACP** is a lightweight, agent-centric communication protocol designed for edge-native multi-agent systems. It combines the efficiency of IoT protocols with the semantic richness of agent communication languages, making it ideal for lightweight AI agents, IoT devices, and edge computing environments.

## **✨ What's New in v2.0 - P2P Architecture**

Version 2.0 introduces a **symmetric peer-to-peer (P2P) architecture**:

**🎯 Key Improvements:**
- **Symmetric Agents**: All agents are equal peers
- **Direct Communication**: Send to any peer without "connecting" first
- **Transport Abstraction**: Pluggable transport layer (UDP, TCP, WebSocket, etc.)
- **Peer Discovery**: Built-in UDP broadcast for automatic peer discovery
- **Simpler API**: Cleaner, more intuitive methods

# ✅ New v2.0 (P2P)
agent = UACPAgent("agent", port=8888)
await agent.tell("192.168.1.100", 8889, "topic", data)  # Direct send!
```

**📚 Full Migration Guide**: See [Migration Guide](#migration-from-v10-to-v20-p2p) below.

---

## **Key Features**

### **P2P Architecture (v2.0)**
- **Symmetric peers**: Every agent can send AND receive
- **No server required**: True peer-to-peer communication
- **Transport abstraction**: UDP, TCP, WebSocket support
- **Peer discovery**: Automatic discovery via UDP broadcast
- **Topic-based routing**: Wildcard pattern matching (`sensor/#`, `*/temp`)

### **Core Protocol**
- **Fixed 8-byte header** for maximum efficiency
- **4 semantic verbs**: PING, TELL, ASK, OBSERVE
- **TLV options** for extensibility
- **QoS levels**: At-most-once, at-least-once, exactly-once
- **CBOR serialization** for compact data representation

### **Memory State Management**
- **Routing & Addressing**: Neighbor tables, route management
- **Subscriptions & Dialogues**: Topic subscriptions, conversation state
- **Reliability & QoS**: Message tracking, block management
- **Timers & Scheduling**: Timer creation, message scheduling
- **Broker & Middleware**: Topic trees, subscriber management
- **Instrumentation & Control**: Logging, metrics, debugging
- **Resource Binding**: Socket management, DMA buffers

### **Enterprise-Grade Robustness**
- **Circuit Breaker Pattern**: Prevents cascading failures
- **Adaptive Timeouts**: Intelligent timeout management
- **Resource Pooling**: Efficient resource management
- **Error Recovery**: Advanced retry and fallback strategies
- **Health Monitoring**: Comprehensive system monitoring

### **Transport & Security**
- **Multiple transports**: UDP, TCP, UDP Multicast, WebSocket, QUIC
- **Security framework**: TLS, DTLS, HMAC, JWT, OAuth2
- **Protocol bridges**: MQTT, CoAP, MCP integration
- **Monitoring tools**: Prometheus metrics, health checks, alerting

---

## **Installation**

### **Basic Installation**
```bash
pip install miuacp
```

### **Installation with Full Features**
```bash
pip install "miuacp[full]"
```

### **Development Installation**
```bash
git clone https://github.com/Arnab-m1/miuACP.git
cd miuACP
pip install -e ".[dev]"
```

---

## **Quick Start (v2.0 P2P)**

### **Simple Two-Agent Communication**
```python
import asyncio
from miuacp import UACPAgent, UACPVerb

async def agent1():
    """Sender agent."""
    agent = UACPAgent(agent_id="agent1", name="Sender", port=8001)
    await agent.start()
    
    # Send directly to agent2 (no connect needed!)
    await agent.tell("127.0.0.1", 8002, "greeting", {"message": "Hello!"})
    
    await asyncio.sleep(2)
    await agent.stop()

async def agent2():
    """Receiver agent."""
    agent = UACPAgent(agent_id="agent2", name="Receiver", port=8002)
    
    # Add message handler
    async def handle_tell(msg, sender_host, sender_port):
        print(f"Received message from {sender_host}:{sender_port}")
    
    agent.add_message_handler(UACPVerb.TELL, handle_tell)
    
    await agent.start()
    await asyncio.sleep(2)
    await agent.stop()

# Run both agents
async def main():
    await asyncio.gather(agent1(), agent2())

asyncio.run(main())
```

### **Peer Discovery**
```python
import asyncio
from miuacp import UACPAgent

async def main():
    agent = UACPAgent(agent_id="discoverer", name="Discovery Agent", port=8001)
    await agent.start()
    
    # Discover peers via UDP broadcast
    peer_count = await agent.discover_peers(broadcast_addr="255.255.255.255", port=8002)
    
    print(f"Found {peer_count} peers:")
    for peer in agent.get_discovered_peers():
        print(f"  - {peer.host}:{peer.port}")
    
    await agent.stop()

asyncio.run(main())
```

### **Topic-Based Routing**
```python
from miuacp import UACPAgent

agent = UACPAgent(agent_id="sensor", name="Sensor Agent", port=8001)

# Add topic handler with wildcard support
async def handle_sensor_data(msg, sender_host, sender_port):
    print(f"Sensor data received from {sender_host}:{sender_port}")

agent.add_topic_handler("sensor/#", handle_sensor_data)  # Matches sensor/temp, sensor/humidity, etc.
agent.add_topic_handler("*/temperature", handle_sensor_data)  # Matches any/temperature

await agent.start()
```

### **Request/Response (Ask/Tell)**
```python
# Ask another agent and wait for response
response = await agent.ask(
    peer_host="192.168.1.100",
    peer_port=8002,
    topic="query/temperature",
    data={"location": "room1"},
    timeout=5.0  # Wait up to 5 seconds
)

if response:
    print(f"Response: {response.payload}")
else:
    print("Request timed out")
```

---

## **P2P Architecture Details**

### **Architecture Comparison**

**v1.0 (Client/Server):**
```
┌─────────────┐          ┌─────────────┐
│  UACPAgent  │          │  UACPAgent  │
├─────────────┤          ├─────────────┤
│ + client ───┼─────────▶│ + server    │
│ + server    │◀─────────┼── + client  │
└─────────────┘          └─────────────┘
  Asymmetric roles        Complex composition
```

**v2.0 (P2P):**
```
┌─────────────┐          ┌─────────────┐
│  UACPAgent  │◀────────▶│  UACPAgent  │
├─────────────┤          ├─────────────┤
│ + transport │          │ + transport │
│ + peers     │          │ + peers     │
│ + handlers  │          │ + handlers  │
└─────────────┘          └─────────────┘
  Symmetric peers         Single transport
```

### **Core Components (v2.0)**

**1. Transport Abstraction**
```python
from miuacp.transport_base import UACPTransport
from miuacp.udp_transport import UDPTransport

# Use default UDP transport
agent = UACPAgent("agent", port=8001)

# Or provide custom transport
custom_transport = UDPTransport()
agent = UACPAgent("agent", port=8001, transport=custom_transport)
```

**2. Peer Registry**
- Automatically tracks discovered peers
- Updates last-seen timestamps
- Provides peer liveness checking

**3. Message Routing**
- Verb-based handlers (PING, TELL, ASK, OBSERVE)
- Topic-based handlers with wildcards
- Automatic response correlation

### **API Reference (v2.0)**

#### **UACPAgent**

**Initialization:**
```python
agent = UACPAgent(
    agent_id="unique-id",        # Unique agent identifier
    name="My Agent",             # Human-readable name
    host="0.0.0.0",             # Bind address
    port=8001,                  # Port (0 for ephemeral)
    transport=None,             # Optional custom transport
    capabilities=[]             # Agent capabilities
)
```

**Lifecycle:**
```python
await agent.start()             # Start agent (bind transport, start receiver)
await agent.stop()              # Stop agent (cleanup resources)
```

**P2P Communication:**
```python
# Send PING to check liveness
await agent.ping(peer_host, peer_port, qos=0)

# Send one-way message (TELL)
await agent.tell(peer_host, peer_port, topic, data, qos=0, conv_id=None)

# Request/response (ASK)
response = await agent.ask(peer_host, peer_port, topic, data, qos=1, timeout=5.0)

# Subscribe to topic (OBSERVE)
await agent.observe(peer_host, peer_port, topic, qos=1)
```

**Peer Discovery:**
```python
# Broadcast discovery
peer_count = await agent.discover_peers(broadcast_addr="255.255.255.255", port=8888, timeout=1.0)

# Get discovered peers
peers = agent.get_discovered_peers()  # Returns List[PeerInfo]
```

**Message Handlers:**
```python
# Verb-based handler
async def handle_ping(msg, sender_host, sender_port):
    print(f"PING from {sender_host}:{sender_port}")

agent.add_message_handler(UACPVerb.PING, handle_ping)

# Topic-based handler (supports wildcards)
async def handle_sensor(msg, sender_host, sender_port):
    print(f"Sensor data: {msg.payload}")

agent.add_topic_handler("sensor/#", handle_sensor)  # Multi-level wildcard
agent.add_topic_handler("*/temp", handle_sensor)    # Single-level wildcard
```

**Statistics:**
```python
stats = agent.get_stats()
# Returns:
# {
#     'messages_sent': 42,
#     'messages_received': 38,
#     'bytes_sent': 2048,
#     'bytes_received': 1920,
#     'peers_discovered': 5,
#     'errors': 0,
#     'agent_id': 'agent-id',
#     'name': 'Agent Name',
#     'port': 8001,
#     'peers': 5
# }
```

---

## **Migration from v1.0 to v2.0 (P2P)**

### **Breaking Changes**

| v1.0 Method | v2.0 Method | Change |
|-------------|-------------|--------|
| `connect_to_agent(host, port)` | ❌ **Removed** | No longer needed |
| `disconnect_from_agent(host, port)` | ❌ **Removed** | No longer needed |
| `tell_agent(host, port, ...)` | `tell(host, port, ...)` | ✅ Renamed |
| `ask_agent(host, port, ...)` | `ask(host, port, ...)` | ✅ Renamed |
| `ping_agent(host, port)` | `ping(host, port)` | ✅ Renamed |
| `observe_agent(host, port, ...)` | `observe(host, port, ...)` | ✅ Renamed |

### **Architecture Changes**

**v1.0:**
```python
from miuacp import UACPAgent, UACPClient, UACPServer

agent = UACPAgent("agent", host="0.0.0.0", port=8888)
# Internally: agent.client = UACPClient()
#            agent.server = UACPServer(host, port)
```

**v2.0:**
```python
from miuacp import UACPAgent
from miuacp.udp_transport import UDPTransport

agent = UACPAgent("agent", host="0.0.0.0", port=8888)
# Internally: agent.transport = UDPTransport()
#            agent.peers = {}
#            agent.receiver_task = asyncio.Task(...)
```

### **Migration Steps**

1. **Update imports** - Remove `UACPClient` and `UACPServer` imports
2. **Remove connect calls** - Delete all `connect_to_agent()` and `disconnect_from_agent()` 
3. **Rename methods** - Change `tell_agent()` → `tell()`, etc.
4. **Update handlers** - Use new handler registration methods
5. **Test** - Verify P2P communication works

**Before (v1.0):**
```python
from miuacp import UACPAgent

agent1 = UACPAgent("agent1", port=8001)
agent2 = UACPAgent("agent2", port=8002)

await agent1.start()
await agent2.start()

# Must connect first
await agent1.connect_to_agent("127.0.0.1", 8002)

# Send message
await agent1.tell_agent("127.0.0.1", 8002, "topic", {"data": "value"})

# Disconnect
await agent1.disconnect_from_agent("127.0.0.1", 8002)
```

**After (v2.0):**
```python
from miuacp import UACPAgent

agent1 = UACPAgent(agent_id="agent1", name="Agent 1", port=8001)
agent2 = UACPAgent(agent_id="agent2", name="Agent 2", port=8002)

await agent1.start()
await agent2.start()

# No connect needed - send directly!
await agent1.tell("127.0.0.1", 8002, "topic", {"data": "value"})

# No disconnect needed
```

---

## **Examples**

### **Ping-Pong (Two Agents)**

Full example: [`examples/p2p_ping_pong.py`](examples/p2p_ping_pong.py)

```bash
# Terminal 1
python3 examples/p2p_ping_pong.py --role ping --port 8001 --peer-port 8002

# Terminal 2
python3 examples/p2p_ping_pong.py --role pong --port 8002
```

### **Multi-Agent Discovery**

Full example: [`examples/p2p_discovery.py`](examples/p2p_discovery.py)

```bash
# Start multiple agents
python3 examples/p2p_discovery.py --name Agent1 --port 8001
python3 examples/p2p_discovery.py --name Agent2 --port 8002
python3 examples/p2p_discovery.py --name Agent3 --port 8003
```

---

## **Testing**

### **Running Tests**
```bash
# Install pytest
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_udp_transport.py -v
pytest tests/test_p2p_agent.py -v
```

### **Test Coverage**

**Transport Tests (7):**
- ✅ Bind to fixed port
- ✅ Bind to ephemeral port
- ✅ Peer-to-peer communication
- ✅ Receive timeout
- ✅ Broadcast enabled
- ✅ Resource cleanup
- ✅ Multiple message handling

**Agent Tests (9):**
- ✅ Agent lifecycle (start/stop)
- ✅ Peer-to-peer PING
- ✅ Peer-to-peer TELL
- ✅ Peer-to-peer ASK
- ✅ Topic-based handlers
- ✅ Peer discovery
- ✅ Peer registry management
- ✅ Statistics tracking
- ✅ Wildcard topic matching

**Total: 16/16 tests passing** ✅

---

## **Performance Benchmarks**

µACP delivers excellent performance while maintaining rich functionality:

| Metric | Value | Comparison |
|--------|-------|------------|
| **Message Throughput** | **407,277 msg/sec** | 5.6x faster than MCP |
| **Message Creation** | 24.55ms (10K msgs) | Rich object creation |
| **Message Packing** | 10.68ms (10K msgs) | Efficient serialization |
| **Memory Usage** | 6.0 MB | Full feature set |
| **Protocol Efficiency** | 0.167 | Better than MQTT (0.080) |

### **Protocol Comparison**
| Protocol | Messages | Throughput | Avg Size | Efficiency |
|----------|----------|------------|----------|------------|
| **µACP** | 10,000 | **51,422** | **47.8** | **0.167** |
| MQTT | 10,000 | 289,498 | 37.6 | 0.080 |
| CoAP | 10,000 | 320,445 | 31.8 | 0.189 |
| MCP | 10,000 | 72,881 | 197.4 | 0.253 |

---

## **Advanced Usage**

### **Basic Message Creation (Low-Level)**
```python
from miuacp import UACPProtocol, UACPVerb, UACPOption, UACPOptionType

# Create protocol instance
uacp = UACPProtocol()

# Create a simple message
message = uacp.create_message(
    verb=UACPVerb.TELL,
    payload="Hello, world!".encode(),
    msg_id=0x123456
)

# Pack message for transmission
packed = message.pack()
print(f"Message size: {len(packed)} bytes")
```

### **Message with Options**
```python
# Create message with topic and content type
message = uacp.create_message(
    verb=UACPVerb.OBSERVE,
    payload="Subscribe to temperature updates".encode(),
    msg_id=0x123457,
    options=[
        UACPOption(UACPOptionType.TOPIC_PATH, "sensors/temperature"),
        UACPOption(UACPOptionType.CONTENT_TYPE, 0)  # CBOR
    ]
)
```

### **Memory State Management**
```python
from miuacp import UACPRouting, UACPSubscriptions, UACPReliability

# Routing
routing = UACPRouting()
routing.add_neighbor("agent_1", "192.168.1.100", 8080)
routing.add_route("network_1", "gateway_1", 1.0, RouteType.DIRECT)

# Subscriptions
subscriptions = UACPSubscriptions()
subscriptions.create_subscription("sub_1", "sensors/*", "agent_1")

# Reliability
reliability = UACPReliability()
reliability.track_message("msg_1", "agent_1", 1, 30.0)
```

### **Robustness Features**
```python
from miuacp import CircuitBreakerManager, AdaptiveTimeout, ResourcePool

# Circuit breaker
cb_manager = CircuitBreakerManager()
cb_manager.record_success("service_1")

# Adaptive timeout
timeout_manager = TimeoutManager()
timeout = timeout_manager.get_timeout("operation_1")

# Resource pooling
def create_connection():
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

pool = ResourcePool(create_connection, config=PoolConfig(min_size=2, max_size=10))
connection = pool.acquire()
```

### **Health Monitoring**
```python
from miuacp import HealthMonitor, CheckType

# Create health monitor
monitor = HealthMonitor()

# Add custom health check
async def check_database():
    # Your database health check logic
    return True

monitor.add_health_check_by_params(
    check_id="db_check",
    name="Database Health Check",
    description="Check database connectivity",
    check_func=check_database,
    check_type=CheckType.CUSTOM
)

# Start monitoring
await monitor.start()
```

---

## **Architecture**

### **Protocol Layers**
```
┌─────────────────────────────────────┐
│           Application               │
├─────────────────────────────────────┤
│     µACP P2P Agents (v2.0)          │
├─────────────────────────────────────┤
│      Transport Abstraction          │
│    (UDP/TCP/WebSocket/QUIC)         │
├─────────────────────────────────────┤
│         µACP Protocol               │
├─────────────────────────────────────┤
│         Security Layer              │
│      (TLS/DTLS/JWT/OAuth2)          │
├─────────────────────────────────────┤
│         Network Layer               │
│         (IP/Ethernet)               │
└─────────────────────────────────────┘
```

### **Core Components**
- **P2P Agents**: Symmetric peer agents with discovery
- **Transport Layer**: Pluggable transport abstraction
- **Protocol Core**: Message creation, parsing, validation
- **Memory State**: Routing, subscriptions, reliability, timers
- **Robustness**: Circuit breakers, timeouts, resource pools
- **Security**: Authentication, encryption, access control
- **Monitoring**: Health checks, metrics, alerting

---

## **Use Cases**

### **IoT & Edge Computing**
- Sensor networks and data collection
- Edge device coordination
- Industrial IoT applications
- Smart city infrastructure

### **Multi-Agent Systems**
- Distributed AI agents
- Autonomous vehicle coordination
- Robotic swarm communication
- Game AI and simulation

### **Microservices**
- Service-to-service communication
- Event-driven architectures
- Distributed tracing
- Health monitoring

### **Research & Development**
- Protocol research
- Network simulation
- Performance testing
- Academic projects

---

## **Protocol Bridges**

µACP provides seamless integration with existing protocols:

### **MQTT Bridge**
```python
from miuacp import MQTTBridge

bridge = MQTTBridge()
bridge.start()

# µACP messages automatically translated to MQTT
# MQTT messages automatically translated to µACP
```

### **CoAP Bridge**
```python
from miuacp import CoAPBridge

bridge = CoAPBridge()
bridge.start()

# Bidirectional translation between µACP and CoAP
```

### **MCP Bridge**
```python
from miuacp import MCPBridge

bridge = MCPBridge()
bridge.start()

# Full compatibility with Model Context Protocol
```

---

## **Documentation**

- **API Reference**: [GitHub Repository](https://github.com/Arnab-m1/miuACP)
- **Examples**: [Examples Directory](https://github.com/Arnab-m1/miuACP/tree/main/examples)
- **RFC Draft**: [RFC Documentation](https://github.com/Arnab-m1/miuACP/blob/main/RFC_DRAFT.md)
- **Contributing**: [Contributing Guide](https://github.com/Arnab-m1/miuACP/blob/main/CONTRIBUTING.md)
- **P2P Migration**: See [Migration Guide](#migration-from-v10-to-v20-p2p) above

---

## **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **Development Setup**
```bash
git clone https://github.com/Arnab-m1/miuACP.git
cd miuACP
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

### **Running Tests**
```bash
# Unit tests
pytest

# Integration tests
pytest tests/integration/

# P2P tests
pytest tests/test_udp_transport.py tests/test_p2p_agent.py -v

# Performance tests
python examples/comprehensive_benchmark.py
```

---

## **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## **Acknowledgments**

- **FIPA-ACL**: For agent communication language concepts
- **MQTT/CoAP**: For IoT protocol design patterns
- **MCP**: For modern agent protocol inspiration
- **CBOR**: For efficient data serialization
- **Python Community**: For excellent tooling and ecosystem

---

## **Support**

- **Issues**: [GitHub Issues](https://github.com/Arnab-m1/miuACP/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Arnab-m1/miuACP/discussions)
- **Email**: arnabb@duck.com
- **Repository**: [https://github.com/Arnab-m1/miuACP](https://github.com/Arnab-m1/miuACP)

---

**µACP v2.0** - True peer-to-peer agent communication for the edge!

*Built with ❤️ by [Arnab](https://arnab.wiki)*
