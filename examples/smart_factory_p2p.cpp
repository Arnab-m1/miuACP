/**
 * @file smart_factory_p2p.cpp
 * @brief Smart Factory P2P Simulation
 * 
 * Simulates a smart factory with 5 agents communicating peer-to-peer:
 * - Coordinator: Orchestrates the factory
 * - Robot Arm: Handles assembly tasks
 * - Conveyor: Manages material transport
 * - Quality Control: Inspects products
 * - Warehouse: Manages inventory
 * 
 * Usage: ./smart_factory_p2p
 */

#include <iostream>
#include <thread>
#include <chrono>
#include <atomic>
#include <csignal>
#include "miuacp/agent.h"

using namespace miuacp;
using namespace std::chrono_literals;

std::atomic<bool> running(true);

void signalHandler(int signum) {
    (void)signum;
    running = false;
}

void runCoordinator() {
    UACPAgent coordinator("coordinator", "Factory Coordinator", "0.0.0.0", 9001);
    
    coordinator.addTopicHandler("factory/#", 
        [](const UACPMessage& msg, const std::string& sender, int port) {
            std::cout << "🏭 [Coordinator] Received: " << msg.getTopicPath() 
                      << " from " << sender << ":" << port << std::endl;
            std::cout << "   Payload: " << msg.getPayloadAsString() << std::endl;
            return msg.createResponse(StatusCode::SUCCESS, "Acknowledged");
        });
    
    if (!coordinator.start()) {
        std::cerr << "Failed to start coordinator!" << std::endl;
        return;
    }
    
    std::cout << "🏭 Coordinator started on port 9001" << std::endl;
    
    std::this_thread::sleep_for(2s);
    
    // Send instructions to other agents
    int cycle = 0;
    while (running && cycle < 5) {
        std::cout << "\n🏭 [Coordinator] Starting production cycle #" << ++cycle << std::endl;
        
        // Tell robot arm to start assembly
        coordinator.tell("127.0.0.1", 9002, "Start assembly", "factory/robot/command");
        std::this_thread::sleep_for(1s);
        
        // Tell conveyor to move materials
        coordinator.tell("127.0.0.1", 9003, "Move batch", "factory/conveyor/command");
        std::this_thread::sleep_for(1s);
        
        // Request quality check
        coordinator.tell("127.0.0.1", 9004, "Inspect batch", "factory/qc/command");
        std::this_thread::sleep_for(1s);
        
        // Update warehouse
        coordinator.tell("127.0.0.1", 9005, "Update inventory", "factory/warehouse/command");
        std::this_thread::sleep_for(2s);
    }
    
    coordinator.stop();
    std::cout << "🏭 Coordinator stopped" << std::endl;
}

void runRobotArm() {
    UACPAgent robot("robot-arm", "Robot Arm", "0.0.0.0", 9002);
    
    robot.addTopicHandler("factory/robot/#",
        [&robot](const UACPMessage& msg, const std::string& sender, int port) {
            (void)sender;
            (void)port;
            std::string cmd = msg.getPayloadAsString();
            std::cout << "🤖 [Robot Arm] Command received: " << cmd << std::endl;
            
            std::this_thread::sleep_for(500ms);
            std::cout << "🤖 [Robot Arm] Assembly complete!" << std::endl;
            
            // Notify coordinator
            robot.tell("127.0.0.1", 9001, "Assembly done", "factory/robot/status");
            
            return msg.createResponse(StatusCode::SUCCESS, "Assembly completed");
        });
    
    if (!robot.start()) {
        std::cerr << "Failed to start robot arm!" << std::endl;
        return;
    }
    
    std::cout << "🤖 Robot Arm started on port 9002" << std::endl;
    
    while (running) {
        std::this_thread::sleep_for(100ms);
    }
    
    robot.stop();
    std::cout << "🤖 Robot Arm stopped" << std::endl;
}

