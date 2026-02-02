# Simple Makefile for miuACP C++ Library (P2P Architecture)

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2 -Iinclude
LDFLAGS = -pthread

# Source files (P2P architecture with UDP transport)
SOURCES = src/option.cpp src/header.cpp src/message.cpp src/protocol.cpp src/udp_transport.cpp src/agent.cpp
OBJECTS = $(SOURCES:.cpp=.o)

# Library name
LIBRARY = libmiuacp.a

# P2P Examples
EXAMPLES = examples/peer_ping_pong examples/agent_discovery examples/smart_factory_p2p

# P2P Tests
TESTS = tests/test_udp_transport tests/test_agent_p2p

# Benchmark
BENCHMARK = benchmark

.PHONY: all clean library examples tests install benchmark

all: library examples tests

library: $(LIBRARY)

$(LIBRARY): $(OBJECTS)
	ar rcs $@ $^

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Examples
examples: $(EXAMPLES)

examples/peer_ping_pong: examples/peer_ping_pong.cpp $(LIBRARY)
	$(CXX) $(CXXFLAGS) $< -L. -lmiuacp $(LDFLAGS) -o $@

examples/agent_discovery: examples/agent_discovery.cpp $(LIBRARY)
	$(CXX) $(CXXFLAGS) $< -L. -lmiuacp $(LDFLAGS) -o $@

examples/smart_factory_p2p: examples/smart_factory_p2p.cpp $(LIBRARY)
	$(CXX) $(CXXFLAGS) $< -L. -lmiuacp $(LDFLAGS) -o $@

# Tests
tests: $(TESTS)

tests/test_udp_transport: tests/test_udp_transport.cpp $(LIBRARY)
	$(CXX) $(CXXFLAGS) $< -L. -lmiuacp $(LDFLAGS) -o $@

tests/test_agent_p2p: tests/test_agent_p2p.cpp $(LIBRARY)
	$(CXX) $(CXXFLAGS) $< -L. -lmiuacp $(LDFLAGS) -o $@

# Benchmark
benchmark: $(BENCHMARK)

$(BENCHMARK): benchmark.cpp $(LIBRARY)
	$(CXX) $(CXXFLAGS) $< -L. -lmiuacp $(LDFLAGS) -o $@

# Clean
clean:
	rm -f $(OBJECTS) $(LIBRARY) $(EXAMPLES) $(TESTS) $(BENCHMARK)
	rm -f src/client.o src/server.o  # Clean old files too

# Install
install: library
	mkdir -p /usr/local/include/miuacp
	mkdir -p /usr/local/lib
	cp include/miuacp/*.h /usr/local/include/miuacp/
	cp $(LIBRARY) /usr/local/lib/

# Test targets
test: tests/test_udp_transport tests/test_agent_p2p
	@echo "========================================"
	@echo "Running UDP Transport Tests..."
	@echo "========================================"
	./tests/test_udp_transport
	@echo ""
	@echo "========================================"
	@echo "Running Agent P2P Tests..."
	@echo "========================================"
	./tests/test_agent_p2p

test-udp: tests/test_udp_transport
	./tests/test_udp_transport

test-agent: tests/test_agent_p2p
	./tests/test_agent_p2p

test-all: test

# Run examples
run-ping-pong: examples/peer_ping_pong
	@echo "Run './examples/peer_ping_pong receiver' in one terminal"
	@echo "Run './examples/peer_ping_pong sender' in another terminal"

run-discovery: examples/agent_discovery
	@echo "Run './examples/agent_discovery agent1 8001' in terminal 1"
	@echo "Run './examples/agent_discovery agent2 8002' in terminal 2"
	@echo "Run './examples/agent_discovery agent3 8003' in terminal 3"

run-factory: examples/smart_factory_p2p
	./examples/smart_factory_p2p

run-benchmark: benchmark
	./benchmark

# Help
help:
	@echo "miuACP P2P Library - Makefile Targets"
	@echo "======================================"
	@echo "  make              - Build library, examples, tests, and benchmark"
	@echo "  make library      - Build static library only"
	@echo "  make examples     - Build all examples"
	@echo "  make tests        - Build all tests"
	@echo "  make benchmark    - Build performance benchmark"
	@echo "  make test         - Run all tests"
	@echo "  make test-udp     - Run UDP transport tests"
	@echo "  make test-agent   - Run agent P2P tests"
	@echo "  make run-factory  - Run smart factory demo"
	@echo "  make run-benchmark - Run performance benchmark"
	@echo "  make clean        - Remove built files"
	@echo "  make install      - Install library and headers"
	@echo "  make help         - Show this help message"
