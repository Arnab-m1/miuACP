/**
 * @file enums.h
 * @brief µACP Protocol Enums and Constants
 * 
 * This file defines all the core enums and constants used in the µACP protocol,
 * including verbs, option types, content types, and other protocol constants.
 * 
 * @author Arnab
 * @version 1.0.0
 * @license MIT
 */

#pragma once

#include <cstdint>
#include <cstddef>

namespace miuacp {

/**
 * @brief µACP protocol verbs (speech acts)
 * 
 * These verbs define the semantic meaning of messages in the µACP protocol.
 * Each verb represents a different type of communication pattern.
 */
enum class UACPVerb : uint8_t {
    PING = 0,      ///< Liveness check / clock hint
    TELL = 1,      ///< Inform (pub/sub)
    ASK = 2,       ///< Request/response (RPC)
    OBSERVE = 3    ///< Subscription to future informs
};

/**
 * @brief µACP TLV option types
 * 
 * These define the types of options that can be included in µACP messages
 * using the Type-Length-Value (TLV) format.
 */
enum class UACPOptionType : uint8_t {
    CONVERSATION_ID = 0x01,    ///< 8-16B: multi-turn task correlation
    CORRELATION_ID = 0x02,     ///< 3B: pair ASK with reply
    TOPIC_PATH = 0x03,         ///< UTF-8 string (e.g., "lab/arm/plan")
    CONTENT_TYPE = 0x04,       ///< small int: CBOR=0, JSON=1, Protobuf=2, Text=3
    ETAG = 0x05,               ///< cache validator
    MAX_AGE = 0x06,            ///< seconds (uint)
    BLOCK = 0x07,              ///< blockwise transfer descriptor
    AUTH = 0x08,               ///< short token id (pairs with COSE/DTLS)
    PRIORITY = 0x09            ///< 0-7 scheduling hint
};

/**
 * @brief µACP content types
 * 
 * These define the serialization format used for message payloads.
 */
enum class UACPContentType : uint8_t {
    CBOR = 0,      ///< CBOR (default)
    JSON = 1,      ///< JSON
    PROTOBUF = 2,  ///< Protocol Buffers
    TEXT = 3       ///< Plain text
};

/**
 * @brief QoS (Quality of Service) levels
 * 
 * These define the delivery guarantees for messages.
 */
enum class QoSLevel : uint8_t {
    AT_MOST_ONCE = 0,    ///< Fire and forget
    AT_LEAST_ONCE = 1,   ///< Acknowledged delivery
    EXACTLY_ONCE = 2     ///< Exactly once delivery
};

/**
 * @brief Protocol constants
 */
namespace Constants {
    constexpr uint8_t PROTOCOL_VERSION = 1;        ///< Current protocol version
    constexpr size_t HEADER_SIZE = 8;              ///< Fixed header size in bytes
    constexpr size_t MAX_MESSAGE_SIZE = 65535;     ///< Maximum message size
    constexpr size_t MAX_OPTIONS = 255;            ///< Maximum number of options
    constexpr size_t MAX_TOPIC_LENGTH = 1024;      ///< Maximum topic path length
    constexpr size_t MAX_PAYLOAD_SIZE = 65527;     ///< Maximum payload size (65535 - 8)
    constexpr uint32_t MAX_MESSAGE_ID = 0xFFFFFF;  ///< Maximum message ID (24 bits)
}

/**
 * @brief Status codes for responses
 */
enum class StatusCode : uint8_t {
    SUCCESS = 0x00,                 ///< Success (OK)
    CREATED = 0x01,                 ///< Resource created successfully
    ACCEPTED = 0x02,                ///< Request accepted for processing
    NO_CONTENT = 0x03,              ///< Request completed, no content to return
    RESET_CONTENT = 0x04,           ///< Request completed, content reset
    BAD_REQUEST = 0x40,             ///< Bad request
    UNAUTHORIZED = 0x41,            ///< Unauthorized
    FORBIDDEN = 0x42,               ///< Forbidden
    NOT_FOUND = 0x43,               ///< Not found
    METHOD_NOT_ALLOWED = 0x44,      ///< Method not allowed
    REQUEST_TIMEOUT = 0x46,         ///< Request timeout
    CONFLICT = 0x47,                ///< Conflict
    PAYLOAD_TOO_LARGE = 0x4A,       ///< Payload too large
    INTERNAL_ERROR = 0x80,          ///< Internal server error
    NOT_IMPLEMENTED = 0x81,         ///< Not implemented
    BAD_GATEWAY = 0x82,             ///< Bad gateway
    SERVICE_UNAVAILABLE = 0x83,     ///< Service unavailable
    GATEWAY_TIMEOUT = 0x84          ///< Gateway timeout
};

} // namespace miuacp
