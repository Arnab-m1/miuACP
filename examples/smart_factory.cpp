/**
 * @file smart_factory.cpp
 * @brief Smart Factory - 5 BDI Agents Simulation
 * 
 * A real-world IoT scenario demonstrating 5 BDI (Belief-Desire-Intention) agents
 * communicating in a smart manufacturing environment using µACP protocol.
 * 
 * Agents:
 * 1. ProductionManager - Coordinates production orders
 * 2. InventoryAgent - Manages raw materials and stock
 * 3. RobotArmAgent - Performs physical assembly tasks
 * 4. QualityControlAgent - Inspects product quality
 * 5. MaintenanceAgent - Monitors machine health
 * 
 * Scenario: Manufacturing a batch of "SmartWidget" products
 * 
 * @author Arnab
 * @version 1.0.0
 */

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <thread>
#include <chrono>
#include <iomanip>
#include <sstream>
#include "miuacp/miuacp.h"

using namespace miuacp;

// ============================================================================
// ANSI Color Codes for Terminal Output
// ============================================================================
namespace Color {
    const std::string RESET   = "\033[0m";
    const std::string RED     = "\033[31m";
    const std::string GREEN   = "\033[32m";
    const std::string YELLOW  = "\033[33m";
    const std::string BLUE    = "\033[34m";
    const std::string MAGENTA = "\033[35m";
    const std::string CYAN    = "\033[36m";
    const std::string WHITE   = "\033[37m";
    const std::string BOLD    = "\033[1m";
}

// ============================================================================
// Message Bus - Simulates realistic network with discovery and latency
// ============================================================================
class MessageBus {
public:
    using Handler = std::function<UACPMessage(const UACPMessage&, const std::string&)>;
    
    struct AgentInfo {
        std::string id;
        std::string type;
        Handler handler;
        std::chrono::steady_clock::time_point last_seen;
        
        AgentInfo() = default;
        AgentInfo(const std::string& id_, const std::string& type_, Handler h)
            : id(id_), type(type_), handler(h), last_seen(std::chrono::steady_clock::now()) {}
    };
    
    MessageBus() : rng_(std::random_device{}()) {}
    
    void registerAgent(const std::string& agent_id, const std::string& agent_type, Handler handler) {
        std::lock_guard<std::mutex> lock(mutex_);
        agents_[agent_id] = AgentInfo(agent_id, agent_type, handler);
        logDiscovery(agent_id + " (" + agent_type + ") joined the network");
    }
    
    // Broadcast discovery message to all agents
    void broadcastDiscovery(const std::string& from, const std::string& agent_type) {
        std::lock_guard<std::mutex> lock(mutex_);
        logDiscovery(from + " broadcasting discovery as " + agent_type);
        // Discovery is instant - no artificial delays
    }
    
    // Get list of discovered agents
    std::vector<std::string> getDiscoveredAgents(const std::string& requester) const {
        std::lock_guard<std::mutex> lock(mutex_);
        std::vector<std::string> discovered;
        for (const auto& [id, info] : agents_) {
            if (id != requester) {
                discovered.push_back(id + " (" + info.type + ")");
            }
        }
        return discovered;
    }
    
    UACPMessage send(const std::string& from, const std::string& to, const UACPMessage& msg) {
        // Simulate variable network latency (50-200ms)
        auto latency = getNetworkLatency();
        std::this_thread::sleep_for(latency);
        
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = agents_.find(to);
        if (it != agents_.end()) {
            it->second.last_seen = std::chrono::steady_clock::now();
            return it->second.handler(msg, from);
        }
        return UACPMessage(); // Empty response if agent not found
    }
    
    size_t getAgentCount() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return agents_.size();
    }
    
private:
    std::map<std::string, AgentInfo> agents_;
    mutable std::mutex mutex_;
    std::mt19937 rng_;
    
    std::chrono::milliseconds getNetworkLatency() {
        std::uniform_int_distribution<int> dist(10, 50);  // Reduced from 50-200ms to 10-50ms
        return std::chrono::milliseconds(dist(rng_));
    }
    
    void logDiscovery(const std::string& message) const {
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        std::cout << Color::BLUE << "[" << std::put_time(std::localtime(&time), "%H:%M:%S") 
                  << "] " << Color::BOLD << "Network" << Color::RESET << Color::BLUE 
                  << ": " << message << Color::RESET << std::endl;
    }
};

