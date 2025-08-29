#!/usr/bin/env python3
"""
Agent Logger - Comprehensive logging system for agent swarm with reasoning capture

Features:
- Reasoning capture for every agent decision
- Session tracking with unique IDs
- JSON export for analysis
- Rich console output with progress bars
- Webhook support for external monitoring
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.live import Live
    from rich.layout import Layout
    from rich.syntax import Syntax
except ImportError:
    print("Warning: Rich not installed. Install with: pip install rich")
    Console = None
    Panel = None

# Initialize console if available
console = Console() if Console else None

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class EventType(Enum):
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    REASONING = "reasoning"
    DECISION = "decision"
    ERROR = "error"
    CHECKPOINT = "checkpoint"
    PHASE_START = "phase_start"
    PHASE_COMPLETE = "phase_complete"

@dataclass
class LogEntry:
    """Single log entry with reasoning and metadata"""
    timestamp: str
    session_id: str
    agent_name: str
    event_type: EventType
    level: LogLevel
    message: str
    reasoning: Optional[str] = None
    data: Optional[Dict] = None
    duration_ms: Optional[int] = None
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "event_type": self.event_type.value,
            "level": self.level.value,
            "message": self.message,
            "reasoning": self.reasoning,
            "data": self.data,
            "duration_ms": self.duration_ms
        }

@dataclass
class AgentMetrics:
    """Performance metrics for an agent"""
    agent_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration_ms: int = 0
    tool_calls: Dict[str, int] = field(default_factory=dict)
    reasoning_entries: List[str] = field(default_factory=list)
    
    @property
    def average_duration_ms(self):
        return self.total_duration_ms / self.total_calls if self.total_calls > 0 else 0
    
    @property
    def success_rate(self):
        return (self.successful_calls / self.total_calls * 100) if self.total_calls > 0 else 0

class ReasoningLogger:
    """Main logger class with reasoning capture and rich output"""
    
    def __init__(self, session_id: Optional[str] = None, log_dir: str = "./sessions"):
        self.session_id = session_id or str(uuid.uuid4())
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.session_file = self.log_dir / f"session_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.entries: List[LogEntry] = []
        self.metrics: Dict[str, AgentMetrics] = {}
        self.current_agent: Optional[str] = None
        self.agent_start_times: Dict[str, float] = {}
        
        # Rich console components
        self.console = console
        self.progress = None
        self.current_task = None
        
        # Initialize session
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize a new logging session"""
        session_info = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "log_file": str(self.session_file)
        }
        
        if self.console:
            self.console.print(Panel(
                f"[bold green]Session Started[/bold green]\n"
                f"Session ID: {self.session_id}\n"
                f"Log File: {self.session_file}",
                title="Agent Logger",
                border_style="green"
            ))
    
    def log_agent_start(self, agent_name: str, context: str = "", reasoning: str = ""):
        """Log when an agent starts execution"""
        self.current_agent = agent_name
        self.agent_start_times[agent_name] = time.time()
        
        if agent_name not in self.metrics:
            self.metrics[agent_name] = AgentMetrics(agent_name)
        
        self.metrics[agent_name].total_calls += 1
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            agent_name=agent_name,
            event_type=EventType.AGENT_START,
            level=LogLevel.INFO,
            message=f"Agent {agent_name} started",
            reasoning=reasoning,
            data={"context": context}
        )
        
        self._add_entry(entry)
        
        if self.console:
            self.console.print(Panel(
                f"[bold blue]Starting: {agent_name}[/bold blue]\n"
                f"[dim]Reasoning: {reasoning}[/dim]\n"
                f"[dim]Context: {context[:100]}...[/dim]" if len(context) > 100 else f"[dim]Context: {context}[/dim]",
                title=f"Agent Execution",
                border_style="blue"
            ))
    
    def log_agent_complete(self, agent_name: str, success: bool = True, result: str = ""):
        """Log when an agent completes execution"""
        duration_ms = None
        if agent_name in self.agent_start_times:
            duration_ms = int((time.time() - self.agent_start_times[agent_name]) * 1000)
            self.metrics[agent_name].total_duration_ms += duration_ms
            
            if success:
                self.metrics[agent_name].successful_calls += 1
            else:
                self.metrics[agent_name].failed_calls += 1
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            agent_name=agent_name,
            event_type=EventType.AGENT_COMPLETE,
            level=LogLevel.INFO if success else LogLevel.ERROR,
            message=f"Agent {agent_name} {'completed' if success else 'failed'}",
            data={"success": success, "result": result},
            duration_ms=duration_ms
        )
        
        self._add_entry(entry)
        
        if self.console:
            status_icon = "[OK]" if success else "[FAIL]"
            status_color = "green" if success else "red"
            duration_str = f" ({duration_ms}ms)" if duration_ms else ""
            
            self.console.print(Panel(
                f"[bold {status_color}]{status_icon} {agent_name} {'Completed' if success else 'Failed'}{duration_str}[/bold {status_color}]\n"
                f"[dim]Result: {result[:200]}...[/dim]" if len(result) > 200 else f"[dim]Result: {result}[/dim]",
                border_style=status_color
            ))
    
    def log_tool_call(self, agent_name: str, tool_name: str, parameters: Dict, reasoning: str):
        """Log when an agent calls a tool"""
        if agent_name in self.metrics:
            if tool_name not in self.metrics[agent_name].tool_calls:
                self.metrics[agent_name].tool_calls[tool_name] = 0
            self.metrics[agent_name].tool_calls[tool_name] += 1
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            agent_name=agent_name,
            event_type=EventType.TOOL_CALL,
            level=LogLevel.INFO,
            message=f"Calling tool: {tool_name}",
            reasoning=reasoning,
            data={"tool": tool_name, "parameters": parameters}
        )
        
        self._add_entry(entry)
        
        if self.console:
            params_str = json.dumps(parameters, indent=2) if len(json.dumps(parameters)) < 200 else f"{json.dumps(parameters)[:200]}..."
            self.console.print(Panel(
                f"[yellow][TOOL] Tool Call: {tool_name}[/yellow]\n"
                f"[bold]Reasoning:[/bold] {reasoning}\n"
                f"[dim]Parameters:[/dim]\n{params_str}",
                border_style="yellow"
            ))
    
    def log_reasoning(self, agent_name: str, reasoning: str, decision: Optional[str] = None):
        """Log agent reasoning and decision making"""
        if agent_name in self.metrics:
            self.metrics[agent_name].reasoning_entries.append(reasoning)
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            agent_name=agent_name,
            event_type=EventType.REASONING if not decision else EventType.DECISION,
            level=LogLevel.INFO,
            message="Agent reasoning" if not decision else f"Decision: {decision}",
            reasoning=reasoning,
            data={"decision": decision} if decision else None
        )
        
        self._add_entry(entry)
        
        if self.console:
            self.console.print(Panel(
                f"[cyan][THINK] {agent_name} Thinking[/cyan]\n"
                f"[bold]Reasoning:[/bold] {reasoning}\n"
                + (f"[bold green]Decision:[/bold green] {decision}" if decision else ""),
                border_style="cyan"
            ))
    
    def log_error(self, agent_name: str, error: str, reasoning: Optional[str] = None):
        """Log an error with optional reasoning"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            agent_name=agent_name,
            event_type=EventType.ERROR,
            level=LogLevel.ERROR,
            message=f"Error in {agent_name}",
            reasoning=reasoning,
            data={"error": error}
        )
        
        self._add_entry(entry)
        
        if self.console:
            self.console.print(Panel(
                f"[bold red][ERROR] Error in {agent_name}[/bold red]\n"
                f"[red]{error}[/red]\n"
                + (f"[dim]Reasoning: {reasoning}[/dim]" if reasoning else ""),
                border_style="red"
            ))
    
    def log_phase(self, phase_name: str, agents: List[str], is_start: bool = True):
        """Log workflow phase start or completion"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            agent_name="orchestrator",
            event_type=EventType.PHASE_START if is_start else EventType.PHASE_COMPLETE,
            level=LogLevel.INFO,
            message=f"Phase {phase_name} {'started' if is_start else 'completed'}",
            data={"phase": phase_name, "agents": agents}
        )
        
        self._add_entry(entry)
        
        if self.console:
            icon = ">" if is_start else "[OK]"
            color = "blue" if is_start else "green"
            self.console.rule(f"[{color}]{icon} Phase: {phase_name} - Agents: {', '.join(agents)}[/{color}]")
    
    def _add_entry(self, entry: LogEntry):
        """Add entry to log and save to file"""
        self.entries.append(entry)
        self._save_entry(entry)
    
    def _save_entry(self, entry: LogEntry):
        """Append entry to session file"""
        with open(self.session_file, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')
    
    def get_metrics_summary(self) -> str:
        """Generate a summary of agent metrics"""
        if not self.metrics:
            return "No metrics available"
        
        if self.console:
            table = Table(title="Agent Performance Metrics")
            table.add_column("Agent", style="cyan")
            table.add_column("Calls", justify="right")
            table.add_column("Success Rate", justify="right")
            table.add_column("Avg Duration", justify="right")
            table.add_column("Tool Calls", justify="right")
            
            for agent_name, metrics in self.metrics.items():
                tool_calls_str = ", ".join([f"{t}:{c}" for t, c in metrics.tool_calls.items()][:3])
                table.add_row(
                    agent_name,
                    str(metrics.total_calls),
                    f"{metrics.success_rate:.1f}%",
                    f"{metrics.average_duration_ms:.0f}ms",
                    tool_calls_str or "-"
                )
            
            return table
        else:
            # Plain text summary
            lines = ["Agent Performance Metrics:"]
            for agent_name, metrics in self.metrics.items():
                lines.append(f"  {agent_name}: {metrics.total_calls} calls, "
                           f"{metrics.success_rate:.1f}% success, "
                           f"{metrics.average_duration_ms:.0f}ms avg")
            return "\n".join(lines)
    
    def export_session(self) -> Dict:
        """Export complete session data"""
        return {
            "session_id": self.session_id,
            "entries": [entry.to_dict() for entry in self.entries],
            "metrics": {
                name: {
                    "total_calls": m.total_calls,
                    "successful_calls": m.successful_calls,
                    "failed_calls": m.failed_calls,
                    "average_duration_ms": m.average_duration_ms,
                    "success_rate": m.success_rate,
                    "tool_calls": m.tool_calls
                }
                for name, m in self.metrics.items()
            },
            "summary": {
                "total_agents": len(self.metrics),
                "total_executions": sum(m.total_calls for m in self.metrics.values()),
                "overall_success_rate": (
                    sum(m.successful_calls for m in self.metrics.values()) /
                    sum(m.total_calls for m in self.metrics.values()) * 100
                ) if sum(m.total_calls for m in self.metrics.values()) > 0 else 0
            }
        }
    
    def close_session(self):
        """Close the logging session and display summary"""
        session_data = self.export_session()
        
        # Save complete session summary
        summary_file = self.session_file.with_suffix('.summary.json')
        with open(summary_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        if self.console:
            self.console.print(self.get_metrics_summary())
            self.console.print(Panel(
                f"[bold green]Session Complete[/bold green]\n"
                f"Session ID: {self.session_id}\n"
                f"Total Executions: {session_data['summary']['total_executions']}\n"
                f"Overall Success Rate: {session_data['summary']['overall_success_rate']:.1f}%\n"
                f"Logs: {self.session_file}\n"
                f"Summary: {summary_file}",
                title="Session Summary",
                border_style="green"
            ))

# Singleton instance for easy access
_logger_instance: Optional[ReasoningLogger] = None

def get_logger(session_id: Optional[str] = None) -> ReasoningLogger:
    """Get or create the singleton logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ReasoningLogger(session_id)
    return _logger_instance

def create_new_session(session_id: Optional[str] = None) -> ReasoningLogger:
    """Force creation of a new logger session"""
    global _logger_instance
    _logger_instance = ReasoningLogger(session_id)
    return _logger_instance

# Example usage
if __name__ == "__main__":
    # Demo the logger
    logger = create_new_session()
    
    # Simulate agent workflow
    logger.log_phase("Architecture", ["project-architect", "database-expert"], is_start=True)
    
    logger.log_agent_start("project-architect", "Design e-commerce platform", "Need to create scalable architecture")
    logger.log_reasoning("project-architect", "Analyzing requirements for high-traffic e-commerce", "Use microservices")
    logger.log_tool_call("project-architect", "create_diagram", {"type": "system", "components": 5}, "Need visual representation")
    logger.log_agent_complete("project-architect", True, "Architecture design complete")
    
    logger.log_agent_start("database-expert", "Design schema", "Need normalized database for products")
    logger.log_error("database-expert", "Connection timeout", "Database server not responding")
    logger.log_agent_complete("database-expert", False, "Failed to complete")
    
    logger.log_phase("Architecture", ["project-architect", "database-expert"], is_start=False)
    
    # Show final metrics
    logger.close_session()