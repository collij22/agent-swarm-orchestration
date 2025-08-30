#!/usr/bin/env python3
"""
Advanced Workflow Engine for Comprehensive E2E Testing

Features:
- Progressive requirement introduction for realistic scenarios
- Conflict detection and resolution testing
- Multi-phase checkpoint management
- Failure injection and recovery testing
- Real-time quality metrics tracking
"""

import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random
import sys
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.agent_runtime import AgentContext, AnthropicAgentRunner, ModelType, create_standard_tools
from lib.agent_logger import get_logger
from lib.mock_anthropic_enhanced import EnhancedMockAnthropicClient

class WorkflowPhase(Enum):
    """Workflow execution phases"""
    INITIALIZATION = "initialization"
    PLANNING = "planning" 
    DEVELOPMENT = "development"
    INTEGRATION = "integration"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    VALIDATION = "validation"

class RequirementPriority(Enum):
    """Requirement priority levels"""
    CRITICAL = "critical"  # Must be completed for success
    HIGH = "high"         # Should be completed 
    MEDIUM = "medium"     # Nice to have
    LOW = "low"          # Optional

class ConflictType(Enum):
    """Types of requirement conflicts"""
    TECHNICAL = "technical"       # Technology choice conflicts
    RESOURCE = "resource"         # Resource constraint conflicts
    TIMELINE = "timeline"         # Timeline conflicts
    ARCHITECTURAL = "architectural"  # Design pattern conflicts
    PERFORMANCE = "performance"   # Performance requirement conflicts

@dataclass
class Requirement:
    """Enhanced requirement with progressive introduction"""
    id: str
    description: str
    priority: RequirementPriority
    phase: WorkflowPhase
    dependencies: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    agents_required: List[str] = field(default_factory=list)
    acceptance_criteria: Dict[str, Any] = field(default_factory=dict)
    completion_percentage: float = 0.0
    status: str = "pending"
    introduced_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    def is_ready(self, completed_requirements: List[str]) -> bool:
        """Check if requirement is ready to be introduced"""
        return all(dep in completed_requirements for dep in self.dependencies)
    
    def has_conflict(self, active_requirements: List[str]) -> bool:
        """Check if requirement conflicts with active requirements"""
        return any(req in active_requirements for req in self.conflicts_with)

