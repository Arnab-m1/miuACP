/**
 * @file udp_transport.h
 * @brief µACP UDP Transport Implementation
 * 
 * UDP transport for peer-to-peer agent communication.
 * Connectionless, supports broadcast and multicast for discovery.
 * 
 * @author Arnab
 * @version 1.0.0
 * @license MIT
 */

#pragma once

#include "transport.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string>
#include <vector>
#include <cstdint>

namespace miuacp {

/**
 * @brief UDP transport for connectionless peer-to-peer communication
 * 
 * Features:
 * - Connectionless: No persistent connections between peers
 * - Single socket: Same socket for send and receive
 * - Broadcast: Discover all agents on LAN
 * - Multicast: Topic-based pub/sub
 * - Lightweight: Minimal overhead for edge devices
 */
class UACPUdpTransport : public UACPTransport {
public:
    /**
     * @brief Constructor
     */
    UACPUdpTransport();
    
    /**
     * @brief Destructor - closes socket if open
     */
    ~UACPUdpTransport() override;
    
    // Disable copy
    UACPUdpTransport(const UACPUdpTransport&) = delete;
    UACPUdpTransport& operator=(const UACPUdpTransport&) = delete;
    
    // Enable move
    UACPUdpTransport(UACPUdpTransport&& other) noexcept;
    UACPUdpTransport& operator=(UACPUdpTransport&& other) noexcept;
    
    // ========== Core Transport Interface ==========
    
    /**
     * @brief Send UDP datagram to peer
     * @param data Binary data to send
     * @param peer_host Hostname or IP address of peer
     * @param peer_port Port number of peer
     * @return true if send succeeded, false otherwise
     */
    bool sendToPeer(const std::vector<uint8_t>& data, 
                   const std::string& peer_host, 
                   int peer_port) override;
    
    /**
     * @brief Receive UDP datagram from any peer
     * @param timeout_ms Timeout in milliseconds (0 = non-blocking, -1 = blocking)
     * @param sender_host Output: IP address of sender
     * @param sender_port Output: port number of sender
     * @return Received data, empty if timeout or error
     */
    std::vector<uint8_t> receiveFromPeer(int timeout_ms, 
                                        std::string& sender_host, 
                                        int& sender_port) override;
    
    /**
     * @brief Bind UDP socket to local address and port
     * @param host Local address ("0.0.0.0" for all interfaces, "127.0.0.1" for loopback)
     * @param port Local port (0 = OS assigns ephemeral port)
     * @return true if bind succeeded, false otherwise
     */
    bool bind(const std::string& host, int port) override;
    
    /**
     * @brief Close UDP socket
     */
    void close() override;
    
    /**
     * @brief Check if socket is bound
     * @return true if bound and operational
     */
    bool isBound() const override;
    
    /**
     * @brief Get local port
     * @return Port number, or 0 if not bound
     */
    int getLocalPort() const override;
    
    // ========== Discovery Features ==========
    
    /**
     * @brief Enable broadcast mode for discovery
     * @return true if broadcast enabled successfully
     */
    bool enableBroadcast() override;
    
    /**
     * @brief Send broadcast message to all agents on LAN
     * @param data Binary data to broadcast
     * @param port Destination port for broadcast
     * @return true if broadcast sent successfully
     */
    bool sendBroadcast(const std::vector<uint8_t>& data, int port) override;
    
    /**
     * @brief Enable multicast mode for pub/sub
     * @param group Multicast group address (e.g., "239.255.0.1")
     * @return true if multicast enabled successfully
     */
    bool enableMulticast(const std::string& group) override;
    
    // ========== Configuration ==========
    
    /**
     * @brief Set receive buffer size
     * @param size Buffer size in bytes
     * @return true if set successfully
     */
    bool setReceiveBufferSize(int size);
    
    /**
     * @brief Set send buffer size
     * @param size Buffer size in bytes
     * @return true if set successfully
     */
    bool setSendBufferSize(int size);
    
    /**
     * @brief Set socket to reuse address (SO_REUSEADDR)
     * @param enable true to enable address reuse
     * @return true if set successfully
     */
    bool setReuseAddress(bool enable);
    
    /**
     * @brief Get maximum UDP packet size
     * @return Maximum datagram size (typically 65507 bytes)
     */
    static constexpr size_t getMaxPacketSize() { return 65507; }

private:
    int socket_fd_;                 // UDP socket file descriptor
    sockaddr_in local_addr_;        // Local address and port
    int local_port_;                // Cached local port number
    bool is_bound_;                 // Whether socket is bound
    bool broadcast_enabled_;        // Whether broadcast is enabled
    std::string multicast_group_;   // Multicast group (empty if not joined)
    
    /**
     * @brief Set socket to non-blocking mode
     * @return true if set successfully
     */
    bool setNonBlocking(bool enable);
    
    /**
     * @brief Wait for socket to be readable (used for timeouts)
     * @param timeout_ms Timeout in milliseconds
     * @return true if readable, false if timeout
     */
    bool waitForReadable(int timeout_ms);
};

} // namespace miuacp
