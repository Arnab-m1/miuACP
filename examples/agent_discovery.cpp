/**
 * @file agent_discovery.cpp
 * @brief Agent Discovery Demo
 * 
 * Demonstrates multiple agents discovering each other via UDP broadcast.
 * Run multiple instances in separate terminals or on different machines.
 * 
 * Usage:
 *   Terminal 1: ./agent_discovery agent1 8001
 *   Terminal 2: ./agent_discovery agent2 8002
 *   Terminal 3: ./agent_discovery agent3 8003
 */

#include <iostream>
#include <thread>
#include <chrono>
#include <csignal>
#include <atomic>
#include "miuacp/agent.h"

using namespace miuacp;
using namespace std::chrono_literals;

std::atomic<bool> running(true);

void signalHandler(int signum) {
    (void)signum;
    std::cout << "\n\n⏹️  Stopping agent..." << std::endl;
    running = false;
}

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cout << "Usage: " << argv[0] << " <agent-name> <port>" << std::endl;
        std::cout << "\nExample:" << std::endl;
        std::cout << "  Terminal 1: " << argv[0] << " agent1 8001" << std::endl;
        std::cout << "  Terminal 2: " << argv[0] << " agent2 8002" << std::endl;
        std::cout << "  Terminal 3: " << argv[0] << " agent3 8003" << std::endl;
        return 1;
    }
    
    std::string agent_name = argv[1];
    int port = std::atoi(argv[2]);
    
    // Setup signal handler
    signal(SIGINT, signalHandler);
    
    std::cout << "========================================" << std::endl;
    std::cout << "  Agent Discovery Demo" << std::endl;
    std::cout << "  Agent: " << agent_name << " (Port " << port << ")" << std::endl;
    std::cout << "========================================" << std::endl << std::endl;
    
    // Create agent
    UACPAgent agent(agent_name, agent_name + " Agent", "0.0.0.0", port);
    
    // Add PING handler to respond to discovery
    agent.addMessageHandler(UACPVerb::PING, 
        [&agent_name](const UACPMessage& msg, const std::string& sender, int sender_port) {
            std::cout << "📨 PING from " << sender << ":" << sender_port << std::endl;
            std::cout << "📤 Sending PONG..." << std::endl;
            return msg.createResponse(StatusCode::SUCCESS, agent_name);
        });
    
    // Start agent
    if (!agent.start()) {
        std::cerr << "❌ Failed to start agent!" << std::endl;
        return 1;
    }
    
    std::cout << "✅ Agent started on port " << agent.getPort() << std::endl;
    std::cout << "🔍 Starting peer discovery..." << std::endl << std::endl;
    
    // Perform discovery every 5 seconds
    int discovery_count = 0;
    auto last_discovery = std::chrono::steady_clock::now();
    auto last_stats = std::chrono::steady_clock::now();
    
    while (running) {
        auto now = std::chrono::steady_clock::now();
        
        // Discover peers every 5 seconds
        if (std::chrono::duration_cast<std::chrono::seconds>(now - last_discovery).count() >= 5) {
            std::cout << "\n🔍 Broadcasting discovery message #" << ++discovery_count << "..." << std::endl;
            
            // Try different broadcast ports to discover agents
            for (int p = 8001; p <= 8010; p++) {
                if (p != port) {  // Don't send to self
                    agent.ping("127.0.0.1", p);
                }
            }
            
            // Also broadcast to LAN
            agent.discoverPeers("255.255.255.255", port);
            
            last_discovery = now;
            
            // Show discovered peers
            std::this_thread::sleep_for(500ms);
            auto peers = agent.getDiscoveredPeers();
            if (!peers.empty()) {
                std::cout << "👥 Discovered " << peers.size() << " peer(s):" << std::endl;
                for (const auto& peer : peers) {
                    std::cout << "   - " << peer << std::endl;
                }
            } else {
                std::cout << "   No peers discovered yet..." << std::endl;
            }
        }
        
        // Print statistics every 15 seconds
        if (std::chrono::duration_cast<std::chrono::seconds>(now - last_stats).count() >= 15) {
            auto stats = agent.getStatistics();
            std::cout << "\n📊 Statistics:" << std::endl;
            std::cout << "   Messages sent: " << stats["messages_sent"] << std::endl;
            std::cout << "   Messages received: " << stats["messages_received"] << std::endl;
            std::cout << "   Peers: " << stats["peers"] << std::endl;
            last_stats = now;
        }
        
        std::this_thread::sleep_for(100ms);
    }
    
    agent.stop();
    std::cout << "\n👋 Agent stopped. Goodbye!" << std::endl;
    
    return 0;
}