void runConveyor() {
    UACPAgent conveyor("conveyor", "Conveyor Belt", "0.0.0.0", 9003);
    
    conveyor.addTopicHandler("factory/conveyor/#",
        [&conveyor](const UACPMessage& msg, const std::string& sender, int port) {
            (void)sender;
            (void)port;
            std::string cmd = msg.getPayloadAsString();
            std::cout << "🛤️  [Conveyor] Command received: " << cmd << std::endl;
            
            std::this_thread::sleep_for(300ms);
            std::cout << "🛤️  [Conveyor] Materials moved!" << std::endl;
            
            conveyor.tell("127.0.0.1", 9001, "Transport complete", "factory/conveyor/status");
            
            return msg.createResponse(StatusCode::SUCCESS, "Transport completed");
        });
    
    if (!conveyor.start()) {
        std::cerr << "Failed to start conveyor!" << std::endl;
        return;
    }
    
    std::cout << "🛤️  Conveyor started on port 9003" << std::endl;
    
    while (running) {
        std::this_thread::sleep_for(100ms);
    }
    
    conveyor.stop();
    std::cout << "🛤️  Conveyor stopped" << std::endl;
}

void runQualityControl() {
    UACPAgent qc("quality-control", "Quality Control", "0.0.0.0", 9004);
    
    qc.addTopicHandler("factory/qc/#",
        [&qc](const UACPMessage& msg, const std::string& sender, int port) {
            (void)sender;
            (void)port;
            std::string cmd = msg.getPayloadAsString();
            std::cout << "🔍 [QC] Command received: " << cmd << std::endl;
            
            std::this_thread::sleep_for(400ms);
            std::cout << "🔍 [QC] Inspection passed! ✓" << std::endl;
            
            qc.tell("127.0.0.1", 9001, "QC passed", "factory/qc/status");
            
            return msg.createResponse(StatusCode::SUCCESS, "Inspection passed");
        });
    
    if (!qc.start()) {
        std::cerr << "Failed to start QC!" << std::endl;
        return;
    }
    
    std::cout << "🔍 Quality Control started on port 9004" << std::endl;
    
    while (running) {
        std::this_thread::sleep_for(100ms);
    }
    
    qc.stop();
    std::cout << "🔍 Quality Control stopped" << std::endl;
}

void runWarehouse() {
    UACPAgent warehouse("warehouse", "Warehouse", "0.0.0.0", 9005);
    
    int inventory = 100;
    
    warehouse.addTopicHandler("factory/warehouse/#",
        [&warehouse, &inventory](const UACPMessage& msg, const std::string& sender, int port) {
            (void)sender;
            (void)port;
            std::string cmd = msg.getPayloadAsString();
            std::cout << "📦 [Warehouse] Command received: " << cmd << std::endl;
            
            inventory += 10;
            std::cout << "📦 [Warehouse] Inventory updated: " << inventory << " units" << std::endl;
            
            warehouse.tell("127.0.0.1", 9001, "Inventory: " + std::to_string(inventory), 
                          "factory/warehouse/status");
            
            return msg.createResponse(StatusCode::SUCCESS, "Inventory updated");
        });
    
    if (!warehouse.start()) {
        std::cerr << "Failed to start warehouse!" << std::endl;
        return;
    }
    
    std::cout << "📦 Warehouse started on port 9005" << std::endl;
    
    while (running) {
        std::this_thread::sleep_for(100ms);
    }
    
    warehouse.stop();
    std::cout << "📦 Warehouse stopped" << std::endl;
}

int main() {
    signal(SIGINT, signalHandler);
    
    std::cout << "========================================" << std::endl;
    std::cout << "  Smart Factory P2P Simulation" << std::endl;
    std::cout << "========================================" << std::endl << std::endl;
    
    std::cout << "Starting 5 peer agents..." << std::endl << std::endl;
    
    // Start all agents in separate threads
    std::thread t_robot(runRobotArm);
    std::thread t_conveyor(runConveyor);
    std::thread t_qc(runQualityControl);
    std::thread t_warehouse(runWarehouse);
    std::thread t_coordinator(runCoordinator);
    
    // Wait for all to complete
    t_coordinator.join();
    
    running = false;
    
    t_robot.join();
    t_conveyor.join();
    t_qc.join();
    t_warehouse.join();
    
    std::cout << "\n========================================" << std::endl;
    std::cout << "  Simulation Complete!" << std::endl;
    std::cout << "========================================" << std::endl;
    
    return 0;
}
