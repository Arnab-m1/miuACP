/**
 * @file client.h
 * @brief µACP Client Implementation
 * 
 * This file defines the UACPClient class for client-side communication
 * with µACP agents and servers.
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
#include <memory>
#include <functional>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <chrono>
#include <future>

namespace miuacp {

/**
 * @brief Connection information for a remote agent
 */
struct ConnectionInfo {
    std::string host;
    int port;
    std::chrono::steady_clock::time_point last_activity;
    uint32_t message_id_counter;
    
    ConnectionInfo(const std::string& h, int p) 
        : host(h), port(p), last_activity(std::chrono::steady_clock::now()), message_id_counter(0) {}
};

/**
 * @brief Pending request waiting for response
 */
struct PendingRequest {
    UACPMessage message;
    std::chrono::steady_clock::time_point timestamp;
    std::chrono::milliseconds timeout;
    std::promise<UACPMessage> promise;
    int retries;
    
    PendingRequest(const UACPMessage& msg, std::chrono::milliseconds timeout_ms, int retry_count = 0)
        : message(msg), timestamp(std::chrono::steady_clock::now()), 
          timeout(timeout_ms), retries(retry_count) {}
};

/**
 * @brief Message handler function type
 */
using MessageHandler = std::function<void(const UACPMessage&, const std::string&, int)>;

/**
 * @brief µACP Client class
 * 
 * Provides client-side functionality for communicating with µACP agents and servers.
 * Supports both synchronous and asynchronous message sending with automatic retries
 * and timeout handling.
 */
class UACPClient {
public:
    /**
     * @brief Constructor
     * @param default_timeout Default timeout for requests in milliseconds
     * @param max_retries Maximum number of retries for failed requests
     */
    UACPClient(std::chrono::milliseconds default_timeout = std::chrono::milliseconds(30000),
               int max_retries = 3);
    
    /**
     * @brief Destructor
     */
    ~UACPClient();
    
    /**
     * @brief Connect to a remote agent
     * @param host Remote host address
     * @param port Remote port
     * @return True if connection successful
     */
    bool connect(const std::string& host, int port);
    
    /**
     * @brief Disconnect from a remote agent
     * @param host Remote host address
     * @param port Remote port
     */
    void disconnect(const std::string& host, int port);
    
    /**
     * @brief Check if connected to a remote agent
     * @param host Remote host address
     * @param port Remote port
     * @return True if connected
     */
    bool isConnected(const std::string& host, int port) const;
    
    /**
     * @brief Send a message synchronously
     * @param host Remote host address
     * @param port Remote port
     * @param message Message to send
     * @return Response message if successful, empty message if failed
     */
    UACPMessage sendMessage(const std::string& host, int port, const UACPMessage& message);
    
    /**
     * @brief Send a message asynchronously
     * @param host Remote host address
     * @param port Remote port
     * @param message Message to send
     * @return Future containing the response message
     */
    std::future<UACPMessage> sendMessageAsync(const std::string& host, int port, const UACPMessage& message);
    
    /**
     * @brief Send a PING message
     * @param host Remote host address
     * @param port Remote port
     * @return True if PING successful
     */
    bool ping(const std::string& host, int port);
    
    /**
     * @brief Send a TELL message
     * @param host Remote host address
     * @param port Remote port
     * @param payload Message payload
     * @param topic Topic path
     * @param qos Quality of service level
     * @return True if message sent successfully
     */
    bool tell(const std::string& host, int port, const std::vector<uint8_t>& payload,
              const std::string& topic = "", uint8_t qos = 0);
    
    /**
     * @brief Send a TELL message with string payload
     * @param host Remote host address
     * @param port Remote port
     * @param payload String payload
     * @param topic Topic path
     * @param qos Quality of service level
     * @return True if message sent successfully
     */
    bool tell(const std::string& host, int port, const std::string& payload,
              const std::string& topic = "", uint8_t qos = 0);
    
