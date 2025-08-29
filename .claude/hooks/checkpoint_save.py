#!/usr/bin/env python3
"""
Checkpoint Save Hook - Automatic checkpoint creation and recovery

Capabilities:
- Automatic checkpoint creation
- State serialization
- Critical decision points detection
- Incremental saves
- Checkpoint compression
- Recovery point management
"""

import os
import json
import time
import gzip
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import pickle

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.hook_manager import HookContext, HookEvent
from lib.agent_logger import get_logger


@dataclass
class Checkpoint:
    """Checkpoint data structure"""
    id: str
    timestamp: float
    agent_name: str
    phase: str
    context: Dict[str, Any]
    artifacts: Dict[str, Any]
    decisions: List[Dict[str, str]]
    metrics: Dict[str, Any]
    is_critical: bool = False
    parent_id: Optional[str] = None
    description: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Checkpoint':
        """Create from dictionary"""
        return cls(**data)


class CheckpointManager:
    """Manages checkpoint creation, storage, and recovery"""
    
    def __init__(self, checkpoint_dir: Path = Path("checkpoints")):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger()
        self.checkpoints: List[Checkpoint] = []
        self.max_checkpoints = 20
        self.checkpoint_interval = 300  # 5 minutes
        self.last_checkpoint_time = 0
        self.incremental_threshold = 1024 * 1024  # 1MB
        
        # Load existing checkpoints
        self._load_checkpoints()
    
    def should_create_checkpoint(self, context: HookContext) -> bool:
        """Determine if checkpoint should be created"""
        current_time = time.time()
        
        # Check triggers based on event type
        if context.event == HookEvent.AGENT_COMPLETE:
            return True
        
        if context.event == HookEvent.WORKFLOW_ERROR:
            return True
        
        if context.event == HookEvent.MILESTONE_REACHED:
            return True
        
        # Check time interval
        if current_time - self.last_checkpoint_time > self.checkpoint_interval:
            return True
        
        # Check for critical decisions
        if self._is_critical_decision(context):
            return True
        
        return False
    
    def create_checkpoint(self, context: HookContext) -> Optional[Checkpoint]:
        """Create a new checkpoint"""
        try:
            checkpoint_id = self._generate_checkpoint_id(context)
            
            # Extract state from context
            state_data = self._extract_state(context)
            
            # Create checkpoint
            checkpoint = Checkpoint(
                id=checkpoint_id,
                timestamp=time.time(),
                agent_name=context.agent_name or "system",
                phase=context.get("current_phase", "unknown"),
                context=state_data["context"],
                artifacts=state_data["artifacts"],
                decisions=state_data["decisions"],
                metrics=state_data["metrics"],
                is_critical=self._is_critical_decision(context),
                parent_id=self._get_parent_checkpoint_id(),
                description=self._generate_description(context)
            )
            
            # Save checkpoint
            self._save_checkpoint(checkpoint)
            
            # Add to list
            self.checkpoints.append(checkpoint)
            
            # Cleanup old checkpoints
            self._cleanup_old_checkpoints()
            
            self.last_checkpoint_time = time.time()
            
            self.logger.log_reasoning(
                "CheckpointHook",
                f"Created checkpoint {checkpoint_id}: {checkpoint.description}"
            )
            
            return checkpoint
            
        except Exception as e:
            self.logger.log_error(
                "CheckpointHook",
                f"Failed to create checkpoint: {str(e)}"
            )
            return None
    
    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Restore from a checkpoint"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.checkpoint.gz"
        
        if not checkpoint_file.exists():
            # Try uncompressed
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.checkpoint.json"
        
        if not checkpoint_file.exists():
            self.logger.log_error(
                "CheckpointHook",
                f"Checkpoint {checkpoint_id} not found"
            )
            return None
        
        try:
            # Load checkpoint
            if checkpoint_file.suffix == ".gz":
                with gzip.open(checkpoint_file, 'rt') as f:
                    data = json.load(f)
            else:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
            
            checkpoint = Checkpoint.from_dict(data)
            
            self.logger.log_reasoning(
                "CheckpointHook",
                f"Restored checkpoint {checkpoint_id}: {checkpoint.description}"
            )
            
            # Return state for restoration
            return {
                "checkpoint": checkpoint,
                "context": checkpoint.context,
                "artifacts": checkpoint.artifacts,
                "decisions": checkpoint.decisions
            }
            
        except Exception as e:
            self.logger.log_error(
                "CheckpointHook",
                f"Failed to restore checkpoint: {str(e)}"
            )
            return None
    
    def _extract_state(self, context: HookContext) -> Dict[str, Any]:
        """Extract state from context for checkpointing"""
        state = {
            "context": {},
            "artifacts": {},
            "decisions": [],
            "metrics": {}
        }
        
        # Extract from HookContext
        state["context"] = {
            "agent_name": context.agent_name,
            "tool_name": context.tool_name,
            "parameters": context.parameters,
            "metadata": context.metadata,
            "timestamp": context.timestamp
        }
        
        # Extract from metadata
        if "agent_context" in context.metadata:
            agent_ctx = context.metadata["agent_context"]
            if hasattr(agent_ctx, "to_dict"):
                agent_data = agent_ctx.to_dict()
                state["artifacts"] = agent_data.get("artifacts", {})
                state["decisions"] = agent_data.get("decisions", [])
        
        # Extract metrics
        state["metrics"] = {
            "execution_time": context.get("execution_time", 0),
            "memory_usage": self._get_memory_usage(),
            "checkpoint_size": 0  # Will be updated after save
        }
        
        return state
    
    def _save_checkpoint(self, checkpoint: Checkpoint):
        """Save checkpoint to disk"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint.id}.checkpoint.json"
        checkpoint_gz = self.checkpoint_dir / f"{checkpoint.id}.checkpoint.gz"
        
        # Convert to JSON
        data = checkpoint.to_dict()
        json_data = json.dumps(data, indent=2)
        
        # Check size and decide on compression
        size = len(json_data.encode())
        
        if size > self.incremental_threshold:
            # Compress large checkpoints
            with gzip.open(checkpoint_gz, 'wt') as f:
                f.write(json_data)
            
            # Update metrics
            checkpoint.metrics["checkpoint_size"] = checkpoint_gz.stat().st_size
            
            self.logger.log_reasoning(
                "CheckpointHook",
                f"Saved compressed checkpoint ({size} -> {checkpoint_gz.stat().st_size} bytes)"
            )
        else:
            # Save uncompressed for small checkpoints
            with open(checkpoint_file, 'w') as f:
                f.write(json_data)
            
            checkpoint.metrics["checkpoint_size"] = size
        
        # Create incremental save if parent exists
        if checkpoint.parent_id:
            self._create_incremental_save(checkpoint)
    
    def _create_incremental_save(self, checkpoint: Checkpoint):
        """Create incremental save based on parent"""
        parent = self._find_checkpoint(checkpoint.parent_id)
        if not parent:
            return
        
        # Calculate diff
        diff = self._calculate_diff(parent, checkpoint)
        
        if diff:
            diff_file = self.checkpoint_dir / f"{checkpoint.id}.diff.json"
            with open(diff_file, 'w') as f:
                json.dump(diff, f, indent=2)
            
            self.logger.log_reasoning(
                "CheckpointHook",
                f"Created incremental save from {parent.id}"
            )
    
    def _calculate_diff(self, parent: Checkpoint, current: Checkpoint) -> Dict[str, Any]:
        """Calculate difference between checkpoints"""
        diff = {
            "parent_id": parent.id,
            "current_id": current.id,
            "changes": {}
        }
        
        # Compare artifacts
        parent_artifacts = parent.artifacts
        current_artifacts = current.artifacts
        
        for key in current_artifacts:
            if key not in parent_artifacts:
                diff["changes"][f"added_{key}"] = current_artifacts[key]
            elif parent_artifacts[key] != current_artifacts[key]:
                diff["changes"][f"modified_{key}"] = {
                    "old": parent_artifacts[key],
                    "new": current_artifacts[key]
                }
        
        # Check removed artifacts
        for key in parent_artifacts:
            if key not in current_artifacts:
                diff["changes"][f"removed_{key}"] = parent_artifacts[key]
        
        # Compare decisions
        new_decisions = current.decisions[len(parent.decisions):]
        if new_decisions:
            diff["changes"]["new_decisions"] = new_decisions
        
        return diff if diff["changes"] else None
    
    def _is_critical_decision(self, context: HookContext) -> bool:
        """Determine if this is a critical decision point"""
        # Critical events
        critical_events = [
            HookEvent.WORKFLOW_ERROR,
            HookEvent.AGENT_ERROR
        ]
        
        if context.event in critical_events:
            return True
        
        # Critical tools
        critical_tools = [
            "delete_file", "drop_database", "deploy_production",
            "modify_config", "update_credentials"
        ]
        
        if context.tool_name in critical_tools:
            return True
        
        # Critical phases
        critical_phases = ["deployment", "migration", "security_update"]
        current_phase = context.get("current_phase", "")
        
        if any(phase in current_phase.lower() for phase in critical_phases):
            return True
        
        # Check for risky operations
        if context.parameters:
            risky_params = ["force", "skip_validation", "no_backup", "override"]
            for param in risky_params:
                if param in context.parameters:
                    return True
        
        return False
    
    def _generate_checkpoint_id(self, context: HookContext) -> str:
        """Generate unique checkpoint ID"""
        data = f"{context.agent_name}-{context.event.value}-{time.time()}"
        return f"checkpoint_{hashlib.md5(data.encode()).hexdigest()[:12]}"
    
    def _get_parent_checkpoint_id(self) -> Optional[str]:
        """Get ID of parent checkpoint"""
        if self.checkpoints:
            return self.checkpoints[-1].id
        return None
    
    def _generate_description(self, context: HookContext) -> str:
        """Generate checkpoint description"""
        if context.event == HookEvent.AGENT_COMPLETE:
            return f"Agent {context.agent_name} completed"
        elif context.event == HookEvent.WORKFLOW_ERROR:
            return f"Error in workflow: {context.error}"
        elif context.event == HookEvent.MILESTONE_REACHED:
            return f"Milestone: {context.get('milestone', 'Unknown')}"
        elif context.tool_name:
            return f"After {context.tool_name} execution"
        else:
            return f"Checkpoint at phase {context.get('current_phase', 'unknown')}"
    
    def _cleanup_old_checkpoints(self):
        """Remove old checkpoints beyond limit"""
        if len(self.checkpoints) > self.max_checkpoints:
            # Keep critical checkpoints and recent ones
            non_critical = [cp for cp in self.checkpoints if not cp.is_critical]
            
            while len(self.checkpoints) > self.max_checkpoints and non_critical:
                oldest = min(non_critical, key=lambda cp: cp.timestamp)
                
                # Remove files
                for pattern in [f"{oldest.id}.checkpoint*", f"{oldest.id}.diff.json"]:
                    for file in self.checkpoint_dir.glob(pattern):
                        file.unlink()
                
                # Remove from lists
                self.checkpoints.remove(oldest)
                non_critical.remove(oldest)
                
                self.logger.log_reasoning(
                    "CheckpointHook",
                    f"Removed old checkpoint {oldest.id}"
                )
    
    def _load_checkpoints(self):
        """Load existing checkpoints from disk"""
        for checkpoint_file in self.checkpoint_dir.glob("*.checkpoint.*"):
            try:
                if checkpoint_file.suffix == ".gz":
                    with gzip.open(checkpoint_file, 'rt') as f:
                        data = json.load(f)
                else:
                    with open(checkpoint_file, 'r') as f:
                        data = json.load(f)
                
                checkpoint = Checkpoint.from_dict(data)
                self.checkpoints.append(checkpoint)
            except Exception:
                pass  # Skip corrupted checkpoints
        
        # Sort by timestamp
        self.checkpoints.sort(key=lambda cp: cp.timestamp)
        
        if self.checkpoints:
            self.last_checkpoint_time = self.checkpoints[-1].timestamp
            self.logger.log_reasoning(
                "CheckpointHook",
                f"Loaded {len(self.checkpoints)} existing checkpoints"
            )
    
    def _find_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Find checkpoint by ID"""
        for checkpoint in self.checkpoints:
            if checkpoint.id == checkpoint_id:
                return checkpoint
        return None
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss // (1024 * 1024)
        except ImportError:
            return 0
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all available checkpoints"""
        return [
            {
                "id": cp.id,
                "timestamp": datetime.fromtimestamp(cp.timestamp).isoformat(),
                "agent": cp.agent_name,
                "phase": cp.phase,
                "description": cp.description,
                "is_critical": cp.is_critical,
                "size": cp.metrics.get("checkpoint_size", 0)
            }
            for cp in self.checkpoints
        ]


# Singleton instance
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """Get or create checkpoint manager"""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager


class CheckpointSaveHook:
    """Hook for automatic checkpoint creation"""
    
    def __init__(self):
        self.manager = get_checkpoint_manager()
        self.logger = get_logger()
    
    def __call__(self, context: HookContext) -> HookContext:
        """Execute checkpoint save hook"""
        if self.manager.should_create_checkpoint(context):
            checkpoint = self.manager.create_checkpoint(context)
            
            if checkpoint:
                context.set("checkpoint_id", checkpoint.id)
                context.set("checkpoint_saved", True)
                
                self.logger.log_reasoning(
                    "CheckpointHook",
                    f"Checkpoint saved: {checkpoint.id} - {checkpoint.description}"
                )
        
        return context


# Export the hook function
checkpoint_save_hook = CheckpointSaveHook()


# Registration helper
def register(hook_manager):
    """Register this hook with the hook manager"""
    from lib.hook_manager import HookEvent
    
    # Register for multiple events
    events = [
        HookEvent.AGENT_COMPLETE,
        HookEvent.WORKFLOW_ERROR,
        HookEvent.MILESTONE_REACHED
    ]
    
    for event in events:
        hook_manager.register_hook(
            name=f"checkpoint_save_{event.value}",
            event_type=event,
            function=checkpoint_save_hook,
            priority=50,
            config={
                "enabled": True,
                "triggers": ["agent_complete", "critical_decision", "error_detected"],
                "interval_minutes": 5,
                "max_checkpoints": 20
            }
        )


if __name__ == "__main__":
    # Test the checkpoint system
    from lib.hook_manager import HookContext, HookEvent
    
    # Create test context
    context = HookContext(
        event=HookEvent.AGENT_COMPLETE,
        agent_name="test-agent",
        tool_name="write_file",
        parameters={"file_path": "test.txt", "content": "Hello"}
    )
    
    # Set some metadata
    context.set("current_phase", "implementation")
    context.set("agent_context", {
        "artifacts": {"file1": "content1"},
        "decisions": [{"decision": "Use Python", "rationale": "Best fit"}]
    })
    
    # Execute hook
    hook = CheckpointSaveHook()
    result = hook(context)
    
    if result.get("checkpoint_saved"):
        print(f"Checkpoint saved: {result.get('checkpoint_id')}")
        
        # List checkpoints
        manager = get_checkpoint_manager()
        checkpoints = manager.list_checkpoints()
        print("\nAvailable checkpoints:")
        for cp in checkpoints:
            print(f"  - {cp['id']}: {cp['description']} ({cp['timestamp']})")
        
        # Test restore
        if checkpoints:
            restored = manager.restore_checkpoint(checkpoints[0]['id'])
            if restored:
                print(f"\nRestored checkpoint: {restored['checkpoint'].description}")