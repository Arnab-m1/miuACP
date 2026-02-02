/**
 * @file benchmark.cpp
 * @brief Performance Benchmarking Tool for µACP P2P
 * 
 * Measures:
 * - Messages per second throughput
 * - Message latency (round-trip time)
 * - Multi-agent scalability
 * - Memory usage
 * - Network overhead
 */

#include <iostream>
#include <iomanip>
#include <chrono>
#include <thread>
#include <atomic>
#include <vector>
#include <numeric>
#include <algorithm>
#include "miuacp/agent.h"

using namespace miuacp;
using namespace std::chrono;

// Benchmark configuration
struct BenchmarkConfig {
    int num_messages = 1000;
    int num_agents = 2;
    int message_size = 100;  // bytes
    bool use_qos = false;
    int test_duration_sec = 10;
};

// Benchmark results
struct BenchmarkResults {
    double messages_per_sec = 0.0;
    double avg_latency_ms = 0.0;
    double min_latency_ms = 0.0;
    double max_latency_ms = 0.0;
    double throughput_kbps = 0.0;
    uint64_t total_messages = 0;
    uint64_t total_bytes = 0;
    std::vector<double> latencies;
};

// Generate test payload
std::string generatePayload(int size) {
    std::string payload;
    payload.reserve(size);
    for (int i = 0; i < size; i++) {
        payload += static_cast<char>('A' + (i % 26));
    }
    return payload;
}

// Benchmark 1: Throughput Test (Messages/sec)
BenchmarkResults benchmarkThroughput(const BenchmarkConfig& config) {
    std::cout << "\n========================================" << std::endl;
    std::cout << "Throughput Benchmark" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Messages: " << config.num_messages << std::endl;
    std::cout << "Message size: " << config.message_size << " bytes" << std::endl;
    std::cout << "QoS: " << (config.use_qos ? "Enabled" : "Disabled") << std::endl << std::endl;
    
    BenchmarkResults results;
    
    // Create sender and receiver
    UACPAgent sender("sender", "Sender", "0.0.0.0", 7101);
    UACPAgent receiver("receiver", "Receiver", "0.0.0.0", 7102);
    
    std::atomic<int> received_count{0};
    
    // Receiver counts messages
    receiver.addMessageHandler(UACPVerb::TELL,
        [&received_count](const UACPMessage& msg, const std::string&, int) {
            received_count++;
            return msg.createResponse(StatusCode::SUCCESS);
        });
    
    sender.start();
    receiver.start();
    
    std::this_thread::sleep_for(100ms);
    
    // Send messages and measure time
    std::string payload = generatePayload(config.message_size);
    
    auto start_time = steady_clock::now();
    
    for (int i = 0; i < config.num_messages; i++) {
        sender.tell("127.0.0.1", 7102, payload, "benchmark/test",
                   config.use_qos ? 1 : 0);
    }
    
    // Wait for all messages to be received
    auto timeout = start_time + seconds(10);
    while (received_count < config.num_messages && steady_clock::now() < timeout) {
        std::this_thread::sleep_for(10ms);
    }
    
    auto end_time = steady_clock::now();
    auto duration = duration_cast<milliseconds>(end_time - start_time);
    
    // Calculate results
    results.total_messages = received_count.load();
    results.total_bytes = results.total_messages * config.message_size;
    results.messages_per_sec = (results.total_messages * 1000.0) / duration.count();
    results.throughput_kbps = (results.total_bytes * 8.0) / duration.count();  // Kbit/s
    
    // Print results
    std::cout << "Duration: " << duration.count() << " ms" << std::endl;
    std::cout << "Messages sent: " << config.num_messages << std::endl;
    std::cout << "Messages received: " << results.total_messages << std::endl;
    std::cout << "Throughput: " << std::fixed << std::setprecision(2)
              << results.messages_per_sec << " msg/s" << std::endl;
    std::cout << "Bandwidth: " << results.throughput_kbps << " Kbit/s" << std::endl;
    
    sender.stop();
    receiver.stop();
    
    return results;
}

// Benchmark 2: Latency Test (Round-trip time)
BenchmarkResults benchmarkLatency(const BenchmarkConfig& config) {
    std::cout << "\n========================================" << std::endl;
    std::cout << "Latency Benchmark (Ping-Pong)" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Messages: " << config.num_messages << std::endl << std::endl;
    
    BenchmarkResults results;
    results.latencies.reserve(config.num_messages);
    
    // Create two agents
    UACPAgent agent1("agent1", "Agent 1", "0.0.0.0", 7201);
    UACPAgent agent2("agent2", "Agent 2", "0.0.0.0", 7202);
    
    // Agent2 echoes PING
    agent2.addMessageHandler(UACPVerb::PING,
        [](const UACPMessage& msg, const std::string&, int) {
            return msg.createResponse(StatusCode::SUCCESS, "pong");
        });
    
    agent1.start();
    agent2.start();
    
    std::this_thread::sleep_for(100ms);
    
    // Measure round-trip time for each PING
    for (int i = 0; i < config.num_messages; i++) {
        auto start = steady_clock::now();
        
        agent1.ping("127.0.0.1", 7202);
        
        auto end = steady_clock::now();
        auto rtt = duration_cast<microseconds>(end - start).count() / 1000.0;  // ms
        
        results.latencies.push_back(rtt);
        
        std::this_thread::sleep_for(1ms);  // Small delay between pings
    }
    
    // Calculate statistics
    results.avg_latency_ms = std::accumulate(results.latencies.begin(),
                                             results.latencies.end(), 0.0) / results.latencies.size();
    results.min_latency_ms = *std::min_element(results.latencies.begin(), results.latencies.end());
    results.max_latency_ms = *std::max_element(results.latencies.begin(), results.latencies.end());
    
    // Calculate percentiles
    std::sort(results.latencies.begin(), results.latencies.end());
    double p50 = results.latencies[results.latencies.size() * 50 / 100];
    double p95 = results.latencies[results.latencies.size() * 95 / 100];
    double p99 = results.latencies[results.latencies.size() * 99 / 100];
    
    // Print results
    std::cout << std::fixed << std::setprecision(3);
    std::cout << "Average RTT: " << results.avg_latency_ms << " ms" << std::endl;
    std::cout << "Min RTT: " << results.min_latency_ms << " ms" << std::endl;
    std::cout << "Max RTT: " << results.max_latency_ms << " ms" << std::endl;
    std::cout << "P50 RTT: " << p50 << " ms" << std::endl;
    std::cout << "P95 RTT: " << p95 << " ms" << std::endl;
    std::cout << "P99 RTT: " << p99 << " ms" << std::endl;
    
    agent1.stop();
    agent2.stop();
    
    return results;
}

