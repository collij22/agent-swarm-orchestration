#!/usr/bin/env python3
"""
Enhanced Orchestration System - Section 8 Implementation

Features:
- Adaptive workflow with dynamic agent selection
- Requirement tracking with ID mapping
- Advanced error recovery and retry logic
- Real-time progress monitoring
- Parallel execution with dependency management
- Manual intervention points
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import networkx as nx

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.table import Table
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

try:
    from .agent_logger import ReasoningLogger, get_logger
    from .agent_runtime import AnthropicAgentRunner, AgentContext, ModelType
except ImportError:
    # For standalone imports
    from agent_logger import ReasoningLogger, get_logger
    from agent_runtime import AnthropicAgentRunner, AgentContext, ModelType


class RequirementStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class AgentExecutionStatus(Enum):
    WAITING = "waiting"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    BLOCKED = "blocked"


@dataclass
class RequirementItem:
    """Individual requirement with tracking"""
    id: str
    description: str
    priority: int = 1  # 1=high, 2=medium, 3=low
    status: RequirementStatus = RequirementStatus.PENDING
    assigned_agents: List[str] = None
    dependencies: List[str] = None  # IDs of other requirements
    completion_percentage: float = 0.0
    artifacts: List[str] = None
    error_messages: List[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_effort: int = 1  # Story points or hours
    
    def __post_init__(self):
        if self.assigned_agents is None:
            self.assigned_agents = []
        if self.dependencies is None:
            self.dependencies = []
        if self.artifacts is None:
            self.artifacts = []
        if self.error_messages is None:
            self.error_messages = []


@dataclass
class AgentExecutionPlan:
    """Plan for agent execution with dependencies"""
    agent_name: str
    requirements: List[str]  # Requirement IDs
    dependencies: List[str]  # Other agent names that must complete first
    status: AgentExecutionStatus = AgentExecutionStatus.WAITING
    priority: int = 1
    max_retries: int = 3
    current_retry: int = 0
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    artifacts_produced: List[str] = None
    
    def __post_init__(self):
        if self.artifacts_produced is None:
            self.artifacts_produced = []


@dataclass
class WorkflowProgress:
    """Real-time workflow progress tracking"""
    workflow_id: str
    total_requirements: int
    completed_requirements: int
    failed_requirements: int
    blocked_requirements: int
    total_agents: int
    completed_agents: int
    failed_agents: int
    running_agents: int
    overall_completion: float
    estimated_remaining_time: Optional[float]
    started_at: str
    updated_at: str
    
    def to_dict(self):
        return asdict(self)


class AdaptiveWorkflowEngine:
    """Enhanced workflow engine with adaptive capabilities"""
    
    def __init__(self, logger: ReasoningLogger):
        self.logger = logger
        self.console = Console() if HAS_RICH else None
        
        # Core state
        self.workflow_id = str(uuid.uuid4())
        self.requirements: Dict[str, RequirementItem] = {}
        self.agent_plans: Dict[str, AgentExecutionPlan] = {}
        self.dependency_graph = nx.DiGraph()
        
        # Progress tracking
        self.progress = WorkflowProgress(
            workflow_id=self.workflow_id,
            total_requirements=0,
            completed_requirements=0,
            failed_requirements=0,
            blocked_requirements=0,
            total_agents=0,
            completed_agents=0,
            failed_agents=0,
            running_agents=0,
            overall_completion=0.0,
            estimated_remaining_time=None,
            started_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Configuration
        self.max_parallel_agents = 3
        self.retry_delays = [5, 15, 30]  # seconds
        self.intervention_threshold = 0.5  # Intervention after 50% failures
        
        # Callbacks for progress updates
        self.progress_callbacks: List[Callable[[WorkflowProgress], None]] = []
    
    def add_progress_callback(self, callback: Callable[[WorkflowProgress], None]):
        """Add callback for progress updates"""
        self.progress_callbacks.append(callback)
    
    def _update_progress(self):
        """Update overall progress and notify callbacks"""
        self.progress.updated_at = datetime.now().isoformat()
        
        # Update requirement stats
        req_statuses = [req.status for req in self.requirements.values()]
        self.progress.total_requirements = len(self.requirements)
        self.progress.completed_requirements = req_statuses.count(RequirementStatus.COMPLETED)
        self.progress.failed_requirements = req_statuses.count(RequirementStatus.FAILED)
        self.progress.blocked_requirements = req_statuses.count(RequirementStatus.BLOCKED)
        
        # Update agent stats
        agent_statuses = [plan.status for plan in self.agent_plans.values()]
        self.progress.total_agents = len(self.agent_plans)
        self.progress.completed_agents = agent_statuses.count(AgentExecutionStatus.COMPLETED)
        self.progress.failed_agents = agent_statuses.count(AgentExecutionStatus.FAILED)
        self.progress.running_agents = agent_statuses.count(AgentExecutionStatus.RUNNING)
        
        # Calculate overall completion
        if self.progress.total_requirements > 0:
            self.progress.overall_completion = (
                self.progress.completed_requirements / self.progress.total_requirements
            ) * 100
        
        # Estimate remaining time
        self._estimate_remaining_time()
        
        # Notify callbacks
        for callback in self.progress_callbacks:
            try:
                callback(self.progress)
            except Exception as e:
                self.logger.log_error("orchestrator", f"Progress callback failed: {e}")
    
    def _estimate_remaining_time(self):
        """Estimate remaining execution time"""
        completed_agents = [p for p in self.agent_plans.values() 
                          if p.status == AgentExecutionStatus.COMPLETED and p.execution_time]
        
        if not completed_agents:
            self.progress.estimated_remaining_time = None
            return
        
        # Calculate average execution time
        avg_time = sum(p.execution_time for p in completed_agents) / len(completed_agents)
        
        # Count remaining agents
        remaining = len([p for p in self.agent_plans.values() 
                        if p.status in [AgentExecutionStatus.WAITING, AgentExecutionStatus.RUNNING]])
        
        # Estimate with parallelization factor
        parallel_factor = min(self.max_parallel_agents, remaining) if remaining > 0 else 1
        estimated_time = (remaining * avg_time) / parallel_factor
        
        self.progress.estimated_remaining_time = estimated_time
    
    def parse_requirements_with_ids(self, requirements_dict: Dict) -> Dict[str, RequirementItem]:
        """Parse requirements and assign IDs with dependency analysis"""
        parsed_requirements = {}
        
        features = requirements_dict.get("features", [])
        
        for idx, feature in enumerate(features):
            # Handle both string features and dictionary features
            if isinstance(feature, dict):
                # Use the existing ID or create one
                req_id = feature.get("id", f"REQ-{idx+1:03d}")
                # Get description from the feature dict
                feature_desc = feature.get("description", feature.get("title", str(feature)))
            else:
                req_id = f"REQ-{idx+1:03d}"
                feature_desc = str(feature)
            
            # Analyze feature for agent assignments and priorities
            assigned_agents, priority = self._analyze_feature_requirements(feature)
            
            # Detect dependencies (simple heuristic)
            dependencies = self._detect_dependencies(feature, features[:idx])
            
            requirement = RequirementItem(
                id=req_id,
                description=feature_desc,
                priority=priority,
                assigned_agents=assigned_agents,
                dependencies=dependencies,
                estimated_effort=self._estimate_effort(feature)
            )
            
            parsed_requirements[req_id] = requirement
        
        # Add technical requirements
        tech_requirements = self._extract_technical_requirements(requirements_dict)
        for idx, tech_req in enumerate(tech_requirements):
            req_id = f"TECH-{idx+1:03d}"
            tech_req.id = req_id  # Update the ID in the requirement
            parsed_requirements[req_id] = tech_req
        
        self.requirements = parsed_requirements
        self._build_dependency_graph()
        
        return parsed_requirements
    
    def _analyze_feature_requirements(self, feature) -> Tuple[List[str], int]:
        """Analyze feature to determine required agents and priority"""
        # Handle both string and dict features
        if isinstance(feature, dict):
            feature_text = f"{feature.get('title', '')} {feature.get('description', '')} {feature.get('id', '')}"
            feature_priority = feature.get('priority', 'medium')
        else:
            feature_text = str(feature)
            feature_priority = 'medium'
        
        feature_lower = feature_text.lower()
        assigned_agents = []
        
        # Use priority from feature dict if available, otherwise determine from text
        if feature_priority in ['high', 'critical']:
            priority = 1
        elif feature_priority == 'low':
            priority = 3
        else:
            priority = 2  # Default medium priority
        
        # Agent assignment rules
        agent_patterns = {
            "frontend-specialist": ["ui", "frontend", "react", "vue", "angular", "interface", "dashboard"],
            "ai-specialist": ["ai", "ml", "categorization", "classification", "recommendation", "intelligent"],
            "database-expert": ["database", "sql", "postgresql", "mongodb", "data model", "schema"],
            "api-integrator": ["api", "integration", "webhook", "external", "third-party"],
            "quality-guardian": ["test", "security", "validation", "compliance", "audit"],
            "performance-optimizer": ["performance", "optimization", "caching", "scaling"],
            "devops-engineer": ["deployment", "docker", "ci/cd", "infrastructure", "monitoring"],
            "documentation-writer": ["documentation", "guide", "manual", "api docs"]
        }
        
        for agent, patterns in agent_patterns.items():
            if any(pattern in feature_lower for pattern in patterns):
                assigned_agents.append(agent)
        
        # Default to rapid-builder for general development
        if not assigned_agents:
            assigned_agents.append("rapid-builder")
        
        # Priority assignment
        high_priority_patterns = ["authentication", "security", "core", "main", "critical"]
        low_priority_patterns = ["nice to have", "optional", "future", "enhancement"]
        
        if any(pattern in feature_lower for pattern in high_priority_patterns):
            priority = 1
        elif any(pattern in feature_lower for pattern in low_priority_patterns):
            priority = 3
        
        return assigned_agents, priority
    
    def _detect_dependencies(self, current_feature, previous_features: List) -> List[str]:
        """Detect dependencies between requirements (simple heuristic)"""
        dependencies = []
        
        # Handle both string and dict features
        if isinstance(current_feature, dict):
            current_text = f"{current_feature.get('title', '')} {current_feature.get('description', '')}"
        else:
            current_text = str(current_feature)
        
        current_lower = current_text.lower()
        
        dependency_patterns = {
            "frontend": ["api", "backend", "authentication"],
            "dashboard": ["authentication", "api", "database"],
            "testing": ["implementation", "api", "frontend"],
            "deployment": ["testing", "implementation"],
            "optimization": ["implementation", "basic functionality"]
        }
        
        for pattern, deps in dependency_patterns.items():
            if pattern in current_lower:
                for idx, prev_feature in enumerate(previous_features):
                    # Handle both string and dict for previous features
                    if isinstance(prev_feature, dict):
                        prev_text = f"{prev_feature.get('title', '')} {prev_feature.get('description', '')}"
                    else:
                        prev_text = str(prev_feature)
                    prev_lower = prev_text.lower()
                    if any(dep in prev_lower for dep in deps):
                        dependencies.append(f"REQ-{idx+1:03d}")
        
        return dependencies
    
    def _estimate_effort(self, feature) -> int:
        """Estimate effort in story points (1-8)"""
        # Handle both string and dict features
        if isinstance(feature, dict):
            feature_text = f"{feature.get('title', '')} {feature.get('description', '')}"
        else:
            feature_text = str(feature)
            
        feature_lower = feature_text.lower()
        
        # High effort patterns
        if any(pattern in feature_lower for pattern in [
            "complete", "full", "comprehensive", "advanced", "complex", "ai", "ml"
        ]):
            return 5
        
        # Low effort patterns
        if any(pattern in feature_lower for pattern in [
            "simple", "basic", "minimal", "documentation", "config"
        ]):
            return 1
        
        # Medium effort (default)
        return 3
    
    def _extract_technical_requirements(self, requirements_dict: Dict) -> List[RequirementItem]:
        """Extract technical requirements from project spec"""
        tech_requirements = []
        
        # Docker requirement
        if requirements_dict.get("deployment") == "docker" or "docker" in str(requirements_dict).lower():
            tech_requirements.append(RequirementItem(
                id="TECH-001",
                description="Docker containerization",
                priority=1,
                assigned_agents=["devops-engineer"],
                estimated_effort=3
            ))
        
        # Testing requirement
        if requirements_dict.get("testing_requirements") or "test" in str(requirements_dict).lower():
            tech_requirements.append(RequirementItem(
                id="TECH-002", 
                description="Testing infrastructure",
                priority=1,
                assigned_agents=["quality-guardian"],
                estimated_effort=4
            ))
        
        return tech_requirements
    
    def _build_dependency_graph(self):
        """Build dependency graph for requirements"""
        self.dependency_graph.clear()
        
        # Add nodes
        for req_id in self.requirements:
            self.dependency_graph.add_node(req_id)
        
        # Add dependency edges
        for req_id, requirement in self.requirements.items():
            for dep_id in requirement.dependencies:
                if dep_id in self.requirements:
                    self.dependency_graph.add_edge(dep_id, req_id)
    
    def create_adaptive_execution_plan(self, available_agents: List[str]) -> Dict[str, AgentExecutionPlan]:
        """Create execution plan with dependency-aware agent scheduling"""
        agent_plans = {}
        
        # Group requirements by assigned agents
        agent_requirements = {}
        for req_id, requirement in self.requirements.items():
            for agent in requirement.assigned_agents:
                if agent in available_agents:
                    if agent not in agent_requirements:
                        agent_requirements[agent] = []
                    agent_requirements[agent].append(req_id)
        
        # Create execution plans
        for agent, req_ids in agent_requirements.items():
            # Calculate dependencies (agents that must run first)
            agent_deps = self._calculate_agent_dependencies(agent, req_ids)
            
            # Calculate priority (highest priority requirement)
            priorities = [self.requirements[req_id].priority for req_id in req_ids]
            agent_priority = min(priorities) if priorities else 2
            
            agent_plans[agent] = AgentExecutionPlan(
                agent_name=agent,
                requirements=req_ids,
                dependencies=agent_deps,
                priority=agent_priority,
                max_retries=3 if agent_priority == 1 else 2  # More retries for high priority
            )
        
        self.agent_plans = agent_plans
        return agent_plans
    
    def _calculate_agent_dependencies(self, agent: str, req_ids: List[str]) -> List[str]:
        """Calculate which agents must complete before this agent can run"""
        dependencies = set()
        
        for req_id in req_ids:
            requirement = self.requirements[req_id]
            
            # Check requirement dependencies
            for dep_req_id in requirement.dependencies:
                if dep_req_id in self.requirements:
                    dep_requirement = self.requirements[dep_req_id]
                    # Add agents responsible for dependency requirements
                    dependencies.update(dep_requirement.assigned_agents)
        
        # Remove self-dependency
        dependencies.discard(agent)
        
        return list(dependencies)
    
    def get_ready_agents(self) -> List[str]:
        """Get agents that are ready to execute (dependencies met)"""
        ready_agents = []
        
        for agent, plan in self.agent_plans.items():
            if plan.status != AgentExecutionStatus.WAITING:
                continue
            
            # Check if all dependencies are completed
            deps_completed = all(
                self.agent_plans[dep_agent].status == AgentExecutionStatus.COMPLETED
                for dep_agent in plan.dependencies
                if dep_agent in self.agent_plans
            )
            
            if deps_completed:
                ready_agents.append(agent)
        
        # Sort by priority
        ready_agents.sort(key=lambda a: self.agent_plans[a].priority)
        
        return ready_agents
    
    async def execute_agent_with_retry(
        self, 
        agent_name: str, 
        runtime: AnthropicAgentRunner,
        context: AgentContext,
        agent_config: Dict
    ) -> Tuple[bool, str, AgentContext]:
        """Execute agent with retry logic and error recovery"""
        plan = self.agent_plans[agent_name]
        plan.status = AgentExecutionStatus.RUNNING
        
        start_time = time.time()
        
        for attempt in range(plan.max_retries + 1):
            plan.current_retry = attempt
            
            try:
                self.logger.log_reasoning(
                    "orchestrator",
                    f"Starting {agent_name} (attempt {attempt + 1}/{plan.max_retries + 1})",
                    f"Requirements: {', '.join(plan.requirements)}"
                )
                
                # Update requirement statuses to in_progress
                for req_id in plan.requirements:
                    if req_id in self.requirements:
                        self.requirements[req_id].status = RequirementStatus.IN_PROGRESS
                        if not self.requirements[req_id].started_at:
                            self.requirements[req_id].started_at = datetime.now().isoformat()
                
                self._update_progress()
                
                # Execute agent
                success, result, updated_context = await runtime.run_agent_async(
                    agent_name,
                    agent_config["prompt"],
                    context,
                    model=self._get_model(agent_config.get("model", "sonnet")),
                    max_iterations=15
                )
                
                if success:
                    # Success - update statuses
                    plan.status = AgentExecutionStatus.COMPLETED
                    plan.execution_time = time.time() - start_time
                    
                    # Update requirement statuses
                    for req_id in plan.requirements:
                        if req_id in self.requirements:
                            self.requirements[req_id].status = RequirementStatus.COMPLETED
                            self.requirements[req_id].completion_percentage = 100.0
                            self.requirements[req_id].completed_at = datetime.now().isoformat()
                    
                    self._update_progress()
                    
                    return True, result, updated_context
                
                else:
                    # Failure - record error and potentially retry
                    error_msg = f"Agent execution failed: {result}"
                    plan.error_message = error_msg
                    
                    # Update requirement error messages
                    for req_id in plan.requirements:
                        if req_id in self.requirements:
                            self.requirements[req_id].error_messages.append(error_msg)
                    
                    if attempt < plan.max_retries:
                        plan.status = AgentExecutionStatus.RETRYING
                        
                        # Wait before retry with exponential backoff
                        delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                        self.logger.log_reasoning(
                            "orchestrator",
                            f"Agent {agent_name} failed, retrying in {delay}s",
                            error_msg
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        # All retries exhausted
                        plan.status = AgentExecutionStatus.FAILED
                        
                        # Check if manual intervention is needed
                        if await self._should_trigger_intervention():
                            if await self._manual_intervention(agent_name, plan, context):
                                # Manual fix succeeded, continue
                                plan.status = AgentExecutionStatus.COMPLETED
                                return True, "Manual intervention successful", context
                        
                        # Mark requirements as failed
                        for req_id in plan.requirements:
                            if req_id in self.requirements:
                                self.requirements[req_id].status = RequirementStatus.FAILED
                        
                        self._update_progress()
                        return False, error_msg, context
            
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.logger.log_error("orchestrator", error_msg)
                
                if attempt < plan.max_retries:
                    plan.status = AgentExecutionStatus.RETRYING
                    await asyncio.sleep(self.retry_delays[min(attempt, len(self.retry_delays) - 1)])
                else:
                    plan.status = AgentExecutionStatus.FAILED
                    plan.error_message = error_msg
                    
                    for req_id in plan.requirements:
                        if req_id in self.requirements:
                            self.requirements[req_id].status = RequirementStatus.FAILED
                            self.requirements[req_id].error_messages.append(error_msg)
                    
                    self._update_progress()
                    return False, error_msg, context
        
        return False, "Max retries exceeded", context
    
    async def _should_trigger_intervention(self) -> bool:
        """Determine if manual intervention should be offered"""
        failed_count = sum(1 for plan in self.agent_plans.values() 
                          if plan.status == AgentExecutionStatus.FAILED)
        total_count = len(self.agent_plans)
        
        if total_count == 0:
            return False
        
        failure_rate = failed_count / total_count
        return failure_rate >= self.intervention_threshold
    
    async def _manual_intervention(
        self, 
        agent_name: str, 
        plan: AgentExecutionPlan, 
        context: AgentContext
    ) -> bool:
        """Handle manual intervention for failed agent"""
        if not HAS_RICH:
            return False
        
        self.console.print(Panel(
            f"[red]Agent {agent_name} has failed all retry attempts.[/red]\n\n"
            f"Requirements affected: {', '.join(plan.requirements)}\n"
            f"Error: {plan.error_message}\n\n"
            "[yellow]Manual intervention options:[/yellow]\n"
            "1. Skip this agent and continue\n"
            "2. Retry with modified parameters\n"
            "3. Abort entire workflow",
            title="Manual Intervention Required",
            border_style="red"
        ))
        
        from rich.prompt import Prompt, IntPrompt
        choice = IntPrompt.ask("Choose option", choices=["1", "2", "3"])
        
        if choice == 1:
            # Skip agent
            for req_id in plan.requirements:
                if req_id in self.requirements:
                    self.requirements[req_id].status = RequirementStatus.SKIPPED
            return True
        elif choice == 2:
            # Retry with modifications
            # This is a simplified implementation - could be enhanced
            return False
        else:
            # Abort workflow
            raise KeyboardInterrupt("Workflow aborted by user intervention")
    
    def _get_model(self, model_name: str) -> ModelType:
        """Convert model name to ModelType"""
        model_map = {
            "haiku": ModelType.HAIKU,
            "sonnet": ModelType.SONNET,
            "opus": ModelType.OPUS
        }
        return model_map.get(model_name, ModelType.SONNET)
    
    def display_progress(self):
        """Display current progress in rich format"""
        if not HAS_RICH:
            return
        
        table = Table(title="Workflow Progress")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Progress", style="yellow")
        
        table.add_row(
            "Overall Completion", 
            f"{self.progress.overall_completion:.1f}%",
            f"[{'=' * int(self.progress.overall_completion/5):20}]"
        )
        table.add_row(
            "Requirements", 
            f"{self.progress.completed_requirements}/{self.progress.total_requirements}",
            f"✓ {self.progress.completed_requirements} ✗ {self.progress.failed_requirements}"
        )
        table.add_row(
            "Agents",
            f"{self.progress.completed_agents}/{self.progress.total_agents}",
            f"✓ {self.progress.completed_agents} ⏳ {self.progress.running_agents} ✗ {self.progress.failed_agents}"
        )
        
        if self.progress.estimated_remaining_time:
            remaining_mins = int(self.progress.estimated_remaining_time / 60)
            table.add_row("Est. Remaining", f"{remaining_mins} minutes", "")
        
        self.console.print(table)
    
    def _serialize_for_json(self, obj):
        """Custom serializer for JSON dump to handle Enums"""
        if isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if isinstance(value, Enum):
                    result[key] = value.value
                elif isinstance(value, list):
                    result[key] = [self._serialize_for_json(v) for v in value]
                elif isinstance(value, dict):
                    result[key] = {k: self._serialize_for_json(v) for k, v in value.items()}
                else:
                    result[key] = value
            return result
        return obj
    
    def get_execution_summary(self) -> Dict:
        """Get detailed execution summary"""
        # Convert enums to values for JSON serialization
        requirements_dict = {}
        for req_id, req in self.requirements.items():
            req_dict = asdict(req)
            req_dict['status'] = req.status.value if isinstance(req.status, Enum) else req.status
            requirements_dict[req_id] = req_dict
            
        agent_plans_dict = {}
        for agent, plan in self.agent_plans.items():
            plan_dict = asdict(plan)
            plan_dict['status'] = plan.status.value if isinstance(plan.status, Enum) else plan.status
            agent_plans_dict[agent] = plan_dict
        
        return {
            "workflow_id": self.workflow_id,
            "progress": asdict(self.progress),
            "requirements": requirements_dict,
            "agent_plans": agent_plans_dict,
            "dependency_graph": {
                "nodes": list(self.dependency_graph.nodes()),
                "edges": list(self.dependency_graph.edges())
            }
        }
    
    def save_checkpoint(self, checkpoint_path: Path):
        """Save comprehensive checkpoint"""
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": self.workflow_id,
            "execution_summary": self.get_execution_summary()
        }
        
        # Custom JSON encoder for Enums
        def enum_encoder(obj):
            if isinstance(obj, Enum):
                return obj.value
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=enum_encoder)
        
        self.logger.log_reasoning(
            "orchestrator",
            f"Checkpoint saved: {checkpoint_path}",
            "Comprehensive workflow state saved"
        )
    
    def load_checkpoint(self, checkpoint_path: Path) -> bool:
        """Load checkpoint and restore state"""
        try:
            with open(checkpoint_path) as f:
                checkpoint_data = json.load(f)
            
            summary = checkpoint_data["execution_summary"]
            
            # Restore requirements with enum conversion
            self.requirements = {}
            for req_id, req_data in summary["requirements"].items():
                # Convert status string back to enum if needed
                if 'status' in req_data and isinstance(req_data['status'], str):
                    req_data['status'] = RequirementStatus(req_data['status'])
                self.requirements[req_id] = RequirementItem(**req_data)
            
            # Restore agent plans with enum conversion
            self.agent_plans = {}
            for agent, plan_data in summary["agent_plans"].items():
                # Convert status string back to enum if needed
                if 'status' in plan_data and isinstance(plan_data['status'], str):
                    plan_data['status'] = AgentExecutionStatus(plan_data['status'])
                self.agent_plans[agent] = AgentExecutionPlan(**plan_data)
            
            # Restore progress
            self.progress = WorkflowProgress(**summary["progress"])
            self.workflow_id = summary["workflow_id"]
            
            # Rebuild dependency graph
            self._build_dependency_graph()
            
            self.logger.log_reasoning(
                "orchestrator",
                f"Checkpoint loaded: {checkpoint_path}",
                f"Restored workflow {self.workflow_id}"
            )
            
            return True
        
        except Exception as e:
            self.logger.log_error("orchestrator", f"Failed to load checkpoint: {e}")
            return False


# Export classes for use in orchestrate_v2.py
__all__ = [
    "AdaptiveWorkflowEngine",
    "RequirementItem",
    "AgentExecutionPlan", 
    "WorkflowProgress",
    "RequirementStatus",
    "AgentExecutionStatus"
]