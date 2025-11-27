"""
µACP Robustness Features Demo

Demonstrates all the new robustness components:
- Circuit Breaker Pattern
- Adaptive Timeouts
- Resource Pooling
- Error Recovery
- Health Monitoring
"""

import asyncio
import time
import random
import socket
from uacp_lib import (
    # Robustness Components
    CircuitBreaker, CircuitBreakerManager, CircuitBreakerConfig,
    AdaptiveTimeout, TimeoutManager, TimeoutConfig, TimeoutStrategy,
    ResourcePool, PoolManager, PoolConfig,
    RetryManager, ErrorRecoveryManager, RobustnessManager, RetryConfig,
    RetryStrategy, ErrorSeverity, retry_on_error, RecoveryAction,
    HealthMonitor, HealthCheck, CheckType, HealthStatus
)


async def demo_circuit_breaker():
    """Demo circuit breaker pattern for robust failure handling."""
    print("\n🔌 === CIRCUIT BREAKER PATTERN ===")
    
    # Create circuit breaker manager
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=10.0,
        success_threshold=2
    )
    cb_manager = CircuitBreakerManager(config)
    await cb_manager.start()
    
    # Simulate unreliable service
    async def unreliable_service():
        if random.random() < 0.7:  # 70% failure rate
            raise Exception("Service temporarily unavailable")
        return "Service response"
    
    # Test circuit breaker behavior
    destination = "unreliable_service"
    print(f"   🎯 Testing circuit breaker for: {destination}")
    
    for attempt in range(5):
        try:
            if cb_manager.is_destination_available(destination):
                result = await unreliable_service()
                cb_manager.record_success(destination)
                print(f"   ✅ Attempt {attempt + 1}: Success - {result}")
            else:
                print(f"   🚫 Attempt {attempt + 1}: Circuit OPEN - Service unavailable")
        except Exception as e:
            cb_manager.record_failure(destination)
            print(f"   ❌ Attempt {attempt + 1}: Failed - {e}")
        
        await asyncio.sleep(1)
    
    # Show circuit breaker status
    status = cb_manager.get_all_status()
    print(f"   📊 Circuit breaker status: {status[destination]['state']}")
    print(f"   📈 Metrics: {status[destination]['metrics']}")
    
    await cb_manager.stop()


async def demo_adaptive_timeout():
    """Demo adaptive timeout management."""
    print("\n⏰ === ADAPTIVE TIMEOUT MANAGEMENT ===")
    
    # Create timeout manager
    config = TimeoutConfig(
        base_timeout=5.0,
        min_timeout=1.0,
        max_timeout=30.0,
        strategy=TimeoutStrategy.HYBRID
    )
    timeout_manager = TimeoutManager(config)
    await timeout_manager.start()
    
    # Simulate operations with varying response times
    async def operation_with_delay(operation_name: str, delay: float):
        await asyncio.sleep(delay)
        return f"Operation {operation_name} completed"
    
    # Test different operations
    operations = [
        ("fast_op", 0.5),
        ("medium_op", 2.0),
        ("slow_op", 8.0),
        ("timeout_op", 15.0)
    ]
    
    for op_name, delay in operations:
        timeout = timeout_manager.get_timeout_value(op_name)
        print(f"   🎯 {op_name}: Current timeout = {timeout:.2f}s")
        
        try:
            start_time = time.time()
            result = await asyncio.wait_for(
                operation_with_delay(op_name, delay),
                timeout=timeout
            )
            response_time = time.time() - start_time
            
            # Record successful operation
            timeout_manager.record_operation(
                op_name, timeout, True, response_time
            )
            print(f"   ✅ {op_name}: Completed in {response_time:.2f}s")
            
        except asyncio.TimeoutError:
            # Record failed operation
            timeout_manager.record_operation(
                op_name, timeout, False, timeout
            )
            print(f"   ❌ {op_name}: Timed out after {timeout:.2f}s")
    
    # Show timeout statistics
    stats = timeout_manager.get_all_statistics()
    print(f"   📊 Timeout statistics:")
    for op_name, op_stats in stats.items():
        print(f"      {op_name}: {op_stats['current_timeout']:.2f}s, "
              f"Success rate: {op_stats['success_rate']:.2%}")
    
    await timeout_manager.stop()


