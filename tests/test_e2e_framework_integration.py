#!/usr/bin/env python3
"""
Integration Tests for Enhanced E2E Test Framework

Tests the complete Phase 1 implementation:
- Advanced Workflow Engine
- Agent Interaction Validator
- Quality Metrics Collector
- Test Data Generators
"""

import unittest
import asyncio
import json
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tests.e2e_infrastructure.workflow_engine import (
    AdvancedWorkflowEngine, WorkflowPhase, RequirementPriority,
    Requirement, Checkpoint, FailureInjection, ConflictType
)
from tests.e2e_infrastructure.interaction_validator import (
    AgentInteractionValidator, AgentInteraction, InteractionType,
    CommunicationProtocol, DependencyChain
)
from tests.e2e_infrastructure.metrics_collector import (
    QualityMetricsCollector, RequirementMetric, CodeQualityMetric,
    SecurityMetric, PerformanceMetric, MetricType, QualityDimension
)
from tests.e2e_infrastructure.test_data_generators import (
    TestDataGenerator, ProjectType, ComplexityLevel
)

from lib.agent_runtime import AgentContext

class TestAdvancedWorkflowEngine(unittest.TestCase):
    """Test the Advanced Workflow Engine"""
    
    def setUp(self):
        """Set up test environment"""
        self.engine = AdvancedWorkflowEngine(
            name="test_workflow",
            use_mock=True
        )
        self.generator = TestDataGenerator(seed=42)
        
    def test_progressive_requirement_introduction(self):
        """Test progressive requirement introduction with dependencies"""
        # Generate requirements with dependencies
        requirements = [
            Requirement(
                id="REQ-001",
                description="Setup authentication",
                priority=RequirementPriority.CRITICAL,
                phase=WorkflowPhase.PLANNING,
                dependencies=[],
                agents_required=["project-architect"]
            ),
            Requirement(
                id="REQ-002",
                description="Create user API",
                priority=RequirementPriority.HIGH,
                phase=WorkflowPhase.DEVELOPMENT,
                dependencies=["REQ-001"],  # Depends on auth
                agents_required=["rapid-builder"]
            ),
            Requirement(
                id="REQ-003",
                description="Add user dashboard",
                priority=RequirementPriority.MEDIUM,
                phase=WorkflowPhase.DEVELOPMENT,
                dependencies=["REQ-001", "REQ-002"],  # Depends on both
                agents_required=["frontend-specialist"]
            )
        ]
        
        for req in requirements:
            self.engine.add_requirement(req)
            
        # Check dependency resolution
        completed = []
        self.assertTrue(requirements[0].is_ready(completed))
        self.assertFalse(requirements[1].is_ready(completed))
        self.assertFalse(requirements[2].is_ready(completed))
        
        completed.append("REQ-001")
        self.assertTrue(requirements[1].is_ready(completed))
        self.assertFalse(requirements[2].is_ready(completed))
        
        completed.append("REQ-002")
        self.assertTrue(requirements[2].is_ready(completed))
        
    def test_conflict_detection_and_resolution(self):
        """Test requirement conflict detection and resolution"""
        # Create conflicting requirements
        req1 = Requirement(
            id="REQ-TECH-001",
            description="Use REST API",
            priority=RequirementPriority.HIGH,
            phase=WorkflowPhase.PLANNING,
            conflicts_with=["REQ-TECH-002"],
            agents_required=["project-architect"]
        )
        
        req2 = Requirement(
            id="REQ-TECH-002",
            description="Use GraphQL API",
            priority=RequirementPriority.MEDIUM,
            phase=WorkflowPhase.PLANNING,
            conflicts_with=["REQ-TECH-001"],
            agents_required=["project-architect"]
        )
        
        self.engine.add_requirements_batch([req1, req2])
        
        # Test conflict detection
        active_reqs = ["REQ-TECH-001"]
        self.assertTrue(req2.has_conflict(active_reqs))
        
        # Test conflict type identification
        conflict_type = self.engine._identify_conflict_type("REQ-TECH-001", "REQ-TECH-002")
        self.assertEqual(conflict_type, ConflictType.TECHNICAL)
        
    def test_checkpoint_creation_and_restoration(self):
        """Test checkpoint creation and restoration"""
        # Set up context
        context = AgentContext(
            project_requirements={"name": "TestProject"},
            completed_tasks=["agent1", "agent2"],
            artifacts={"test": "data"},
            decisions=[],
            current_phase="development"
        )
        self.engine.set_context(context)
        
        # Run async test
        async def test_checkpoint():
            await self.engine.initialize()
            
            # Create checkpoint
            await self.engine._create_checkpoint("test_checkpoint")
            
            # Verify checkpoint was created
            self.assertEqual(len(self.engine.checkpoints), 1)
            checkpoint = self.engine.checkpoints[0]
            self.assertEqual(checkpoint.id, "test_checkpoint")
            self.assertEqual(checkpoint.phase, WorkflowPhase.INITIALIZATION)
            
            # Modify context
            self.engine.context.completed_tasks.append("agent3")
            
            # Restore from checkpoint
            success = await self.engine.restore_from_checkpoint("test_checkpoint")
            self.assertTrue(success)
            
            # Verify restoration
            self.assertEqual(len(self.engine.context.completed_tasks), 2)
            self.assertNotIn("agent3", self.engine.context.completed_tasks)
            
        asyncio.run(test_checkpoint())
        
    def test_failure_injection_and_recovery(self):
        """Test failure injection and recovery mechanisms"""
        # Configure failure injection
        failure_config = self.generator.generate_failure_injection_config(
            failure_rate=0.5,
            targeted_agents=["rapid-builder"]
        )
        self.engine.failure_injection = failure_config
        
        # Test failure detection
        self.assertTrue(failure_config.enabled)
        self.assertGreater(failure_config.agent_failure_rates["rapid-builder"], 0)
        
        # Test recovery strategy
        self.assertIn(failure_config.recovery_strategy, 
                     ["exponential_backoff", "linear_backoff", "immediate_retry"])
        self.assertGreaterEqual(failure_config.max_retries, 2)
        
    def test_quality_metrics_tracking(self):
        """Test quality metrics tracking during workflow"""
        # Run async test
        async def test_metrics():
            await self.engine.initialize()
            
            # Add requirements
            project = self.generator.generate_project_requirements(
                ProjectType.WEB_APP,
                ComplexityLevel.SIMPLE
            )
            requirements = self.generator.generate_requirements_list(project)
            
            for req in requirements[:3]:  # Test with first 3 requirements
                self.engine.add_requirement(req)
                
            # Execute workflow (partial)
            self.engine.current_phase = WorkflowPhase.PLANNING
            await self.engine._execute_phase(WorkflowPhase.PLANNING)
            
            # Check metrics
            self.assertGreater(self.engine.metrics["total_agents_executed"], 0)
            self.assertIn("planning", self.engine.metrics["phase_timings"])
            
        asyncio.run(test_metrics())