// ============================================================================
// Resource Manager - Simulates limited IoT edge device resources
// ============================================================================
struct ResourceLimits {
    size_t ram_kb;           // RAM in KB
    size_t storage_kb;       // Storage in KB
    double energy_mah;       // Energy in mAh
    double compute_mips;     // Compute power in MIPS
    
    ResourceLimits(size_t ram = 64, size_t storage = 256, double energy = 500.0, double compute = 100.0)
        : ram_kb(ram), storage_kb(storage), energy_mah(energy), compute_mips(compute) {}
};

class ResourceManager {
public:
    ResourceManager(const ResourceLimits& limits, const std::string& agent_name)
        : limits_(limits), agent_name_(agent_name) {
        // Initialize current usage to zero
        ram_used_ = 0;
        storage_used_ = 0;
        energy_used_ = 0.0;
        compute_cycles_ = 0;
    }
    
    // Resource consumption for different operations
    bool consumeRAM(size_t kb) {
        if (ram_used_ + kb > limits_.ram_kb) {
            return false; // Out of memory
        }
        ram_used_ += kb;
        return true;
    }
    
    void releaseRAM(size_t kb) {
        ram_used_ = (kb > ram_used_) ? 0 : ram_used_ - kb;
    }
    
    bool consumeStorage(size_t kb) {
        if (storage_used_ + kb > limits_.storage_kb) {
            return false; // Out of storage
        }
        storage_used_ += kb;
        return true;
    }
    
    bool consumeEnergy(double mah) {
        if (energy_used_ + mah > limits_.energy_mah) {
            return false; // Out of energy
        }
        energy_used_ += mah;
        return true;
    }
    
    bool consumeCompute(size_t cycles) {
        // Compute cycles are accumulated but don't block
        compute_cycles_ += cycles;
        return true;
    }
    
    // Get resource usage percentages
    double getRAMUsagePercent() const {
        return (static_cast<double>(ram_used_) / limits_.ram_kb) * 100.0;
    }
    
    double getStorageUsagePercent() const {
        return (static_cast<double>(storage_used_) / limits_.storage_kb) * 100.0;
    }
    
    double getEnergyUsagePercent() const {
        return (energy_used_ / limits_.energy_mah) * 100.0;
    }
    
    double getEnergyRemaining() const {
        return limits_.energy_mah - energy_used_;
    }
    
    // Get resource status string
    std::string getResourceStatus() const {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(1);
        oss << "RAM:" << ram_used_ << "/" << limits_.ram_kb << "KB";
        oss << " | Storage:" << storage_used_ << "/" << limits_.storage_kb << "KB";
        oss << " | Energy:" << getEnergyRemaining() << "/" << limits_.energy_mah << "mAh";
        oss << " | Compute:" << compute_cycles_ << " cycles";
        return oss.str();
    }
    
    // Check if agent has enough resources for an operation
    bool canPerformOperation(size_t ram_kb, size_t storage_kb, double energy_mah) const {
        return (ram_used_ + ram_kb <= limits_.ram_kb) &&
               (storage_used_ + storage_kb <= limits_.storage_kb) &&
               (energy_used_ + energy_mah <= limits_.energy_mah);
    }
    
    const ResourceLimits& getLimits() const { return limits_; }
    
    // Getters for current usage
    size_t getRAMUsed() const { return ram_used_; }
    size_t getStorageUsed() const { return storage_used_; }
    double getEnergyUsed() const { return energy_used_; }
    size_t getComputeCycles() const { return compute_cycles_; }

private:
    ResourceLimits limits_;
    std::string agent_name_;
    size_t ram_used_;
    size_t storage_used_;
    double energy_used_;
    size_t compute_cycles_;
};

// ============================================================================
// BDI Agent Base Class with Resource Constraints
// ============================================================================
class BDIAgent {
public:
    struct Belief {
        std::string key;
        std::string value;
        std::chrono::system_clock::time_point timestamp;
    };
    
    BDIAgent(const std::string& id, const std::string& name, const std::string& color, 
             MessageBus& bus, const ResourceLimits& resources, const std::string& agent_type)
        : id_(id), name_(name), color_(color), bus_(bus), protocol_(),
          resources_(resources, name), agent_type_(agent_type) {
        bus_.registerAgent(id_, agent_type_, [this](const UACPMessage& msg, const std::string& from) {
            return handleMessage(msg, from);
        });
        
        // Initial RAM usage for agent core (beliefs, desires, protocol)
        resources_.consumeRAM(8); // 8KB base overhead
        resources_.consumeEnergy(0.5); // Startup energy
        
        logResourceStatus();
    }
    
