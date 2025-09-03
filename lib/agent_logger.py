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
import re
from .human_logger import HumanReadableLogger, SummaryLevel

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

# Initialize console with Windows encoding fix
if Console:
    import sys
    import os
    
    # Detect if we're running in a subprocess or non-interactive environment
    # Rich console can hang in Windows subprocesses, so disable it in those cases
    is_subprocess = (
        # Check if we're not in a terminal
        not sys.stdout.isatty() or
        # Check for common subprocess indicators
        os.environ.get('DISABLE_RICH_CONSOLE') or
        # Check if we're being piped
        not sys.stderr.isatty()
    )
    
    if is_subprocess:
        # Disable Rich console to prevent hanging
        console = None
    else:
        try:
            # Force UTF-8 encoding on Windows to handle Unicode characters
            console = Console(
                file=sys.stdout,
                force_terminal=True,
                width=120,
                legacy_windows=False
            )
        except Exception:
            # If console creation fails, set to None
            console = None
    
    # Set console encoding to handle Unicode on Windows
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # Ignore encoding errors
else:
    console = None

def clean_unicode_for_windows(text: str) -> str:
    """Replace common Unicode characters with ASCII equivalents for Windows compatibility"""
    replacements = {
        '✅': '[OK]',
        '❌': '[FAIL]',
        '⚠️': '[WARN]', 
        '⚠': '[WARN]',
        '🔧': '[TOOL]',
        '📝': '[NOTE]',
        '✓': '[OK]',
        '✗': '[FAIL]',
        '→': '->',
        '⛓️': '[CHAIN]',
        '⏹️': '[STOP]',
        '▶': '>'
    }
    
    for unicode_char, ascii_replacement in replacements.items():
        text = text.replace(unicode_char, ascii_replacement)
    
    # Remove any remaining problematic Unicode characters
    text = re.sub(r'[^\x00-\x7F]+', '?', text)
    
    return text

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
    
    def __init__(self, session_id: Optional[str] = None, log_dir: str = "./sessions", 
                 enable_human_log: bool = True, summary_level: SummaryLevel = SummaryLevel.CONCISE):
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
        
        # Human-readable logger
        self.human_logger = None
        if enable_human_log:
            self.human_logger = HumanReadableLogger(
                self.session_id, 
                str(self.log_dir),
                summary_level
            )
        
        # Initialize session
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize a new logging session"""
        import sys
        
        session_info = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "log_file": str(self.session_file)
        }
        
        # Check if stdout is available
        if sys.stdout is None or (hasattr(sys.stdout, 'closed') and sys.stdout.closed):
            # Can't print anything, just return
            return
        
        # Try using Rich console, fallback to print if it fails
        try:
            if self.console and hasattr(self.console, 'file') and self.console.file and not self.console.file.closed:
                self.console.print(Panel(
                    f"[bold green]Session Started[/bold green]\n"
                    f"Session ID: {self.session_id}\n"
                    f"Log File: {self.session_file}",
                    title="Agent Logger",
                    border_style="green"
                ))
            else:
                # Fallback to standard print
                print(f"\n{'='*60}")
                print(f"Session Started")
                print(f"Session ID: {self.session_id}")
                print(f"Log File: {self.session_file}")
                print(f"{'='*60}\n")
        except (ValueError, AttributeError, OSError) as e:
            # If any error, try simple print
            try:
                print(f"\n{'='*60}")
                print(f"Session Started")
                print(f"Session ID: {self.session_id}")
                print(f"Log File: {self.session_file}")
                print(f"{'='*60}\n")
            except:
                # If even simple print fails, just continue silently
                pass
    
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
        
        # Log to human-readable logger
        if self.human_logger:
            # Extract requirements from context if available
            requirements = []
            if context:
                try:
                    import json
                    context_data = json.loads(context) if isinstance(context, str) else context
                    if isinstance(context_data, dict) and 'requirements' in context_data:
                        requirements = context_data['requirements']
                except:
                    pass
            self.human_logger.log_agent_start(agent_name, requirements)
        
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
        
        # Log to human-readable logger
        if self.human_logger:
            self.human_logger.log_agent_complete(agent_name, success, result[:200] if result else "")
        
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
        
        # Log file operations to human logger
        if self.human_logger and tool_name == "write_file" and parameters:
            file_path = parameters.get('file_path', '')
            if file_path:
                self.human_logger.log_file_operation(agent_name, "create", file_path)
                # Also log as key output
                self.human_logger.log_key_output(agent_name, f"Created: {file_path}")
        
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
            content = (
                f"[yellow][TOOL] Tool Call: {tool_name}[/yellow]\n"
                f"[bold]Reasoning:[/bold] {clean_unicode_for_windows(reasoning)}\n"
                f"[dim]Parameters:[/dim]\n{params_str}"
            )
            self.console.print(Panel(
                content,
                border_style="yellow"
            ))
    
    def log_reasoning(self, agent_name: str, reasoning: str, decision: Optional[str] = None):
        """Log agent reasoning and decision making"""
        # Clean reasoning to prevent loops (especially for DevOps-Engineer)
        if agent_name == "devops-engineer" and reasoning:
            # Deduplicate reasoning lines
            lines = reasoning.split('\n')
            unique_lines = []
            seen = set()
            for line in lines:
                line_stripped = line.strip()
                if line_stripped and line_stripped not in seen:
                    unique_lines.append(line)
                    seen.add(line_stripped)
                    if len(unique_lines) >= 5:  # Max 5 unique lines for DevOps
                        break
            reasoning = '\n'.join(unique_lines)
        
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
        
        # Log decision to human logger
        if self.human_logger and decision:
            # Mark as critical if it contains certain keywords
            critical = any(word in decision.lower() for word in ['architecture', 'security', 'oauth', 'database'])
            self.human_logger.log_decision(agent_name, decision, critical)
        
        if self.console:
            content = (
                f"[cyan][THINK] {agent_name} Thinking[/cyan]\n"
                f"[bold]Reasoning:[/bold] {clean_unicode_for_windows(reasoning)}\n"
                + (f"[bold green]Decision:[/bold green] {clean_unicode_for_windows(decision)}" if decision else "")
            )
            self.console.print(Panel(
                content,
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
        
        # Log error to human logger
        if self.human_logger:
            self.human_logger.log_error_resolution(agent_name, error[:100], "Attempting recovery")
        
        if self.console:
            content = (
                f"[bold red][ERROR] Error in {agent_name}[/bold red]\n"
                f"[red]{clean_unicode_for_windows(error)}[/red]\n"
                + (f"[dim]Reasoning: {clean_unicode_for_windows(reasoning)}[/dim]" if reasoning else "")
            )
            try:
                self.console.print(Panel(
                    content,
                    border_style="red"
                ))
                # Force flush to ensure output is written
                import sys
                sys.stdout.flush()
            except Exception as e:
                # Fallback to simple print if Rich has issues
                print(f"[ERROR] {agent_name}: {error}")
    
    def log_warning(self, agent_name: str, warning: str, reasoning: Optional[str] = None):
        """Log a warning with optional reasoning"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            agent_name=agent_name or self.current_agent,
            event_type=EventType.ERROR,  # Using ERROR event type but WARNING level
            level=LogLevel.WARNING,
            message=f"Warning in {agent_name}",
            reasoning=reasoning,
            data={"warning": warning}
        )
        
        self._add_entry(entry)
        
        # Log warning to human logger if it has the method
        if self.human_logger and hasattr(self.human_logger, 'log_warning'):
            self.human_logger.log_warning(agent_name or self.current_agent, warning)
        
        if self.console:
            content = (
                f"[bold yellow][WARN] Warning in {agent_name}[/bold yellow]\n"
                f"[yellow]{clean_unicode_for_windows(warning)}[/yellow]\n"
                + (f"[dim]Reasoning: {clean_unicode_for_windows(reasoning)}[/dim]" if reasoning else "")
            )
            try:
                self.console.print(Panel(
                    content,
                    border_style="yellow"
                ))
                # Force flush to ensure output is written
                import sys
                sys.stdout.flush()
            except Exception as e:
                # Fallback to simple print if Rich has issues
                print(f"[WARNING] {agent_name}: {warning}")
    
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
        
        # Finalize human-readable summary
        if self.human_logger:
            stats = {
                "total_duration": f"{sum(m.total_duration_ms for m in self.metrics.values()) / 1000:.1f}s",
                "success_rate": session_data['summary']['overall_success_rate'],
                "requirements_completed": len([e for e in self.entries if e.event_type == EventType.DECISION])
            }
            human_summary_file = self.human_logger.finalize_summary(
                overall_success=session_data['summary']['overall_success_rate'] > 90,
                stats=stats
            )
            if self.console:
                self.console.print(f"[dim]Human-readable summary: {human_summary_file}[/dim]")
        
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

def create_new_session(session_id: Optional[str] = None, 
                      enable_human_log: bool = True,
                      summary_level: SummaryLevel = SummaryLevel.CONCISE) -> ReasoningLogger:
    """Force creation of a new logger session"""
    global _logger_instance
    _logger_instance = ReasoningLogger(session_id, enable_human_log=enable_human_log, summary_level=summary_level)
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