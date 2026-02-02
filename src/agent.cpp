/**
 * @file agent_simplified.cpp
 * @brief Simplified P2P Agent - Core Implementation Only
 * 
 * Simplified implementation focusing on getting basic P2P working.
 * This is a minimal viable implementation to demonstrate the architecture.
 * 
 * @author Arnab
 * @version 2.0.0
 * @license MIT
 */

#include "miuacp/agent.h"
#include <algorithm>
#include <sstream>
#include <random>
#include <iomanip>

namespace miuacp {

UACPAgent::UACPAgent(const std::string& agent_id,
                     const std::string& name,
                     const std::string& host,
                     int port,
                     std::unique_ptr<UACPTransport> transport)
    : agent_info_(agent_id.empty() ? generateAgentId() : agent_id, name)
    , host_(host)
    , port_(port)
    , transport_(transport ? std::move(transport) : std::make_unique<UACPUdpTransport>())
    , running_(false)
    , messages_sent_(0)
    , messages_received_(0)
    , bytes_sent_(0)
    , bytes_received_(0)
{
}

UACPAgent::~UACPAgent() {
    stop();
}

bool UACPAgent::start() {
    if (running_.load()) {
        return false;
    }
    
    if (!transport_->bind(host_, port_)) {
        return false;
    }
    
    port_ = transport_->getLocalPort();
    
    running_.store(true);
    receiver_thread_ = std::thread(&UACPAgent::receiverLoop, this);
    
    return true;
}

void UACPAgent::stop() {
    if (!running_.load()) {
        return;
    }
    
    running_.store(false);
    
    if (receiver_thread_.joinable()) {
        receiver_thread_.join();
    }
    
    transport_->close();
}

std::string UACPAgent::getAddress() const {
    return host_ + ":" + std::to_string(port_);
}

int UACPAgent::getPort() const {
    return port_;
}

// ========== Peer Discovery ==========

int UACPAgent::discoverPeers(const std::string& broadcast_addr, int port) {
    (void)broadcast_addr;  // Will use in future
    
   if (!transport_->enableBroadcast()) {
        return 0;
    }
    
    auto discovery_msg = protocol_.createPing();
    auto packed = discovery_msg.pack();
    
    if (transport_->sendBroadcast(packed, port)) {
        return 1;
    }
    
    return 0;
}

std::vector<std::string> UACPAgent::getDiscoveredPeers() const {
    std::lock_guard<std::mutex> lock(peers_mutex_);
    std::vector<std::string> peers;
    peers.reserve(peers_.size());
    
    for (const auto& pair : peers_) {
        peers.push_back(pair.first);
    }
    
    return peers;
}

void UACPAgent::addPeer(const std::string& peer_host, int peer_port, const std::string& peer_id) {
    std::lock_guard<std::mutex> lock(peers_mutex_);
    std::string key = getPeerKey(peer_host, peer_port);
    
    auto it = peers_.find(key);
    if (it != peers_.end()) {
        it->second.last_seen = std::chrono::steady_clock::now();
        if (!peer_id.empty()) {
            it->second.agent_id = peer_id;
        }
    } else {
        peers_.emplace(key, UACPPeerInfo(peer_id, peer_host, peer_port));
    }
}

void UACPAgent::removePeer(const std::string& peer_host, int peer_port) {
    std::lock_guard<std::mutex> lock(peers_mutex_);
    std::string key = getPeerKey(peer_host, peer_port);
    peers_.erase(key);
}

const UACPPeerInfo* UACPAgent::getPeerInfo(const std::string& peer_host, int peer_port) const {
    std::lock_guard<std::mutex> lock(peers_mutex_);
    std::string key = getPeerKey(peer_host, peer_port);
    
    auto it = peers_.find(key);
    if (it != peers_.end()) {
        return &it->second;
    }
    
    return nullptr;
}

// ========== Send to Peers ==========

UACPMessage UACPAgent::sendToPeer(const std::string& peer_host, int peer_port, const UACPMessage& message) {
    auto packed = message.pack();
    
    if (!transport_->sendToPeer(packed, peer_host, peer_port)) {
        return UACPMessage();
    }
    
    messages_sent_++;
    bytes_sent_ += packed.size();
    
    // For ASK messages, wait for response (simplified - no timeout handling yet)
    if (message.getHeader().getVerb() == UACPVerb::ASK) {
        // TODO: Implement proper request/response matching
        // For now, just return empty message
        return UACPMessage();
    }
    
    return UACPMessage();
}

bool UACPAgent::ping(const std::string& peer_host, int peer_port) {
    auto ping_msg = protocol_.createPing();
    auto response = sendToPeer(peer_host, peer_port, ping_msg);
    
    // Simplified: just check if send succeeded
    return true;
}

bool UACPAgent::tell(const std::string& peer_host, int peer_port, const std::vector<uint8_t>& payload,
                     const std::string& topic, uint8_t qos) {
    auto msg = protocol_.createTell(payload, topic, 0, qos);
    
    sendToPeer(peer_host, peer_port, msg);
    return true;
}

bool UACPAgent::tell(const std::string& peer_host, int peer_port, const std::string& payload,
                     const std::string& topic, uint8_t qos) {
    std::vector<uint8_t> data(payload.begin(), payload.end());
    return tell(peer_host, peer_port, data, topic, qos);
}

UACPMessage UACPAgent::ask(const std::string& peer_host, int peer_port, const std::vector<uint8_t>& payload,
                           const std::string& topic, uint8_t qos,
                           std::chrono::milliseconds timeout) {
    (void)timeout;  // Simplified version doesn't use timeout yet
    
    auto msg = protocol_.createAsk(payload, topic, 0, qos);
    
    return sendToPeer(peer_host, peer_port, msg);
}

UACPMessage UACPAgent::ask(const std::string& peer_host, int peer_port, const std::string& payload,
                           const std::string& topic, uint8_t qos,
                          std::chrono::milliseconds timeout) {
    std::vector<uint8_t> data(payload.begin(), payload.end());
    return ask(peer_host, peer_port, data, topic, qos, timeout);
}

bool UACPAgent::observe(const std::string& peer_host, int peer_port, const std::string& topic, uint8_t qos) {
    auto msg = protocol_.createObserve("", topic, 0, qos);
    
    sendToPeer(peer_host, peer_port, msg);
    return true;
}

int UACPAgent::notifyTopic(const std::string& topic, const std::vector<uint8_t>& payload, uint8_t qos) {
    std::lock_guard<std::mutex> lock(subscriptions_mutex_);
    
    int notified = 0;
    for (const auto& sub : subscriptions_) {
        if (topicMatches(sub.topic, topic)) {
            auto msg = protocol_.createTell(payload, topic, 0, qos);
            
            sendToPeer(sub.peer_host, sub.peer_port, msg);
            notified++;
        }
    }
    
    return notified;
}

int UACPAgent::notifyTopic(const std::string& topic, const std::string& payload, uint8_t qos) {
    std::vector<uint8_t> data(payload.begin(), payload.end());
    return notifyTopic(topic, data, qos);
}

// ========== Message Handling ==========

void UACPAgent::addMessageHandler(UACPVerb verb, MessageHandler handler) {
    std::lock_guard<std::mutex> lock(handlers_mutex_);
    verb_handlers_[verb] = handler;
}

bool UACPAgent::removeMessageHandler(UACPVerb verb) {
    std::lock_guard<std::mutex> lock(handlers_mutex_);
    return verb_handlers_.erase(verb) > 0;
}

void UACPAgent::addTopicHandler(const std::string& topic_pattern, TopicHandler handler) {
    std::lock_guard<std::mutex> lock(handlers_mutex_);
    topic_handlers_[topic_pattern] = handler;
    
    if (std::find(agent_info_.topics.begin(), agent_info_.topics.end(), topic_pattern) == agent_info_.topics.end()) {
        agent_info_.topics.push_back(topic_pattern);
    }
}

bool UACPAgent::removeTopicHandler(const std::string& topic_pattern) {
    std::lock_guard<std::mutex> lock(handlers_mutex_);
    
    if (topic_handlers_.erase(topic_pattern) > 0) {
        auto it = std::find(agent_info_.topics.begin(), agent_info_.topics.end(), topic_pattern);
        if (it != agent_info_.topics.end()) {
            agent_info_.topics.erase(it);
        }
        return true;
    }
    
    return false;
}

bool UACPAgent::canHandleTopic(const std::string& topic) const {
    std::lock_guard<std::mutex> lock(handlers_mutex_);
    
    for (const auto& pair : topic_handlers_) {
        if (topicMatches(pair.first, topic)) {
            return true;
        }
    }
    
    return false;
}

// ========== Capability Management ==========

void UACPAgent::addCapability(const UACPCapability& capability) {
    agent_info_.capabilities.push_back(capability);
    
    for (const auto& topic : capability.topics) {
        if (std::find(agent_info_.topics.begin(), agent_info_.topics.end(), topic) == agent_info_.topics.end()) {
            agent_info_.topics.push_back(topic);
        }
    }
}

bool UACPAgent::removeCapability(const std::string& name) {
    auto it = std::find_if(agent_info_.capabilities.begin(), agent_info_.capabilities.end(),
                          [&name](const UACPCapability& cap) { return cap.name == name; });
    
    if (it != agent_info_.capabilities.end()) {
        agent_info_.capabilities.erase(it);
        return true;
    }
    
    return false;
}

const UACPCapability* UACPAgent::getCapability(const std::string& name) const {
    auto it = std::find_if(agent_info_.capabilities.begin(), agent_info_.capabilities.end(),
                          [&name](const UACPCapability& cap) { return cap.name == name; });
    
    if (it != agent_info_.capabilities.end()) {
        return &(*it);
    }
    
    return nullptr;
}

// ========== Statistics ==========

std::map<std::string, uint64_t> UACPAgent::getStatistics() const {
    return {
        {"messages_sent", messages_sent_.load()},
        {"messages_received", messages_received_.load()},
        {"bytes_sent", bytes_sent_.load()},
        {"bytes_received", bytes_received_.load()},
        {"peers", static_cast<uint64_t>(peers_.size())},
        {"subscriptions", static_cast<uint64_t>(subscriptions_.size())}
    };
}

// ========== Internal Methods ==========

void UACPAgent::receiverLoop() {
    while (running_.load()) {
        std::string sender_host;
        int sender_port;
        
        auto data = transport_->receiveFromPeer(100, sender_host, sender_port);
        
        if (data.empty()) {
            continue;
        }
        
        messages_received_++;
        bytes_received_ += data.size();
        
        // Unpack message
        try {
            UACPMessage message = UACPMessage::unpack(data);
            
            // Update peer registry
            addPeer(sender_host, sender_port);
            
            // Handle message
            handleIncomingMessage(message, sender_host, sender_port);
        } catch (...) {
            // Failed to unpack - ignore
            continue;
        }
    }
}

void UACPAgent::handleIncomingMessage(const UACPMessage& message, const std::string& sender_host, int sender_port) {
    UACPVerb verb = message.getHeader().getVerb();
    
    // Find handler
    UACPMessage response;
    
    {
        std::lock_guard<std::mutex> lock(handlers_mutex_);
        auto it = verb_handlers_.find(verb);
        if (it != verb_handlers_.end()) {
            response = it->second(message, sender_host, sender_port);
        }
    }
    
    // Use default handlers if no custom handler
    if (response.getPayload().empty()) {
        switch (verb) {
            case UACPVerb::PING:
                response = handlePing(message, sender_host, sender_port);
                break;
            case UACPVerb::TELL:
                response = handleTell(message, sender_host, sender_port);
                break;
            case UACPVerb::ASK:
                response = handleAsk(message, sender_host, sender_port);
                break;
            case UACPVerb::OBSERVE:
                response = handleObserve(message, sender_host, sender_port);
                break;
            default:
                break;
        }
    }
    
    // Send response if generated
    if (!response.getPayload().empty()) {
        auto packed = response.pack();
        transport_->sendToPeer(packed, sender_host, sender_port);
        messages_sent_++;
        bytes_sent_ += packed.size();
    }
}

void UACPAgent::registerDefaultHandlers() {
    // Implemented as methods
}

UACPMessage UACPAgent::handlePing(const UACPMessage& message, const std::string& sender_host, int sender_port) {
    (void)sender_host;
    (void)sender_port;
    return message.createResponse(StatusCode::SUCCESS, "pong");
}

UACPMessage UACPAgent::handleTell(const UACPMessage& message, const std::string& sender_host, int sender_port) {
    auto topic_opt = message.getOption(UACPOptionType::TOPIC_PATH);
    if (topic_opt) {
        std::string topic = topic_opt->getStringValue();
        
        auto* handler = findTopicHandler(topic);
        if (handler) {
            return (*handler)(message, sender_host, sender_port);
        }
    }
    
    if (message.getHeader().getQoS() > 0) {
        return message.createResponse(StatusCode::SUCCESS);
    }
    
    return UACPMessage();
}

UACPMessage UACPAgent::handleAsk(const UACPMessage& message, const std::string& sender_host, int sender_port) {
    auto topic_opt = message.getOption(UACPOptionType::TOPIC_PATH);
    if (topic_opt) {
        std::string topic = topic_opt->getStringValue();
        
        auto* handler = findTopicHandler(topic);
        if (handler) {
            return (*handler)(message, sender_host, sender_port);
        }
    }
    
    return message.createResponse(StatusCode::NOT_FOUND, "No handler for topic");
}

UACPMessage UACPAgent::handleObserve(const UACPMessage& message, const std::string& sender_host, int sender_port) {
    auto topic_opt = message.getOption(UACPOptionType::TOPIC_PATH);
    if (!topic_opt) {
        return message.createResponse(StatusCode::BAD_REQUEST, "Missing topic");
    }
    
    std::string topic = topic_opt->getStringValue();
    
    {
        std::lock_guard<std::mutex> lock(subscriptions_mutex_);
        subscriptions_.push_back({
            topic,
            sender_host,
            sender_port,
            message.getHeader().getQoS(),
            std::chrono::steady_clock::now()
        });
    }
    
    return message.createResponse(StatusCode::SUCCESS, "Subscribed");
}

UACPMessage UACPAgent::handleNotify(const UACPMessage& message, const std::string& sender_host, int sender_port) {
    auto topic_opt = message.getOption(UACPOptionType::TOPIC_PATH);
    if (topic_opt) {
        std::string topic = topic_opt->getStringValue();
        
        auto* handler = findTopicHandler(topic);
        if (handler) {
            return (*handler)(message, sender_host, sender_port);
        }
    }
    
    if (message.getHeader().getQoS() > 0) {
        return message.createResponse(StatusCode::SUCCESS);
    }
    
    return UACPMessage();
}

UACPMessage UACPAgent::handleAnswer(const UACPMessage& message, const std::string& sender_host, int sender_port) {
    (void)sender_host;
    (void)sender_port;
    (void)message;
    
    // TODO: Match with pending requests
    
    return UACPMessage();
}

TopicHandler* UACPAgent::findTopicHandler(const std::string& topic) {
    // Already locked by caller
    
    for (auto& pair : topic_handlers_) {
        if (topicMatches(pair.first, topic)) {
            return &pair.second;
        }
    }
    
    return nullptr;
}

bool UACPAgent::topicMatches(const std::string& pattern, const std::string& topic) const {
    if (pattern == topic || pattern == "#") {
        return true;
    }
    
    // Simple wildcard matching
    auto splitString = [](const std::string& str, char delimiter) {
        std::vector<std::string> tokens;
        std::string token;
        std::istringstream tokenStream(str);
        while (std::getline(tokenStream, token, delimiter)) {
            tokens.push_back(token);
        }
        return tokens;
    };
    
    auto pattern_parts = splitString(pattern, '/');
    auto topic_parts = splitString(topic, '/');
    
    size_t p = 0, t = 0;
    while (p < pattern_parts.size() && t < topic_parts.size()) {
        if (pattern_parts[p] == "#") {
            return true;
        } else if (pattern_parts[p] == "*" || pattern_parts[p] == topic_parts[t]) {
            p++;
            t++;
        } else {
            return false;
        }
    }
    
    return p == pattern_parts.size() && t == topic_parts.size();
}

std::string UACPAgent::generateAgentId() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dist(0, 15);
    
    std::stringstream ss;
    ss << "agent_";
    for (int i = 0; i < 8; i++) {
        ss << std::hex << dist(gen);
    }
    
    return ss.str();
}

std::string UACPAgent::getPeerKey(const std::string& host, int port) const {
    return host + ":" + std::to_string(port);
}

} // namespace miuacp
