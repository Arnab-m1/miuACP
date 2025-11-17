/**
 * @file basic_usage.cpp
 * @brief Basic µACP Library Usage Example
 * 
 * This example demonstrates the basic usage of the µACP C++ library,
 * including message creation, packing, and unpacking.
 */

#include <iostream>
#include <vector>
#include <string>
#include "miuacp/miuacp.h"

using namespace miuacp;

void printMessageInfo(const UACPMessage& message) {
    std::cout << "Message Info:" << std::endl;
    std::cout << "  Verb: " << static_cast<int>(message.getHeader().getVerb()) << std::endl;
    std::cout << "  Message ID: " << message.getHeader().getMessageId() << std::endl;
    std::cout << "  QoS: " << static_cast<int>(message.getHeader().getQoS()) << std::endl;
    std::cout << "  Code: " << static_cast<int>(message.getHeader().getCode()) << std::endl;
    std::cout << "  Options Count: " << static_cast<int>(message.getHeader().getOptionsCount()) << std::endl;
    std::cout << "  Payload Size: " << message.getPayload().size() << " bytes" << std::endl;
    std::cout << "  Total Size: " << message.getPackedSize() << " bytes" << std::endl;
    std::cout << std::endl;
}

int main() {
    std::cout << "µACP C++ Library - Basic Usage Example" << std::endl;
    std::cout << "=====================================" << std::endl;
    std::cout << "Library Version: " << getVersion() << std::endl;
    std::cout << "Author: " << getAuthor() << std::endl;
    std::cout << std::endl;
    
    // Create protocol instance
    UACPProtocol protocol;
    
    // Example 1: Create a simple PING message
    std::cout << "Example 1: PING Message" << std::endl;
    std::cout << "----------------------" << std::endl;
    UACPMessage ping_msg = protocol.createPing();
    printMessageInfo(ping_msg);
    
    // Example 2: Create a TELL message with string payload
    std::cout << "Example 2: TELL Message with String Payload" << std::endl;
    std::cout << "-------------------------------------------" << std::endl;
    std::string tell_payload = "Hello, µACP World!";
    UACPMessage tell_msg = protocol.createTell(tell_payload, "greetings/hello");
    printMessageInfo(tell_msg);
    std::cout << "  Payload: " << tell_msg.getPayloadAsString() << std::endl;
    std::cout << "  Topic: " << tell_msg.getTopicPath() << std::endl;
    std::cout << std::endl;
    
    // Example 3: Create an ASK message with binary payload
    std::cout << "Example 3: ASK Message with Binary Payload" << std::endl;
    std::cout << "------------------------------------------" << std::endl;
    std::vector<uint8_t> ask_payload = {0x48, 0x65, 0x6C, 0x6C, 0x6F}; // "Hello"
    UACPMessage ask_msg = protocol.createAsk(ask_payload, "requests/data", 0, 1);
    printMessageInfo(ask_msg);
    std::cout << "  Payload (hex): ";
    for (uint8_t byte : ask_msg.getPayload()) {
        printf("%02X ", byte);
    }
    std::cout << std::endl;
    std::cout << "  Topic: " << ask_msg.getTopicPath() << std::endl;
    std::cout << std::endl;
    
    // Example 4: Create an OBSERVE message
    std::cout << "Example 4: OBSERVE Message" << std::endl;
    std::cout << "-------------------------" << std::endl;
    std::string observe_payload = "Subscribe to temperature updates";
    UACPMessage observe_msg = protocol.createObserve(observe_payload, "sensors/temperature");
    printMessageInfo(observe_msg);
    std::cout << "  Payload: " << observe_msg.getPayloadAsString() << std::endl;
    std::cout << "  Topic: " << observe_msg.getTopicPath() << std::endl;
    std::cout << std::endl;
    
    // Example 5: Add custom options
    std::cout << "Example 5: Message with Custom Options" << std::endl;
    std::cout << "--------------------------------------" << std::endl;
    UACPMessage custom_msg = protocol.createTell("Custom message", "test/custom");
    custom_msg.addOption(UACPOptionType::PRIORITY, 5u);
    custom_msg.addOption(UACPOptionType::MAX_AGE, 3600u);
    custom_msg.setContentType(UACPContentType::JSON);
    printMessageInfo(custom_msg);
    
    // Print options
    std::cout << "  Options:" << std::endl;
    for (const auto& option : custom_msg.getOptions()) {
        std::cout << "    Type: " << static_cast<int>(option.getType());
        if (option.isStringValue()) {
            std::cout << ", Value: " << option.getStringValue();
        } else if (option.isIntValue()) {
            std::cout << ", Value: " << option.getIntValue();
        }
        std::cout << std::endl;
    }
    std::cout << "  Content Type: " << static_cast<int>(custom_msg.getContentType()) << std::endl;
    std::cout << std::endl;
    
    // Example 6: Pack and unpack messages
    std::cout << "Example 6: Pack and Unpack Messages" << std::endl;
    std::cout << "-----------------------------------" << std::endl;
    
    // Pack the custom message
    std::vector<uint8_t> packed_data = custom_msg.pack();
    std::cout << "  Packed size: " << packed_data.size() << " bytes" << std::endl;
    
    // Unpack the message
    UACPMessage unpacked_msg = UACPMessage::unpack(packed_data);
    std::cout << "  Unpacked successfully!" << std::endl;
    std::cout << "  Original payload: " << custom_msg.getPayloadAsString() << std::endl;
    std::cout << "  Unpacked payload: " << unpacked_msg.getPayloadAsString() << std::endl;
    std::cout << "  Original topic: " << custom_msg.getTopicPath() << std::endl;
    std::cout << "  Unpacked topic: " << unpacked_msg.getTopicPath() << std::endl;
    std::cout << std::endl;
    
    // Example 7: Create response message
    std::cout << "Example 7: Create Response Message" << std::endl;
    std::cout << "----------------------------------" << std::endl;
    UACPMessage response = ask_msg.createResponse(StatusCode::SUCCESS, "Response data");
    printMessageInfo(response);
    std::cout << "  Is Request: " << (ask_msg.isRequest() ? "Yes" : "No") << std::endl;
    std::cout << "  Is Response: " << (response.isResponse() ? "Yes" : "No") << std::endl;
    std::cout << std::endl;
    
    // Example 8: Message validation
    std::cout << "Example 8: Message Validation" << std::endl;
    std::cout << "-----------------------------" << std::endl;
    std::cout << "  PING message valid: " << (ping_msg.isValid() ? "Yes" : "No") << std::endl;
    std::cout << "  TELL message valid: " << (tell_msg.isValid() ? "Yes" : "No") << std::endl;
    std::cout << "  ASK message valid: " << (ask_msg.isValid() ? "Yes" : "No") << std::endl;
    std::cout << "  OBSERVE message valid: " << (observe_msg.isValid() ? "Yes" : "No") << std::endl;
    std::cout << "  Custom message valid: " << (custom_msg.isValid() ? "Yes" : "No") << std::endl;
    std::cout << "  Response message valid: " << (response.isValid() ? "Yes" : "No") << std::endl;
    std::cout << std::endl;
    
    std::cout << "Basic usage example completed successfully!" << std::endl;
    
    return 0;
}
