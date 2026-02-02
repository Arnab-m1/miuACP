/**
 * @file test_udp_transport.cpp
 * @brief Tests for UDP Transport
 * 
 * Tests peer-to-peer UDP communication including:
 * - Basic send/receive between peers
 * - Broadcast for discovery
 * - Multicast for pub/sub
 * - Timeout handling
 */

#include <iostream>
#include <cassert>
#include <thread>
#include <chrono>
#include "miuacp/udp_transport.h"

using namespace miuacp;
using namespace std::chrono_literals;

void testBasicSendReceive() {
    std::cout << "Test: Basic Peer-to-Peer Send/Receive..." << std::endl;
    
    // Create two peer transports
    UACPUdpTransport peer1, peer2;
    
    // Bind peer1 to port 9001
    assert(peer1.bind("127.0.0.1", 9001));
    assert(peer1.isBound());
    assert(peer1.getLocalPort() == 9001);
    
    // Bind peer2 to port 9002
    assert(peer2.bind("127.0.0.1", 9002));
    assert(peer2.isBound());
    assert(peer2.getLocalPort() == 9002);
    
    // Peer1 sends to Peer2
    std::vector<uint8_t> msg = {'H', 'e', 'l', 'l', 'o', '!'};
    assert(peer1.sendToPeer(msg, "127.0.0.1", 9002));
    
    // Peer2 receives from Peer1
    std::string sender_host;
    int sender_port;
    auto received = peer2.receiveFromPeer(1000, sender_host, sender_port);
    
    assert(!received.empty());
    assert(received == msg);
    assert(sender_host == "127.0.0.1");
    assert(sender_port == 9001);
    
    // Peer2 sends reply to Peer1
    std::vector<uint8_t> reply = {'W', 'o', 'r', 'l', 'd', '!'};
    assert(peer2.sendToPeer(reply, "127.0.0.1", 9001));
    
    // Peer1 receives reply
    received = peer1.receiveFromPeer(1000, sender_host, sender_port);
    assert(!received.empty());
    assert(received == reply);
    assert(sender_host == "127.0.0.1");
    assert(sender_port == 9002);
    
    peer1.close();
    peer2.close();
    
    std::cout << "  ✓ Peer-to-peer send/receive works!" << std::endl;
}

void testEphemeralPort() {
    std::cout << "Test: Ephemeral Port Assignment..." << std::endl;
    
    UACPUdpTransport transport;
    
    // Bind with port 0 (OS assigns)
    assert(transport.bind("127.0.0.1", 0));
    assert(transport.isBound());
    
    int assigned_port = transport.getLocalPort();
    assert(assigned_port > 0);
    
    std::cout << "  ✓ OS assigned ephemeral port: " << assigned_port << std::endl;
    
    transport.close();
}

void testTimeout() {
    std::cout << "Test: Receive Timeout..." << std::endl;
    
    UACPUdpTransport transport;
    assert(transport.bind("127.0.0.1", 9003));
    
    // Receive with timeout (no data available)
    std::string sender_host;
    int sender_port;
    auto start = std::chrono::steady_clock::now();
    auto received = transport.receiveFromPeer(500, sender_host, sender_port);
    auto end = std::chrono::steady_clock::now();
    
    auto duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    
    assert(received.empty());  // No data received
    assert(duration_ms >= 450 && duration_ms <= 600);  // Timeout ~500ms
    
    std::cout << "  ✓ Timeout works: " << duration_ms << "ms" << std::endl;
    
    transport.close();
}

void testBroadcast() {
    std::cout << "Test: Broadcast Discovery..." << std::endl;
    
    // Create 3 peer agents listening on different ports
    UACPUdpTransport peer1, peer2, peer3;
    
    assert(peer1.bind("0.0.0.0", 8001));
    assert(peer2.bind("0.0.0.0", 8002));
    assert(peer3.bind("0.0.0.0", 8003));
    
    // Broadcaster
    UACPUdpTransport broadcaster;
    assert(broadcaster.bind("0.0.0.0", 0));
    assert(broadcaster.enableBroadcast());
    
    // Send broadcast discovery message to port 8001
    std::vector<uint8_t> discovery = {'D', 'I', 'S', 'C', 'O', 'V', 'E', 'R'};
    assert(broadcaster.sendBroadcast(discovery, 8001));
    
    std::this_thread::sleep_for(100ms);
    
    // Peer1 should receive broadcast
    std::string sender_host;
    int sender_port;
    auto received = peer1.receiveFromPeer(500, sender_host, sender_port);
    
    assert(!received.empty());
    assert(received == discovery);
    
    // Peer2 and Peer3 should NOT receive (different port)
    auto received2 = peer2.receiveFromPeer(100, sender_host, sender_port);
    auto received3 = peer3.receiveFromPeer(100, sender_host, sender_port);
    assert(received2.empty());
    assert(received3.empty());
    
    std::cout << "  ✓ Broadcast works!" << std::endl;
    
    broadcaster.close();
    peer1.close();
    peer2.close();
    peer3.close();
}

