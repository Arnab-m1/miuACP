/**
 * @file header.cpp
 * @brief µACP Protocol Header Implementation
 */

#include "miuacp/header.h"
#include <stdexcept>
#include <cstring>

namespace miuacp {

UACPHeader::UACPHeader()
    : version_(Constants::PROTOCOL_VERSION), verb_(UACPVerb::PING), 
      qos_(0), code_(0), msg_id_(0), opts_count_(0) {
}

UACPHeader::UACPHeader(uint8_t version, UACPVerb verb, uint8_t qos, 
                       uint8_t code, uint32_t msg_id, uint8_t opts_count)
    : version_(version), verb_(verb), qos_(qos), 
      code_(code), msg_id_(msg_id), opts_count_(opts_count) {
}

std::vector<uint8_t> UACPHeader::pack() const {
    std::vector<uint8_t> result(8);
    
    // Pack into 64 bits: VVTTQQCC MMMMMMMM MMMMMMMM MMMMMMMM OOOOOOOO
    uint64_t header = 0;
    header |= (static_cast<uint64_t>(version_ & 0x3) << 62);
    header |= (static_cast<uint64_t>(static_cast<uint8_t>(verb_) & 0x3) << 60);
    header |= (static_cast<uint64_t>(qos_ & 0x3) << 58);
    header |= (static_cast<uint64_t>(code_ & 0xFF) << 50);
    header |= (static_cast<uint64_t>(msg_id_ & 0xFFFFFF) << 26);
    header |= (static_cast<uint64_t>(opts_count_ & 0xFF) << 18);
    
    // Convert to big-endian bytes
    result[0] = (header >> 56) & 0xFF;
    result[1] = (header >> 48) & 0xFF;
    result[2] = (header >> 40) & 0xFF;
    result[3] = (header >> 32) & 0xFF;
    result[4] = (header >> 24) & 0xFF;
    result[5] = (header >> 16) & 0xFF;
    result[6] = (header >> 8) & 0xFF;
    result[7] = header & 0xFF;
    
    return result;
}

UACPHeader UACPHeader::unpack(const std::vector<uint8_t>& data) {
    return unpack(data, 0);
}

UACPHeader UACPHeader::unpack(const std::vector<uint8_t>& data, size_t offset) {
    if (data.size() < offset + 8) {
        throw std::runtime_error("Insufficient data for header");
    }
    
    // Convert from big-endian bytes to 64-bit integer
    uint64_t header = 0;
    header |= (static_cast<uint64_t>(data[offset]) << 56);
    header |= (static_cast<uint64_t>(data[offset + 1]) << 48);
    header |= (static_cast<uint64_t>(data[offset + 2]) << 40);
    header |= (static_cast<uint64_t>(data[offset + 3]) << 32);
    header |= (static_cast<uint64_t>(data[offset + 4]) << 24);
    header |= (static_cast<uint64_t>(data[offset + 5]) << 16);
    header |= (static_cast<uint64_t>(data[offset + 6]) << 8);
    header |= static_cast<uint64_t>(data[offset + 7]);
    
    // Extract fields
    uint8_t version = (header >> 62) & 0x3;
    UACPVerb verb = static_cast<UACPVerb>((header >> 60) & 0x3);
    uint8_t qos = (header >> 58) & 0x3;
    uint8_t code = (header >> 50) & 0xFF;
    uint32_t msg_id = (header >> 26) & 0xFFFFFF;
    uint8_t opts_count = (header >> 18) & 0xFF;
    
    return UACPHeader(version, verb, qos, code, msg_id, opts_count);
}

bool UACPHeader::isValid() const {
    return isValidVersion(version_) && 
           isValidQoS(qos_) && 
           isValidMessageId(msg_id_);
}

UACPHeader UACPHeader::createResponse(const UACPHeader& request_header, StatusCode response_code) {
    return UACPHeader(
        request_header.version_,
        request_header.verb_,
        request_header.qos_,
        static_cast<uint8_t>(response_code),
        request_header.msg_id_,
        0  // Options count will be set when options are added
    );
}

bool UACPHeader::isValidVersion(uint8_t version) {
    return version <= Constants::PROTOCOL_VERSION;
}

bool UACPHeader::isValidQoS(uint8_t qos) {
    return qos <= 2; // QoS levels 0, 1, 2
}

bool UACPHeader::isValidMessageId(uint32_t msg_id) {
    return msg_id <= Constants::MAX_MESSAGE_ID;
}

} // namespace miuacp
