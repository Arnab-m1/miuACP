/**
 * @file header.h
 * @brief µACP Protocol Header Implementation
 * 
 * This file defines the UACPHeader class for handling the fixed 8-byte
 * header structure of µACP messages.
 * 
 * @author Arnab
 * @version 1.0.0
 * @license MIT
 */

#pragma once

#include "enums.h"
#include <vector>
#include <cstdint>

namespace miuacp {

/**
 * @brief µACP fixed 8-byte header class
 * 
 * The header contains all essential protocol information in a compact format:
 * - Version (2 bits): Protocol version
 * - Verb (2 bits): Message verb type
 * - QoS (2 bits): Quality of service level
 * - Code (8 bits): Response code
 * - Message ID (24 bits): Unique message identifier
 * - Options Count (8 bits): Number of TLV options
 */
class UACPHeader {
public:
    /**
     * @brief Default constructor
     */
    UACPHeader();
    
    /**
     * @brief Constructor with parameters
     * @param version Protocol version
     * @param verb Message verb
     * @param qos Quality of service level
     * @param code Response code
     * @param msg_id Message ID
     * @param opts_count Number of options
     */
    UACPHeader(uint8_t version, UACPVerb verb, uint8_t qos, 
               uint8_t code, uint32_t msg_id, uint8_t opts_count);
    
    /**
     * @brief Copy constructor
     */
    UACPHeader(const UACPHeader& other) = default;
    
    /**
     * @brief Move constructor
     */
    UACPHeader(UACPHeader&& other) noexcept = default;
    
    /**
     * @brief Assignment operator
     */
    UACPHeader& operator=(const UACPHeader& other) = default;
    
    /**
     * @brief Move assignment operator
     */
    UACPHeader& operator=(UACPHeader&& other) noexcept = default;
    
    /**
     * @brief Destructor
     */
    ~UACPHeader() = default;
    
    // Getters
    uint8_t getVersion() const { return version_; }
    UACPVerb getVerb() const { return verb_; }
    uint8_t getQoS() const { return qos_; }
    uint8_t getCode() const { return code_; }
    uint32_t getMessageId() const { return msg_id_; }
    uint8_t getOptionsCount() const { return opts_count_; }
    
    // Setters
    void setVersion(uint8_t version) { version_ = version; }
    void setVerb(UACPVerb verb) { verb_ = verb; }
    void setQoS(uint8_t qos) { qos_ = qos; }
    void setCode(uint8_t code) { code_ = code; }
    void setMessageId(uint32_t msg_id) { msg_id_ = msg_id; }
    void setOptionsCount(uint8_t opts_count) { opts_count_ = opts_count; }
    
    /**
     * @brief Pack header into 8 bytes
     * @return Packed header bytes
     */
    std::vector<uint8_t> pack() const;
    
    /**
     * @brief Unpack header from 8 bytes
     * @param data Binary data (must be at least 8 bytes)
     * @return Unpacked header
     * @throws std::runtime_error if data is too short
     */
    static UACPHeader unpack(const std::vector<uint8_t>& data);
    
    /**
     * @brief Unpack header from 8 bytes at specific offset
     * @param data Binary data
     * @param offset Starting offset
     * @return Unpacked header
     * @throws std::runtime_error if data is too short
     */
    static UACPHeader unpack(const std::vector<uint8_t>& data, size_t offset);
    
    /**
     * @brief Get header size (always 8 bytes)
     * @return Header size in bytes
     */
    static constexpr size_t getSize() { return Constants::HEADER_SIZE; }
    
    /**
     * @brief Validate header values
     * @return True if header is valid
     */
    bool isValid() const;
    
    /**
     * @brief Create a response header
     * @param request_header Original request header
     * @param response_code Response status code
     * @return Response header
     */
    static UACPHeader createResponse(const UACPHeader& request_header, StatusCode response_code);

private:
    uint8_t version_;      ///< Protocol version (2 bits)
    UACPVerb verb_;        ///< Message verb (2 bits)
    uint8_t qos_;          ///< Quality of service (2 bits)
    uint8_t code_;         ///< Response code (8 bits)
    uint32_t msg_id_;      ///< Message ID (24 bits)
    uint8_t opts_count_;   ///< Number of options (8 bits)
    
    /**
     * @brief Validate version field
     * @param version Version to validate
     * @return True if valid
     */
    static bool isValidVersion(uint8_t version);
    
    /**
     * @brief Validate QoS field
     * @param qos QoS to validate
     * @return True if valid
     */
    static bool isValidQoS(uint8_t qos);
    
    /**
     * @brief Validate message ID field
     * @param msg_id Message ID to validate
     * @return True if valid
     */
    static bool isValidMessageId(uint32_t msg_id);
};

} // namespace miuacp
