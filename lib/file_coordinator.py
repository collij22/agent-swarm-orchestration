"""
File Coordinator - Manages file locking and prevents agent conflicts
This module ensures that multiple agents don't modify the same file simultaneously
"""

import threading
import time
from typing import Dict, Optional, Set, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import os

@dataclass
class FileLock:
    """Represents a lock on a file"""
    file_path: str
    agent_name: str
    locked_at: datetime
    lock_type: str = "exclusive"  # "exclusive" or "shared"
    
    def is_expired(self, timeout_seconds: int = 300) -> bool:
        """Check if lock has expired (default 5 minutes)"""
        elapsed = (datetime.now() - self.locked_at).total_seconds()
        return elapsed > timeout_seconds


@dataclass 
class FileModification:
    """Tracks a file modification by an agent"""
    file_path: str
    agent_name: str
    modified_at: datetime
    operation: str  # "create", "update", "delete"
    content_hash: Optional[str] = None


class FileCoordinator:
    """
    Coordinates file access between multiple agents to prevent conflicts.
    
    Features:
    - File locking with timeout
    - Shared vs exclusive locks
    - Modification tracking
    - Conflict detection
    - Wait queue for locked files
    """
    
    def __init__(self, lock_timeout: int = 300, enable_wait_queue: bool = True):
        """
        Initialize the file coordinator.
        
        Args:
            lock_timeout: Seconds before a lock expires (default 5 minutes)
            enable_wait_queue: Whether to queue agents waiting for locks
        """
        self.file_locks: Dict[str, FileLock] = {}
        self.file_owners: Dict[str, str] = {}  # file_path -> agent_name (primary owner)
        self.modifications: List[FileModification] = []
        self.wait_queue: Dict[str, List[str]] = {}  # file_path -> list of waiting agents
        self.lock_timeout = lock_timeout
        self.enable_wait_queue = enable_wait_queue
        self._lock = threading.Lock()  # Thread safety
        
        # Statistics
        self.stats = {
            "locks_acquired": 0,
            "locks_denied": 0,
            "locks_expired": 0,
            "conflicts_prevented": 0
        }
    
    def normalize_path(self, file_path: str) -> str:
        """Normalize file path for consistent comparison"""
        return str(Path(file_path).resolve()).lower()
    
    def acquire_lock(self, file_path: str, agent_name: str, 
                    lock_type: str = "exclusive", wait: bool = False) -> bool:
        """
        Attempt to acquire a lock on a file.
        
        Args:
            file_path: Path to the file to lock
            agent_name: Name of the agent requesting the lock
            lock_type: "exclusive" (write) or "shared" (read)
            wait: Whether to wait in queue if file is locked
            
        Returns:
            True if lock acquired, False otherwise
        """
        with self._lock:
            file_path = self.normalize_path(file_path)
            
            # Clean up expired locks
            self._cleanup_expired_locks()
            
            # Check if file is already locked
            if file_path in self.file_locks:
                existing_lock = self.file_locks[file_path]
                
                # Check if same agent already has the lock
                if existing_lock.agent_name == agent_name:
                    return True
                
                # Check if lock is expired
                if existing_lock.is_expired(self.lock_timeout):
                    self.stats["locks_expired"] += 1
                    del self.file_locks[file_path]
                else:
                    # File is locked by another agent
                    if lock_type == "shared" and existing_lock.lock_type == "shared":
                        # Multiple shared locks are allowed
                        return True
                    
                    # Add to wait queue if enabled
                    if wait and self.enable_wait_queue:
                        if file_path not in self.wait_queue:
                            self.wait_queue[file_path] = []
                        if agent_name not in self.wait_queue[file_path]:
                            self.wait_queue[file_path].append(agent_name)
                    
                    self.stats["locks_denied"] += 1
                    self.stats["conflicts_prevented"] += 1
                    return False
            
            # Acquire the lock
            self.file_locks[file_path] = FileLock(
                file_path=file_path,
                agent_name=agent_name,
                locked_at=datetime.now(),
                lock_type=lock_type
            )
            
            # Set primary owner if not set
            if file_path not in self.file_owners:
                self.file_owners[file_path] = agent_name
            
            self.stats["locks_acquired"] += 1
            return True
    
    def release_lock(self, file_path: str, agent_name: str) -> bool:
        """
        Release a lock on a file.
        
        Args:
            file_path: Path to the file to unlock
            agent_name: Name of the agent releasing the lock
            
        Returns:
            True if lock released, False if agent didn't own the lock
        """
        with self._lock:
            file_path = self.normalize_path(file_path)
            
            if file_path in self.file_locks:
                if self.file_locks[file_path].agent_name == agent_name:
                    del self.file_locks[file_path]
                    
                    # Process wait queue
                    if file_path in self.wait_queue and self.wait_queue[file_path]:
                        # Next agent in queue automatically gets the lock
                        next_agent = self.wait_queue[file_path].pop(0)
                        self.file_locks[file_path] = FileLock(
                            file_path=file_path,
                            agent_name=next_agent,
                            locked_at=datetime.now(),
                            lock_type="exclusive"
                        )
                        
                        if not self.wait_queue[file_path]:
                            del self.wait_queue[file_path]
                    
                    return True
            
            return False
    
    def track_modification(self, file_path: str, agent_name: str, 
                         operation: str, content_hash: Optional[str] = None):
        """
        Track a file modification by an agent.
        
        Args:
            file_path: Path to the modified file
            agent_name: Name of the agent that modified the file
            operation: Type of operation ("create", "update", "delete")
            content_hash: Optional hash of file content for conflict detection
        """
        with self._lock:
            file_path = self.normalize_path(file_path)
            
            modification = FileModification(
                file_path=file_path,
                agent_name=agent_name,
                modified_at=datetime.now(),
                operation=operation,
                content_hash=content_hash
            )
            
            self.modifications.append(modification)
    
    def get_file_owner(self, file_path: str) -> Optional[str]:
        """Get the primary owner (creator) of a file"""
        file_path = self.normalize_path(file_path)
        return self.file_owners.get(file_path)
    
    def is_file_locked(self, file_path: str) -> bool:
        """Check if a file is currently locked"""
        with self._lock:
            file_path = self.normalize_path(file_path)
            self._cleanup_expired_locks()
            return file_path in self.file_locks
    
    def get_lock_info(self, file_path: str) -> Optional[FileLock]:
        """Get information about a file lock"""
        with self._lock:
            file_path = self.normalize_path(file_path)
            return self.file_locks.get(file_path)
    
    def get_waiting_agents(self, file_path: str) -> List[str]:
        """Get list of agents waiting for a file lock"""
        with self._lock:
            file_path = self.normalize_path(file_path)
            return self.wait_queue.get(file_path, []).copy()
    
    def _cleanup_expired_locks(self):
        """Remove expired locks (internal use)"""
        expired = []
        for file_path, lock in self.file_locks.items():
            if lock.is_expired(self.lock_timeout):
                expired.append(file_path)
        
        for file_path in expired:
            del self.file_locks[file_path]
            self.stats["locks_expired"] += 1
    
    def get_agent_locks(self, agent_name: str) -> List[str]:
        """Get all files currently locked by an agent"""
        with self._lock:
            locked_files = []
            for file_path, lock in self.file_locks.items():
                if lock.agent_name == agent_name:
                    locked_files.append(file_path)
            return locked_files
    
    def release_all_agent_locks(self, agent_name: str) -> int:
        """Release all locks held by an agent (useful for cleanup)"""
        with self._lock:
            released = 0
            files_to_release = []
            
            for file_path, lock in self.file_locks.items():
                if lock.agent_name == agent_name:
                    files_to_release.append(file_path)
            
            for file_path in files_to_release:
                if self.release_lock(file_path, agent_name):
                    released += 1
            
            return released
    
    def get_modification_history(self, file_path: str) -> List[FileModification]:
        """Get modification history for a file"""
        with self._lock:
            file_path = self.normalize_path(file_path)
            return [m for m in self.modifications if m.file_path == file_path]
    
    def detect_conflicts(self, time_window_seconds: int = 60) -> List[Tuple[str, List[str]]]:
        """
        Detect potential conflicts (multiple agents modifying same file within time window).
        
        Returns:
            List of (file_path, [agent_names]) tuples
        """
        with self._lock:
            conflicts = {}
            current_time = datetime.now()
            
            for mod in self.modifications:
                elapsed = (current_time - mod.modified_at).total_seconds()
                if elapsed <= time_window_seconds:
                    if mod.file_path not in conflicts:
                        conflicts[mod.file_path] = set()
                    conflicts[mod.file_path].add(mod.agent_name)
            
            # Filter to only files modified by multiple agents
            return [(path, list(agents)) for path, agents in conflicts.items() 
                   if len(agents) > 1]
    
    def get_statistics(self) -> Dict:
        """Get coordinator statistics"""
        with self._lock:
            return {
                **self.stats,
                "active_locks": len(self.file_locks),
                "waiting_agents": sum(len(q) for q in self.wait_queue.values()),
                "tracked_modifications": len(self.modifications),
                "unique_files": len(set(m.file_path for m in self.modifications))
            }
    
    def save_state(self, file_path: str):
        """Save coordinator state to file for recovery"""
        with self._lock:
            state = {
                "file_locks": {
                    path: {
                        "agent_name": lock.agent_name,
                        "locked_at": lock.locked_at.isoformat(),
                        "lock_type": lock.lock_type
                    }
                    for path, lock in self.file_locks.items()
                },
                "file_owners": self.file_owners,
                "modifications": [
                    {
                        "file_path": mod.file_path,
                        "agent_name": mod.agent_name,
                        "modified_at": mod.modified_at.isoformat(),
                        "operation": mod.operation,
                        "content_hash": mod.content_hash
                    }
                    for mod in self.modifications
                ],
                "wait_queue": self.wait_queue,
                "stats": self.stats
            }
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(state, f, indent=2)
    
    def load_state(self, file_path: str) -> bool:
        """Load coordinator state from file"""
        if not os.path.exists(file_path):
            return False
        
        with self._lock:
            try:
                with open(file_path, 'r') as f:
                    state = json.load(f)
                
                # Restore file locks
                self.file_locks = {}
                for path, lock_data in state.get("file_locks", {}).items():
                    self.file_locks[path] = FileLock(
                        file_path=path,
                        agent_name=lock_data["agent_name"],
                        locked_at=datetime.fromisoformat(lock_data["locked_at"]),
                        lock_type=lock_data.get("lock_type", "exclusive")
                    )
                
                # Restore other state
                self.file_owners = state.get("file_owners", {})
                self.wait_queue = state.get("wait_queue", {})
                self.stats = state.get("stats", self.stats)
                
                # Restore modifications
                self.modifications = []
                for mod_data in state.get("modifications", []):
                    self.modifications.append(FileModification(
                        file_path=mod_data["file_path"],
                        agent_name=mod_data["agent_name"],
                        modified_at=datetime.fromisoformat(mod_data["modified_at"]),
                        operation=mod_data["operation"],
                        content_hash=mod_data.get("content_hash")
                    ))
                
                return True
            except Exception as e:
                print(f"Failed to load coordinator state: {e}")
                return False


# Global instance for sharing between agents
_global_coordinator = None

def get_file_coordinator() -> FileCoordinator:
    """Get or create the global file coordinator instance"""
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = FileCoordinator()
    return _global_coordinator