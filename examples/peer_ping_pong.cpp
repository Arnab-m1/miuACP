/**
 * @file peer_ping_pong.cpp
 * @brief Simple Peer-to-Peer Ping Pong Example
 * 
 * Demonstrates two agents communicating directly with each other.
 * Run two instances in separate terminals.
 * 
 * Usage:
 *   Terminal 1: ./peer_ping_pong receiver
 *   Terminal 2: ./peer_ping_pong sender
 */

#include <iostream>
#include <thread>
#include <chrono>
#include "miuacp/agent.h"

using namespace miuacp;
using namespace std::chrono_literals;

void runReceiver() {
    std::cout << "========================================" << std::endl;
    std::cout << "  Receiver Agent (Listening on 8002)" << std::endl;
    std::cout << "========================================" << std::endl << std::endl;
    
    // Create receiver agent
    UACPAgent receiver("receiver", "Receiver Agent", "0.0.0.0", 8002);
    
    // Add custom message handler
    receiver.addMessageHandler(UACPVerb::PING, 
        [](const UACPMessage& msg, const std::string& sender, int port) {
            std::cout << "📨 Received PING from " << sender << ":" << port << std::endl;
            std::cout << "📤 Sending PONG..." << std::endl << std::endl;
            return msg.createResponse(StatusCode::SUCCESS, "pong");
        });
    
    receiver.addMessageHandler(UACPVerb::TELL,
        [](const UACPMessage& msg, const std::string& sender, int port) {
            std::cout << "📨 Received TELL from " << sender << ":" << port << std::endl;
            std::cout << "   Payload: " << msg.getPayloadAsString() << std::endl << std::endl;
            return msg.createResponse(StatusCode::SUCCESS);
        });
    
    // Start agent
    if (!receiver.start()) {
        std::cerr << "Failed to start receiver agent!" << std::endl;
        return;
    }
    
    std::cout << "✅ Receiver agent started on port " << receiver.getPort() << std::endl;
    std::cout << "🎧 Listening for messages..." << std::endl << std::endl;
    
    // Run for 60 seconds
    for (int i = 0; i < 60; i++) {
        std::this_thread::sleep_for(1s);
        
        // Print statistics every 10 seconds
        if ((i + 1) % 10 == 0) {
            auto stats = receiver.getStatistics();
            std::cout << "📊 Stats: Received " << stats["messages_received"] 
                      << " messages, " << stats["bytes_received"] << " bytes" << std::endl;
        }
    }
    
    receiver.stop();
    std::cout << std::endl << "👋 Receiver agent stopped." << std::endl;
}

void runSender() {
    std::cout << "========================================" << std::endl;
    std::cout << "  Sender Agent (Port 8001)" << std::endl;
    std::cout << "========================================" << std::endl << std::endl;
    
    // Create sender agent
    UACPAgent sender("sender", "Sender Agent", "0.0.0.0", 8001);
    
    // Start agent
    if (!sender.start()) {
        std::cerr << "Failed to start sender agent!" << std::endl;
        return;
    }
    
    std::cout << "✅ Sender agent started on port " << sender.getPort() << std::endl << std::endl;
    
    // Wait a bit for receiver to be ready
    std::cout << "⏳ Waiting for receiver..." << std::endl;
    std::this_thread::sleep_for(2s);
    
    // Send PING to receiver
    std::cout << "📤 Sending PING to 127.0.0.1:8002..." << std::endl;
    bool pong = sender.ping("127.0.0.1", 8002);
    std::cout << (pong ? "✅ PING sent!" : "❌ PING failed!") << std::endl << std::endl;
    
    std::this_thread::sleep_for(500ms);
    
    // Send several TELL messages
    for (int i = 1; i <= 5; i++) {
        std::string message = "Hello from sender #" + std::to_string(i);
        std::cout << "📤 Sending TELL: \"" << message << "\"" << std::endl;
        sender.tell("127.0.0.1", 8002, message);
        std::this_thread::sleep_for(1s);
    }
    
    std::this_thread::sleep_for(1s);
    
    // Print statistics
    auto stats = sender.getStatistics();
    std::cout << std::endl << "📊 Final Stats:" << std::endl;
    std::cout << "   Messages sent: " << stats["messages_sent"] << std::endl;
    std::cout << "   Bytes sent: " << stats["bytes_sent"] << std::endl;
    std::cout << "   Peers discovered: " << stats["peers"] << std::endl;
    
    sender.stop();
    std::cout << std::endl << "👋 Sender agent stopped." << std::endl;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " <sender|receiver>" << std::endl;
        std::cout << std::endl;
        std::cout << "Run in two terminals:" << std::endl;
        std::cout << "  Terminal 1: " << argv[0] << " receiver" << std::endl;
        std::cout << "  Terminal 2: " << argv[0] << " sender" << std::endl;
        return 1;
    }
    
    std::string role = argv[1];
    
    if (role == "receiver") {
        runReceiver();
    } else if (role == "sender") {
        runSender();
    } else {
        std::cerr << "Invalid role. Use 'sender' or 'receiver'" << std::endl;
        return 1;
    }
    
    return 0;
}
