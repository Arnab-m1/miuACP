/**
 * @file option.cpp
 * @brief µACP TLV Option Implementation
 */

#include "miuacp/option.h"
#include <stdexcept>
#include <cstring>

namespace miuacp {

UACPOption::UACPOption()
    : type_(UACPOptionType::TOPIC_PATH), is_string_(false), is_int_(false) {
}

UACPOption::UACPOption(UACPOptionType type, const std::string& value)
    : type_(type), is_string_(true), is_int_(false) {
    value_ = std::vector<uint8_t>(value.begin(), value.end());
}

UACPOption::UACPOption(UACPOptionType type, uint32_t value)
    : type_(type), is_string_(false), is_int_(true) {
    value_ = packInt(value);
}

UACPOption::UACPOption(UACPOptionType type, const std::vector<uint8_t>& value)
    : type_(type), is_string_(false), is_int_(false) {
    value_ = value;
}

UACPOption::UACPOption(const UACPOption& other)
    : type_(other.type_), value_(other.value_), 
      is_string_(other.is_string_), is_int_(other.is_int_) {
}

UACPOption::UACPOption(UACPOption&& other) noexcept
    : type_(other.type_), value_(std::move(other.value_)),
      is_string_(other.is_string_), is_int_(other.is_int_) {
}

UACPOption& UACPOption::operator=(const UACPOption& other) {
    if (this != &other) {
        type_ = other.type_;
        value_ = other.value_;
        is_string_ = other.is_string_;
        is_int_ = other.is_int_;
    }
    return *this;
}

UACPOption& UACPOption::operator=(UACPOption&& other) noexcept {
    if (this != &other) {
        type_ = other.type_;
        value_ = std::move(other.value_);
        is_string_ = other.is_string_;
        is_int_ = other.is_int_;
    }
    return *this;
}

std::string UACPOption::getStringValue() const {
    if (!is_string_) {
        throw std::runtime_error("Option value is not a string");
    }
    return std::string(value_.begin(), value_.end());
}

uint32_t UACPOption::getIntValue() const {
    if (!is_int_) {
        throw std::runtime_error("Option value is not an integer");
    }
    return unpackInt(value_, 0);
}

std::vector<uint8_t> UACPOption::pack() const {
    std::vector<uint8_t> result;
    
    // Type (1 byte)
    result.push_back(static_cast<uint8_t>(type_));
    
    // Length (1 byte for values up to 255 bytes)
    if (value_.size() > 255) {
        throw std::runtime_error("Option value too large");
    }
    result.push_back(static_cast<uint8_t>(value_.size()));
    
    // Value
    result.insert(result.end(), value_.begin(), value_.end());
    
    return result;
}

size_t UACPOption::unpack(const std::vector<uint8_t>& data, size_t offset, UACPOption& option) {
    if (data.size() < offset + 2) {
        throw std::runtime_error("Insufficient data for option header");
    }
    
    // Type (1 byte)
    UACPOptionType type = static_cast<UACPOptionType>(data[offset]);
    offset++;
    
    // Length (1 byte)
    uint8_t length = data[offset];
    offset++;
    
    // Check if we have enough data for the value
    if (data.size() < offset + length) {
        throw std::runtime_error("Insufficient data for option value");
    }
    
    // Value
    std::vector<uint8_t> value(data.begin() + offset, data.begin() + offset + length);
    offset += length;
    
    // Create option - try to detect if it's an integer or string
    if (length == 4) {
        // Try to create as integer first
        try {
            option = UACPOption(type, unpackInt(value, 0));
        } catch (...) {
            // If that fails, create as string
            option = UACPOption(type, std::string(value.begin(), value.end()));
        }
    } else {
        // Create as string for non-4-byte values
        option = UACPOption(type, std::string(value.begin(), value.end()));
    }
    
    return offset;
}

size_t UACPOption::getPackedSize() const {
    return 2 + value_.size(); // Type (1) + Length (1) + Value
}

std::vector<uint8_t> UACPOption::packInt(uint32_t value) {
    std::vector<uint8_t> result(4);
    result[0] = (value >> 24) & 0xFF;
    result[1] = (value >> 16) & 0xFF;
    result[2] = (value >> 8) & 0xFF;
    result[3] = value & 0xFF;
    return result;
}

uint32_t UACPOption::unpackInt(const std::vector<uint8_t>& data, size_t offset) {
    if (data.size() < offset + 4) {
        throw std::runtime_error("Insufficient data for integer value");
    }
    
    uint32_t value = 0;
    value |= (static_cast<uint32_t>(data[offset]) << 24);
    value |= (static_cast<uint32_t>(data[offset + 1]) << 16);
    value |= (static_cast<uint32_t>(data[offset + 2]) << 8);
    value |= static_cast<uint32_t>(data[offset + 3]);
    
    return value;
}

} // namespace miuacp
