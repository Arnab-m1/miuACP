"""
µACP Library Integration Test

Tests integration with various components and real-world scenarios.
"""

import asyncio
import time
import json
import socket
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from uacp_lib import (
    # Core Protocol
    UACPProtocol, UACPHeader, UACPOption, UACPOptionType, UACPVerb, UACPMessage,
    
    # Memory State Components
    UACPRouting, UACPSubscriptions, UACPReliability, UACPTimers, 
    UACPBroker, UACPInstrumentation, UACPResources,
    RouteType, LogLevel, MetricType,
    
    # Robustness Components
    CircuitBreaker, CircuitBreakerManager, CircuitBreakerConfig,
    AdaptiveTimeout, TimeoutManager, TimeoutConfig, TimeoutStrategy,
    ResourcePool, PoolManager, PoolConfig,
    RetryManager, ErrorRecoveryManager, RobustnessManager, RetryConfig,
    RetryStrategy, ErrorSeverity, retry_on_error,
    HealthMonitor, HealthCheck, CheckType, HealthStatus
)


class IntegrationTestSuite:
    """Integration test suite for µACP library."""
    
    def __init__(self):
        self.console = Console()
        self.test_results = []
        
    async def test_core_protocol_integration(self):
        """Test core protocol integration."""
        self.console.print("\n🔧 Testing Core Protocol Integration")
        
        try:
            # Create protocol instance
            uacp = UACPProtocol()
            
            # Test message creation
            message = uacp.create_message(
                verb=UACPVerb.TELL,
                payload="Hello, world!".encode(),
                msg_id=0x123456,
                options=[
                    UACPOption(UACPOptionType.TOPIC_PATH, "test/topic"),
                    UACPOption(UACPOptionType.CONTENT_TYPE, 0)
                ]
            )
            
            # Test message packing/unpacking
            packed = message.pack()
            unpacked = UACPMessage.unpack(packed)
            
            # Verify integrity
            assert message.header.verb == unpacked.header.verb
            assert message.payload == unpacked.payload
            assert message.header.msg_id == unpacked.header.msg_id
            
            self.test_results.append(("Core Protocol", "✅ PASS", "Message creation, packing, and unpacking"))
            self.console.print("   ✅ Core protocol integration successful")
            
        except Exception as e:
            self.test_results.append(("Core Protocol", "❌ FAIL", str(e)))
            self.console.print(f"   ❌ Core protocol integration failed: {e}")
    
    async def test_memory_state_integration(self):
        """Test memory state components integration."""
        self.console.print("\n🧠 Testing Memory State Components Integration")
        
        try:
            # Test routing integration
            routing = UACPRouting()
            routing.add_neighbor("agent_1", "192.168.1.100", 8080)
            routing.add_route("network_1", "gateway_1", 1.0, RouteType.DIRECT)
            
            # Test subscriptions integration
            subscriptions = UACPSubscriptions()
            subscriptions.create_subscription("sub_1", "sensors/*", "agent_1")
            subscriptions.create_dialogue("dialogue_1", "agent_1", "agent_2")
            
            # Test reliability integration
            reliability = UACPReliability()
            reliability.track_message("msg_1", "agent_1", 1, 30.0)
            reliability.add_block("msg_1", 0, b"block_data")
            
            # Test timers integration
            timers = UACPTimers()
            timer_id = timers.create_timer("timer_1", 5.0)
            timers.schedule_message("scheduled_msg", "agent_1", 2.0, 1)
            
            # Test broker integration
            broker = UACPBroker()
            broker.add_topic("sensors/temperature")
            broker.add_subscriber("sensors/temperature", "agent_1")
            
            # Test instrumentation integration
            instrumentation = UACPInstrumentation()
            instrumentation.log(LogLevel.INFO, "test_source", "Test log message")
            instrumentation.increment_counter("test_counter", 1)
            
            # Test resources integration
            resources = UACPResources()
            socket_id = resources.create_socket(socket.SOCK_STREAM, socket.AF_INET)
            dma_id = resources.allocate_dma_buffer("dma_1", 1024, "device_1")
            
            self.test_results.append(("Memory State", "✅ PASS", "All components integrated successfully"))
            self.console.print("   ✅ Memory state components integration successful")
            
        except Exception as e:
            self.test_results.append(("Memory State", "❌ FAIL", str(e)))
            self.console.print(f"   ❌ Memory state components integration failed: {e}")
    
    async def test_robustness_integration(self):
        """Test robustness features integration."""
        self.console.print("\n🛡️ Testing Robustness Features Integration")
        
        try:
            # Test circuit breaker integration
            cb_manager = CircuitBreakerManager()
            cb_manager.get_circuit_breaker("service_1")
            cb_manager.record_success("service_1")
            
            # Test adaptive timeout integration
            timeout_manager = TimeoutManager()
            timeout_manager.get_timeout("operation_1")
            timeout_manager.record_operation("operation_1", 5.0, True, 2.0)
            
            # Test resource pooling integration
            def create_resource():
                return f"resource_{time.time()}"
            
            pool = ResourcePool(create_resource, config=PoolConfig(min_size=2, max_size=10))
            resource = pool.acquire()
            if resource:
                pool.release(resource)
            
            # Test error recovery integration
            robustness_manager = RobustnessManager()
            
            @retry_on_error(RetryConfig(max_attempts=3))
            async def test_function():
                return "success"
            
            result = await test_function()
            assert result == "success"
            
            # Test health monitoring integration
            health_monitor = HealthMonitor()
            await health_monitor.start()
            
            # Add custom health check
            async def test_health_check():
                return True
            
            health_monitor.add_health_check_by_params(
                check_id="test_check",
                name="Test Health Check",
                description="Test health check for integration testing",
                check_func=test_health_check,
                check_type=CheckType.CUSTOM
            )
            
            await health_monitor.stop()
            
            self.test_results.append(("Robustness", "✅ PASS", "All robustness features integrated successfully"))
            self.console.print("   ✅ Robustness features integration successful")
            
        except Exception as e:
            self.test_results.append(("Robustness", "❌ FAIL", str(e)))
            self.console.print(f"   ❌ Robustness features integration failed: {e}")
    
    async def test_real_world_scenario(self):
        """Test real-world multi-agent communication scenario."""
        self.console.print("\n🌍 Testing Real-World Multi-Agent Scenario")
        
        try:
            # Simulate multi-agent communication
            agents = {}
            messages = []
            
            # Create agents with different capabilities
            for i in range(5):
                agent_id = f"agent_{i}"
                
                # Initialize routing
                routing = UACPRouting()
                routing.add_neighbor(agent_id, f"192.168.1.{100+i}", 8080+i)
                
                # Initialize subscriptions
                subscriptions = UACPSubscriptions()
                subscriptions.create_subscription(f"sub_{i}", f"sensors/agent_{i}/*", agent_id)
                
                # Initialize reliability
                reliability = UACPReliability()
                
                # Initialize timers
                timers = UACPTimers()
                
                # Initialize broker
                broker = UACPBroker()
                broker.add_topic(f"sensors/agent_{i}/temperature")
                broker.add_subscriber(f"sensors/agent_{i}/temperature", agent_id)
                
                # Initialize instrumentation
                instrumentation = UACPInstrumentation()
                
                # Initialize resources
                resources = UACPResources()
                
                agents[agent_id] = {
                    'routing': routing,
                    'subscriptions': subscriptions,
                    'reliability': reliability,
                    'timers': timers,
                    'broker': broker,
                    'instrumentation': instrumentation,
                    'resources': resources
                }
            
            # Simulate message exchange
            uacp = UACPProtocol()
            
            for i in range(10):
                # Agent sends temperature reading
                sender = f"agent_{i % 5}"
                message = uacp.create_message(
                    verb=UACPVerb.TELL,
                    payload=f"Temperature: {20 + i}°C".encode(),
                    msg_id=i,
                    options=[
                        UACPOption(UACPOptionType.TOPIC_PATH, f"sensors/{sender}/temperature"),
                        UACPOption(UACPOptionType.CONTENT_TYPE, 0)
                    ]
                )
                
                # Track message for reliability
                agents[sender]['reliability'].track_message(f"msg_{i}", sender, 1, 30.0)
                
                # Log message
                agents[sender]['instrumentation'].log(
                    LogLevel.INFO, 
                    sender,
                    f"Sent temperature reading: {20 + i}°C"
                )
                
                # Record metric
                agents[sender]['instrumentation'].increment_counter(
                    "messages_sent", 1
                )
                
                messages.append(message)
            
            # Simulate message processing
            for message in messages:
                # Parse message
                parsed = UACPMessage.unpack(message.pack())
                
                # Extract topic
                topic_opt = next((opt for opt in parsed.options if opt.type == UACPOptionType.TOPIC_PATH), None)
                if topic_opt:
                    topic = topic_opt.value
                    
                    # Find subscribers
                    for agent_id, agent_data in agents.items():
                        subscribers = agent_data['broker'].get_subscribers(topic)
                        if agent_id in subscribers:
                            # Process message
                            agent_data['instrumentation'].log(
                                LogLevel.INFO,
                                agent_id,
                                f"Received message on topic: {topic}"
                            )
                            agent_data['instrumentation'].increment_counter(
                                "messages_received", 1
                            )
            
            self.test_results.append(("Real-World Scenario", "✅ PASS", "Multi-agent communication successful"))
            self.console.print("   ✅ Real-world multi-agent scenario successful")
            
        except Exception as e:
            self.test_results.append(("Real-World Scenario", "❌ FAIL", str(e)))
            self.console.print(f"   ❌ Real-world scenario failed: {e}")
    
    def display_results(self):
        """Display integration test results."""
        table = Table(title="µACP Library Integration Test Results")
        
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="green")
        
        for component, status, details in self.test_results:
            table.add_row(component, status, details)
        
        self.console.print(table)
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, status, _ in self.test_results if status == "✅ PASS")
        failed_tests = total_tests - passed_tests
        
        self.console.print(f"\n📊 Test Summary:")
        self.console.print(f"   Total Tests: {total_tests}")
        self.console.print(f"   Passed: {passed_tests} ✅")
        self.console.print(f"   Failed: {failed_tests} ❌")
        self.console.print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests == 0:
            self.console.print("\n🎉 All integration tests passed! µACP library is fully functional.")
        else:
            self.console.print(f"\n⚠️  {failed_tests} test(s) failed. Please check the details above.")
    
    async def run_all_tests(self):
        """Run all integration tests."""
        self.console.print(Panel.fit("🚀 µACP Library Integration Test Suite", style="bold blue"))
        self.console.print("Testing integration of all components and real-world scenarios.")
        
        try:
            # Run all tests
            await self.test_core_protocol_integration()
            await self.test_memory_state_integration()
            await self.test_robustness_integration()
            await self.test_real_world_scenario()
            
            # Display results
            self.display_results()
            
        except Exception as e:
            self.console.print(f"\n❌ Integration test suite failed with error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main integration test execution."""
    test_suite = IntegrationTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
