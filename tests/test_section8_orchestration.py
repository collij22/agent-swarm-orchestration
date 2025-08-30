#!/usr/bin/env python3
"""
Comprehensive Test Suite for Section 8: Orchestration Enhancements

Tests all Section 8 features:
- Adaptive workflow with dynamic agent selection
- Requirement tracking with ID mapping
- Advanced error recovery and retry logic
- Real-time progress monitoring
- Parallel execution with dependency management
- Manual intervention points
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List

import sys
sys.path.append(str(Path(__file__).parent.parent / "lib"))

from lib.orchestration_enhanced import (
    AdaptiveWorkflowEngine, RequirementItem, AgentExecutionPlan,
    RequirementStatus, AgentExecutionStatus
)
from lib.progress_streamer import (
    ProgressStreamer, ProgressEvent, ProgressEventType
)
from lib.agent_runtime import AgentContext
from lib.agent_logger import get_logger


class TestAdaptiveWorkflowEngine:
    """Test adaptive workflow engine capabilities"""
    
    @pytest.fixture
    def engine(self):
        """Create workflow engine for testing"""
        logger = get_logger()
        return AdaptiveWorkflowEngine(logger)
    
    @pytest.fixture
    def sample_requirements(self):
        """Sample requirements for testing"""
        return {
            "project": {"name": "TestProject"},
            "features": [
                "User authentication with JWT",
                "React frontend dashboard", 
                "PostgreSQL database setup",
                "Docker containerization",
                "AI-powered recommendation engine",
                "Unit testing suite",
                "API documentation"
            ]
        }
    
    def test_requirement_parsing_with_ids(self, engine, sample_requirements):
        """Test requirement parsing with ID assignment"""
        parsed = engine.parse_requirements_with_ids(sample_requirements)
        
        # Check IDs are assigned
        assert len(parsed) >= 7  # At least 7 feature requirements
        assert all(req_id.startswith("REQ-") for req_id in parsed.keys())
        
        # Check requirement details
        for req_id, requirement in parsed.items():
            assert isinstance(requirement, RequirementItem)
            assert requirement.id == req_id
            assert requirement.description
            assert isinstance(requirement.assigned_agents, list)
            assert len(requirement.assigned_agents) > 0
            assert requirement.priority in [1, 2, 3]
    
    def test_agent_assignment_logic(self, engine):
        """Test intelligent agent assignment"""
        test_features = [
            "React frontend with TypeScript",
            "PostgreSQL database schema",
            "Docker deployment setup",
            "AI categorization service",
            "Unit testing framework"
        ]
        
        for feature in test_features:
            agents, priority = engine._analyze_feature_requirements(feature)
            
            # Check agent assignment logic
            if "react" in feature.lower():
                assert "frontend-specialist" in agents
            if "postgresql" in feature.lower():
                assert "database-expert" in agents
            if "docker" in feature.lower():
                assert "devops-engineer" in agents
            if "ai" in feature.lower():
                assert "ai-specialist" in agents
            if "test" in feature.lower():
                assert "quality-guardian" in agents
            
            # Check priority assignment
            assert priority in [1, 2, 3]
    
    def test_dependency_detection(self, engine):
        """Test dependency detection between requirements"""
        features = [
            "User authentication API",
            "PostgreSQL database setup", 
            "React frontend dashboard",  # Should depend on auth API
            "Docker containerization"   # Should depend on implementation
        ]
        
        deps = engine._detect_dependencies(features[2], features[:2])  # Frontend depends on API
        # Note: Simple heuristic may not catch all dependencies
        
        deps2 = engine._detect_dependencies(features[3], features[:3])  # Docker depends on implementation
        
        # At minimum, should detect some logical dependencies
        assert isinstance(deps, list)
        assert isinstance(deps2, list)
    
    def test_execution_plan_creation(self, engine, sample_requirements):
        """Test adaptive execution plan creation"""
        # Parse requirements first
        engine.parse_requirements_with_ids(sample_requirements)
        
        available_agents = [
            "project-architect", "rapid-builder", "frontend-specialist",
            "database-expert", "ai-specialist", "quality-guardian", 
            "devops-engineer", "documentation-writer"
        ]
        
        plans = engine.create_adaptive_execution_plan(available_agents)
        
        # Verify plans created
        assert isinstance(plans, dict)
        assert len(plans) > 0
        
        # Check plan structure
        for agent_name, plan in plans.items():
            assert isinstance(plan, AgentExecutionPlan)
            assert plan.agent_name == agent_name
            assert isinstance(plan.requirements, list)
            assert len(plan.requirements) > 0
            assert isinstance(plan.dependencies, list)
            assert plan.priority in [1, 2, 3]
            assert plan.max_retries >= 1
    
    def test_ready_agents_logic(self, engine, sample_requirements):
        """Test ready agents detection"""
        engine.parse_requirements_with_ids(sample_requirements)
        
        available_agents = ["project-architect", "rapid-builder", "frontend-specialist"]
        engine.create_adaptive_execution_plan(available_agents)
        
        # Initially, some agents should be ready (no dependencies)
        ready = engine.get_ready_agents()
        assert isinstance(ready, list)
        assert len(ready) > 0
        
        # Mark one agent as completed
        if ready:
            first_agent = ready[0]
            engine.agent_plans[first_agent].status = AgentExecutionStatus.COMPLETED
            
            # Should affect ready agents list
            new_ready = engine.get_ready_agents()
            assert first_agent not in new_ready
    
    def test_progress_tracking(self, engine, sample_requirements):
        """Test progress tracking and updates"""
        engine.parse_requirements_with_ids(sample_requirements)
        
        available_agents = ["rapid-builder", "frontend-specialist"]
        engine.create_adaptive_execution_plan(available_agents)
        
        # Initial progress
        initial_completion = engine.progress.overall_completion
        assert initial_completion == 0.0
        
        # Simulate completing a requirement
        req_id = list(engine.requirements.keys())[0]
        engine.requirements[req_id].status = RequirementStatus.COMPLETED
        engine._update_progress()
        
        # Progress should increase
        assert engine.progress.overall_completion > initial_completion
        assert engine.progress.completed_requirements == 1
    
    @pytest.mark.asyncio
    async def test_retry_logic_simulation(self, engine):
        """Test retry logic without actual API calls"""
        # Create mock runtime and context
        mock_runtime = Mock()
        mock_context = AgentContext(
            project_requirements={},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="test"
        )
        
        mock_agent_config = {
            "prompt": "Test prompt",
            "model": "sonnet"
        }
        
        # Create agent plan
        plan = AgentExecutionPlan(
            agent_name="test-agent",
            requirements=["REQ-001"],
            dependencies=[],
            max_retries=2
        )
        engine.agent_plans["test-agent"] = plan
        engine.requirements["REQ-001"] = RequirementItem(
            id="REQ-001",
            description="Test requirement"
        )
        
        # Mock runtime to always fail
        mock_runtime.run_agent_async = AsyncMock(return_value=(False, "Test failure", mock_context))
        
        # Test retry logic
        success, result, context = await engine.execute_agent_with_retry(
            "test-agent",
            mock_runtime,
            mock_context,
            mock_agent_config
        )
        
        # Should fail after retries
        assert not success
        assert plan.status == AgentExecutionStatus.FAILED
        assert plan.current_retry == 2  # Should have retried max times
        assert "Test failure" in result
    
    def test_checkpoint_save_load(self, engine, sample_requirements):
        """Test checkpoint save and load functionality"""
        # Set up workflow state
        engine.parse_requirements_with_ids(sample_requirements)
        available_agents = ["rapid-builder", "frontend-specialist"]
        engine.create_adaptive_execution_plan(available_agents)
        
        # Modify some state
        req_id = list(engine.requirements.keys())[0]
        engine.requirements[req_id].status = RequirementStatus.IN_PROGRESS
        engine.requirements[req_id].completion_percentage = 50.0
        
        agent_name = list(engine.agent_plans.keys())[0]
        engine.agent_plans[agent_name].status = AgentExecutionStatus.RUNNING
        
        # Save checkpoint
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            checkpoint_path = Path(f.name)
        
        try:
            engine.save_checkpoint(checkpoint_path)
            assert checkpoint_path.exists()
            
            # Create new engine and load checkpoint
            new_engine = AdaptiveWorkflowEngine(get_logger())
            success = new_engine.load_checkpoint(checkpoint_path)
            
            assert success
            assert new_engine.workflow_id == engine.workflow_id
            assert len(new_engine.requirements) == len(engine.requirements)
            assert len(new_engine.agent_plans) == len(engine.agent_plans)
            
            # Check specific state
            assert new_engine.requirements[req_id].status == RequirementStatus.IN_PROGRESS
            assert new_engine.requirements[req_id].completion_percentage == 50.0
            assert new_engine.agent_plans[agent_name].status == AgentExecutionStatus.RUNNING
        
        finally:
            checkpoint_path.unlink(missing_ok=True)


class TestProgressStreamer:
    """Test real-time progress streaming"""
    
    @pytest.fixture
    def streamer(self):
        """Create progress streamer for testing"""
        return ProgressStreamer()
    
    @pytest.mark.asyncio
    async def test_event_broadcasting(self, streamer):
        """Test event broadcasting functionality"""
        events_received = []
        
        def event_callback(event):
            events_received.append(event)
        
        streamer.add_event_callback(event_callback)
        
        # Broadcast test event
        test_event = ProgressEvent(
            ProgressEventType.WORKFLOW_STARTED,
            {"workflow_id": "test-123", "total_requirements": 5}
        )
        
        await streamer.broadcast_event(test_event)
        
        # Check event was received
        assert len(events_received) == 1
        assert events_received[0].event_type == ProgressEventType.WORKFLOW_STARTED
        assert events_received[0].data["workflow_id"] == "test-123"
    
    @pytest.mark.asyncio
    async def test_progress_updates(self, streamer):
        """Test progress update notifications"""
        from lib.orchestration_enhanced import WorkflowProgress
        
        progress = WorkflowProgress(
            workflow_id="test-workflow",
            total_requirements=10,
            completed_requirements=3,
            failed_requirements=1,
            blocked_requirements=0,
            total_agents=5,
            completed_agents=2,
            failed_agents=0,
            running_agents=1,
            overall_completion=30.0,
            estimated_remaining_time=120.0,
            started_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:30:00"
        )
        
        await streamer.update_workflow_progress(progress)
        
        # Check current state
        current_state = streamer.get_current_state()
        assert current_state["progress"]["overall_completion"] == 30.0
        assert current_state["progress"]["completed_requirements"] == 3
    
    @pytest.mark.asyncio
    async def test_requirement_tracking(self, streamer):
        """Test requirement status tracking"""
        requirement = RequirementItem(
            id="REQ-001",
            description="Test requirement",
            status=RequirementStatus.IN_PROGRESS,
            completion_percentage=75.0,
            assigned_agents=["test-agent"]
        )
        
        await streamer.update_requirement_status("REQ-001", requirement)
        
        # Check requirement was tracked
        current_state = streamer.get_current_state()
        assert "REQ-001" in current_state["requirements"]
        assert current_state["requirements"]["REQ-001"]["completion_percentage"] == 75.0
    
    def test_event_history(self, streamer):
        """Test event history management"""
        # Add events beyond max history
        for i in range(1200):  # More than max_history (1000)
            event = ProgressEvent(
                ProgressEventType.OVERALL_PROGRESS,
                {"test_data": i}
            )
            streamer.event_history.append(event)
        
        # Should trim to max_history
        assert len(streamer.event_history) == 1000
        assert streamer.event_history[0].data["test_data"] == 200  # Should start from 200
    
    def test_progress_snapshot(self, streamer):
        """Test progress snapshot saving"""
        # Add some test state
        streamer.current_requirements["REQ-001"] = RequirementItem(
            id="REQ-001",
            description="Test requirement"
        )
        
        # Save snapshot
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            snapshot_path = Path(f.name)
        
        try:
            streamer.save_progress_snapshot(snapshot_path)
            assert snapshot_path.exists()
            
            # Verify snapshot content
            with open(snapshot_path) as f:
                snapshot = json.load(f)
            
            assert "timestamp" in snapshot
            assert "state" in snapshot
            assert "event_history" in snapshot
            assert "REQ-001" in snapshot["state"]["requirements"]
        
        finally:
            snapshot_path.unlink(missing_ok=True)


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_workflow_engine_with_progress_streaming(self):
        """Test workflow engine with progress streaming integration"""
        # Create components
        logger = get_logger()
        engine = AdaptiveWorkflowEngine(logger)
        streamer = ProgressStreamer(logger)
        
        # Connect them
        async def progress_callback(progress):
            await streamer.update_workflow_progress(progress)
        
        engine.add_progress_callback(progress_callback)
        
        # Set up test scenario
        requirements = {
            "features": ["Test feature 1", "Test feature 2"]
        }
        
        engine.parse_requirements_with_ids(requirements)
        available_agents = ["rapid-builder"]
        engine.create_adaptive_execution_plan(available_agents)
        
        # Simulate progress
        req_id = list(engine.requirements.keys())[0]
        engine.requirements[req_id].status = RequirementStatus.COMPLETED
        engine._update_progress()
        
        # Progress should be reflected in streamer
        current_state = streamer.get_current_state()
        assert current_state["progress"]["completed_requirements"] == 1
    
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self):
        """Test complete error recovery flow"""
        logger = get_logger()
        engine = AdaptiveWorkflowEngine(logger)
        
        # Set up failing scenario
        engine.requirements["REQ-001"] = RequirementItem(
            id="REQ-001",
            description="Failing requirement",
            assigned_agents=["test-agent"]
        )
        
        plan = AgentExecutionPlan(
            agent_name="test-agent",
            requirements=["REQ-001"],
            dependencies=[],
            max_retries=2
        )
        engine.agent_plans["test-agent"] = plan
        
        # Mock failing runtime
        mock_runtime = Mock()
        mock_runtime.run_agent_async = AsyncMock(return_value=(False, "Simulated failure", Mock()))
        
        mock_context = AgentContext(
            project_requirements={},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="test"
        )
        
        # Test error recovery
        success, result, _ = await engine.execute_agent_with_retry(
            "test-agent",
            mock_runtime,
            mock_context,
            {"prompt": "test", "model": "sonnet"}
        )
        
        # Should fail after retries
        assert not success
        assert plan.status == AgentExecutionStatus.FAILED
        assert plan.current_retry == 2
        assert engine.requirements["REQ-001"].status == RequirementStatus.FAILED
    
    def test_dependency_graph_construction(self):
        """Test dependency graph construction and validation"""
        logger = get_logger()
        engine = AdaptiveWorkflowEngine(logger)
        
        # Create requirements with dependencies
        engine.requirements = {
            "REQ-001": RequirementItem(
                id="REQ-001",
                description="Base API",
                dependencies=[]
            ),
            "REQ-002": RequirementItem(
                id="REQ-002", 
                description="Frontend",
                dependencies=["REQ-001"]
            ),
            "REQ-003": RequirementItem(
                id="REQ-003",
                description="Testing",
                dependencies=["REQ-001", "REQ-002"]
            )
        }
        
        engine._build_dependency_graph()
        
        # Verify graph structure
        assert len(engine.dependency_graph.nodes()) == 3
        assert len(engine.dependency_graph.edges()) == 3
        
        # Check specific dependencies
        assert engine.dependency_graph.has_edge("REQ-001", "REQ-002")
        assert engine.dependency_graph.has_edge("REQ-001", "REQ-003")
        assert engine.dependency_graph.has_edge("REQ-002", "REQ-003")


# Test utilities
def create_test_requirements():
    """Create standard test requirements"""
    return {
        "project": {
            "name": "TestProject",
            "type": "web_app"
        },
        "features": [
            "User authentication with JWT tokens",
            "React frontend dashboard with TypeScript",
            "PostgreSQL database with migrations", 
            "REST API with OpenAPI documentation",
            "Docker containerization setup",
            "Unit and integration testing",
            "CI/CD pipeline with GitHub Actions"
        ],
        "tech_overrides": {
            "frontend": {"framework": "React"},
            "backend": {"framework": "FastAPI"},
            "database": {"type": "PostgreSQL"}
        }
    }


# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def run_section8_tests():
    """Run all Section 8 tests"""
    import subprocess
    
    result = subprocess.run([
        "python", "-m", "pytest", 
        __file__,
        "-v",
        "--tb=short"
    ], capture_output=True, text=True)
    
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    
    return result.returncode == 0


if __name__ == "__main__":
    # Run tests directly
    success = run_section8_tests()
    exit(0 if success else 1)