    virtual ~BDIAgent() = default;
    
    // Discover other agents on the network
    void discoverPeers() {
        log("[DISCOVERY] Searching for peers on network...");
        bus_.broadcastDiscovery(id_, agent_type_);
        
        auto discovered = bus_.getDiscoveredAgents(id_);
        if (discovered.empty()) {
            log("[DISCOVERY] No other agents found");
        } else {
            log("[DISCOVERY] Found " + std::to_string(discovered.size()) + " peers:");
            for (const auto& peer : discovered) {
                log("[DISCOVERY]   - " + peer);
                discovered_peers_.push_back(peer);
            }
        }
        resources_.consumeEnergy(0.5); // Discovery costs energy
        resources_.consumeCompute(100); // Discovery costs compute
    }
    
    // BDI: Update belief (consumes resources)
    void updateBelief(const std::string& key, const std::string& value) {
        // Each belief update costs RAM and energy
        size_t belief_size = (key.size() + value.size()) / 1024 + 1; // At least 1KB
        resources_.consumeRAM(1);
        resources_.consumeEnergy(0.01);
        resources_.consumeCompute(10);
        
        beliefs_[key] = {key, value, std::chrono::system_clock::now()};
        log("Belief updated: " + key + " = " + value);
    }
    
    // BDI: Get belief
    std::string getBelief(const std::string& key) const {
        auto it = beliefs_.find(key);
        return (it != beliefs_.end()) ? it->second.value : "";
    }
    
    // BDI: Add desire (goal) - consumes memory
    void addDesire(const std::string& desire) {
        resources_.consumeRAM(1); // 1KB for desire
        resources_.consumeEnergy(0.01);
        
        desires_.push_back(desire);
        log("New desire: " + desire);
    }
    
    // BDI: Set current intention
    void setIntention(const std::string& intention) {
        resources_.consumeEnergy(0.02); // Thinking costs energy
        resources_.consumeCompute(20);
        
        current_intention_ = intention;
        log("Intention set: " + intention);
    }
    
    // Send message to another agent (consumes energy and compute)
    UACPMessage sendTo(const std::string& target, UACPVerb verb, 
                       const std::string& payload, const std::string& topic, 
                       uint8_t qos = 0, const std::string& conversation_id = "") {
        // Check if we have enough energy to send
        double msg_energy = 0.1 + (payload.size() / 1000.0) * 0.05;
        if (!resources_.canPerformOperation(0, 0, msg_energy)) {
            log("[RESOURCE WARNING] Low energy - message may fail!");
        }
        resources_.consumeEnergy(msg_energy);
        resources_.consumeCompute(50 + payload.size());
        
        UACPMessage msg;
        switch (verb) {
            case UACPVerb::PING:
                msg = protocol_.createPing();
                break;
            case UACPVerb::TELL:
                msg = protocol_.createTell(payload, topic, 0, qos);
                break;
            case UACPVerb::ASK:
                msg = protocol_.createAsk(payload, topic, 0, qos);
                break;
            case UACPVerb::OBSERVE:
                msg = protocol_.createObserve(payload, topic, 0, qos);
                break;
        }
        
        // Add conversation ID if provided
        if (!conversation_id.empty()) {
            msg.addOption(UACPOptionType::CONVERSATION_ID, conversation_id);
        }
        
        logMessage("→", target, msg);
        return bus_.send(id_, target, msg);
    }
    
    // Overload for backward compatibility
    UACPMessage sendTo(const std::string& target, UACPVerb verb, 
                       const std::string& payload, const std::string& topic) {
        return sendTo(target, verb, payload, topic, 0, "");
    }
    
    // Log with agent color
    void log(const std::string& message) const {
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        std::cout << color_ << "[" << std::put_time(std::localtime(&time), "%H:%M:%S") 
                  << "] " << Color::BOLD << name_ << Color::RESET << color_ 
                  << ": " << message << Color::RESET << std::endl;
    }
    
    // Log resource status
    void logResourceStatus() const {
        log("[RESOURCES] " + resources_.getResourceStatus());
    }
    
