# µACP C++ Library

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/Arnab-m1/miuACP)
[![C++](https://img.shields.io/badge/C%2B%2B-17-blue.svg)](https://en.cppreference.com/w/cpp/17)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CMake](https://img.shields.io/badge/CMake-3.12%2B-green.svg)](https://cmake.org/)

**µACP C++** is a lightweight, high-performance C++ implementation of the Micro Agent Communication Protocol, designed for edge-native multi-agent systems. It provides efficient message handling, protocol compliance, and easy integration into C++ applications.

## **Key Features**

### **Core Protocol**
- **Fixed 8-byte header** for maximum efficiency
- **4 semantic verbs**: PING, TELL, ASK, OBSERVE
- **TLV options** for extensibility
- **QoS levels**: At-most-once, at-least-once, exactly-once
- **High-performance** message packing/unpacking

### **C++ Specific Features**
- **Modern C++17** implementation
- **Header-only** core components
- **CMake** build system
- **Cross-platform** compatibility
- **Zero external dependencies** for core functionality
- **Exception-safe** design
- **RAII** resource management

### **Performance**
- **Minimal overhead** message processing
- **Efficient memory usage**
- **Fast serialization/deserialization**
- **Optimized for embedded systems**

## **Installation**

### **Building from Source**

```bash
# Clone the repository
git clone https://github.com/Arnab-m1/miuACP.git
cd miuACP/miuACP-c

# Create build directory
mkdir build && cd build

# Configure with CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build the library
make -j$(nproc)

# Install (optional)
sudo make install
```

### **Using with CMake**

```cmake
# Find the package
find_package(miuacp REQUIRED)

# Link to your target
target_link_libraries(your_target miuacp)
```

### **Manual Integration**

Simply copy the `include/miuacp/` directory to your project and include the headers:

```cpp
#include "miuacp/miuacp.h"
```

## **Quick Start**

### **Basic Message Creation**

```cpp
#include "miuacp/miuacp.h"
#include <iostream>

using namespace miuacp;

int main() {
    // Create protocol instance
    UACPProtocol protocol;
    
    // Create a simple PING message
    UACPMessage ping = protocol.createPing();
    
    // Create a TELL message with payload
    UACPMessage tell = protocol.createTell("Hello, World!", "greetings/hello");
    
    // Pack messages for transmission
    std::vector<uint8_t> ping_data = ping.pack();
    std::vector<uint8_t> tell_data = tell.pack();
    
    std::cout << "PING message size: " << ping_data.size() << " bytes" << std::endl;
    std::cout << "TELL message size: " << tell_data.size() << " bytes" << std::endl;
    
    return 0;
}
```

### **Message with Options**

```cpp
// Create message with custom options
UACPMessage message = protocol.createTell("Temperature: 25°C", "sensors/temp");
message.addOption(UACPOptionType::PRIORITY, 5u);
message.addOption(UACPOptionType::MAX_AGE, 3600u);
message.setContentType(UACPContentType::JSON);

// Pack and send
std::vector<uint8_t> data = message.pack();
```

### **Message Unpacking**

```cpp
// Unpack received message
UACPMessage received = UACPMessage::unpack(received_data);

// Access message components
UACPVerb verb = received.getHeader().getVerb();
std::string payload = received.getPayloadAsString();
std::string topic = received.getTopicPath();

// Check if it's a request or response
if (received.isRequest()) {
    // Handle request
    UACPMessage response = received.createResponse(StatusCode::SUCCESS, "OK");
    send(response.pack());
}
```

## **API Reference**

### **Core Classes**

#### **UACPProtocol**
Main protocol interface for creating and managing messages.

```cpp
class UACPProtocol {
public:
    UACPMessage createPing(uint32_t msg_id = 0) const;
    UACPMessage createTell(const std::string& payload, 
                          const std::string& topic = "", 
                          uint32_t msg_id = 0, 
                          uint8_t qos = 0) const;
    UACPMessage createAsk(const std::string& payload, 
                         const std::string& topic = "", 
                         uint32_t msg_id = 0, 
                         uint8_t qos = 1) const;
    UACPMessage createObserve(const std::string& payload, 
                             const std::string& topic, 
                             uint32_t msg_id = 0, 
                             uint8_t qos = 1) const;
    uint32_t generateMessageId();
    bool validateMessage(const UACPMessage& message) const;
};
```

#### **UACPMessage**
Represents a complete µACP message with header, options, and payload.

```cpp
class UACPMessage {
public:
    // Message creation and modification
    void addOption(UACPOptionType type, const std::string& value);
    void addOption(UACPOptionType type, uint32_t value);
    void setPayload(const std::string& payload);
    void setTopicPath(const std::string& topic);
    void setContentType(UACPContentType type);
    
    // Message access
    const UACPHeader& getHeader() const;
    const std::vector<UACPOption>& getOptions() const;
    const std::vector<uint8_t>& getPayload() const;
    std::string getPayloadAsString() const;
    std::string getTopicPath() const;
    UACPContentType getContentType() const;
    
    // Message operations
    std::vector<uint8_t> pack() const;
    static UACPMessage unpack(const std::vector<uint8_t>& data);
    UACPMessage createResponse(StatusCode code, const std::string& payload) const;
    
    // Validation
    bool isValid() const;
    bool isRequest() const;
    bool isResponse() const;
};
```

#### **UACPHeader**
Fixed 8-byte header containing protocol information.

```cpp
class UACPHeader {
public:
    // Getters
    uint8_t getVersion() const;
    UACPVerb getVerb() const;
    uint8_t getQoS() const;
    uint8_t getCode() const;
    uint32_t getMessageId() const;
    uint8_t getOptionsCount() const;
    
    // Setters
    void setVersion(uint8_t version);
    void setVerb(UACPVerb verb);
    void setQoS(uint8_t qos);
    void setCode(uint8_t code);
    void setMessageId(uint32_t msg_id);
    void setOptionsCount(uint8_t opts_count);
    
    // Operations
    std::vector<uint8_t> pack() const;
    static UACPHeader unpack(const std::vector<uint8_t>& data);
    bool isValid() const;
    static UACPHeader createResponse(const UACPHeader& request, StatusCode code);
};
```

#### **UACPOption**
Type-Length-Value option for message extensibility.

```cpp
class UACPOption {
public:
    // Constructors
    UACPOption(UACPOptionType type, const std::string& value);
    UACPOption(UACPOptionType type, uint32_t value);
    UACPOption(UACPOptionType type, const std::vector<uint8_t>& value);
    
    // Access
    UACPOptionType getType() const;
    std::string getStringValue() const;
    uint32_t getIntValue() const;
    const std::vector<uint8_t>& getBytesValue() const;
    
    // Operations
    std::vector<uint8_t> pack() const;
    static size_t unpack(const std::vector<uint8_t>& data, size_t offset, UACPOption& option);
    size_t getPackedSize() const;
};
```

### **Enums and Constants**

```cpp
// Protocol verbs
enum class UACPVerb : uint8_t {
    PING = 0,      // Liveness check
    TELL = 1,      // Inform (pub/sub)
    ASK = 2,       // Request/response (RPC)
    OBSERVE = 3    // Subscription
};

// Option types
enum class UACPOptionType : uint8_t {
    CONVERSATION_ID = 0x01,
    CORRELATION_ID = 0x02,
    TOPIC_PATH = 0x03,
    CONTENT_TYPE = 0x04,
    ETAG = 0x05,
    MAX_AGE = 0x06,
    BLOCK = 0x07,
    AUTH = 0x08,
    PRIORITY = 0x09
};

// Content types
enum class UACPContentType : uint8_t {
    CBOR = 0,      // Default
    JSON = 1,
    PROTOBUF = 2,
    TEXT = 3
};

// Status codes
enum class StatusCode : uint8_t {
    SUCCESS = 0,
    BAD_REQUEST = 1,
    UNAUTHORIZED = 2,
    // ... more status codes
};
```

## **Performance Characteristics**

The C++ implementation provides excellent performance:

|         Metric        |     Value   |                Notes            |
|-----------------------|-------------|---------------------------------|
| **Message Creation**  | < 1μs       | Typical message creation time   |
| **Message Packing**   | < 2μs       | Serialization to binary format  |
| **Message Unpacking** | < 3μs       | Deserialization from binary     |
| **Memory Overhead**   | < 100 bytes | Per message object              |
| **Binary Size**       | ~50KB       | Static library size             |

## **Architecture**

### **Protocol Structure**
```
┌─────────────────────────────────────┐
│           Application               │
├─────────────────────────────────────┤
│           µACP C++ Library          │
│    (UACPProtocol, UACPMessage)      │
├─────────────────────────────────────┤
│         Transport Layer             │
│    (UDP/TCP/WebSocket/QUIC)         │
├─────────────────────────────────────┤
│         Network Layer               │
│         (IP/Ethernet)               │
└─────────────────────────────────────┘
```

### **Message Format**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   Header    │   Options   │   Payload   │   Padding   │
│   (8 bytes) │  (variable) │  (variable) │   (if any)  │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

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

## **Examples**

### **Running Examples**

```bash
# Build examples
cd build
make basic_usage

# Run basic usage example
./bin/basic_usage
```

### **Example Output**
```
µACP C++ Library - Basic Usage Example
=====================================
Library Version: 1.0.0
Author: Arnab

Example 1: PING Message
----------------------
Message Info:
  Verb: 0
  Message ID: 12345
  QoS: 0
  Code: 0
  Options Count: 0
  Payload Size: 0 bytes
  Total Size: 8 bytes
```

## **Development**

### **Building for Development**

```bash
# Debug build
cmake .. -DCMAKE_BUILD_TYPE=Debug
make -j$(nproc)

# Run tests
make test
```

### **Code Style**
- Follow C++17 standards
- Use RAII principles
- Exception-safe design
- Clear documentation

### **Contributing**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## **Documentation**

- **API Reference**: See header files in `include/miuacp/`
- **Examples**: See `examples/` directory
- **Python Version**: [miuACP Python Library](https://github.com/Arnab-m1/miuACP)
- **Protocol Specification**: [RFC Draft](https://github.com/Arnab-m1/miuACP/blob/main/RFC_DRAFT.md)

## **Related Projects**

- **miuACP Python**: Original Python implementation
- **miuACP Tools**: Development and testing tools
- **Protocol Bridges**: MQTT, CoAP, MCP integration

## **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## **Acknowledgments**

- **FIPA-ACL**: For agent communication language concepts
- **MQTT/CoAP**: For IoT protocol design patterns
- **MCP**: For modern agent protocol inspiration
- **C++ Community**: For excellent tooling and ecosystem

## **Support**

- **Issues**: [GitHub Issues](https://github.com/Arnab-m1/miuACP/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Arnab-m1/miuACP/discussions)
- **Email**: 
- **Repository**: [https://github.com/Arnab-m1/miuACP](https://github.com/Arnab-m1/miuACP)

---

**µACP C++** - Making agent communication lightweight, robust, and efficient! 

*Built with ❤️ by [Arnab](https://arnab-m1.github.io)*