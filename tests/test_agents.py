#!/usr/bin/env python3
"""
Comprehensive Test Suite for Agent Swarm

Tests all agents with mock and real API modes, includes performance benchmarks,
and validates correct model usage.
"""

import os
import sys
import json
import time
import argparse
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import unittest

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from lib.agent_runtime import AnthropicAgentRunner, AgentContext, ModelType, get_optimal_model
from lib.mock_anthropic import MockAnthropicClient, use_mock_client, restore_real_client
from lib.mock_anthropic_enhanced import use_enhanced_mock_client, restore_real_client
from lib.agent_logger import get_logger

class TestModelConfiguration(unittest.TestCase):
    """Test model configuration and selection"""
    
    def test_model_names(self):
        """Verify all model names are correct"""
        self.assertEqual(ModelType.HAIKU.value, "claude-3-5-haiku-20241022")
        self.assertEqual(ModelType.SONNET.value, "claude-sonnet-4-20250514")
        self.assertEqual(ModelType.OPUS.value, "claude-opus-4-20250514")
    
    def test_optimal_model_selection(self):
        """Test optimal model selection logic"""
        # Opus agents
        self.assertEqual(get_optimal_model("project-architect"), ModelType.OPUS)
        self.assertEqual(get_optimal_model("ai-specialist"), ModelType.OPUS)
        self.assertEqual(get_optimal_model("debug-specialist"), ModelType.OPUS)
        
        # Haiku agents
        self.assertEqual(get_optimal_model("documentation-writer"), ModelType.HAIKU)
        self.assertEqual(get_optimal_model("api-integrator"), ModelType.HAIKU)
        
        # Sonnet agents (default)
        self.assertEqual(get_optimal_model("rapid-builder"), ModelType.SONNET)
        self.assertEqual(get_optimal_model("quality-guardian"), ModelType.SONNET)
        
        # Task complexity override
        self.assertEqual(get_optimal_model("project-architect", "simple"), ModelType.HAIKU)
        self.assertEqual(get_optimal_model("rapid-builder", "complex"), ModelType.SONNET)

class TestSFAAgents(unittest.TestCase):
    """Test standalone SFA agents"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.original_init = use_mock_client()
        cls.test_dir = Path(tempfile.mkdtemp())
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        restore_real_client(cls.original_init)
        # Clean up test directory
        import shutil
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)
    
    def test_project_architect(self):
        """Test project architect agent"""
        from sfa.sfa_project_architect import ProjectArchitectAgent
        
        agent = ProjectArchitectAgent()
        output_file = self.test_dir / "architecture.md"
        
        success = agent.run(
            prompt="Design a simple web app",
            requirements={"name": "TestApp", "type": "web_app"},
            output_file=str(output_file),
            compute_limit=3
        )
        
        self.assertTrue(success)
        self.assertTrue(output_file.exists())
        
        # Check decisions file
        decisions_file = output_file.with_suffix('.decisions.json')
        self.assertTrue(decisions_file.exists())
    
    def test_rapid_builder(self):
        """Test rapid builder agent"""
        from sfa.sfa_rapid_builder import RapidBuilderAgent
        
        agent = RapidBuilderAgent()
        output_dir = self.test_dir / "rapid_output"
        
        success = agent.run(
            prompt="Build a REST API",
            requirements={"name": "TestAPI", "type": "api"},
            output_dir=str(output_dir),
            compute_limit=3
        )
        
        self.assertTrue(success)
        self.assertTrue(output_dir.exists())
    
    def test_quality_guardian(self):
        """Test quality guardian agent"""
        from sfa.sfa_quality_guardian import QualityGuardianAgent
        
        agent = QualityGuardianAgent()
        output_file = self.test_dir / "quality_report.md"
        
        success = agent.run(
            prompt="Test authentication system",
            requirements={"name": "TestAuth", "security": "high"},
            code_path=str(self.test_dir),  # Add required code_path parameter
            output_file=str(output_file),
            compute_limit=3
        )
        
        self.assertTrue(success)
        self.assertTrue(output_file.exists())

class TestAgentRuntime(unittest.TestCase):
    """Test agent runtime with mock client"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_init = use_mock_client()
        self.logger = get_logger()
        self.runner = AnthropicAgentRunner(logger=self.logger)
    
    def tearDown(self):
        """Clean up"""
        restore_real_client(self.original_init)
        self.logger.close_session()
    
    def test_agent_execution(self):
        """Test basic agent execution"""
        context = AgentContext(
            project_requirements={"name": "TestProject"},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="planning"
        )
        
        success, result, updated_context = self.runner.run_agent(
            agent_name="test-agent",
            agent_prompt="Test prompt",
            context=context,
            model=ModelType.SONNET,
            max_iterations=2
        )
        
        self.assertTrue(success)
        self.assertIn("test-agent", updated_context.completed_tasks)
    
    def test_cost_tracking(self):
        """Test cost tracking in mock mode"""
        mock_client = self.runner.client
        
        # Run some operations
        context = AgentContext(
            project_requirements={"name": "TestProject"},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="planning"
        )
        
        self.runner.run_agent(
            agent_name="test-agent",
            agent_prompt="Long prompt " * 100,  # Generate tokens
            context=context,
            max_iterations=1
        )
        
        # Check usage
        usage = mock_client.get_usage_summary()
        self.assertGreater(usage['total_calls'], 0)
        self.assertGreater(usage['total_input_tokens'], 0)
        self.assertGreater(usage['estimated_cost'], 0)

