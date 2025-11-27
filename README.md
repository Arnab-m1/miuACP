# µACP (Micro Agent Communication Protocol)

[![PyPI version](https://badge.fury.io/py/miuacp.svg)](https://badge.fury.io/py/miuacp)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/Arnab-m1/miuACP)
[![Python versions](https://img.shields.io/pypi/pyversions/miuacp.svg)](https://pypi.org/project/miuacp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/GitHub-miuACP-blue.svg)](https://github.com/Arnab-m1/miuACP)
[![GitHub stars](https://img.shields.io/github/stars/Arnab-m1/miuACP.svg)](https://github.com/Arnab-m1/miuACP/stargazers)

**µACP** is a lightweight, agent-centric communication protocol designed for edge-native multi-agent systems. It combines the efficiency of IoT protocols with the semantic richness of agent communication languages, making it ideal for lightweight AI agents, IoT devices, and edge computing environments.

## **Key Features**

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

## **Quick Start**

### **Basic Message Creation**
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

### **Agent Communication**
```python
from miuacp import UACPAgent, UACPServer

# Create agent
agent = UACPAgent("sensor_agent")

# Start server
server = UACPServer("0.0.0.0", 8080)
await server.start()

# Send message
await agent.send_message(
    "192.168.1.100:8080",
    UACPVerb.TELL,
    "Temperature: 25°C".encode(),
    options=[UACPOption(UACPOptionType.TOPIC_PATH, "sensors/temp")]
)
```

## **Advanced Usage**

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

##  **Architecture**

### **Protocol Layers**
```
┌─────────────────────────────────────┐
│           Application               │
├─────────────────────────────────────┤
│           µACP Protocol             │
├─────────────────────────────────────┤
│         Transport Layer             │
│    (UDP/TCP/WebSocket/QUIC)         │
├─────────────────────────────────────┤
│         Security Layer              │
│      (TLS/DTLS/JWT/OAuth2)          │
├─────────────────────────────────────┤
│         Network Layer               │
│         (IP/Ethernet)               │
└─────────────────────────────────────┘
```

### **Core Components**
- **Protocol Core**: Message creation, parsing, validation
- **Memory State**: Routing, subscriptions, reliability, timers
- **Robustness**: Circuit breakers, timeouts, resource pools
- **Transport**: Multiple transport bindings
- **Security**: Authentication, encryption, access control
- **Monitoring**: Health checks, metrics, alerting

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

## **Development Tools**

### **CLI Tools**
```bash
# Agent management
uacp-agent --help

# Client operations
uacp-client --help

# Server management
uacp-server --help
```

### **Testing & Benchmarking**
```bash
# Run integration tests
python -m pytest tests/

# Run performance benchmarks
python examples/comprehensive_benchmark.py

# Run protocol comparison
python examples/protocol_comparison_benchmark.py
```

### **Monitoring & Debugging**
```python
from miuacp import UACPInstrumentation

# Enable debug logging
instrumentation = UACPInstrumentation()
instrumentation.set_log_level(LogLevel.DEBUG)

# Record custom metrics
instrumentation.increment_counter("messages_sent", 1)
instrumentation.record_gauge("queue_size", 42)
```

## **Documentation**

- **API Reference**: [GitHub Repository](https://github.com/Arnab-m1/miuACP)
- **Examples**: [Examples Directory](https://github.com/Arnab-m1/miuACP/tree/main/examples)
- **RFC Draft**: [RFC Documentation](https://github.com/Arnab-m1/miuACP/blob/main/RFC_DRAFT.md)
- **Contributing**: [Contributing Guide](https://github.com/Arnab-m1/miuACP/blob/main/CONTRIBUTING.md)

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

# Performance tests
python examples/comprehensive_benchmark.py
```

## **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## **Acknowledgments**

- **FIPA-ACL**: For agent communication language concepts
- **MQTT/CoAP**: For IoT protocol design patterns
- **MCP**: For modern agent protocol inspiration
- **CBOR**: For efficient data serialization
- **Python Community**: For excellent tooling and ecosystem

## **Support**

- **Issues**: [GitHub Issues](https://github.com/Arnab-m1/miuACP/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Arnab-m1/miuACP/discussions)
- **Email**: hello@arnab.wiki
- **Repository**: [https://github.com/Arnab-m1/miuACP](https://github.com/Arnab-m1/miuACP)

---

**µACP** - Making agent communication lightweight, robust, and efficient!

*Built with ❤️ by [Arnab](https://arnab.wiki)*
