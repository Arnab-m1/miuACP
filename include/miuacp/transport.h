/**
 * @file transport.h
 * @brief µACP Transport Layer Abstraction
 * 
 * Abstract interface for peer-to-peer transport implementations.
 * Supports both connectionless (UDP) and connection-oriented (TCP) protocols.
 * 
 * @author Arnab
 * @version 1.0.0
 * @license MIT
 */

#pragma once

#include <vector>
#include <string>
#include <cstdint>

namespace miuacp {

/**
 * @brief Abstract transport interface for peer-to-peer communication
 * 
 * This interface provides a common abstraction for different transport protocols.
 * All agents use transports to communicate directly with other peer agents.
 * 
 * Key design principles:
 * - Symmetric: Same transport can send and receive
 * - Peer-to-peer: No client/server distinction
 * - Protocol-agnostic: Works with UDP, TCP, or custom transports
 */
class UACPTransport {
public:
    virtual ~UACPTransport() = default;
    
    /**
     * @brief Send data to a peer agent
     * @param data Binary data to send
     * @param peer_host Hostname or IP address of peer
     * @param peer_port Port number of peer
     * @return true if send succeeded, false otherwise
     * 
     * For UDP: Sends datagram to peer
     * For TCP: Connects to peer (if needed) and sends data
     */
    virtual bool sendToPeer(const std::vector<uint8_t>& data, 
                           const std::string& peer_host, 
                           int peer_port) = 0;
    
    /**
     * @brief Receive data from any peer agent
     * @param timeout_ms Timeout in milliseconds (0 = non-blocking, -1 = blocking)
     * @param sender_host Output: hostname/IP of sender
     * @param sender_port Output: port number of sender
     * @return Received data, empty if timeout or error
     * 
     * For UDP: Receives datagram from any peer
     * For TCP: Receives from connected peer or accepts new connection
     */
    virtual std::vector<uint8_t> receiveFromPeer(int timeout_ms, 
                                                 std::string& sender_host, 
                                                 int& sender_port) = 0;
    
    /**
     * @brief Bind transport to local address and port
     * @param host Local address to bind ("0.0.0.0" for all interfaces)
     * @param port Local port (0 = OS assigns ephemeral port)
     * @return true if bind succeeded, false otherwise
     * 
     * All peer agents must bind to receive messages from other peers.
     */
    virtual bool bind(const std::string& host, int port) = 0;
    
    /**
     * @brief Close the transport
     * 
     * Closes sockets, releases resources, stops accepting connections.
     */
    virtual void close() = 0;
    
    /**
     * @brief Check if transport is bound and ready
     * @return true if bound and operational, false otherwise
     */
    virtual bool isBound() const = 0;
    
    /**
     * @brief Get the local port this transport is bound to
     * @return Port number, or 0 if not bound
     */
    virtual int getLocalPort() const = 0;
    
    // ========== Discovery Features (Optional) ==========
    
    /**
     * @brief Enable broadcast mode (for discovery)
     * @return true if broadcast enabled, false if not supported
     * 
     * Used for agent discovery on local network.
     * Only applicable to UDP.
     */
    virtual bool enableBroadcast() { return false; }
    
    /**
     * @brief Send broadcast message (for discovery)
     * @param data Binary data to broadcast
     * @param port Destination port for broadcast
     * @return true if broadcast sent, false otherwise
     * 
     * Only applicable to UDP.
     */
    virtual bool sendBroadcast(const std::vector<uint8_t>& data, int port) { 
        (void)data; (void)port; 
        return false; 
    }
    
    /**
     * @brief Enable multicast mode (for pub/sub)
     * @param group Multicast group address (e.g., "239.255.0.1")
     * @return true if multicast enabled, false if not supported
     * 
     * Used for topic-based publish/subscribe.
     * Only applicable to UDP.
     */
    virtual bool enableMulticast(const std::string& group) { 
        (void)group; 
        return false; 
    }
    
    // ========== Connection Management (Optional) ==========
    
    /**
     * @brief Explicitly connect to a peer (for connection-oriented protocols)
     * @param host Peer hostname/IP
     * @param port Peer port
     * @return true if connected, false otherwise
     * 
     * For UDP: No-op (connectionless)
     * For TCP: Establishes connection to peer
     */
    virtual bool connect(const std::string& host, int port) { 
        (void)host; (void)port; 
        return true; 
    }
    
    /**
     * @brief Disconnect from peer (for connection-oriented protocols)
     * 
     * For UDP: No-op (connectionless)
     * For TCP: Closes connection
     */
    virtual void disconnect() {}
    
    /**
     * @brief Check if connected to a peer
     * @return true if connected, false otherwise
     * 
     * For UDP: Always returns true (connectionless)
     * For TCP: Returns true if connection established
     */
    virtual bool isConnected() const { return true; }
};

} // namespace miuacp