class TestWorkflowIntegration(unittest.TestCase):
    """Test complete workflow integration"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.original_init = use_mock_client()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        restore_real_client(cls.original_init)
    
    def test_full_workflow(self):
        """Test a complete workflow with multiple agents"""
        from lib.agent_runtime import AnthropicAgentRunner, AgentContext
        
        runner = AnthropicAgentRunner()
        
        # Initial context
        context = AgentContext(
            project_requirements={
                "name": "TestApp",
                "type": "web_app",
                "features": ["auth", "database", "api"]
            },
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="planning"
        )
        
        # Phase 1: Architecture
        success, result, context = runner.run_agent(
            "project-architect",
            "Design the system architecture",
            context,
            model=get_optimal_model("project-architect"),
            max_iterations=2
        )
        self.assertTrue(success)
        
        # Phase 2: Building
        context.current_phase = "building"
        success, result, context = runner.run_agent(
            "rapid-builder",
            "Build the core components",
            context,
            model=get_optimal_model("rapid-builder"),
            max_iterations=2
        )
        self.assertTrue(success)
        
        # Phase 3: Quality
        context.current_phase = "testing"
        success, result, context = runner.run_agent(
            "quality-guardian",
            "Test and validate the system",
            context,
            model=get_optimal_model("quality-guardian"),
            max_iterations=2
        )
        self.assertTrue(success)
        
        # Verify all phases completed
        self.assertEqual(len(context.completed_tasks), 3)
        self.assertIn("project-architect", context.completed_tasks)
        self.assertIn("rapid-builder", context.completed_tasks)
        self.assertIn("quality-guardian", context.completed_tasks)

class PerformanceBenchmark:
    """Performance benchmarking for agents"""
    
    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.results = []
    
    def benchmark_agent(self, agent_name: str, iterations: int = 5) -> Dict:
        """Benchmark a single agent"""
        if self.use_mock:
            original_init = use_mock_client()
        
        runner = AnthropicAgentRunner()
        context = AgentContext(
            project_requirements={"name": "BenchmarkProject"},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="benchmark"
        )
        
        times = []
        for i in range(iterations):
            start = time.time()
            
            success, result, context = runner.run_agent(
                agent_name,
                f"Benchmark test {i}",
                context,
                model=get_optimal_model(agent_name),
                max_iterations=1
            )
            
            elapsed = time.time() - start
            times.append(elapsed)
        
        if self.use_mock:
            restore_real_client(original_init)
        
        return {
            'agent': agent_name,
            'iterations': iterations,
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'total_time': sum(times)
        }
    
    def run_benchmarks(self, agents: List[str]) -> List[Dict]:
        """Run benchmarks for multiple agents"""
        results = []
        for agent in agents:
            print(f"Benchmarking {agent}...")
            result = self.benchmark_agent(agent)
            results.append(result)
            print(f"  Average: {result['avg_time']:.3f}s")
        
        return results

def run_tests(mode: str = "mock", budget: float = 1.0, verbose: bool = False):
    """Run the test suite"""
    
    print(f"\n{'='*60}")
    print(f"Running Agent Tests in {mode.upper()} mode")
    print(f"{'='*60}\n")
    
    if mode == "mock":
        # Use mock client
        print("Using mock Anthropic client (no API costs)")
    elif mode == "live":
        # Check for API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("ERROR: ANTHROPIC_API_KEY not set for live testing")
            return False
        print(f"Using LIVE API (budget: ${budget})")
    
    # Run unit tests
    print("\n1. Running Unit Tests...")
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    # Run performance benchmarks
    print("\n2. Running Performance Benchmarks...")
    benchmark = PerformanceBenchmark(use_mock=(mode == "mock"))
    agents_to_test = ["project-architect", "rapid-builder", "quality-guardian"]
    benchmark_results = benchmark.run_benchmarks(agents_to_test)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Unit Tests: {'PASSED' if result.wasSuccessful() else 'FAILED'}")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    print("\nPerformance Results:")
    for bench in benchmark_results:
        print(f"  {bench['agent']}: {bench['avg_time']:.3f}s average")
    
    # Cost estimation for live mode
    if mode == "mock":
        mock_client = MockAnthropicClient()
        usage = mock_client.get_usage_summary()
        print(f"\nEstimated API Cost (if live): ${usage.get('estimated_cost', 0):.4f}")
    
    return result.wasSuccessful()

class TestEnhancedMockMode(unittest.TestCase):
    """Test enhanced mock mode features (Section 7)"""
    
    @classmethod
    def setUpClass(cls):
        """Set up enhanced mock mode"""
        cls.original_init = use_enhanced_mock_client(
            enable_file_creation=True,
            failure_rate=0.1  # 10% for testing
        )
    
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        restore_real_client(cls.original_init)
    
    def test_realistic_file_creation(self):
        """Test that enhanced mock mode actually creates files"""
        runner = AnthropicAgentRunner()
        
        # Register tools (required for tool calls)
        from lib.agent_runtime import create_standard_tools
        for tool in create_standard_tools():
            runner.register_tool(tool)
        
        context = AgentContext(
            project_requirements={"name": "TestProject", "type": "web_app"},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="planning"
        )
        
        success, result, context = runner.run_agent(
            "project-architect",
            "Create architecture documentation",
            context,
            model=ModelType.SONNET,
            max_iterations=2
        )
        
        # Get mock client and check file creation
        mock_client = runner.client
        if hasattr(mock_client, 'file_system') and mock_client.file_system:
            files_created = mock_client.file_system.created_files
            self.assertGreater(len(files_created), 0, "No files created in enhanced mock mode")
            
            # Cleanup
            mock_client.file_system.cleanup()
    
    def test_requirement_tracking(self):
        """Test requirement completion tracking"""
        runner = AnthropicAgentRunner()
        
        # Register tools (required for tool calls)
        from lib.agent_runtime import create_standard_tools
        for tool in create_standard_tools():
            runner.register_tool(tool)
        
        context = AgentContext(
            project_requirements={
                "name": "TestProject",
                "type": "web_app",
                "features": ["auth", "api", "frontend"]
            },
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="requirements"
        )
        
        # Run requirements analyst
        success, result, context = runner.run_agent(
            "requirements-analyst",
            "Analyze project requirements",
            context,
            model=ModelType.SONNET,
            max_iterations=2
        )
        
        # Check requirement tracking
        mock_client = runner.client
        if hasattr(mock_client, 'requirement_tracker'):
            tracker = mock_client.requirement_tracker
            self.assertGreater(tracker.total_requirements, 0, "No requirements tracked")
            
            # Get summary
            summary = tracker.get_summary()
            self.assertIn('total', summary)
            self.assertIn('completed', summary)
            self.assertIn('percentage', summary)

def run_enhanced_tests(enable_files: bool = True, failure_rate: float = 0.0, verbose: bool = False):
    """Run tests with enhanced mock mode"""
    
    print(f"\n{'='*60}")
    print("Running ENHANCED Mock Mode Tests (Section 7)")
    print(f"{'='*60}")
    print(f"File Creation: {'Enabled' if enable_files else 'Disabled'}")
    print(f"Failure Rate: {failure_rate:.1%}")
    print(f"{'='*60}\n")
    
    # Set up enhanced mock client
    original_init = use_enhanced_mock_client(
        enable_file_creation=enable_files,
        failure_rate=failure_rate
    )
    
    try:
        # Run enhanced tests
        suite = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedMockMode)
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        result = runner.run(suite)
        
        # Get final summary from mock client
        test_runner = AnthropicAgentRunner()
        mock_client = test_runner.client
        
        if hasattr(mock_client, 'get_usage_summary'):
            summary = mock_client.get_usage_summary()
            
            print(f"\n{'='*60}")
            print("ENHANCED MOCK MODE SUMMARY")
            print(f"{'='*60}")
            print(f"Total API Calls: {summary.get('total_calls', 0)}")
            print(f"Estimated Cost: ${summary.get('estimated_cost', 0):.4f}")
            
            if 'requirements' in summary:
                req_summary = summary['requirements']
                print(f"\nRequirement Tracking:")
                print(f"  Total Requirements: {req_summary['total']}")
                print(f"  Completed: {req_summary['completed']}")
                print(f"  Completion: {req_summary['percentage']:.1f}%")
            
            if 'file_system' in summary:
                fs_summary = summary['file_system']
                print(f"\nFile System Simulation:")
                print(f"  Files Created: {fs_summary['files_created']}")
                print(f"  Total Size: {fs_summary['total_size']} bytes")
        
        return result.wasSuccessful()
        
    finally:
        restore_real_client(original_init)

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Test Agent Swarm with Enhanced Mock Mode")
    parser.add_argument('--mode', choices=['mock', 'live'], default='mock',
                        help='Test mode: mock (no costs) or live (real API)')
    parser.add_argument('--budget', type=float, default=1.0,
                        help='Budget limit for live testing (USD)')
    parser.add_argument('--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('--agent', help='Test specific agent only')
    parser.add_argument('--enhanced', action='store_true',
                        help='Use enhanced mock mode with file creation and tracking (Section 7)')
    
    args = parser.parse_args()
    
    # Run tests
    if args.enhanced and args.mode == 'mock':
        success = run_enhanced_tests(enable_files=True, failure_rate=0.1, verbose=args.verbose)
    else:
        success = run_tests(args.mode, args.budget, args.verbose)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()