/**
 * @file agent.h
 * @brief µACP Agent Implementation
 * 
 * This file defines the UACPAgent class which combines client and server
 * functionality to create a complete agent implementation.
 * 
 * @author Arnab
 * @version 1.0.0
 * @license MIT
 */

#pragma once

#include "client.h"
#include "server.h"
#include "protocol.h"
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <functional>
#include <atomic>
#include <future>

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
 * @brief Agent information for discovery
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
 * @brief Topic handler function type
 */
using TopicHandler = std::function<UACPMessage(const UACPMessage&, const std::string&, int)>;

/**
 * @brief µACP Agent class
 * 
 * Complete agent implementation that combines client and server functionality.
 * Provides a unified interface for agent communication, capability management,
 * and topic-based message handling.
 */
class UACPAgent {
public:
    /**
     * @brief Constructor
     * @param agent_id Unique agent identifier
     * @param name Agent name
     * @param host Host address to bind server to
     * @param port Port to listen on
     */
    UACPAgent(const std::string& agent_id = "", const std::string& name = "µACP Agent",
              const std::string& host = "0.0.0.0", int port = 8888);
    
    /**
     * @brief Destructor
     */
    ~UACPAgent();
    
    /**
     * @brief Start the agent
     * @return True if started successfully
     */
    bool start();
    
    /**
     * @brief Stop the agent
     */
    void stop();
    
    /**
     * @brief Check if agent is running
     * @return True if running
     */
    bool isRunning() const;
    
    /**
     * @brief Get agent information
     * @return Agent information
     */
    const UACPAgentInfo& getAgentInfo() const { return agent_info_; }
    
    /**
     * @brief Get agent address
     * @return Agent host:port string
     */
    std::string getAddress() const;
    
    // Capability management
    /**
     * @brief Add capability to agent
     * @param capability Capability to add
     */
    void addCapability(const UACPCapability& capability);
    
    /**
     * @brief Remove capability by name
     * @param name Capability name
     * @return True if capability was found and removed
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
    
    // Topic handling
    /**
     * @brief Add topic handler
     * @param topic Topic pattern (supports wildcards)
     * @param handler Handler function
     */
    void addTopicHandler(const std::string& topic, TopicHandler handler);
    
    /**
     * @brief Remove topic handler
     * @param topic Topic pattern
     * @return True if handler was found and removed
     */
    bool removeTopicHandler(const std::string& topic);
    
    /**
     * @brief Check if agent can handle topic
     * @param topic Topic to check
     * @return True if agent can handle the topic
     */
    bool canHandleTopic(const std::string& topic) const;
    
    // Message sending (client functionality)
    /**
     * @brief Send message to another agent
     * @param host Remote host
     * @param port Remote port
     * @param message Message to send
     * @return Response message if successful, empty message if failed
     */
    UACPMessage sendMessage(const std::string& host, int port, const UACPMessage& message);
    
    /**
     * @brief Send message asynchronously
     * @param host Remote host
     * @param port Remote port
     * @param message Message to send
     * @return Future containing the response message
     */
    std::future<UACPMessage> sendMessageAsync(const std::string& host, int port, const UACPMessage& message);
    
    /**
     * @brief Send PING to another agent
     * @param host Remote host
     * @param port Remote port
     * @return True if PING successful
     */
    bool ping(const std::string& host, int port);
    
    /**
     * @brief Send TELL message to another agent
     * @param host Remote host
     * @param port Remote port
     * @param payload Message payload
     * @param topic Topic path
     * @param qos Quality of service level
     * @return True if message sent successfully
     */
    bool tell(const std::string& host, int port, const std::vector<uint8_t>& payload,
              const std::string& topic = "", uint8_t qos = 0);
    
    /**
     * @brief Send TELL message with string payload
     * @param host Remote host
     * @param port Remote port
     * @param payload String payload
     * @param topic Topic path
     * @param qos Quality of service level
     * @return True if message sent successfully
     */
    bool tell(const std::string& host, int port, const std::string& payload,
              const std::string& topic = "", uint8_t qos = 0);
    
    /**
     * @brief Send ASK message and wait for response
     * @param host Remote host
     * @param port Remote port
     * @param payload Request payload
     * @param topic Topic path
     * @param qos Quality of service level
     * @param timeout Timeout in milliseconds
     * @return Response message if successful, empty message if failed
     */
    UACPMessage ask(const std::string& host, int port, const std::vector<uint8_t>& payload,
                    const std::string& topic = "", uint8_t qos = 1,
                    std::chrono::milliseconds timeout = std::chrono::milliseconds(30000));
    
