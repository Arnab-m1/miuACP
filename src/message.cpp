/**
 * @file message.cpp
 * @brief µACP Message Implementation
 */

#include "miuacp/message.h"
#include <stdexcept>
#include <algorithm>

namespace miuacp {

UACPMessage::UACPMessage() : header_(), is_response_(false) {
}

UACPMessage::UACPMessage(const UACPHeader& header) : header_(header), is_response_(false) {
}

UACPMessage::UACPMessage(UACPVerb verb, const std::vector<uint8_t>& payload, 
                         uint32_t msg_id, uint8_t qos, uint8_t code)
    : header_(Constants::PROTOCOL_VERSION, verb, qos, code, msg_id, 0),
      payload_(payload), is_response_(false) {
}

UACPMessage::UACPMessage(const UACPMessage& other)
    : header_(other.header_), options_(other.options_), payload_(other.payload_), is_response_(other.is_response_) {
}

UACPMessage::UACPMessage(UACPMessage&& other) noexcept
    : header_(std::move(other.header_)), 
      options_(std::move(other.options_)), 
      payload_(std::move(other.payload_)),
      is_response_(other.is_response_) {
}

UACPMessage& UACPMessage::operator=(const UACPMessage& other) {
    if (this != &other) {
        header_ = other.header_;
        options_ = other.options_;
        payload_ = other.payload_;
        is_response_ = other.is_response_;
    }
    return *this;
}

UACPMessage& UACPMessage::operator=(UACPMessage&& other) noexcept {
    if (this != &other) {
        header_ = std::move(other.header_);
        options_ = std::move(other.options_);
        payload_ = std::move(other.payload_);
        is_response_ = other.is_response_;
    }
    return *this;
}

void UACPMessage::addOption(const UACPOption& option) {
    // Remove existing option of same type
    removeOption(option.getType());
    
    // Add new option
    options_.push_back(option);
    updateOptionsCount();
}

void UACPMessage::addOption(UACPOptionType type, const std::string& value) {
    addOption(UACPOption(type, value));
}

void UACPMessage::addOption(UACPOptionType type, uint32_t value) {
    addOption(UACPOption(type, value));
}

void UACPMessage::addOption(UACPOptionType type, const std::vector<uint8_t>& value) {
    addOption(UACPOption(type, value));
}

const UACPOption* UACPMessage::getOption(UACPOptionType type) const {
    auto it = std::find_if(options_.begin(), options_.end(),
        [type](const UACPOption& opt) { return opt.getType() == type; });
    
    return (it != options_.end()) ? &(*it) : nullptr;
}

bool UACPMessage::removeOption(UACPOptionType type) {
    auto it = std::find_if(options_.begin(), options_.end(),
        [type](const UACPOption& opt) { return opt.getType() == type; });
    
    if (it != options_.end()) {
        options_.erase(it);
        updateOptionsCount();
        return true;
    }
    return false;
}

void UACPMessage::setPayload(const std::string& payload) {
    payload_ = std::vector<uint8_t>(payload.begin(), payload.end());
}

void UACPMessage::setPayload(const std::vector<uint8_t>& payload) {
    payload_ = payload;
}

std::string UACPMessage::getPayloadAsString() const {
    return std::string(payload_.begin(), payload_.end());
}

std::vector<uint8_t> UACPMessage::pack() const {
    if (!isValid()) {
        throw std::runtime_error("Invalid message");
    }
    
    std::vector<uint8_t> result;
    
    // Pack header
    auto header_bytes = header_.pack();
    result.insert(result.end(), header_bytes.begin(), header_bytes.end());
    
    // Pack options
    for (const auto& option : options_) {
        auto option_bytes = option.pack();
        result.insert(result.end(), option_bytes.begin(), option_bytes.end());
    }
    
    // Pack payload
    result.insert(result.end(), payload_.begin(), payload_.end());
    
    return result;
}

UACPMessage UACPMessage::unpack(const std::vector<uint8_t>& data) {
    return unpack(data, 0);
}

UACPMessage UACPMessage::unpack(const std::vector<uint8_t>& data, size_t offset) {
    if (data.size() < offset + UACPHeader::getSize()) {
        throw std::runtime_error("Insufficient data for message header");
    }
    
    // Unpack header
    UACPHeader header = UACPHeader::unpack(data, offset);
    offset += UACPHeader::getSize();
    
    UACPMessage message(header);
    
    // Unpack options
    for (uint8_t i = 0; i < header.getOptionsCount(); ++i) {
        UACPOption option;
        offset = UACPOption::unpack(data, offset, option);
        message.options_.push_back(option);
    }
    
    // Unpack payload
    if (offset < data.size()) {
        message.payload_ = std::vector<uint8_t>(data.begin() + offset, data.end());
    }
    
    return message;
}

size_t UACPMessage::getPackedSize() const {
    size_t size = UACPHeader::getSize();
    
    for (const auto& option : options_) {
        size += option.getPackedSize();
    }
    
    size += payload_.size();
    
    return size;
}

bool UACPMessage::isValid() const {
    return header_.isValid() && validateSize();
}

UACPMessage UACPMessage::createResponse(StatusCode response_code, 
                                        const std::vector<uint8_t>& response_payload) const {
    UACPHeader response_header = UACPHeader::createResponse(header_, response_code);
    UACPMessage response(response_header);
    response.setPayload(response_payload);
    response.is_response_ = true;
    return response;
}

UACPMessage UACPMessage::createResponse(StatusCode response_code, 
                                        const std::string& response_payload) const {
    return createResponse(response_code, std::vector<uint8_t>(response_payload.begin(), response_payload.end()));
}

bool UACPMessage::isRequest() const {
    return !is_response_;
}

bool UACPMessage::isResponse() const {
    return is_response_;
}

std::string UACPMessage::getTopicPath() const {
    const UACPOption* topic_opt = getOption(UACPOptionType::TOPIC_PATH);
    return topic_opt ? topic_opt->getStringValue() : "";
}

void UACPMessage::setTopicPath(const std::string& topic_path) {
    addOption(UACPOptionType::TOPIC_PATH, topic_path);
}

UACPContentType UACPMessage::getContentType() const {
    const UACPOption* content_type_opt = getOption(UACPOptionType::CONTENT_TYPE);
    if (content_type_opt) {
        return static_cast<UACPContentType>(content_type_opt->getIntValue());
    }
    return UACPContentType::CBOR; // Default
}

void UACPMessage::setContentType(UACPContentType content_type) {
    addOption(UACPOptionType::CONTENT_TYPE, static_cast<uint32_t>(content_type));
}

void UACPMessage::updateOptionsCount() {
    header_.setOptionsCount(static_cast<uint8_t>(options_.size()));
}

bool UACPMessage::validateSize() const {
    return getPackedSize() <= Constants::MAX_MESSAGE_SIZE;
}

} // namespace miuacp
