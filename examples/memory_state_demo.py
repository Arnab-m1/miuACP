#!/usr/bin/env python3
"""
µACP Memory State Components Demo

This demo showcases all the memory state components:
1. Routing & Addressing State
2. Subscription & Dialogue State  
3. Reliability & QoS State
4. Timers & Scheduling State
5. Broker & Middleware State
6. Instrumentation & Control State
7. Resource Binding State
"""

import asyncio
import time
import uuid
import socket
from uacp_lib import (
    # Memory state components
    UACPRouting, RouteType, NATState,
    UACPSubscriptions, SubscriptionState, DialogueState, CorrelationState, ContractState,
    UACPReliability, QoSLevel, MessageState,
    UACPTimers, TimerType, TimerState, MessagePriority,
    UACPBroker, BrokerNodeType, MessageRetention, LoadBalancerStrategy,
    UACPInstrumentation, LogLevel, MetricType, PolicyType,
    UACPResources, ResourceType, ResourceState
)


async def demo_routing():
    """Demo routing and addressing state management."""
    print("\n🔀 === ROUTING & ADDRESSING STATE ===")
    
    routing = UACPRouting()
    await routing.start()
    
    # Add neighbors
    routing.add_neighbor("agent1", "192.168.1.10", 8080, RouteType.DIRECT)
    routing.add_neighbor("agent2", "192.168.1.11", 8080, RouteType.NAT_MAPPED)
    routing.add_neighbor("agent3", "10.0.0.5", 9090, RouteType.FORWARDED)
    
    # Join multicast groups
    routing.join_multicast_group("224.0.0.1", 8080, "agent1")
    routing.join_multicast_group("224.0.0.1", 8080, "agent2")
    
    # Add NAT mappings
    routing.add_nat_mapping("192.168.1.10", 8080, "203.0.113.1", 12345, "agent1")
    
    # Add routes
    routing.add_route("network1", "192.168.1.1", 1.0, RouteType.DIRECT)
    routing.add_route("network2", "10.0.0.1", 2.0, RouteType.FORWARDED)
    
    print(f"   📍 Neighbors: {len(routing.neighbors)}")
    print(f"   🌐 Multicast groups: {len(routing.multicast_groups)}")
    print(f"   🛣️  Routes: {len(routing.routing_table)}")
    print(f"   🔄 NAT mappings: {len(routing.nat_mappings)}")
    
    # Export state
    state = routing.export_state()
    print(f"   📊 Stats: {state['stats']}")
    
    await routing.stop()


async def demo_subscriptions():
    """Demo subscription and dialogue state management."""
    print("\n📡 === SUBSCRIPTION & DIALOGUE STATE ===")
    
    subs = UACPSubscriptions()
    await subs.start()
    
    # Create subscriptions
    subs.create_subscription("sensors/temperature", "agent1", qos=1)
    subs.create_subscription("sensors/humidity", "agent1", qos=0)
    subs.create_subscription("alerts/*", "agent2", qos=2)
    subs.create_subscription("control/+/status", "agent3", qos=1)
    
    # Create dialogues
    dialogue1 = subs.create_dialogue("conv_001", "agent1", {"agent2", "agent3"})
    dialogue2 = subs.create_dialogue("conv_002", "agent2", {"agent1"})
    
    # Create correlations
    corr1 = subs.create_correlation("msg_001", "agent1", "agent2")
    corr2 = subs.create_correlation("msg_002", "agent2", "agent1")
    
    # Create contracts
    contract1 = subs.create_contract("task_assignment", "agent1", {"agent2", "agent3"}, 
                                   {"task": "monitor_sensors"}, time.time() + 3600)
    
    print(f"   📋 Subscriptions: {len(subs.subscriptions)}")
    print(f"   💬 Dialogues: {len(subs.dialogues)}")
    print(f"   🔗 Correlations: {len(subs.correlations)}")
    print(f"   📜 Contracts: {len(subs.contracts)}")
    
    # Get subscribers for topics
    temp_subs = subs.get_subscribers_for_topic("sensors/temperature")
    alert_subs = subs.get_subscribers_for_topic("alerts/fire")
    print(f"   🌡️  Temperature subscribers: {temp_subs}")
    print(f"   🚨 Alert subscribers: {alert_subs}")
    
    await subs.stop()