class TestAgentInteractionValidator(unittest.TestCase):
    """Test the Agent Interaction Validator"""
    
    def setUp(self):
        """Set up test environment"""
        self.validator = AgentInteractionValidator()
        self.generator = TestDataGenerator()
        
    def test_interaction_tracking_and_validation(self):
        """Test tracking and validation of agent interactions"""
        # Create test interaction
        interaction = AgentInteraction(
            id="test_interaction_1",
            source_agent="project-architect",
            target_agent="rapid-builder",
            interaction_type=InteractionType.SEQUENTIAL,
            protocol=CommunicationProtocol.CONTEXT_PASSING,
            timestamp=datetime.now(),
            data_transferred={"test": "data"},
            success=True
        )
        
        # Track interaction
        self.validator.track_interaction(interaction)
        
        # Verify tracking
        self.assertEqual(self.validator.metrics["total_interactions"], 1)
        self.assertEqual(self.validator.metrics["successful_interactions"], 1)
        
        # Test validation
        success, errors = interaction.validate()
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
        
    def test_context_passing_validation(self):
        """Test context passing validation between agents"""
        # Create contexts
        context_before = AgentContext(
            project_requirements={},
            completed_tasks=["agent1"],
            artifacts={"artifact1": "data1"},
            decisions=[{"decision": "test"}],
            current_phase="development"
        )
        
        context_after = AgentContext(
            project_requirements={},
            completed_tasks=["agent1", "agent2"],
            artifacts={"artifact1": "data1", "artifact2": "data2"},
            decisions=[{"decision": "test"}],
            current_phase="development"
        )
        
        # Validate context passing
        success, errors = self.validator.validate_context_passing(
            context_before,
            context_after,
            "agent2"
        )
        
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
        
        # Test context loss detection
        context_bad = AgentContext(
            project_requirements={},
            completed_tasks=["agent1"],  # agent2 not added
            artifacts={"artifact2": "data2"},  # artifact1 lost
            decisions=[],  # decisions lost
            current_phase="development"
        )
        
        success, errors = self.validator.validate_context_passing(
            context_before,
            context_bad,
            "agent2"
        )
        
        self.assertFalse(success)
        self.assertGreater(len(errors), 0)
        
    def test_dependency_chain_building(self):
        """Test building dependency chains between agents"""
        # Create interaction graph
        interactions = [
            ("project-architect", "rapid-builder"),
            ("rapid-builder", "frontend-specialist"),
            ("rapid-builder", "api-integrator"),
            ("frontend-specialist", "quality-guardian"),
            ("api-integrator", "quality-guardian")
        ]
        
        for source, target in interactions:
            interaction = AgentInteraction(
                id=f"{source}_{target}",
                source_agent=source,
                target_agent=target,
                interaction_type=InteractionType.SEQUENTIAL,
                protocol=CommunicationProtocol.ARTIFACT_SHARING,
                timestamp=datetime.now(),
                artifacts_shared=["test.json"]
            )
            self.validator.track_interaction(interaction)
            
        # Build dependency chain
        context = AgentContext(
            project_requirements={},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="development"
        )
        
        chain = self.validator.build_dependency_chain(
            "project-architect",
            "quality-guardian",
            context
        )
        
        # Verify chain
        self.assertIsNotNone(chain)
        self.assertIn("project-architect", chain.agents)
        self.assertIn("quality-guardian", chain.agents)
        self.assertTrue(chain.is_complete())
        
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies"""
        # Create circular dependency
        interactions = [
            ("agent1", "agent2"),
            ("agent2", "agent3"),
            ("agent3", "agent1")  # Creates cycle
        ]
        
        for source, target in interactions:
            interaction = AgentInteraction(
                id=f"{source}_{target}",
                source_agent=source,
                target_agent=target,
                interaction_type=InteractionType.SEQUENTIAL,
                protocol=CommunicationProtocol.CONTEXT_PASSING,
                timestamp=datetime.now(),
                data_transferred={"test": "data"}
            )
            self.validator.track_interaction(interaction)
            
        # Detect cycles
        cycles = self.validator.detect_circular_dependencies()
        self.assertGreater(len(cycles), 0)
        
    def test_tool_usage_analysis(self):
        """Test tool usage pattern analysis"""
        # Track tool usage
        for i in range(10):
            self.validator.analyze_tool_usage(
                agent_name="rapid-builder",
                tool_name="write_file",
                parameters={"file_path": f"test_{i}.py"},
                execution_time_ms=100 + i * 10,
                success=i < 8  # 80% success rate
            )
            
        # Check patterns
        pattern_key = "rapid-builder_write_file"
        self.assertIn(pattern_key, self.validator.tool_patterns)
        
        pattern = self.validator.tool_patterns[pattern_key]
        self.assertEqual(pattern.usage_count, 10)
        self.assertEqual(pattern.success_count, 8)
        self.assertEqual(pattern.failure_count, 2)
        self.assertEqual(pattern.success_rate, 80.0)
        
    def test_interaction_pattern_analysis(self):
        """Test overall interaction pattern analysis"""
        # Create complex interaction patterns
        # Sequential chain
        for i in range(3):
            interaction = AgentInteraction(
                id=f"seq_{i}",
                source_agent=f"agent{i}",
                target_agent=f"agent{i+1}",
                interaction_type=InteractionType.SEQUENTIAL,
                protocol=CommunicationProtocol.CONTEXT_PASSING,
                timestamp=datetime.now(),
                data_transferred={"test": "data"}
            )
            self.validator.track_interaction(interaction)
            
        # Parallel group
        for i in range(2, 5):
            interaction = AgentInteraction(
                id=f"parallel_{i}",
                source_agent="agent1",
                target_agent=f"parallel_agent{i}",
                interaction_type=InteractionType.PARALLEL,
                protocol=CommunicationProtocol.ARTIFACT_SHARING,
                timestamp=datetime.now(),
                artifacts_shared=["shared.json"]
            )
            self.validator.track_interaction(interaction)
            
        # Analyze patterns
        patterns = self.validator.analyze_interaction_patterns()
        
        self.assertIn("sequential_chains", patterns)
        self.assertIn("parallel_groups", patterns)
        self.assertGreater(len(patterns["sequential_chains"]), 0)


class TestQualityMetricsCollector(unittest.TestCase):
    """Test the Quality Metrics Collector"""
    
    def setUp(self):
        """Set up test environment"""
        self.collector = QualityMetricsCollector("TestProject")
        self.generator = TestDataGenerator()
        
    def test_requirement_metric_tracking(self):
        """Test requirement metric tracking and calculation"""
        # Create requirement metric
        metric = RequirementMetric(
            requirement_id="REQ-001",
            description="User authentication",
            priority="critical",
            agents_assigned=["project-architect", "rapid-builder"],
            files_created=["auth.py", "user_model.py"],
            acceptance_criteria={
                "implemented": True,
                "tested": True,
                "documented": False,
                "secure": True
            }
        )
        
        # Calculate completion
        completion = metric.calculate_completion()
        self.assertEqual(completion, 75.0)  # 3 out of 4 criteria met
        
        # Track metric
        self.collector.track_requirement(metric)
        self.assertEqual(self.collector.aggregate_metrics["total_requirements"], 1)
        
    def test_code_quality_analysis(self):
        """Test code quality metric analysis"""
        # Create a test Python file
        test_file = Path("test_quality_file.py")
        test_code = '''
def calculate_complexity(x, y, z):
    """Calculate something complex"""
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            else:
                return x + y
        else:
            return x
    else:
        return 0
        
# Duplicate code
def calculate_complexity_2(x, y, z):
    """Calculate something complex"""
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
'''
        
        test_file.write_text(test_code)
        
        try:
            # Analyze file
            self.collector.track_code_quality(str(test_file))
            
            # Check metrics
            self.assertIn(str(test_file), self.collector.code_quality_metrics)
            metric = self.collector.code_quality_metrics[str(test_file)]
            
            self.assertEqual(metric.language, "python")
            self.assertGreater(metric.lines_of_code, 0)
            self.assertGreater(metric.cyclomatic_complexity, 1)
            self.assertGreater(metric.duplication_percentage, 0)
            
        finally:
            # Clean up
            test_file.unlink()
            
    def test_security_compliance_scoring(self):
        """Test security compliance scoring"""
        # Create security metric
        metric = SecurityMetric(
            scan_timestamp=datetime.now(),
            vulnerabilities={
                "critical": [],
                "high": ["SQL injection risk"],
                "medium": ["Weak password policy", "Missing HTTPS"],
                "low": ["Verbose error messages"]
            },
            compliance_checks={
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "authentication": True,
                "authorization": False,
                "audit_logging": True
            }
        )
        
        # Calculate compliance score
        score = metric.compliance_score
        # Base score: 4/5 checks = 80%
        # Penalty: 1 high (10) + 2 medium (10) = 20
        # Expected: 80 - 20 = 60
        self.assertEqual(score, 60.0)
        
        # Track metric
        self.collector.track_security(metric)
        self.assertEqual(len(self.collector.security_metrics), 1)
        
    def test_performance_benchmark_tracking(self):
        """Test performance benchmark tracking"""
        # Create performance metrics
        for i in range(5):
            metric = PerformanceMetric(
                operation=f"api_endpoint_{i}",
                execution_time_ms=100 + i * 20,
                memory_usage_mb=50 + i * 10,
                cpu_usage_percent=20 + i * 5,
                throughput=1000 - i * 100,
                latency_p50=80 + i * 10,
                latency_p95=150 + i * 20,
                latency_p99=200 + i * 30,
                error_rate=0.01 * i
            )
            self.collector.track_performance(metric)
            
        # Check SLA compliance
        sla = {
            "max_latency_p95": 200,
            "min_throughput": 500,
            "max_error_rate": 0.02
        }
        
        score = self.collector.calculate_performance_score(sla)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
        
    def test_quality_dimension_evaluation(self):
        """Test evaluation of quality dimensions"""
        # Add sample metrics
        req_metric = RequirementMetric(
            requirement_id="REQ-001",
            description="Test requirement",
            priority="high",
            acceptance_criteria={"test": True}
        )
        req_metric.completion_percentage = 80
        self.collector.track_requirement(req_metric)
        
        # Evaluate dimensions
        dimensions = self.collector.evaluate_quality_dimensions()
        
        # Check all dimensions are present
        for dim in QualityDimension:
            self.assertIn(dim.value, dimensions)
            self.assertGreaterEqual(dimensions[dim.value], 0)
            self.assertLessEqual(dimensions[dim.value], 100)
            
    def test_threshold_checking(self):
        """Test quality threshold checking"""
        # Set up metrics to test thresholds
        self.collector.aggregate_metrics["average_completion"] = 75  # Below 80 threshold
        self.collector.aggregate_metrics["average_code_quality"] = 85  # Above 70 threshold
        self.collector.aggregate_metrics["security_compliance"] = 90  # Above 85 threshold
        
        # Check thresholds
        results = self.collector.check_thresholds()
        
        self.assertFalse(results["requirement_coverage"])  # 75 < 80
        self.assertTrue(results["code_quality"])  # 85 > 70
        self.assertTrue(results["security_compliance"])  # 90 > 85
        
    def test_comprehensive_quality_report(self):
        """Test generation of comprehensive quality report"""
        # Add various metrics
        project = self.generator.generate_project_requirements(
            ProjectType.WEB_APP,
            ComplexityLevel.SIMPLE
        )
        
        # Add requirement metrics
        for i, feature in enumerate(project["features"][:3]):
            metric = RequirementMetric(
                requirement_id=f"REQ-{i+1:03d}",
                description=feature,
                priority="high",
                acceptance_criteria={"implemented": True, "tested": i > 0}
            )
            metric.calculate_completion()
            self.collector.track_requirement(metric)
            
        # Generate report
        report = self.collector.generate_quality_report()
        
        # Verify report structure
        self.assertIn("project_name", report)
        self.assertIn("summary", report)
        self.assertIn("quality_dimensions", report)
        self.assertIn("threshold_compliance", report)
        self.assertIn("recommendations", report)
        
        # Check summary metrics
        self.assertEqual(report["project_name"], "TestProject")
        self.assertGreater(report["summary"]["overall_quality_score"], 0)


class TestDataGenerators(unittest.TestCase):
    """Test the Test Data Generators"""
    
    def setUp(self):
        """Set up test environment"""
        self.generator = TestDataGenerator(seed=42)
        
    def test_project_requirements_generation(self):
        """Test generation of project requirements"""
        # Generate for different project types and complexities
        for project_type in [ProjectType.WEB_APP, ProjectType.API_SERVICE]:
            for complexity in [ComplexityLevel.SIMPLE, ComplexityLevel.COMPLEX]:
                project = self.generator.generate_project_requirements(
                    project_type,
                    complexity
                )
                
                # Verify structure
                self.assertIn("name", project)
                self.assertIn("features", project)
                self.assertIn("tech_stack", project)
                self.assertIn("constraints", project)
                self.assertIn("success_metrics", project)
                
                # Verify complexity matches feature count
                if complexity == ComplexityLevel.SIMPLE:
                    self.assertLessEqual(len(project["features"]), 5)
                elif complexity == ComplexityLevel.COMPLEX:
                    self.assertGreaterEqual(len(project["features"]), 11)
                    
    def test_requirements_list_generation(self):
        """Test generation of Requirement objects"""
        project = self.generator.generate_project_requirements(
            ProjectType.WEB_APP,
            ComplexityLevel.MEDIUM
        )
        
        requirements = self.generator.generate_requirements_list(
            project,
            include_conflicts=True
        )
        
        # Verify requirements
        self.assertGreater(len(requirements), 0)
        self.assertEqual(len(requirements), len(project["features"]))
        
        # Check for conflicts
        has_conflicts = any(req.conflicts_with for req in requirements)
        self.assertTrue(has_conflicts)  # Should have some conflicts
        
        # Check dependencies
        has_dependencies = any(req.dependencies for req in requirements)
        self.assertTrue(has_dependencies)  # Should have some dependencies
        
    def test_failure_injection_generation(self):
        """Test generation of failure injection configs"""
        config = self.generator.generate_failure_injection_config(
            failure_rate=0.2,
            targeted_agents=["rapid-builder", "frontend-specialist"]
        )
        
        # Verify configuration
        self.assertTrue(config.enabled)
        self.assertGreater(config.agent_failure_rates["rapid-builder"], 0.2)
        self.assertGreater(config.agent_failure_rates["frontend-specialist"], 0.2)
        
        # Check other agents have lower rates
        self.assertLess(config.agent_failure_rates.get("documentation-writer", 0), 0.4)
        
    def test_mock_agent_response_generation(self):
        """Test generation of mock agent responses"""
        # Test successful response
        response = self.generator.generate_mock_agent_response(
            "rapid-builder",
            "Create user API",
            success=True
        )
        
        self.assertTrue(response["success"])
        self.assertIn("files_created", response)
        self.assertGreater(len(response["files_created"]), 0)
        self.assertIn("tools_used", response)
        
        # Test failure response
        response = self.generator.generate_mock_agent_response(
            "rapid-builder",
            "Create user API",
            success=False
        )
        
        self.assertFalse(response["success"])
        self.assertIn("error", response)
        self.assertIn("error_details", response)
        
    def test_quality_metrics_generation(self):
        """Test generation of quality metrics"""
        metrics = self.generator.generate_quality_metrics(
            "REQ-001",
            completion_level=0.9
        )
        
        # Verify metrics
        self.assertIn("completion_percentage", metrics)
        self.assertIn("code_quality_score", metrics)
        self.assertIn("test_coverage", metrics)
        
        # Check ranges
        self.assertGreaterEqual(metrics["completion_percentage"], 0)
        self.assertLessEqual(metrics["completion_percentage"], 100)
        self.assertGreaterEqual(metrics["code_quality_score"], 0)
        self.assertLessEqual(metrics["code_quality_score"], 100)


class TestE2EIntegration(unittest.TestCase):
    """Integration tests combining all components"""
    
    def test_complete_workflow_execution(self):
        """Test complete E2E workflow with all components"""
        # Initialize components
        generator = TestDataGenerator(seed=42)
        engine = AdvancedWorkflowEngine("integration_test", use_mock=True)
        validator = AgentInteractionValidator()
        collector = QualityMetricsCollector("IntegrationTest")
        
        # Generate test project
        project = generator.generate_project_requirements(
            ProjectType.WEB_APP,
            ComplexityLevel.SIMPLE
        )
        
        requirements = generator.generate_requirements_list(project)
        
        # Add requirements to engine
        for req in requirements[:3]:  # Test with subset
            engine.add_requirement(req)
            
        # Run async workflow
        async def run_workflow():
            # Initialize engine
            await engine.initialize()
            
            # Execute planning phase
            await engine._execute_phase(WorkflowPhase.PLANNING)
            
            # Simulate agent interactions
            for i in range(len(requirements[:2])):
                interaction = AgentInteraction(
                    id=f"interaction_{i}",
                    source_agent=requirements[i].agents_required[0] if requirements[i].agents_required else "unknown",
                    target_agent=requirements[i+1].agents_required[0] if requirements[i+1].agents_required else "unknown",
                    interaction_type=InteractionType.SEQUENTIAL,
                    protocol=CommunicationProtocol.CONTEXT_PASSING,
                    timestamp=datetime.now(),
                    data_transferred={"requirement": requirements[i].id}
                )
                validator.track_interaction(interaction)
                
                # Track requirement completion
                req_metric = RequirementMetric(
                    requirement_id=requirements[i].id,
                    description=requirements[i].description,
                    priority=requirements[i].priority.value,
                    agents_assigned=requirements[i].agents_required,
                    acceptance_criteria=requirements[i].acceptance_criteria
                )
                req_metric.completion_percentage = 80 + i * 10
                collector.track_requirement(req_metric)
                
            # Generate reports
            workflow_report = engine._generate_report()
            interaction_report = validator.generate_validation_report()
            quality_report = collector.generate_quality_report()
            
            return workflow_report, interaction_report, quality_report
            
        # Execute workflow
        workflow_report, interaction_report, quality_report = asyncio.run(run_workflow())
        
        # Verify reports
        self.assertIsNotNone(workflow_report)
        self.assertIn("requirements", workflow_report)
        
        self.assertIsNotNone(interaction_report)
        self.assertIn("summary", interaction_report)
        
        self.assertIsNotNone(quality_report)
        self.assertIn("overall_quality_score", quality_report["summary"])


if __name__ == "__main__":
    # Run tests
    unittest.main()