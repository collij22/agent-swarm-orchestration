#!/usr/bin/env python3
"""
Production Monitor
Real-time monitoring of agent execution, requirement coverage, errors, performance, and costs
"""

import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, deque
import statistics
from enum import Enum


class MetricType(Enum):
    """Types of metrics tracked"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class ExecutionMetric:
    """Individual execution metric"""
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    requirements_handled: List[str] = field(default_factory=list)
    files_created: int = 0
    api_calls: int = 0
    tokens_used: int = 0
    estimated_cost: float = 0.0
    retry_count: int = 0
    memory_usage_mb: float = 0.0
    
    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "agent_name": self.agent_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "error_message": self.error_message,
            "requirements_handled": self.requirements_handled,
            "files_created": self.files_created,
            "api_calls": self.api_calls,
            "tokens_used": self.tokens_used,
            "estimated_cost": self.estimated_cost,
            "retry_count": self.retry_count,
            "memory_usage_mb": self.memory_usage_mb
        }


@dataclass
class SystemMetrics:
    """System-wide metrics snapshot"""
    timestamp: datetime
    active_agents: int
    queued_tasks: int
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    api_rate_limit_remaining: int
    total_cost_today: float
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "active_agents": self.active_agents,
            "queued_tasks": self.queued_tasks,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_usage_percent": self.disk_usage_percent,
            "api_rate_limit_remaining": self.api_rate_limit_remaining,
            "total_cost_today": self.total_cost_today
        }


class ProductionMonitor:
    """
    Central monitoring system for production agent swarm
    """
    
    def __init__(self, 
                 metrics_dir: str = "metrics",
                 alert_thresholds: Optional[Dict] = None,
                 retention_days: int = 30):
        """
        Initialize production monitor
        
        Args:
            metrics_dir: Directory to store metrics
            alert_thresholds: Custom alert thresholds
            retention_days: How long to retain metrics
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(exist_ok=True)
        
        # Current executions
        self.active_executions: Dict[str, ExecutionMetric] = {}
        self.completed_executions: deque = deque(maxlen=1000)  # Keep last 1000
        
        # Aggregated metrics
        self.agent_metrics: Dict[str, Dict] = defaultdict(lambda: {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_duration": 0.0,
            "total_cost": 0.0,
            "total_api_calls": 0,
            "total_tokens": 0,
            "average_duration": 0.0,
            "success_rate": 0.0,
            "error_types": defaultdict(int)
        })
        
        # Requirement coverage
        self.requirement_coverage: Dict[str, Dict] = defaultdict(lambda: {
            "assigned_agents": [],
            "execution_count": 0,
            "completion_percentage": 0,
            "last_updated": None
        })
        
        # Error tracking
        self.error_registry: Dict[str, List] = defaultdict(list)
        self.error_patterns: Dict[str, int] = defaultdict(int)
        
        # Performance metrics (sliding window)
        self.performance_window = deque(maxlen=100)  # Last 100 executions
        
        # Cost tracking
        self.cost_tracker = {
            "hourly": deque(maxlen=24),  # Last 24 hours
            "daily": deque(maxlen=30),   # Last 30 days
            "total": 0.0
        }
        
        # Alert thresholds
        self.alert_thresholds = alert_thresholds or {
            "error_rate": 0.20,  # 20% error rate
            "avg_duration": 60.0,  # 60 seconds average
            "memory_percent": 80.0,  # 80% memory usage
            "cpu_percent": 90.0,  # 90% CPU usage
            "cost_per_hour": 10.0,  # $10/hour
            "api_rate_limit": 10  # 10 calls remaining
        }
        
        # System metrics history
        self.system_metrics_history = deque(maxlen=1000)
        
        # Alert history
        self.alerts_triggered: List[Dict] = []
        
        # Start time
        self.monitor_start_time = datetime.now()
        
        # Load historical metrics if available
        self._load_historical_metrics()
    
    def start_execution(self, agent_name: str, requirements: List[str] = None) -> str:
        """
        Record start of agent execution
        
        Returns:
            Execution ID for tracking
        """
        execution_id = f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        metric = ExecutionMetric(
            agent_name=agent_name,
            start_time=datetime.now(),
            requirements_handled=requirements or []
        )
        
        self.active_executions[execution_id] = metric
        
        # Update requirement coverage
        for req_id in (requirements or []):
            self.requirement_coverage[req_id]["execution_count"] += 1
            if agent_name not in self.requirement_coverage[req_id]["assigned_agents"]:
                self.requirement_coverage[req_id]["assigned_agents"].append(agent_name)
        
        return execution_id
    
    def end_execution(self, execution_id: str, success: bool, 
                     error_message: str = None, metrics: Dict = None):
        """
        Record end of agent execution
        
        Args:
            execution_id: ID returned from start_execution
            success: Whether execution was successful
            error_message: Error message if failed
            metrics: Additional metrics (files_created, api_calls, etc.)
        """
        if execution_id not in self.active_executions:
            return
        
        execution = self.active_executions[execution_id]
        execution.end_time = datetime.now()
        execution.success = success
        execution.error_message = error_message
        
        # Update with additional metrics
        if metrics:
            execution.files_created = metrics.get("files_created", 0)
            execution.api_calls = metrics.get("api_calls", 0)
            execution.tokens_used = metrics.get("tokens_used", 0)
            execution.estimated_cost = metrics.get("estimated_cost", 0.0)
            execution.retry_count = metrics.get("retry_count", 0)
            execution.memory_usage_mb = metrics.get("memory_usage_mb", 0.0)
        
        # Move to completed
        self.completed_executions.append(execution)
        del self.active_executions[execution_id]
        
        # Update agent metrics
        agent_metrics = self.agent_metrics[execution.agent_name]
        agent_metrics["total_executions"] += 1
        if success:
            agent_metrics["successful_executions"] += 1
        else:
            agent_metrics["failed_executions"] += 1
            if error_message:
                # Categorize error
                error_type = self._categorize_error(error_message)
                agent_metrics["error_types"][error_type] += 1
                self.error_registry[execution.agent_name].append({
                    "timestamp": execution.end_time,
                    "error": error_message,
                    "type": error_type
                })
        
        agent_metrics["total_duration"] += execution.duration_seconds
        agent_metrics["total_cost"] += execution.estimated_cost
        agent_metrics["total_api_calls"] += execution.api_calls
        agent_metrics["total_tokens"] += execution.tokens_used
        
        # Update averages
        total_execs = agent_metrics["total_executions"]
        agent_metrics["average_duration"] = agent_metrics["total_duration"] / total_execs
        agent_metrics["success_rate"] = agent_metrics["successful_executions"] / total_execs
        
        # Update performance window
        self.performance_window.append(execution)
        
        # Update cost tracking
        self.cost_tracker["total"] += execution.estimated_cost
        self._update_cost_windows(execution.estimated_cost)
        
        # Check for alerts
        self._check_alerts(execution)
    
    def update_requirement_coverage(self, requirement_id: str, 
                                   completion_percentage: int):
        """Update requirement completion percentage"""
        self.requirement_coverage[requirement_id]["completion_percentage"] = completion_percentage
        self.requirement_coverage[requirement_id]["last_updated"] = datetime.now()
    
    def record_system_metrics(self, active_agents: int = 0, queued_tasks: int = 0,
                            api_rate_limit_remaining: int = 100):
        """Record system-wide metrics"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_usage_percent = psutil.disk_usage('/').percent
        except ImportError:
            cpu_percent = 0.0
            memory_percent = 0.0
            disk_usage_percent = 0.0
        
        # Calculate today's cost
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_cost = sum(
            exec.estimated_cost for exec in self.completed_executions
            if exec.end_time and exec.end_time >= today_start
        )
        
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            active_agents=active_agents or len(self.active_executions),
            queued_tasks=queued_tasks,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage_percent=disk_usage_percent,
            api_rate_limit_remaining=api_rate_limit_remaining,
            total_cost_today=today_cost
        )
        
        self.system_metrics_history.append(metrics)
        
        # Check system-level alerts
        self._check_system_alerts(metrics)
        
        return metrics
    
    def get_agent_performance_report(self, agent_name: str = None) -> Dict:
        """Get performance report for specific agent or all agents"""
        if agent_name:
            return self.agent_metrics.get(agent_name, {})
        return dict(self.agent_metrics)
    
    def get_requirement_coverage_report(self) -> Dict:
        """Get requirement coverage report"""
        total_requirements = len(self.requirement_coverage)
        if total_requirements == 0:
            return {"total": 0, "average_completion": 0, "requirements": {}}
        
        total_completion = sum(
            req["completion_percentage"] 
            for req in self.requirement_coverage.values()
        )
        
        return {
            "total": total_requirements,
            "average_completion": total_completion / total_requirements,
            "requirements": dict(self.requirement_coverage)
        }
    
    def get_error_analysis(self, time_window_hours: int = 24) -> Dict:
        """Analyze errors in the specified time window"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        recent_errors = []
        error_counts = defaultdict(int)
        
        for agent, errors in self.error_registry.items():
            for error in errors:
                if error["timestamp"] >= cutoff_time:
                    recent_errors.append({
                        "agent": agent,
                        **error
                    })
                    error_counts[error["type"]] += 1
        
        return {
            "time_window_hours": time_window_hours,
            "total_errors": len(recent_errors),
            "error_types": dict(error_counts),
            "recent_errors": recent_errors[-10:],  # Last 10 errors
            "most_common_type": max(error_counts, key=error_counts.get) if error_counts else None
        }
    
    def get_performance_summary(self) -> Dict:
        """Get overall performance summary"""
        if not self.performance_window:
            return {
                "average_duration": 0,
                "success_rate": 0,
                "throughput_per_hour": 0
            }
        
        recent_executions = list(self.performance_window)
        durations = [e.duration_seconds for e in recent_executions]
        successes = sum(1 for e in recent_executions if e.success)
        
        # Calculate throughput
        if recent_executions:
            time_span = (recent_executions[-1].end_time - recent_executions[0].start_time).total_seconds()
            throughput = (len(recent_executions) / time_span) * 3600 if time_span > 0 else 0
        else:
            throughput = 0
        
        return {
            "average_duration": statistics.mean(durations) if durations else 0,
            "median_duration": statistics.median(durations) if durations else 0,
            "p95_duration": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "success_rate": (successes / len(recent_executions)) if recent_executions else 0,
            "throughput_per_hour": throughput,
            "total_executions": len(recent_executions)
        }
    
    def get_cost_analysis(self) -> Dict:
        """Get cost analysis"""
        # Current hour cost
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        hour_cost = sum(
            exec.estimated_cost for exec in self.completed_executions
            if exec.end_time and exec.end_time >= current_hour
        )
        
        # Projection based on current rate
        uptime_hours = (datetime.now() - self.monitor_start_time).total_seconds() / 3600
        if uptime_hours > 0:
            hourly_rate = self.cost_tracker["total"] / uptime_hours
            daily_projection = hourly_rate * 24
            monthly_projection = daily_projection * 30
        else:
            hourly_rate = daily_projection = monthly_projection = 0
        
        return {
            "current_hour": hour_cost,
            "today": self.cost_tracker.get("daily", [0])[-1] if self.cost_tracker.get("daily") else 0,
            "total": self.cost_tracker["total"],
            "hourly_rate": hourly_rate,
            "daily_projection": daily_projection,
            "monthly_projection": monthly_projection,
            "cost_per_agent": {
                agent: metrics["total_cost"]
                for agent, metrics in self.agent_metrics.items()
            }
        }
    
    def get_alerts(self, active_only: bool = True) -> List[Dict]:
        """Get triggered alerts"""
        if active_only:
            # Return alerts from last hour
            cutoff = datetime.now() - timedelta(hours=1)
            return [
                alert for alert in self.alerts_triggered
                if alert["timestamp"] >= cutoff
            ]
        return self.alerts_triggered
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.monitor_start_time).total_seconds(),
            "agent_performance": self.get_agent_performance_report(),
            "requirement_coverage": self.get_requirement_coverage_report(),
            "error_analysis": self.get_error_analysis(),
            "performance_summary": self.get_performance_summary(),
            "cost_analysis": self.get_cost_analysis(),
            "system_metrics": self.system_metrics_history[-1].to_dict() if self.system_metrics_history else None,
            "active_alerts": self.get_alerts(active_only=True)
        }
        
        if format == "json":
            return json.dumps(metrics, indent=2, default=str)
        elif format == "prometheus":
            return self._format_prometheus_metrics(metrics)
        else:
            return str(metrics)
    
    def save_metrics(self):
        """Save metrics to disk"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = self.metrics_dir / f"metrics_{timestamp}.json"
        
        with open(metrics_file, 'w') as f:
            f.write(self.export_metrics())
        
        # Cleanup old metrics
        self._cleanup_old_metrics()
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error type from message"""
        error_lower = error_message.lower()
        
        if "rate limit" in error_lower:
            return "rate_limit"
        elif "timeout" in error_lower:
            return "timeout"
        elif "connection" in error_lower or "network" in error_lower:
            return "network"
        elif "file not found" in error_lower or "no such file" in error_lower:
            return "file_not_found"
        elif "permission" in error_lower or "access denied" in error_lower:
            return "permission"
        elif "validation" in error_lower:
            return "validation"
        elif "memory" in error_lower or "resource" in error_lower:
            return "resource"
        else:
            return "unknown"
    
    def _update_cost_windows(self, cost: float):
        """Update cost tracking windows"""
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        current_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Update hourly
        if not self.cost_tracker["hourly"] or self.cost_tracker["hourly"][-1][0] != current_hour:
            self.cost_tracker["hourly"].append((current_hour, cost))
        else:
            self.cost_tracker["hourly"][-1] = (current_hour, self.cost_tracker["hourly"][-1][1] + cost)
        
        # Update daily
        if not self.cost_tracker["daily"] or self.cost_tracker["daily"][-1][0] != current_day:
            self.cost_tracker["daily"].append((current_day, cost))
        else:
            self.cost_tracker["daily"][-1] = (current_day, self.cost_tracker["daily"][-1][1] + cost)
    
    def _check_alerts(self, execution: ExecutionMetric):
        """Check if execution triggers any alerts"""
        alerts = []
        
        # Check agent-specific error rate
        agent_metrics = self.agent_metrics[execution.agent_name]
        if agent_metrics["total_executions"] >= 10:  # Need minimum executions
            error_rate = 1 - agent_metrics["success_rate"]
            if error_rate > self.alert_thresholds["error_rate"]:
                alerts.append({
                    "type": "high_error_rate",
                    "severity": "warning",
                    "agent": execution.agent_name,
                    "value": error_rate,
                    "threshold": self.alert_thresholds["error_rate"],
                    "message": f"Agent {execution.agent_name} error rate {error_rate:.1%} exceeds threshold"
                })
        
        # Check execution duration
        if execution.duration_seconds > self.alert_thresholds["avg_duration"]:
            alerts.append({
                "type": "slow_execution",
                "severity": "info",
                "agent": execution.agent_name,
                "value": execution.duration_seconds,
                "threshold": self.alert_thresholds["avg_duration"],
                "message": f"Agent {execution.agent_name} took {execution.duration_seconds:.1f}s to execute"
            })
        
        # Add alerts to history
        for alert in alerts:
            alert["timestamp"] = datetime.now()
            self.alerts_triggered.append(alert)
    
    def _check_system_alerts(self, metrics: SystemMetrics):
        """Check system-level alerts"""
        alerts = []
        
        # Memory alert
        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append({
                "type": "high_memory",
                "severity": "warning",
                "value": metrics.memory_percent,
                "threshold": self.alert_thresholds["memory_percent"],
                "message": f"Memory usage {metrics.memory_percent:.1f}% exceeds threshold"
            })
        
        # CPU alert
        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append({
                "type": "high_cpu",
                "severity": "warning",
                "value": metrics.cpu_percent,
                "threshold": self.alert_thresholds["cpu_percent"],
                "message": f"CPU usage {metrics.cpu_percent:.1f}% exceeds threshold"
            })
        
        # API rate limit alert
        if metrics.api_rate_limit_remaining < self.alert_thresholds["api_rate_limit"]:
            alerts.append({
                "type": "low_rate_limit",
                "severity": "critical",
                "value": metrics.api_rate_limit_remaining,
                "threshold": self.alert_thresholds["api_rate_limit"],
                "message": f"API rate limit down to {metrics.api_rate_limit_remaining} calls"
            })
        
        # Cost alert
        hour_cost = self.cost_tracker["hourly"][-1][1] if self.cost_tracker["hourly"] else 0
        if hour_cost > self.alert_thresholds["cost_per_hour"]:
            alerts.append({
                "type": "high_cost",
                "severity": "warning",
                "value": hour_cost,
                "threshold": self.alert_thresholds["cost_per_hour"],
                "message": f"Hourly cost ${hour_cost:.2f} exceeds threshold"
            })
        
        # Add alerts to history
        for alert in alerts:
            alert["timestamp"] = datetime.now()
            self.alerts_triggered.append(alert)
    
    def _format_prometheus_metrics(self, metrics: Dict) -> str:
        """Format metrics for Prometheus"""
        lines = []
        
        # Agent metrics
        for agent, agent_metrics in metrics["agent_performance"].items():
            safe_agent = agent.replace("-", "_")
            lines.append(f'agent_executions_total{{agent="{agent}"}} {agent_metrics["total_executions"]}')
            lines.append(f'agent_success_rate{{agent="{agent}"}} {agent_metrics["success_rate"]}')
            lines.append(f'agent_avg_duration_seconds{{agent="{agent}"}} {agent_metrics["average_duration"]}')
            lines.append(f'agent_total_cost_dollars{{agent="{agent}"}} {agent_metrics["total_cost"]}')
        
        # System metrics
        if metrics["system_metrics"]:
            sys = metrics["system_metrics"]
            lines.append(f'system_active_agents {sys["active_agents"]}')
            lines.append(f'system_queued_tasks {sys["queued_tasks"]}')
            lines.append(f'system_cpu_percent {sys["cpu_percent"]}')
            lines.append(f'system_memory_percent {sys["memory_percent"]}')
            lines.append(f'system_api_rate_limit_remaining {sys["api_rate_limit_remaining"]}')
        
        # Cost metrics
        cost = metrics["cost_analysis"]
        lines.append(f'cost_total_dollars {cost["total"]}')
        lines.append(f'cost_hourly_rate_dollars {cost["hourly_rate"]}')
        
        # Performance metrics
        perf = metrics["performance_summary"]
        lines.append(f'performance_avg_duration_seconds {perf["average_duration"]}')
        lines.append(f'performance_success_rate {perf["success_rate"]}')
        lines.append(f'performance_throughput_per_hour {perf["throughput_per_hour"]}')
        
        return "\n".join(lines)
    
    def _load_historical_metrics(self):
        """Load historical metrics from disk"""
        # Find most recent metrics file
        metrics_files = sorted(self.metrics_dir.glob("metrics_*.json"))
        if metrics_files:
            latest = metrics_files[-1]
            try:
                with open(latest, 'r') as f:
                    data = json.load(f)
                    # Restore cost tracker total
                    if "cost_analysis" in data:
                        self.cost_tracker["total"] = data["cost_analysis"].get("total", 0)
            except Exception as e:
                print(f"Failed to load historical metrics: {e}")
    
    def _cleanup_old_metrics(self, retention_days: int = 30):
        """Clean up metrics older than retention period"""
        cutoff = datetime.now() - timedelta(days=retention_days)
        
        for metrics_file in self.metrics_dir.glob("metrics_*.json"):
            # Parse timestamp from filename
            try:
                timestamp_str = metrics_file.stem.replace("metrics_", "")
                file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                if file_time < cutoff:
                    metrics_file.unlink()
            except:
                pass  # Skip files with unexpected names


# Example usage
if __name__ == "__main__":
    monitor = ProductionMonitor()
    
    # Simulate agent execution
    exec_id = monitor.start_execution("rapid-builder", ["REQ-001", "REQ-002"])
    time.sleep(2)
    monitor.end_execution(exec_id, True, metrics={
        "files_created": 5,
        "api_calls": 10,
        "tokens_used": 1500,
        "estimated_cost": 0.05
    })
    
    # Record system metrics
    monitor.record_system_metrics(active_agents=2, queued_tasks=5)
    
    # Get reports
    print("\nPerformance Summary:")
    print(json.dumps(monitor.get_performance_summary(), indent=2))
    
    print("\nCost Analysis:")
    print(json.dumps(monitor.get_cost_analysis(), indent=2))
    
    print("\nExporting metrics...")
    print(monitor.export_metrics()[:500])  # First 500 chars