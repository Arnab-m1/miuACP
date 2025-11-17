/**
 * @file protocol.h
 * @brief µACP Protocol Core Implementation
 * 
 * This file defines the UACPProtocol class which provides the main interface
 * for creating and managing µACP messages and protocol operations.
 * 
 * @author Arnab
 * @version 1.0.0
 * @license MIT
 */

#pragma once

#include "message.h"
#include "header.h"
#include "option.h"
#include "enums.h"
#include <vector>
#include <string>
#include <memory>
#include <functional>
#include <random>

namespace miuacp {

/**
 * @brief µACP Protocol core class
 * 
 * Provides the main interface for µACP protocol operations including:
 * - Message creation and validation
 * - Protocol utilities and helpers
 * - Message ID generation
 * - Protocol constants and configuration
 */
class UACPProtocol {
public:
    /**
     * @brief Constructor
     */
    UACPProtocol();
    
    /**
     * @brief Destructor
     */
    ~UACPProtocol() = default;
    
    /**
     * @brief Create a new message
     * @param verb Message verb
     * @param payload Message payload
     * @param msg_id Message ID (0 for auto-generated)
     * @param qos Quality of service level
     * @param code Response code
     * @return Created message
     */
    UACPMessage createMessage(UACPVerb verb, 
                             const std::vector<uint8_t>& payload,
                             uint32_t msg_id = 0,
                             uint8_t qos = 0,
                             uint8_t code = 0) const;
    
    /**
     * @brief Create a new message with string payload
     * @param verb Message verb
     * @param payload String payload
     * @param msg_id Message ID (0 for auto-generated)
     * @param qos Quality of service level
     * @param code Response code
     * @return Created message
     */
    UACPMessage createMessage(UACPVerb verb, 
                             const std::string& payload,
                             uint32_t msg_id = 0,
                             uint8_t qos = 0,
                             uint8_t code = 0) const;
    
    /**
     * @brief Create a PING message
     * @param msg_id Message ID (0 for auto-generated)
     * @return PING message
     */
    UACPMessage createPing(uint32_t msg_id = 0) const;
    
    /**
     * @brief Create a TELL message
     * @param payload Message payload
     * @param topic Topic path
     * @param msg_id Message ID (0 for auto-generated)
     * @param qos Quality of service level
     * @return TELL message
     */
    UACPMessage createTell(const std::vector<uint8_t>& payload,
                          const std::string& topic = "",
                          uint32_t msg_id = 0,
                          uint8_t qos = 0) const;
    
    /**
     * @brief Create a TELL message with string payload
     * @param payload String payload
     * @param topic Topic path
     * @param msg_id Message ID (0 for auto-generated)
     * @param qos Quality of service level
     * @return TELL message
     */
    UACPMessage createTell(const std::string& payload,
                          const std::string& topic = "",
                          uint32_t msg_id = 0,
                          uint8_t qos = 0) const;
    
    /**
     * @brief Create an ASK message
     * @param payload Request payload
     * @param topic Topic path
     * @param msg_id Message ID (0 for auto-generated)
     * @param qos Quality of service level
     * @return ASK message
     */
    UACPMessage createAsk(const std::vector<uint8_t>& payload,
                         const std::string& topic = "",
                         uint32_t msg_id = 0,
                         uint8_t qos = 1) const;
    
    /**
     * @brief Create an ASK message with string payload
     * @param payload String request payload
     * @param topic Topic path
     * @param msg_id Message ID (0 for auto-generated)
     * @param qos Quality of service level
     * @return ASK message
     */
    UACPMessage createAsk(const std::string& payload,
                         const std::string& topic = "",
                         uint32_t msg_id = 0,
                         uint8_t qos = 1) const;
    
    /**
     * @brief Create an OBSERVE message
     * @param payload Subscription payload
     * @param topic Topic path to observe
     * @param msg_id Message ID (0 for auto-generated)
     * @param qos Quality of service level
     * @return OBSERVE message
     */
    UACPMessage createObserve(const std::vector<uint8_t>& payload,
                             const std::string& topic,
                             uint32_t msg_id = 0,
                             uint8_t qos = 1) const;
    
    /**
     * @brief Create an OBSERVE message with string payload
     * @param payload String subscription payload
     * @param topic Topic path to observe
     * @param msg_id Message ID (0 for auto-generated)
     * @param qos Quality of service level
     * @return OBSERVE message
     */
    UACPMessage createObserve(const std::string& payload,
                             const std::string& topic,
                             uint32_t msg_id = 0,
                             uint8_t qos = 1) const;
    
    /**
     * @brief Generate a unique message ID
     * @return Unique message ID
     */
    uint32_t generateMessageId() const;
    
    /**
     * @brief Validate a message
     * @param message Message to validate
     * @return True if message is valid
     */
    bool validateMessage(const UACPMessage& message) const;
    
    /**
     * @brief Get protocol version
     * @return Protocol version
     */
    static uint8_t getProtocolVersion() { return Constants::PROTOCOL_VERSION; }
    
    /**
     * @brief Get maximum message size
     * @return Maximum message size in bytes
     */
    static size_t getMaxMessageSize() { return Constants::MAX_MESSAGE_SIZE; }
    
    /**
     * @brief Get maximum payload size
     * @return Maximum payload size in bytes
     */
    static size_t getMaxPayloadSize() { return Constants::MAX_PAYLOAD_SIZE; }
    
    /**
     * @brief Check if message size is valid
     * @param size Message size to check
     * @return True if size is valid
     */
    static bool isValidMessageSize(size_t size) {
        return size <= Constants::MAX_MESSAGE_SIZE;
    }
    
    /**
     * @brief Check if payload size is valid
     * @param size Payload size to check
     * @return True if size is valid
     */
    static bool isValidPayloadSize(size_t size) {
        return size <= Constants::MAX_PAYLOAD_SIZE;
    }

private:
    mutable std::mt19937 rng_;                     ///< Random number generator
    mutable std::uniform_int_distribution<uint32_t> msg_id_dist_;  ///< Message ID distribution
    
    /**
     * @brief Initialize random number generator
     */
    void initializeRNG();
};

} // namespace miuacp
