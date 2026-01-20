/**
 * @file agent.cpp
 * @brief µACP Agent Implementation (Stub)
 * 
 * This file provides stub implementations for the UACPAgent class.
 * Full implementation is pending.
 */

#include "miuacp/agent.h"
#include <stdexcept>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <random>

namespace miuacp {

// Constructor
UACPAgent::UACPAgent(const std::string& agent_id, const std::string& name,
                     const std::string& host, int port)
    : agent_info_(agent_id.empty() ? generateAgentId() : agent_id, name),
      running_(false) {
    client_ = std::make_unique<UACPClient>();
    server_ = std::make_unique<UACPServer>(host, port);
    registerDefaultHandlers();
}

// Destructor
UACPAgent::~UACPAgent() {
    stop();
}

bool UACPAgent::start() {
    if (running_) return true;
    
    bool server_started = server_->start();
    if (server_started) {
        client_->start();
        running_ = true;
    }
    return server_started;
}

void UACPAgent::stop() {
    if (!running_) return;
    
    client_->stop();
    server_->stop();
    running_ = false;
}

bool UACPAgent::isRunning() const {
    return running_;
}

std::string UACPAgent::getAddress() const {
    return server_->getAddress();
}

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

void UACPAgent::addTopicHandler(const std::string& topic, TopicHandler handler) {
    std::lock_guard<std::mutex> lock(topic_handlers_mutex_);
    topic_handlers_[topic] = handler;
}

bool UACPAgent::removeTopicHandler(const std::string& topic) {
    std::lock_guard<std::mutex> lock(topic_handlers_mutex_);
    return topic_handlers_.erase(topic) > 0;
}

bool UACPAgent::canHandleTopic(const std::string& topic) const {
    std::lock_guard<std::mutex> lock(topic_handlers_mutex_);
    for (const auto& [pattern, handler] : topic_handlers_) {
        if (topicMatches(pattern, topic)) {
            return true;
        }
    }
    return false;
}

UACPMessage UACPAgent::sendMessage(const std::string& host, int port, const UACPMessage& message) {
    return client_->sendMessage(host, port, message);
}

std::future<UACPMessage> UACPAgent::sendMessageAsync(const std::string& host, int port, const UACPMessage& message) {
    return client_->sendMessageAsync(host, port, message);
}

bool UACPAgent::ping(const std::string& host, int port) {
    return client_->ping(host, port);
}

bool UACPAgent::tell(const std::string& host, int port, const std::vector<uint8_t>& payload,
                     const std::string& topic, uint8_t qos) {
    return client_->tell(host, port, payload, topic, qos);
}

bool UACPAgent::tell(const std::string& host, int port, const std::string& payload,
                     const std::string& topic, uint8_t qos) {
    return client_->tell(host, port, payload, topic, qos);
}

UACPMessage UACPAgent::ask(const std::string& host, int port, const std::vector<uint8_t>& payload,
                           const std::string& topic, uint8_t qos, std::chrono::milliseconds timeout) {
    return client_->ask(host, port, payload, topic, qos, timeout);
}

UACPMessage UACPAgent::ask(const std::string& host, int port, const std::string& payload,
                           const std::string& topic, uint8_t qos, std::chrono::milliseconds timeout) {
    return client_->ask(host, port, payload, topic, qos, timeout);
}

bool UACPAgent::observe(const std::string& host, int port, const std::vector<uint8_t>& payload,
                        const std::string& topic, uint8_t qos) {
    return client_->observe(host, port, payload, topic, qos);
}

bool UACPAgent::observe(const std::string& host, int port, const std::string& payload,
                        const std::string& topic, uint8_t qos) {
    return client_->observe(host, port, payload, topic, qos);
}

int UACPAgent::broadcastToTopic(const std::string& topic, const UACPMessage& message) {
    return server_->broadcastToTopic(topic, message);
}

int UACPAgent::broadcastToTopic(const std::string& topic, const std::vector<uint8_t>& payload, uint8_t qos) {
    UACPMessage message = protocol_.createTell(payload, topic, 0, qos);
    return broadcastToTopic(topic, message);
}

int UACPAgent::broadcastToTopic(const std::string& topic, const std::string& payload, uint8_t qos) {
    UACPMessage message = protocol_.createTell(payload, topic, 0, qos);
    return broadcastToTopic(topic, message);
}

std::map<std::string, uint64_t> UACPAgent::getStatistics() const {
    auto client_stats = client_->getStatistics();
    auto server_stats = server_->getStatistics();
    
    std::map<std::string, uint64_t> combined;
    for (const auto& [key, value] : client_stats) {
        combined["client." + key] = value;
    }
    for (const auto& [key, value] : server_stats) {
        combined["server." + key] = value;
    }
    return combined;
}

std::map<std::string, uint64_t> UACPAgent::getClientStatistics() const {
    return client_->getStatistics();
}

std::map<std::string, uint64_t> UACPAgent::getServerStatistics() const {
    return server_->getStatistics();
}

void UACPAgent::registerDefaultHandlers() {
    server_->addMessageHandler(UACPVerb::PING, 
        [this](const UACPMessage& msg, const std::string& host, int port) {
            return handlePing(msg, host, port);
        });
    server_->addMessageHandler(UACPVerb::TELL,
        [this](const UACPMessage& msg, const std::string& host, int port) {
            return handleTell(msg, host, port);
        });
    server_->addMessageHandler(UACPVerb::ASK,
        [this](const UACPMessage& msg, const std::string& host, int port) {
            return handleAsk(msg, host, port);
        });
    server_->addMessageHandler(UACPVerb::OBSERVE,
        [this](const UACPMessage& msg, const std::string& host, int port) {
            return handleObserve(msg, host, port);
        });
}

UACPMessage UACPAgent::handlePing(const UACPMessage& message, const std::string& /*client_host*/, int /*client_port*/) {
    return message.createResponse(StatusCode::SUCCESS, "pong");
}

UACPMessage UACPAgent::handleTell(const UACPMessage& message, const std::string& client_host, int client_port) {
    auto handler = findTopicHandler(message.getTopicPath());
    if (handler) {
        return (*handler)(message, client_host, client_port);
    }
    return message.createResponse(StatusCode::SUCCESS);
}

UACPMessage UACPAgent::handleAsk(const UACPMessage& message, const std::string& client_host, int client_port) {
    auto handler = findTopicHandler(message.getTopicPath());
    if (handler) {
        return (*handler)(message, client_host, client_port);
    }
    return message.createResponse(StatusCode::NOT_FOUND, "No handler for topic");
}

UACPMessage UACPAgent::handleObserve(const UACPMessage& message, const std::string& /*client_host*/, int /*client_port*/) {
    return message.createResponse(StatusCode::SUCCESS);
}

TopicHandler* UACPAgent::findTopicHandler(const std::string& topic) {
    std::lock_guard<std::mutex> lock(topic_handlers_mutex_);
    
    // Exact match first
    auto it = topic_handlers_.find(topic);
    if (it != topic_handlers_.end()) {
        return &(it->second);
    }
    
    // Try pattern matching
    for (auto& [pattern, handler] : topic_handlers_) {
        if (topicMatches(pattern, topic)) {
            return &handler;
        }
    }
    
    return nullptr;
}

bool UACPAgent::topicMatches(const std::string& pattern, const std::string& topic) const {
    // Simple wildcard matching: # matches any suffix, + matches one level
    if (pattern == topic) return true;
    if (pattern == "#") return true;
    
    // Handle trailing # wildcard
    if (pattern.size() > 1 && pattern.back() == '#') {
        std::string prefix = pattern.substr(0, pattern.size() - 1);
        return topic.substr(0, prefix.size()) == prefix;
    }
    
    return false;
}

std::string UACPAgent::generateAgentId() {
    auto now = std::chrono::high_resolution_clock::now();
    auto seed = now.time_since_epoch().count();
    std::mt19937 rng(static_cast<unsigned int>(seed));
    std::uniform_int_distribution<uint32_t> dist(0, 0xFFFFFFFF);
    
    std::ostringstream oss;
    oss << "agent-" << std::hex << std::setfill('0') << std::setw(8) << dist(rng);
    return oss.str();
}

} // namespace miuacp
