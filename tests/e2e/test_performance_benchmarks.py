#!/usr/bin/env python3
"""
Performance Benchmarking and Load Testing Suite
Tests system performance, scalability, and concurrent execution
"""

import pytest
import asyncio
import time
import psutil
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json
import tempfile
import shutil

# Import production components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.production_monitor import ProductionMonitor
from lib.agent_runtime import AgentContext, ModelType


@dataclass
class PerformanceMetrics:
    """Performance metrics for a test run"""
    test_name: str
    duration: float
    throughput: float  # operations per second
    latency_p50: float
    latency_p95: float
    latency_p99: float
    cpu_usage_avg: float
    memory_usage_mb: float
    concurrent_executions: int
    errors: int
    success_rate: float


@dataclass
class BenchmarkResult:
    """Result of a benchmark test"""
    name: str
    metrics: PerformanceMetrics
    passed: bool
    thresholds_met: Dict[str, bool]
    recommendations: List[str]


class PerformanceBenchmark:
    """Performance benchmarking system"""
    
    def __init__(self):
        self.monitor = ProductionMonitor()
        self.metrics_history: List[PerformanceMetrics] = []
        self.resource_samples: List[Dict] = []
        self.temp_dirs: List[str] = []
        
        # Performance thresholds
        self.thresholds = {
            "agent_execution_time": 30.0,  # seconds
            "workflow_completion_time": 120.0,  # seconds
            "api_response_time": 0.2,  # seconds
            "throughput_min": 1.0,  # ops/second
            "success_rate_min": 0.9,  # 90%
            "memory_limit_mb": 1024,  # 1GB
            "cpu_usage_max": 80.0  # 80%
        }
    
    def setup(self):
        """Setup benchmark environment"""
        self.start_resource_monitoring()
    
    def teardown(self):
        """Cleanup benchmark environment"""
        # Cleanup temp directories
        for temp_dir in self.temp_dirs:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        self.temp_dirs.clear()
    
    def start_resource_monitoring(self):
        """Start monitoring system resources"""
        self.resource_samples.clear()
        
        async def monitor_resources():
            while True:
                sample = {
                    "timestamp": time.time(),
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                    "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
                }
                self.resource_samples.append(sample)
                await asyncio.sleep(1)
        
        # Start monitoring in background
        asyncio.create_task(monitor_resources())
    
    async def benchmark_agent_execution(
        self,
        agent_name: str,
        iterations: int = 10
    ) -> BenchmarkResult:
        """Benchmark individual agent execution"""
        
        latencies = []
        start_time = time.time()
        errors = 0
        
        for i in range(iterations):
            iter_start = time.time()
            
            try:
                # Create test context
                context = AgentContext(
                    project_requirements={"test": f"iteration_{i}"},
                    completed_tasks=[],
                    artifacts={},
                    decisions=[],
                    current_phase="benchmark"
                )
                
                # Mock agent execution
                await self._mock_agent_execution(agent_name, context)
                
                latency = time.time() - iter_start
                latencies.append(latency)
                
            except Exception as e:
                errors += 1
                print(f"Error in iteration {i}: {e}")
        
        duration = time.time() - start_time
        
        # Calculate metrics
        metrics = PerformanceMetrics(
            test_name=f"agent_{agent_name}",
            duration=duration,
            throughput=iterations / duration if duration > 0 else 0,
            latency_p50=statistics.median(latencies) if latencies else 0,
            latency_p95=self._percentile(latencies, 95) if latencies else 0,
            latency_p99=self._percentile(latencies, 99) if latencies else 0,
            cpu_usage_avg=self._get_avg_cpu_usage(start_time, time.time()),
            memory_usage_mb=self._get_max_memory_usage(start_time, time.time()),
            concurrent_executions=1,
            errors=errors,
            success_rate=(iterations - errors) / iterations if iterations > 0 else 0
        )
        
        # Check thresholds
        thresholds_met = {
            "execution_time": metrics.latency_p95 <= self.thresholds["agent_execution_time"],
            "success_rate": metrics.success_rate >= self.thresholds["success_rate_min"],
            "memory": metrics.memory_usage_mb <= self.thresholds["memory_limit_mb"],
            "cpu": metrics.cpu_usage_avg <= self.thresholds["cpu_usage_max"]
        }
        
        # Generate recommendations
        recommendations = []
        if not thresholds_met["execution_time"]:
            recommendations.append(f"Agent {agent_name} is slow (P95: {metrics.latency_p95:.2f}s)")
        if not thresholds_met["success_rate"]:
            recommendations.append(f"Agent {agent_name} has high error rate ({(1-metrics.success_rate)*100:.1f}%)")
        if not thresholds_met["memory"]:
            recommendations.append(f"Agent {agent_name} uses too much memory ({metrics.memory_usage_mb:.0f}MB)")
        
        self.metrics_history.append(metrics)
        
        return BenchmarkResult(
            name=f"agent_{agent_name}_benchmark",
            metrics=metrics,
            passed=all(thresholds_met.values()),
            thresholds_met=thresholds_met,
            recommendations=recommendations
        )
    
    async def benchmark_workflow(
        self,
        workflow_type: str,
        agent_count: int = 5
    ) -> BenchmarkResult:
        """Benchmark complete workflow execution"""
        
        start_time = time.time()
        
        # Create workflow context
        context = AgentContext(
            project_requirements={
                "type": workflow_type,
                "benchmark": True
            },
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="benchmark"
        )
        
        # Execute workflow agents
        agent_latencies = []
        errors = 0
        
        for i in range(agent_count):
            agent_start = time.time()
            
            try:
                agent_name = f"agent_{i}"
                await self._mock_agent_execution(agent_name, context)
                context.completed_tasks.append(agent_name)
                
                latency = time.time() - agent_start
                agent_latencies.append(latency)
                
            except Exception as e:
                errors += 1
                print(f"Error in agent {i}: {e}")
        
        duration = time.time() - start_time
        
        # Calculate metrics
        metrics = PerformanceMetrics(
            test_name=f"workflow_{workflow_type}",
            duration=duration,
            throughput=agent_count / duration if duration > 0 else 0,
            latency_p50=statistics.median(agent_latencies) if agent_latencies else 0,
            latency_p95=self._percentile(agent_latencies, 95) if agent_latencies else 0,
            latency_p99=self._percentile(agent_latencies, 99) if agent_latencies else 0,
            cpu_usage_avg=self._get_avg_cpu_usage(start_time, time.time()),
            memory_usage_mb=self._get_max_memory_usage(start_time, time.time()),
            concurrent_executions=1,
            errors=errors,
            success_rate=(agent_count - errors) / agent_count if agent_count > 0 else 0
        )
        
        # Check thresholds
        thresholds_met = {
            "completion_time": duration <= self.thresholds["workflow_completion_time"],
            "throughput": metrics.throughput >= self.thresholds["throughput_min"],
            "success_rate": metrics.success_rate >= self.thresholds["success_rate_min"]
        }
        
        # Generate recommendations
        recommendations = []
        if not thresholds_met["completion_time"]:
            recommendations.append(f"Workflow too slow ({duration:.1f}s)")
        if not thresholds_met["throughput"]:
            recommendations.append(f"Low throughput ({metrics.throughput:.2f} agents/s)")
        
        self.metrics_history.append(metrics)
        
        return BenchmarkResult(
            name=f"workflow_{workflow_type}_benchmark",
            metrics=metrics,
            passed=all(thresholds_met.values()),
            thresholds_met=thresholds_met,
            recommendations=recommendations
        )
    
    async def load_test_concurrent_projects(
        self,
        num_projects: int = 5,
        project_type: str = "web_app"
    ) -> BenchmarkResult:
        """Load test with concurrent project executions"""
        
        start_time = time.time()
        
        # Create tasks for concurrent execution
        tasks = []
        for i in range(num_projects):
            task = asyncio.create_task(
                self._execute_project(f"project_{i}", project_type)
            )
            tasks.append(task)
        
        # Wait for all projects to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        # Count successes and errors
        successes = sum(1 for r in results if r is True)
        errors = sum(1 for r in results if r is False or isinstance(r, Exception))
        
        # Calculate metrics
        metrics = PerformanceMetrics(
            test_name=f"load_test_{num_projects}_projects",
            duration=duration,
            throughput=num_projects / duration if duration > 0 else 0,
            latency_p50=duration / num_projects,  # Simplified for load test
            latency_p95=duration / num_projects * 1.5,
            latency_p99=duration / num_projects * 2,
            cpu_usage_avg=self._get_avg_cpu_usage(start_time, time.time()),
            memory_usage_mb=self._get_max_memory_usage(start_time, time.time()),
            concurrent_executions=num_projects,
            errors=errors,
            success_rate=successes / num_projects if num_projects > 0 else 0
        )
        
        # Check thresholds
        thresholds_met = {
            "success_rate": metrics.success_rate >= self.thresholds["success_rate_min"],
            "memory": metrics.memory_usage_mb <= self.thresholds["memory_limit_mb"] * num_projects,
            "throughput": metrics.throughput >= 0.1  # At least 0.1 projects/second
        }
        
        # Generate recommendations
        recommendations = []
        if not thresholds_met["success_rate"]:
            recommendations.append(f"High failure rate under load ({errors}/{num_projects} failed)")
        if not thresholds_met["memory"]:
            recommendations.append(f"Memory usage too high ({metrics.memory_usage_mb:.0f}MB for {num_projects} projects)")
        if metrics.throughput < 0.5:
            recommendations.append(f"Consider optimizing for better concurrent performance")
        
        self.metrics_history.append(metrics)
        
        return BenchmarkResult(
            name=f"load_test_{num_projects}",
            metrics=metrics,
            passed=all(thresholds_met.values()),
            thresholds_met=thresholds_met,
            recommendations=recommendations
        )
    
    async def stress_test(
        self,
        duration_seconds: int = 60,
        max_concurrent: int = 10
    ) -> BenchmarkResult:
        """Stress test system with increasing load"""
        
        start_time = time.time()
        results = []
        current_load = 1
        
        while time.time() - start_time < duration_seconds:
            # Gradually increase load
            if current_load < max_concurrent:
                current_load = min(current_load + 1, max_concurrent)
            
            # Execute concurrent tasks
            tasks = []
            for i in range(current_load):
                task = asyncio.create_task(
                    self._mock_agent_execution(f"stress_agent_{i}", None)
                )
                tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Brief pause between batches
            await asyncio.sleep(1)
        
        duration = time.time() - start_time
        
        # Calculate metrics
        successes = sum(1 for r in results if r is True)
        errors = len(results) - successes
        
        metrics = PerformanceMetrics(
            test_name="stress_test",
            duration=duration,
            throughput=len(results) / duration if duration > 0 else 0,
            latency_p50=0.5,  # Simplified for stress test
            latency_p95=1.0,
            latency_p99=2.0,
            cpu_usage_avg=self._get_avg_cpu_usage(start_time, time.time()),
            memory_usage_mb=self._get_max_memory_usage(start_time, time.time()),
            concurrent_executions=max_concurrent,
            errors=errors,
            success_rate=successes / len(results) if results else 0
        )
        
        # Determine breaking point
        breaking_point = None
        if metrics.cpu_usage_avg > 90:
            breaking_point = "CPU exhaustion"
        elif metrics.memory_usage_mb > self.thresholds["memory_limit_mb"] * 2:
            breaking_point = "Memory exhaustion"
        elif metrics.success_rate < 0.5:
            breaking_point = "High error rate"
        
        # Generate recommendations
        recommendations = []
        if breaking_point:
            recommendations.append(f"System breaking point: {breaking_point}")
        recommendations.append(f"Max sustainable load: ~{int(metrics.throughput * 0.8)} ops/s")
        
        return BenchmarkResult(
            name="stress_test",
            metrics=metrics,
            passed=metrics.success_rate >= 0.7,  # 70% success under stress
            thresholds_met={"stress_tolerance": metrics.success_rate >= 0.7},
            recommendations=recommendations
        )
    
    async def _mock_agent_execution(
        self,
        agent_name: str,
        context: Optional[AgentContext]
    ) -> bool:
        """Mock agent execution for benchmarking"""
        # Simulate work with sleep
        await asyncio.sleep(0.1 + (hash(agent_name) % 10) * 0.01)
        
        # Simulate some CPU work
        result = sum(i * i for i in range(1000))
        
        # Randomly fail sometimes (5% failure rate)
        import random
        if random.random() < 0.05:
            raise Exception(f"Simulated failure in {agent_name}")
        
        return True
    
    async def _execute_project(
        self,
        project_name: str,
        project_type: str
    ) -> bool:
        """Execute a mock project for load testing"""
        try:
            # Create temp directory for project
            temp_dir = tempfile.mkdtemp(prefix=f"bench_{project_name}_")
            self.temp_dirs.append(temp_dir)
            
            # Simulate project execution
            context = AgentContext(
                project_requirements={
                    "name": project_name,
                    "type": project_type
                },
                completed_tasks=[],
                artifacts={"project_directory": temp_dir},
                decisions=[],
                current_phase="execution"
            )
            
            # Execute mock agents
            agent_count = 3 + hash(project_name) % 3
            for i in range(agent_count):
                await self._mock_agent_execution(f"{project_name}_agent_{i}", context)
                context.completed_tasks.append(f"agent_{i}")
            
            return True
            
        except Exception as e:
            print(f"Project {project_name} failed: {e}")
            return False
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _get_avg_cpu_usage(self, start_time: float, end_time: float) -> float:
        """Get average CPU usage during time period"""
        samples = [
            s["cpu_percent"] for s in self.resource_samples
            if start_time <= s["timestamp"] <= end_time
        ]
        return statistics.mean(samples) if samples else 0
    
    def _get_max_memory_usage(self, start_time: float, end_time: float) -> float:
        """Get maximum memory usage during time period"""
        samples = [
            s["memory_mb"] for s in self.resource_samples
            if start_time <= s["timestamp"] <= end_time
        ]
        return max(samples) if samples else 0
    
    def generate_report(self) -> str:
        """Generate performance benchmark report"""
        report = []
        report.append("=" * 60)
        report.append("PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 60)
        
        if not self.metrics_history:
            report.append("No benchmarks executed")
            return "\n".join(report)
        
        # Summary statistics
        avg_throughput = statistics.mean(m.throughput for m in self.metrics_history)
        avg_success_rate = statistics.mean(m.success_rate for m in self.metrics_history)
        max_memory = max(m.memory_usage_mb for m in self.metrics_history)
        avg_cpu = statistics.mean(m.cpu_usage_avg for m in self.metrics_history)
        
        report.append("\nSUMMARY STATISTICS")
        report.append("-" * 40)
        report.append(f"Tests executed: {len(self.metrics_history)}")
        report.append(f"Average throughput: {avg_throughput:.2f} ops/s")
        report.append(f"Average success rate: {avg_success_rate * 100:.1f}%")
        report.append(f"Peak memory usage: {max_memory:.0f} MB")
        report.append(f"Average CPU usage: {avg_cpu:.1f}%")
        
        # Individual test results
        report.append("\nINDIVIDUAL TEST RESULTS")
        report.append("-" * 40)
        
        for metrics in self.metrics_history:
            report.append(f"\n{metrics.test_name}:")
            report.append(f"  Duration: {metrics.duration:.2f}s")
            report.append(f"  Throughput: {metrics.throughput:.2f} ops/s")
            report.append(f"  Latency P50/P95/P99: {metrics.latency_p50:.3f}s / {metrics.latency_p95:.3f}s / {metrics.latency_p99:.3f}s")
            report.append(f"  Success rate: {metrics.success_rate * 100:.1f}%")
            report.append(f"  CPU/Memory: {metrics.cpu_usage_avg:.1f}% / {metrics.memory_usage_mb:.0f}MB")
            
            if metrics.concurrent_executions > 1:
                report.append(f"  Concurrent executions: {metrics.concurrent_executions}")
        
        return "\n".join(report)


class TestPerformanceBenchmarks:
    """Test cases for performance benchmarks"""
    
    @pytest.fixture
    def benchmark(self):
        """Create benchmark instance"""
        bench = PerformanceBenchmark()
        bench.setup()
        yield bench
        bench.teardown()
    
    @pytest.mark.asyncio
    async def test_agent_benchmark(self, benchmark):
        """Test individual agent performance"""
        result = await benchmark.benchmark_agent_execution(
            "test_agent",
            iterations=5
        )
        
        assert result.metrics.success_rate >= 0.8
        assert result.metrics.latency_p95 < 60  # Should complete within 60s
        assert result.metrics.throughput > 0
    
    @pytest.mark.asyncio
    async def test_workflow_benchmark(self, benchmark):
        """Test workflow performance"""
        result = await benchmark.benchmark_workflow(
            "test_workflow",
            agent_count=3
        )
        
        assert result.metrics.success_rate >= 0.8
        assert result.metrics.duration < 180  # 3 minutes max
        assert result.metrics.throughput > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_load(self, benchmark):
        """Test concurrent project load"""
        result = await benchmark.load_test_concurrent_projects(
            num_projects=3,
            project_type="api_service"
        )
        
        assert result.metrics.success_rate >= 0.6  # 60% success under load
        assert result.metrics.concurrent_executions == 3
        assert result.metrics.memory_usage_mb < 2048  # 2GB limit
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_stress_test(self, benchmark):
        """Test system under stress"""
        result = await benchmark.stress_test(
            duration_seconds=10,
            max_concurrent=5
        )
        
        assert result.metrics.success_rate >= 0.5  # 50% success under stress
        assert len(result.recommendations) > 0  # Should provide recommendations
    
    @pytest.mark.asyncio
    async def test_resource_monitoring(self, benchmark):
        """Test resource monitoring during execution"""
        # Execute some work
        await benchmark.benchmark_agent_execution("resource_test", iterations=3)
        
        # Check resource samples were collected
        assert len(benchmark.resource_samples) > 0
        
        # Check metrics calculation
        cpu_avg = benchmark._get_avg_cpu_usage(
            time.time() - 10,
            time.time()
        )
        assert cpu_avg >= 0
        
        memory_max = benchmark._get_max_memory_usage(
            time.time() - 10,
            time.time()
        )
        assert memory_max > 0
    
    def test_report_generation(self, benchmark):
        """Test performance report generation"""
        # Add some mock metrics
        benchmark.metrics_history.append(
            PerformanceMetrics(
                test_name="test1",
                duration=10.0,
                throughput=5.0,
                latency_p50=0.5,
                latency_p95=1.0,
                latency_p99=2.0,
                cpu_usage_avg=50.0,
                memory_usage_mb=512,
                concurrent_executions=1,
                errors=1,
                success_rate=0.9
            )
        )
        
        report = benchmark.generate_report()
        
        assert "PERFORMANCE BENCHMARK REPORT" in report
        assert "SUMMARY STATISTICS" in report
        assert "test1" in report
        assert "90.0%" in report  # Success rate


if __name__ == "__main__":
    # Run performance benchmark demo
    async def demo():
        print("Performance Benchmark Demo")
        print("=" * 60)
        
        benchmark = PerformanceBenchmark()
        benchmark.setup()
        
        try:
            # Test agent performance
            print("\n1. Testing Agent Performance...")
            agent_result = await benchmark.benchmark_agent_execution(
                "demo_agent",
                iterations=5
            )
            print(f"   Result: {'PASS' if agent_result.passed else 'FAIL'}")
            print(f"   Throughput: {agent_result.metrics.throughput:.2f} ops/s")
            print(f"   Success rate: {agent_result.metrics.success_rate * 100:.1f}%")
            
            # Test workflow performance
            print("\n2. Testing Workflow Performance...")
            workflow_result = await benchmark.benchmark_workflow(
                "demo_workflow",
                agent_count=3
            )
            print(f"   Result: {'PASS' if workflow_result.passed else 'FAIL'}")
            print(f"   Duration: {workflow_result.metrics.duration:.2f}s")
            print(f"   Throughput: {workflow_result.metrics.throughput:.2f} agents/s")
            
            # Test concurrent load
            print("\n3. Testing Concurrent Load...")
            load_result = await benchmark.load_test_concurrent_projects(
                num_projects=3,
                project_type="test"
            )
            print(f"   Result: {'PASS' if load_result.passed else 'FAIL'}")
            print(f"   Concurrent projects: {load_result.metrics.concurrent_executions}")
            print(f"   Success rate: {load_result.metrics.success_rate * 100:.1f}%")
            print(f"   Memory usage: {load_result.metrics.memory_usage_mb:.0f}MB")
            
            # Generate report
            print("\n" + benchmark.generate_report())
            
        finally:
            benchmark.teardown()
    
    asyncio.run(demo())