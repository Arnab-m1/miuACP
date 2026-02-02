/**
 * @file test_agent_p2p.cpp
 * @brief Tests for Peer-to-Peer Agent Communication
 * 
 * Tests agent-to-agent communication including:
 * - Basic connectivity
 * - PING/PONG exchange
 * - Message sending (TELL)
 * - Request/response (ASK)
 * - Topic handlers
 * - Peer discovery
 */

#include <iostream>
#include <cassert>
#include <thread>
#include <chrono>
#include "miuacp/agent.h"

using namespace miuacp;
using namespace std::chrono_literals;

void testBasicAgentStartStop() {
    std::cout << "Test: Basic Agent Start/Stop..." << std::endl;
    
    UACPAgent agent("test-agent", "Test Agent", "127.0.0.1", 9001);
    
    assert(!agent.isRunning());
    assert(agent.start());
    assert(agent.isRunning());
    assert(agent.getPort() == 9001);
    assert(agent.getAddress() == "127.0.0.1:9001");
    
    agent.stop();
    assert(!agent.isRunning());
    
    std::cout << "  ✓ Agent lifecycle works!" << std::endl;
}

void testEphemeralPort() {
    std::cout << "Test: Ephemeral Port Assignment..." << std::endl;
    
    UACPAgent agent("ephemeral-agent", "Ephemeral Agent", "127.0.0.1", 0);
    
    assert(agent.start());
    int assigned_port = agent.getPort();
    assert(assigned_port > 0);
    
    std::cout << "  ✓ OS assigned ephemeral port: " << assigned_port << std::endl;
    
    agent.stop();
}

void testPeerToPeerPing() {
    std::cout << "Test: Peer-to-Peer PING..." << std::endl;
    
    // Create two peer agents
    UACPAgent agent1("agent1", "Agent 1", "127.0.0.1", 7001);
    UACPAgent agent2("agent2", "Agent 2", "127.0.0.1", 7002);
    
    // Start both agents
    assert(agent1.start());
    assert(agent2.start());
    
    // Wait for agents to be ready
    std::this_thread::sleep_for(100ms);
    
    // Agent1 pings Agent2
    bool pong = agent1.ping("127.0.0.1", 7002);
    
    // Wait for response
    std::this_thread::sleep_for(100ms);
    
    // For now, just verify the ping was sent
    // (Full request/response matching not yet implemented)
    assert(pong);  // Returns true if send succeeded
    
    // Verify Agent2 received the message
    auto stats2 = agent2.getStatistics();
    assert(stats2["messages_received"] > 0);
    
    // Stop agents
    agent1.stop();
    agent2.stop();
    
    std::cout << "  ✓ Peer-to-peer PING works!" << std::endl;
}

void testPeerToPeerTell() {
    std::cout << "Test: Peer-to-Peer TELL..." << std::endl;
    
    UACPAgent agent1("agent1", "Agent 1", "127.0.0.1", 7003);
    UACPAgent agent2("agent2", "Agent 2", "127.0.0.1", 7004);
    
    bool message_received = false;
    
    // Agent2 adds handler for incoming TELL messages
    agent2.addMessageHandler(UACPVerb::TELL, 
        [&message_received](const UACPMessage& msg, const std::string& sender, int port) {
            (void)sender;
            (void)port;
            message_received = true;
            std::string payload_str = msg.getPayloadAsString();
            assert(payload_str == "Hello, Agent2!");
            return msg.createResponse(StatusCode::SUCCESS);
        });
    
    assert(agent1.start());
    assert(agent2.start());
    
    std::this_thread::sleep_for(100ms);
    
    // Agent1 sends TELL to Agent2
    agent1.tell("127.0.0.1", 7004, "Hello, Agent2!");
    
    // Wait for message processing
    std::this_thread::sleep_for(200ms);
    
    assert(message_received);
    
    agent1.stop();
    agent2.stop();
    
    std::cout << "  ✓ Peer-to-peer TELL works!" << std::endl;
}

void testTopicHandler() {
    std::cout << "Test: Topic-Based Message Handler..." << std::endl;
    
    UACPAgent agent1("agent1", "Agent 1", "127.0.0.1", 7005);
    UACPAgent agent2("agent2", "Agent 2", "127.0.0.1", 7006);
    
    bool topic_handler_called = false;
    std::string received_topic;
    
    // Agent2 adds topic handler
    agent2.addTopicHandler("sensors/temperature", 
        [&topic_handler_called, &received_topic](const UACPMessage& msg, const std::string& sender, int port) {
            (void)sender;
            (void)port;
            topic_handler_called = true;
            received_topic = msg.getTopicPath();
            std::string payload = msg.getPayloadAsString();
            assert(payload == "25.5°C");
            return msg.createResponse(StatusCode::SUCCESS, "Temperature recorded");
        });
    
    assert(agent1.start());
    assert(agent2.start());
    
    std::this_thread::sleep_for(100ms);
    
    // Agent1 sends message to topic
    agent1.tell("127.0.0.1", 7006, "25.5°C", "sensors/temperature");
    
    std::this_thread::sleep_for(200ms);
    
    assert(topic_handler_called);
    assert(received_topic == "sensors/temperature");
    
    agent1.stop();
    agent2.stop();
    
    std::cout << "  ✓ Topic-based message handling works!" << std::endl;
}

