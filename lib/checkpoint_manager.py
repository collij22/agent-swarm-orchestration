#!/usr/bin/env python3
"""
Enhanced Checkpoint Manager - Phase 4.2 Implementation  
Comprehensive checkpoint system with full context preservation
"""

import json
import pickle
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

@dataclass
class CheckpointMetadata:
    """Metadata for a checkpoint"""
    checkpoint_id: str
    agent_name: str
    timestamp: datetime
    progress_percentage: float
    files_created: List[str]
    artifacts_saved: List[str]
    decisions_made: List[str]
    validation_status: str
    can_resume: bool
    parent_checkpoint: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "checkpoint_id": self.checkpoint_id,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "progress_percentage": self.progress_percentage,
            "files_created": self.files_created,
            "artifacts_saved": self.artifacts_saved,
            "decisions_made": self.decisions_made,
            "validation_status": self.validation_status,
            "can_resume": self.can_resume,
            "parent_checkpoint": self.parent_checkpoint
        }

class CheckpointManager:
    """
    Enhanced checkpoint manager for Phase 4.2
    Saves and restores complete execution context
    """
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.active_checkpoints = {}
        self.checkpoint_chain = []  # Track checkpoint lineage
        
    def create_checkpoint(
        self,
        agent_name: str,
        progress: float,
        context: Any,
        files_created: List[str] = None,
        validation_passed: bool = True
    ) -> str:
        """
        Create comprehensive checkpoint with full context
        Phase 4.2 requirement: Save complete execution state
        
        Args:
            agent_name: Name of the agent creating checkpoint
            progress: Progress percentage (0-100)
            context: Full AgentContext object
            files_created: List of files created by agent
            validation_passed: Whether validation passed
            
        Returns:
            checkpoint_id: Unique checkpoint identifier
        """
        # Generate unique checkpoint ID
        timestamp = datetime.now()
        checkpoint_id = self._generate_checkpoint_id(agent_name, timestamp)
        
        # Create checkpoint directory
        checkpoint_path = self.checkpoint_dir / checkpoint_id
        checkpoint_path.mkdir(exist_ok=True)
        
        # Save context
        context_file = checkpoint_path / "context.json"
        self._save_context(context, context_file)
        
        # Save files created (copy them to checkpoint)
        if files_created:
            files_dir = checkpoint_path / "files"
            files_dir.mkdir(exist_ok=True)
            self._backup_files(files_created, files_dir)
        
        # Extract artifacts and decisions from context
        artifacts = []
        decisions = []
        
        if hasattr(context, 'artifacts'):
            artifacts = list(context.artifacts.keys())
            # Save artifacts separately
            artifacts_file = checkpoint_path / "artifacts.json"
            with open(artifacts_file, 'w') as f:
                json.dump(context.artifacts, f, indent=2, default=str)
        
        if hasattr(context, 'decisions'):
            decisions = [str(d) for d in context.decisions]
            # Save decisions
            decisions_file = checkpoint_path / "decisions.json"
            with open(decisions_file, 'w') as f:
                json.dump(decisions, f, indent=2)
        
        # Create metadata
        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            agent_name=agent_name,
            timestamp=timestamp,
            progress_percentage=progress,
            files_created=files_created or [],
            artifacts_saved=artifacts,
            decisions_made=decisions,
            validation_status="passed" if validation_passed else "failed",
            can_resume=validation_passed,
            parent_checkpoint=self.checkpoint_chain[-1] if self.checkpoint_chain else None
        )
        
        # Save metadata
        metadata_file = checkpoint_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        # Update tracking
        self.active_checkpoints[checkpoint_id] = metadata
        self.checkpoint_chain.append(checkpoint_id)
        
        # Save checkpoint index
        self._update_checkpoint_index()
        
        return checkpoint_id
    
    def resume_from_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Resume from checkpoint with full context restoration
        Phase 4.2 requirement: Complete context restoration
        
        Args:
            checkpoint_id: Checkpoint to resume from
            
        Returns:
            Restored context and state, or None if checkpoint not found
        """
        checkpoint_path = self.checkpoint_dir / checkpoint_id
        
        if not checkpoint_path.exists():
            return None
        
        # Load metadata
        metadata_file = checkpoint_path / "metadata.json"
        if not metadata_file.exists():
            return None
            
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Check if checkpoint can be resumed
        if not metadata.get('can_resume', False):
            return None
        
        # Load context
        context_file = checkpoint_path / "context.json"
        context = self._load_context(context_file)
        
        # Load artifacts
        artifacts = {}
        artifacts_file = checkpoint_path / "artifacts.json"
        if artifacts_file.exists():
            with open(artifacts_file, 'r') as f:
                artifacts = json.load(f)
        
        # Load decisions
        decisions = []
        decisions_file = checkpoint_path / "decisions.json"
        if decisions_file.exists():
            with open(decisions_file, 'r') as f:
                decisions = json.load(f)
        
        # Restore files if needed
        files_dir = checkpoint_path / "files"
        restored_files = []
        if files_dir.exists():
            restored_files = self._restore_files(files_dir)
        
        # Build restoration package
        restoration = {
            "checkpoint_id": checkpoint_id,
            "agent_name": metadata['agent_name'],
            "progress": metadata['progress_percentage'],
            "context": context,
            "artifacts": artifacts,
            "decisions": decisions,
            "files_restored": restored_files,
            "timestamp": metadata['timestamp'],
            "parent_checkpoint": metadata.get('parent_checkpoint')
        }
        
        return restoration
    
    def get_checkpoint_chain(self, checkpoint_id: str) -> List[str]:
        """
        Get the chain of checkpoints leading to this one
        Useful for understanding execution history
        """
        chain = []
        current_id = checkpoint_id
        
        while current_id:
            checkpoint_path = self.checkpoint_dir / current_id / "metadata.json"
            if not checkpoint_path.exists():
                break
                
            with open(checkpoint_path, 'r') as f:
                metadata = json.load(f)
            
            chain.append(current_id)
            current_id = metadata.get('parent_checkpoint')
        
        return list(reversed(chain))
    
    def list_checkpoints(
        self, 
        agent_name: Optional[str] = None,
        can_resume_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List available checkpoints with filtering
        """
        checkpoints = []
        
        for checkpoint_dir in self.checkpoint_dir.iterdir():
            if checkpoint_dir.is_dir():
                metadata_file = checkpoint_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Apply filters
                    if agent_name and metadata['agent_name'] != agent_name:
                        continue
                    if can_resume_only and not metadata.get('can_resume', False):
                        continue
                    
                    checkpoints.append(metadata)
        
        # Sort by timestamp
        checkpoints.sort(key=lambda x: x['timestamp'], reverse=True)
        return checkpoints
    
    def cleanup_old_checkpoints(self, keep_last: int = 10):
        """
        Clean up old checkpoints to save space
        Keeps the most recent N checkpoints
        """
        checkpoints = self.list_checkpoints()
        
        if len(checkpoints) > keep_last:
            to_remove = checkpoints[keep_last:]
            
            for checkpoint_meta in to_remove:
                checkpoint_path = self.checkpoint_dir / checkpoint_meta['checkpoint_id']
                if checkpoint_path.exists():
                    shutil.rmtree(checkpoint_path)
            
            # Update index
            self._update_checkpoint_index()
    
    def _generate_checkpoint_id(self, agent_name: str, timestamp: datetime) -> str:
        """Generate unique checkpoint ID"""
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        hash_input = f"{agent_name}_{timestamp_str}_{id(self)}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"checkpoint_{agent_name}_{timestamp_str}_{hash_suffix}"
    
    def _save_context(self, context: Any, file_path: Path):
        """Save context object to JSON"""
        # Convert context to dictionary
        context_dict = {}
        
        if hasattr(context, '__dict__'):
            for key, value in context.__dict__.items():
                try:
                    # Try to serialize to JSON
                    json.dumps(value, default=str)
                    context_dict[key] = value
                except (TypeError, ValueError):
                    # If not JSON serializable, convert to string
                    context_dict[key] = str(value)
        else:
            context_dict = {"context": str(context)}
        
        with open(file_path, 'w') as f:
            json.dump(context_dict, f, indent=2, default=str)
    
    def _load_context(self, file_path: Path) -> Dict[str, Any]:
        """Load context from JSON"""
        if not file_path.exists():
            return {}
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def _backup_files(self, files: List[str], backup_dir: Path):
        """Backup files to checkpoint directory"""
        for file_path in files:
            source = Path(file_path)
            if source.exists():
                # Preserve directory structure
                relative_path = source.relative_to(Path.cwd()) if source.is_absolute() else source
                dest = backup_dir / relative_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                if source.is_file():
                    shutil.copy2(source, dest)
                elif source.is_dir():
                    shutil.copytree(source, dest, dirs_exist_ok=True)
    
    def _restore_files(self, backup_dir: Path) -> List[str]:
        """Restore files from checkpoint directory"""
        restored = []
        
        for backup_file in backup_dir.rglob('*'):
            if backup_file.is_file():
                # Calculate original path
                relative_path = backup_file.relative_to(backup_dir)
                original_path = Path.cwd() / relative_path
                
                # Create directories if needed
                original_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file back
                shutil.copy2(backup_file, original_path)
                restored.append(str(original_path))
        
        return restored
    
    def _update_checkpoint_index(self):
        """Update the checkpoint index file"""
        index_file = self.checkpoint_dir / "index.json"
        
        index = {
            "last_updated": datetime.now().isoformat(),
            "total_checkpoints": len(list(self.checkpoint_dir.iterdir())) - 1,  # Exclude index file
            "active_chain": self.checkpoint_chain,
            "checkpoints": []
        }
        
        # Add checkpoint summaries
        for checkpoint_id, metadata in self.active_checkpoints.items():
            index["checkpoints"].append({
                "id": checkpoint_id,
                "agent": metadata.agent_name,
                "progress": metadata.progress_percentage,
                "can_resume": metadata.can_resume
            })
        
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    def get_latest_checkpoint(self, agent_name: Optional[str] = None) -> Optional[str]:
        """Get the most recent checkpoint ID"""
        checkpoints = self.list_checkpoints(agent_name=agent_name, can_resume_only=True)
        
        if checkpoints:
            return checkpoints[0]['checkpoint_id']
        
        return None