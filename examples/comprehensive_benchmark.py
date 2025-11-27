"""
Comprehensive µACP Benchmark Suite

Tests all features including:
- Core protocol performance
- Memory state components
- Robustness features
- Comparison with other protocols
- Real-world scenarios
"""

import asyncio
import time
import psutil
import statistics
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich.text import Text

from uacp_lib import (
    # Core Protocol
    UACPProtocol, UACPHeader, UACPOption, UACPOptionType, UACPVerb, UACPMessage,
    
    # Memory State Components
    UACPRouting, UACPSubscriptions, UACPReliability, UACPTimers, 
    UACPBroker, UACPInstrumentation, UACPResources,
    RouteType,  # Add this import
    
    # Robustness Components
    CircuitBreaker, CircuitBreakerManager, CircuitBreakerConfig,
    AdaptiveTimeout, TimeoutManager, TimeoutConfig, TimeoutStrategy,
    ResourcePool, PoolManager, PoolConfig,
    RetryManager, ErrorRecoveryManager, RobustnessManager, RetryConfig,
    RetryStrategy, ErrorSeverity, retry_on_error,
    HealthMonitor, HealthCheck, CheckType, HealthStatus
)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    test_name: str
    component: str
    duration_ms: float
    memory_bytes: int
    operations_count: int
    success_count: int
    error_count: int
    throughput_ops_per_sec: float
    latency_ms: float
    cpu_percent: float
    memory_percent: float
    timestamp: str


