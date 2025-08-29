#!/usr/bin/env python3
"""
Performance Tracker - Real-time performance monitoring for agent swarm

Features:
- Real-time performance monitoring
- Resource usage tracking (memory, CPU)
- Execution time analysis
- Bottleneck detection
- Performance alerts
- Rate limiting management
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import deque, defaultdict
from enum import Enum
import json
import warnings

class PerformanceMetric(Enum):
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    API_CALLS = "api_calls"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    LATENCY = "latency"

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class PerformanceSnapshot:
    """A snapshot of performance metrics at a point in time"""
    timestamp: float
    memory_mb: float
    cpu_percent: float
    active_agents: int
    pending_tasks: int
    api_calls_per_minute: float
    average_latency_ms: float
    error_rate: float

@dataclass
class PerformanceAlert:
    """Performance alert"""
    timestamp: str
    severity: AlertSeverity
    metric: PerformanceMetric
    message: str
    value: float
    threshold: float

@dataclass
class AgentExecution:
    """Track individual agent execution"""
    agent_name: str
    start_time: float
    end_time: Optional[float] = None
    memory_start_mb: Optional[float] = None
    memory_end_mb: Optional[float] = None
    api_calls: int = 0
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0
    
    @property
    def memory_delta_mb(self) -> float:
        if self.memory_start_mb and self.memory_end_mb:
            return self.memory_end_mb - self.memory_start_mb
        return 0

class PerformanceTracker:
    """Real-time performance tracking for agent swarm"""
    
    def __init__(self, 
                 alert_callback: Optional[Callable[[PerformanceAlert], None]] = None,
                 snapshot_interval_seconds: int = 10):
        
        # Performance thresholds
        self.thresholds = {
            PerformanceMetric.EXECUTION_TIME: 30000,  # 30 seconds
            PerformanceMetric.MEMORY_USAGE: 1024,  # 1GB
            PerformanceMetric.CPU_USAGE: 80,  # 80%
            PerformanceMetric.API_CALLS: 100,  # per minute
            PerformanceMetric.ERROR_RATE: 5,  # 5%
            PerformanceMetric.LATENCY: 5000,  # 5 seconds
        }
        
        # Tracking data structures
        self.active_executions: Dict[str, AgentExecution] = {}
        self.completed_executions: deque = deque(maxlen=1000)
        self.performance_history: deque = deque(maxlen=360)  # 1 hour at 10s intervals
        self.alerts: deque = deque(maxlen=100)
        
        # API rate limiting
        self.api_calls_timestamps: deque = deque(maxlen=1000)
        self.api_limits = {
            "claude-3-opus": {"per_minute": 10, "per_hour": 100},
            "claude-3-sonnet": {"per_minute": 20, "per_hour": 200},
            "claude-3-haiku": {"per_minute": 50, "per_hour": 500},
        }
        
        # Statistics
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_api_calls": 0,
            "total_memory_used_mb": 0,
            "peak_memory_mb": 0,
            "peak_cpu_percent": 0,
        }
        
        # Bottleneck detection
        self.bottlenecks = defaultdict(list)
        
        # Alert callback
        self.alert_callback = alert_callback
        
        # Monitoring thread
        self.monitoring = False
        self.monitor_thread = None
        self.snapshot_interval = snapshot_interval_seconds
        
        # Process info
        self.process = psutil.Process()
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            snapshot = self.capture_snapshot()
            self.performance_history.append(snapshot)
            self.check_thresholds(snapshot)
            time.sleep(self.snapshot_interval)
    
    def capture_snapshot(self) -> PerformanceSnapshot:
        """Capture current performance snapshot"""
        # Memory usage
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # CPU usage
        cpu_percent = self.process.cpu_percent(interval=0.1)
        
        # Active agents
        active_agents = len(self.active_executions)
        
        # API calls per minute
        now = time.time()
        recent_api_calls = sum(1 for t in self.api_calls_timestamps if now - t < 60)
        
        # Average latency
        recent_executions = [e for e in self.completed_executions 
                           if hasattr(e, 'start_time') and now - e.start_time < 60]
        avg_latency = (
            sum(e.duration_ms for e in recent_executions) / len(recent_executions)
            if recent_executions else 0
        )
        
        # Error rate
        recent_errors = sum(1 for e in recent_executions if e.error)
        error_rate = (recent_errors / len(recent_executions) * 100) if recent_executions else 0
        
        # Update peak stats
        self.stats["peak_memory_mb"] = max(self.stats["peak_memory_mb"], memory_mb)
        self.stats["peak_cpu_percent"] = max(self.stats["peak_cpu_percent"], cpu_percent)
        
        return PerformanceSnapshot(
            timestamp=now,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            active_agents=active_agents,
            pending_tasks=0,  # Would need task queue integration
            api_calls_per_minute=recent_api_calls,
            average_latency_ms=avg_latency,
            error_rate=error_rate
        )
    
    def start_execution(self, agent_name: str) -> str:
        """Start tracking an agent execution"""
        execution_id = f"{agent_name}_{time.time()}"
        
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        execution = AgentExecution(
            agent_name=agent_name,
            start_time=time.time(),
            memory_start_mb=memory_mb
        )
        
        self.active_executions[execution_id] = execution
        self.stats["total_executions"] += 1
        
        return execution_id
    
    def end_execution(self, execution_id: str, success: bool = True, error: Optional[str] = None):
        """End tracking an agent execution"""
        if execution_id not in self.active_executions:
            return
        
        execution = self.active_executions[execution_id]
        execution.end_time = time.time()
        
        memory_info = self.process.memory_info()
        execution.memory_end_mb = memory_info.rss / 1024 / 1024
        
        if success:
            self.stats["successful_executions"] += 1
        else:
            self.stats["failed_executions"] += 1
            execution.error = error
        
        # Check for bottlenecks
        if execution.duration_ms > self.thresholds[PerformanceMetric.EXECUTION_TIME]:
            self.bottlenecks[execution.agent_name].append({
                "timestamp": datetime.now().isoformat(),
                "duration_ms": execution.duration_ms,
                "type": "slow_execution"
            })
        
        # Move to completed
        self.completed_executions.append(execution)
        del self.active_executions[execution_id]
    
    def track_api_call(self, model: str, tokens: int = 0) -> bool:
        """Track an API call and check rate limits"""
        now = time.time()
        self.api_calls_timestamps.append(now)
        self.stats["total_api_calls"] += 1
        
        # Check rate limits
        if model in self.api_limits:
            limits = self.api_limits[model]
            
            # Check per minute limit
            recent_minute = sum(1 for t in self.api_calls_timestamps if now - t < 60)
            if recent_minute > limits["per_minute"]:
                self._create_alert(
                    AlertSeverity.WARNING,
                    PerformanceMetric.API_CALLS,
                    f"API rate limit approaching for {model}",
                    recent_minute,
                    limits["per_minute"]
                )
                return False
            
            # Check per hour limit
            recent_hour = sum(1 for t in self.api_calls_timestamps if now - t < 3600)
            if recent_hour > limits["per_hour"]:
                self._create_alert(
                    AlertSeverity.CRITICAL,
                    PerformanceMetric.API_CALLS,
                    f"API rate limit exceeded for {model}",
                    recent_hour,
                    limits["per_hour"]
                )
                return False
        
        return True
    
    def check_thresholds(self, snapshot: PerformanceSnapshot):
        """Check if any thresholds are exceeded"""
        # Memory threshold
        if snapshot.memory_mb > self.thresholds[PerformanceMetric.MEMORY_USAGE]:
            self._create_alert(
                AlertSeverity.WARNING,
                PerformanceMetric.MEMORY_USAGE,
                f"High memory usage: {snapshot.memory_mb:.1f}MB",
                snapshot.memory_mb,
                self.thresholds[PerformanceMetric.MEMORY_USAGE]
            )
        
        # CPU threshold
        if snapshot.cpu_percent > self.thresholds[PerformanceMetric.CPU_USAGE]:
            self._create_alert(
                AlertSeverity.WARNING,
                PerformanceMetric.CPU_USAGE,
                f"High CPU usage: {snapshot.cpu_percent:.1f}%",
                snapshot.cpu_percent,
                self.thresholds[PerformanceMetric.CPU_USAGE]
            )
        
        # Latency threshold
        if snapshot.average_latency_ms > self.thresholds[PerformanceMetric.LATENCY]:
            self._create_alert(
                AlertSeverity.WARNING,
                PerformanceMetric.LATENCY,
                f"High latency: {snapshot.average_latency_ms:.1f}ms",
                snapshot.average_latency_ms,
                self.thresholds[PerformanceMetric.LATENCY]
            )
        
        # Error rate threshold
        if snapshot.error_rate > self.thresholds[PerformanceMetric.ERROR_RATE]:
            self._create_alert(
                AlertSeverity.CRITICAL,
                PerformanceMetric.ERROR_RATE,
                f"High error rate: {snapshot.error_rate:.1f}%",
                snapshot.error_rate,
                self.thresholds[PerformanceMetric.ERROR_RATE]
            )
    
    def _create_alert(self, 
                     severity: AlertSeverity,
                     metric: PerformanceMetric,
                     message: str,
                     value: float,
                     threshold: float):
        """Create and dispatch an alert"""
        alert = PerformanceAlert(
            timestamp=datetime.now().isoformat(),
            severity=severity,
            metric=metric,
            message=message,
            value=value,
            threshold=threshold
        )
        
        self.alerts.append(alert)
        
        if self.alert_callback:
            self.alert_callback(alert)
    
    def get_bottlenecks(self, top_n: int = 5) -> Dict[str, List]:
        """Get top bottlenecks"""
        # Sort agents by number of bottleneck incidents
        sorted_bottlenecks = sorted(
            self.bottlenecks.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        return dict(sorted_bottlenecks[:top_n])
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        recent_snapshots = list(self.performance_history)[-6:]  # Last minute
        
        if recent_snapshots:
            avg_memory = sum(s.memory_mb for s in recent_snapshots) / len(recent_snapshots)
            avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
            avg_latency = sum(s.average_latency_ms for s in recent_snapshots) / len(recent_snapshots)
        else:
            avg_memory = avg_cpu = avg_latency = 0
        
        return {
            "current": {
                "active_agents": len(self.active_executions),
                "memory_mb": self.process.memory_info().rss / 1024 / 1024,
                "cpu_percent": self.process.cpu_percent(interval=0.1),
            },
            "averages": {
                "memory_mb": avg_memory,
                "cpu_percent": avg_cpu,
                "latency_ms": avg_latency,
            },
            "peaks": {
                "memory_mb": self.stats["peak_memory_mb"],
                "cpu_percent": self.stats["peak_cpu_percent"],
            },
            "totals": {
                "executions": self.stats["total_executions"],
                "successful": self.stats["successful_executions"],
                "failed": self.stats["failed_executions"],
                "api_calls": self.stats["total_api_calls"],
            },
            "success_rate": (
                self.stats["successful_executions"] / self.stats["total_executions"] * 100
                if self.stats["total_executions"] > 0 else 0
            ),
            "recent_alerts": len([a for a in self.alerts if a.severity == AlertSeverity.CRITICAL])
        }
    
    def predict_resource_needs(self, planned_agents: List[str]) -> Dict:
        """Predict resource needs for planned agent executions"""
        predictions = {
            "estimated_memory_mb": 0,
            "estimated_duration_ms": 0,
            "estimated_api_calls": 0,
            "warnings": []
        }
        
        # Calculate averages per agent
        agent_stats = defaultdict(lambda: {"count": 0, "total_duration": 0, "total_memory": 0})
        
        for execution in self.completed_executions:
            if hasattr(execution, 'agent_name'):
                stats = agent_stats[execution.agent_name]
                stats["count"] += 1
                stats["total_duration"] += execution.duration_ms
                stats["total_memory"] += execution.memory_delta_mb
        
        # Predict based on historical data
        for agent in planned_agents:
            if agent in agent_stats and agent_stats[agent]["count"] > 0:
                stats = agent_stats[agent]
                avg_duration = stats["total_duration"] / stats["count"]
                avg_memory = stats["total_memory"] / stats["count"]
                
                predictions["estimated_duration_ms"] += avg_duration
                predictions["estimated_memory_mb"] += avg_memory
                predictions["estimated_api_calls"] += 1  # Rough estimate
                
                # Check if this agent is a known bottleneck
                if agent in self.bottlenecks:
                    predictions["warnings"].append(f"{agent} has performance issues")
        
        # Check if predicted resources exceed thresholds
        current_memory = self.process.memory_info().rss / 1024 / 1024
        predicted_total_memory = current_memory + predictions["estimated_memory_mb"]
        
        if predicted_total_memory > self.thresholds[PerformanceMetric.MEMORY_USAGE]:
            predictions["warnings"].append(
                f"Predicted memory usage ({predicted_total_memory:.1f}MB) exceeds threshold"
            )
        
        return predictions
    
    def export_performance_data(self, output_file: str):
        """Export performance data for analysis"""
        data = {
            "summary": self.get_performance_summary(),
            "bottlenecks": self.get_bottlenecks(),
            "alerts": [
                {
                    "timestamp": alert.timestamp,
                    "severity": alert.severity.value,
                    "metric": alert.metric.value,
                    "message": alert.message,
                    "value": alert.value,
                    "threshold": alert.threshold
                }
                for alert in self.alerts
            ],
            "history": [
                {
                    "timestamp": snapshot.timestamp,
                    "memory_mb": snapshot.memory_mb,
                    "cpu_percent": snapshot.cpu_percent,
                    "active_agents": snapshot.active_agents,
                    "api_calls_per_minute": snapshot.api_calls_per_minute,
                    "average_latency_ms": snapshot.average_latency_ms,
                    "error_rate": snapshot.error_rate
                }
                for snapshot in self.performance_history
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return f"Performance data exported to {output_file}"

# Context manager for tracking execution
class track_execution:
    """Context manager for tracking agent execution"""
    
    def __init__(self, tracker: PerformanceTracker, agent_name: str):
        self.tracker = tracker
        self.agent_name = agent_name
        self.execution_id = None
    
    def __enter__(self):
        self.execution_id = self.tracker.start_execution(self.agent_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        error = str(exc_val) if exc_val else None
        self.tracker.end_execution(self.execution_id, success, error)

# Example usage
if __name__ == "__main__":
    def alert_handler(alert: PerformanceAlert):
        print(f"[{alert.severity.value.upper()}] {alert.message}")
    
    # Create tracker
    tracker = PerformanceTracker(alert_callback=alert_handler)
    tracker.start_monitoring()
    
    # Simulate agent execution
    with track_execution(tracker, "test-agent"):
        time.sleep(1)  # Simulate work
        tracker.track_api_call("claude-3-sonnet", tokens=1000)
    
    # Get performance summary
    summary = tracker.get_performance_summary()
    print(f"\nPerformance Summary:")
    print(f"  Active Agents: {summary['current']['active_agents']}")
    print(f"  Memory Usage: {summary['current']['memory_mb']:.1f}MB")
    print(f"  CPU Usage: {summary['current']['cpu_percent']:.1f}%")
    print(f"  Success Rate: {summary['success_rate']:.1f}%")
    
    # Predict resource needs
    predictions = tracker.predict_resource_needs(["agent1", "agent2"])
    print(f"\nResource Predictions:")
    print(f"  Estimated Duration: {predictions['estimated_duration_ms']:.1f}ms")
    print(f"  Estimated Memory: {predictions['estimated_memory_mb']:.1f}MB")
    
    tracker.stop_monitoring()