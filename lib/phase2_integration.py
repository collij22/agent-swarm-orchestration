#!/usr/bin/env python3
"""
Phase 2 Integration Module
Connects file coordination, verification, and inter-agent communication 
to the orchestration system.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Import Phase 2 components
import sys
from pathlib import Path
# Add lib directory to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent))

try:
    from file_coordinator import get_file_coordinator, FileCoordinator
    from agent_verification import AgentVerification
except ImportError as e:
    print(f"Import error: {e}")
    raise

# For AgentContext, we'll create a simple version if full import fails
try:
    from agent_runtime import AgentContext, clean_reasoning
except ImportError:
    # Create a minimal AgentContext for testing
    from dataclasses import dataclass, field
    from typing import Dict, List, Any
    
    @dataclass
    class AgentContext:
        """Minimal AgentContext for testing"""
        project_requirements: Dict = field(default_factory=dict)
        completed_tasks: List[str] = field(default_factory=list)
        artifacts: Dict[str, Any] = field(default_factory=dict)
        decisions: List[Dict[str, str]] = field(default_factory=list)
        current_phase: str = "execution"
        created_files: Dict[str, Dict] = field(default_factory=dict)
        verification_required: List[str] = field(default_factory=list)
        agent_dependencies: Dict[str, List[str]] = field(default_factory=dict)
        incomplete_tasks: List[Dict] = field(default_factory=list)
        
        def add_created_file(self, agent_name: str, file_path: str, file_type: str = "code", verified: bool = False):
            if agent_name not in self.created_files:
                self.created_files[agent_name] = []
            self.created_files[agent_name].append({
                "path": file_path,
                "type": file_type,
                "verified": verified,
                "timestamp": datetime.now().isoformat()
            })
        
        def to_dict(self):
            return {
                "project_requirements": self.project_requirements,
                "completed_tasks": self.completed_tasks,
                "artifacts": self.artifacts,
                "decisions": self.decisions,
                "current_phase": self.current_phase,
                "created_files": self.created_files,
                "verification_required": self.verification_required,
                "agent_dependencies": self.agent_dependencies,
                "incomplete_tasks": self.incomplete_tasks
            }
    
    def clean_reasoning(text: str, max_lines: int = 3) -> str:
        """Minimal clean_reasoning for testing"""
        if not text:
            return text
        lines = text.split('\n')
        unique_lines = []
        seen = set()
        for line in lines:
            line_stripped = line.strip()
            if line_stripped and line_stripped not in seen:
                unique_lines.append(line)
                seen.add(line_stripped)
                if len(unique_lines) >= max_lines:
                    break
        return '\n'.join(unique_lines)

class Phase2Integration:
    """
    Integrates Phase 2 enhancements into the orchestration system.
    Provides a unified interface for file locking, verification, and communication.
    """
    
    def __init__(self, project_name: str = "default"):
        """Initialize Phase 2 integration components."""
        self.project_name = project_name
        self.file_coordinator = get_file_coordinator()
        self.verification = AgentVerification()
        self.agent_contexts = {}  # Store context per agent
        
        # Statistics tracking
        self.stats = {
            "files_locked": 0,
            "verifications_run": 0,
            "artifacts_shared": 0,
            "conflicts_prevented": 0
        }
    
    def before_agent_execution(self, agent_name: str, files_to_modify: List[str] = None) -> bool:
        """
        Pre-execution setup for an agent.
        
        Args:
            agent_name: Name of the agent about to execute
            files_to_modify: List of files the agent intends to modify
        
        Returns:
            True if agent can proceed, False if blocked
        """
        # Acquire locks for files the agent will modify
        if files_to_modify:
            locked_files = []
            for file_path in files_to_modify:
                if self.file_coordinator.acquire_lock(file_path, agent_name):
                    locked_files.append(file_path)
                    self.stats["files_locked"] += 1
                else:
                    # Failed to acquire lock, release already locked files
                    lock_info = self.file_coordinator.get_lock_info(file_path)
                    print(f"[WARNING] {agent_name} blocked: {file_path} locked by {lock_info.agent_name if lock_info else 'unknown'}")
                    
                    # Release any locks we acquired
                    for locked_file in locked_files:
                        self.file_coordinator.release_lock(locked_file, agent_name)
                    
                    self.stats["conflicts_prevented"] += 1
                    return False
        
        # Initialize or get agent context
        if agent_name not in self.agent_contexts:
            self.agent_contexts[agent_name] = AgentContext(
                project_requirements={},
                completed_tasks=[],
                artifacts={},
                decisions=[],
                current_phase="execution"
            )
        
        return True
    
    def after_agent_execution(self, agent_name: str, created_files: List[str] = None,
                            modified_files: List[str] = None) -> Dict[str, Any]:
        """
        Post-execution cleanup and verification for an agent.
        
        Args:
            agent_name: Name of the agent that just executed
            created_files: List of files created by the agent
            modified_files: List of files modified by the agent
        
        Returns:
            Verification results dictionary
        """
        results = {
            "agent": agent_name,
            "verification_passed": True,
            "errors": [],
            "warnings": []
        }
        
        # Release file locks
        released_count = self.file_coordinator.release_all_agent_locks(agent_name)
        if released_count > 0:
            print(f"[INFO] Released {released_count} file locks for {agent_name}")
        
        # Track modifications
        all_files = (created_files or []) + (modified_files or [])
        for file_path in all_files:
            self.file_coordinator.track_modification(
                file_path=file_path,
                agent_name=agent_name,
                operation="create" if file_path in (created_files or []) else "update"
            )
            
            # Track in agent context
            if agent_name in self.agent_contexts:
                self.agent_contexts[agent_name].add_created_file(
                    agent_name=agent_name,
                    file_path=file_path,
                    file_type=self._get_file_type(file_path)
                )
        
        # Run verification suite
        if all_files:
            verification_results = self.verification.run_verification_suite(all_files)
            self.stats["verifications_run"] += 1
            
            for file_path, file_results in verification_results.items():
                if file_results.get("errors"):
                    results["verification_passed"] = False
                    results["errors"].extend([
                        f"{file_path}: {error}" for error in file_results["errors"]
                    ])
                
                if file_results.get("warnings"):
                    results["warnings"].extend([
                        f"{file_path}: {warning}" for warning in file_results["warnings"]
                    ])
        
        return results
    
    def share_agent_artifact(self, agent_name: str, artifact_type: str, 
                            content: Any, description: str = None) -> bool:
        """
        Share an artifact between agents.
        
        Args:
            agent_name: Name of the agent sharing the artifact
            artifact_type: Type of artifact (e.g., "api_schema", "database_model")
            content: The artifact content
            description: Optional description
        
        Returns:
            True if artifact was shared successfully
        """
        if agent_name not in self.agent_contexts:
            return False
        
        context = self.agent_contexts[agent_name]
        artifact_key = f"{agent_name}_{artifact_type}"
        
        context.artifacts[artifact_key] = {
            "type": artifact_type,
            "content": content,
            "description": description,
            "shared_by": agent_name,
            "timestamp": datetime.now().isoformat()
        }
        
        self.stats["artifacts_shared"] += 1
        print(f"[INFO] {agent_name} shared {artifact_type} artifact")
        
        return True
    
    def get_shared_artifacts(self, artifact_type: str = None) -> Dict[str, Any]:
        """
        Get shared artifacts, optionally filtered by type.
        
        Args:
            artifact_type: Optional filter by artifact type
        
        Returns:
            Dictionary of shared artifacts
        """
        all_artifacts = {}
        
        for agent_name, context in self.agent_contexts.items():
            for key, artifact in context.artifacts.items():
                if artifact_type is None or artifact.get("type") == artifact_type:
                    all_artifacts[key] = artifact
        
        return all_artifacts
    
    def check_agent_dependencies(self, agent_name: str, 
                                required_artifacts: List[str]) -> Tuple[bool, List[str]]:
        """
        Check if an agent's dependencies are available.
        
        Args:
            agent_name: Name of the agent
            required_artifacts: List of required artifact keys
        
        Returns:
            Tuple of (dependencies_met, missing_artifacts)
        """
        all_artifacts = self.get_shared_artifacts()
        missing = []
        
        for artifact_key in required_artifacts:
            if artifact_key not in all_artifacts:
                missing.append(artifact_key)
        
        return len(missing) == 0, missing
    
    def clean_agent_reasoning(self, agent_name: str, reasoning_text: str) -> str:
        """
        Clean and deduplicate agent reasoning output.
        
        Args:
            agent_name: Name of the agent
            reasoning_text: Raw reasoning text
        
        Returns:
            Cleaned reasoning text
        """
        # Apply special handling for DevOps-Engineer
        if agent_name.lower() == "devops-engineer":
            return clean_reasoning(reasoning_text, max_lines=5)
        else:
            return clean_reasoning(reasoning_text, max_lines=10)
    
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type from extension."""
        ext = Path(file_path).suffix.lower()
        
        type_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "react",
            ".tsx": "react",
            ".json": "config",
            ".yaml": "config",
            ".yml": "config",
            ".md": "documentation",
            ".txt": "text",
            ".sh": "script",
            ".bat": "script",
            ".dockerfile": "docker",
            ".env": "config"
        }
        
        return type_map.get(ext, "unknown")
    
    def get_conflict_report(self, time_window: int = 60) -> Dict[str, Any]:
        """
        Get a report of potential file conflicts.
        
        Args:
            time_window: Time window in seconds to check for conflicts
        
        Returns:
            Conflict report dictionary
        """
        conflicts = self.file_coordinator.detect_conflicts(time_window)
        
        return {
            "conflicts_detected": len(conflicts),
            "conflicting_files": [
                {
                    "file": file_path,
                    "agents": agents
                }
                for file_path, agents in conflicts
            ],
            "prevention_stats": self.file_coordinator.get_statistics()
        }
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get Phase 2 integration statistics."""
        return {
            "phase2_stats": self.stats,
            "file_coordinator_stats": self.file_coordinator.get_statistics(),
            "active_agents": list(self.agent_contexts.keys()),
            "total_artifacts_shared": sum(
                len(ctx.artifacts) for ctx in self.agent_contexts.values()
            )
        }
    
    def save_state(self, output_dir: str = "checkpoints"):
        """
        Save Phase 2 integration state for recovery.
        
        Args:
            output_dir: Directory to save state files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save file coordinator state
        self.file_coordinator.save_state(
            str(output_path / f"file_coordinator_{self.project_name}.json")
        )
        
        # Save agent contexts
        contexts_data = {
            agent_name: context.to_dict()
            for agent_name, context in self.agent_contexts.items()
        }
        
        with open(output_path / f"agent_contexts_{self.project_name}.json", 'w') as f:
            json.dump(contexts_data, f, indent=2, default=str)
        
        # Save integration stats
        with open(output_path / f"phase2_stats_{self.project_name}.json", 'w') as f:
            json.dump(self.get_integration_stats(), f, indent=2)
        
        print(f"[INFO] Phase 2 state saved to {output_path}")
    
    def load_state(self, output_dir: str = "checkpoints") -> bool:
        """
        Load Phase 2 integration state from saved files.
        
        Args:
            output_dir: Directory containing state files
        
        Returns:
            True if state was loaded successfully
        """
        output_path = Path(output_dir)
        
        try:
            # Load file coordinator state
            coordinator_file = output_path / f"file_coordinator_{self.project_name}.json"
            if coordinator_file.exists():
                self.file_coordinator.load_state(str(coordinator_file))
            
            # Load agent contexts
            contexts_file = output_path / f"agent_contexts_{self.project_name}.json"
            if contexts_file.exists():
                with open(contexts_file, 'r') as f:
                    contexts_data = json.load(f)
                
                for agent_name, context_dict in contexts_data.items():
                    self.agent_contexts[agent_name] = AgentContext(
                        project_requirements=context_dict.get("project_requirements", {}),
                        completed_tasks=context_dict.get("completed_tasks", []),
                        artifacts=context_dict.get("artifacts", {}),
                        decisions=context_dict.get("decisions", []),
                        current_phase=context_dict.get("current_phase", "execution"),
                        created_files=context_dict.get("created_files", {}),
                        verification_required=context_dict.get("verification_required", []),
                        agent_dependencies=context_dict.get("agent_dependencies", {}),
                        incomplete_tasks=context_dict.get("incomplete_tasks", [])
                    )
            
            print(f"[INFO] Phase 2 state loaded from {output_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load Phase 2 state: {e}")
            return False