async def demo_reliability():
    """Demo reliability and QoS state management."""
    print("\n🔄 === RELIABILITY & QoS STATE ===")
    
    reliability = UACPReliability()
    await reliability.start()
    
    # Track messages
    reliability.track_message("msg_001", QoSLevel.AT_LEAST_ONCE, "agent2", 1024)
    reliability.track_message("msg_002", QoSLevel.EXACTLY_ONCE, "agent3", 2048)
    reliability.track_message("msg_003", QoSLevel.AT_MOST_ONCE, "agent1", 512)
    
    # Create reassembly buffers
    reliability.create_reassembly_buffer("transfer_001", 5)
    reliability.add_block("transfer_001", 0, b"block0")
    reliability.add_block("transfer_001", 2, b"block2")
    reliability.add_block("transfer_001", 1, b"block1")
    
    # Create sliding windows
    reliability.create_sliding_window("window_001", 10)
    reliability.send_packet("window_001", 1)
    reliability.send_packet("window_001", 2)
    reliability.receive_ack("window_001", 1)
    
    # Check duplicates
    is_dup1 = reliability.is_duplicate("msg_001")
    is_dup2 = reliability.is_duplicate("msg_001")  # Should be duplicate
    
    print(f"   📨 Message trackers: {len(reliability.message_trackers)}")
    print(f"   🧩 Reassembly buffers: {len(reliability.reassembly_buffers)}")
    print(f"   📊 Sliding windows: {len(reliability.sliding_windows)}")
    print(f"   🔄 Duplicate check: {is_dup1}, {is_dup2}")
    
    # Update message states
    reliability.update_message_state("msg_001", MessageState.ACKED)
    reliability.update_message_state("msg_002", MessageState.DELIVERED)
    
    print(f"   📊 Stats: {reliability.get_stats()}")
    
    await reliability.stop()


async def demo_timers():
    """Demo timer and scheduling state management."""
    print("\n⏰ === TIMERS & SCHEDULING STATE ===")
    
    timers = UACPTimers()
    await timers.start()
    
    # Create different types of timers
    retry_timer = timers.create_retransmission_timer("msg_001", 30.0)
    heartbeat_timer = timers.create_heartbeat_timer("agent1", 60.0)
    session_timer = timers.create_session_timer("session_001", "agent1", 300.0)
    
    # Schedule messages
    msg1 = timers.schedule_message({"type": "alert", "level": "high"}, "agent2", 
                                 MessagePriority.CRITICAL, delay=5.0)
    msg2 = timers.schedule_message({"type": "status", "level": "normal"}, "agent3", 
                                 MessagePriority.NORMAL, delay=10.0)
    
    # Create additional session timers
    session2 = timers.create_session_timer("session_002", "agent2", 600.0)
    
    print(f"   ⏱️  Active timers: {len(timers.timers)}")
    print(f"   📅 Scheduled messages: {len(timers.scheduled_messages)}")
    print(f"   🔐 Session timers: {len(timers.session_timers)}")
    
    # Get next message
    next_msg = timers.get_next_message()
    if next_msg:
        print(f"   📤 Next message: {next_msg.message_data}")
    
    # Update session activity
    timers.update_session_activity("session_001")
    
    print(f"   📊 Stats: {timers.get_stats()}")
    
    await timers.stop()