@dataclass
class Checkpoint:
    """Workflow checkpoint for recovery testing"""
    id: str
    phase: WorkflowPhase
    timestamp: datetime
    context: AgentContext
    completed_requirements: List[str]
    active_agents: List[str]
    metrics: Dict[str, Any]
    error_state: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        """Serialize checkpoint to dictionary"""
        return {
            "id": self.id,
            "phase": self.phase.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context.to_dict(),
            "completed_requirements": self.completed_requirements,
            "active_agents": self.active_agents,
            "metrics": self.metrics,
            "error_state": self.error_state
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Checkpoint':
        """Deserialize checkpoint from dictionary"""
        return cls(
            id=data["id"],
            phase=WorkflowPhase(data["phase"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context=AgentContext(**data["context"]),
            completed_requirements=data["completed_requirements"],
            active_agents=data["active_agents"],
            metrics=data["metrics"],
            error_state=data.get("error_state")
        )

@dataclass
class FailureInjection:
    """Configuration for failure injection testing"""
    enabled: bool = False
    agent_failure_rates: Dict[str, float] = field(default_factory=dict)
    tool_failure_rates: Dict[str, float] = field(default_factory=dict)
    network_failure_rate: float = 0.0
    checkpoint_failure_rate: float = 0.0
    recovery_strategy: str = "exponential_backoff"
    max_retries: int = 3
    failure_patterns: List[str] = field(default_factory=list)
    
    def should_fail(self, component: str, component_type: str = "agent") -> bool:
        """Determine if a component should fail based on configuration"""
        if not self.enabled:
            return False
            
        if component_type == "agent":
            rate = self.agent_failure_rates.get(component, 0.0)
        elif component_type == "tool":
            rate = self.tool_failure_rates.get(component, 0.0)
        else:
            rate = self.network_failure_rate
            
        return random.random() < rate

class AdvancedWorkflowEngine:
    """Advanced workflow engine for comprehensive E2E testing"""
    
    def __init__(self, 
                 name: str,
                 use_mock: bool = True,
                 failure_injection: Optional[FailureInjection] = None,
                 checkpoint_dir: Optional[Path] = None):
        """Initialize the workflow engine
        
        Args:
            name: Workflow name for identification
            use_mock: Use mock client instead of real API
            failure_injection: Configuration for failure testing
            checkpoint_dir: Directory for checkpoint storage
        """
        self.name = name
        self.use_mock = use_mock
        self.failure_injection = failure_injection or FailureInjection()
        self.checkpoint_dir = checkpoint_dir or Path("tests/checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.logger = get_logger()
        self.requirements: List[Requirement] = []
        self.checkpoints: List[Checkpoint] = []
        self.current_phase = WorkflowPhase.INITIALIZATION
        self.context: Optional[AgentContext] = None
        self.runner: Optional[AnthropicAgentRunner] = None
        
        # Metrics tracking
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "total_agents_executed": 0,
            "successful_agents": 0,
            "failed_agents": 0,
            "requirements_completed": 0,
            "requirements_failed": 0,
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "checkpoints_created": 0,
            "recoveries_attempted": 0,
            "recoveries_successful": 0,
            "tool_calls": 0,
            "api_calls": 0,
            "estimated_cost": 0.0,
            "phase_timings": {},
            "agent_timings": {},
            "quality_scores": {}
        }
        
        # Conflict resolution strategies
        self.conflict_resolution_strategies = {
            ConflictType.TECHNICAL: self._resolve_technical_conflict,
            ConflictType.RESOURCE: self._resolve_resource_conflict,
            ConflictType.TIMELINE: self._resolve_timeline_conflict,
            ConflictType.ARCHITECTURAL: self._resolve_architectural_conflict,
            ConflictType.PERFORMANCE: self._resolve_performance_conflict
        }
        
    def add_requirement(self, requirement: Requirement):
        """Add a requirement to the workflow"""
        self.requirements.append(requirement)
        
    def add_requirements_batch(self, requirements: List[Requirement]):
        """Add multiple requirements at once"""
        self.requirements.extend(requirements)
        
    def set_context(self, context: AgentContext):
        """Set the initial context for the workflow"""
        self.context = context
        
    async def initialize(self):
        """Initialize the workflow engine and components"""
        self.metrics["start_time"] = datetime.now()
        
        # Initialize runner based on mode
        if self.use_mock:
            # For mock mode, we use the regular runner with mock client
            # This ensures all the tool registration works properly
            self.runner = AnthropicAgentRunner(logger=self.logger)
            # The runner will use mock mode if no API key is set
            self.runner.client = None  # Force mock mode
        else:
            self.runner = AnthropicAgentRunner(logger=self.logger)
            
        # Register standard tools
        for tool in create_standard_tools():
            self.runner.register_tool(tool)
            
        # Initialize context if not set
        if not self.context:
            self.context = AgentContext(
                project_requirements={},
                completed_tasks=[],
                artifacts={},
                decisions=[],
                current_phase=self.current_phase.value
            )
            
        self.logger.log_agent_start(
            "workflow_engine",
            f"Initialized {self.name}",
            f"Mode: {'mock' if self.use_mock else 'live'}, Failure injection: {self.failure_injection.enabled}"
        )
        
    async def execute_workflow(self) -> Dict[str, Any]:
        """Execute the complete workflow with progressive requirements"""
        await self.initialize()
        
        try:
            # Execute each phase
            for phase in WorkflowPhase:
                await self._execute_phase(phase)
                
            # Final validation
            await self._validate_completion()
            
        except Exception as e:
            self.logger.log_error("workflow_engine", str(e), "Workflow execution failed")
            await self._attempt_recovery()
            
        finally:
            self.metrics["end_time"] = datetime.now()
            return self._generate_report()
            
    async def _execute_phase(self, phase: WorkflowPhase):
        """Execute a specific workflow phase"""
        self.current_phase = phase
        self.context.current_phase = phase.value
        phase_start = datetime.now()
        
        self.logger.log_agent_start(
            f"phase_{phase.value}",
            f"Starting {phase.value} phase",
            f"Requirements pending: {len([r for r in self.requirements if r.phase == phase and r.status == 'pending'])}"
        )
        
        # Get requirements for this phase
        phase_requirements = self._get_phase_requirements(phase)
        
        # Progressive requirement introduction
        for requirement in phase_requirements:
            if await self._should_introduce_requirement(requirement):
                await self._introduce_requirement(requirement)
                
        # Create checkpoint
        await self._create_checkpoint(f"phase_{phase.value}_complete")
        
        # Record phase timing
        self.metrics["phase_timings"][phase.value] = (datetime.now() - phase_start).total_seconds()
        
    async def _should_introduce_requirement(self, requirement: Requirement) -> bool:
        """Determine if a requirement should be introduced"""
        completed_reqs = [r.id for r in self.requirements if r.status == "completed"]
        active_reqs = [r.id for r in self.requirements if r.status == "in_progress"]
        
        # Check dependencies
        if not requirement.is_ready(completed_reqs):
            return False
            
        # Check for conflicts
        if requirement.has_conflict(active_reqs):
            # Attempt conflict resolution
            return await self._attempt_conflict_resolution(requirement, active_reqs)
            
        return True
        
    async def _introduce_requirement(self, requirement: Requirement):
        """Introduce and execute a requirement"""
        requirement.introduced_at = datetime.now()
        requirement.status = "in_progress"
        
        self.logger.log_reasoning(
            "requirement_introduction",
            f"Introducing requirement {requirement.id}: {requirement.description}"
        )
        
        # Execute agents for this requirement
        for agent_name in requirement.agents_required:
            if await self._should_execute_agent(agent_name):
                success = await self._execute_agent(agent_name, requirement)
                
                if not success and self.failure_injection.enabled:
                    # Attempt recovery
                    success = await self._recover_agent_execution(agent_name, requirement)
                    
                if not success and requirement.priority == RequirementPriority.CRITICAL:
                    raise Exception(f"Critical requirement {requirement.id} failed")
                    
        # Update requirement status
        await self._validate_requirement(requirement)
        
    async def _should_execute_agent(self, agent_name: str) -> bool:
        """Check if agent should be executed (for failure injection)"""
        if self.failure_injection.should_fail(agent_name, "agent"):
            self.logger.log_error(
                agent_name,
                "Simulated failure",
                "Failure injection triggered"
            )
            self.metrics["failed_agents"] += 1
            return False
        return True
        
    async def _execute_agent(self, agent_name: str, requirement: Requirement) -> bool:
        """Execute a specific agent for a requirement"""
        agent_start = datetime.now()
        self.metrics["total_agents_executed"] += 1
        
        try:
            # Simulate agent execution with context
            agent_prompt = f"Execute {requirement.description} with priority {requirement.priority.value}"
            
            success, result, updated_context = await self.runner.run_agent_async(
                agent_name,
                agent_prompt,
                self.context,
                model=ModelType.SONNET,
                max_iterations=5
            )
            
            if success:
                self.context = updated_context
                self.metrics["successful_agents"] += 1
                
                # Track agent timing
                self.metrics["agent_timings"][agent_name] = (datetime.now() - agent_start).total_seconds()
                
                return True
            else:
                self.metrics["failed_agents"] += 1
                return False
                
        except Exception as e:
            self.logger.log_error(agent_name, str(e), "Agent execution failed")
            self.metrics["failed_agents"] += 1
            return False
            
    async def _recover_agent_execution(self, agent_name: str, requirement: Requirement) -> bool:
        """Attempt to recover from agent execution failure"""
        self.metrics["recoveries_attempted"] += 1
        
        for attempt in range(self.failure_injection.max_retries):
            self.logger.log_reasoning(
                f"{agent_name}_recovery",
                f"Recovery attempt {attempt + 1}/{self.failure_injection.max_retries}"
            )
            
            # Exponential backoff
            await asyncio.sleep(2 ** attempt)
            
            # Retry execution
            if await self._execute_agent(agent_name, requirement):
                self.metrics["recoveries_successful"] += 1
                return True
                
        return False
        
    async def _validate_requirement(self, requirement: Requirement):
        """Validate requirement completion"""
        validation_results = {}
        
        # Check acceptance criteria
        for criterion, expected in requirement.acceptance_criteria.items():
            actual = self._evaluate_criterion(criterion, expected)
            validation_results[criterion] = {
                "expected": expected,
                "actual": actual,
                "passed": actual == expected
            }
            
        requirement.validation_results = validation_results
        
        # Calculate completion percentage
        passed_criteria = sum(1 for r in validation_results.values() if r["passed"])
        total_criteria = len(validation_results)
        
        requirement.completion_percentage = (passed_criteria / total_criteria * 100) if total_criteria > 0 else 0
        
        # Update status
        if requirement.completion_percentage >= 80:  # 80% threshold for completion
            requirement.status = "completed"
            requirement.completed_at = datetime.now()
            self.metrics["requirements_completed"] += 1
        else:
            requirement.status = "failed"
            self.metrics["requirements_failed"] += 1
            
    def _evaluate_criterion(self, criterion: str, expected: Any) -> Any:
        """Evaluate a specific acceptance criterion"""
        # Check in context artifacts
        if criterion in self.context.artifacts:
            return self.context.artifacts[criterion]
            
        # Check in created files
        if criterion == "files_created":
            return len(self.context.get_all_files())
            
        # Check in completed tasks
        if criterion == "agents_completed":
            return len(self.context.completed_tasks)
            
        return None
        
    async def _attempt_conflict_resolution(self, requirement: Requirement, active_requirements: List[str]) -> bool:
        """Attempt to resolve conflicts between requirements"""
        self.metrics["conflicts_detected"] += 1
        
        for active_req_id in active_requirements:
            if active_req_id in requirement.conflicts_with:
                # Identify conflict type
                conflict_type = self._identify_conflict_type(requirement.id, active_req_id)
                
                # Apply resolution strategy
                resolution_strategy = self.conflict_resolution_strategies.get(
                    conflict_type,
                    self._default_conflict_resolution
                )
                
                if await resolution_strategy(requirement, active_req_id):
                    self.metrics["conflicts_resolved"] += 1
                    return True
                    
        return False
        
    def _identify_conflict_type(self, req1_id: str, req2_id: str) -> ConflictType:
        """Identify the type of conflict between requirements"""
        # Simple heuristic - can be enhanced with NLP
        if "tech" in req1_id.lower() or "tech" in req2_id.lower():
            return ConflictType.TECHNICAL
        elif "resource" in req1_id.lower() or "resource" in req2_id.lower():
            return ConflictType.RESOURCE
        elif "time" in req1_id.lower() or "time" in req2_id.lower():
            return ConflictType.TIMELINE
        elif "arch" in req1_id.lower() or "arch" in req2_id.lower():
            return ConflictType.ARCHITECTURAL
        elif "perf" in req1_id.lower() or "perf" in req2_id.lower():
            return ConflictType.PERFORMANCE
        else:
            return ConflictType.TECHNICAL
            
    async def _resolve_technical_conflict(self, requirement: Requirement, conflicting_id: str) -> bool:
        """Resolve technical conflicts between requirements"""
        self.logger.log_reasoning(
            "conflict_resolution",
            f"Resolving technical conflict between {requirement.id} and {conflicting_id}"
        )
        
        # Prioritize based on requirement priority
        conflicting_req = next((r for r in self.requirements if r.id == conflicting_id), None)
        if conflicting_req and requirement.priority.value < conflicting_req.priority.value:
            # Defer lower priority requirement
            requirement.phase = WorkflowPhase.INTEGRATION  # Move to later phase
            return True
            
        return False
        
    async def _resolve_resource_conflict(self, requirement: Requirement, conflicting_id: str) -> bool:
        """Resolve resource conflicts"""
        # Implement resource allocation logic
        return False
        
    async def _resolve_timeline_conflict(self, requirement: Requirement, conflicting_id: str) -> bool:
        """Resolve timeline conflicts"""
        # Adjust timeline or defer requirement
        return False
        
    async def _resolve_architectural_conflict(self, requirement: Requirement, conflicting_id: str) -> bool:
        """Resolve architectural conflicts"""
        # Consult project-architect agent for resolution
        return False
        
    async def _resolve_performance_conflict(self, requirement: Requirement, conflicting_id: str) -> bool:
        """Resolve performance conflicts"""
        # Balance performance requirements
        return False
        
    async def _default_conflict_resolution(self, requirement: Requirement, conflicting_id: str) -> bool:
        """Default conflict resolution strategy"""
        return False
        
    def _get_phase_requirements(self, phase: WorkflowPhase) -> List[Requirement]:
        """Get requirements for a specific phase"""
        return [r for r in self.requirements if r.phase == phase and r.status == "pending"]
        
    async def _create_checkpoint(self, checkpoint_id: str):
        """Create a workflow checkpoint"""
        checkpoint = Checkpoint(
            id=checkpoint_id,
            phase=self.current_phase,
            timestamp=datetime.now(),
            context=self.context,
            completed_requirements=[r.id for r in self.requirements if r.status == "completed"],
            active_agents=self.context.completed_tasks[-5:] if self.context else [],
            metrics=self.metrics.copy()
        )
        
        self.checkpoints.append(checkpoint)
        self.metrics["checkpoints_created"] += 1
        
        # Save to disk with custom JSON encoder for datetime
        checkpoint_file = self.checkpoint_dir / f"{self.name}_{checkpoint_id}_{int(time.time())}.json"
        
        # Custom JSON encoder for datetime objects
        import json
        from datetime import datetime
        
        def json_encoder(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        checkpoint_file.write_text(json.dumps(checkpoint.to_dict(), indent=2, default=json_encoder))
        
        self.logger.log_reasoning(
            "checkpoint_creation",
            f"Created checkpoint {checkpoint_id} at phase {self.current_phase.value}"
        )
        
    async def restore_from_checkpoint(self, checkpoint_id: str):
        """Restore workflow from a checkpoint"""
        checkpoint = next((c for c in self.checkpoints if c.id == checkpoint_id), None)
        
        if checkpoint:
            self.context = checkpoint.context
            self.current_phase = checkpoint.phase
            self.metrics = checkpoint.metrics
            
            # Update requirement statuses
            for req in self.requirements:
                if req.id in checkpoint.completed_requirements:
                    req.status = "completed"
                    
            self.logger.log_reasoning(
                "checkpoint_restore",
                f"Restored from checkpoint {checkpoint_id}"
            )
            return True
            
        return False
        
    async def _attempt_recovery(self):
        """Attempt to recover from workflow failure"""
        if self.checkpoints:
            last_checkpoint = self.checkpoints[-1]
            if await self.restore_from_checkpoint(last_checkpoint.id):
                # Continue from checkpoint
                await self.execute_workflow()
                
    async def _validate_completion(self):
        """Validate overall workflow completion"""
        critical_requirements = [r for r in self.requirements if r.priority == RequirementPriority.CRITICAL]
        critical_completed = [r for r in critical_requirements if r.status == "completed"]
        
        if len(critical_completed) < len(critical_requirements):
            raise Exception(f"Not all critical requirements completed: {len(critical_completed)}/{len(critical_requirements)}")
            
        # Calculate quality scores
        self._calculate_quality_scores()
        
    def _calculate_quality_scores(self):
        """Calculate quality scores for the workflow"""
        # Requirement coverage
        total_reqs = len(self.requirements)
        completed_reqs = len([r for r in self.requirements if r.status == "completed"])
        self.metrics["quality_scores"]["requirement_coverage"] = (completed_reqs / total_reqs * 100) if total_reqs > 0 else 0
        
        # Agent success rate
        total_agents = self.metrics["total_agents_executed"]
        successful_agents = self.metrics["successful_agents"]
        self.metrics["quality_scores"]["agent_success_rate"] = (successful_agents / total_agents * 100) if total_agents > 0 else 0
        
        # Recovery success rate
        recoveries = self.metrics["recoveries_attempted"]
        successful_recoveries = self.metrics["recoveries_successful"]
        self.metrics["quality_scores"]["recovery_success_rate"] = (successful_recoveries / recoveries * 100) if recoveries > 0 else 100
        
        # Conflict resolution rate
        conflicts = self.metrics["conflicts_detected"]
        resolved = self.metrics["conflicts_resolved"]
        self.metrics["quality_scores"]["conflict_resolution_rate"] = (resolved / conflicts * 100) if conflicts > 0 else 100
        
        # Overall quality score (weighted average)
        weights = {
            "requirement_coverage": 0.4,
            "agent_success_rate": 0.3,
            "recovery_success_rate": 0.2,
            "conflict_resolution_rate": 0.1
        }
        
        overall_score = sum(
            self.metrics["quality_scores"][metric] * weight
            for metric, weight in weights.items()
        )
        
        self.metrics["quality_scores"]["overall"] = overall_score
        
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive workflow report"""
        duration = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds() if self.metrics["end_time"] else 0
        
        return {
            "workflow_name": self.name,
            "execution_mode": "mock" if self.use_mock else "live",
            "duration_seconds": duration,
            "phases_completed": len(self.metrics["phase_timings"]),
            "requirements": {
                "total": len(self.requirements),
                "completed": self.metrics["requirements_completed"],
                "failed": self.metrics["requirements_failed"],
                "completion_rate": (self.metrics["requirements_completed"] / len(self.requirements) * 100) if self.requirements else 0
            },
            "agents": {
                "total_executed": self.metrics["total_agents_executed"],
                "successful": self.metrics["successful_agents"],
                "failed": self.metrics["failed_agents"],
                "success_rate": (self.metrics["successful_agents"] / self.metrics["total_agents_executed"] * 100) if self.metrics["total_agents_executed"] > 0 else 0
            },
            "conflicts": {
                "detected": self.metrics["conflicts_detected"],
                "resolved": self.metrics["conflicts_resolved"],
                "resolution_rate": (self.metrics["conflicts_resolved"] / self.metrics["conflicts_detected"] * 100) if self.metrics["conflicts_detected"] > 0 else 100
            },
            "recovery": {
                "attempts": self.metrics["recoveries_attempted"],
                "successful": self.metrics["recoveries_successful"],
                "success_rate": (self.metrics["recoveries_successful"] / self.metrics["recoveries_attempted"] * 100) if self.metrics["recoveries_attempted"] > 0 else 100
            },
            "checkpoints": self.metrics["checkpoints_created"],
            "quality_scores": self.metrics["quality_scores"],
            "phase_timings": self.metrics["phase_timings"],
            "agent_timings": self.metrics["agent_timings"],
            "estimated_cost": self.metrics["estimated_cost"]
        }