async def demo_resource_pooling():
    """Demo resource pooling for efficient resource management."""
    print("\n🏊 === RESOURCE POOLING ===")
    
    # Create resource pool manager
    pool_manager = PoolManager()
    await pool_manager.start()
    
    # Create a connection pool
    def create_connection():
        """Factory function to create a connection."""
        return f"connection_{random.randint(1000, 9999)}"
    
    def cleanup_connection(conn):
        """Cleanup function for connections."""
        pass  # In real implementation, close connection
    
    def health_check_connection(conn):
        """Health check for connections."""
        return random.random() > 0.1  # 90% healthy
    
    # Create connection pool
    pool_config = PoolConfig(
        min_size=2,
        max_size=10,
        initial_size=3,
        acquire_timeout=5.0
    )
    
    connection_pool = ResourcePool(
        resource_factory=create_connection,
        resource_cleanup=cleanup_connection,
        resource_health_check=health_check_connection,
        config=pool_config
    )
    
    pool_manager.create_pool("connections", connection_pool)
    
    # Simulate multiple clients using the pool
    async def client_work(client_id: int):
        """Simulate client work using pooled resources."""
        print(f"   👤 Client {client_id}: Acquiring connection...")
        
        connection = connection_pool.acquire(timeout=2.0)
        if connection:
            print(f"   🔌 Client {client_id}: Got connection {connection}")
            
            # Simulate work
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Release connection
            connection_pool.release(connection)
            print(f"   🔓 Client {client_id}: Released connection {connection}")
        else:
            print(f"   ❌ Client {client_id}: Failed to acquire connection")
    
    # Run multiple clients concurrently
    clients = [client_work(i) for i in range(8)]
    await asyncio.gather(*clients)
    
    # Show pool statistics
    stats = pool_manager.get_all_statistics()
    print(f"   📊 Pool statistics:")
    for pool_name, pool_stats in stats.items():
        metrics = pool_stats['metrics']
        print(f"      {pool_name}: {metrics['current_available']} available, "
              f"{metrics['current_in_use']} in use, "
              f"{metrics['current_total']} total")
    
    await pool_manager.stop()


async def demo_error_recovery():
    """Demo error recovery and retry mechanisms."""
    print("\n🔄 === ERROR RECOVERY & RETRY ===")
    
    # Create robustness manager
    robustness_manager = RobustnessManager()
    await robustness_manager.start()
    
    # Test retry decorator
    @retry_on_error(RetryConfig(
        max_attempts=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=1.0
    ))
    async def unreliable_operation():
        """An operation that might fail."""
        if random.random() < 0.8:  # 80% failure rate
            raise Exception("Operation failed")
        return "Operation succeeded"
    
    # Test the retry mechanism
    print("   🎯 Testing retry mechanism...")
    try:
        result = await unreliable_operation()
        print(f"   ✅ Final result: {result}")
    except Exception as e:
        print(f"   ❌ All retries exhausted: {e}")
    
    # Test error recovery manager
    recovery_manager = robustness_manager.error_recovery_manager
    
    # Register recovery actions
    async def restart_service(context):
        print(f"   🔄 Restarting service with context: {context}")
        await asyncio.sleep(0.5)
        return True
    
    async def fallback_service(context):
        print(f"   🆘 Using fallback service with context: {context}")
        await asyncio.sleep(0.3)
        return True
    
    # Register actions
    recovery_manager.register_recovery_action(
        RecoveryAction(
            action_id="restart_service",
            action_type="restart",
            description="Restart the failed service",
            execute_func=restart_service,
            priority=1
        )
    )
    
    recovery_manager.register_recovery_action(
        RecoveryAction(
            action_id="fallback_service",
            action_type="fallback",
            description="Use fallback service",
            execute_func=fallback_service,
            priority=2
        )
    )
    
    # Register fallback strategy
    recovery_manager.register_fallback_strategy(
        "critical_operation",
        ["restart_service", "fallback_service"]
    )
    
    # Test fallback strategy
    print("   🎯 Testing fallback strategy...")
    success = await recovery_manager.execute_fallback_strategy(
        "critical_operation",
        {"operation": "data_processing", "priority": "high"}
    )
    print(f"   📊 Fallback strategy result: {success}")
    
    # Show recovery statistics
    stats = robustness_manager.get_robustness_statistics()
    print(f"   📊 Recovery statistics:")
    print(f"      Retry: {stats['retry_statistics']}")
    print(f"      Recovery: {stats['recovery_statistics']}")
    
    await robustness_manager.stop()