// Benchmark 3: Multi-Agent Scalability
void benchmarkMultiAgent(const BenchmarkConfig& config) {
    std::cout << "\n========================================" << std::endl;
    std::cout << "Multi-Agent Scalability Benchmark" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Number of agents: " << config.num_agents << std::endl;
    std::cout << "Test duration: " << config.test_duration_sec << " seconds" << std::endl << std::endl;
    
    // Create multiple agents
    std::vector<std::unique_ptr<UACPAgent>> agents;
    std::vector<std::atomic<int>> message_counts(config.num_agents);
    
    for (int i = 0; i < config.num_agents; i++) {
        auto agent = std::make_unique<UACPAgent>(
            "agent" + std::to_string(i),
            "Agent " + std::to_string(i),
            "0.0.0.0",
            7300 + i
        );
        
        // Each agent counts received messages
        int agent_id = i;
        agent->addMessageHandler(UACPVerb::TELL,
            [&message_counts, agent_id](const UACPMessage& msg, const std::string&, int) {
                message_counts[agent_id]++;
                return msg.createResponse(StatusCode::SUCCESS);
            });
        
        agent->start();
        agents.push_back(std::move(agent));
    }
    
    std::this_thread::sleep_for(200ms);
    
    // Each agent sends to all others
    auto start_time = steady_clock::now();
    auto end_time = start_time + seconds(config.test_duration_sec);
    
    std::string payload = generatePayload(100);
    
    while (steady_clock::now() < end_time) {
        for (int i = 0; i < config.num_agents; i++) {
            for (int j = 0; j < config.num_agents; j++) {
                if (i != j) {
                    agents[i]->tell("127.0.0.1", 7300 + j, payload);
                }
            }
        }
        std::this_thread::sleep_for(100ms);
    }
    
    std::this_thread::sleep_for(500ms);  // Wait for remaining messages
    
    // Print results
    std::cout << "Results per agent:" << std::endl;
    uint64_t total_messages = 0;
    for (int i = 0; i < config.num_agents; i++) {
        auto stats = agents[i]->getStatistics();
        total_messages += stats["messages_received"];
        std::cout << "  Agent " << i << ": "
                  << "sent=" << stats["messages_sent"]
                  << ", received=" << stats["messages_received"]
                  << std::endl;
    }
    
    double duration_sec = config.test_duration_sec;
    double total_throughput = total_messages / duration_sec;
    
    std::cout << "\nTotal messages: " << total_messages << std::endl;
    std::cout << "Aggregate throughput: " << std::fixed << std::setprecision(2)
              << total_throughput << " msg/s" << std::endl;
    std::cout << "Per-agent throughput: " << (total_throughput / config.num_agents)
              << " msg/s" << std::endl;
    
    // Stop all agents
    for (auto& agent : agents) {
        agent->stop();
    }
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "µACP P2P Performance Benchmark" << std::endl;
    std::cout << "========================================" << std::endl;
    
    BenchmarkConfig config;
    
    // Test 1: Throughput (no QoS)
    config.num_messages = 1000;
    config.message_size = 100;
    config.use_qos = false;
    auto result1 = benchmarkThroughput(config);
    
    // Test 2: Throughput (with QoS)
    config.use_qos = true;
    auto result2 = benchmarkThroughput(config);
    
    // Test 3: Latency
    config.num_messages = 100;
    auto result3 = benchmarkLatency(config);
    
    // Test 4: Multi-agent (2 agents)
    config.num_agents = 2;
    config.test_duration_sec = 5;
    benchmarkMultiAgent(config);
    
    // Test 5: Multi-agent (5 agents)
    config.num_agents = 5;
    config.test_duration_sec = 5;
    benchmarkMultiAgent(config);
    
    // Summary
    std::cout << "\n========================================" << std::endl;
    std::cout << "Benchmark Summary" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Throughput (no QoS): " << std::fixed << std::setprecision(2)
              << result1.messages_per_sec << " msg/s" << std::endl;
    std::cout << "Throughput (with QoS): " << result2.messages_per_sec << " msg/s" << std::endl;
    std::cout << "Average Latency: " << std::setprecision(3)
              << result3.avg_latency_ms << " ms" << std::endl;
    std::cout << "========================================" << std::endl;
    
    return 0;
}
