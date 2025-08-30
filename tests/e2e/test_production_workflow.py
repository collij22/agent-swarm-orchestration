#!/usr/bin/env python3
"""
Comprehensive E2E Production Workflow Tests
Tests full production workflows with monitoring, recovery, and validation
"""

import pytest
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Import production components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.production_monitor import ProductionMonitor
from lib.recovery_manager import RecoveryManager
from lib.alert_manager import AlertManager, AlertRule, AlertSeverity
from lib.requirement_tracker import RequirementTracker
from lib.agent_validator import AgentValidator
from lib.agent_runtime import AgentContext, AnthropicAgentRunner, ModelType


@dataclass
class WorkflowTestResult:
    """Result of a workflow test"""
    workflow_name: str
    success: bool
    completion_rate: float
    agent_metrics: Dict[str, Dict]
    errors: List[str]
    recovery_attempts: int
    total_duration: float
    quality_score: float


class ProductionWorkflowTester:
    """Comprehensive production workflow testing"""
    
    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.monitor = ProductionMonitor()
        self.recovery_manager = RecoveryManager()
        self.alert_manager = AlertManager()
        self.requirement_tracker = RequirementTracker()
        self.agent_validator = AgentValidator()
        self.temp_dir = None
        
    def setup(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp(prefix="workflow_test_")
        
        # Setup alert rules
        self.alert_manager.add_rule(AlertRule(
            name="high_failure_rate",
            description="Agent failure rate exceeds 30%",
            metric="failure_rate",
            threshold=0.3,
            condition="> 0.3",
            severity=AlertSeverity.CRITICAL
        ))
        
        self.alert_manager.add_rule(AlertRule(
            name="slow_execution",
            description="Agent execution exceeds 60 seconds",
            metric="execution_time",
            threshold=60,
            condition="> 60",
            severity=AlertSeverity.WARNING
        ))
        
    def teardown(self):
        """Cleanup test environment"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_full_workflow_execution(
        self,
        workflow_type: str,
        requirements: Dict[str, Any]
    ) -> WorkflowTestResult:
        """Test a complete workflow execution with monitoring"""
        
        start_time = time.time()
        workflow_name = f"test_{workflow_type}_{int(start_time)}"
        errors = []
        agent_metrics = {}
        recovery_attempts = 0
        
        try:
            # Initialize workflow
            execution_id = self.monitor.start_execution(
                agent_name=f"orchestrator_{workflow_type}",
                requirements=list(requirements.get("features", []))
            )
            
            # Load requirements
            self.requirement_tracker.load_requirements(requirements)
            
            # Create context
            context = AgentContext(
                project_requirements=requirements,
                completed_tasks=[],
                artifacts={"project_directory": self.temp_dir},
                decisions=[],
                current_phase="initialization"
            )
            
            # Define workflow agents based on type
            workflow_agents = self._get_workflow_agents(workflow_type)
            
            # Execute agents with monitoring and recovery
            for agent_config in workflow_agents:
                agent_name = agent_config["name"]
                agent_prompt = agent_config["prompt"]
                required_requirements = agent_config.get("requirements", [])
                
                # Track agent execution
                agent_exec_id = self.monitor.start_execution(
                    agent_name=agent_name,
                    requirements=required_requirements
                )
                
                try:
                    # Execute with recovery
                    success, result, error = await self.recovery_manager.recover_with_retry(
                        agent_name=agent_name,
                        agent_executor=self._create_agent_executor(
                            agent_name, agent_prompt, context
                        ),
                        context=context.to_dict(),
                        max_attempts=3
                    )
                    
                    if success:
                        # Validate agent output
                        validation_result = self.agent_validator.validate_agent_output(
                            agent_name=agent_name,
                            output={"files": context.get_agent_files(agent_name)},
                            project_path=self.temp_dir
                        )
                        
                        # Update requirement progress
                        for req in required_requirements:
                            if validation_result["is_valid"]:
                                self.requirement_tracker.update_progress(
                                    req, 100, agent_name
                                )
                            else:
                                self.requirement_tracker.update_progress(
                                    req, 50, agent_name
                                )
                                errors.append(f"{agent_name}: {validation_result['issues']}")
                        
                        # Record metrics
                        agent_metrics[agent_name] = {
                            "success": True,
                            "validation": validation_result["is_valid"],
                            "files_created": len(context.get_agent_files(agent_name)),
                            "duration": time.time() - start_time
                        }
                        
                        # Update context
                        context.completed_tasks.append(agent_name)
                        
                    else:
                        errors.append(f"{agent_name}: {error}")
                        agent_metrics[agent_name] = {
                            "success": False,
                            "error": str(error),
                            "duration": time.time() - start_time
                        }
                        recovery_attempts += 1
                    
                    # End agent execution
                    self.monitor.end_execution(
                        agent_exec_id,
                        success=success,
                        metrics={"estimated_cost": 0.1}
                    )
                    
                except Exception as e:
                    errors.append(f"{agent_name}: Exception - {str(e)}")
                    agent_metrics[agent_name] = {
                        "success": False,
                        "exception": str(e),
                        "duration": time.time() - start_time
                    }
                    
                    self.monitor.end_execution(
                        agent_exec_id,
                        success=False,
                        error=str(e)
                    )
            
            # Calculate completion rate
            coverage = self.requirement_tracker.get_coverage_report()
            completion_rate = coverage["overall_completion"]
            
            # Calculate quality score
            quality_metrics = await self._calculate_quality_score(
                context, requirements, errors
            )
            
            # End workflow execution
            self.monitor.end_execution(
                execution_id,
                success=completion_rate >= 80,
                metrics={
                    "completion_rate": completion_rate,
                    "quality_score": quality_metrics,
                    "agents_executed": len(workflow_agents)
                }
            )
            
            # Check alerts
            await self.alert_manager.evaluate_rules({
                "failure_rate": len(errors) / max(len(workflow_agents), 1),
                "execution_time": time.time() - start_time
            })
            
            return WorkflowTestResult(
                workflow_name=workflow_name,
                success=completion_rate >= 80,
                completion_rate=completion_rate,
                agent_metrics=agent_metrics,
                errors=errors,
                recovery_attempts=recovery_attempts,
                total_duration=time.time() - start_time,
                quality_score=quality_metrics
            )
            
        except Exception as e:
            errors.append(f"Workflow exception: {str(e)}")
            return WorkflowTestResult(
                workflow_name=workflow_name,
                success=False,
                completion_rate=0,
                agent_metrics=agent_metrics,
                errors=errors,
                recovery_attempts=recovery_attempts,
                total_duration=time.time() - start_time,
                quality_score=0
            )
    
    def _get_workflow_agents(self, workflow_type: str) -> List[Dict]:
        """Get agents for specific workflow type"""
        workflows = {
            "web_app": [
                {
                    "name": "project-architect",
                    "prompt": "Design the web application architecture",
                    "requirements": ["REQ-001", "REQ-002"]
                },
                {
                    "name": "rapid-builder",
                    "prompt": "Build the core application",
                    "requirements": ["REQ-003", "REQ-004"]
                },
                {
                    "name": "frontend-specialist",
                    "prompt": "Create the React UI",
                    "requirements": ["REQ-005"]
                },
                {
                    "name": "quality-guardian",
                    "prompt": "Test and validate the application",
                    "requirements": ["REQ-006"]
                },
                {
                    "name": "devops-engineer",
                    "prompt": "Setup deployment pipeline",
                    "requirements": ["REQ-007"]
                }
            ],
            "api_service": [
                {
                    "name": "project-architect",
                    "prompt": "Design the API architecture",
                    "requirements": ["REQ-001"]
                },
                {
                    "name": "rapid-builder",
                    "prompt": "Build the API endpoints",
                    "requirements": ["REQ-002", "REQ-003"]
                },
                {
                    "name": "database-expert",
                    "prompt": "Design and optimize database",
                    "requirements": ["REQ-004"]
                },
                {
                    "name": "quality-guardian",
                    "prompt": "Test API endpoints",
                    "requirements": ["REQ-005"]
                }
            ],
            "ai_solution": [
                {
                    "name": "ai-specialist",
                    "prompt": "Design AI/ML pipeline",
                    "requirements": ["REQ-001", "REQ-002"]
                },
                {
                    "name": "rapid-builder",
                    "prompt": "Build ML service",
                    "requirements": ["REQ-003"]
                },
                {
                    "name": "performance-optimizer",
                    "prompt": "Optimize model performance",
                    "requirements": ["REQ-004"]
                }
            ]
        }
        return workflows.get(workflow_type, workflows["web_app"])
    
    def _create_agent_executor(
        self,
        agent_name: str,
        agent_prompt: str,
        context: AgentContext
    ):
        """Create an agent executor function"""
        async def executor():
            if self.use_mock:
                # Mock execution
                await asyncio.sleep(0.5)  # Simulate work
                
                # Create mock files
                mock_files = self._generate_mock_files(agent_name)
                for file_info in mock_files:
                    file_path = Path(self.temp_dir) / file_info["path"]
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(file_info["content"])
                    context.add_created_file(
                        agent_name,
                        str(file_path),
                        file_info["type"]
                    )
                
                return True, f"Mock execution of {agent_name}", None
            else:
                # Real execution would go here
                runner = AnthropicAgentRunner()
                success, result, updated_context = await runner.run_agent_async(
                    agent_name,
                    agent_prompt,
                    context,
                    model=ModelType.SONNET,
                    max_iterations=5
                )
                return success, result, None if success else result
        
        return executor
    
    def _generate_mock_files(self, agent_name: str) -> List[Dict]:
        """Generate mock files for agent"""
        files_by_agent = {
            "project-architect": [
                {"path": "docs/architecture.md", "type": "documentation", 
                 "content": "# System Architecture\n\nDesigned by architect"},
                {"path": "docs/database_schema.sql", "type": "code",
                 "content": "CREATE TABLE users (id INT PRIMARY KEY);"}
            ],
            "rapid-builder": [
                {"path": "src/main.py", "type": "code",
                 "content": "def main():\n    print('Application started')"},
                {"path": "src/config.py", "type": "code",
                 "content": "DATABASE_URL = 'postgresql://localhost/app'"}
            ],
            "frontend-specialist": [
                {"path": "frontend/src/App.tsx", "type": "code",
                 "content": "export default function App() { return <div>App</div> }"},
                {"path": "frontend/package.json", "type": "config",
                 "content": '{"name": "frontend", "version": "1.0.0"}'}
            ],
            "quality-guardian": [
                {"path": "tests/test_main.py", "type": "test",
                 "content": "def test_main():\n    assert True"},
                {"path": "tests/test_api.py", "type": "test",
                 "content": "def test_api():\n    assert True"}
            ],
            "devops-engineer": [
                {"path": "Dockerfile", "type": "config",
                 "content": "FROM python:3.11\nCOPY . /app\nCMD python main.py"},
                {"path": ".github/workflows/ci.yml", "type": "config",
                 "content": "name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest"}
            ]
        }
        return files_by_agent.get(agent_name, [
            {"path": f"{agent_name}/output.txt", "type": "code",
             "content": f"Output from {agent_name}"}
        ])
    
    async def _calculate_quality_score(
        self,
        context: AgentContext,
        requirements: Dict,
        errors: List[str]
    ) -> float:
        """Calculate overall quality score"""
        score = 100.0
        
        # Deduct for errors
        score -= len(errors) * 5
        
        # Check for critical files
        critical_files = ["src/main.py", "Dockerfile", "tests/test_main.py"]
        for critical_file in critical_files:
            if not any(critical_file in f for f in context.get_all_files()):
                score -= 10
        
        # Check requirement coverage
        coverage = self.requirement_tracker.get_coverage_report()
        if coverage["overall_completion"] < 80:
            score -= (80 - coverage["overall_completion"]) * 0.5
        
        return max(0, min(100, score))


class TestProductionWorkflow:
    """Test cases for production workflows"""
    
    @pytest.fixture
    def tester(self):
        """Create workflow tester"""
        tester = ProductionWorkflowTester(use_mock=True)
        tester.setup()
        yield tester
        tester.teardown()
    
    @pytest.mark.asyncio
    async def test_web_app_workflow(self, tester):
        """Test complete web application workflow"""
        requirements = {
            "project": {
                "name": "TestWebApp",
                "type": "web_app"
            },
            "features": [
                "User authentication",
                "Real-time notifications",
                "Admin dashboard",
                "API integration",
                "Responsive UI",
                "Testing suite",
                "CI/CD pipeline"
            ]
        }
        
        result = await tester.test_full_workflow_execution("web_app", requirements)
        
        assert result.success, f"Workflow failed: {result.errors}"
        assert result.completion_rate >= 80, f"Low completion: {result.completion_rate}%"
        assert result.quality_score >= 70, f"Low quality: {result.quality_score}"
        assert result.total_duration < 60, f"Too slow: {result.total_duration}s"
        assert len(result.errors) <= 1, f"Too many errors: {result.errors}"
    
    @pytest.mark.asyncio
    async def test_api_service_workflow(self, tester):
        """Test API service workflow"""
        requirements = {
            "project": {
                "name": "TestAPI",
                "type": "api_service"
            },
            "features": [
                "RESTful endpoints",
                "Database integration",
                "Authentication",
                "Rate limiting",
                "API documentation"
            ]
        }
        
        result = await tester.test_full_workflow_execution("api_service", requirements)
        
        assert result.success, f"Workflow failed: {result.errors}"
        assert result.completion_rate >= 80, f"Low completion: {result.completion_rate}%"
        assert "rapid-builder" in result.agent_metrics
        assert result.agent_metrics["rapid-builder"]["success"]
    
    @pytest.mark.asyncio
    async def test_ai_solution_workflow(self, tester):
        """Test AI solution workflow"""
        requirements = {
            "project": {
                "name": "TestAI",
                "type": "ai_solution"
            },
            "features": [
                "ML pipeline",
                "Model training",
                "API endpoint",
                "Performance optimization"
            ]
        }
        
        result = await tester.test_full_workflow_execution("ai_solution", requirements)
        
        assert result.success, f"Workflow failed: {result.errors}"
        assert "ai-specialist" in result.agent_metrics
        assert result.agent_metrics["ai-specialist"]["success"]
    
    @pytest.mark.asyncio
    async def test_workflow_with_monitoring(self, tester):
        """Test workflow with production monitoring"""
        requirements = {
            "project": {"name": "MonitoredApp", "type": "web_app"},
            "features": ["Basic app"]
        }
        
        result = await tester.test_full_workflow_execution("web_app", requirements)
        
        # Check monitoring metrics
        health = tester.monitor.get_system_health()
        assert health["is_healthy"]
        assert health["active_executions"] == 0  # All completed
        assert health["total_executions"] > 0
        
        # Check alerts
        alerts = tester.alert_manager.get_active_alerts()
        critical_alerts = [a for a in alerts if a["severity"] == AlertSeverity.CRITICAL]
        assert len(critical_alerts) == 0, f"Critical alerts: {critical_alerts}"
    
    @pytest.mark.asyncio
    async def test_workflow_recovery(self, tester):
        """Test workflow recovery from failures"""
        # Inject failure for testing
        with patch.object(tester, '_create_agent_executor') as mock_executor:
            # Make first attempt fail, second succeed
            call_count = {"count": 0}
            
            async def failing_executor():
                call_count["count"] += 1
                if call_count["count"] == 1:
                    return False, None, "Simulated failure"
                return True, "Success after retry", None
            
            mock_executor.return_value = failing_executor
            
            requirements = {
                "project": {"name": "RecoveryTest", "type": "api_service"},
                "features": ["Test recovery"]
            }
            
            result = await tester.test_full_workflow_execution("api_service", requirements)
            
            # Should recover from failure
            assert result.recovery_attempts > 0
            assert call_count["count"] > 1  # Should have retried


if __name__ == "__main__":
    # Run tests
    import unittest
    
    async def run_tests():
        tester = ProductionWorkflowTester(use_mock=True)
        tester.setup()
        
        try:
            print("Testing Web App Workflow...")
            result = await tester.test_full_workflow_execution(
                "web_app",
                {
                    "project": {"name": "TestApp", "type": "web_app"},
                    "features": ["User auth", "Dashboard", "API"]
                }
            )
            
            print(f"Success: {result.success}")
            print(f"Completion: {result.completion_rate}%")
            print(f"Quality: {result.quality_score}")
            print(f"Duration: {result.total_duration:.2f}s")
            print(f"Errors: {len(result.errors)}")
            
            if result.errors:
                print("\nErrors encountered:")
                for error in result.errors:
                    print(f"  - {error}")
            
            print("\nAgent Metrics:")
            for agent, metrics in result.agent_metrics.items():
                print(f"  {agent}: {metrics}")
            
        finally:
            tester.teardown()
    
    asyncio.run(run_tests())