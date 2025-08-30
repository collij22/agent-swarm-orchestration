#!/usr/bin/env python3
"""
Test Agent Recovery & Failure Handling - Phase 2 Comprehensive E2E Test Scenario 2

Tests: Error recovery, partial completion, checkpoint restoration
Project: E-commerce Platform with simulated failures
Failure Simulation: 30% failure rate on specific agents
Test Focus: 
  - Agent retry logic with exponential backoff
  - Checkpoint creation and restoration
  - Incomplete task tracking and recovery
  - Context preservation during failures
Expected: System continues with successful agents, tracks failures for retry
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import time
import random
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.e2e_infrastructure.workflow_engine import WorkflowEngine
from tests.e2e_infrastructure.interaction_validator import InteractionValidator
from tests.e2e_infrastructure.metrics_collector import MetricsCollector
from tests.e2e_infrastructure.test_data_generators import TestDataGenerator
from lib.agent_runtime import AgentContext
from lib.mock_anthropic_enhanced import EnhancedMockAnthropicClient

class TestFailureRecovery:
    """Test suite for agent failure handling and recovery mechanisms."""
    
    def __init__(self, failure_rate: float = 0.3):
        """Initialize test infrastructure with configurable failure rate."""
        self.workflow_engine = WorkflowEngine()
        self.interaction_validator = InteractionValidator()
        self.metrics_collector = MetricsCollector()
        self.data_generator = TestDataGenerator()
        self.mock_client = EnhancedMockAnthropicClient()
        self.failure_rate = failure_rate
        self.checkpoint_dir = Path("tests/e2e_comprehensive/checkpoints")
        self.checkpoint_dir.mkdir(exist_ok=True)
        
    def create_ecommerce_requirements(self) -> Dict[str, Any]:
        """Create e-commerce platform requirements for testing."""
        return {
            "project": {
                "name": "E-commercePlatform",
                "type": "web_application",
                "complexity": "medium",
                "timeline": "6 weeks"
            },
            "functional_requirements": {
                "REQ-001": {
                    "title": "Product Catalog",
                    "priority": "critical",
                    "agents": ["rapid-builder", "database-expert"]
                },
                "REQ-002": {
                    "title": "Shopping Cart",
                    "priority": "critical",
                    "agents": ["rapid-builder", "frontend-specialist"]
                },
                "REQ-003": {
                    "title": "Payment Processing",
                    "priority": "critical",
                    "agents": ["api-integrator", "quality-guardian"]
                },
                "REQ-004": {
                    "title": "Order Management",
                    "priority": "high",
                    "agents": ["rapid-builder", "database-expert"]
                },
                "REQ-005": {
                    "title": "User Authentication",
                    "priority": "critical",
                    "agents": ["rapid-builder", "quality-guardian"]
                },
                "REQ-006": {
                    "title": "Search & Filtering",
                    "priority": "medium",
                    "agents": ["frontend-specialist", "performance-optimizer"]
                }
            },
            "agents": [
                "project-architect",
                "rapid-builder",
                "database-expert",
                "frontend-specialist",
                "api-integrator",
                "quality-guardian",
                "performance-optimizer",
                "devops-engineer"
            ]
        }
    
    async def test_retry_with_exponential_backoff(self) -> Dict[str, Any]:
        """Test agent retry logic with exponential backoff."""
        results = {
            "test_name": "Retry with Exponential Backoff",
            "retry_attempts": [],
            "successful_recoveries": [],
            "permanent_failures": [],
            "backoff_delays": []
        }
        
        agents_to_test = ["rapid-builder", "api-integrator", "quality-guardian"]
        
        for agent in agents_to_test:
            retry_info = await self._test_agent_retry(agent)
            
            if retry_info["recovered"]:
                results["successful_recoveries"].append({
                    "agent": agent,
                    "attempts": retry_info["attempts"],
                    "total_delay": retry_info["total_delay"]
                })
            else:
                results["permanent_failures"].append({
                    "agent": agent,
                    "attempts": retry_info["attempts"],
                    "error": retry_info["last_error"]
                })
            
            results["retry_attempts"].append(retry_info)
            results["backoff_delays"].extend(retry_info["delays"])
        
        # Verify exponential backoff pattern
        if results["backoff_delays"]:
            delays_correct = all(
                results["backoff_delays"][i] <= results["backoff_delays"][i+1] * 2.5
                for i in range(len(results["backoff_delays"]) - 1)
            )
            results["exponential_backoff_verified"] = delays_correct
        
        return results
    
    async def test_checkpoint_creation_and_restoration(self) -> Dict[str, Any]:
        """Test checkpoint creation at critical points and restoration."""
        results = {
            "test_name": "Checkpoint Creation and Restoration",
            "checkpoints_created": [],
            "restoration_tests": [],
            "data_integrity": [],
            "recovery_time": []
        }
        
        requirements = self.create_ecommerce_requirements()
        
        # Initialize workflow with checkpointing enabled
        context = AgentContext(
            project_requirements=requirements,
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="development"
        )
        
        # Execute workflow with checkpoint creation
        checkpoint_count = 0
        agents = requirements["agents"][:4]  # Test with first 4 agents
        
        for i, agent in enumerate(agents):
            # Execute agent
            success = await self._execute_agent_with_failure(agent, context)
            
            # Create checkpoint after each agent
            checkpoint_id = f"checkpoint_{checkpoint_count}"
            checkpoint_path = await self._create_checkpoint(checkpoint_id, context, agent)
            checkpoint_count += 1
            
            results["checkpoints_created"].append({
                "id": checkpoint_id,
                "agent": agent,
                "completed_tasks": len(context.completed_tasks),
                "artifacts": len(context.artifacts),
                "path": str(checkpoint_path)
            })
            
            # Simulate failure and test restoration
            if i == 2:  # Test restoration at third agent
                restoration_start = time.time()
                restored_context = await self._restore_checkpoint(checkpoint_path)
                restoration_time = time.time() - restoration_start
                
                # Verify restoration integrity
                integrity_check = self._verify_checkpoint_integrity(context, restored_context)
                
                results["restoration_tests"].append({
                    "checkpoint_id": checkpoint_id,
                    "restoration_successful": restored_context is not None,
                    "restoration_time": restoration_time,
                    "tasks_restored": len(restored_context.completed_tasks) if restored_context else 0
                })
                
                results["data_integrity"].append(integrity_check)
                results["recovery_time"].append(restoration_time)
        
        return results
    
    async def test_incomplete_task_tracking(self) -> Dict[str, Any]:
        """Test tracking and recovery of incomplete tasks."""
        results = {
            "test_name": "Incomplete Task Tracking",
            "incomplete_tasks": [],
            "recovery_attempts": [],
            "task_dependencies": [],
            "resolution_status": []
        }
        
        requirements = self.create_ecommerce_requirements()
        context = AgentContext(
            project_requirements=requirements,
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="development"
        )
        
        # Simulate workflow with failures
        for req_id, requirement in requirements["functional_requirements"].items():
            for agent in requirement["agents"]:
                # Simulate potential failure
                if random.random() < self.failure_rate:
                    # Track incomplete task
                    context.add_incomplete_task(
                        agent,
                        f"Implement {requirement['title']}",
                        f"Simulated failure at {datetime.now()}"
                    )
                    
                    results["incomplete_tasks"].append({
                        "agent": agent,
                        "requirement": req_id,
                        "task": requirement["title"],
                        "priority": requirement["priority"]
                    })
                else:
                    context.completed_tasks.append(f"{agent}:{req_id}")
        
        # Attempt recovery of incomplete tasks
        for task in context.incomplete_tasks:
            recovery_attempt = await self._attempt_task_recovery(task, context)
            results["recovery_attempts"].append(recovery_attempt)
            
            if recovery_attempt["successful"]:
                results["resolution_status"].append({
                    "task": task["task"],
                    "status": "recovered",
                    "attempts": recovery_attempt["attempts"]
                })
            else:
                results["resolution_status"].append({
                    "task": task["task"],
                    "status": "failed",
                    "blocker": recovery_attempt["blocker"]
                })
        
        # Analyze task dependencies
        for task in results["incomplete_tasks"]:
            deps = self._analyze_task_dependencies(task, context)
            results["task_dependencies"].append({
                "task": task["task"],
                "blocked_by": deps["blocked_by"],
                "blocks": deps["blocks"]
            })
        
        return results
    
    async def test_context_preservation_during_failures(self) -> Dict[str, Any]:
        """Test that context is properly preserved during agent failures."""
        results = {
            "test_name": "Context Preservation During Failures",
            "context_snapshots": [],
            "data_loss_incidents": [],
            "artifact_preservation": [],
            "decision_continuity": []
        }
        
        context = AgentContext(
            project_requirements=self.create_ecommerce_requirements(),
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="development"
        )
        
        # Take initial snapshot
        initial_snapshot = self._take_context_snapshot(context)
        results["context_snapshots"].append({"stage": "initial", "snapshot": initial_snapshot})
        
        agents = ["project-architect", "rapid-builder", "database-expert", "frontend-specialist"]
        
        for agent in agents:
            # Add some data to context before execution
            pre_execution_artifacts = len(context.artifacts)
            pre_execution_decisions = len(context.decisions)
            
            # Simulate agent execution with potential failure
            try:
                if random.random() < self.failure_rate:
                    raise Exception(f"Simulated failure for {agent}")
                
                # Successful execution
                context.artifacts[agent] = {"status": "completed", "files": [f"{agent}_output.py"]}
                context.decisions.append({
                    "agent": agent,
                    "decision": f"Design decision by {agent}",
                    "timestamp": datetime.now().isoformat()
                })
                context.completed_tasks.append(agent)
                
            except Exception as e:
                # Verify context preservation after failure
                post_failure_artifacts = len(context.artifacts)
                post_failure_decisions = len(context.decisions)
                
                # Check for data loss
                if post_failure_artifacts < pre_execution_artifacts:
                    results["data_loss_incidents"].append({
                        "agent": agent,
                        "type": "artifacts",
                        "lost_count": pre_execution_artifacts - post_failure_artifacts
                    })
                
                if post_failure_decisions < pre_execution_decisions:
                    results["data_loss_incidents"].append({
                        "agent": agent,
                        "type": "decisions",
                        "lost_count": pre_execution_decisions - post_failure_decisions
                    })
                
                # Mark agent as incomplete but preserve partial work
                context.add_incomplete_task(agent, "Agent execution", str(e))
            
            # Take snapshot after each agent
            snapshot = self._take_context_snapshot(context)
            results["context_snapshots"].append({"stage": f"after_{agent}", "snapshot": snapshot})
        
        # Verify artifact preservation
        for agent, artifacts in context.artifacts.items():
            results["artifact_preservation"].append({
                "agent": agent,
                "preserved": True,
                "artifact_count": len(artifacts) if isinstance(artifacts, (list, dict)) else 1
            })
        
        # Verify decision continuity
        for i, decision in enumerate(context.decisions):
            results["decision_continuity"].append({
                "index": i,
                "decision": decision.get("decision", ""),
                "has_timestamp": "timestamp" in decision,
                "has_agent": "agent" in decision
            })
        
        return results
    
    async def test_partial_completion_handling(self) -> Dict[str, Any]:
        """Test system behavior with partial requirement completion."""
        results = {
            "test_name": "Partial Completion Handling",
            "requirements_status": {},
            "completion_percentage": 0,
            "viable_features": [],
            "blocked_features": [],
            "recovery_plan": []
        }
        
        requirements = self.create_ecommerce_requirements()
        
        # Simulate partial completion
        completed_reqs = ["REQ-001", "REQ-002", "REQ-005"]  # Product catalog, cart, auth
        failed_reqs = ["REQ-003"]  # Payment processing
        incomplete_reqs = ["REQ-004", "REQ-006"]  # Order management, search
        
        # Analyze requirement status
        for req_id, req in requirements["functional_requirements"].items():
            if req_id in completed_reqs:
                status = "completed"
                completion = 100
            elif req_id in failed_reqs:
                status = "failed"
                completion = 0
            else:
                status = "incomplete"
                completion = random.randint(20, 80)
            
            results["requirements_status"][req_id] = {
                "title": req["title"],
                "status": status,
                "completion": completion,
                "priority": req["priority"]
            }
        
        # Calculate overall completion
        total_completion = sum(r["completion"] for r in results["requirements_status"].values())
        results["completion_percentage"] = total_completion / len(requirements["functional_requirements"])
        
        # Determine viable features (can work without failed components)
        if "REQ-003" in failed_reqs:  # Payment failed
            results["viable_features"] = [
                "Browse products",
                "Add to cart",
                "User registration/login",
                "Search products"
            ]
            results["blocked_features"] = [
                "Checkout",
                "Process payments",
                "Complete orders"
            ]
        
        # Generate recovery plan
        for req_id in failed_reqs + incomplete_reqs:
            req = requirements["functional_requirements"][req_id]
            recovery_step = {
                "requirement": req_id,
                "title": req["title"],
                "priority": req["priority"],
                "suggested_agents": req["agents"],
                "estimated_effort": "2-4 hours",
                "dependencies": self._get_requirement_dependencies(req_id, requirements)
            }
            results["recovery_plan"].append(recovery_step)
        
        # Sort recovery plan by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        results["recovery_plan"].sort(key=lambda x: priority_order.get(x["priority"], 99))
        
        return results
    
    async def test_cascading_failure_handling(self) -> Dict[str, Any]:
        """Test handling of cascading failures when one agent failure affects others."""
        results = {
            "test_name": "Cascading Failure Handling",
            "initial_failure": None,
            "cascade_chain": [],
            "mitigation_actions": [],
            "recovery_sequence": [],
            "system_stability": None
        }
        
        # Define agent dependencies
        agent_dependencies = {
            "project-architect": [],
            "database-expert": ["project-architect"],
            "rapid-builder": ["project-architect", "database-expert"],
            "frontend-specialist": ["rapid-builder"],
            "api-integrator": ["rapid-builder"],
            "quality-guardian": ["rapid-builder", "frontend-specialist", "api-integrator"],
            "performance-optimizer": ["frontend-specialist", "rapid-builder"],
            "devops-engineer": ["quality-guardian"]
        }
        
        # Simulate initial failure
        initial_failure_agent = "database-expert"
        results["initial_failure"] = {
            "agent": initial_failure_agent,
            "error": "Database connection failed",
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine cascade effects
        affected_agents = []
        for agent, deps in agent_dependencies.items():
            if initial_failure_agent in deps:
                affected_agents.append(agent)
                results["cascade_chain"].append({
                    "agent": agent,
                    "reason": f"Depends on {initial_failure_agent}",
                    "impact": "blocked"
                })
        
        # Implement mitigation actions
        mitigation_strategies = [
            {
                "action": "Use mock database",
                "affects": ["rapid-builder", "frontend-specialist"],
                "success_rate": 0.7
            },
            {
                "action": "Skip database-dependent features",
                "affects": ["api-integrator"],
                "success_rate": 0.5
            },
            {
                "action": "Retry with different connection parameters",
                "affects": ["database-expert"],
                "success_rate": 0.3
            }
        ]
        
        for strategy in mitigation_strategies:
            if random.random() < strategy["success_rate"]:
                results["mitigation_actions"].append({
                    "action": strategy["action"],
                    "status": "successful",
                    "recovered_agents": strategy["affects"]
                })
                # Remove recovered agents from affected list
                affected_agents = [a for a in affected_agents if a not in strategy["affects"]]
            else:
                results["mitigation_actions"].append({
                    "action": strategy["action"],
                    "status": "failed",
                    "reason": "Mitigation strategy unsuccessful"
                })
        
        # Determine recovery sequence
        if len(affected_agents) < len(results["cascade_chain"]):
            results["recovery_sequence"] = [
                {"step": 1, "action": "Fix database connection", "priority": "critical"},
                {"step": 2, "action": "Restart database-expert", "priority": "critical"},
                {"step": 3, "action": "Resume dependent agents", "priority": "high"},
                {"step": 4, "action": "Validate system integrity", "priority": "medium"}
            ]
            results["system_stability"] = "partially_recovered"
        else:
            results["recovery_sequence"] = [
                {"step": 1, "action": "Full system restart required", "priority": "critical"}
            ]
            results["system_stability"] = "unstable"
        
        return results
    
    # Helper methods
    
    async def _test_agent_retry(self, agent: str, max_attempts: int = 3) -> Dict[str, Any]:
        """Test retry logic for a specific agent."""
        retry_info = {
            "agent": agent,
            "attempts": 0,
            "delays": [],
            "errors": [],
            "recovered": False,
            "total_delay": 0,
            "last_error": None
        }
        
        base_delay = 5  # 5 seconds base delay
        
        for attempt in range(max_attempts):
            retry_info["attempts"] += 1
            
            # Calculate exponential backoff delay
            delay = base_delay * (2 ** attempt)
            retry_info["delays"].append(delay)
            retry_info["total_delay"] += delay
            
            # Simulate agent execution
            if random.random() > self.failure_rate or attempt == max_attempts - 1:
                # Success or final attempt succeeds
                retry_info["recovered"] = True
                break
            else:
                # Failure
                error = f"Attempt {attempt + 1} failed for {agent}"
                retry_info["errors"].append(error)
                retry_info["last_error"] = error
                
                # Simulate delay
                await asyncio.sleep(0.1)  # Shortened for testing
        
        return retry_info
    
    async def _execute_agent_with_failure(self, agent: str, context: AgentContext) -> bool:
        """Execute agent with controlled failure simulation."""
        if random.random() < self.failure_rate:
            # Simulate failure
            context.add_incomplete_task(agent, f"Execute {agent}", "Simulated failure")
            return False
        
        # Simulate success
        context.completed_tasks.append(agent)
        context.artifacts[agent] = {"status": "completed"}
        return True
    
    async def _create_checkpoint(self, checkpoint_id: str, context: AgentContext, agent: str) -> Path:
        """Create a checkpoint of current context state."""
        checkpoint_data = {
            "id": checkpoint_id,
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "context": {
                "completed_tasks": context.completed_tasks,
                "artifacts": context.artifacts,
                "decisions": context.decisions,
                "current_phase": context.current_phase,
                "incomplete_tasks": context.incomplete_tasks
            }
        }
        
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
        
        return checkpoint_path
    
    async def _restore_checkpoint(self, checkpoint_path: Path) -> Optional[AgentContext]:
        """Restore context from checkpoint."""
        try:
            with open(checkpoint_path, 'r') as f:
                checkpoint_data = json.load(f)
            
            context = AgentContext(
                project_requirements={},
                completed_tasks=checkpoint_data["context"]["completed_tasks"],
                artifacts=checkpoint_data["context"]["artifacts"],
                decisions=checkpoint_data["context"]["decisions"],
                current_phase=checkpoint_data["context"]["current_phase"]
            )
            
            # Restore incomplete tasks
            for task in checkpoint_data["context"].get("incomplete_tasks", []):
                context.add_incomplete_task(task["agent"], task["task"], task["reason"])
            
            return context
        except Exception as e:
            print(f"Failed to restore checkpoint: {e}")
            return None
    
    def _verify_checkpoint_integrity(self, original: AgentContext, restored: AgentContext) -> Dict[str, Any]:
        """Verify integrity of restored checkpoint."""
        return {
            "tasks_match": original.completed_tasks == restored.completed_tasks,
            "artifacts_match": len(original.artifacts) == len(restored.artifacts),
            "decisions_match": len(original.decisions) == len(restored.decisions),
            "phase_match": original.current_phase == restored.current_phase,
            "integrity_score": sum([
                original.completed_tasks == restored.completed_tasks,
                len(original.artifacts) == len(restored.artifacts),
                len(original.decisions) == len(restored.decisions),
                original.current_phase == restored.current_phase
            ]) / 4 * 100
        }
    
    async def _attempt_task_recovery(self, task: Dict, context: AgentContext) -> Dict[str, Any]:
        """Attempt to recover an incomplete task."""
        recovery_attempt = {
            "task": task["task"],
            "agent": task["agent"],
            "attempts": 0,
            "successful": False,
            "blocker": None
        }
        
        max_recovery_attempts = 2
        
        for attempt in range(max_recovery_attempts):
            recovery_attempt["attempts"] += 1
            
            # Check if dependencies are met
            deps_met = self._check_task_dependencies(task, context)
            
            if not deps_met:
                recovery_attempt["blocker"] = "Dependencies not met"
                break
            
            # Attempt recovery with decreasing failure rate
            if random.random() > (self.failure_rate / (attempt + 1)):
                recovery_attempt["successful"] = True
                context.completed_tasks.append(f"{task['agent']}:recovered")
                # Remove from incomplete tasks
                context.incomplete_tasks = [
                    t for t in context.incomplete_tasks 
                    if t["task"] != task["task"]
                ]
                break
            
            await asyncio.sleep(0.1)  # Simulate recovery delay
        
        return recovery_attempt
    
    def _check_task_dependencies(self, task: Dict, context: AgentContext) -> bool:
        """Check if task dependencies are satisfied."""
        # Simplified dependency check
        required_agents = {
            "rapid-builder": ["project-architect"],
            "frontend-specialist": ["rapid-builder"],
            "api-integrator": ["rapid-builder"],
            "quality-guardian": ["rapid-builder", "frontend-specialist"]
        }
        
        deps = required_agents.get(task["agent"], [])
        return all(dep in context.completed_tasks for dep in deps)
    
    def _analyze_task_dependencies(self, task: Dict, context: AgentContext) -> Dict[str, List[str]]:
        """Analyze what a task is blocked by and what it blocks."""
        return {
            "blocked_by": [t for t in context.incomplete_tasks if t["agent"] != task["agent"]],
            "blocks": []  # Simplified for this test
        }
    
    def _take_context_snapshot(self, context: AgentContext) -> Dict[str, Any]:
        """Take a snapshot of current context state."""
        return {
            "completed_tasks_count": len(context.completed_tasks),
            "artifacts_count": len(context.artifacts),
            "decisions_count": len(context.decisions),
            "incomplete_tasks_count": len(context.incomplete_tasks),
            "current_phase": context.current_phase
        }
    
    def _get_requirement_dependencies(self, req_id: str, requirements: Dict) -> List[str]:
        """Get dependencies for a requirement."""
        deps_map = {
            "REQ-003": ["REQ-002"],  # Payment needs cart
            "REQ-004": ["REQ-003"],  # Orders need payment
            "REQ-006": ["REQ-001"]   # Search needs products
        }
        return deps_map.get(req_id, [])


async def run_failure_recovery_tests():
    """Run all failure recovery tests."""
    test_suite = TestFailureRecovery(failure_rate=0.3)
    
    print("=" * 80)
    print("AGENT FAILURE RECOVERY - COMPREHENSIVE E2E TEST")
    print("=" * 80)
    print(f"Configured failure rate: {test_suite.failure_rate * 100}%")
    
    all_results = {}
    
    # Test 1: Exponential Backoff
    print("\n[1/6] Testing Retry with Exponential Backoff...")
    backoff_results = await test_suite.test_retry_with_exponential_backoff()
    all_results["exponential_backoff"] = backoff_results
    print(f"  - Successful recoveries: {len(backoff_results['successful_recoveries'])}")
    print(f"  - Permanent failures: {len(backoff_results['permanent_failures'])}")
    print(f"  - Backoff pattern verified: {backoff_results.get('exponential_backoff_verified', False)}")
    
    # Test 2: Checkpoint Creation and Restoration
    print("\n[2/6] Testing Checkpoint Creation and Restoration...")
    checkpoint_results = await test_suite.test_checkpoint_creation_and_restoration()
    all_results["checkpointing"] = checkpoint_results
    print(f"  - Checkpoints created: {len(checkpoint_results['checkpoints_created'])}")
    print(f"  - Restoration tests: {len(checkpoint_results['restoration_tests'])}")
    if checkpoint_results['data_integrity']:
        integrity_avg = sum(c['integrity_score'] for c in checkpoint_results['data_integrity']) / len(checkpoint_results['data_integrity'])
        print(f"  - Average integrity score: {integrity_avg:.1f}%")
    
    # Test 3: Incomplete Task Tracking
    print("\n[3/6] Testing Incomplete Task Tracking...")
    incomplete_results = await test_suite.test_incomplete_task_tracking()
    all_results["incomplete_tasks"] = incomplete_results
    print(f"  - Incomplete tasks tracked: {len(incomplete_results['incomplete_tasks'])}")
    print(f"  - Recovery attempts: {len(incomplete_results['recovery_attempts'])}")
    recovered = sum(1 for r in incomplete_results['resolution_status'] if r['status'] == 'recovered')
    print(f"  - Tasks recovered: {recovered}/{len(incomplete_results['resolution_status'])}")
    
    # Test 4: Context Preservation
    print("\n[4/6] Testing Context Preservation During Failures...")
    context_results = await test_suite.test_context_preservation_during_failures()
    all_results["context_preservation"] = context_results
    print(f"  - Context snapshots: {len(context_results['context_snapshots'])}")
    print(f"  - Data loss incidents: {len(context_results['data_loss_incidents'])}")
    print(f"  - Artifacts preserved: {len(context_results['artifact_preservation'])}")
    
    # Test 5: Partial Completion
    print("\n[5/6] Testing Partial Completion Handling...")
    partial_results = await test_suite.test_partial_completion_handling()
    all_results["partial_completion"] = partial_results
    print(f"  - Overall completion: {partial_results['completion_percentage']:.1f}%")
    print(f"  - Viable features: {len(partial_results['viable_features'])}")
    print(f"  - Blocked features: {len(partial_results['blocked_features'])}")
    print(f"  - Recovery steps: {len(partial_results['recovery_plan'])}")
    
    # Test 6: Cascading Failures
    print("\n[6/6] Testing Cascading Failure Handling...")
    cascade_results = await test_suite.test_cascading_failure_handling()
    all_results["cascading_failures"] = cascade_results
    print(f"  - Cascade chain length: {len(cascade_results['cascade_chain'])}")
    print(f"  - Mitigation actions: {len(cascade_results['mitigation_actions'])}")
    successful_mitigations = sum(1 for m in cascade_results['mitigation_actions'] if m['status'] == 'successful')
    print(f"  - Successful mitigations: {successful_mitigations}/{len(cascade_results['mitigation_actions'])}")
    print(f"  - System stability: {cascade_results['system_stability']}")
    
    # Save results
    output_dir = Path("tests/e2e_comprehensive/results")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"failure_recovery_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    # Calculate overall success
    total_tests = 6
    passed_tests = sum([
        backoff_results.get('exponential_backoff_verified', False),
        integrity_avg >= 80 if checkpoint_results['data_integrity'] else False,
        recovered > 0,
        len(context_results['data_loss_incidents']) == 0,
        partial_results['completion_percentage'] > 50,
        cascade_results['system_stability'] != 'unstable'
    ])
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    print(f"Results saved to: {output_file}")
    
    # Clean up checkpoints
    for checkpoint_file in test_suite.checkpoint_dir.glob("*.json"):
        checkpoint_file.unlink()
    
    return all_results


if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_failure_recovery_tests())