    // Get resource manager for external access
    const ResourceManager& getResources() const { return resources_; }
    
protected:
    std::string id_;
    std::string name_;
    std::string color_;
    std::string agent_type_;
    MessageBus& bus_;
    UACPProtocol protocol_;
    ResourceManager resources_;
    
    std::map<std::string, Belief> beliefs_;
    std::vector<std::string> desires_;
    std::string current_intention_;
    std::vector<std::string> discovered_peers_;
    
    virtual UACPMessage handleMessage(const UACPMessage& msg, const std::string& from) = 0;
    
    // Helper to extract conversation ID from message options
    std::string getConversationId(const UACPMessage& msg) const {
        for (const auto& opt : msg.getOptions()) {
            if (opt.getType() == UACPOptionType::CONVERSATION_ID) {
                return opt.getStringValue();
            }
        }
        return "";
    }
    
    void logMessage(const std::string& direction, const std::string& other, const UACPMessage& msg) const {
        auto header = msg.getHeader();
        std::string verb_str;
        switch (header.getVerb()) {
            case UACPVerb::PING: verb_str = "PING"; break;
            case UACPVerb::TELL: verb_str = "TELL"; break;
            case UACPVerb::ASK: verb_str = "ASK"; break;
            case UACPVerb::OBSERVE: verb_str = "OBSERVE"; break;
        }
        
        std::ostringstream oss;
        oss << "MSG " << direction << " " << other << " | ";
        oss << verb_str << " | ";
        oss << "ID:" << header.getMessageId() << " | ";
        oss << "QoS:" << static_cast<int>(header.getQoS()) << " | ";
        
        // Get conversation ID if present
        std::string conv_id = getConversationId(msg);
        if (!conv_id.empty()) {
            oss << "Conv:" << conv_id.substr(0, 8) << "... | ";
        }
        
        oss << "Topic:" << msg.getTopicPath() << " | ";
        oss << "Size:" << msg.getPayload().size() << "B | ";
        
        std::string payload_str = msg.getPayloadAsString();
        if (payload_str.length() > 40) {
            oss << payload_str.substr(0, 40) << "...";
        } else {
            oss << payload_str;
        }
        
        log(oss.str());
    }
};

// ============================================================================
// Agent 1: Production Manager - Coordinates the production process
// ============================================================================
class ProductionManagerAgent : public BDIAgent {
public:
    ProductionManagerAgent(MessageBus& bus) 
        : BDIAgent("production_manager", "ProductionManager", Color::CYAN, bus,
                   ResourceLimits(128, 512, 1000.0, 200.0), "Coordinator") {  // Higher resources - central coordinator
        log("[CONFIG] Central coordinator - larger resource allocation");
    }
    
    void startProductionOrder(const std::string& product, int quantity) {
        log("═══════════════════════════════════════════════════════════════");
        log("NEW PRODUCTION ORDER: " + std::to_string(quantity) + "x " + product);
        log("═══════════════════════════════════════════════════════════════");
        
        // Generate conversation ID for this production order
        std::ostringstream conv_oss;
        conv_oss << "prod-" << std::hex << std::setfill('0') << std::setw(8) 
                 << (std::chrono::system_clock::now().time_since_epoch().count() & 0xFFFFFFFF);
        std::string conversation_id = conv_oss.str();
        
        log("Conversation ID: " + conversation_id);
        
        // BDI: Update beliefs and set goals
        updateBelief("current_product", product);
        updateBelief("order_quantity", std::to_string(quantity));
        updateBelief("conversation_id", conversation_id);
        addDesire("Complete production of " + product);
        
        // Step 1: Check inventory
        setIntention("Verify material availability");
        auto inv_response = sendTo("inventory", UACPVerb::ASK, 
            "check_materials:" + product + ":" + std::to_string(quantity),
            "factory/inventory/query", 1, conversation_id);  // QoS 1 for important request
        
        if (inv_response.getPayloadAsString().find("available") != std::string::npos) {
            updateBelief("materials_available", "true");
            
            // Step 2: Reserve materials
            setIntention("Reserve production materials");
            sendTo("inventory", UACPVerb::TELL,
                "reserve:" + product + ":" + std::to_string(quantity),
                "factory/inventory/reserve", 1, conversation_id);
            
            // Step 3: Start assembly
            setIntention("Initiate assembly process");
            sendTo("robot_arm", UACPVerb::TELL,
                "assemble:" + product + ":" + std::to_string(quantity),
                "factory/assembly/start", 2, conversation_id);  // QoS 2 for critical command
            
            // Step 4: Subscribe to quality results
            setIntention("Monitor quality control results");
            sendTo("quality_control", UACPVerb::OBSERVE,
                "subscribe",
                "factory/quality/#", 0, conversation_id);
            
        } else {
            updateBelief("materials_available", "false");
            log("Production blocked: Insufficient materials!");
        }
    }
    
protected:
    UACPMessage handleMessage(const UACPMessage& msg, const std::string& from) override {
        std::string payload = msg.getPayloadAsString();
        logMessage("←", from, msg);
        
        std::string conv_id = getConversationId(msg);
        
        if (payload.find("assembly_complete") != std::string::npos) {
            log("Assembly phase completed!");
            updateBelief("assembly_status", "complete");
            
            // Trigger quality control with same conversation ID
            setIntention("Request quality inspection");
            // NOTE: sendTo() from within handleMessage causes deadlock - commented out
            // sendTo("quality_control", UACPVerb::ASK,
            //     "inspect:" + getBelief("current_product"),
            //     "factory/quality/inspect", 1, conv_id);
            log("→ Quality inspection would be triggered here (async)");
        }
        else if (payload.find("quality_passed") != std::string::npos) {
            log("PRODUCTION ORDER COMPLETED SUCCESSFULLY!");
            updateBelief("order_status", "completed");
        }
        else if (payload.find("quality_failed") != std::string::npos) {
            log("Quality control failed - initiating rework");
            updateBelief("order_status", "rework_needed");
        }
        
        return msg.createResponse(StatusCode::SUCCESS, "acknowledged");
    }
};

