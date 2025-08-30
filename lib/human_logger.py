#!/usr/bin/env python3
"""
Human-Readable Logger - Generates concise markdown summaries of agent executions

Features:
- Markdown format for easy reading
- Key decisions and outputs only
- Agent handoff tracking
- File operation summaries
- Error resolution tracking
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

@dataclass
class AgentSummary:
    """Summary of a single agent's execution"""
    name: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "running"
    requirements: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    key_decisions: List[str] = field(default_factory=list)
    key_outputs: List[str] = field(default_factory=list)
    errors_resolved: List[str] = field(default_factory=list)
    handoff_to: List[str] = field(default_factory=list)
    artifacts_shared: List[str] = field(default_factory=list)
    
    def format_markdown(self) -> str:
        """Format agent summary as markdown"""
        status_icon = {
            "success": "[OK]",
            "failed": "[FAIL]",
            "running": "[RUN]",
            "skipped": "[SKIP]"
        }.get(self.status, "?")
        
        lines = []
        lines.append(f"### {self.name} [{self.start_time} - {self.end_time or 'running'}] {status_icon}")
        
        if self.requirements:
            lines.append(f"Requirements: {', '.join(self.requirements)}")
        
        if self.key_outputs:
            lines.append("Key Outputs:")
            for output in self.key_outputs[:5]:  # Limit to 5 most important
                lines.append(f"- {output}")
        
        if self.files_created:
            count = len(self.files_created)
            if count <= 3:
                lines.append(f"Files Created: {', '.join(self.files_created)}")
            else:
                lines.append(f"Files Created: {count} files ({', '.join(self.files_created[:3])}, ...)")
        
        if self.files_modified:
            count = len(self.files_modified)
            lines.append(f"Files Modified: {count}")
        
        if self.key_decisions:
            lines.append(f"Decision: {self.key_decisions[0]}")  # Show most important decision
        
        if self.errors_resolved:
            lines.append("Errors Resolved:")
            for error in self.errors_resolved[:3]:
                lines.append(f"- {error}")
        
        if self.handoff_to:
            lines.append(f"-> Handoff to: {', '.join(self.handoff_to)}")
        
        return "\n".join(lines)

class SummaryLevel(Enum):
    CONCISE = "concise"    # ~100 lines
    DETAILED = "detailed"  # ~200 lines
    VERBOSE = "verbose"    # ~500 lines

