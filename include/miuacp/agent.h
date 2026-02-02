/**
 * @file agent.h
 * @brief µACP Peer-to-Peer Agent Implementation
 * 
 * This file defines the UACPAgent class for symmetric peer-to-peer agent communication.
 * Agents can send to and receive from any other agent without client/server distinction.
 * 
 * @author Arnab
 * @version 2.0.0 (Redesigned for P2P)
 * @license MIT
 */

#pragma once

#include "transport.h"
#include "udp_transport.h"
#include "protocol.h"
#include "message.h"
#include <string>
#include <vector>
#include <map>
#include <set>
#include <memory>
#include <functional>
#include <atomic>
#include <thread>
#include <mutex>
#include <future>
#include <chrono>

namespace miuacp {

/**
 * @brief Agent capability definition
 */
struct UACPCapability {
    std::string name;
    std::string description;
    std::vector<std::string> topics;  // Topics this capability can handle
    std::string input_format;         // Expected input format
    std::string output_format;        // Output format
    
    UACPCapability(const std::string& n, const std::string& desc, 
                   const std::vector<std::string>& t, 
                   const std::string& input_fmt = "text", 
                   const std::string& output_fmt = "text")
        : name(n), description(desc), topics(t), input_format(input_fmt), output_format(output_fmt) {}
};

/**
 * @brief Peer agent information
 */
struct UACPPeerInfo {
    std::string agent_id;
    std::string host;
    int port;
    std::chrono::steady_clock::time_point last_seen;
    std::vector<UACPCapability> capabilities;
    
    UACPPeerInfo(const std::string& id, const std::string& h, int p)
        : agent_id(id), host(h), port(p), last_seen(std::chrono::steady_clock::now()) {}
};

/**
 * @brief Agent information for self-description
 */
struct UACPAgentInfo {
    std::string agent_id;
    std::string name;
    std::vector<UACPCapability> capabilities;
    std::vector<std::string> topics;
    std::vector<UACPContentType> content_types;
    size_t max_block_size;
    
    UACPAgentInfo(const std::string& id, const std::string& n)
        : agent_id(id), name(n), max_block_size(1024) {}
};

/**
 * @brief Message handler function type
 * @param message Incoming message
 * @param sender_host Hostname/IP of sender
 * @param sender_port Port of sender
 * @return Response message (or empty if no response needed)
 */
using MessageHandler = std::function<UACPMessage(const UACPMessage&, const std::string&, int)>;

/**
 * @brief Topic handler function type
 * @param message Incoming message
 * @param sender_host Hostname/IP of sender
 * @param sender_port Port of sender
 * @return Response message (or empty if no response needed)
 */
using TopicHandler = std::function<UACPMessage(const UACPMessage&, const std::string&, int)>;

/**
 * @brief µACP Peer-to-Peer Agent class
 * 
 * Symmetric agent that can send to and receive from any other agent.
 * No client/server distinction - all agents are equal peers.
 * 
 * Features:
 * - Send messages to any peer
 * - Receive messages from any peer
 * - Discover peers via broadcast/multicast
 * - Handle messages via verb or topic handlers
 * - Automatic response generation
 * - Conversation tracking
 * - Subscription management
 */
class UACPAgent {
public:
    /**
     * @brief Constructor
     * @param agent_id Unique agent identifier (auto-generated if empty)
     * @param name Human-readable agent name
     * @param host Local address to bind ("0.0.0.0" for all interfaces)
     * @param port Local port to listen on (0 = OS assigns ephemeral port)
     * @param transport Optional custom transport (defaults to UDP)
     */
    UACPAgent(const std::string& agent_id = "",
              const std::string& name = "µACP Agent",
              const std::string& host = "0.0.0.0",
              int port = 0,
              std::unique_ptr<UACPTransport> transport = nullptr);
    
    /**
     * @brief Destructor - stops agent and closes transport
     */
    ~UACPAgent();
    