    /**
     * @brief Send ASK message with string payload and wait for response
     * @param host Remote host
     * @param port Remote port
     * @param payload String request payload
     * @param topic Topic path
     * @param qos Quality of service level
     * @param timeout Timeout in milliseconds
     * @return Response message if successful, empty message if failed
     */
    UACPMessage ask(const std::string& host, int port, const std::string& payload,
                    const std::string& topic = "", uint8_t qos = 1,
                    std::chrono::milliseconds timeout = std::chrono::milliseconds(30000));
    
    /**
     * @brief Send OBSERVE message to another agent
     * @param host Remote host
     * @param port Remote port
     * @param payload Subscription payload
     * @param topic Topic path to observe
     * @param qos Quality of service level
     * @return True if message sent successfully
     */
    bool observe(const std::string& host, int port, const std::vector<uint8_t>& payload,
                 const std::string& topic, uint8_t qos = 1);
    
    /**
     * @brief Send OBSERVE message with string payload
     * @param host Remote host
     * @param port Remote port
     * @param payload String subscription payload
     * @param topic Topic path to observe
     * @param qos Quality of service level
     * @return True if message sent successfully
     */
    bool observe(const std::string& host, int port, const std::string& payload,
                 const std::string& topic, uint8_t qos = 1);
    
    // Broadcasting
    /**
     * @brief Broadcast message to all subscribers of a topic
     * @param topic Topic to broadcast to
     * @param message Message to broadcast
     * @return Number of subscribers notified
     */
    int broadcastToTopic(const std::string& topic, const UACPMessage& message);
    
    /**
     * @brief Broadcast message to all subscribers of a topic
     * @param topic Topic to broadcast to
     * @param payload Message payload
     * @param qos Quality of service level
     * @return Number of subscribers notified
     */
    int broadcastToTopic(const std::string& topic, const std::vector<uint8_t>& payload, uint8_t qos = 0);
    
    /**
     * @brief Broadcast message with string payload
     * @param topic Topic to broadcast to
     * @param payload String payload
     * @param qos Quality of service level
     * @return Number of subscribers notified
     */
    int broadcastToTopic(const std::string& topic, const std::string& payload, uint8_t qos = 0);
    
    // Statistics and monitoring
    /**
     * @brief Get agent statistics
     * @return Map of statistics
     */
    std::map<std::string, uint64_t> getStatistics() const;
    
    /**
     * @brief Get client statistics
     * @return Map of client statistics
     */
    std::map<std::string, uint64_t> getClientStatistics() const;
    
    /**
     * @brief Get server statistics
     * @return Map of server statistics
     */
    std::map<std::string, uint64_t> getServerStatistics() const;

private:
    UACPAgentInfo agent_info_;
    std::unique_ptr<UACPClient> client_;
    std::unique_ptr<UACPServer> server_;
    UACPProtocol protocol_;
    
    // Topic handlers
    std::map<std::string, TopicHandler> topic_handlers_;
    mutable std::mutex topic_handlers_mutex_;
    
    // Agent state
    std::atomic<bool> running_;
    
    /**
     * @brief Register default message handlers
     */
    void registerDefaultHandlers();
    
    /**
     * @brief Handle incoming PING message
     * @param message PING message
     * @param client_host Client host
     * @param client_port Client port
     * @return Response message
     */
    UACPMessage handlePing(const UACPMessage& message, const std::string& client_host, int client_port);
    
    /**
     * @brief Handle incoming TELL message
     * @param message TELL message
     * @param client_host Client host
     * @param client_port Client port
     * @return Response message
     */
    UACPMessage handleTell(const UACPMessage& message, const std::string& client_host, int client_port);
    
    /**
     * @brief Handle incoming ASK message
     * @param message ASK message
     * @param client_host Client host
     * @param client_port Client port
     * @return Response message
     */
    UACPMessage handleAsk(const UACPMessage& message, const std::string& client_host, int client_port);
    
    /**
     * @brief Handle incoming OBSERVE message
     * @param message OBSERVE message
     * @param client_host Client host
     * @param client_port Client port
     * @return Response message
     */
    UACPMessage handleObserve(const UACPMessage& message, const std::string& client_host, int client_port);
    
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
     * @return True if pattern matches topic
     */
    bool topicMatches(const std::string& pattern, const std::string& topic) const;
    
    /**
     * @brief Generate unique agent ID
     * @return Unique agent ID
     */
    std::string generateAgentId();
};

} // namespace miuacp