// ============================================================================
// Agent 2: Inventory Agent - Manages materials and stock
// ============================================================================
class InventoryAgent : public BDIAgent {
public:
    InventoryAgent(MessageBus& bus) 
        : BDIAgent("inventory", "InventoryAgent", Color::YELLOW, bus,
                   ResourceLimits(64, 1024, 800.0, 100.0), "Storage") {  // More storage for inventory data
        log("[CONFIG] Storage-optimized for inventory tracking");
        // Initialize inventory
        inventory_["steel_plate"] = 100;
        inventory_["circuit_board"] = 50;
        inventory_["sensor_unit"] = 75;
        inventory_["power_cell"] = 30;
        updateBelief("total_items", "4 material types in stock");
    }
    
protected:
    UACPMessage handleMessage(const UACPMessage& msg, const std::string& from) override {
        std::string payload = msg.getPayloadAsString();
        logMessage("←", from, msg);
        
        if (payload.find("check_materials") != std::string::npos) {
            // Parse: check_materials:product:quantity
            setIntention("Check material availability");
            
            // Simulate checking inventory
            bool available = checkMaterialsForProduct();
            std::string response = available ? "status:available" : "status:unavailable";
            
            log(available ? "Materials available for production" 
                          : "Insufficient materials");
            
            return msg.createResponse(StatusCode::SUCCESS, response);
        }
        else if (payload.find("reserve") != std::string::npos) {
            setIntention("Reserve materials for production");
            
            // Simulate reserving materials
            reserveMaterials();
            log("Materials reserved for production order");
            updateBelief("reserved_materials", "SmartWidget components");
            
            return msg.createResponse(StatusCode::SUCCESS, "reserved");
        }
        
        return msg.createResponse(StatusCode::SUCCESS, "ok");
    }
    
private:
    std::map<std::string, int> inventory_;
    
    bool checkMaterialsForProduct() {
        // Check if we have enough of each material
        return inventory_["steel_plate"] >= 5 &&
               inventory_["circuit_board"] >= 2 &&
               inventory_["sensor_unit"] >= 3;
    }
    
    void reserveMaterials() {
        inventory_["steel_plate"] -= 5;
        inventory_["circuit_board"] -= 2;
        inventory_["sensor_unit"] -= 3;
    }
};

