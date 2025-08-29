#!/usr/bin/env python3
"""
Session Manager - Comprehensive session management for agent swarm

Features:
- Session storage and retrieval
- Session replay functionality
- Session comparison and analysis
- Checkpoint management
- Debugging utilities
"""

import json
import os
import shutil
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Import agent components
from agent_logger import LogEntry, EventType, LogLevel, AgentMetrics
from agent_runtime import AgentContext, AnthropicAgentRunner

class SessionStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    REPLAYING = "replaying"

class ReplayMode(Enum):
    MOCK = "mock"  # Simulate execution without API calls
    REAL = "real"  # Real execution with API calls
    STEP = "step"  # Step-through debugging mode

@dataclass
class SessionMetadata:
    """Metadata for a session"""
    session_id: str
    version: str = "2.0"
    project_type: str = "unknown"
    status: SessionStatus = SessionStatus.RUNNING
    created_at: str = ""
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    requirements: Dict = None
    tags: List[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.requirements is None:
            self.requirements = {}
        if self.tags is None:
            self.tags = []

@dataclass
class Checkpoint:
    """Workflow checkpoint"""
    name: str
    timestamp: str
    agent_name: str
    phase: str
    state: Dict
    reasoning: str
    
@dataclass
class SessionData:
    """Complete session data"""
    metadata: SessionMetadata
    entries: List[LogEntry]
    metrics: Dict[str, AgentMetrics]
    checkpoints: List[Checkpoint]
    decisions: List[Dict]
    errors: List[Dict]
    api_calls: Dict
    performance: Dict
    
    def to_dict(self) -> Dict:
        metadata_dict = asdict(self.metadata)
        # Convert enum to string
        if isinstance(metadata_dict.get("status"), SessionStatus):
            metadata_dict["status"] = metadata_dict["status"].value
        
        return {
            "metadata": metadata_dict,
            "entries": [entry.to_dict() if hasattr(entry, 'to_dict') else entry for entry in self.entries],
            "metrics": {
                name: asdict(metric) if hasattr(metric, '__dict__') else metric 
                for name, metric in self.metrics.items()
            },
            "checkpoints": [asdict(cp) for cp in self.checkpoints],
            "decisions": self.decisions,
            "errors": self.errors,
            "api_calls": self.api_calls,
            "performance": self.performance
        }

class SessionManager:
    """Manages agent swarm sessions"""
    
    def __init__(self, base_dir: str = "./sessions"):
        self.base_dir = Path(base_dir)
        self.active_dir = self.base_dir / "active"
        self.completed_dir = self.base_dir / "completed"
        self.failed_dir = self.base_dir / "failed"
        self.archived_dir = self.base_dir / "archived"
        
        # Create directory structure
        for dir_path in [self.active_dir, self.completed_dir, self.failed_dir, self.archived_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Session index cache
        self._index_cache = {}
        self._rebuild_index()
        
        # Current session being managed
        self.current_session: Optional[SessionData] = None
        
    def _rebuild_index(self):
        """Rebuild the session index"""
        self._index_cache = {}
        
        for status_dir in [self.active_dir, self.completed_dir, self.failed_dir]:
            for session_file in status_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        data = json.load(f)
                        metadata = data.get("metadata", {})
                        session_id = metadata.get("session_id", session_file.stem)
                        self._index_cache[session_id] = {
                            "path": session_file,
                            "status": metadata.get("status", "unknown"),
                            "created_at": metadata.get("created_at", ""),
                            "project_type": metadata.get("project_type", "unknown")
                        }
                except Exception as e:
                    print(f"Error indexing {session_file}: {e}")
    
    def create_session(self, 
                      project_type: str = "unknown",
                      requirements: Dict = None,
                      tags: List[str] = None) -> SessionData:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        metadata = SessionMetadata(
            session_id=session_id,
            project_type=project_type,
            requirements=requirements or {},
            tags=tags or []
        )
        
        self.current_session = SessionData(
            metadata=metadata,
            entries=[],
            metrics={},
            checkpoints=[],
            decisions=[],
            errors=[],
            api_calls={"total": 0, "by_model": {}, "estimated_cost": 0.0},
            performance={"peak_memory_mb": 0, "cpu_usage": {}}
        )
        
        # Save initial session
        self.save_session(self.current_session, self.active_dir)
        return self.current_session
    
    def load_session(self, session_id: str) -> Optional[SessionData]:
        """Load a session by ID"""
        if session_id not in self._index_cache:
            self._rebuild_index()
        
        if session_id not in self._index_cache:
            return None
        
        session_path = self._index_cache[session_id]["path"]
        
        try:
            with open(session_path, 'r') as f:
                data = json.load(f)
            
            # Convert to SessionData
            metadata_dict = data["metadata"]
            # Convert status string back to enum if needed
            if "status" in metadata_dict and isinstance(metadata_dict["status"], str):
                metadata_dict["status"] = SessionStatus(metadata_dict["status"])
            
            metadata = SessionMetadata(**metadata_dict)
            
            session = SessionData(
                metadata=metadata,
                entries=data.get("entries", []),
                metrics=data.get("metrics", {}),
                checkpoints=[Checkpoint(**cp) for cp in data.get("checkpoints", [])],
                decisions=data.get("decisions", []),
                errors=data.get("errors", []),
                api_calls=data.get("api_calls", {}),
                performance=data.get("performance", {})
            )
            
            return session
            
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    
    def save_session(self, session: SessionData, directory: Optional[Path] = None):
        """Save a session to disk"""
        if directory is None:
            # Determine directory based on status
            if session.metadata.status == SessionStatus.COMPLETED:
                directory = self.completed_dir
            elif session.metadata.status == SessionStatus.FAILED:
                directory = self.failed_dir
            else:
                directory = self.active_dir
        
        session_file = directory / f"{session.metadata.session_id}.json"
        
        with open(session_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
        
        # Update index
        self._index_cache[session.metadata.session_id] = {
            "path": session_file,
            "status": session.metadata.status.value,
            "created_at": session.metadata.created_at,
            "project_type": session.metadata.project_type
        }
    
    def complete_session(self, session_id: str, success: bool = True):
        """Mark a session as complete"""
        session = self.load_session(session_id)
        if not session:
            return
        
        # Update metadata
        session.metadata.status = SessionStatus.COMPLETED if success else SessionStatus.FAILED
        session.metadata.completed_at = datetime.now().isoformat()
        
        if session.metadata.created_at:
            start_time = datetime.fromisoformat(session.metadata.created_at)
            duration = datetime.now() - start_time
            session.metadata.duration_ms = int(duration.total_seconds() * 1000)
        
        # Move from active to appropriate directory
        old_path = self.active_dir / f"{session_id}.json"
        if old_path.exists():
            old_path.unlink()
        
        self.save_session(session)
    
    def list_sessions(self, 
                     status: Optional[SessionStatus] = None,
                     project_type: Optional[str] = None,
                     date_from: Optional[datetime] = None,
                     date_to: Optional[datetime] = None) -> List[Dict]:
        """List sessions with optional filters"""
        sessions = []
        
        for session_id, info in self._index_cache.items():
            # Apply filters
            if status and info["status"] != status.value:
                continue
            if project_type and info["project_type"] != project_type:
                continue
            if date_from or date_to:
                created_at = datetime.fromisoformat(info["created_at"])
                if date_from and created_at < date_from:
                    continue
                if date_to and created_at > date_to:
                    continue
            
            sessions.append({
                "session_id": session_id,
                **info
            })
        
        # Sort by creation date
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions
    
    def add_checkpoint(self, session_id: str, checkpoint: Checkpoint):
        """Add a checkpoint to a session"""
        session = self.load_session(session_id)
        if session:
            session.checkpoints.append(checkpoint)
            self.save_session(session)
    
    def replay_session(self, 
                      session_id: str,
                      mode: ReplayMode = ReplayMode.MOCK,
                      start_from: Optional[str] = None,
                      agents_to_skip: List[str] = None) -> bool:
        """Replay a session"""
        session = self.load_session(session_id)
        if not session:
            print(f"Session {session_id} not found")
            return False
        
        print(f"Replaying session {session_id} in {mode.value} mode")
        
        # Update status
        session.metadata.status = SessionStatus.REPLAYING
        self.save_session(session)
        
        # Create replay context
        context = AgentContext(
            project_requirements=session.metadata.requirements,
            completed_tasks=[],
            artifacts={},
            decisions=session.decisions,
            current_phase="replay"
        )
        
        # Replay from checkpoint if specified
        start_index = 0
        if start_from:
            for i, entry in enumerate(session.entries):
                if hasattr(entry, 'agent_name') and entry.agent_name == start_from:
                    start_index = i
                    break
        
        # Replay entries
        success = True
        for entry in session.entries[start_index:]:
            if not isinstance(entry, dict):
                continue
            
            agent_name = entry.get("agent_name", "")
            
            # Skip if in skip list
            if agents_to_skip and agent_name in agents_to_skip:
                print(f"Skipping agent: {agent_name}")
                continue
            
            event_type = entry.get("event_type", "")
            
            if event_type == "agent_start":
                print(f"\nReplaying agent: {agent_name}")
                
                if mode == ReplayMode.MOCK:
                    # Simulate execution
                    print(f"  [MOCK] {entry.get('message', '')}")
                    if entry.get("reasoning"):
                        print(f"  Reasoning: {entry['reasoning']}")
                
                elif mode == ReplayMode.REAL:
                    # Real execution would go here
                    print(f"  [REAL] Would execute: {agent_name}")
                
                elif mode == ReplayMode.STEP:
                    # Step-through mode
                    print(f"  [STEP] {entry.get('message', '')}")
                    if entry.get("reasoning"):
                        print(f"  Reasoning: {entry['reasoning']}")
                    input("Press Enter to continue...")
        
        # Restore original status
        session.metadata.status = SessionStatus.COMPLETED if success else SessionStatus.FAILED
        self.save_session(session)
        
        return success
    
    def compare_sessions(self, session_id1: str, session_id2: str) -> Dict:
        """Compare two sessions"""
        session1 = self.load_session(session_id1)
        session2 = self.load_session(session_id2)
        
        if not session1 or not session2:
            return {"error": "One or both sessions not found"}
        
        comparison = {
            "session1": session_id1,
            "session2": session_id2,
            "duration_diff_ms": (session1.metadata.duration_ms or 0) - (session2.metadata.duration_ms or 0),
            "agents_diff": {
                "session1_only": [],
                "session2_only": [],
                "common": []
            },
            "metrics_comparison": {},
            "api_calls_diff": {
                "total": session1.api_calls.get("total", 0) - session2.api_calls.get("total", 0),
                "cost": session1.api_calls.get("estimated_cost", 0) - session2.api_calls.get("estimated_cost", 0)
            },
            "errors": {
                "session1": len(session1.errors),
                "session2": len(session2.errors)
            }
        }
        
        # Compare agents used
        agents1 = set(session1.metrics.keys())
        agents2 = set(session2.metrics.keys())
        comparison["agents_diff"]["session1_only"] = list(agents1 - agents2)
        comparison["agents_diff"]["session2_only"] = list(agents2 - agents1)
        comparison["agents_diff"]["common"] = list(agents1 & agents2)
        
        # Compare metrics for common agents
        for agent in comparison["agents_diff"]["common"]:
            if agent in session1.metrics and agent in session2.metrics:
                m1 = session1.metrics[agent]
                m2 = session2.metrics[agent]
                comparison["metrics_comparison"][agent] = {
                    "duration_diff": m1.get("average_duration_ms", 0) - m2.get("average_duration_ms", 0),
                    "success_rate_diff": m1.get("success_rate", 0) - m2.get("success_rate", 0)
                }
        
        return comparison
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get a summary of a session"""
        session = self.load_session(session_id)
        if not session:
            return None
        
        summary = {
            "session_id": session_id,
            "status": session.metadata.status.value,
            "project_type": session.metadata.project_type,
            "duration_ms": session.metadata.duration_ms,
            "total_agents": len(session.metrics),
            "total_checkpoints": len(session.checkpoints),
            "total_errors": len(session.errors),
            "api_calls": session.api_calls,
            "agent_summary": {}
        }
        
        # Add agent-specific summaries
        for agent_name, metrics in session.metrics.items():
            summary["agent_summary"][agent_name] = {
                "calls": metrics.get("total_calls", 0),
                "success_rate": metrics.get("success_rate", 0),
                "avg_duration_ms": metrics.get("average_duration_ms", 0)
            }
        
        return summary
    
    def archive_old_sessions(self, days_old: int = 30):
        """Archive sessions older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        archived_count = 0
        
        for session_id, info in list(self._index_cache.items()):
            created_at = datetime.fromisoformat(info["created_at"])
            if created_at < cutoff_date and info["status"] in ["completed", "failed"]:
                # Load and compress session
                session_path = Path(info["path"])
                if session_path.exists():
                    # Compress and move to archive
                    archive_path = self.archived_dir / f"{session_id}.json.gz"
                    
                    with open(session_path, 'rb') as f_in:
                        with gzip.open(archive_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Remove original
                    session_path.unlink()
                    
                    # Update index
                    del self._index_cache[session_id]
                    archived_count += 1
        
        print(f"Archived {archived_count} sessions")
        return archived_count
    
    def debug_session(self, session_id: str, breakpoint_agent: Optional[str] = None) -> Dict:
        """Debug a failed session"""
        session = self.load_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        debug_info = {
            "session_id": session_id,
            "status": session.metadata.status.value,
            "errors": session.errors,
            "last_successful_agent": None,
            "failure_point": None,
            "reasoning_before_failure": [],
            "checkpoints_available": len(session.checkpoints)
        }
        
        # Find failure point
        for i, entry in enumerate(session.entries):
            if isinstance(entry, dict):
                if entry.get("event_type") == "agent_complete" and entry.get("level") != "ERROR":
                    debug_info["last_successful_agent"] = entry.get("agent_name")
                elif entry.get("level") == "ERROR":
                    debug_info["failure_point"] = {
                        "agent": entry.get("agent_name"),
                        "message": entry.get("message"),
                        "reasoning": entry.get("reasoning")
                    }
                    
                    # Get reasoning entries before failure
                    for j in range(max(0, i-5), i):
                        if session.entries[j].get("reasoning"):
                            debug_info["reasoning_before_failure"].append(
                                session.entries[j].get("reasoning")
                            )
                    break
        
        return debug_info

# Example usage and testing
if __name__ == "__main__":
    # Create session manager
    manager = SessionManager()
    
    # Create a new session
    session = manager.create_session(
        project_type="web_app",
        requirements={"name": "TestApp", "features": ["auth", "api"]},
        tags=["test", "demo"]
    )
    
    print(f"Created session: {session.metadata.session_id}")
    
    # Add a checkpoint
    checkpoint = Checkpoint(
        name="phase_1_complete",
        timestamp=datetime.now().isoformat(),
        agent_name="project-architect",
        phase="planning",
        state={"status": "designed"},
        reasoning="Architecture design complete"
    )
    manager.add_checkpoint(session.metadata.session_id, checkpoint)
    
    # Complete the session
    manager.complete_session(session.metadata.session_id, success=True)
    
    # List sessions
    sessions = manager.list_sessions()
    print(f"\nFound {len(sessions)} sessions")
    
    # Get session summary
    summary = manager.get_session_summary(session.metadata.session_id)
    print(f"\nSession Summary: {json.dumps(summary, indent=2)}")