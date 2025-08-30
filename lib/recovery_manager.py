#!/usr/bin/env python3
"""
Recovery Manager
Handles agent failures with exponential backoff, context preservation, alternative agents, and checkpoints
"""

import json
import asyncio
import pickle
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import hashlib


class RecoveryStrategy(Enum):
    """Recovery strategies for failed agents"""
    RETRY_SAME = "retry_same"  # Retry the same agent
    ALTERNATIVE_AGENT = "alternative_agent"  # Try an alternative agent
    PARTIAL_COMPLETION = "partial_completion"  # Accept partial completion
    MANUAL_INTERVENTION = "manual_intervention"  # Request manual help
    SKIP_TASK = "skip_task"  # Skip the failed task


@dataclass
class RecoveryContext:
    """Context preserved across recovery attempts"""
    agent_name: str
    task_description: str
    attempt_number: int = 0
    max_attempts: int = 3
    error_history: List[Dict] = field(default_factory=list)
    partial_results: Dict = field(default_factory=dict)
    checkpoint_id: Optional[str] = None
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY_SAME
    alternative_agents: List[str] = field(default_factory=list)
    manual_intervention_requested: bool = False
    
    def add_error(self, error: str, timestamp: datetime = None):
        """Add error to history"""
        self.error_history.append({
            "attempt": self.attempt_number,
            "error": error,
            "timestamp": (timestamp or datetime.now()).isoformat()
        })
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "agent_name": self.agent_name,
            "task_description": self.task_description,
            "attempt_number": self.attempt_number,
            "max_attempts": self.max_attempts,
            "error_history": self.error_history,
            "partial_results": self.partial_results,
            "checkpoint_id": self.checkpoint_id,
            "recovery_strategy": self.recovery_strategy.value,
            "alternative_agents": self.alternative_agents,
            "manual_intervention_requested": self.manual_intervention_requested
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RecoveryContext':
        """Create from dictionary"""
        context = cls(
            agent_name=data["agent_name"],
            task_description=data["task_description"],
            attempt_number=data.get("attempt_number", 0),
            max_attempts=data.get("max_attempts", 3),
            error_history=data.get("error_history", []),
            partial_results=data.get("partial_results", {}),
            checkpoint_id=data.get("checkpoint_id"),
            recovery_strategy=RecoveryStrategy(data.get("recovery_strategy", "retry_same")),
            alternative_agents=data.get("alternative_agents", []),
            manual_intervention_requested=data.get("manual_intervention_requested", False)
        )
        return context


@dataclass
class Checkpoint:
    """Checkpoint for state preservation"""
    id: str
    timestamp: datetime
    agent_name: str
    context: Dict
    artifacts: Dict
    completed_tasks: List[str]
    partial_results: Dict
    metadata: Dict = field(default_factory=dict)
    
    def save(self, checkpoint_dir: Path):
        """Save checkpoint to disk"""
        checkpoint_file = checkpoint_dir / f"checkpoint_{self.id}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump({
                "id": self.id,
                "timestamp": self.timestamp.isoformat(),
                "agent_name": self.agent_name,
                "context": self.context,
                "artifacts": self.artifacts,
                "completed_tasks": self.completed_tasks,
                "partial_results": self.partial_results,
                "metadata": self.metadata
            }, f, indent=2)
    
    @classmethod
    def load(cls, checkpoint_file: Path) -> 'Checkpoint':
        """Load checkpoint from disk"""
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
        
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            agent_name=data["agent_name"],
            context=data["context"],
            artifacts=data["artifacts"],
            completed_tasks=data["completed_tasks"],
            partial_results=data["partial_results"],
            metadata=data.get("metadata", {})
        )


