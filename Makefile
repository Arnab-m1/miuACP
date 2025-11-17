# Simple Makefile for miuACP C++ Library

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2 -Iinclude
LDFLAGS = -pthread

# Source files
SOURCES = src/option.cpp src/header.cpp src/message.cpp src/protocol.cpp
OBJECTS = $(SOURCES:.cpp=.o)

# Library name
LIBRARY = libmiuacp.a

# Example and test executables
EXAMPLES = examples/basic_usage
TESTS = tests/test_basic tests/test_comprehensive

.PHONY: all clean library examples tests

all: library examples tests

library: $(LIBRARY)

$(LIBRARY): $(OBJECTS)
	ar rcs $@ $^

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

examples: $(EXAMPLES)

examples/basic_usage: examples/basic_usage.cpp $(LIBRARY)
	$(CXX) $(CXXFLAGS) $< -L. -lmiuacp $(LDFLAGS) -o $@

tests: $(TESTS)

tests/test_basic: tests/test_basic.cpp $(LIBRARY)
	$(CXX) $(CXXFLAGS) $< -L. -lmiuacp $(LDFLAGS) -o $@

tests/test_comprehensive: tests/test_comprehensive.cpp $(LIBRARY)
	$(CXX) $(CXXFLAGS) $< -L. -lmiuacp $(LDFLAGS) -o $@

clean:
	rm -f $(OBJECTS) $(LIBRARY) $(EXAMPLES) $(TESTS)

install: library
	mkdir -p /usr/local/include/miuacp
	mkdir -p /usr/local/lib
	cp include/miuacp/*.h /usr/local/include/miuacp/
	cp $(LIBRARY) /usr/local/lib/

test: tests/test_basic
	./tests/test_basic

test-comprehensive: tests/test_comprehensive
	./tests/test_comprehensive

test-all: test test-comprehensive

run-example: examples/basic_usage
	./examples/basic_usage
