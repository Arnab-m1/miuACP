cmake_minimum_required(VERSION 3.12)
project(miuacp VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set build type to Release if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -Wall -Wextra -Wpedantic")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -Wall -Wextra")

# Include directories
include_directories(include)

# Source files
set(MIUACP_SOURCES
    src/option.cpp
    src/header.cpp
    src/message.cpp
    src/protocol.cpp
    src/udp_transport.cpp
    src/agent.cpp
    # Note: client.cpp and server.cpp are deprecated in favor of P2P agent
)

# Header files
set(MIUACP_HEADERS
    include/miuacp/miuacp.h
    include/miuacp/enums.h
    include/miuacp/header.h
    include/miuacp/option.h
    include/miuacp/message.h
    include/miuacp/protocol.h
    include/miuacp/transport.h
    include/miuacp/udp_transport.h
    include/miuacp/agent.h
)

# Create static library
add_library(miuacp_static STATIC ${MIUACP_SOURCES})
target_include_directories(miuacp_static PUBLIC include)
set_target_properties(miuacp_static PROPERTIES
    OUTPUT_NAME miuacp
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
)

# Create shared library
add_library(miuacp_shared SHARED ${MIUACP_SOURCES})
target_include_directories(miuacp_shared PUBLIC include)
set_target_properties(miuacp_shared PROPERTIES
    OUTPUT_NAME miuacp
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
)

# Create alias for the library (defaults to shared)
add_library(miuacp ALIAS miuacp_shared)

# Install targets
install(TARGETS miuacp_static miuacp_shared
    EXPORT miuacpTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
    INCLUDES DESTINATION include
)

# Install headers
install(FILES ${MIUACP_HEADERS}
    DESTINATION include/miuacp
)

# Install CMake config files
install(EXPORT miuacpTargets
    FILE miuacpTargets.cmake
    NAMESPACE miuacp::
    DESTINATION lib/cmake/miuacp
)

# Create config file
include(CMakePackageConfigHelpers)
write_basic_package_version_file(
    miuacpConfigVersion.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY AnyNewerVersion
)

configure_package_config_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/cmake/miuacpConfig.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/miuacpConfig.cmake
    INSTALL_DESTINATION lib/cmake/miuacp
)

install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/miuacpConfig.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/miuacpConfigVersion.cmake
    DESTINATION lib/cmake/miuacp
)

# Enable testing
enable_testing()

# Add tests if they exist
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/tests)
    add_subdirectory(tests)
endif()

# Add examples if they exist
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/examples)
    add_subdirectory(examples)
endif()

# Print configuration summary
message(STATUS "miuACP C++ Library Configuration:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "  Static library: miuacp_static")
message(STATUS "  Shared library: miuacp_shared")