class RecoveryManager:
    """
    Manages recovery from agent failures with various strategies
    """
    
    def __init__(self, checkpoint_dir: str = "checkpoints/recovery"):
        """Initialize recovery manager"""
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Recovery contexts for active recoveries
        self.active_recoveries: Dict[str, RecoveryContext] = {}
        
        # Alternative agent mappings
        self.agent_alternatives = {
            "rapid-builder": ["code-migrator", "meta-agent"],
            "frontend-specialist": ["rapid-builder", "meta-agent"],
            "ai-specialist": ["api-integrator", "rapid-builder"],
            "database-expert": ["rapid-builder", "code-migrator"],
            "api-integrator": ["rapid-builder", "ai-specialist"],
            "quality-guardian": ["debug-specialist", "meta-agent"],
            "devops-engineer": ["meta-agent", "rapid-builder"],
            "documentation-writer": ["meta-agent"],
            "performance-optimizer": ["debug-specialist", "quality-guardian"],
            "code-migrator": ["rapid-builder", "meta-agent"],
            "debug-specialist": ["quality-guardian", "meta-agent"],
            "requirements-analyst": ["project-orchestrator"],
            "project-architect": ["meta-agent"],
            "project-orchestrator": ["meta-agent"],
            "meta-agent": []  # No alternatives for meta-agent
        }
        
        # Exponential backoff configuration
        self.base_delay = 5  # Base delay in seconds
        self.max_delay = 300  # Maximum delay (5 minutes)
        self.backoff_multiplier = 2  # Exponential multiplier
        
        # Manual intervention queue
        self.manual_intervention_queue: List[RecoveryContext] = []
    
    async def recover_with_retry(self, 
                                agent_name: str,
                                agent_executor: Callable,
                                context: Any,
                                task_description: str = "",
                                max_attempts: int = 3,
                                preserve_context: bool = True) -> Tuple[bool, Any, Any]:
        """
        Attempt to recover from agent failure with exponential backoff
        
        Args:
            agent_name: Name of the failed agent
            agent_executor: Function to execute the agent
            context: Agent execution context
            task_description: Description of the task
            max_attempts: Maximum retry attempts
            preserve_context: Whether to preserve context between attempts
            
        Returns:
            Tuple of (success, result, updated_context)
        """
        recovery_id = self._generate_recovery_id(agent_name, task_description)
        
        # Create or retrieve recovery context
        if recovery_id in self.active_recoveries:
            recovery_context = self.active_recoveries[recovery_id]
        else:
            recovery_context = RecoveryContext(
                agent_name=agent_name,
                task_description=task_description,
                max_attempts=max_attempts,
                alternative_agents=self.agent_alternatives.get(agent_name, [])
            )
            self.active_recoveries[recovery_id] = recovery_context
        
        # Main recovery loop
        while recovery_context.attempt_number < recovery_context.max_attempts:
            recovery_context.attempt_number += 1
            
            # Calculate delay with exponential backoff
            if recovery_context.attempt_number > 1:
                delay = min(
                    self.base_delay * (self.backoff_multiplier ** (recovery_context.attempt_number - 2)),
                    self.max_delay
                )
                print(f"\n⏳ Waiting {delay}s before retry attempt {recovery_context.attempt_number}/{recovery_context.max_attempts}")
                await asyncio.sleep(delay)
            
            # Create checkpoint before attempt
            checkpoint = await self._create_checkpoint(agent_name, context, recovery_context)
            recovery_context.checkpoint_id = checkpoint.id
            
            try:
                # Determine which agent to use based on strategy
                executing_agent = agent_name
                if recovery_context.recovery_strategy == RecoveryStrategy.ALTERNATIVE_AGENT:
                    executing_agent = self._select_alternative_agent(recovery_context)
                    if not executing_agent:
                        executing_agent = agent_name  # Fallback to original
                
                print(f"\n🔄 Recovery attempt {recovery_context.attempt_number} for {executing_agent}")
                
                # Prepare context with recovery information
                if preserve_context:
                    enhanced_context = self._enhance_context_for_recovery(
                        context, recovery_context
                    )
                else:
                    enhanced_context = context
                
                # Execute agent
                success, result, updated_context = await agent_executor(
                    executing_agent, enhanced_context
                )
                
                if success:
                    print(f"✅ Recovery successful for {executing_agent}")
                    # Clean up recovery context
                    del self.active_recoveries[recovery_id]
                    return True, result, updated_context
                else:
                    # Record error
                    recovery_context.add_error(str(result))
                    
                    # Store partial results if any
                    if hasattr(updated_context, 'artifacts'):
                        recovery_context.partial_results.update(
                            updated_context.artifacts
                        )
                    
                    # Determine next strategy
                    recovery_context.recovery_strategy = self._determine_recovery_strategy(
                        recovery_context
                    )
                    
            except Exception as e:
                recovery_context.add_error(str(e))
                print(f"❌ Recovery attempt {recovery_context.attempt_number} failed: {e}")
        
        # All attempts exhausted
        return await self._handle_recovery_failure(recovery_context, context)
    
    async def recover_from_checkpoint(self, checkpoint_id: str, 
                                     agent_executor: Callable) -> Tuple[bool, Any, Any]:
        """
        Recover from a saved checkpoint
        
        Args:
            checkpoint_id: ID of the checkpoint to restore
            agent_executor: Function to execute the agent
            
        Returns:
            Tuple of (success, result, context)
        """
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            return False, f"Checkpoint {checkpoint_id} not found", None
        
        try:
            checkpoint = Checkpoint.load(checkpoint_file)
            
            # Restore context
            from agent_runtime import AgentContext
            context = AgentContext(
                project_requirements=checkpoint.context.get("project_requirements", {}),
                completed_tasks=checkpoint.completed_tasks,
                artifacts=checkpoint.artifacts,
                decisions=checkpoint.context.get("decisions", []),
                current_phase=checkpoint.context.get("current_phase", "recovery")
            )
            
            # Add recovery metadata
            context.artifacts["recovered_from_checkpoint"] = checkpoint_id
            context.artifacts["recovery_timestamp"] = datetime.now().isoformat()
            
            print(f"\n📥 Restored from checkpoint {checkpoint_id}")
            print(f"   Agent: {checkpoint.agent_name}")
            print(f"   Completed tasks: {len(checkpoint.completed_tasks)}")
            print(f"   Artifacts: {len(checkpoint.artifacts)}")
            
            # Resume execution
            return await agent_executor(checkpoint.agent_name, context)
            
        except Exception as e:
            return False, f"Failed to restore checkpoint: {e}", None
    
    def request_manual_intervention(self, recovery_context: RecoveryContext) -> str:
        """
        Request manual intervention for unrecoverable failures
        
        Returns:
            Intervention request ID
        """
        recovery_context.manual_intervention_requested = True
        self.manual_intervention_queue.append(recovery_context)
        
        intervention_id = f"intervention_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n⚠️  Manual Intervention Required")
        print(f"   ID: {intervention_id}")
        print(f"   Agent: {recovery_context.agent_name}")
        print(f"   Task: {recovery_context.task_description}")
        print(f"   Attempts: {recovery_context.attempt_number}")
        print(f"   Errors: {len(recovery_context.error_history)}")
        
        # Save intervention request
        intervention_file = self.checkpoint_dir / f"{intervention_id}.json"
        with open(intervention_file, 'w') as f:
            json.dump(recovery_context.to_dict(), f, indent=2)
        
        return intervention_id
    
    def get_manual_interventions(self) -> List[Dict]:
        """Get pending manual interventions"""
        return [ctx.to_dict() for ctx in self.manual_intervention_queue]
    
    def resolve_manual_intervention(self, intervention_id: str, 
                                  resolution: Dict) -> bool:
        """
        Resolve a manual intervention
        
        Args:
            intervention_id: ID of the intervention
            resolution: Resolution details (action, notes, etc.)
            
        Returns:
            Success status
        """
        intervention_file = self.checkpoint_dir / f"{intervention_id}.json"
        
        if not intervention_file.exists():
            return False
        
        # Load and update intervention
        with open(intervention_file, 'r') as f:
            data = json.load(f)
        
        data["resolution"] = resolution
        data["resolved_at"] = datetime.now().isoformat()
        
        # Save resolution
        with open(intervention_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Remove from queue
        self.manual_intervention_queue = [
            ctx for ctx in self.manual_intervention_queue
            if f"intervention_{ctx.task_description}" != intervention_id
        ]
        
        return True
    
    async def _create_checkpoint(self, agent_name: str, context: Any,
                                recovery_context: RecoveryContext) -> Checkpoint:
        """Create a checkpoint for recovery"""
        checkpoint_id = f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Extract context data
        context_dict = {}
        if hasattr(context, 'to_dict'):
            context_dict = context.to_dict()
        elif hasattr(context, '__dict__'):
            context_dict = {k: v for k, v in context.__dict__.items() 
                          if not k.startswith('_')}
        
        checkpoint = Checkpoint(
            id=checkpoint_id,
            timestamp=datetime.now(),
            agent_name=agent_name,
            context=context_dict,
            artifacts=getattr(context, 'artifacts', {}),
            completed_tasks=getattr(context, 'completed_tasks', []),
            partial_results=recovery_context.partial_results,
            metadata={
                "attempt_number": recovery_context.attempt_number,
                "recovery_strategy": recovery_context.recovery_strategy.value,
                "error_count": len(recovery_context.error_history)
            }
        )
        
        checkpoint.save(self.checkpoint_dir)
        return checkpoint
    
    def _enhance_context_for_recovery(self, context: Any, 
                                     recovery_context: RecoveryContext) -> Any:
        """Enhance context with recovery information"""
        # Add recovery information to context
        if hasattr(context, 'artifacts'):
            context.artifacts["recovery_info"] = {
                "attempt": recovery_context.attempt_number,
                "previous_errors": recovery_context.error_history,
                "partial_results": recovery_context.partial_results,
                "strategy": recovery_context.recovery_strategy.value
            }
            
            # Add suggestions based on previous errors
            suggestions = self._generate_recovery_suggestions(recovery_context)
            if suggestions:
                context.artifacts["recovery_suggestions"] = suggestions
        
        return context
    
    def _determine_recovery_strategy(self, recovery_context: RecoveryContext) -> RecoveryStrategy:
        """Determine the best recovery strategy based on failure patterns"""
        
        # Analyze error patterns
        error_types = [self._categorize_error(e["error"]) for e in recovery_context.error_history]
        
        # If same error keeps happening, try alternative agent
        if len(set(error_types)) == 1 and recovery_context.attempt_number >= 2:
            if recovery_context.alternative_agents:
                return RecoveryStrategy.ALTERNATIVE_AGENT
        
        # If we have partial results and near max attempts, accept partial
        if recovery_context.partial_results and recovery_context.attempt_number >= recovery_context.max_attempts - 1:
            return RecoveryStrategy.PARTIAL_COMPLETION
        
        # If no alternatives and multiple failures, request manual intervention
        if recovery_context.attempt_number >= recovery_context.max_attempts - 1:
            if not recovery_context.alternative_agents:
                return RecoveryStrategy.MANUAL_INTERVENTION
        
        # Default to retry same agent
        return RecoveryStrategy.RETRY_SAME
    
    def _select_alternative_agent(self, recovery_context: RecoveryContext) -> Optional[str]:
        """Select an alternative agent based on availability and past performance"""
        if not recovery_context.alternative_agents:
            return None
        
        # Simple selection: pick first alternative not yet tried
        # In production, this could use performance metrics
        for alt_agent in recovery_context.alternative_agents:
            # Check if we've already tried this agent
            tried = any(
                alt_agent in error.get("agent", recovery_context.agent_name)
                for error in recovery_context.error_history
            )
            if not tried:
                return alt_agent
        
        return None
    
    def _generate_recovery_suggestions(self, recovery_context: RecoveryContext) -> List[str]:
        """Generate suggestions based on error history"""
        suggestions = []
        
        # Analyze recent errors
        if recovery_context.error_history:
            last_error = recovery_context.error_history[-1]["error"].lower()
            
            if "rate limit" in last_error:
                suggestions.append("Wait longer between API calls or reduce request frequency")
            elif "timeout" in last_error:
                suggestions.append("Increase timeout duration or break task into smaller parts")
            elif "file not found" in last_error:
                suggestions.append("Verify required files exist or create them first")
            elif "permission" in last_error:
                suggestions.append("Check file permissions and access rights")
            elif "validation" in last_error:
                suggestions.append("Review input validation requirements")
            elif "memory" in last_error:
                suggestions.append("Reduce memory usage or increase available resources")
        
        # Add strategy-specific suggestions
        if recovery_context.recovery_strategy == RecoveryStrategy.ALTERNATIVE_AGENT:
            suggestions.append(f"Using alternative agent due to repeated failures")
        elif recovery_context.recovery_strategy == RecoveryStrategy.PARTIAL_COMPLETION:
            suggestions.append("Accepting partial results to make progress")
        
        return suggestions
    
    async def _handle_recovery_failure(self, recovery_context: RecoveryContext, 
                                      context: Any) -> Tuple[bool, Any, Any]:
        """Handle complete recovery failure"""
        
        if recovery_context.recovery_strategy == RecoveryStrategy.PARTIAL_COMPLETION:
            # Return partial results
            if recovery_context.partial_results:
                print(f"\n⚠️  Accepting partial completion for {recovery_context.agent_name}")
                if hasattr(context, 'artifacts'):
                    context.artifacts.update(recovery_context.partial_results)
                return True, "Partial completion accepted", context
        
        elif recovery_context.recovery_strategy == RecoveryStrategy.MANUAL_INTERVENTION:
            # Request manual intervention
            intervention_id = self.request_manual_intervention(recovery_context)
            return False, f"Manual intervention required: {intervention_id}", context
        
        elif recovery_context.recovery_strategy == RecoveryStrategy.SKIP_TASK:
            # Skip the task
            print(f"\n⏭️  Skipping task for {recovery_context.agent_name}")
            return True, "Task skipped", context
        
        # Default: complete failure
        error_summary = f"Recovery failed after {recovery_context.attempt_number} attempts"
        if recovery_context.error_history:
            error_summary += f". Last error: {recovery_context.error_history[-1]['error']}"
        
        return False, error_summary, context
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error type from message"""
        error_lower = error_message.lower()
        
        if "rate limit" in error_lower:
            return "rate_limit"
        elif "timeout" in error_lower:
            return "timeout"
        elif "connection" in error_lower or "network" in error_lower:
            return "network"
        elif "file not found" in error_lower:
            return "file_not_found"
        elif "permission" in error_lower:
            return "permission"
        elif "validation" in error_lower:
            return "validation"
        elif "memory" in error_lower:
            return "resource"
        else:
            return "unknown"
    
    def _generate_recovery_id(self, agent_name: str, task_description: str) -> str:
        """Generate unique recovery ID"""
        content = f"{agent_name}_{task_description}_{datetime.now().date()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def cleanup_old_checkpoints(self, days: int = 7):
        """Clean up old checkpoints"""
        cutoff = datetime.now() - timedelta(days=days)
        
        for checkpoint_file in self.checkpoint_dir.glob("checkpoint_*.json"):
            try:
                # Load checkpoint to check timestamp
                checkpoint = Checkpoint.load(checkpoint_file)
                if checkpoint.timestamp < cutoff:
                    checkpoint_file.unlink()
            except:
                pass  # Skip corrupted files


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def failing_agent(name: str, context: Any):
        """Simulated failing agent"""
        import random
        if random.random() < 0.7:  # 70% failure rate
            return False, "Simulated failure", context
        return True, "Success!", context
    
    async def test_recovery():
        manager = RecoveryManager()
        
        # Test recovery with retry
        from types import SimpleNamespace
        context = SimpleNamespace(
            artifacts={},
            completed_tasks=[],
            project_requirements={}
        )
        
        success, result, updated_context = await manager.recover_with_retry(
            agent_name="test-agent",
            agent_executor=failing_agent,
            context=context,
            task_description="Test task",
            max_attempts=5
        )
        
        print(f"\n\nFinal result: Success={success}, Result={result}")
    
    # Run test
    asyncio.run(test_recovery())