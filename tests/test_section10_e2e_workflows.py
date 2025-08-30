#!/usr/bin/env python3
"""
Section 10: End-to-End Workflow Testing Suite

Comprehensive test suite that validates complete workflows from requirements
to deliverables, ensuring all agents work together correctly and requirements
are fully satisfied.
"""

import os
import sys
import json
import time
import tempfile
import unittest
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from lib.agent_runtime import AnthropicAgentRunner, AgentContext, ModelType, create_standard_tools
from lib.mock_anthropic_enhanced import use_enhanced_mock_client, restore_real_client
from lib.session_manager import SessionManager
from lib.agent_logger import get_logger
from lib.quality_validation import validate_requirements_tool, generate_completion_report_tool
from lib.session_analysis_enhanced import SessionAnalysisEngine, RequirementCoverageAnalyzer

@dataclass
class WorkflowTestCase:
    """Defines a complete workflow test case"""
    name: str
    project_type: str
    requirements: Dict
    expected_agents: List[str]
    expected_files: List[str]
    success_criteria: Dict[str, any]
    timeout_seconds: int = 300

@dataclass
class WorkflowResult:
    """Results of a workflow execution"""
    success: bool
    agents_executed: List[str]
    files_created: List[str]
    completion_percentage: float
    errors: List[str]
    execution_time: float
    requirements_satisfied: Dict[str, bool]

