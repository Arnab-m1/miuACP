/**
 * @file option.h
 * @brief µACP TLV Option Implementation
 * 
 * This file defines the UACPOption class for handling Type-Length-Value
 * options in µACP messages.
 * 
 * @author Arnab
 * @version 1.0.0
 * @license MIT
 */

#pragma once

#include "enums.h"
#include <vector>
#include <string>
#include <cstdint>
#include <memory>

namespace miuacp {

/**
 * @brief µACP TLV option class
 * 
 * Represents a Type-Length-Value option that can be included in µACP messages.
 * Options provide extensibility and additional metadata for messages.
 */
class UACPOption {
public:
    /**
     * @brief Default constructor
     */
    UACPOption();
    
    /**
     * @brief Constructor for string value
     * @param type Option type
     * @param value String value
     */
    UACPOption(UACPOptionType type, const std::string& value);
    
    /**
     * @brief Constructor for integer value
     * @param type Option type
     * @param value Integer value
     */
    UACPOption(UACPOptionType type, uint32_t value);
    
    /**
     * @brief Constructor for byte array value
     * @param type Option type
     * @param value Byte array value
     */
    UACPOption(UACPOptionType type, const std::vector<uint8_t>& value);
    
    /**
     * @brief Copy constructor
     */
    UACPOption(const UACPOption& other);
    
    /**
     * @brief Move constructor
     */
    UACPOption(UACPOption&& other) noexcept;
    
    /**
     * @brief Assignment operator
     */
    UACPOption& operator=(const UACPOption& other);
    
    /**
     * @brief Move assignment operator
     */
    UACPOption& operator=(UACPOption&& other) noexcept;
    
    /**
     * @brief Destructor
     */
    ~UACPOption() = default;
    
    /**
     * @brief Get option type
     * @return Option type
     */
    UACPOptionType getType() const { return type_; }
    
    /**
     * @brief Get option value as string
     * @return String value
     * @throws std::runtime_error if value is not a string
     */
    std::string getStringValue() const;
    
    /**
     * @brief Get option value as integer
     * @return Integer value
     * @throws std::runtime_error if value is not an integer
     */
    uint32_t getIntValue() const;
    
    /**
     * @brief Get option value as byte array
     * @return Byte array value
     */
    const std::vector<uint8_t>& getBytesValue() const { return value_; }
    
    /**
     * @brief Check if option has string value
     * @return True if string value
     */
    bool isStringValue() const { return is_string_; }
    
    /**
     * @brief Check if option has integer value
     * @return True if integer value
     */
    bool isIntValue() const { return is_int_; }
    
    /**
     * @brief Pack option into binary format
     * @return Packed option bytes
     */
    std::vector<uint8_t> pack() const;
    
    /**
     * @brief Unpack option from binary format
     * @param data Binary data
     * @param offset Starting offset in data
     * @return Number of bytes consumed
     * @throws std::runtime_error if unpacking fails
     */
    static size_t unpack(const std::vector<uint8_t>& data, size_t offset, UACPOption& option);
    
    /**
     * @brief Get packed size of option
     * @return Size in bytes when packed
     */
    size_t getPackedSize() const;

private:
    UACPOptionType type_;                    ///< Option type
    std::vector<uint8_t> value_;             ///< Option value as bytes
    bool is_string_;                         ///< True if value is a string
    bool is_int_;                           ///< True if value is an integer
    
    /**
     * @brief Helper to pack integer value
     * @param value Integer value
     * @return Packed bytes
     */
    static std::vector<uint8_t> packInt(uint32_t value);
    
    /**
     * @brief Helper to unpack integer value
     * @param data Binary data
     * @param offset Starting offset
     * @return Unpacked integer value
     */
    static uint32_t unpackInt(const std::vector<uint8_t>& data, size_t offset);
};

} // namespace miuacp