async def demo_broker():
    """Demo broker and middleware state management."""
    print("\n🏪 === BROKER & MIDDLEWARE STATE ===")
    
    broker = UACPBroker()
    await broker.start()
    
    # Add subscribers to topics
    broker.add_subscriber("sensors/temperature", "agent1")
    broker.add_subscriber("sensors/temperature", "agent2")
    broker.add_subscriber("sensors/humidity", "agent1")
    broker.add_subscriber("alerts/*", "agent3")
    broker.add_subscriber("control/+/status", "agent2")
    
    # Store retained messages
    broker.store_retained_message("sensors/temperature", "msg_001", b"25.5C", 1)
    broker.store_retained_message("sensors/humidity", "msg_002", b"60%", 1)
    broker.store_retained_message("alerts/fire", "msg_003", b"FIRE_ALERT", 2)
    
    # Create flow control credits
    broker.create_flow_credit("conn_001", "agent1", 100, 10.0)
    broker.create_flow_credit("conn_002", "agent2", 50, 5.0)
    
    # Add load balancer targets
    broker.add_load_balancer_target("target_001", "192.168.1.10", 8080, weight=2)
    broker.add_load_balancer_target("target_002", "192.168.1.11", 8080, weight=1)
    
    # Map connections
    broker.map_connection("conn_001", "agent1", "target_001", sticky=True)
    broker.map_connection("conn_002", "agent2", "target_002")
    
    print(f"   📡 Topics: {len(broker.topic_cache)}")
    print(f"   💾 Retained messages: {len(broker.retained_messages)}")
    print(f"   💳 Flow credits: {len(broker.flow_credits)}")
    print(f"   ⚖️  Load balancer targets: {len(broker.load_balancer_targets)}")
    print(f"   🔗 Connection mappings: {len(broker.connection_mappings)}")
    
    # Get subscribers for topics
    temp_subs = broker.get_subscribers("sensors/temperature")
    alert_subs = broker.get_subscribers("alerts/fire")
    print(f"   🌡️  Temperature subscribers: {temp_subs}")
    print(f"   🚨 Alert subscribers: {alert_subs}")
    
    # Get topic tree
    topic_tree = broker.get_topic_tree()
    print(f"   🌳 Topic tree depth: {len(str(topic_tree))}")
    
    print(f"   📊 Stats: {broker.get_stats()}")
    
    await broker.stop()


async def demo_instrumentation():
    """Demo instrumentation and control state management."""
    print("\n📊 === INSTRUMENTATION & CONTROL STATE ===")
    
    inst = UACPInstrumentation()
    await inst.start()
    
    # Log messages
    inst.info("demo", "Starting instrumentation demo")
    inst.warning("demo", "This is a warning message")
    inst.error("demo", "This is an error message")
    
    # Update metrics
    inst.increment_counter("messages.sent", 10)
    inst.increment_counter("messages.received", 8)
    inst.set_gauge("system.memory.used", 1024 * 1024 * 100)  # 100MB
    inst.record_histogram("latency.request_response", 150.5)
    inst.record_histogram("latency.request_response", 200.3)
    inst.record_histogram("latency.request_response", 125.7)
    
    # Create traces
    trace1 = inst.start_trace("http_request", "web_server")
    inst.add_trace_event(trace1, "request_received", {"method": "GET", "path": "/api/data"})
    inst.add_trace_event(trace1, "database_query", {"table": "users", "query": "SELECT *"})
    inst.end_trace(trace1, {"status": "success", "duration_ms": 45})
    
    # Add policies
    rate_limit_policy = inst.add_policy(
        PolicyType.RATE_LIMIT, "api_rate_limit", "Limit API requests per minute",
        {"requests_per_minute": {"max": 100}},
        [{"action": "throttle", "delay": 60}]
    )
    
    quota_policy = inst.add_policy(
        PolicyType.QUOTA, "storage_quota", "Limit storage usage",
        {"storage_mb": {"max": 1024}},
        [{"action": "reject", "message": "Storage quota exceeded"}]
    )
    
    # Create quotas
    inst.create_quota("api_requests", 1000, 3600)  # 1000 requests per hour
    inst.create_quota("storage_mb", 1024, 86400)   # 1GB per day
    
    # Evaluate policies
    api_context = {"requests_per_minute": 50, "user_id": "user123"}
    api_result = inst.evaluate_policy(PolicyType.RATE_LIMIT, api_context)
    
    storage_context = {"storage_mb": 2048, "user_id": "user456"}
    storage_result = inst.evaluate_policy(PolicyType.QUOTA, storage_context)
    
    print(f"   📝 Log entries: {len(inst.log_buffer)}")
    print(f"   📊 Metrics: {len(inst.metrics)}")
    print(f"   🔍 Traces: {len(inst.trace_contexts)}")
    print(f"   📋 Policies: {len(inst.policies)}")
    print(f"   🎯 Quotas: {len(inst.quotas)}")
    
    print(f"   🔒 API policy result: {api_result['allowed']}")
    print(f"   💾 Storage policy result: {storage_result['allowed']}")
    
    # Check quotas
    api_quota = inst.check_quota("api_requests", 10)
    storage_quota = inst.check_quota("storage_mb", 100)
    print(f"   🎯 API quota check: {api_quota}")
    print(f"   💾 Storage quota check: {storage_quota}")
    
    print(f"   📊 Stats: {inst.get_stats()}")
    
    await inst.stop()