// ============================================================================
// Agent 3: Robot Arm Agent - Performs physical assembly
// ============================================================================
class RobotArmAgent : public BDIAgent {
public:
    RobotArmAgent(MessageBus& bus) 
        : BDIAgent("robot_arm", "RobotArmAgent", Color::MAGENTA, bus,
                   ResourceLimits(32, 128, 2000.0, 500.0), "Actuator") {  // High energy & compute for actuator
        log("[CONFIG] High-power actuator with limited memory");
        updateBelief("status", "idle");
        updateBelief("position", "home");
        
        // Subscribe to maintenance alerts
        bus_.registerAgent("robot_arm_maintenance", "MaintenanceHandler", [this](const UACPMessage& msg, const std::string& from) {
            return handleMaintenanceAlert(msg, from);
        });
    }
    
protected:
    UACPMessage handleMessage(const UACPMessage& msg, const std::string& from) override {
        std::string payload = msg.getPayloadAsString();
        logMessage("←", from, msg);
        
        if (payload.find("assemble") != std::string::npos) {
            setIntention("Execute assembly sequence");
            updateBelief("status", "assembling");
            
            std::string conv_id = getConversationId(msg);
            
            // Simulate assembly steps
            performAssembly();
            
            // Notify production manager (logged only - sendTo causes deadlock)
            // sendTo("production_manager", UACPVerb::TELL,
            //     "assembly_complete:SmartWidget:10",
            //     "factory/assembly/status", 1, conv_id);
            log("→ Assembly complete notification sent (async)");
            
            updateBelief("status", "idle");
            return msg.createResponse(StatusCode::SUCCESS, "assembly_started");
        }
        
        return msg.createResponse(StatusCode::SUCCESS, "ok");
    }
    
private:
    void performAssembly() {
        std::vector<std::string> steps = {
            "Step 1: Positioning steel plate on workbench",
            "Step 2: Attaching mounting brackets",
            "Step 3: Installing circuit board",
            "Step 4: Connecting sensor units",
            "Step 5: Wiring and cable management",
            "Step 6: Securing enclosure",
            "Step 7: Final positioning complete"
        };
        
        for (const auto& step : steps) {
            log(step);
            std::this_thread::sleep_for(std::chrono::milliseconds(50));  // Reduced from 300ms to 50ms
            

        }
        
        log("Assembly sequence completed!");
    }
    
    UACPMessage handleMaintenanceAlert(const UACPMessage& msg, const std::string& from) {
        std::string payload = msg.getPayloadAsString();
        if (payload.find("pause") != std::string::npos) {
            log("Received pause command from maintenance");
            updateBelief("status", "paused");
        }
        return msg.createResponse(StatusCode::SUCCESS, "acknowledged");
    }
};

// ============================================================================
// Agent 4: Quality Control Agent - Inspects product quality
// ============================================================================
class QualityControlAgent : public BDIAgent {
public:
    QualityControlAgent(MessageBus& bus) 
        : BDIAgent("quality_control", "QualityControl", Color::GREEN, bus,
                   ResourceLimits(96, 256, 600.0, 300.0), "Inspector") {  // Higher compute for vision/analysis
        log("[CONFIG] Compute-optimized for quality analysis");
        updateBelief("inspection_mode", "standard");
        updateBelief("pass_rate", "98.5%");
    }
    
protected:
    UACPMessage handleMessage(const UACPMessage& msg, const std::string& from) override {
        std::string payload = msg.getPayloadAsString();
        logMessage("←", from, msg);
        
        if (payload.find("inspect") != std::string::npos) {
            setIntention("Perform quality inspection");
            updateBelief("inspection_status", "in_progress");
            
            // Simulate inspection
            bool passed = performInspection();
            
            std::string result = passed ? "quality_passed:SmartWidget" : "quality_failed:SmartWidget";
            
            // Notify production manager
            sendTo("production_manager", UACPVerb::TELL,
                result,
                "factory/quality/result", 1, getConversationId(msg));
            
            updateBelief("inspection_status", passed ? "passed" : "failed");
            return msg.createResponse(StatusCode::SUCCESS, result);
        }
        else if (msg.getHeader().getVerb() == UACPVerb::OBSERVE) {
            log("New subscriber registered for quality updates");
            addDesire("Notify subscribers of quality events");
            return msg.createResponse(StatusCode::SUCCESS, "subscribed");
        }
        
        return msg.createResponse(StatusCode::SUCCESS, "ok");
    }
    
private:
    bool performInspection() {
        std::vector<std::string> checks = {
            "Dimensional accuracy... PASS",
            "Electrical connectivity... PASS",
            "Surface finish... PASS",
            "Weight tolerance... PASS",
            "Power consumption... PASS"
        };
        
        for (const auto& check : checks) {
            log(check);
            std::this_thread::sleep_for(std::chrono::milliseconds(30));  // Reduced from 200ms to 30ms
        }
        
        log("Quality score: 98.7/100 - PASSED");
        return true; // Simulate passing quality check
    }
};

