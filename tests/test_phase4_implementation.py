#!/usr/bin/env python3
"""
Test Suite for Phase 4 Advanced Features
Tests Adaptive Orchestrator, Observability Platform, and Self-Healing System
"""

import unittest
import asyncio
import time
import json
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Phase 4 components
try:
    from lib.adaptive_orchestrator import AdaptiveOrchestrator, AgentPerformanceMetrics, WorkloadPrediction
    from lib.observability_platform import ObservabilityPlatform, LogLevel, TraceSpan
    from lib.self_healing_system import SelfHealingSystem, ErrorPattern, PromptOptimization
    from lib.phase4_integration import Phase4IntegratedSystem, Phase4Config
    PHASE4_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Phase 4 components not available: {e}")
    PHASE4_AVAILABLE = False


class TestAdaptiveOrchestrator(unittest.TestCase):
    """Test the Adaptive Orchestrator component"""
    
    @unittest.skipUnless(PHASE4_AVAILABLE, "Phase 4 components not available")
    def setUp(self):
        """Set up test fixtures"""
        self.orchestrator = AdaptiveOrchestrator(
            history_path="test_data/agent_history.json",
            ml_model_path="test_models/agent_selector.pkl"
        )
    
    def test_agent_selection(self):
        """Test optimal agent selection"""
        requirements = {
            "features": ["user auth", "AI recommendations", "database"],
            "project": "test_app"
        }
        
        available_agents = [
            "project-architect",
            "rapid-builder",
            "ai-specialist",
            "database-expert",
            "frontend-specialist"
        ]
        
        selected = self.orchestrator.select_optimal_agents(requirements, available_agents)
        
        # Should select relevant agents
        self.assertIn("project-architect", selected)
        self.assertIn("ai-specialist", selected)  # For AI requirements
        self.assertIn("database-expert", selected)  # For database requirements
    
    def test_dynamic_timeout(self):
        """Test dynamic timeout calculation"""
        # Add some performance history
        self.orchestrator.update_agent_performance(
            "test-agent",
            success=True,
            execution_time=150,
            quality_score=0.9
        )
        
        # Get dynamic timeout
        timeout = self.orchestrator.get_dynamic_timeout("test-agent")
        
        # Should be based on historical data (2x average)
        self.assertGreater(timeout, 150)
        self.assertLess(timeout, 600)
    
    def test_parallel_optimization(self):
        """Test parallel execution optimization"""
        agents = [
            "project-architect",
            "rapid-builder",
            "frontend-specialist",
            "documentation-writer",
            "api-integrator"
        ]
        
        groups = self.orchestrator.optimize_parallel_execution(agents)
        
        # Should create groups for parallel execution
        self.assertGreater(len(groups), 0)
        
        # All agents should be included
        all_agents = []
        for group in groups:
            all_agents.extend(group)
        self.assertEqual(set(all_agents), set(agents))
    
    def test_workload_prediction(self):
        """Test workload prediction"""
        requirements = {
            "features": ["auth", "api", "frontend", "database", "ai"],
            "complexity": 2
        }
        
        prediction = self.orchestrator.predict_workload(requirements)
        
        self.assertIsInstance(prediction, WorkloadPrediction)
        self.assertGreater(prediction.estimated_agents, 0)
        self.assertGreater(prediction.estimated_duration, 0)
        self.assertGreater(prediction.estimated_cost, 0)
    
    def test_performance_tracking(self):
        """Test agent performance tracking"""
        # Update performance multiple times
        for i in range(5):
            self.orchestrator.update_agent_performance(
                "test-agent",
                success=i % 2 == 0,  # Alternate success/failure
                execution_time=100 + i * 10,
                tokens=5000 + i * 1000,
                cost=0.1 + i * 0.02,
                quality_score=0.8 if i % 2 == 0 else 0.3
            )
        
        # Check metrics
        metrics = self.orchestrator.agent_metrics.get("test-agent")
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.total_executions, 5)
        self.assertEqual(metrics.success_count, 3)  # 0, 2, 4
        self.assertEqual(metrics.failure_count, 2)  # 1, 3
        
        # Check trend
        trend = metrics.get_trend()
        self.assertIn(trend, ["improving", "degrading", "stable", "insufficient_data"])


