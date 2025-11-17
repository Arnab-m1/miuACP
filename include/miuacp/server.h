/**
 * @file server.h
 * @brief µACP Server Implementation
 * 
 * This file defines the UACPServer class for server-side message handling
 * and agent communication.
 * 
 * @author Arnab
 * @version 1.0.0
 * @license MIT
 */

#pragma once

#include "protocol.h"
#include "message.h"
#include <string>
#include <vector>
#include <map>
#include <set>
#include <memory>
#include <functional>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <chrono>

namespace miuacp {

/**
 * @brief Active subscription to a topic
 */
struct Subscription {
    std::string topic;
    std::string client_host;
    int client_port;
    uint8_t qos;
    std::chrono::steady_clock::time_point timestamp;
    std::string conversation_id;
    
    Subscription(const std::string& t, const std::string& host, int port, uint8_t q, const std::string& conv_id = "")
        : topic(t), client_host(host), client_port(port), qos(q), 
          timestamp(std::chrono::steady_clock::now()), conversation_id(conv_id) {}
};

/**
 * @brief Multi-turn conversation context
 */
struct Conversation {
    std::string conversation_id;
    std::string topic;
    std::string client_host;
    int client_port;
    std::map<std::string, std::string> state;
    std::chrono::steady_clock::time_point created_at;
    std::chrono::steady_clock::time_point last_activity;
    
    Conversation(const std::string& conv_id, const std::string& t, const std::string& host, int port)
        : conversation_id(conv_id), topic(t), client_host(host), client_port(port),
          created_at(std::chrono::steady_clock::now()),
          last_activity(std::chrono::steady_clock::now()) {}
};

/**
 * @brief Server message handler function type
 */
using ServerMessageHandler = std::function<UACPMessage(const UACPMessage&, const std::string&, int)>;

/**
 * @brief µACP Server class
 * 
 * Provides server-side functionality for handling µACP messages from clients.
 * Supports message routing, subscriptions, conversations, and automatic responses.
 */
class UACPServer {
public:
    /**
     * @brief Constructor
     * @param host Host address to bind to
     * @param port Port to listen on
     * @param max_connections Maximum number of concurrent connections
     * @param subscription_timeout Subscription timeout in milliseconds
     */
    UACPServer(const std::string& host = "0.0.0.0", int port = 8888,
               int max_connections = 100,
               std::chrono::milliseconds subscription_timeout = std::chrono::milliseconds(3600000));
    
    /**
     * @brief Destructor
     */
    ~UACPServer();
    
    /**
     * @brief Start the server
     * @return True if started successfully
     */
    bool start();
    
    /**
     * @brief Stop the server
     */
    void stop();
    
    /**
     * @brief Check if server is running
     * @return True if running
     */
    bool isRunning() const { return running_; }
    
    /**
     * @brief Get server address
     * @return Server host:port string
     */
    std::string getAddress() const;
    
    /**
     * @brief Add message handler for specific verb
     * @param verb Message verb to handle
     * @param handler Handler function
     */
    void addMessageHandler(UACPVerb verb, ServerMessageHandler handler);
    
    /**
     * @brief Remove message handler
     * @param verb Message verb
     */
    void removeMessageHandler(UACPVerb verb);
    
    /**
     * @brief Broadcast message to all subscribers of a topic
     * @param topic Topic to broadcast to
     * @param message Message to broadcast
     * @return Number of subscribers notified
     */
    int broadcastToTopic(const std::string& topic, const UACPMessage& message);
    
    /**
     * @brief Send message to specific client
     * @param host Client host
     * @param port Client port
     * @param message Message to send
     * @return True if sent successfully
     */
    bool sendToClient(const std::string& host, int port, const UACPMessage& message);
    
    /**
     * @brief Get active subscriptions for a topic
     * @param topic Topic name
     * @return Vector of subscriptions
     */
    std::vector<Subscription> getSubscriptions(const std::string& topic) const;
    
    /**
     * @brief Get all active subscriptions
     * @return Map of topic to subscriptions
     */
    std::map<std::string, std::vector<Subscription>> getAllSubscriptions() const;
    
