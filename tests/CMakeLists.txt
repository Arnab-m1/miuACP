# Tests CMakeLists.txt

# Basic tests
add_executable(test_basic test_basic.cpp)
target_link_libraries(test_basic miuacp)

# Set output directory
set_target_properties(test_basic PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Add test to CTest
add_test(NAME BasicTests COMMAND test_basic)