    /**
     * @brief Send an ASK message and wait for response
     * @param host Remote host address
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
     * @brief Send an ASK message with string payload and wait for response
     * @param host Remote host address
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
     * @brief Send an OBSERVE message
     * @param host Remote host address
     * @param port Remote port
     * @param payload Subscription payload
     * @param topic Topic path to observe
     * @param qos Quality of service level
     * @return True if message sent successfully
     */
    bool observe(const std::string& host, int port, const std::vector<uint8_t>& payload,
                 const std::string& topic, uint8_t qos = 1);
    
    /**
     * @brief Send an OBSERVE message with string payload
     * @param host Remote host address
     * @param port Remote port
     * @param payload String subscription payload
     * @param topic Topic path to observe
     * @param qos Quality of service level
     * @return True if message sent successfully
     */
    bool observe(const std::string& host, int port, const std::string& payload,
                 const std::string& topic, uint8_t qos = 1);
    
    /**
     * @brief Add message handler for incoming messages
     * @param verb Message verb to handle
     * @param handler Handler function
     */
    void addMessageHandler(UACPVerb verb, MessageHandler handler);
    
    /**
     * @brief Remove message handler
     * @param verb Message verb
     */
    void removeMessageHandler(UACPVerb verb);
    
    /**
     * @brief Start the client (for receiving messages)
     */
    void start();
    
    /**
     * @brief Stop the client
     */
    void stop();
    
    /**
     * @brief Check if client is running
     * @return True if running
     */
    bool isRunning() const { return running_; }
    
    /**
     * @brief Get client statistics
     * @return Map of statistics
     */
    std::map<std::string, uint64_t> getStatistics() const;

private:
    UACPProtocol protocol_;
    std::chrono::milliseconds default_timeout_;
    int max_retries_;
    
    // Connection management
    std::map<std::string, std::shared_ptr<ConnectionInfo>> connections_;
    mutable std::mutex connections_mutex_;
    
    // Pending requests
    std::map<uint32_t, std::shared_ptr<PendingRequest>> pending_requests_;
    mutable std::mutex pending_requests_mutex_;
    
    // Message handlers
    std::map<UACPVerb, MessageHandler> message_handlers_;
    mutable std::mutex handlers_mutex_;
    
    // Client state
    std::atomic<bool> running_;
    std::thread receiver_thread_;
    std::atomic<bool> stop_requested_;
    
    // Statistics
    mutable std::mutex stats_mutex_;
    std::map<std::string, uint64_t> statistics_;
    
    /**
     * @brief Get or create connection info
     * @param host Remote host
     * @param port Remote port
     * @return Connection info
     */
    std::shared_ptr<ConnectionInfo> getConnectionInfo(const std::string& host, int port);
    
    /**
     * @brief Generate next message ID for connection
     * @param host Remote host
     * @param port Remote port
     * @return Next message ID
     */
    uint32_t getNextMessageId(const std::string& host, int port);
    
    /**
     * @brief Send raw data to remote host
     * @param host Remote host
     * @param port Remote port
     * @param data Data to send
     * @return True if sent successfully
     */
    bool sendRawData(const std::string& host, int port, const std::vector<uint8_t>& data);
    
    /**
     * @brief Receive raw data from remote host
     * @param host Remote host
     * @param port Remote port
     * @param data Buffer to receive data
     * @param timeout Timeout in milliseconds
     * @return Number of bytes received, -1 if failed
     */
    int receiveRawData(const std::string& host, int port, std::vector<uint8_t>& data,
                       std::chrono::milliseconds timeout);
    
    /**
     * @brief Message receiver thread function
     */
    void receiverThreadFunction();
    
    /**
     * @brief Process incoming message
     * @param message Received message
     * @param host Source host
     * @param port Source port
     */
    void processIncomingMessage(const UACPMessage& message, const std::string& host, int port);
    
    /**
     * @brief Update statistics
     * @param key Statistic key
     * @param increment Value to add
     */
    void updateStatistics(const std::string& key, uint64_t increment = 1);
    
    /**
     * @brief Clean up expired pending requests
     */
    void cleanupExpiredRequests();
};

} // namespace miuacp