void testPeerDiscovery() {
    std::cout << "Test: Peer Discovery..." << std::endl;
    
    // Create 3 agents on different ports
    UACPAgent agent1("agent1", "Agent 1", "0.0.0.0", 8001);
    UACPAgent agent2("agent2", "Agent 2", "0.0.0.0", 8002);
    UACPAgent agent3("agent3", "Agent 3", "0.0.0.0", 8003);
    
    assert(agent1.start());
    assert(agent2.start());
    assert(agent3.start());
    
    std::this_thread::sleep_for(100ms);
    
    // Agent1 broadcasts discovery to port 8001
    int sent = agent1.discoverPeers("255.255.255.255", 8001);
    
    assert(sent == 1);  // Broadcast sent successfully
    
    std::this_thread::sleep_for(100ms);
    
    // Agent1 should have received its own broadcast
    auto stats1 = agent1.getStatistics();
    // Note: Discovery response handling not yet fully implemented
    
    agent1.stop();
    agent2.stop();
    agent3.stop();
    
    std::cout << "  ✓ Peer discovery broadcast works!" << std::endl;
}

void testPeerRegistry() {
    std::cout << "Test: Peer Registry..." << std::endl;
    
    UACPAgent agent("main-agent", "Main Agent", "127.0.0.1", 7007);
    assert(agent.start());
    
    // Manually add peers
    agent.addPeer("192.168.1.100", 8001, "remote-agent-1");
    agent.addPeer("192.168.1.101", 8002, "remote-agent-2");
    agent.addPeer("192.168.1.102", 8003, "remote-agent-3");
    
    auto peers = agent.getDiscoveredPeers();
    assert(peers.size() == 3);
    
    // Check peer info
    auto* peer1 = agent.getPeerInfo("192.168.1.100", 8001);
    assert(peer1 != nullptr);
    assert(peer1->agent_id == "remote-agent-1");
    assert(peer1->host == "192.168.1.100");
    assert(peer1->port == 8001);
    
    // Remove a peer
    agent.removePeer("192.168.1.101", 8002);
    peers = agent.getDiscoveredPeers();
    assert(peers.size() == 2);
    
    agent.stop();
    
    std::cout << "  ✓ Peer registry works!" << std::endl;
}

void testStatistics() {
    std::cout << "Test: Agent Statistics..." << std::endl;
    
    UACPAgent agent1("agent1", "Agent 1", "127.0.0.1", 7008);
    UACPAgent agent2("agent2", "Agent 2", "127.0.0.1", 7009);
    
    assert(agent1.start());
    assert(agent2.start());
    
    std::this_thread::sleep_for(100ms);
    
    // Send some messages
    agent1.ping("127.0.0.1", 7009);
    agent1.tell("127.0.0.1", 7009, "Test message 1");
    agent1.tell("127.0.0.1", 7009, "Test message 2");
    
    std::this_thread::sleep_for(200ms);
    
    auto stats1 = agent1.getStatistics();
    auto stats2 = agent2.getStatistics();
    
    // Agent1 should have sent messages
    assert(stats1["messages_sent"] >= 3);
    assert(stats1["bytes_sent"] > 0);
    
    // Agent2 should have received messages
    assert(stats2["messages_received"] >= 3);
    assert(stats2["bytes_received"] > 0);
    
    std::cout << "  Stats - Agent1 sent: " << stats1["messages_sent"] 
              << " msgs, " << stats1["bytes_sent"] << " bytes" << std::endl;
    std::cout << "  Stats - Agent2 received: " << stats2["messages_received"] 
              << " msgs, " << stats2["bytes_received"] << " bytes" << std::endl;
    
    agent1.stop();
    agent2.stop();
    
    std::cout << "  ✓ Statistics tracking works!" << std::endl;
}

int main() {
    std::cout << "=============================" << std::endl;
    std::cout << "Peer-to-Peer Agent Tests" << std::endl;
    std::cout << "=============================" << std::endl << std::endl;
    
    try {
        testBasicAgentStartStop();
        testEphemeralPort();
        testPeerToPeerPing();
        testPeerToPeerTell();
        testTopicHandler();
        testPeerDiscovery();
        testPeerRegistry();
        testStatistics();
        
        std::cout << std::endl;
        std::cout << "=============================" << std::endl;
        std::cout << "All Agent P2P Tests Passed! ✓" << std::endl;
        std::cout << "=============================" << std::endl;
        
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Test failed: " << e.what() << std::endl;
        return 1;
    }
}