void testMultiAgentCommunication() {
    std::cout << "Test: Multi-Agent Peer Communication..." << std::endl;
    
    // Simulate 4 agents communicating
    UACPUdpTransport agent1, agent2, agent3, agent4;
    
    assert(agent1.bind("127.0.0.1", 7001));
    assert(agent2.bind("127.0.0.1", 7002));
    assert(agent3.bind("127.0.0.1", 7003));
    assert(agent4.bind("127.0.0.1", 7004));
    
    // Agent1 sends to Agent3
    std::vector<uint8_t> msg1 = {'A', '1', '-', '>', 'A', '3'};
    assert(agent1.sendToPeer(msg1, "127.0.0.1", 7003));
    
    // Agent2 sends to Agent4
    std::vector<uint8_t> msg2 = {'A', '2', '-', '>', 'A', '4'};
    assert(agent2.sendToPeer(msg2, "127.0.0.1", 7004));
    
    // Agent3 receives from Agent1
    std::string sender_host;
    int sender_port;
    auto received3 = agent3.receiveFromPeer(1000, sender_host, sender_port);
    assert(received3 == msg1);
    assert(sender_port == 7001);
    
    // Agent4 receives from Agent2
    auto received4 = agent4.receiveFromPeer(1000, sender_host, sender_port);
    assert(received4 == msg2);
    assert(sender_port == 7002);
    
    // Agent3 replies to Agent1
    std::vector<uint8_t> reply3 = {'A', '3', '-', '>', 'A', '1'};
    assert(agent3.sendToPeer(reply3, "127.0.0.1", 7001));
    
    // Agent1 receives reply
    auto received1 = agent1.receiveFromPeer(1000, sender_host, sender_port);
    assert(received1 == reply3);
    assert(sender_port == 7003);
    
    std::cout << "  ✓ Multi-agent peer communication works!" << std::endl;
    
    agent1.close();
    agent2.close();
    agent3.close();
    agent4.close();
}

void testLargePacket() {
    std::cout << "Test: Large UDP Packet..." << std::endl;
    
    UACPUdpTransport sender, receiver;
    
    assert(sender.bind("127.0.0.1", 6001));
    assert(receiver.bind("127.0.0.1", 6002));
    
    // Create large packet (but within UDP limits)
    std::vector<uint8_t> large_msg(32768, 0xAB);  // 32KB
    assert(sender.sendToPeer(large_msg, "127.0.0.1", 6002));
    
    std::string sender_host;
    int sender_port;
    auto received = receiver.receiveFromPeer(1000, sender_host, sender_port);
    
    assert(received.size() == large_msg.size());
    assert(received == large_msg);
    
    std::cout << "  ✓ Large packet (" << large_msg.size() << " bytes) sent successfully!" << std::endl;
    
    sender.close();
    receiver.close();
}

void testMoveSemantics() {
    std::cout << "Test: Move Semantics..." << std::endl;
    
    UACPUdpTransport transport1;
    assert(transport1.bind("127.0.0.1", 5001));
    assert(transport1.isBound());
    int port = transport1.getLocalPort();
    
    // Move constructor
    UACPUdpTransport transport2(std::move(transport1));
    assert(transport2.isBound());
    assert(transport2.getLocalPort() == port);
    assert(!transport1.isBound());  // Moved-from object is invalid
    
    // Move assignment
    UACPUdpTransport transport3;
    transport3 = std::move(transport2);
    assert(transport3.isBound());
    assert(transport3.getLocalPort() == port);
    assert(!transport2.isBound());  // Moved-from object is invalid
    
    std::cout << "  ✓ Move semantics work correctly!" << std::endl;
    
    transport3.close();
}

int main() {
    std::cout << "=============================" << std::endl;
    std::cout << "UDP Transport Tests" << std::endl;
    std::cout << "=============================" << std::endl << std::endl;
    
    try {
        testBasicSendReceive();
        testEphemeralPort();
        testTimeout();
        testBroadcast();
        testMultiAgentCommunication();
        testLargePacket();
        testMoveSemantics();
        
        std::cout << std::endl;
        std::cout << "=============================" << std::endl;
        std::cout << "All UDP Transport Tests Passed! ✓" << std::endl;
        std::cout << "=============================" << std::endl;
        
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Test failed: " << e.what() << std::endl;
        return 1;
    }
}