    // Disable copy
    UACPAgent(const UACPAgent&) = delete;
    UACPAgent& operator=(const UACPAgent&) = delete;
    
    // ========== Lifecycle ==========
    
    /**
     * @brief Start the agent (bind transport and begin receiving)
     * @return true if started successfully
     */
    bool start();
    
    /**
     * @brief Stop the agent (stop receiving and close transport)
     */
    void stop();
    
    /**
     * @brief Check if agent is running
     * @return true if running
     */
    bool isRunning() const { return running_.load(); }
    
    // ========== Agent Information ==========
    
    /**
     * @brief Get agent ID
     * @return Agent identifier
     */
    std::string getAgentId() const { return agent_info_.agent_id; }
    
    /**
     * @brief Get agent name
     * @return Agent name
     */
    std::string getName() const { return agent_info_.name; }
    
    /**
     * @brief Get agent address as "host:port"
     * @return Address string
     */
    std::string getAddress() const;
    
    /**
     * @brief Get local port agent is bound to
     * @return Port number (0 if not bound)
     */
    int getPort() const;
    
    /**
     * @brief Get agent information
     * @return Reference to agent info
     */
    const UACPAgentInfo& getAgentInfo() const { return agent_info_; }
    
    // ========== Peer Discovery ==========
    
    /**
     * @brief Discover peers on the network via broadcast
     * @param broadcast_addr Broadcast address (default: 255.255.255.255)
     * @param port Port to broadcast to (default: 8888)
     * @return Number of discovery messages sent
     */
    int discoverPeers(const std::string& broadcast_addr = "255.255.255.255", int port = 8888);
    
    /**
     * @brief Get list of discovered peers
     * @return Vector of peer addresses as "host:port"
     */
    std::vector<std::string> getDiscoveredPeers() const;
    
    /**
     * @brief Manually add a known peer
     * @param peer_host Peer hostname/IP
     * @param peer_port Peer port
     * @param peer_id Peer agent ID (optional)
     */
    void addPeer(const std::string& peer_host, int peer_port, const std::string& peer_id = "");
    
    /**
     * @brief Remove a peer from registry
     * @param peer_host Peer hostname/IP
     * @param peer_port Peer port
     */
    void removePeer(const std::string& peer_host, int peer_port);
    
    /**
     * @brief Get peer information
     * @param peer_host Peer hostname/IP
     * @param peer_port Peer port
     * @return Pointer to peer info if found, nullptr otherwise
     */
    const UACPPeerInfo* getPeerInfo(const std::string& peer_host, int peer_port) const;
    
    // ========== Send to Peers ==========
    
    /**
     * @brief Send message to a peer
     * @param peer_host Peer hostname/IP
     * @param peer_port Peer port
     * @param message Message to send
     * @return Response message if successful, empty message if failed
     */
    UACPMessage sendToPeer(const std::string& peer_host, int peer_port, const UACPMessage& message);
    
    /**
     * @brief Send PING to peer
     * @param peer_host Peer hostname/IP
     * @param peer_port Peer port
     * @return true if peer responded with PONG
     */
    bool ping(const std::string& peer_host, int peer_port);
    
    /**
     * @brief Send TELL (one-way message) to peer
     * @param peer_host Peer hostname/IP
     * @param peer_port Peer port
     * @param payload Message payload
     * @param topic Topic path
     * @param qos Quality of service level
     * @return true if message sent successfully
     */
    bool tell(const std::string& peer_host, int peer_port, const std::vector<uint8_t>& payload,
              const std::string& topic = "", uint8_t qos = 0);
    
    /**
     * @brief Send TELL with string payload
     * @param peer_host Peer hostname/IP
     * @param peer_port Peer port
     * @param payload String payload
     * @param topic Topic path
     * @param qos Quality of service level
     * @return true if message sent successfully
     */
    bool tell(const std::string& peer_host, int peer_port, const std::string& payload,
              const std::string& topic = "", uint8_t qos = 0);
    