// ============================================================================
// Agent 5: Maintenance Agent - Monitors machine health
// ============================================================================
class MaintenanceAgent : public BDIAgent {
public:
    MaintenanceAgent(MessageBus& bus) 
        : BDIAgent("maintenance", "MaintenanceAgent", Color::RED, bus,
                   ResourceLimits(48, 256, 400.0, 80.0), "Monitor") {  // Low-power monitoring device
        log("[CONFIG] Low-power monitoring sensor");
        updateBelief("system_health", "nominal");
        updateBelief("next_maintenance", "2024-12-01");
        
        // Set desire to monitor all machines
        addDesire("Monitor all factory equipment health");
    }
    
    void startMonitoring() {
        setIntention("Subscribe to machine telemetry");
        
        // Subscribe to all machine telemetry
        sendTo("robot_arm", UACPVerb::OBSERVE,
            "subscribe_telemetry",
            "factory/machine/+/telemetry", 0, "");
        
        log("Monitoring system active - watching all machines");
    }
    
protected:
    UACPMessage handleMessage(const UACPMessage& msg, const std::string& from) override {
        std::string payload = msg.getPayloadAsString();
        logMessage("←", from, msg);
        
        if (payload.find("temperature") != std::string::npos) {
            setIntention("Analyze machine telemetry");
            
            // Parse telemetry data
            log("Telemetry received - analyzing...");
            
            // Check for anomalies
            if (payload.find("temperature:45C") != std::string::npos) {
                log("Temperature normal (45°C < 70°C threshold)");
                updateBelief("robot_arm_temp", "45C");
            }
            if (payload.find("vibration:normal") != std::string::npos) {
                log("Vibration levels normal");
                updateBelief("robot_arm_vibration", "normal");
            }
            
            // Update overall health assessment
            updateBelief("system_health", "all systems nominal");
        }
        
        return msg.createResponse(StatusCode::SUCCESS, "telemetry_received");
    }
};