async def demo_resources():
    """Demo resource binding state management."""
    print("\n🔧 === RESOURCE BINDING STATE ===")
    
    resources = UACPResources()
    await resources.start()
    
    # Create socket resources
    socket1 = resources.create_socket(socket.SOCK_STREAM, socket.AF_INET)
    socket2 = resources.create_socket(socket.SOCK_DGRAM, socket.AF_INET)
    
    # Bind and connect sockets
    resources.bind_socket(socket1, ("0.0.0.0", 8080))
    resources.connect_socket(socket2, ("192.168.1.10", 9090))
    
    # Allocate DMA buffers
    dma1 = resources.allocate_dma_buffer(4096, "nic_001")
    dma2 = resources.allocate_dma_buffer(8192, "nic_001")
    dma3 = resources.allocate_dma_buffer(2048, "nic_002")
    
    # Create crypto contexts
    crypto1 = resources.create_crypto_context("AES-256", 256, "crypto_accel_001")
    crypto2 = resources.create_crypto_context("RSA-2048", 2048, "crypto_accel_002")
    
    # Open storage handles
    storage1 = resources.open_storage("file", "/tmp/data.log", "w")
    storage2 = resources.open_storage("file", "/var/log/system.log", "r")
    
    print(f"   🔌 Sockets: {len(resources.sockets)}")
    print(f"   💾 DMA buffers: {len(resources.dma_buffers)}")
    print(f"   🔐 Crypto contexts: {len(resources.crypto_contexts)}")
    print(f"   📁 Storage handles: {len(resources.storage_handles)}")
    print(f"   🔧 Total resources: {len(resources.resources)}")
    
    # Get resource status
    socket_info = resources.get_resource(socket1)
    dma_info = resources.get_dma_buffer(dma1)
    crypto_info = resources.get_crypto_context(crypto1)
    storage_info = resources.get_storage_handle(storage1)
    
    print(f"   📊 Socket resource: {socket_info.resource_type if socket_info else 'N/A'}")
    print(f"   💾 DMA buffer size: {dma_info.size if dma_info else 'N/A'}")
    print(f"   🔐 Crypto algorithm: {crypto_info.algorithm if crypto_info else 'N/A'}")
    print(f"   📁 Storage path: {storage_info.path if storage_info else 'N/A'}")
    
    print(f"   📊 Stats: {resources.get_stats()}")
    
    await resources.stop()


async def main():
    """Main demo function."""
    print("🚀 µACP Memory State Components Demo")
    print("=" * 50)
    
    try:
        await demo_routing()
        await demo_subscriptions()
        await demo_reliability()
        await demo_timers()
        await demo_broker()
        await demo_instrumentation()
        await demo_resources()
        
        print("\n✅ All memory state components demo completed successfully!")
        print("\n📋 Summary of implemented components:")
        print("   1. ✅ Routing & Addressing State")
        print("   2. ✅ Subscription & Dialogue State")
        print("   3. ✅ Reliability & QoS State")
        print("   4. ✅ Timers & Scheduling State")
        print("   5. ✅ Broker & Middleware State")
        print("   6. ✅ Instrumentation & Control State")
        print("   7. ✅ Resource Binding State")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