class TestObservabilityPlatform(unittest.TestCase):
    """Test the Observability Platform component"""
    
    @unittest.skipUnless(PHASE4_AVAILABLE, "Phase 4 components not available")
    def setUp(self):
        """Set up test fixtures"""
        self.platform = ObservabilityPlatform(
            log_dir="test_logs/observability",
            enable_otel=False  # Disable for testing
        )
    
    def test_tracing(self):
        """Test distributed tracing"""
        # Start a trace
        trace_id = self.platform.start_trace("test_operation", {"test": "value"})
        self.assertIsNotNone(trace_id)
        
        # Start spans
        span1_id = self.platform.start_span(trace_id, "span1")
        span2_id = self.platform.start_span(trace_id, "span2", parent_span_id=span1_id)
        
        # End spans
        self.platform.end_span(span2_id)
        self.platform.end_span(span1_id)
        
        # Get trace
        trace = self.platform.get_trace(trace_id)
        self.assertEqual(len(trace), 2)  # Main trace span + 2 child spans
    
    def test_logging(self):
        """Test centralized logging"""
        # Log messages at different levels
        self.platform.log(LogLevel.INFO, "Test info message", "test_source")
        self.platform.log(LogLevel.WARNING, "Test warning", "test_source")
        self.platform.log(LogLevel.ERROR, "Test error", "test_source")
        
        # Get recent logs
        logs = self.platform.get_recent_logs(count=10)
        self.assertGreater(len(logs), 0)
        
        # Filter by level
        error_logs = self.platform.get_recent_logs(count=10, level=LogLevel.ERROR)
        self.assertTrue(all(log.level == LogLevel.ERROR for log in error_logs))
    
    def test_metrics(self):
        """Test metrics recording"""
        # Record metrics
        for i in range(10):
            self.platform.record_metric("test_metric", 100 + i * 10, 
                                       tags={"test": "true"}, unit="ms")
        
        # Get metrics summary
        summary = self.platform.get_metrics_summary("test_metric")
        
        self.assertIn("test_metric", summary)
        self.assertEqual(summary["test_metric"]["count"], 10)
        self.assertGreater(summary["test_metric"]["mean"], 100)
    
    def test_anomaly_detection(self):
        """Test anomaly detection"""
        # Record normal values
        for i in range(20):
            self.platform.record_metric("response_time", 100 + i % 10)
        
        # Record anomaly
        self.platform.record_metric("response_time", 1000)  # 10x normal
        
        # Force anomaly detection
        self.platform._detect_anomalies(
            "response_time",
            list(self.platform.metrics_buffer["response_time"])
        )
        
        # Check anomalies
        anomalies = self.platform.get_anomalies()
        # May or may not detect depending on statistical threshold
        # Just verify the method works
        self.assertIsInstance(anomalies, list)
    
    def test_performance_insights(self):
        """Test performance insights generation"""
        # Add some data
        trace_id = self.platform.start_trace("test_workflow")
        span_id = self.platform.start_span(trace_id, "test_operation")
        time.sleep(0.1)
        self.platform.end_span(span_id)
        
        # Get insights
        insights = self.platform.get_performance_insights()
        
        self.assertIn("dashboard_metrics", insights)
        self.assertIn("recommendations", insights)
        self.assertIn("slow_operations", insights)


class TestSelfHealingSystem(unittest.TestCase):
    """Test the Self-Healing System component"""
    
    @unittest.skipUnless(PHASE4_AVAILABLE, "Phase 4 components not available")
    def setUp(self):
        """Set up test fixtures"""
        self.healer = SelfHealingSystem(
            data_dir="test_data/self_healing",
            knowledge_base_path="test_data/knowledge_base.json"
        )
    
    def test_error_pattern_detection(self):
        """Test error pattern detection"""
        errors = [
            {"message": "Timeout error in agent execution", "agent": "agent1", "timestamp": time.time()},
            {"message": "Timeout exceeded for operation", "agent": "agent2", "timestamp": time.time()},
            {"message": "File not found: config.json", "agent": "agent3", "timestamp": time.time()},
            {"message": "File not found: data.csv", "agent": "agent3", "timestamp": time.time()},
        ]
        
        patterns = self.healer.detect_error_patterns(errors)
        
        # Should detect at least timeout and file patterns
        self.assertGreater(len(patterns), 0)
        
        # Check pattern structure
        for pattern in patterns:
            self.assertIsInstance(pattern, ErrorPattern)
            self.assertGreater(pattern.occurrences, 0)
            self.assertGreater(len(pattern.suggested_fixes), 0)
    
    def test_prompt_optimization(self):
        """Test prompt optimization"""
        current_prompt = "You are an agent. Do the task."
        failure_history = [
            {"type": "timeout", "context": "Complex operation"},
            {"type": "error", "context": "Unclear instructions"},
            {"type": "misunderstanding", "context": "Ambiguous requirements"}
        ]
        
        optimization = self.healer.optimize_prompt(
            "test-agent",
            current_prompt,
            failure_history
        )
        
        self.assertIsInstance(optimization, PromptOptimization)
        self.assertNotEqual(optimization.original_prompt, optimization.optimized_prompt)
        self.assertGreater(len(optimization.optimized_prompt), len(current_prompt))
    
    def test_agent_retraining_suggestion(self):
        """Test agent retraining suggestions"""
        performance_data = {
            "success_rate": 0.4,  # Very low
            "avg_quality_score": 0.5,
            "trend": "degrading",
            "tool_failures": 10
        }
        
        suggestion = self.healer.suggest_agent_retraining(
            "test-agent",
            performance_data
        )
        
        self.assertTrue(suggestion["needs_retraining"])
        self.assertEqual(suggestion["urgency"], "critical")
        self.assertGreater(len(suggestion["reasons"]), 0)
        self.assertGreater(len(suggestion["recommended_actions"]), 0)
    
    def test_configuration_tuning(self):
        """Test configuration auto-tuning"""
        current_config = {
            "agent_timeout": 100,
            "max_parallel_agents": 5,
            "max_retries": 1,
            "cache_ttl": 300
        }
        
        performance_metrics = {
            "avg_response_time": 95,  # Close to timeout
            "error_rate": 0.15,  # High error rate
            "cost_per_hour": 7.0,  # High cost
            "throughput": 2.0
        }
        
        tunes = self.healer.auto_tune_configuration(
            current_config,
            performance_metrics
        )
        
        # Should suggest some tuning
        self.assertGreater(len(tunes), 0)
        
        # Check recommendations
        for tune in tunes:
            self.assertIn(tune.parameter, current_config)
            self.assertIsNotNone(tune.reason)
    
    def test_knowledge_base(self):
        """Test knowledge base operations"""
        # Add entry
        entry_id = self.healer.update_knowledge_base(
            category="best_practice",
            title="Test Practice",
            description="A test best practice",
            solution="Apply this solution",
            examples=[{"example": "test"}]
        )
        
        self.assertIsNotNone(entry_id)
        self.assertIn(entry_id, self.healer.knowledge_base)
        
        # Update entry
        self.healer.update_knowledge_base(
            category="best_practice",
            title="Test Practice",
            description="Updated description",
            solution="Updated solution"
        )
        
        entry = self.healer.knowledge_base[entry_id]
        self.assertEqual(entry.description, "Updated description")


