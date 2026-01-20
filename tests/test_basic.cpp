/**
 * @file test_basic.cpp
 * @brief Basic tests for µACP C++ Library
 * 
 * Simple tests to verify the basic functionality of the µACP library.
 */

#include <iostream>
#include <cassert>
#include "miuacp/miuacp.h"

using namespace miuacp;

void testVersionInfo() {
    std::cout << "Testing version info..." << std::endl;
    
    assert(std::string(getVersion()) == "1.0.0");
    assert(std::string(getAuthor()) == "Arnab");
    assert(std::string(getEmail()) == "hello@arnab.wiki");
    assert(std::string(getLicense()) == "MIT");
    
    int major, minor, patch;
    getVersionComponents(major, minor, patch);
    assert(major == 1);
    assert(minor == 0);
    assert(patch == 0);
    
    std::cout << "✓ Version info test passed" << std::endl;
}

void testEnums() {
    std::cout << "Testing enums..." << std::endl;
    
    assert(static_cast<int>(UACPVerb::PING) == 0);
    assert(static_cast<int>(UACPVerb::TELL) == 1);
    assert(static_cast<int>(UACPVerb::ASK) == 2);
    assert(static_cast<int>(UACPVerb::OBSERVE) == 3);
    
    assert(static_cast<int>(UACPOptionType::CONVERSATION_ID) == 0x01);
    assert(static_cast<int>(UACPOptionType::TOPIC_PATH) == 0x03);
    
    assert(static_cast<int>(UACPContentType::CBOR) == 0);
    assert(static_cast<int>(UACPContentType::JSON) == 1);
    
    std::cout << "✓ Enums test passed" << std::endl;
}

void testHeader() {
    std::cout << "Testing header..." << std::endl;
    
    // Test header creation
    UACPHeader header(1, UACPVerb::TELL, 1, 0, 12345, 2);
    assert(header.getVersion() == 1);
    assert(header.getVerb() == UACPVerb::TELL);
    assert(header.getQoS() == 1);
    assert(header.getCode() == 0);
    assert(header.getMessageId() == 12345);
    assert(header.getOptionsCount() == 2);
    assert(header.isValid());
    
    // Test header packing/unpacking
    auto packed = header.pack();
    assert(packed.size() == 8);
    
    auto unpacked = UACPHeader::unpack(packed);
    assert(unpacked.getVersion() == header.getVersion());
    assert(unpacked.getVerb() == header.getVerb());
    assert(unpacked.getQoS() == header.getQoS());
    assert(unpacked.getCode() == header.getCode());
    assert(unpacked.getMessageId() == header.getMessageId());
    assert(unpacked.getOptionsCount() == header.getOptionsCount());
    
    std::cout << "✓ Header test passed" << std::endl;
}

void testOption() {
    std::cout << "Testing option..." << std::endl;
    
    // Test string option
    UACPOption string_opt(UACPOptionType::TOPIC_PATH, "test/topic");
    assert(string_opt.getType() == UACPOptionType::TOPIC_PATH);
    assert(string_opt.isStringValue());
    assert(string_opt.getStringValue() == "test/topic");
    
    // Test integer option
    UACPOption int_opt(UACPOptionType::PRIORITY, 5u);
    assert(int_opt.getType() == UACPOptionType::PRIORITY);
    assert(int_opt.isIntValue());
    assert(int_opt.getIntValue() == 5);
    
    // Test packing/unpacking
    auto packed = string_opt.pack();
    assert(packed.size() > 0);
    
    UACPOption unpacked_opt(UACPOptionType::TOPIC_PATH, "");
    size_t consumed = UACPOption::unpack(packed, 0, unpacked_opt);
    assert(consumed == packed.size());
    assert(unpacked_opt.getStringValue() == "test/topic");
    
    std::cout << "✓ Option test passed" << std::endl;
}

void testMessage() {
    std::cout << "Testing message..." << std::endl;
    
    // Test message creation
    UACPMessage message(UACPVerb::TELL, std::vector<uint8_t>{'H', 'e', 'l', 'l', 'o'}, 12345, 1, 0);
    assert(message.getHeader().getVerb() == UACPVerb::TELL);
    assert(message.getHeader().getMessageId() == 12345);
    assert(message.getPayload().size() == 5);
    assert(message.getPayloadAsString() == "Hello");
    assert(message.isValid());
    
    // Test adding options
    message.addOption(UACPOptionType::TOPIC_PATH, "test/topic");
    message.addOption(UACPOptionType::PRIORITY, 3u);
    assert(message.getOptions().size() == 2);
    assert(message.getTopicPath() == "test/topic");
    
    // Test packing/unpacking
    auto packed = message.pack();
    assert(packed.size() > 0);
    
    auto unpacked = UACPMessage::unpack(packed);
    assert(unpacked.getHeader().getVerb() == message.getHeader().getVerb());
    assert(unpacked.getHeader().getMessageId() == message.getHeader().getMessageId());
    assert(unpacked.getPayloadAsString() == message.getPayloadAsString());
    assert(unpacked.getTopicPath() == message.getTopicPath());
    
    std::cout << "✓ Message test passed" << std::endl;
}

void testProtocol() {
    std::cout << "Testing protocol..." << std::endl;
    
    UACPProtocol protocol;
    
    // Test message creation
    auto ping_msg = protocol.createPing();
    assert(ping_msg.getHeader().getVerb() == UACPVerb::PING);
    assert(ping_msg.getPayload().empty());
    
    auto tell_msg = protocol.createTell("Hello World", "test/topic");
    assert(tell_msg.getHeader().getVerb() == UACPVerb::TELL);
    assert(tell_msg.getPayloadAsString() == "Hello World");
    assert(tell_msg.getTopicPath() == "test/topic");
    
    auto ask_msg = protocol.createAsk("Request data", "test/request");
    assert(ask_msg.getHeader().getVerb() == UACPVerb::ASK);
    assert(ask_msg.getPayloadAsString() == "Request data");
    assert(ask_msg.getTopicPath() == "test/request");
    
    auto observe_msg = protocol.createObserve("Subscribe", "test/subscribe");
    assert(observe_msg.getHeader().getVerb() == UACPVerb::OBSERVE);
    assert(observe_msg.getPayloadAsString() == "Subscribe");
    assert(observe_msg.getTopicPath() == "test/subscribe");
    
    // Test message validation
    assert(protocol.validateMessage(ping_msg));
    assert(protocol.validateMessage(tell_msg));
    assert(protocol.validateMessage(ask_msg));
    assert(protocol.validateMessage(observe_msg));
    
    std::cout << "✓ Protocol test passed" << std::endl;
}

int main() {
    std::cout << "µACP C++ Library - Basic Tests" << std::endl;
    std::cout << "=============================" << std::endl;
    std::cout << "Library Version: " << getVersion() << std::endl;
    std::cout << std::endl;
    
    try {
        testVersionInfo();
        testEnums();
        testHeader();
        testOption();
        testMessage();
        testProtocol();
        
        std::cout << std::endl;
        std::cout << "All tests passed successfully!" << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Test failed: " << e.what() << std::endl;
        return 1;
    }
}
