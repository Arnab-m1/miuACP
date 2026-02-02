# µACP Library - Peer-to-Peer Multi-Agent Communication

[![Version](https://img.shields.io/badge/version-2.0.0--P2P-blue.svg)](https://github.com/Arnab-m1/miuACP)
[![C++](https://img.shields.io/badge/C%2B%2B-17-blue.svg)](https://en.cppreference.com/w/cpp/17)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-15%2F15%20passing-brightgreen.svg)](#testing)

**µACP C++** is a lightweight, high-performance peer-to-peer multi-agent communication library. Designed for edge-native systems, it enables direct agent-to-agent communication without central servers or brokers.

## 🎉 What's New in v2.0 (P2P Architecture)

**Major architectural redesign from client/server to symmetric peer-to-peer:**

- ✨ **True P2P**: All agents are equal peers - no client/server distinction
- 🚀 **UDP Transport**: Connectionless, low-latency peer communication
- 📡 **Auto-Discovery**: Agents find each other via UDP broadcast  
- 🎯 **Topic Routing**: Publish/subscribe with wildcard matching
- 📊 **Built-in Stats**: Track messages, bytes, and peer connections
- 🧪 **15/15 Tests Passing**: Comprehensive test coverage

---

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Examples](#examples)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Performance](#performance)
- [Migration Guide](#migration-guide)
- [Contributing](#contributing)

---

## ✨ Features

### Core Protocol
- **Fixed 8-byte header** for minimal overhead
- **4 semantic verbs**: PING, TELL, ASK, OBSERVE
- **TLV options** for extensibility
- **QoS levels**: At-most-once, at-least-once, exactly-once
- **Topic-based routing** with wildcard support (`#`, `*`)

### P2P Architecture
- **Symmetric peers**: Every agent can send AND receive
- **Direct communication**: No central broker required
- **UDP broadcast discovery**: Agents find peers automatically
- **Multicast support**: Efficient topic-based pub/sub
- **Peer registry**: Track discovered agents

### C++ Features
- **Modern C++17** with move semantics
- **Zero external dependencies** for core
- **Thread-safe** message handling
- **RAII** resource management
- **Exception-safe** design

### Performance
- **High throughput**: 1,500+ messages/sec per agent
- **Low latency**: Sub-100ms on local network
- **Minimal memory**: Optimized for edge devices
- **Scalable**: Tested with multiple simultaneous agents

---

## 📦 Installation

### Building from Source

```bash
# Clone repository
git clone https://github.com/Arnab-m1/miuACP.git
cd miuACP

# Build with Makefile (recommended)
make all

# Or build with CMake
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

# Install (optional)
sudo make install
```

### Using with CMake

```cmake
find_package(miuacp REQUIRED)
target_link_libraries(your_target miuacp)
```

### Manual Integration

Copy `include/miuacp/` to your project:

```cpp
#include "miuacp/agent.h"
```

---

## 🚀 Quick Start

### Creating a Peer Agent

```cpp
#include "miuacp/agent.h"

using namespace miuacp;

int main() {
    // Create agent on port 8001
    UACPAgent agent("my-agent", "My Agent", "0.0.0.0", 8001);
    
    // Start agent (binds UDP socket, starts receiver)
    agent.start();
    
    // Keep running...
    std::this_thread::sleep_for(std::chrono::minutes(5));
    
    agent.stop();
    return 0;
}
```

### Sending Messages to Peers

```cpp
// PING another agent
agent.ping("192.168.1.100", 8002);

// Send TELL message
agent.tell("192.168.1.100", 8002, "Hello, peer!", "chat/messages");

// Send ASK request
auto response = agent.ask("192.168.1.100", 8002, 
                         "Get temperature", "sensors/temp");

// Subscribe to peer's topic
agent.observe("192.168.1.100", 8002, "alerts/#");
```

### Handling Incoming Messages

```cpp
// Add message handler for PING
agent.addMessageHandler(UACPVerb::PING,
    [](const UACPMessage& msg, const std::string& sender, int port) {
        std::cout << "PING from " << sender << ":" << port << std::endl;
        return msg.createResponse(StatusCode::SUCCESS, "pong");
    });

// Add topic handler with wildcards
agent.addTopicHandler("sensors/#",
    [](const UACPMessage& msg, const std::string& sender, int port) {
        std::string topic = msg.getTopicPath();
        std::string data = msg.getPayloadAsString();
        std::cout << "Sensor data on " << topic << ": " << data << std::endl;
        return msg.createResponse(StatusCode::SUCCESS);
    });
```

### Peer Discovery

```cpp
// Broadcast discovery message
agent.discoverPeers("255.255.255.255", 8001);

// Get discovered peers
auto peers = agent.getDiscoveredPeers();
for (const auto& peer : peers) {
    std::cout << "Found peer: " << peer << std::endl;
}
```

---

## 📚 Examples

### 1. Peer Ping-Pong

Two agents communicate directly:

```bash
# Terminal 1 (receiver)
./examples/peer_ping_pong receiver

# Terminal 2 (sender)
./examples/peer_ping_pong sender
```

### 2. Agent Discovery

Multiple agents discover each other:

```bash
# Run in separate terminals
./examples/agent_discovery agent1 8001
./examples/agent_discovery agent2 8002
./examples/agent_discovery agent3 8003
```

### 3. Smart Factory P2P

5 agents coordinate manufacturing:

```bash
./examples/smart_factory_p2p
```

Output:
```
🏭 [Coordinator] Starting production cycle #1
🤖 [Robot Arm] Command received: Start assembly
🛤️  [Conveyor] Command received: Move batch
🔍 [QC] Inspection passed! ✓
📦 [Warehouse] Inventory updated: 110 units
```

---

## 📖 API Reference

### UACPAgent

Main class for peer-to-peer communication.

#### Lifecycle

```cpp
UACPAgent(const std::string& agent_id,
          const std::string& name,
          const std::string& host,
          int port,
          std::unique_ptr<UACPTransport> transport = nullptr);

bool start();   // Bind transport, start receiver thread
void stop();    // Stop receiver, close transport
bool isRunning() const;
```

#### Send Methods

```cpp
// PING a peer
bool ping(const std::string& peer_host, int peer_port);

// Send TELL message
bool tell(const std::string& peer_host, int peer_port,
          const std::string& payload,
          const std::string& topic = "",
          uint8_t qos = 0);

// Send ASK request
UACPMessage ask(const std::string& peer_host, int peer_port,
                const std::string& payload,
                const std::string& topic = "",
                uint8_t qos = 1,
                std::chrono::milliseconds timeout = 5000ms);

// Subscribe to topic
bool observe(const std::string& peer_host, int peer_port,
             const std::string& topic,
             uint8_t qos = 1);
```

#### Message Handlers

```cpp
using MessageHandler = std::function<UACPMessage(
    const UACPMessage&, const std::string&, int)>;

// Add verb-based handler
void addMessageHandler(UACPVerb verb, MessageHandler handler);

// Add topic-based handler (supports wildcards: *, #)
void addTopicHandler(const std::string& topic_pattern,
                     TopicHandler handler);

// Remove handlers
bool removeMessageHandler(UACPVerb verb);
bool removeTopicHandler(const std::string& topic_pattern);
```

#### Peer Management

```cpp
// Discover peers via broadcast
int discoverPeers(const std::string& broadcast_addr, int port);

// Manual peer management
void addPeer(const std::string& host, int port,
             const std::string& peer_id = "");
void removePeer(const std::string& host, int port);

// Query peers
std::vector<std::string> getDiscoveredPeers() const;
const UACPPeerInfo* getPeerInfo(const std::string& host, int port) const;
```

#### Statistics

```cpp
std::map<std::string, uint64_t> getStatistics() const;
// Returns: messages_sent, messages_received, bytes_sent,
//          bytes_received, peers, subscriptions
```

### UACPTransport (Abstract Interface)

Base class for all transports (UDP, TCP, etc.).

```cpp
virtual bool bind(const std::string& host, int port) = 0;
virtual bool sendToPeer(const std::vector<uint8_t>& data,
                       const std::string& peer_host, int peer_port) = 0;
virtual std::vector<uint8_t> receiveFromPeer(int timeout_ms,
                                             std::string& sender_host,
                                             int& sender_port) = 0;
virtual bool enableBroadcast() = 0;
virtual bool enableMulticast(const std::string& group, int port) = 0;
```

---

## 🧪 Testing

### Run All Tests

```bash
make test
```

### Run Specific Tests

```bash
make test-udp      # UDP transport tests (7 tests)
make test-agent    # Agent P2P tests (8 tests)
```

### Test Coverage

**UDP Transport (7/7 ✅)**
- Basic peer-to-peer send/receive
- Ephemeral port assignment  
- Receive timeout handling
- Broadcast discovery
- Multi-agent communication (4 agents)
- Large packet handling (32KB)
- Move semantics

**Agent P2P (8/8 ✅)**
- Agent lifecycle (start/stop)
- Ephemeral port assignment
- Peer-to-peer PING
- Peer-to-peer TELL  
- Topic-based message handlers
- Peer discovery
- Peer registry management
- Statistics tracking

**Total: 15/15 tests passing**

---

## 📊 Performance

From benchmarking on Intel i5 @ 2.4GHz, 8GB RAM:

| Metric | Value |
|--------|-------|
| Messages/sec | 1,500+ per agent |
| Throughput | ~20 KB/sec per agent |
| Latency (local) | < 100ms |
| Memory/agent | ~5 MB |
| Max tested agents | 5 simultaneous |

Run benchmarks:

```bash
make benchmark
./benchmark
```

---

## 🔄 Migration Guide

### From v1.0 (Client/Server) to v2.0 (P2P)

**Old Code (v1.0):**
```cpp
// Client side
UACPClient client;
client.connect("server.local", 8080);
client.sendTell("Hello", "topic");
client.disconnect();

// Server side  
UACPServer server(8080);
server.addHandler(UACPVerb::TELL, handler);
server.start();
```

**New Code (v2.0):**
```cpp
// Both are symmetric peers now!
UACPAgent agent1("agent1", "Agent 1", "0.0.0.0", 8001);
agent1.start();
agent1.tell("192.168.1.100", 8002, "Hello", "topic");

UACPAgent agent2("agent2", "Agent 2", "0.0.0.0", 8002);
agent2.addTopicHandler("topic", handler);
agent2.start();
```

### Key Changes

1. **No `UACPClient`/`UACPServer`** - Use `UACPAgent` for everything
2. **No `connect()`** - Send directly to any peer's `host:port`
3. **All agents can send + receive** - Symmetric design
4. **Built-in discovery** - Use `discoverPeers()` instead of hardcoded IPs

---

## 🏗️ Build System

### Makefile Targets

```bash
make all           # Build library, examples, tests
make library       # Build static library only
make examples      # Build all examples
make tests         # Build all tests
make test          # Build and run all tests
make clean         # Remove built files
make install       # Install library and headers
make help          # Show all targets
```

### CMake Options

```bash
cmake .. -DCMAKE_BUILD_TYPE=Release    # Release build
cmake .. -DCMAKE_BUILD_TYPE=Debug      # Debug build
cmake .. -DBUILD_EXAMPLES=ON           # Include examples
cmake .. -DBUILD_TESTING=ON            # Include tests
```

---

## 📁 Project Structure

```
miuACP/
├── include/miuacp/
│   ├── transport.h          # Transport abstraction
│   ├── udp_transport.h      # UDP P2P implementation
│   ├── agent.h              # Peer agent (P2P)
│   ├── message.h            # µACP messages
│   ├── protocol.h           # Protocol utilities
│   ├── enums.h              # Protocol enums
│   ├── header.h             # Message headers
│   └── option.h             # TLV options
├── src/
│   ├── udp_transport.cpp    # UDP implementation
│   ├── agent.cpp            # Agent implementation
│   └── [protocol files]
├── tests/
│   ├── test_udp_transport.cpp   # Transport tests
│   └── test_agent_p2p.cpp       # Agent tests
├── examples/
│   ├── peer_ping_pong.cpp       # 2-agent demo
│   ├── agent_discovery.cpp      # Discovery demo
│   └── smart_factory_p2p.cpp    # 5-agent factory
├── CMakeLists.txt
├── Makefile
└── README.md
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass (`make test`)
5. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🔗 Links

- **GitHub**: https://github.com/Arnab-m1/miuACP
- **Python Version**: https://github.com/Arnab-m1/miuACP/tree/python-lib
- **Documentation**: See `docs/` directory
- **Issues**: https://github.com/Arnab-m1/miuACP/issues

---

## 💡 Use Cases

- **IoT Edge Networks**: Lightweight agent communication on resource-constrained devices
- **Multi-Agent Systems**: Coordinate autonomous agents without central control
- **Distributed Sensors**: Sensor networks with peer-to-peer data sharing
- **Smart Manufacturing**: Factory automation with decentralized coordination
- **Robotics**: Multi-robot systems with direct communication

---

## 🙏 Acknowledgments

Built with inspiration from CoAP, MQTT, and modern multi-agent system architectures.

**All agents are now equal peers!** 🎉