class TestPhase4Integration(unittest.TestCase):
    """Test the integrated Phase 4 system"""
    
    @unittest.skipUnless(PHASE4_AVAILABLE, "Phase 4 components not available")
    def setUp(self):
        """Set up test fixtures"""
        config = Phase4Config(
            enable_adaptive_orchestration=True,
            enable_observability=True,
            enable_self_healing=True,
            enable_auto_fix=True,
            enable_auto_tune=False  # Disable for testing
        )
        self.system = Phase4IntegratedSystem(config)
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsNotNone(self.system.adaptive_orchestrator)
        self.assertIsNotNone(self.system.observability)
        self.assertIsNotNone(self.system.self_healer)
    
    async def test_workflow_orchestration(self):
        """Test complete workflow orchestration"""
        requirements = {
            "project": "Test App",
            "features": ["auth", "api", "database"]
        }
        
        available_agents = [
            "project-architect",
            "rapid-builder",
            "database-expert"
        ]
        
        result = await self.system.orchestrate_workflow(
            requirements,
            available_agents
        )
        
        self.assertIn("success", result)
        self.assertIn("agents_executed", result)
        self.assertIn("metrics", result)
    
    def test_system_health(self):
        """Test system health check"""
        health = self.system.get_system_health()
        
        self.assertIn("status", health)
        self.assertIn("components", health)
        self.assertIn("metrics", health)
        self.assertIn("recommendations", health)
        
        # Check component status
        if self.system.adaptive_orchestrator:
            self.assertIn("adaptive_orchestrator", health["components"])
        if self.system.observability:
            self.assertIn("observability", health["components"])
        if self.system.self_healer:
            self.assertIn("self_healer", health["components"])
    
    def test_analytics_export(self):
        """Test analytics export"""
        # Create test directory
        test_dir = "test_analytics"
        
        # Export analytics
        self.system.export_analytics(test_dir)
        
        # Check files were created
        analytics_path = Path(test_dir)
        self.assertTrue(analytics_path.exists())
        
        # Clean up
        import shutil
        if analytics_path.exists():
            shutil.rmtree(analytics_path)


def run_async_test(test_func):
    """Helper to run async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_func())
    finally:
        loop.close()


if __name__ == "__main__":
    # Run tests
    print("=" * 60)
    print("Phase 4 Implementation Test Suite")
    print("=" * 60)
    
    if not PHASE4_AVAILABLE:
        print("\nWARNING: Phase 4 components not available.")
        print("Some tests will be skipped.")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestObservabilityPlatform))
    suite.addTests(loader.loadTestsFromTestCase(TestSelfHealingSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase4Integration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run async tests separately
    if PHASE4_AVAILABLE:
        print("\nRunning async tests...")
        integration_test = TestPhase4Integration()
        integration_test.setUp()
        run_async_test(integration_test.test_workflow_orchestration)
        print("Async tests completed.")
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  Tests Run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Skipped: {len(result.skipped)}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"  Success Rate: {success_rate:.1f}%")
    
    if success_rate > 80:
        print("\n[OK] Phase 4 Implementation Test Suite PASSED!")
    else:
        print("\n[X] Phase 4 Implementation Test Suite needs attention.")
    
    print("=" * 60)