    /**
     * @brief Send ASK (request-response) to peer and wait for response
     * @param peer_host Peer hostname/IP
     * @param peer_port Peer port
     * @param payload Request payload
     * @param topic Topic path
     * @param qos Quality of service level
     * @param timeout Timeout for response
     * @return Response message if successful, empty message if timeout/failed
     */
    UACPMessage ask(const std::string& peer_host, int peer_port, const std::vector<uint8_t>& payload,
                    const std::string& topic = "", uint8_t qos = 1,
                    std::chrono::milliseconds timeout = std::chrono::milliseconds(30000));
    
    /**
     * @brief Send ASK with string payload
     * @param peer_host Peer hostname/IP
     * @param peer_port Peer port
     * @param payload String request payload
     * @param topic Topic path
     * @param qos Quality of service level
     * @param timeout Timeout for response
     * @return Response message if successful, empty message if timeout/failed
     */
    UACPMessage ask(const std::string& peer_host, int peer_port, const std::string& payload,
                    const std::string& topic = "", uint8_t qos = 1,
                    std::chrono::milliseconds timeout = std::chrono::milliseconds(30000));
    
    /**
     * @brief Send OBSERVE (subscribe to topic) to peer
     * @param peer_host Peer hostname/IP
     * @param peer_port Peer port
     * @param topic Topic to observe
     * @param qos Quality of service level
     * @return true if subscription successful
     */
    bool observe(const std::string& peer_host, int peer_port, const std::string& topic, uint8_t qos = 1);
    
    /**
     * @brief Send NOTIFY (publish) to all subscribers of a topic
     * @param topic Topic to notify
     * @param payload Notification payload
     * @param qos Quality of service level
     * @return Number of subscribers notified
     */
    int notifyTopic(const std::string& topic, const std::vector<uint8_t>& payload, uint8_t qos = 0);
    
    /**
     * @brief Send NOTIFY with string payload
     * @param topic Topic to notify
     * @param payload String notification payload
     * @param qos Quality of service level
     * @return Number of subscribers notified
     */
    int notifyTopic(const std::string& topic, const std::string& payload, uint8_t qos = 0);
    
    // ========== Message Handling ==========
    
    /**
     * @brief Add message handler for a specific verb
     * @param verb Verb to handle
     * @param handler Handler function
     */
    void addMessageHandler(UACPVerb verb, MessageHandler handler);
    
    /**
     * @brief Remove message handler for a verb
     * @param verb Verb
     * @return true if handler was found and removed
     */
    bool removeMessageHandler(UACPVerb verb);
    
    /**
     * @brief Add topic handler
     * @param topic_pattern Topic pattern (supports wildcards: * and #)
     * @param handler Handler function
     */
    void addTopicHandler(const std::string& topic_pattern, TopicHandler handler);
    
    /**
     * @brief Remove topic handler
     * @param topic_pattern Topic pattern
     * @return true if handler was found and removed
     */
    bool removeTopicHandler(const std::string& topic_pattern);
    
    /**
     * @brief Check if agent can handle topic
     * @param topic Topic to check
     * @return true if agent has a handler for this topic
     */
    bool canHandleTopic(const std::string& topic) const;
    
    // ========== Capability Management ==========
    
    /**
     * @brief Add capability to agent
     * @param capability Capability to add
     */
    void addCapability(const UACPCapability& capability);
    
    /**
     * @brief Remove capability by name
     * @param name Capability name
     * @return true if capability was found and removed
     */
    bool removeCapability(const std::string& name);
    
    /**
     * @brief Get capability by name
     * @param name Capability name
     * @return Pointer to capability if found, nullptr otherwise
     */
    const UACPCapability* getCapability(const std::string& name) const;
    
    /**
     * @brief Get all capabilities
     * @return Vector of capabilities
     */
    const std::vector<UACPCapability>& getCapabilities() const { return agent_info_.capabilities; }
    
    // ========== Statistics ==========
    