    /**
     * @brief Get active conversations
     * @return Map of conversation ID to conversation
     */
    std::map<std::string, Conversation> getConversations() const;
    
    /**
     * @brief Get conversation by ID
     * @param conversation_id Conversation ID
     * @return Pointer to conversation if found, nullptr otherwise
     */
    const Conversation* getConversation(const std::string& conversation_id) const;
    
    /**
     * @brief Update conversation state
     * @param conversation_id Conversation ID
     * @param key State key
     * @param value State value
     * @return True if conversation found and updated
     */
    bool updateConversationState(const std::string& conversation_id, 
                                const std::string& key, const std::string& value);
    
    /**
     * @brief Get server statistics
     * @return Map of statistics
     */
    std::map<std::string, uint64_t> getStatistics() const;

private:
    std::string host_;
    int port_;
    int max_connections_;
    std::chrono::milliseconds subscription_timeout_;
    
    // Server state
    std::atomic<bool> running_;
    std::atomic<bool> stop_requested_;
    std::thread server_thread_;
    
    // Message handlers
    std::map<UACPVerb, ServerMessageHandler> message_handlers_;
    mutable std::mutex handlers_mutex_;
    
    // Subscriptions and conversations
    std::map<std::string, std::vector<Subscription>> subscriptions_;  // topic -> subscriptions
    std::map<std::string, Conversation> conversations_;  // conv_id -> conversation
    mutable std::mutex subscriptions_mutex_;
    mutable std::mutex conversations_mutex_;
    
    // Protocol and message management
    UACPProtocol protocol_;
    std::atomic<uint32_t> message_id_counter_;
    
    // Statistics
    mutable std::mutex stats_mutex_;
    std::map<std::string, uint64_t> statistics_;
    
    /**
     * @brief Server thread function
     */
    void serverThreadFunction();
    
    /**
     * @brief Handle incoming message
     * @param message Received message
     * @param client_host Client host address
     * @param client_port Client port
     */
    void handleMessage(const UACPMessage& message, const std::string& client_host, int client_port);
    
    /**
     * @brief Handle PING message
     * @param message PING message
     * @param client_host Client host
     * @param client_port Client port
     * @return Response message
     */
    UACPMessage handlePing(const UACPMessage& message, const std::string& client_host, int client_port);
    
    /**
     * @brief Handle TELL message
     * @param message TELL message
     * @param client_host Client host
     * @param client_port Client port
     * @return Response message
     */
    UACPMessage handleTell(const UACPMessage& message, const std::string& client_host, int client_port);
    
    /**
     * @brief Handle ASK message
     * @param message ASK message
     * @param client_host Client host
     * @param client_port Client port
     * @return Response message
     */
    UACPMessage handleAsk(const UACPMessage& message, const std::string& client_host, int client_port);
    
    /**
     * @brief Handle OBSERVE message
     * @param message OBSERVE message
     * @param client_host Client host
     * @param client_port Client port
     * @return Response message
     */
    UACPMessage handleObserve(const UACPMessage& message, const std::string& client_host, int client_port);
    
    /**
     * @brief Generate next message ID
     * @return Next message ID
     */
    uint32_t getNextMessageId();
    
    /**
     * @brief Add subscription
     * @param subscription Subscription to add
     */
    void addSubscription(const Subscription& subscription);
    
    /**
     * @brief Remove subscription
     * @param topic Topic name
     * @param client_host Client host
     * @param client_port Client port
     * @return True if subscription was found and removed
     */
    bool removeSubscription(const std::string& topic, const std::string& client_host, int client_port);
    
    /**
     * @brief Clean up expired subscriptions
     */
    void cleanupExpiredSubscriptions();
    
    /**
     * @brief Clean up expired conversations
     */
    void cleanupExpiredConversations();
    
    /**
     * @brief Update statistics
     * @param key Statistic key
     * @param increment Value to add
     */
    void updateStatistics(const std::string& key, uint64_t increment = 1);
    
    /**
     * @brief Send response to client
     * @param client_host Client host
     * @param client_port Client port
     * @param response Response message
     * @return True if sent successfully
     */
    bool sendResponse(const std::string& client_host, int client_port, const UACPMessage& response);
};

} // namespace miuacp
