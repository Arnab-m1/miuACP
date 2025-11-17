/**
 * @file message.h
 * @brief µACP Message Implementation
 * 
 * This file defines the UACPMessage class for handling complete µACP messages
 * including header, options, and payload.
 * 
 * @author Arnab
 * @version 1.0.0
 * @license MIT
 */

#pragma once

#include "header.h"
#include "option.h"
#include "enums.h"
#include <vector>
#include <string>
#include <memory>
#include <functional>

namespace miuacp {

/**
 * @brief µACP message class
 * 
 * Represents a complete µACP message containing:
 * - Fixed 8-byte header
 * - Variable number of TLV options
 * - Variable length payload
 */
class UACPMessage {
public:
    /**
     * @brief Default constructor
     */
    UACPMessage();
    
    /**
     * @brief Constructor with header
     * @param header Message header
     */
    UACPMessage(const UACPHeader& header);
    
    /**
     * @brief Constructor with parameters
     * @param verb Message verb
     * @param payload Message payload
     * @param msg_id Message ID
     * @param qos Quality of service level
     * @param code Response code
     */
    UACPMessage(UACPVerb verb, const std::vector<uint8_t>& payload, 
                uint32_t msg_id = 0, uint8_t qos = 0, uint8_t code = 0);
    
    /**
     * @brief Copy constructor
     */
    UACPMessage(const UACPMessage& other);
    
    /**
     * @brief Move constructor
     */
    UACPMessage(UACPMessage&& other) noexcept;
    
    /**
     * @brief Assignment operator
     */
    UACPMessage& operator=(const UACPMessage& other);
    
    /**
     * @brief Move assignment operator
     */
    UACPMessage& operator=(UACPMessage&& other) noexcept;
    
    /**
     * @brief Destructor
     */
    ~UACPMessage() = default;
    
    // Header access
    const UACPHeader& getHeader() const { return header_; }
    UACPHeader& getHeader() { return header_; }
    
    // Options access
    const std::vector<UACPOption>& getOptions() const { return options_; }
    std::vector<UACPOption>& getOptions() { return options_; }
    
    // Payload access
    const std::vector<uint8_t>& getPayload() const { return payload_; }
    std::vector<uint8_t>& getPayload() { return payload_; }
    
    /**
     * @brief Add option to message
     * @param option Option to add
     */
    void addOption(const UACPOption& option);
    
    /**
     * @brief Add option with string value
     * @param type Option type
     * @param value String value
     */
    void addOption(UACPOptionType type, const std::string& value);
    
    /**
     * @brief Add option with integer value
     * @param type Option type
     * @param value Integer value
     */
    void addOption(UACPOptionType type, uint32_t value);
    
    /**
     * @brief Add option with byte array value
     * @param type Option type
     * @param value Byte array value
     */
    void addOption(UACPOptionType type, const std::vector<uint8_t>& value);
    
    /**
     * @brief Get option by type
     * @param type Option type to find
     * @return Pointer to option if found, nullptr otherwise
     */
    const UACPOption* getOption(UACPOptionType type) const;
    
    /**
     * @brief Remove option by type
     * @param type Option type to remove
     * @return True if option was found and removed
     */
    bool removeOption(UACPOptionType type);
    
    /**
     * @brief Set payload from string
     * @param payload String payload
     */
    void setPayload(const std::string& payload);
    
    /**
     * @brief Set payload from byte array
     * @param payload Byte array payload
     */
    void setPayload(const std::vector<uint8_t>& payload);
    
    /**
     * @brief Get payload as string
     * @return Payload as string
     */
    std::string getPayloadAsString() const;
    
    /**
     * @brief Pack message into binary format
     * @return Packed message bytes
     * @throws std::runtime_error if message is invalid
     */
    std::vector<uint8_t> pack() const;
    
    /**
     * @brief Unpack message from binary format
     * @param data Binary data
     * @return Unpacked message
     * @throws std::runtime_error if unpacking fails
     */
    static UACPMessage unpack(const std::vector<uint8_t>& data);
    
    /**
     * @brief Unpack message from binary format at specific offset
     * @param data Binary data
     * @param offset Starting offset
     * @return Unpacked message
     * @throws std::runtime_error if unpacking fails
     */
    static UACPMessage unpack(const std::vector<uint8_t>& data, size_t offset);
    
    /**
     * @brief Get total message size when packed
     * @return Size in bytes
     */
    size_t getPackedSize() const;
    
    /**
     * @brief Validate message
     * @return True if message is valid
     */
    bool isValid() const;
    
    /**
     * @brief Create a response message
     * @param response_code Response status code
     * @param response_payload Response payload
     * @return Response message
     */
    UACPMessage createResponse(StatusCode response_code, 
                              const std::vector<uint8_t>& response_payload = {}) const;
    
    /**
     * @brief Create a response message with string payload
     * @param response_code Response status code
     * @param response_payload Response payload as string
     * @return Response message
     */
    UACPMessage createResponse(StatusCode response_code, 
                              const std::string& response_payload) const;
    
    /**
     * @brief Check if message is a request
     * @return True if request message
     */
    bool isRequest() const;
    
    /**
     * @brief Check if message is a response
     * @return True if response message
     */
    bool isResponse() const;
    
    /**
     * @brief Get topic path from options
     * @return Topic path if found, empty string otherwise
     */
    std::string getTopicPath() const;
    
    /**
     * @brief Set topic path in options
     * @param topic_path Topic path to set
     */
    void setTopicPath(const std::string& topic_path);
    
    /**
     * @brief Get content type from options
     * @return Content type if found, CBOR as default
     */
    UACPContentType getContentType() const;
    
    /**
     * @brief Set content type in options
     * @param content_type Content type to set
     */
    void setContentType(UACPContentType content_type);

private:
    UACPHeader header_;                    ///< Message header
    std::vector<UACPOption> options_;      ///< Message options
    std::vector<uint8_t> payload_;         ///< Message payload
    bool is_response_;                     ///< Whether this message is a response
    
    /**
     * @brief Update options count in header
     */
    void updateOptionsCount();
    
    /**
     * @brief Validate message size
     * @return True if size is valid
     */
    bool validateSize() const;
};

} // namespace miuacp