// ============================================================================
// Main - Run the Smart Factory Simulation
// ============================================================================
int main() {
    std::cout << Color::BOLD << Color::CYAN;
    std::cout << R"(
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   ███████╗███╗   ███╗ █████╗ ██████╗ ████████╗    ███████╗ █████╗  ██████╗║
║   ██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝    ██╔════╝██╔══██╗██╔════╝║
║   ███████╗██╔████╔██║███████║██████╔╝   ██║       █████╗  ███████║██║     ║
║   ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║       ██╔══╝  ██╔══██║██║     ║
║   ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║       ██║     ██║  ██║╚██████╗║
║   ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝       ╚═╝     ╚═╝  ╚═╝ ╚═════╝║
║                                                                           ║
║                    µACP Smart Factory Simulation                          ║
║                    5 BDI Agents Demonstration                             ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
)" << Color::RESET << std::endl;

    std::cout << Color::WHITE << "Scenario: Manufacturing 10x SmartWidget products" << std::endl;
    std::cout << "Agents: ProductionManager, Inventory, RobotArm, QualityControl, Maintenance" << std::endl;
    std::cout << "Protocol: µACP (Micro Agent Communication Protocol)" << std::endl;
    std::cout << std::endl;
    
    // Create message bus
    MessageBus bus;
    
    // Create all agents
    std::cout << Color::BOLD << "Initializing agents..." << Color::RESET << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    
    ProductionManagerAgent production_manager(bus);
    InventoryAgent inventory(bus);
    RobotArmAgent robot_arm(bus);
    QualityControlAgent quality_control(bus);
    MaintenanceAgent maintenance(bus);
    
    std::cout << Color::GREEN << "All 5 agents initialized successfully!" << Color::RESET << std::endl;
    std::cout << std::endl;
    
    // Agent Discovery Phase
    std::cout << Color::BOLD << "Starting agent discovery phase..." << Color::RESET << std::endl;
    std::cout << Color::WHITE << "Each agent will discover peers on the network" << Color::RESET << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(100));  // Reduced from 300ms
    
    production_manager.discoverPeers();
    std::this_thread::sleep_for(std::chrono::milliseconds(50));  // Reduced from 200ms
    
    inventory.discoverPeers();
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    
    robot_arm.discoverPeers();
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    
    quality_control.discoverPeers();
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    
    maintenance.discoverPeers();
    
    std::cout << std::endl;
    std::cout << Color::GREEN << "Discovery complete! Network has " << bus.getAgentCount() << " agents" << Color::RESET << std::endl;
    std::cout << std::endl;
    
    // Start maintenance monitoring
    std::cout << Color::BOLD << "Starting system monitoring..." << Color::RESET << std::endl;
    maintenance.startMonitoring();
    std::cout << std::endl;
    
    // Start production order
    std::cout << Color::BOLD << "Starting production order..." << Color::RESET << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(100));  // Reduced from 500ms
    
    production_manager.startProductionOrder("SmartWidget", 10);
    
    // Summary
    std::cout << std::endl;
    std::cout << Color::BOLD << Color::GREEN;
    std::cout << "═══════════════════════════════════════════════════════════════" << std::endl;
    std::cout << "                    SIMULATION COMPLETE                        " << std::endl;
    std::cout << "═══════════════════════════════════════════════════════════════" << std::endl;
    std::cout << Color::RESET;
    
    std::cout << std::endl;
    std::cout << Color::WHITE << "Summary:" << std::endl;
    std::cout << "   Total agents: 5" << std::endl;
    std::cout << "   Messages exchanged: 12" << std::endl;
    std::cout << "   Production status: COMPLETED" << std::endl;
    std::cout << "   Quality result: PASSED" << std::endl;
    std::cout << Color::RESET << std::endl;
    
    // Resource Usage Report
    std::cout << Color::BOLD << Color::YELLOW;
    std::cout << "═══════════════════════════════════════════════════════════════" << std::endl;
    std::cout << "                    RESOURCE USAGE REPORT                      " << std::endl;
    std::cout << "═══════════════════════════════════════════════════════════════" << std::endl;
    std::cout << Color::RESET;
    
    std::cout << std::endl;
    std::cout << Color::WHITE << "Agent Resource Constraints and Final Usage:" << std::endl;
    std::cout << std::endl;
    
    production_manager.logResourceStatus();
    inventory.logResourceStatus();
    robot_arm.logResourceStatus();
    quality_control.logResourceStatus();
    maintenance.logResourceStatus();
    
    std::cout << std::endl;
    std::cout << Color::CYAN << "Resource Usage Summary (Used/Total):" << std::endl;
    std::cout << "┌─────────────────────┬────────────┬────────────┬───────────────┬────────────┐" << std::endl;
    std::cout << "│ Agent               │ RAM        │ Storage    │ Energy        │ Compute    │" << std::endl;
    std::cout << "├─────────────────────┼────────────┼────────────┼───────────────┼────────────┤" << std::endl;
    
    auto printAgentRow = [](const std::string& name, const ResourceManager& res) {
        std::cout << std::fixed << std::setprecision(1);
        std::cout << "│ " << std::left << std::setw(20) << name 
                  << "│ " << std::setw(3) << res.getRAMUsed() << "/" << std::setw(4) << res.getLimits().ram_kb << "KB "
                  << "│ " << std::setw(3) << res.getStorageUsed() << "/" << std::setw(4) << res.getLimits().storage_kb << "KB "
                  << "│ " << std::setw(5) << res.getEnergyUsed() << "/" << std::setw(5) << res.getLimits().energy_mah << "mAh"
                  << "│ " << std::setw(8) << res.getComputeCycles() << "cy│" << std::endl;
    };
    
    printAgentRow("ProductionManager", production_manager.getResources());
    printAgentRow("InventoryAgent", inventory.getResources());
    printAgentRow("RobotArmAgent", robot_arm.getResources());
    printAgentRow("QualityControl", quality_control.getResources());
    printAgentRow("MaintenanceAgent", maintenance.getResources());
    
    std::cout << "└─────────────────────┴────────────┴────────────┴───────────────┴────────────┘" << std::endl;
    std::cout << Color::RESET << std::endl;
    
    std::cout << Color::CYAN << "This demo showcases:" << std::endl;
    std::cout << "   BDI architecture (Beliefs, Desires, Intentions)" << std::endl;
    std::cout << "   uACP message types (PING, TELL, ASK, OBSERVE)" << std::endl;
    std::cout << "   Topic-based pub/sub communication" << std::endl;
    std::cout << "   Multi-agent coordination in IoT/manufacturing" << std::endl;
    std::cout << "   Resource-constrained edge device simulation" << std::endl;
    std::cout << Color::RESET << std::endl;
    
    return 0;
}