class EndToEndWorkflowTests(unittest.TestCase):
    """Comprehensive E2E workflow tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_dir = Path(tempfile.mkdtemp(prefix="e2e_workflow_"))
        cls.original_cwd = os.getcwd()
        os.chdir(cls.test_dir)
        
        # Use enhanced mock client for predictable results
        use_enhanced_mock_client()
        
        cls.logger = get_logger()
        cls.session_manager = SessionManager()
        cls.analysis_engine = SessionAnalysisEngine()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        os.chdir(cls.original_cwd)
        shutil.rmtree(cls.test_dir, ignore_errors=True)
        restore_real_client()
    
    def test_simple_api_workflow(self):
        """Test complete API service workflow"""
        test_case = WorkflowTestCase(
            name="Simple API Service",
            project_type="api_service",
            requirements={
                "name": "TaskAPI",
                "features": ["user_auth", "task_crud", "api_docs"],
                "tech_stack": {"backend": "fastapi", "database": "postgresql"}
            },
            expected_agents=["project-architect", "rapid-builder", "quality-guardian"],
            expected_files=["main.py", "requirements.txt", "README.md"],
            success_criteria={
                "min_files": 5,
                "has_tests": True,
                "has_docs": True,
                "completion_threshold": 80.0
            }
        )
        
        result = self._execute_workflow(test_case)
        self.assertTrue(result.success, f"Workflow failed: {result.errors}")
        self.assertGreaterEqual(result.completion_percentage, 80.0)
        self.assertIn("project-architect", result.agents_executed)
        self.assertIn("rapid-builder", result.agents_executed)
        
    def test_fullstack_webapp_workflow(self):
        """Test complete full-stack web application workflow"""
        test_case = WorkflowTestCase(
            name="Full-Stack Web App",
            project_type="full_stack_webapp",
            requirements={
                "name": "TaskManager",
                "features": ["user_auth", "task_management", "real_time_updates", "dashboard"],
                "tech_stack": {
                    "frontend": "react_typescript",
                    "backend": "fastapi", 
                    "database": "postgresql",
                    "cache": "redis"
                }
            },
            expected_agents=["project-architect", "rapid-builder", "frontend-specialist", "quality-guardian", "devops-engineer"],
            expected_files=["main.py", "package.json", "Dockerfile", "docker-compose.yml"],
            success_criteria={
                "min_files": 15,
                "has_frontend": True,
                "has_backend": True,
                "has_tests": True,
                "has_deployment": True,
                "completion_threshold": 70.0
            },
            timeout_seconds=600
        )
        
        result = self._execute_workflow(test_case)
        self.assertTrue(result.success, f"Workflow failed: {result.errors}")
        self.assertGreaterEqual(result.completion_percentage, 70.0)
        self.assertIn("frontend-specialist", result.agents_executed)
        self.assertIn("devops-engineer", result.agents_executed)
        
    def test_ai_integration_workflow(self):
        """Test workflow with AI features"""
        test_case = WorkflowTestCase(
            name="AI-Powered App",
            project_type="ai_solution",
            requirements={
                "name": "SmartTasker",
                "features": ["task_categorization", "priority_prediction", "smart_scheduling"],
                "ai_features": ["openai_integration", "task_analysis", "recommendation_engine"],
                "tech_stack": {"backend": "fastapi", "ai": "openai", "database": "postgresql"}
            },
            expected_agents=["project-architect", "ai-specialist", "rapid-builder", "quality-guardian"],
            expected_files=["main.py", "ai_client.py", "requirements.txt"],
            success_criteria={
                "min_files": 8,
                "has_ai_integration": True,
                "has_tests": True,
                "completion_threshold": 75.0
            }
        )
        
        result = self._execute_workflow(test_case)
        self.assertTrue(result.success, f"Workflow failed: {result.errors}")
        self.assertGreaterEqual(result.completion_percentage, 75.0)
        self.assertIn("ai-specialist", result.agents_executed)
        
    def test_legacy_migration_workflow(self):
        """Test legacy system migration workflow"""
        # Create some legacy files first
        legacy_dir = self.test_dir / "legacy_system"
        legacy_dir.mkdir(exist_ok=True)
        (legacy_dir / "old_app.py").write_text("# Legacy Python 2.7 app\nprint 'Hello World'")
        (legacy_dir / "requirements.txt").write_text("Django==1.8\nMySQL-python==1.2.3")
        
        test_case = WorkflowTestCase(
            name="Legacy Migration",
            project_type="migration_project",
            requirements={
                "name": "LegacyMigration",
                "migration_type": "python2_to_python3",
                "target_stack": {"backend": "fastapi", "database": "postgresql"},
                "preserve_features": ["user_auth", "data_export"]
            },
            expected_agents=["code-migrator", "rapid-builder", "quality-guardian"],
            expected_files=["main.py", "requirements.txt", "migration_report.md"],
            success_criteria={
                "min_files": 6,
                "has_migration_report": True,
                "has_tests": True,
                "completion_threshold": 65.0
            }
        )
        
        result = self._execute_workflow(test_case)
        self.assertTrue(result.success, f"Workflow failed: {result.errors}")
        self.assertIn("code-migrator", result.agents_executed)
        
    def test_performance_critical_workflow(self):
        """Test workflow with performance requirements"""
        test_case = WorkflowTestCase(
            name="High-Performance API",
            project_type="high_performance_api",
            requirements={
                "name": "FastAPI",
                "performance_requirements": {
                    "response_time": "< 100ms",
                    "throughput": "> 1000 rps",
                    "memory_usage": "< 512MB"
                },
                "features": ["caching", "connection_pooling", "async_processing"],
                "tech_stack": {"backend": "fastapi", "cache": "redis", "database": "postgresql"}
            },
            expected_agents=["project-architect", "rapid-builder", "performance-optimizer", "quality-guardian"],
            expected_files=["main.py", "cache_config.py", "performance_tests.py"],
            success_criteria={
                "min_files": 8,
                "has_performance_tests": True,
                "has_caching": True,
                "completion_threshold": 80.0
            }
        )
        
        result = self._execute_workflow(test_case)
        self.assertTrue(result.success, f"Workflow failed: {result.errors}")
        self.assertIn("performance-optimizer", result.agents_executed)
        
    def test_multi_service_workflow(self):
        """Test workflow with multiple microservices"""
        test_case = WorkflowTestCase(
            name="Microservices Architecture",
            project_type="microservices",
            requirements={
                "name": "TaskPlatform",
                "services": ["user_service", "task_service", "notification_service", "gateway"],
                "features": ["service_discovery", "load_balancing", "monitoring"],
                "tech_stack": {"backend": "fastapi", "database": "postgresql", "cache": "redis"}
            },
            expected_agents=["project-architect", "rapid-builder", "devops-engineer", "quality-guardian"],
            expected_files=["docker-compose.yml", "gateway/main.py", "user_service/main.py"],
            success_criteria={
                "min_files": 12,
                "has_multiple_services": True,
                "has_orchestration": True,
                "completion_threshold": 70.0
            },
            timeout_seconds=900
        )
        
        result = self._execute_workflow(test_case)
        self.assertTrue(result.success, f"Workflow failed: {result.errors}")
        self.assertIn("devops-engineer", result.agents_executed)
        
    def _execute_workflow(self, test_case: WorkflowTestCase) -> WorkflowResult:
        """Execute a complete workflow and return results"""
        start_time = time.time()
        errors = []
        agents_executed = []
        files_created = []
        
        try:
            # Create session
            session = self.session_manager.create_session(
                project_type=test_case.project_type,
                requirements=test_case.requirements,
                tags=["e2e_test", test_case.name.lower().replace(" ", "_")]
            )
            
            # Initialize agent runtime
            runtime = AnthropicAgentRunner(logger=self.logger)
            
            # Register standard tools
            for tool in create_standard_tools():
                runtime.register_tool(tool)
            
            # Create initial context
            context = AgentContext(
                project_requirements=test_case.requirements,
                completed_tasks=[],
                artifacts={},
                decisions=[],
                current_phase="initialization"
            )
            
            # Execute agents based on project type
            agent_sequence = self._get_agent_sequence(test_case.project_type, test_case.requirements)
            
            for agent_name in agent_sequence:
                if time.time() - start_time > test_case.timeout_seconds:
                    errors.append(f"Timeout exceeded for workflow {test_case.name}")
                    break
                    
                try:
                    # Load agent prompt (simulate)
                    agent_prompt = self._get_agent_prompt(agent_name, test_case.requirements)
                    
                    # Execute agent
                    success, result, updated_context = runtime.run_agent(
                        agent_name=agent_name,
                        agent_prompt=agent_prompt,
                        context=context,
                        model=self._get_model_for_agent(agent_name),
                        max_iterations=5
                    )
                    
                    if success:
                        agents_executed.append(agent_name)
                        context = updated_context
                        
                        # Track files created by this agent
                        if agent_name in context.created_files:
                            files_created.extend([f["path"] for f in context.created_files[agent_name]])
                    else:
                        errors.append(f"Agent {agent_name} failed: {result}")
                        
                except Exception as e:
                    errors.append(f"Exception in agent {agent_name}: {str(e)}")
            
            # Analyze completion
            completion_percentage = self._calculate_completion(test_case, context, files_created)
            requirements_satisfied = self._check_requirements(test_case, context, files_created)
            
            # Validate success criteria
            success = self._validate_success_criteria(test_case, agents_executed, files_created, completion_percentage)
            
            return WorkflowResult(
                success=success and len(errors) == 0,
                agents_executed=agents_executed,
                files_created=files_created,
                completion_percentage=completion_percentage,
                errors=errors,
                execution_time=time.time() - start_time,
                requirements_satisfied=requirements_satisfied
            )
            
        except Exception as e:
            errors.append(f"Workflow execution failed: {str(e)}")
            return WorkflowResult(
                success=False,
                agents_executed=agents_executed,
                files_created=files_created,
                completion_percentage=0.0,
                errors=errors,
                execution_time=time.time() - start_time,
                requirements_satisfied={}
            )
    
    def _get_agent_sequence(self, project_type: str, requirements: Dict) -> List[str]:
        """Determine agent execution sequence based on project type"""
        sequences = {
            "api_service": ["project-architect", "rapid-builder", "quality-guardian"],
            "full_stack_webapp": ["project-architect", "rapid-builder", "frontend-specialist", "quality-guardian", "devops-engineer"],
            "ai_solution": ["project-architect", "ai-specialist", "rapid-builder", "quality-guardian"],
            "migration_project": ["code-migrator", "rapid-builder", "quality-guardian"],
            "high_performance_api": ["project-architect", "rapid-builder", "performance-optimizer", "quality-guardian"],
            "microservices": ["project-architect", "rapid-builder", "devops-engineer", "quality-guardian"]
        }
        
        base_sequence = sequences.get(project_type, ["project-architect", "rapid-builder", "quality-guardian"])
        
        # Add documentation if required
        if requirements.get("needs_docs", True):
            base_sequence.insert(-1, "documentation-writer")
        
        return base_sequence
    
    def _get_agent_prompt(self, agent_name: str, requirements: Dict) -> str:
        """Generate agent-specific prompt"""
        prompts = {
            "project-architect": f"Design the architecture for {requirements.get('name', 'the project')} with requirements: {json.dumps(requirements, indent=2)}",
            "rapid-builder": f"Build the core implementation for {requirements.get('name', 'the project')} based on the architecture",
            "frontend-specialist": f"Create the frontend for {requirements.get('name', 'the project')} using React and TypeScript",
            "ai-specialist": f"Implement AI features for {requirements.get('name', 'the project')}: {requirements.get('ai_features', [])}",
            "quality-guardian": f"Test and validate {requirements.get('name', 'the project')} ensuring all requirements are met",
            "devops-engineer": f"Setup deployment and infrastructure for {requirements.get('name', 'the project')}",
            "performance-optimizer": f"Optimize performance for {requirements.get('name', 'the project')} with requirements: {requirements.get('performance_requirements', {})}",
            "code-migrator": f"Migrate legacy code for {requirements.get('name', 'the project')} from {requirements.get('migration_type', 'legacy system')}",
            "documentation-writer": f"Create comprehensive documentation for {requirements.get('name', 'the project')}"
        }
        
        return prompts.get(agent_name, f"Work on {requirements.get('name', 'the project')} as {agent_name}")
    
    def _get_model_for_agent(self, agent_name: str) -> ModelType:
        """Get appropriate model for agent"""
        opus_agents = ["project-architect", "ai-specialist", "debug-specialist"]
        haiku_agents = ["documentation-writer", "api-integrator"]
        
        if agent_name in opus_agents:
            return ModelType.OPUS
        elif agent_name in haiku_agents:
            return ModelType.HAIKU
        else:
            return ModelType.SONNET
    
    def _calculate_completion(self, test_case: WorkflowTestCase, context: AgentContext, files_created: List[str]) -> float:
        """Calculate workflow completion percentage"""
        total_score = 0
        max_score = 0
        
        # Agent execution score (40%)
        max_score += 40
        executed_agents = len([a for a in test_case.expected_agents if a in context.completed_tasks])
        total_score += (executed_agents / len(test_case.expected_agents)) * 40
        
        # File creation score (30%)
        max_score += 30
        created_files = len([f for f in test_case.expected_files if any(f in created for created in files_created)])
        if test_case.expected_files:
            total_score += (created_files / len(test_case.expected_files)) * 30
        else:
            total_score += 30  # No specific files expected
        
        # Requirements satisfaction score (30%)
        max_score += 30
        features = test_case.requirements.get('features', [])
        if features:
            # Simulate feature completion check
            completed_features = min(len(features), len(context.artifacts))
            total_score += (completed_features / len(features)) * 30
        else:
            total_score += 30
        
        return min(100.0, (total_score / max_score) * 100)
    
    def _check_requirements(self, test_case: WorkflowTestCase, context: AgentContext, files_created: List[str]) -> Dict[str, bool]:
        """Check which requirements were satisfied"""
        satisfied = {}
        
        # Check feature requirements
        for feature in test_case.requirements.get('features', []):
            # Simple heuristic: if feature mentioned in artifacts or files created
            satisfied[f"feature_{feature}"] = (
                any(feature in str(artifact) for artifact in context.artifacts.values()) or
                any(feature in file_path for file_path in files_created)
            )
        
        # Check technical requirements
        tech_stack = test_case.requirements.get('tech_stack', {})
        for component, technology in tech_stack.items():
            satisfied[f"tech_{component}_{technology}"] = any(
                technology in file_path or technology in str(artifact)
                for artifact in context.artifacts.values()
                for file_path in files_created
            )
        
        return satisfied
    
    def _validate_success_criteria(self, test_case: WorkflowTestCase, agents_executed: List[str], files_created: List[str], completion_percentage: float) -> bool:
        """Validate workflow success criteria"""
        criteria = test_case.success_criteria
        
        # Check minimum files
        if "min_files" in criteria and len(files_created) < criteria["min_files"]:
            return False
        
        # Check completion threshold
        if completion_percentage < criteria.get("completion_threshold", 80.0):
            return False
        
        # Check specific requirements
        if criteria.get("has_tests", False) and not any("test" in f for f in files_created):
            return False
        
        if criteria.get("has_docs", False) and not any(f.endswith(".md") for f in files_created):
            return False
        
        if criteria.get("has_frontend", False) and "frontend-specialist" not in agents_executed:
            return False
        
        if criteria.get("has_backend", False) and "rapid-builder" not in agents_executed:
            return False
        
        if criteria.get("has_deployment", False) and "devops-engineer" not in agents_executed:
            return False
        
        return True

class WorkflowRegressionTests(unittest.TestCase):
    """Test for workflow regressions and consistency"""
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="regression_"))
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        use_enhanced_mock_client()
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        restore_real_client()
    
    def test_workflow_consistency(self):
        """Test that same requirements produce consistent results"""
        requirements = {
            "name": "ConsistencyTest",
            "features": ["auth", "crud"],
            "tech_stack": {"backend": "fastapi"}
        }
        
        results = []
        for i in range(3):  # Run 3 times
            result = self._run_simple_workflow(requirements)
            results.append(result)
        
        # Check consistency
        agent_sets = [set(r.agents_executed) for r in results]
        self.assertTrue(all(agents == agent_sets[0] for agents in agent_sets),
                       "Agent execution should be consistent across runs")
        
        completion_percentages = [r.completion_percentage for r in results]
        self.assertTrue(all(abs(p - completion_percentages[0]) < 5.0 for p in completion_percentages),
                       "Completion percentages should be consistent")
    
    def test_requirement_edge_cases(self):
        """Test edge cases in requirement handling"""
        edge_cases = [
            {"name": "EmptyFeatures", "features": []},
            {"name": "NoTechStack"},
            {"name": "SpecialChars", "features": ["auth@#$", "crud!"]},
            {"name": "VeryLongName" * 10, "features": ["feature"] * 50}
        ]
        
        for requirements in edge_cases:
            result = self._run_simple_workflow(requirements)
            self.assertTrue(result.success, f"Edge case failed: {requirements}")
    
    def _run_simple_workflow(self, requirements: Dict) -> WorkflowResult:
        """Run a simple workflow for testing"""
        runtime = AnthropicAgentRunner(logger=get_logger())
        
        for tool in create_standard_tools():
            runtime.register_tool(tool)
        
        context = AgentContext(
            project_requirements=requirements,
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="testing"
        )
        
        agents_executed = []
        files_created = []
        
        for agent_name in ["project-architect", "rapid-builder"]:
            success, result, context = runtime.run_agent(
                agent_name=agent_name,
                agent_prompt=f"Work on {requirements.get('name', 'project')}",
                context=context,
                model=ModelType.SONNET,
                max_iterations=3
            )
            
            if success:
                agents_executed.append(agent_name)
                if agent_name in context.created_files:
                    files_created.extend([f["path"] for f in context.created_files[agent_name]])
        
        return WorkflowResult(
            success=len(agents_executed) >= 2,
            agents_executed=agents_executed,
            files_created=files_created,
            completion_percentage=len(agents_executed) * 50.0,
            errors=[],
            execution_time=1.0,
            requirements_satisfied={}
        )

class WorkflowBenchmarks(unittest.TestCase):
    """Performance benchmarks for workflows"""
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="benchmark_"))
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        use_enhanced_mock_client()
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        restore_real_client()
    
    def test_workflow_performance_benchmarks(self):
        """Benchmark different workflow types"""
        benchmarks = {
            "simple_api": {"agents": 3, "expected_time": 30},
            "fullstack": {"agents": 5, "expected_time": 60},
            "microservices": {"agents": 4, "expected_time": 90}
        }
        
        results = {}
        for workflow_type, expectations in benchmarks.items():
            start_time = time.time()
            
            # Run simplified workflow
            result = self._benchmark_workflow(workflow_type, expectations["agents"])
            
            execution_time = time.time() - start_time
            results[workflow_type] = {
                "execution_time": execution_time,
                "success": result,
                "expected_time": expectations["expected_time"]
            }
            
            # Allow some flexibility in timing (2x expected is acceptable for mock)
            self.assertLess(execution_time, expectations["expected_time"] * 2,
                          f"{workflow_type} took too long: {execution_time}s")
        
        print("\nWorkflow Performance Benchmarks:")
        for workflow, metrics in results.items():
            print(f"  {workflow}: {metrics['execution_time']:.2f}s (expected: {metrics['expected_time']}s)")
    
    def _benchmark_workflow(self, workflow_type: str, agent_count: int) -> bool:
        """Run a benchmark workflow"""
        runtime = AnthropicAgentRunner(logger=get_logger())
        
        for tool in create_standard_tools():
            runtime.register_tool(tool)
        
        context = AgentContext(
            project_requirements={"name": f"Benchmark{workflow_type}"},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="benchmarking"
        )
        
        agents = ["project-architect", "rapid-builder", "quality-guardian", "devops-engineer", "frontend-specialist"][:agent_count]
        success_count = 0
        
        for agent_name in agents:
            success, _, context = runtime.run_agent(
                agent_name=agent_name,
                agent_prompt=f"Work on benchmark {workflow_type}",
                context=context,
                model=ModelType.SONNET,
                max_iterations=2
            )
            if success:
                success_count += 1
        
        return success_count >= len(agents) * 0.8  # 80% success rate

def run_e2e_tests():
    """Run all E2E tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(EndToEndWorkflowTests))
    suite.addTests(loader.loadTestsFromTestCase(WorkflowRegressionTests))
    suite.addTests(loader.loadTestsFromTestCase(WorkflowBenchmarks))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_e2e_tests()
    sys.exit(0 if success else 1)