def example_usage():
    """Example of how to use Phase 2 integration in orchestration."""
    
    # Initialize integration
    integration = Phase2Integration(project_name="test_project")
    
    # Before agent execution
    agent_name = "rapid-builder"
    files_to_modify = ["src/main.py", "src/config.json"]
    
    if integration.before_agent_execution(agent_name, files_to_modify):
        print(f"[OK] {agent_name} can proceed with execution")
        
        # Simulate agent execution...
        created_files = ["src/main.py", "src/utils.py"]
        
        # After agent execution
        results = integration.after_agent_execution(
            agent_name, 
            created_files=created_files
        )
        
        if results["verification_passed"]:
            print(f"[OK] {agent_name} passed all verifications")
        else:
            print(f"[ERROR] {agent_name} verification failed:")
            for error in results["errors"]:
                print(f"  - {error}")
        
        # Share an artifact
        integration.share_agent_artifact(
            agent_name,
            "api_schema",
            {"endpoints": ["/api/users", "/api/products"]},
            "REST API schema for the application"
        )
    else:
        print(f"[BLOCKED] {agent_name} cannot proceed - files are locked")
    
    # Check for conflicts
    conflict_report = integration.get_conflict_report()
    if conflict_report["conflicts_detected"] > 0:
        print(f"[WARNING] Detected {conflict_report['conflicts_detected']} conflicts")
    
    # Get integration stats
    stats = integration.get_integration_stats()
    print(f"\nPhase 2 Integration Stats:")
    print(json.dumps(stats, indent=2))
    
    # Save state for recovery
    integration.save_state()


if __name__ == "__main__":
    example_usage()