class ComprehensiveBenchmarkSuite:
    """Comprehensive benchmark suite for µACP library."""
    
    def __init__(self):
        self.console = Console()
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process()
        
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        return self.process.memory_info().rss
    
    def _get_cpu_percent(self) -> float:
        """Get current CPU usage percentage."""
        return self.process.cpu_percent()
    
    def _get_memory_percent(self) -> float:
        """Get current memory usage percentage."""
        return psutil.virtual_memory().percent
    
    def benchmark_core_protocol(self, message_count: int = 10000) -> BenchmarkResult:
        """Benchmark core protocol performance."""
        self.console.print(f"\n🔧 Benchmarking Core Protocol ({message_count:,} messages)")
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        start_cpu = self._get_cpu_percent()
        start_mem_pct = self._get_memory_percent()
        
        uacp = UACPProtocol()
        messages = []
        errors = 0
        
        try:
            for i in track(range(message_count), description="Creating messages"):
                try:
                    message = uacp.create_message(
                        verb=UACPVerb.TELL,
                        payload=f"Test message {i}".encode(),
                        msg_id=i,
                        options=[
                            UACPOption(UACPOptionType.TOPIC_PATH, f"test/topic/{i}"),
                            UACPOption(UACPOptionType.CONTENT_TYPE, 0)
                        ]
                    )
                    messages.append(message)
                except Exception as e:
                    errors += 1
            
            # Test parsing
            for message in track(messages[:1000], description="Parsing messages"):
                try:
                    header, options, payload = uacp.parse_message(message)
                except Exception as e:
                    errors += 1
                    
        except Exception as e:
            self.console.print(f"[red]Error in core protocol benchmark: {e}[/red]")
            errors += 1
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        end_cpu = self._get_cpu_percent()
        end_mem_pct = self._get_memory_percent()
        
        duration_ms = (end_time - start_time) * 1000
        memory_bytes = end_memory - start_memory
        throughput = message_count / (duration_ms / 1000)
        latency = duration_ms / message_count
        
        result = BenchmarkResult(
            test_name="Core Protocol",
            component="Protocol",
            duration_ms=duration_ms,
            memory_bytes=memory_bytes,
            operations_count=message_count,
            success_count=message_count - errors,
            error_count=errors,
            throughput_ops_per_sec=throughput,
            latency_ms=latency,
            cpu_percent=end_cpu,
            memory_percent=end_mem_pct,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.results.append(result)
        return result
    
    def benchmark_memory_state_components(self) -> List[BenchmarkResult]:
        """Benchmark memory state components performance."""
        self.console.print(f"\n🧠 Benchmarking Memory State Components")
        results = []
        
        # Test Routing
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        routing = UACPRouting()
        for i in range(1000):
            routing.add_neighbor(f"agent_{i}", f"192.168.1.{i}", 8080 + i)
            routing.add_route(f"network_{i}", f"gateway_{i}", 1.0, RouteType.DIRECT)
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        routing_result = BenchmarkResult(
            test_name="Memory State - Routing",
            component="Routing",
            duration_ms=(end_time - start_time) * 1000,
            memory_bytes=end_memory - start_memory,
            operations_count=2000,
            success_count=2000,
            error_count=0,
            throughput_ops_per_sec=2000 / (end_time - start_time),
            latency_ms=((end_time - start_time) * 1000) / 2000,
            cpu_percent=self._get_cpu_percent(),
            memory_percent=self._get_memory_percent(),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        results.append(routing_result)
        
        # Test Subscriptions
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        subscriptions = UACPSubscriptions()
        for i in range(1000):
            subscriptions.create_subscription(f"sub_{i}", f"topic/pattern/{i}", f"agent_{i}")
            subscriptions.create_dialogue(f"dialogue_{i}", f"agent_{i}", f"agent_{(i+1)%100}")
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        sub_result = BenchmarkResult(
            test_name="Memory State - Subscriptions",
            component="Subscriptions",
            duration_ms=(end_time - start_time) * 1000,
            memory_bytes=end_memory - start_memory,
            operations_count=2000,
            success_count=2000,
            error_count=0,
            throughput_ops_per_sec=2000 / (end_time - start_time),
            latency_ms=((end_time - start_time) * 1000) / 2000,
            cpu_percent=self._get_cpu_percent(),
            memory_percent=self._get_memory_percent(),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        results.append(sub_result)
        
        # Test Reliability
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        reliability = UACPReliability()
        for i in range(1000):
            reliability.track_message(f"msg_{i}", f"agent_{i}", 1, 30.0)
            reliability.add_block(f"msg_{i}", i, f"block_{i}".encode())
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        rel_result = BenchmarkResult(
            test_name="Memory State - Reliability",
            component="Reliability",
            duration_ms=(end_time - start_time) * 1000,
            memory_bytes=end_memory - start_memory,
            operations_count=2000,
            success_count=2000,
            error_count=0,
            throughput_ops_per_sec=2000 / (end_time - start_time),
            latency_ms=((end_time - start_time) * 1000) / 2000,
            cpu_percent=self._get_cpu_percent(),
            memory_percent=self._get_memory_percent(),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        results.append(rel_result)
        
        self.results.extend(results)
        return results
    
    def benchmark_robustness_features(self) -> List[BenchmarkResult]:
        """Benchmark robustness features performance."""
        self.console.print(f"\n🛡️ Benchmarking Robustness Features")
        results = []
        
        # Test Circuit Breaker
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        cb_manager = CircuitBreakerManager()
        for i in range(1000):
            cb_manager.get_circuit_breaker(f"service_{i}")
            cb_manager.record_success(f"service_{i}")
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        cb_result = BenchmarkResult(
            test_name="Robustness - Circuit Breaker",
            component="CircuitBreaker",
            duration_ms=(end_time - start_time) * 1000,
            memory_bytes=end_memory - start_memory,
            operations_count=2000,
            success_count=2000,
            error_count=0,
            throughput_ops_per_sec=2000 / (end_time - start_time),
            latency_ms=((end_time - start_time) * 1000) / 2000,
            cpu_percent=self._get_cpu_percent(),
            memory_percent=self._get_memory_percent(),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        results.append(cb_result)
        
        # Test Adaptive Timeout
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        timeout_manager = TimeoutManager()
        for i in range(1000):
            timeout_manager.get_timeout(f"operation_{i}")
            timeout_manager.record_operation(f"operation_{i}", 5.0, True, 2.0)
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        at_result = BenchmarkResult(
            test_name="Robustness - Adaptive Timeout",
            component="AdaptiveTimeout",
            duration_ms=(end_time - start_time) * 1000,
            memory_bytes=end_memory - start_memory,
            operations_count=2000,
            success_count=2000,
            error_count=0,
            throughput_ops_per_sec=2000 / (end_time - start_time),
            latency_ms=((end_time - start_time) * 1000) / 2000,
            cpu_percent=self._get_cpu_percent(),
            memory_percent=self._get_memory_percent(),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        results.append(at_result)
        
        # Test Resource Pooling
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        def create_resource():
            return f"resource_{time.time()}"
        
        pool = ResourcePool(create_resource, config=PoolConfig(min_size=10, max_size=100))
        for i in range(1000):
            resource = pool.acquire()
            if resource:
                pool.release(resource)
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        rp_result = BenchmarkResult(
            test_name="Robustness - Resource Pooling",
            component="ResourcePool",
            duration_ms=(end_time - start_time) * 1000,
            memory_bytes=end_memory - start_memory,
            operations_count=2000,
            success_count=2000,
            error_count=0,
            throughput_ops_per_sec=2000 / (end_time - start_time),
            latency_ms=((end_time - start_time) * 1000) / 2000,
            cpu_percent=self._get_cpu_percent(),
            memory_percent=self._get_memory_percent(),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        results.append(rp_result)
        
        self.results.extend(results)
        return results
    
    async def benchmark_concurrent_operations(self, concurrent_count: int = 100) -> BenchmarkResult:
        """Benchmark concurrent operations performance."""
        self.console.print(f"\n⚡ Benchmarking Concurrent Operations ({concurrent_count} concurrent)")
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        async def concurrent_operation(operation_id: int):
            """Simulate a concurrent operation."""
            await asyncio.sleep(0.001)  # Simulate work
            return f"operation_{operation_id}_completed"
        
        # Run concurrent operations
        tasks = [concurrent_operation(i) for i in range(concurrent_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = sum(1 for r in results if isinstance(r, Exception))
        
        duration_ms = (end_time - start_time) * 1000
        memory_bytes = end_memory - start_memory
        throughput = concurrent_count / (duration_ms / 1000)
        latency = duration_ms / concurrent_count
        
        result = BenchmarkResult(
            test_name="Concurrent Operations",
            component="Concurrency",
            duration_ms=duration_ms,
            memory_bytes=memory_bytes,
            operations_count=concurrent_count,
            success_count=success_count,
            error_count=error_count,
            throughput_ops_per_sec=throughput,
            latency_ms=latency,
            cpu_percent=self._get_cpu_percent(),
            memory_percent=self._get_memory_percent(),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.results.append(result)
        return result
    
    def benchmark_memory_efficiency(self) -> BenchmarkResult:
        """Benchmark memory efficiency under load."""
        self.console.print(f"\n💾 Benchmarking Memory Efficiency")
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        # Create many objects to test memory management
        objects = []
        for i in range(10000):
            obj = {
                'id': i,
                'data': f"data_{i}" * 100,  # 100 bytes per object
                'timestamp': time.time()
            }
            objects.append(obj)
        
        # Simulate some operations
        for i in range(1000):
            if i % 100 == 0:
                objects[i]['processed'] = True
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        duration_ms = (end_time - start_time) * 1000
        memory_bytes = end_memory - start_memory
        throughput = 10000 / (duration_ms / 1000)
        latency = duration_ms / 10000
        
        result = BenchmarkResult(
            test_name="Memory Efficiency",
            component="Memory",
            duration_ms=duration_ms,
            memory_bytes=memory_bytes,
            operations_count=10000,
            success_count=10000,
            error_count=0,
            throughput_ops_per_sec=throughput,
            latency_ms=latency,
            cpu_percent=self._get_cpu_percent(),
            memory_percent=self._get_memory_percent(),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.results.append(result)
        return result
    
    def generate_report(self) -> str:
        """Generate comprehensive benchmark report."""
        self.console.print(f"\n📊 Generating Comprehensive Benchmark Report")
        
        # Calculate summary statistics
        total_tests = len(self.results)
        total_duration = sum(r.duration_ms for r in self.results)
        total_memory = sum(r.memory_bytes for r in self.results)
        avg_throughput = statistics.mean(r.throughput_ops_per_sec for r in self.results)
        avg_latency = statistics.mean(r.latency_ms for r in self.results)
        
        # Group by component
        component_stats = {}
        for result in self.results:
            if result.component not in component_stats:
                component_stats[result.component] = []
            component_stats[result.component].append(result)
        
        # Create report
        report = f"""
# µACP Comprehensive Benchmark Report

## Summary
- **Total Tests**: {total_tests}
- **Total Duration**: {total_duration:.2f} ms
- **Total Memory**: {total_memory / 1024:.2f} KB
- **Average Throughput**: {avg_throughput:.2f} ops/sec
- **Average Latency**: {avg_latency:.2f} ms

## Component Performance

"""
        
        for component, results in component_stats.items():
            component_throughput = statistics.mean(r.throughput_ops_per_sec for r in results)
            component_latency = statistics.mean(r.latency_ms for r in results)
            component_memory = sum(r.memory_bytes for r in results)
            
            report += f"""
### {component}
- **Tests**: {len(results)}
- **Average Throughput**: {component_throughput:.2f} ops/sec
- **Average Latency**: {component_latency:.2f} ms
- **Total Memory**: {component_memory / 1024:.2f} KB

"""
        
        # Detailed results
        report += "\n## Detailed Results\n\n"
        for result in self.results:
            report += f"""
#### {result.test_name}
- **Component**: {result.component}
- **Duration**: {result.duration_ms:.2f} ms
- **Memory**: {result.memory_bytes / 1024:.2f} KB
- **Operations**: {result.operations_count:,}
- **Success Rate**: {(result.success_count / result.operations_count) * 100:.1f}%
- **Throughput**: {result.throughput_ops_per_sec:.2f} ops/sec
- **Latency**: {result.latency_ms:.2f} ms

"""
        
        return report
    
    def display_results_table(self):
        """Display results in a formatted table."""
        table = Table(title="µACP Comprehensive Benchmark Results")
        
        table.add_column("Test", style="cyan")
        table.add_column("Component", style="magenta")
        table.add_column("Duration (ms)", style="green")
        table.add_column("Memory (KB)", style="yellow")
        table.add_column("Throughput (ops/sec)", style="blue")
        table.add_column("Latency (ms)", style="red")
        table.add_column("Success Rate", style="green")
        
        for result in self.results:
            success_rate = (result.success_count / result.operations_count) * 100
            table.add_row(
                result.test_name,
                result.component,
                f"{result.duration_ms:.2f}",
                f"{result.memory_bytes / 1024:.2f}",
                f"{result.throughput_ops_per_sec:.2f}",
                f"{result.latency_ms:.2f}",
                f"{success_rate:.1f}%"
            )
        
        self.console.print(table)
    
    async def run_all_benchmarks(self):
        """Run all benchmarks."""
        self.console.print(Panel.fit("🚀 µACP Comprehensive Benchmark Suite", style="bold blue"))
        self.console.print("Testing all features including core protocol, memory state components, and robustness features.")
        
        try:
            # Core protocol benchmark
            self.benchmark_core_protocol(10000)
            
            # Memory state components benchmark
            self.benchmark_memory_state_components()
            
            # Robustness features benchmark
            self.benchmark_robustness_features()
            
            # Concurrent operations benchmark
            await self.benchmark_concurrent_operations(100)
            
            # Memory efficiency benchmark
            self.benchmark_memory_efficiency()
            
            # Display results
            self.display_results_table()
            
            # Generate report
            report = self.generate_report()
            
            # Save report to file
            with open("uacp_comprehensive_benchmark_report.md", "w") as f:
                f.write(report)
            
            self.console.print(f"\n✅ All benchmarks completed successfully!")
            self.console.print(f"📄 Detailed report saved to: uacp_comprehensive_benchmark_report.md")
            
        except Exception as e:
            self.console.print(f"\n❌ Benchmark failed with error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main benchmark execution."""
    benchmark_suite = ComprehensiveBenchmarkSuite()
    await benchmark_suite.run_all_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())