async def demo_health_monitoring():
    """Demo comprehensive health monitoring."""
    print("\n🏥 === HEALTH MONITORING ===")
    
    # Create health monitor
    health_monitor = HealthMonitor()
    await health_monitor.start()
    
    # Add custom health checks
    async def network_connectivity_check():
        """Check network connectivity."""
        try:
            # Try to connect to a known host
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except Exception:
            return False
    
    async def service_health_check():
        """Check service health."""
        # Simulate service check
        await asyncio.sleep(0.1)
        return random.random() > 0.2  # 80% healthy
    
    # Register custom checks
    health_monitor.add_health_check(
        HealthCheck(
            check_id="network_connectivity",
            name="Network Connectivity",
            description="Check if network is accessible",
            check_type=CheckType.NETWORK,
            check_func=network_connectivity_check,
            timeout=10.0,
            interval=30.0,
            critical=True
        )
    )
    
    health_monitor.add_health_check(
        HealthCheck(
            check_id="service_health",
            name="Service Health",
            description="Check service health status",
            check_type=CheckType.SERVICE,
            check_func=service_health_check,
            timeout=15.0,
            interval=60.0,
            critical=False
        )
    )
    
    # Test performance profiling
    print("   🎯 Testing performance profiling...")
    
    for i in range(5):
        # Start profiling
        start_time = health_monitor.start_profiling("test_operation")
        
        # Simulate operation
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # End profiling
        success = random.random() > 0.3  # 70% success rate
        health_monitor.end_profiling("test_operation", start_time, success)
    
    # Wait for health checks to run
    await asyncio.sleep(2)
    
    # Get health status
    status = health_monitor.get_health_status()
    print(f"   📊 Overall health: {status['overall_health']}")
    print(f"   🔍 Health checks: {len(status['health_checks'])}")
    print(f"   📈 Performance profiles: {len(status['performance_profiles'])}")
    
    # Show system metrics
    system_metrics = health_monitor.get_system_metrics(duration_minutes=1)
    if system_metrics:
        latest = system_metrics[-1]
        print(f"   💻 System metrics:")
        print(f"      CPU: {latest.cpu_percent:.1f}%")
        print(f"      Memory: {latest.memory_percent:.1f}%")
        print(f"      Disk: {latest.disk_usage_percent:.1f}%")
    
    await health_monitor.stop()


async def main():
    """Main demo function."""
    print("🚀 µACP Robustness Features Demo")
    print("=" * 60)
    print("This demo showcases all the new robustness components")
    print("that make µACP comparable to A2A/MCP libraries for")
    print("lightweight AI agent communications.")
    print("=" * 60)
    
    try:
        await demo_circuit_breaker()
        await demo_adaptive_timeout()
        await demo_resource_pooling()
        await demo_error_recovery()
        await demo_health_monitoring()
        
        print("\n✅ All robustness features demo completed successfully!")
        print("\n📋 Summary of implemented robustness components:")
        print("   1. ✅ Circuit Breaker Pattern - Robust failure handling")
        print("   2. ✅ Adaptive Timeouts - Intelligent timeout management")
        print("   3. ✅ Resource Pooling - Efficient resource management")
        print("   4. ✅ Error Recovery - Advanced retry and fallback strategies")
        print("   5. ✅ Health Monitoring - Comprehensive system monitoring")
        print("\n🎯 µACP is now production-ready with enterprise-grade robustness!")
        print("   Comparable to A2A/MCP libraries while maintaining lightweight design.")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