    /**
     * @brief Get agent statistics
     * @return Map of statistics
     */
    std::map<std::string, uint64_t> getStatistics() const;

private:
    // Agent info
    UACPAgentInfo agent_info_;
    std::string host_;
    int port_;
    
    // Transport layer
    std::unique_ptr<UACPTransport> transport_;
    UACPProtocol protocol_;
    
    // Peer registry
    std::map<std::string, UACPPeerInfo> peers_;  // "host:port" -> peer info
    mutable std::mutex peers_mutex_;
    
    // Message handlers
    std::map<UACPVerb, MessageHandler> verb_handlers_;
    std::map<std::string, TopicHandler> topic_handlers_;
    mutable std::mutex handlers_mutex_;
    
    // Subscriptions (peers that have subscribed to our topics)
    struct Subscription {
        std::string topic;
        std::string peer_host;
        int peer_port;
        uint8_t qos;
        std::chrono::steady_clock::time_point timestamp;
    };
    std::vector<Subscription> subscriptions_;
    mutable std::mutex subscriptions_mutex_;
    
    // Pending requests (waiting for responses)
    struct PendingRequest {
        uint32_t message_id;
        UACPMessage request;
        std::chrono::steady_clock::time_point timestamp;
        std::chrono::milliseconds timeout;
        std::promise<UACPMessage> promise;
    };
    std::map<uint32_t, PendingRequest> pending_requests_;
    mutable std::mutex pending_requests_mutex_;
    
    // State
    std::atomic<bool> running_;
    std::thread receiver_thread_;
    
    // Statistics
    std::atomic<uint64_t> messages_sent_;
    std::atomic<uint64_t> messages_received_;
    std::atomic<uint64_t> bytes_sent_;
    std::atomic<uint64_t> bytes_received_;
    
    // ========== Internal Methods ==========
    
    /**
     * @brief Receiver loop (runs in separate thread)
     */
    void receiverLoop();
    
    /**
     * @brief Handle incoming message from a peer
     * @param message Incoming message
     * @param sender_host Sender hostname/IP
     * @param sender_port Sender port
     */
    void handleIncomingMessage(const UACPMessage& message, const std::string& sender_host, int sender_port);
    
    /**
     * @brief Register default message handlers
     */
    void registerDefaultHandlers();
    
    /**
     * @brief Default PING handler
     */
    UACPMessage handlePing(const UACPMessage& message, const std::string& sender_host, int sender_port);
    
    /**
     * @brief Default TELL handler
     */
    UACPMessage handleTell(const UACPMessage& message, const std::string& sender_host, int sender_port);
    
    /**
     * @brief Default ASK handler
     */
    UACPMessage handleAsk(const UACPMessage& message, const std::string& sender_host, int sender_port);
    
    /**
     * @brief Default OBSERVE handler
     */
    UACPMessage handleObserve(const UACPMessage& message, const std::string& sender_host, int sender_port);
    
    /**
     * @brief Default NOTIFY handler
     */
    UACPMessage handleNotify(const UACPMessage& message, const std::string& sender_host, int sender_port);
    
    /**
     * @brief Default ANSWER handler (response to ASK)
     */
    UACPMessage handleAnswer(const UACPMessage& message, const std::string& sender_host, int sender_port);
    
    /**
     * @brief Find matching topic handler
     * @param topic Topic to match
     * @return Pointer to handler if found, nullptr otherwise
     */
    TopicHandler* findTopicHandler(const std::string& topic);
    
    /**
     * @brief Check if topic pattern matches topic
     * @param pattern Topic pattern (may contain wildcards)
     * @param topic Topic to match
     * @return true if pattern matches topic
     */
    bool topicMatches(const std::string& pattern, const std::string& topic) const;
    
    /**
     * @brief Generate unique agent ID
     * @return Unique agent ID
     */
    std::string generateAgentId();
    
    /**
     * @brief Generate peer key from host and port
     * @param host Hostname/IP
     * @param port Port
     * @return Peer key as "host:port"
     */
    std::string getPeerKey(const std::string& host, int port) const;
};

} // namespace miuacp
