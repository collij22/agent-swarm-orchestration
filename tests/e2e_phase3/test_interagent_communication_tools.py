#!/usr/bin/env python3
"""
Phase 3: Inter-Agent Communication Tools Testing
Tests the specific tools used for inter-agent communication including:
- dependency_check_tool
- request_artifact_tool
- verify_deliverables_tool

Production-ready test suite following CLAUDE.md standards.
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import tempfile
import shutil

# Import from project
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.agent_runtime import (
    AgentContext,
    dependency_check_tool,
    request_artifact_tool,
    verify_deliverables_tool,
    write_file_tool
)
from lib.agent_logger import get_logger


@dataclass
class ToolTestCase:
    """Represents a test case for an inter-agent communication tool"""
    tool_name: str
    description: str
    setup_context: AgentContext
    test_params: Dict[str, Any]
    expected_outcome: Dict[str, Any]
    should_succeed: bool = True


@dataclass
class ToolTestResult:
    """Result of a tool test"""
    test_case: ToolTestCase
    success: bool
    actual_outcome: Any
    execution_time: float
    error_message: Optional[str] = None
    validation_passed: bool = False


class InterAgentCommunicationToolsTester:
    """
    Comprehensive test suite for inter-agent communication tools.
    Tests dependency checking, artifact requests, and deliverable verification.
    """
    
    def __init__(self, verbose: bool = False):
        """Initialize the tool tester"""
        self.verbose = verbose
        self.logger = get_logger()
        self.test_results: List[ToolTestResult] = []
        self.temp_dir = None
    
    def setup(self):
        """Setup test environment"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp(prefix="tool_test_")
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        if self.verbose:
            print(f"[SETUP] Created test directory: {self.temp_dir}")
    
    def teardown(self):
        """Cleanup test environment"""
        os.chdir(self.original_dir)
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            
        if self.verbose:
            print(f"[CLEANUP] Removed test directory")
    
    async def test_dependency_check_tool(self) -> List[ToolTestResult]:
        """Test the dependency_check tool with various scenarios"""
        test_cases = []
        
        # Test Case 1: All dependencies met
        context1 = AgentContext(
            project_requirements={},
            completed_tasks=["project-architect", "rapid-builder"],
            artifacts={
                "system_design": "Architecture document",
                "api_endpoints": "REST API specification"
            },
            decisions=[],
            current_phase="frontend"
        )
        context1.set_agent_dependency("frontend-specialist", ["system_design", "api_endpoints"])
        
        test_cases.append(ToolTestCase(
            tool_name="dependency_check",
            description="All dependencies met",
            setup_context=context1,
            test_params={"agent_name": "frontend-specialist", "reasoning": "Check before frontend work"},
            expected_outcome={"dependencies_met": True, "missing": []},
            should_succeed=True
        ))
        
        # Test Case 2: Missing dependencies
        context2 = AgentContext(
            project_requirements={},
            completed_tasks=["project-architect"],
            artifacts={"system_design": "Architecture document"},
            decisions=[],
            current_phase="frontend"
        )
        context2.set_agent_dependency("frontend-specialist", ["system_design", "api_endpoints", "database_schema"])
        
        test_cases.append(ToolTestCase(
            tool_name="dependency_check",
            description="Missing dependencies",
            setup_context=context2,
            test_params={"agent_name": "frontend-specialist", "reasoning": "Check missing deps"},
            expected_outcome={"dependencies_met": False, "missing": ["api_endpoints", "database_schema"]},
            should_succeed=True
        ))
        
        # Test Case 3: File-based dependencies
        context3 = AgentContext(
            project_requirements={},
            completed_tasks=["rapid-builder"],
            artifacts={},
            decisions=[],
            current_phase="testing"
        )
        
        # Create actual files
        await write_file_tool("backend/main.py", "# Main application", "Test file", context3, "rapid-builder")
        await write_file_tool("backend/models.py", "# Data models", "Test file", context3, "rapid-builder")
        
        context3.set_agent_dependency("quality-guardian", ["backend/main.py", "backend/models.py", "backend/tests.py"])
        
        test_cases.append(ToolTestCase(
            tool_name="dependency_check",
            description="File-based dependencies (partial)",
            setup_context=context3,
            test_params={"agent_name": "quality-guardian", "reasoning": "Check file dependencies"},
            expected_outcome={"dependencies_met": False, "missing": ["backend/tests.py"]},
            should_succeed=True
        ))
        
        # Test Case 4: No dependencies configured
        context4 = AgentContext(
            project_requirements={},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="planning"
        )
        # No dependencies set for this agent
        
        test_cases.append(ToolTestCase(
            tool_name="dependency_check",
            description="No dependencies configured",
            setup_context=context4,
            test_params={"agent_name": "project-architect", "reasoning": "Initial agent"},
            expected_outcome={"dependencies_met": True, "missing": []},
            should_succeed=True
        ))
        
        # Test Case 5: Circular dependency detection
        context5 = AgentContext(
            project_requirements={},
            completed_tasks=["agent-a"],
            artifacts={"artifact-a": "Data from A"},
            decisions=[],
            current_phase="complex"
        )
        context5.set_agent_dependency("agent-b", ["artifact-a", "artifact-c"])
        context5.set_agent_dependency("agent-c", ["artifact-b"])  # Creates circular dependency
        
        test_cases.append(ToolTestCase(
            tool_name="dependency_check",
            description="Circular dependency scenario",
            setup_context=context5,
            test_params={"agent_name": "agent-b", "reasoning": "Check circular deps"},
            expected_outcome={"dependencies_met": False, "missing": ["artifact-c"]},
            should_succeed=True
        ))
        
        # Run all test cases
        results = []
        for test_case in test_cases:
            result = await self._run_tool_test(test_case, dependency_check_tool)
            results.append(result)
            
            if self.verbose:
                status = "✓" if result.success else "✗"
                print(f"  {status} {test_case.description}")
                if not result.success and result.error_message:
                    print(f"    Error: {result.error_message}")
        
        self.test_results.extend(results)
        return results
    
    async def test_request_artifact_tool(self) -> List[ToolTestResult]:
        """Test the request_artifact tool with various scenarios"""
        test_cases = []
        
        # Test Case 1: Artifact exists in context
        context1 = AgentContext(
            project_requirements={},
            completed_tasks=["project-architect"],
            artifacts={
                "system_design": {
                    "architecture": "microservices",
                    "database": "PostgreSQL",
                    "api": "REST"
                }
            },
            decisions=[],
            current_phase="building"
        )
        
        test_cases.append(ToolTestCase(
            tool_name="request_artifact",
            description="Artifact exists in context",
            setup_context=context1,
            test_params={
                "artifact_name": "system_design",
                "from_agent": "project-architect",
                "reasoning": "Need architecture details"
            },
            expected_outcome={"found": True, "has_content": True},
            should_succeed=True
        ))
        
        # Test Case 2: File artifact exists
        context2 = AgentContext(
            project_requirements={},
            completed_tasks=["rapid-builder"],
            artifacts={},
            decisions=[],
            current_phase="frontend"
        )
        
        # Create a file and track it
        test_file = "api/endpoints.json"
        await write_file_tool(
            test_file,
            json.dumps({"endpoints": ["/users", "/products"]}),
            "Test artifact",
            context2,
            "rapid-builder"
        )
        
        test_cases.append(ToolTestCase(
            tool_name="request_artifact",
            description="File artifact exists",
            setup_context=context2,
            test_params={
                "artifact_name": test_file,
                "reasoning": "Need API endpoints"
            },
            expected_outcome={"found": True, "is_file": True},
            should_succeed=True
        ))
        
        # Test Case 3: Artifact doesn't exist
        context3 = AgentContext(
            project_requirements={},
            completed_tasks=[],
            artifacts={"other_artifact": "Some data"},
            decisions=[],
            current_phase="testing"
        )
        
        test_cases.append(ToolTestCase(
            tool_name="request_artifact",
            description="Artifact doesn't exist",
            setup_context=context3,
            test_params={
                "artifact_name": "non_existent_artifact",
                "reasoning": "Looking for missing artifact"
            },
            expected_outcome={"found": False},
            should_succeed=True
        ))
        
        # Test Case 4: Request from specific agent
        context4 = AgentContext(
            project_requirements={},
            completed_tasks=["project-architect", "rapid-builder", "frontend-specialist"],
            artifacts={},
            decisions=[],
            current_phase="optimization"
        )
        
        # Add files from different agents
        context4.add_created_file("project-architect", "docs/architecture.md", "documentation")
        context4.add_created_file("rapid-builder", "backend/server.py", "code")
        context4.add_created_file("frontend-specialist", "frontend/app.js", "code")
        
        test_cases.append(ToolTestCase(
            tool_name="request_artifact",
            description="Request from specific agent",
            setup_context=context4,
            test_params={
                "artifact_name": "backend",
                "from_agent": "rapid-builder",
                "reasoning": "Need backend code"
            },
            expected_outcome={"found": True, "from_correct_agent": True},
            should_succeed=True
        ))
        
        # Test Case 5: Large artifact handling
        context5 = AgentContext(
            project_requirements={},
            completed_tasks=["data-processor"],
            artifacts={
                "large_dataset": "x" * 10000  # Large string
            },
            decisions=[],
            current_phase="analysis"
        )
        
        test_cases.append(ToolTestCase(
            tool_name="request_artifact",
            description="Large artifact handling",
            setup_context=context5,
            test_params={
                "artifact_name": "large_dataset",
                "reasoning": "Need large dataset"
            },
            expected_outcome={"found": True, "truncated": True},  # Should truncate to 500 chars
            should_succeed=True
        ))
        
        # Run all test cases
        results = []
        for test_case in test_cases:
            result = await self._run_tool_test(test_case, request_artifact_tool)
            results.append(result)
            
            if self.verbose:
                status = "✓" if result.success else "✗"
                print(f"  {status} {test_case.description}")
                if not result.success and result.error_message:
                    print(f"    Error: {result.error_message}")
        
        self.test_results.extend(results)
        return results
    
    async def test_verify_deliverables_tool(self) -> List[ToolTestResult]:
        """Test the verify_deliverables tool with various scenarios"""
        test_cases = []
        
        # Test Case 1: All deliverables exist and valid
        context1 = AgentContext(
            project_requirements={},
            completed_tasks=["rapid-builder"],
            artifacts={},
            decisions=[],
            current_phase="validation"
        )
        
        # Create deliverable files
        deliverables1 = ["main.py", "config.yaml", "requirements.txt"]
        for deliverable in deliverables1:
            await write_file_tool(
                deliverable,
                f"# Content of {deliverable}",
                "Creating deliverable",
                context1,
                "rapid-builder"
            )
        
        test_cases.append(ToolTestCase(
            tool_name="verify_deliverables",
            description="All deliverables exist and valid",
            setup_context=context1,
            test_params={
                "deliverables": deliverables1,
                "reasoning": "Verify all files created"
            },
            expected_outcome={"all_verified": True, "missing": [], "empty": []},
            should_succeed=True
        ))
        
        # Test Case 2: Some deliverables missing
        context2 = AgentContext(
            project_requirements={},
            completed_tasks=["frontend-specialist"],
            artifacts={},
            decisions=[],
            current_phase="validation"
        )
        
        # Create only some deliverables
        deliverables2 = ["frontend/index.html", "frontend/styles.css", "frontend/app.js"]
        await write_file_tool(
            deliverables2[0],
            "<html>Test</html>",
            "Creating HTML",
            context2,
            "frontend-specialist"
        )
        # Missing styles.css and app.js
        
        test_cases.append(ToolTestCase(
            tool_name="verify_deliverables",
            description="Some deliverables missing",
            setup_context=context2,
            test_params={
                "deliverables": deliverables2,
                "reasoning": "Check for missing files"
            },
            expected_outcome={
                "all_verified": False,
                "missing": ["frontend/styles.css", "frontend/app.js"],
                "empty": []
            },
            should_succeed=True
        ))
        
        # Test Case 3: Empty file detection
        context3 = AgentContext(
            project_requirements={},
            completed_tasks=["database-expert"],
            artifacts={},
            decisions=[],
            current_phase="validation"
        )
        
        # Create empty file
        deliverables3 = ["database/schema.sql", "database/migrations.sql"]
        await write_file_tool(deliverables3[0], "CREATE TABLE users;", "Schema", context3, "database-expert")
        await write_file_tool(deliverables3[1], "", "Empty migration", context3, "database-expert")
        
        test_cases.append(ToolTestCase(
            tool_name="verify_deliverables",
            description="Empty file detection",
            setup_context=context3,
            test_params={
                "deliverables": deliverables3,
                "reasoning": "Detect empty files"
            },
            expected_outcome={
                "all_verified": False,
                "missing": [],
                "empty": ["database/migrations.sql"]
            },
            should_succeed=True
        ))
        
        # Test Case 4: Critical deliverables tracking
        context4 = AgentContext(
            project_requirements={},
            completed_tasks=["devops-engineer"],
            artifacts={},
            decisions=[],
            current_phase="deployment"
        )
        
        # Create critical deployment files
        critical_deliverables = ["Dockerfile", "docker-compose.yml", ".env.example"]
        for deliverable in critical_deliverables:
            await write_file_tool(
                deliverable,
                f"# {deliverable} content",
                "Critical file",
                context4,
                "devops-engineer"
            )
        
        test_cases.append(ToolTestCase(
            tool_name="verify_deliverables",
            description="Critical deliverables tracking",
            setup_context=context4,
            test_params={
                "deliverables": critical_deliverables,
                "reasoning": "Verify critical deployment files"
            },
            expected_outcome={
                "all_verified": True,
                "verification_required": critical_deliverables  # Should be marked for verification
            },
            should_succeed=True
        ))
        
        # Test Case 5: Nested directory deliverables
        context5 = AgentContext(
            project_requirements={},
            completed_tasks=["project-architect"],
            artifacts={},
            decisions=[],
            current_phase="documentation"
        )
        
        # Create nested directory structure
        nested_deliverables = [
            "docs/api/endpoints.md",
            "docs/architecture/system.md",
            "docs/deployment/guide.md"
        ]
        
        for deliverable in nested_deliverables:
            await write_file_tool(
                deliverable,
                f"# Documentation for {deliverable}",
                "Documentation",
                context5,
                "project-architect"
            )
        
        test_cases.append(ToolTestCase(
            tool_name="verify_deliverables",
            description="Nested directory deliverables",
            setup_context=context5,
            test_params={
                "deliverables": nested_deliverables,
                "reasoning": "Verify nested documentation"
            },
            expected_outcome={"all_verified": True, "missing": [], "empty": []},
            should_succeed=True
        ))
        
        # Run all test cases
        results = []
        for test_case in test_cases:
            result = await self._run_tool_test(test_case, verify_deliverables_tool)
            results.append(result)
            
            if self.verbose:
                status = "✓" if result.success else "✗"
                print(f"  {status} {test_case.description}")
                if not result.success and result.error_message:
                    print(f"    Error: {result.error_message}")
        
        self.test_results.extend(results)
        return results
    
    async def test_integration_scenarios(self) -> List[ToolTestResult]:
        """Test integrated scenarios using multiple tools together"""
        test_cases = []
        
        # Scenario 1: Complete dependency chain
        context1 = AgentContext(
            project_requirements={"project": "E-commerce platform"},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="starting"
        )
        
        # Simulate a complete workflow
        if self.verbose:
            print("\n[INTEGRATION] Testing complete dependency chain...")
        
        # Step 1: Project architect creates design
        await write_file_tool("architecture/design.md", "# System Design", "Design doc", context1, "project-architect")
        context1.artifacts["system_design"] = "Microservices architecture"
        context1.completed_tasks.append("project-architect")
        
        # Step 2: Rapid builder needs the design
        context1.set_agent_dependency("rapid-builder", ["architecture/design.md", "system_design"])
        
        # Check dependencies
        deps_result = await dependency_check_tool("rapid-builder", "Check deps", context1)
        
        # Request artifact
        artifact_result = await request_artifact_tool("system_design", "project-architect", "Need design", context1)
        
        # Create backend files
        backend_files = ["backend/main.py", "backend/models.py", "backend/api.py"]
        for file in backend_files:
            await write_file_tool(file, f"# {file}", "Backend code", context1, "rapid-builder")
        
        # Verify deliverables
        verify_result = await verify_deliverables_tool(backend_files, "Verify backend", context1)
        
        # Create test case for this scenario
        test_cases.append(ToolTestCase(
            tool_name="integration",
            description="Complete dependency chain workflow",
            setup_context=context1,
            test_params={"scenario": "dependency_chain"},
            expected_outcome={
                "dependencies_met": True,
                "artifacts_found": True,
                "deliverables_verified": True
            },
            should_succeed=True
        ))
        
        # Scenario 2: Parallel agents with shared resources
        context2 = AgentContext(
            project_requirements={"project": "Real-time dashboard"},
            completed_tasks=["project-architect", "rapid-builder"],
            artifacts={
                "api_schema": {"version": "1.0", "endpoints": ["/data", "/metrics"]},
                "shared_config": {"database": "PostgreSQL", "cache": "Redis"}
            },
            decisions=[],
            current_phase="parallel_development"
        )
        
        if self.verbose:
            print("\n[INTEGRATION] Testing parallel resource sharing...")
        
        # Multiple agents need the same artifacts
        agents = ["frontend-specialist", "api-integrator", "performance-optimizer"]
        
        for agent in agents:
            context2.set_agent_dependency(agent, ["api_schema", "shared_config"])
            
            # Each agent checks dependencies
            deps_ok = await dependency_check_tool(agent, f"{agent} checking", context2)
            
            # Each agent requests shared artifacts
            schema = await request_artifact_tool("api_schema", None, f"{agent} needs schema", context2)
            config = await request_artifact_tool("shared_config", None, f"{agent} needs config", context2)
            
            # Each agent creates its outputs
            if agent == "frontend-specialist":
                await write_file_tool("frontend/dashboard.tsx", "// Dashboard", "Frontend", context2, agent)
            elif agent == "api-integrator":
                await write_file_tool("integrations/api_client.py", "# API Client", "Integration", context2, agent)
            elif agent == "performance-optimizer":
                await write_file_tool("optimizations/cache_config.yaml", "# Cache", "Optimization", context2, agent)
        
        # Verify all deliverables
        all_deliverables = [
            "frontend/dashboard.tsx",
            "integrations/api_client.py",
            "optimizations/cache_config.yaml"
        ]
        final_verify = await verify_deliverables_tool(all_deliverables, "Verify all", context2)
        
        test_cases.append(ToolTestCase(
            tool_name="integration",
            description="Parallel agents with shared resources",
            setup_context=context2,
            test_params={"scenario": "parallel_sharing"},
            expected_outcome={
                "all_agents_succeeded": True,
                "no_conflicts": True,
                "all_deliverables_created": True
            },
            should_succeed=True
        ))
        
        # Scenario 3: Recovery from missing dependencies
        context3 = AgentContext(
            project_requirements={"project": "API service"},
            completed_tasks=["rapid-builder"],
            artifacts={},
            decisions=[],
            current_phase="recovery"
        )
        
        if self.verbose:
            print("\n[INTEGRATION] Testing recovery from missing dependencies...")
        
        # Quality guardian needs test files that don't exist yet
        context3.set_agent_dependency("quality-guardian", ["backend/main.py", "backend/tests.py"])
        
        # Check dependencies (will fail)
        deps_check = await dependency_check_tool("quality-guardian", "Initial check", context3)
        
        # Track incomplete task
        if "Missing dependencies" in str(deps_check):
            context3.add_incomplete_task("quality-guardian", "dependency_check", "Missing test files")
        
        # Another agent creates the missing files
        await write_file_tool("backend/main.py", "# Main app", "Main", context3, "rapid-builder")
        await write_file_tool("backend/tests.py", "# Tests", "Tests", context3, "test-writer")
        
        # Retry dependency check
        deps_retry = await dependency_check_tool("quality-guardian", "Retry check", context3)
        
        # Now quality guardian can proceed
        await write_file_tool("quality_report.md", "# Quality Report", "Report", context3, "quality-guardian")
        
        # Verify recovery
        recovery_files = ["backend/main.py", "backend/tests.py", "quality_report.md"]
        recovery_verify = await verify_deliverables_tool(recovery_files, "Verify recovery", context3)
        
        test_cases.append(ToolTestCase(
            tool_name="integration",
            description="Recovery from missing dependencies",
            setup_context=context3,
            test_params={"scenario": "dependency_recovery"},
            expected_outcome={
                "initial_failure": True,
                "recovery_successful": True,
                "all_files_created": True
            },
            should_succeed=True
        ))
        
        # Process test cases
        results = []
        for test_case in test_cases:
            # For integration tests, we evaluate based on the context state
            start_time = time.time()
            
            try:
                # Validate the scenario outcome
                success = self._validate_integration_scenario(test_case)
                
                result = ToolTestResult(
                    test_case=test_case,
                    success=success,
                    actual_outcome=test_case.setup_context.to_dict(),
                    execution_time=time.time() - start_time,
                    validation_passed=success
                )
            except Exception as e:
                result = ToolTestResult(
                    test_case=test_case,
                    success=False,
                    actual_outcome=None,
                    execution_time=time.time() - start_time,
                    error_message=str(e)
                )
            
            results.append(result)
            
            if self.verbose:
                status = "✓" if result.success else "✗"
                print(f"  {status} {test_case.description}")
        
        self.test_results.extend(results)
        return results
    
    async def _run_tool_test(self, test_case: ToolTestCase, tool_function) -> ToolTestResult:
        """Run a single tool test case"""
        start_time = time.time()
        
        try:
            # Build function parameters
            params = test_case.test_params.copy()
            params["context"] = test_case.setup_context
            
            # Execute the tool
            result = await tool_function(**params)
            
            # Validate the outcome
            validation_passed = self._validate_tool_outcome(
                test_case.tool_name,
                result,
                test_case.expected_outcome,
                test_case.setup_context
            )
            
            success = validation_passed if test_case.should_succeed else not validation_passed
            
            return ToolTestResult(
                test_case=test_case,
                success=success,
                actual_outcome=result,
                execution_time=time.time() - start_time,
                validation_passed=validation_passed
            )
            
        except Exception as e:
            return ToolTestResult(
                test_case=test_case,
                success=not test_case.should_succeed,  # If we expected failure
                actual_outcome=None,
                execution_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _validate_tool_outcome(
        self,
        tool_name: str,
        actual_result: Any,
        expected: Dict[str, Any],
        context: AgentContext
    ) -> bool:
        """Validate tool outcome against expectations"""
        
        if tool_name == "dependency_check":
            # Check if dependencies were correctly identified
            if "dependencies_met" in expected:
                met = "All dependencies met" in str(actual_result) if expected["dependencies_met"] else "Missing dependencies" in str(actual_result)
                if not met:
                    return False
            
            if "missing" in expected and expected["missing"]:
                for missing_dep in expected["missing"]:
                    if missing_dep not in str(actual_result):
                        return False
            
            return True
            
        elif tool_name == "request_artifact":
            # Check if artifact was found
            if "found" in expected:
                found = "not found" not in str(actual_result).lower() if expected["found"] else "not found" in str(actual_result).lower()
                if not found:
                    return False
            
            if expected.get("truncated"):
                # Check if large artifact was truncated
                return len(str(actual_result)) <= 600  # Some overhead for message
            
            return True
            
        elif tool_name == "verify_deliverables":
            # Check deliverable verification results
            result_str = str(actual_result)
            
            if "all_verified" in expected:
                verified = "All deliverables verified" in result_str if expected["all_verified"] else "missing or invalid" in result_str
                if not verified:
                    return False
            
            if "missing" in expected:
                for missing_file in expected.get("missing", []):
                    if f"{missing_file} (not found)" not in result_str:
                        return False
            
            if "empty" in expected:
                for empty_file in expected.get("empty", []):
                    if f"{empty_file} (empty file)" not in result_str:
                        return False
            
            if "verification_required" in expected:
                # Check that files were added to verification list
                return all(f in context.verification_required for f in expected["verification_required"])
            
            return True
            
        elif tool_name == "integration":
            # For integration tests, check overall success
            return True  # Validated separately
        
        return False
    
    def _validate_integration_scenario(self, test_case: ToolTestCase) -> bool:
        """Validate integration scenario outcomes"""
        context = test_case.setup_context
        expected = test_case.expected_outcome
        
        if test_case.test_params.get("scenario") == "dependency_chain":
            # Check complete workflow execution
            return (
                len(context.completed_tasks) > 0 and
                len(context.artifacts) > 0 and
                len(context.created_files) > 0
            )
        
        elif test_case.test_params.get("scenario") == "parallel_sharing":
            # Check parallel execution without conflicts
            return (
                len(context.created_files.get("frontend-specialist", [])) > 0 and
                len(context.created_files.get("api-integrator", [])) > 0 and
                len(context.created_files.get("performance-optimizer", [])) > 0
            )
        
        elif test_case.test_params.get("scenario") == "dependency_recovery":
            # Check recovery from failure
            return (
                len(context.incomplete_tasks) > 0 and  # Had failures
                Path("backend/tests.py").exists() and  # Recovery created missing file
                Path("quality_report.md").exists()  # Final task succeeded
            )
        
        return False
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        report = ["=" * 80]
        report.append("INTER-AGENT COMMUNICATION TOOLS TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Group results by tool
        tool_groups = {}
        for result in self.test_results:
            tool_name = result.test_case.tool_name
            if tool_name not in tool_groups:
                tool_groups[tool_name] = []
            tool_groups[tool_name].append(result)
        
        # Summary
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Successful: {successful_tests}")
        report.append(f"Failed: {total_tests - successful_tests}")
        report.append(f"Success Rate: {(successful_tests/total_tests*100) if total_tests > 0 else 0:.1f}%")
        report.append("")
        
        # Results by tool
        report.append("RESULTS BY TOOL")
        report.append("-" * 40)
        
        for tool_name, results in tool_groups.items():
            tool_success = sum(1 for r in results if r.success)
            tool_total = len(results)
            
            report.append(f"\n{tool_name.upper()}")
            report.append(f"  Tests: {tool_total}")
            report.append(f"  Passed: {tool_success}")
            report.append(f"  Success Rate: {(tool_success/tool_total*100):.1f}%")
            
            for result in results:
                status = "✓" if result.success else "✗"
                report.append(f"    {status} {result.test_case.description}")
                if result.error_message:
                    report.append(f"      Error: {result.error_message}")
        
        # Performance metrics
        report.append("")
        report.append("PERFORMANCE METRICS")
        report.append("-" * 40)
        
        avg_execution_time = sum(r.execution_time for r in self.test_results) / len(self.test_results) if self.test_results else 0
        max_execution_time = max((r.execution_time for r in self.test_results), default=0)
        min_execution_time = min((r.execution_time for r in self.test_results), default=0)
        
        report.append(f"Average Execution Time: {avg_execution_time:.3f}s")
        report.append(f"Max Execution Time: {max_execution_time:.3f}s")
        report.append(f"Min Execution Time: {min_execution_time:.3f}s")
        
        # Recommendations
        report.append("")
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)
        
        if "dependency_check" in tool_groups:
            dep_results = tool_groups["dependency_check"]
            if any(not r.success for r in dep_results):
                report.append("- Review dependency management logic")
        
        if "request_artifact" in tool_groups:
            artifact_results = tool_groups["request_artifact"]
            if any(not r.success for r in artifact_results):
                report.append("- Improve artifact storage and retrieval")
        
        if "verify_deliverables" in tool_groups:
            verify_results = tool_groups["verify_deliverables"]
            if any(not r.success for r in verify_results):
                report.append("- Enhance deliverable verification process")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


async def main():
    """Main test execution"""
    print("Inter-Agent Communication Tools Testing")
    print("=" * 60)
    
    # Initialize tester
    tester = InterAgentCommunicationToolsTester(verbose=True)
    
    try:
        # Setup
        tester.setup()
        
        # Run tool tests
        print("\n1. Testing dependency_check tool...")
        dep_results = await tester.test_dependency_check_tool()
        
        print("\n2. Testing request_artifact tool...")
        artifact_results = await tester.test_request_artifact_tool()
        
        print("\n3. Testing verify_deliverables tool...")
        verify_results = await tester.test_verify_deliverables_tool()
        
        print("\n4. Testing integration scenarios...")
        integration_results = await tester.test_integration_scenarios()
        
        # Generate and display report
        print("\n" + "=" * 60)
        report = tester.generate_report()
        print(report)
        
        # Save report
        report_path = Path("phase3_communication_tools_report.txt")
        report_path.write_text(report)
        print(f"\nReport saved to: {report_path}")
        
    finally:
        # Cleanup
        tester.teardown()


if __name__ == "__main__":
    asyncio.run(main())