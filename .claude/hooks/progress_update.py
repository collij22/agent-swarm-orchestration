#!/usr/bin/env python3
"""
Progress Update Hook - Real-time progress reporting and tracking

Capabilities:
- Real-time progress reporting
- ETA calculations
- User notifications
- Dashboard updates
- Milestone tracking
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import sys

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.hook_manager import HookContext, HookEvent
from lib.agent_logger import get_logger


@dataclass
class ProgressState:
    """Progress tracking state"""
    total_tasks: int = 0
    completed_tasks: int = 0
    current_task: str = ""
    current_agent: str = ""
    start_time: float = field(default_factory=time.time)
    milestones_reached: List[str] = field(default_factory=list)
    task_times: Dict[str, float] = field(default_factory=dict)
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time
    
    def estimate_remaining_time(self) -> float:
        """Estimate remaining time based on average task time"""
        if self.completed_tasks == 0:
            return 0.0
        
        avg_time = self.elapsed_time / self.completed_tasks
        remaining_tasks = self.total_tasks - self.completed_tasks
        return avg_time * remaining_tasks


class ProgressUpdateHook:
    """Progress tracking and reporting hook"""
    
    def __init__(self):
        self.logger = get_logger()
        self.progress_state = ProgressState()
        self.last_update = 0
        self.update_interval = 10  # seconds
        self.milestones = [
            "requirements_complete",
            "architecture_defined",
            "implementation_started",
            "testing_phase",
            "deployment_ready"
        ]
    
    def __call__(self, context: HookContext) -> HookContext:
        """Execute progress update"""
        current_time = time.time()
        
        # Update progress state
        self._update_progress_state(context)
        
        # Check if it's time for an update
        if current_time - self.last_update >= self.update_interval:
            self._report_progress(context)
            self.last_update = current_time
        
        # Check for milestones
        self._check_milestones(context)
        
        # Calculate ETA
        eta = self._calculate_eta()
        context.set("eta_seconds", eta)
        
        # Add progress info to context
        context.set("progress", {
            "percent": self.progress_state.progress_percent,
            "completed": self.progress_state.completed_tasks,
            "total": self.progress_state.total_tasks,
            "current_task": self.progress_state.current_task,
            "eta": eta
        })
        
        return context
    
    def _update_progress_state(self, context: HookContext):
        """Update progress state from context"""
        # Update current task/agent
        if context.agent_name:
            self.progress_state.current_agent = context.agent_name
        
        if context.tool_name:
            self.progress_state.current_task = f"{context.agent_name}:{context.tool_name}"
        
        # Update task counts
        if context.event == HookEvent.AGENT_START:
            # Estimate total tasks if not set
            if self.progress_state.total_tasks == 0:
                # Rough estimate based on typical workflow
                self.progress_state.total_tasks = context.get("estimated_tasks", 10)
        
        elif context.event == HookEvent.AGENT_COMPLETE:
            self.progress_state.completed_tasks += 1
            
            # Track task completion time
            agent_name = context.agent_name
            if agent_name:
                task_time = context.get("execution_time", 0)
                self.progress_state.task_times[agent_name] = task_time
        
        # Update from metadata
        if "completed_tasks" in context.metadata:
            completed = context.metadata["completed_tasks"]
            if isinstance(completed, list):
                self.progress_state.completed_tasks = len(completed)
    
    def _report_progress(self, context: HookContext):
        """Report current progress"""
        state = self.progress_state
        
        # Create progress bar
        progress_bar = self._create_progress_bar(state.progress_percent)
        
        # Format time
        elapsed = timedelta(seconds=int(state.elapsed_time))
        eta = timedelta(seconds=int(state.estimate_remaining_time()))
        
        # Log progress
        self.logger.log_reasoning(
            "ProgressHook",
            f"Progress: {progress_bar} {state.progress_percent:.1f}% "
            f"({state.completed_tasks}/{state.total_tasks}) "
            f"Elapsed: {elapsed} ETA: {eta}"
        )
        
        # Log current task
        if state.current_task:
            self.logger.log_reasoning(
                "ProgressHook",
                f"Current: {state.current_task}"
            )
    
    def _check_milestones(self, context: HookContext):
        """Check for milestone completion"""
        phase = context.get("current_phase", "")
        
        for milestone in self.milestones:
            if milestone not in self.progress_state.milestones_reached:
                if self._is_milestone_reached(milestone, phase, context):
                    self.progress_state.milestones_reached.append(milestone)
                    
                    self.logger.log_reasoning(
                        "ProgressHook",
                        f"[MILESTONE] Milestone reached: {milestone}"
                    )
                    
                    # Fire milestone event
                    context.set("milestone", milestone)
                    context.set("milestone_reached", True)
    
    def _is_milestone_reached(self, milestone: str, phase: str, context: HookContext) -> bool:
        """Check if a specific milestone is reached"""
        phase_lower = phase.lower()
        
        if milestone == "requirements_complete":
            return "requirements" in context.get("completed_tasks", [])
        elif milestone == "architecture_defined":
            return "architect" in phase_lower or "architecture" in phase_lower
        elif milestone == "implementation_started":
            return "implementation" in phase_lower or "building" in phase_lower
        elif milestone == "testing_phase":
            return "test" in phase_lower or "quality" in phase_lower
        elif milestone == "deployment_ready":
            return "deploy" in phase_lower or "devops" in phase_lower
        
        return False
    
    def _calculate_eta(self) -> float:
        """Calculate estimated time to completion"""
        return self.progress_state.estimate_remaining_time()
    
    def _create_progress_bar(self, percent: float, width: int = 30) -> str:
        """Create a text progress bar"""
        filled = int(width * percent / 100)
        empty = width - filled
        return f"[{'=' * filled}{' ' * empty}]"


# Export the hook
progress_update_hook = ProgressUpdateHook()


def register(hook_manager):
    """Register this hook with the hook manager"""
    from lib.hook_manager import HookEvent
    
    # Register for multiple events
    events = [
        HookEvent.AGENT_START,
        HookEvent.AGENT_COMPLETE,
        HookEvent.PROGRESS_UPDATE,
        HookEvent.MILESTONE_REACHED
    ]
    
    for event in events:
        hook_manager.register_hook(
            name=f"progress_update_{event.value}",
            event_type=event,
            function=progress_update_hook,
            priority=70,
            config={
                "enabled": True,
                "update_interval": 10,
                "real_time_reporting": True
            }
        )