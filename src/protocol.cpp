/**
 * @file protocol.cpp
 * @brief µACP Protocol Core Implementation
 */

#include "miuacp/protocol.h"
#include <chrono>
#include <random>
#include <stdexcept>

namespace miuacp {

UACPProtocol::UACPProtocol() {
    initializeRNG();
}

UACPMessage UACPProtocol::createMessage(UACPVerb verb, 
                                        const std::vector<uint8_t>& payload,
                                        uint32_t msg_id,
                                        uint8_t qos,
                                        uint8_t code) const {
    if (msg_id == 0) {
        msg_id = generateMessageId();
    }
    
    UACPMessage message(verb, payload, msg_id, qos, code);
    return message;
}

UACPMessage UACPProtocol::createMessage(UACPVerb verb, 
                                        const std::string& payload,
                                        uint32_t msg_id,
                                        uint8_t qos,
                                        uint8_t code) const {
    std::vector<uint8_t> payload_bytes(payload.begin(), payload.end());
    return createMessage(verb, payload_bytes, msg_id, qos, code);
}

UACPMessage UACPProtocol::createPing(uint32_t msg_id) const {
    return createMessage(UACPVerb::PING, std::vector<uint8_t>(), msg_id, 0, 0);
}

UACPMessage UACPProtocol::createTell(const std::vector<uint8_t>& payload,
                                     const std::string& topic,
                                     uint32_t msg_id,
                                     uint8_t qos) const {
    UACPMessage message = createMessage(UACPVerb::TELL, payload, msg_id, qos, 0);
    if (!topic.empty()) {
        message.setTopicPath(topic);
    }
    return message;
}

UACPMessage UACPProtocol::createTell(const std::string& payload,
                                     const std::string& topic,
                                     uint32_t msg_id,
                                     uint8_t qos) const {
    std::vector<uint8_t> payload_bytes(payload.begin(), payload.end());
    return createTell(payload_bytes, topic, msg_id, qos);
}

UACPMessage UACPProtocol::createAsk(const std::vector<uint8_t>& payload,
                                    const std::string& topic,
                                    uint32_t msg_id,
                                    uint8_t qos) const {
    UACPMessage message = createMessage(UACPVerb::ASK, payload, msg_id, qos, 0);
    if (!topic.empty()) {
        message.setTopicPath(topic);
    }
    return message;
}

UACPMessage UACPProtocol::createAsk(const std::string& payload,
                                    const std::string& topic,
                                    uint32_t msg_id,
                                    uint8_t qos) const {
    std::vector<uint8_t> payload_bytes(payload.begin(), payload.end());
    return createAsk(payload_bytes, topic, msg_id, qos);
}

UACPMessage UACPProtocol::createObserve(const std::vector<uint8_t>& payload,
                                        const std::string& topic,
                                        uint32_t msg_id,
                                        uint8_t qos) const {
    if (topic.empty()) {
        throw std::runtime_error("Topic is required for OBSERVE message");
    }
    
    UACPMessage message = createMessage(UACPVerb::OBSERVE, payload, msg_id, qos, 0);
    message.setTopicPath(topic);
    return message;
}

UACPMessage UACPProtocol::createObserve(const std::string& payload,
                                        const std::string& topic,
                                        uint32_t msg_id,
                                        uint8_t qos) const {
    std::vector<uint8_t> payload_bytes(payload.begin(), payload.end());
    return createObserve(payload_bytes, topic, msg_id, qos);
}

uint32_t UACPProtocol::generateMessageId() const {
    std::lock_guard<std::mutex> lock(rng_mutex_);
    return msg_id_dist_(rng_);
}

bool UACPProtocol::validateMessage(const UACPMessage& message) const {
    return message.isValid();
}

void UACPProtocol::initializeRNG() {
    auto seed = std::chrono::high_resolution_clock::now().time_since_epoch().count();
    rng_.seed(static_cast<unsigned int>(seed));
    msg_id_dist_ = std::uniform_int_distribution<uint32_t>(1, Constants::MAX_MESSAGE_ID);
}

} // namespace miuacp