class HumanReadableLogger:
    """Generates human-readable markdown summaries of agent executions"""
    
    def __init__(self, session_id: str, log_dir: str = "./sessions", 
                 level: SummaryLevel = SummaryLevel.CONCISE):
        self.session_id = session_id
        self.log_dir = Path(log_dir)
        self.level = level
        
        # Create human-readable log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.summary_file = self.log_dir / f"session_{session_id}_{timestamp}_human.md"
        
        # Track agent summaries
        self.agents: Dict[str, AgentSummary] = {}
        self.current_agent: Optional[str] = None
        
        # Track overall metrics
        self.total_files_created: Set[str] = set()
        self.total_files_modified: Set[str] = set()
        self.total_errors: List[str] = []
        self.critical_decisions: List[tuple] = []  # (agent, decision)
        
        # Initialize the markdown file
        self._initialize_summary()
    
    def _initialize_summary(self):
        """Initialize the markdown summary file"""
        header = f"""# Agent Swarm Execution Summary

**Session ID:** {self.session_id}  
**Started:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Summary Level:** {self.level.value}

---

## Agent Execution Flow

"""
        self._write_to_file(header)
    
    def _write_to_file(self, content: str, append: bool = True):
        """Write content to the markdown file"""
        mode = 'a' if append else 'w'
        with open(self.summary_file, mode, encoding='utf-8') as f:
            f.write(content)
    
    def log_agent_start(self, agent_name: str, requirements: List[str] = None):
        """Log when an agent starts"""
        self.current_agent = agent_name
        self.agents[agent_name] = AgentSummary(
            name=agent_name,
            start_time=datetime.now().strftime('%H:%M:%S'),
            requirements=requirements or []
        )
        
        if self.level == SummaryLevel.VERBOSE:
            self._write_to_file(f"\n### {agent_name} [Started {self.agents[agent_name].start_time}]\n")
    
    def log_agent_complete(self, agent_name: str, success: bool, summary: str = None):
        """Log when an agent completes"""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            agent.end_time = datetime.now().strftime('%H:%M:%S')
            agent.status = "success" if success else "failed"
            
            # Write agent summary to file
            self._write_to_file(f"\n{agent.format_markdown()}\n")
    
    def log_file_operation(self, agent_name: str, operation: str, file_path: str):
        """Log file creation or modification"""
        if agent_name not in self.agents:
            return
        
        agent = self.agents[agent_name]
        clean_path = file_path.replace('\\', '/').replace('//', '/')
        
        if operation == "create":
            agent.files_created.append(clean_path)
            self.total_files_created.add(clean_path)
        elif operation == "modify":
            agent.files_modified.append(clean_path)
            self.total_files_modified.add(clean_path)
    
    def log_key_output(self, agent_name: str, output: str):
        """Log a key output or artifact from an agent"""
        if agent_name in self.agents:
            # Truncate long outputs
            if len(output) > 100:
                output = output[:97] + "..."
            self.agents[agent_name].key_outputs.append(output)
    
    def log_decision(self, agent_name: str, decision: str, critical: bool = False):
        """Log an important decision made by an agent"""
        if agent_name in self.agents:
            self.agents[agent_name].key_decisions.append(decision)
            if critical:
                self.critical_decisions.append((agent_name, decision))
    
    def log_error_resolution(self, agent_name: str, error: str, resolution: str):
        """Log how an error was resolved"""
        if agent_name in self.agents:
            self.agents[agent_name].errors_resolved.append(f"{error} -> {resolution}")
        self.total_errors.append(f"[{agent_name}] {error}")
    
    def log_handoff(self, from_agent: str, to_agents: List[str], artifacts: List[str] = None):
        """Log agent handoffs and communication"""
        if from_agent in self.agents:
            self.agents[from_agent].handoff_to = to_agents
            if artifacts:
                self.agents[from_agent].artifacts_shared = artifacts
    
    def log_requirement_complete(self, req_id: str, agent_name: str):
        """Log requirement completion"""
        if self.level in [SummaryLevel.DETAILED, SummaryLevel.VERBOSE]:
            self._write_to_file(f"- Requirement {req_id} completed by {agent_name}\n")
    
    def finalize_summary(self, overall_success: bool = True, stats: Dict = None):
        """Write final summary section"""
        summary = f"""
---

## Execution Summary

**Status:** {'SUCCESS' if overall_success else 'FAILED'}  
**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Agents Run:** {len(self.agents)}  
**Files Created:** {len(self.total_files_created)}  
**Files Modified:** {len(self.total_files_modified)}  

"""
        
        if self.critical_decisions and self.level != SummaryLevel.CONCISE:
            summary += "### Critical Decisions\n"
            for agent, decision in self.critical_decisions[:5]:
                summary += f"- [{agent}] {decision}\n"
            summary += "\n"
        
        if self.total_errors:
            summary += f"### Errors Encountered ({len(self.total_errors)})\n"
            for error in self.total_errors[:5]:
                summary += f"- {error}\n"
            summary += "\n"
        
        if stats:
            summary += "### Performance Metrics\n"
            if "total_duration" in stats:
                summary += f"- Total Duration: {stats['total_duration']}\n"
            if "success_rate" in stats:
                summary += f"- Success Rate: {stats['success_rate']:.1f}%\n"
            if "requirements_completed" in stats:
                summary += f"- Requirements Completed: {stats['requirements_completed']}\n"
        
        summary += f"\n---\n*Full logs available at: {self.summary_file.parent / f'session_{self.session_id}_*.json'}*\n"
        
        self._write_to_file(summary)
        
        return self.summary_file
    
    def get_summary_path(self) -> Path:
        """Get the path to the summary file"""
        return self.summary_file