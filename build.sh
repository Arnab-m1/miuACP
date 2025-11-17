#!/bin/bash

# µACP C++ Library Build Script
# This script builds the library, runs tests, and creates examples

set -e  # Exit on any error

echo "µACP C++ Library Build Script"
echo "============================="

# Clean previous builds
echo "Cleaning previous builds..."
make clean

# Build the library
echo "Building library..."
make library

# Run tests
echo "Running tests..."
make test

# Build and run example
echo "Building and running example..."
make run-example

echo ""
echo "Build completed successfully!"
echo ""
echo "Library files created:"
echo "  - libmiuacp.a (static library)"
echo "  - tests/test_basic (test executable)"
echo "  - examples/basic_usage (example executable)"
echo ""
echo "To install the library system-wide:"
echo "  sudo make install"
echo ""
echo "To use the library in your project:"
echo "  g++ -std=c++17 -Iinclude your_code.cpp -L. -lmiuacp -pthread"
