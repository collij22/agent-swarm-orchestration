#!/usr/bin/env python3
"""
Observability Platform - Comprehensive monitoring and tracing system
Provides distributed tracing, centralized logging, anomaly detection, and insights
"""

import json
import time
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import traceback
from enum import Enum

# Try importing optional dependencies
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False
    print("Warning: OpenTelemetry not installed. Tracing features limited.")

try:
    import numpy as np
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Warning: scipy not installed. Anomaly detection will use basic methods.")

class LogLevel(Enum):
    """Log levels for centralized logging"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class TraceSpan:
    """Represents a span in distributed tracing"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict] = field(default_factory=list)
    status: str = "in_progress"
    error: Optional[str] = None
    
    def end(self, error: Optional[str] = None):
        """End the span and calculate duration"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = "error" if error else "success"
        self.error = error

@dataclass
class LogEntry:
    """Centralized log entry"""
    timestamp: float
    level: LogLevel
    message: str
    source: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    error_details: Optional[str] = None

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    timestamp: float
    metric_name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

@dataclass
class AnomalyEvent:
    """Detected anomaly event"""
    timestamp: float
    metric_name: str
    expected_value: float
    actual_value: float
    deviation: float
    severity: str  # low, medium, high, critical
    description: str
    context: Dict[str, Any] = field(default_factory=dict)

class ObservabilityPlatform:
    """
    Comprehensive observability platform for the agent swarm
    Features:
    - Distributed tracing (OpenTelemetry compatible)
    - Centralized logging
    - Real-time metrics and dashboards
    - Anomaly detection
    - Performance insights
    """
    
    def __init__(self, 
                 log_dir: str = "logs/observability",
                 metrics_retention_hours: int = 24,
                 enable_otel: bool = True,
                 otlp_endpoint: str = "localhost:4317"):
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Tracing
        self.traces: Dict[str, List[TraceSpan]] = defaultdict(list)
        self.active_spans: Dict[str, TraceSpan] = {}
        
        # Logging
        self.log_buffer: deque = deque(maxlen=10000)  # Keep last 10k logs in memory
        self.log_file = self.log_dir / f"central_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Metrics
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.metrics_retention = timedelta(hours=metrics_retention_hours)
        
        # Anomaly detection
        self.baseline_metrics: Dict[str, Dict] = {}  # Statistical baselines
        self.anomaly_history: List[AnomalyEvent] = []
        self.anomaly_thresholds = {
            "response_time": 2.0,  # 2x standard deviation
            "error_rate": 3.0,     # 3x standard deviation
            "cost": 2.5,           # 2.5x standard deviation
            "token_usage": 2.0     # 2x standard deviation
        }
        
        # Performance insights
        self.performance_summaries: Dict[str, Dict] = {}
        self.slow_operations: List[Dict] = []
        self.error_patterns: Dict[str, int] = defaultdict(int)
        
        # Dashboard data
        self.dashboard_metrics = {
            "total_traces": 0,
            "active_traces": 0,
            "total_logs": 0,
            "error_count": 0,
            "anomaly_count": 0,
            "avg_response_time": 0.0,
            "success_rate": 0.0
        }
        
        # OpenTelemetry setup
        self.tracer = None
        if enable_otel and HAS_OTEL:
            self._setup_opentelemetry(otlp_endpoint)
        
        # Start background tasks
        self._start_background_tasks()
    
    def _setup_opentelemetry(self, endpoint: str):
        """Setup OpenTelemetry tracing"""
        try:
            # Create tracer provider
            trace.set_tracer_provider(TracerProvider())
            
            # Configure OTLP exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=endpoint,
                insecure=True
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            
            print(f"OpenTelemetry tracing initialized with endpoint: {endpoint}")
            
        except Exception as e:
            print(f"Failed to setup OpenTelemetry: {e}")
            self.tracer = None
    
    def _start_background_tasks(self):
        """Start background processing tasks"""
        # Only start background tasks if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # Schedule periodic tasks
            asyncio.create_task(self._periodic_metrics_cleanup())
            asyncio.create_task(self._periodic_anomaly_detection())
            asyncio.create_task(self._periodic_dashboard_update())
        except RuntimeError:
            # No running event loop - skip background tasks for sync usage
            pass
    
    async def _periodic_metrics_cleanup(self):
        """Periodically clean up old metrics"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run hourly
                
                cutoff_time = time.time() - self.metrics_retention.total_seconds()
                
                for metric_name in list(self.metrics_buffer.keys()):
                    # Remove old metrics
                    while self.metrics_buffer[metric_name]:
                        if self.metrics_buffer[metric_name][0].timestamp < cutoff_time:
                            self.metrics_buffer[metric_name].popleft()
                        else:
                            break
                    
                    # Remove empty metric buffers
                    if not self.metrics_buffer[metric_name]:
                        del self.metrics_buffer[metric_name]
                        
            except Exception as e:
                self.log(LogLevel.ERROR, f"Error in metrics cleanup: {e}", "observability")
    
    async def _periodic_anomaly_detection(self):
        """Periodically run anomaly detection"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Detect anomalies in recent metrics
                for metric_name, metrics in self.metrics_buffer.items():
                    if len(metrics) > 10:  # Need enough data points
                        self._detect_anomalies(metric_name, list(metrics))
                        
            except Exception as e:
                self.log(LogLevel.ERROR, f"Error in anomaly detection: {e}", "observability")
    
    async def _periodic_dashboard_update(self):
        """Periodically update dashboard metrics"""
        while True:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                
                self._update_dashboard_metrics()
                
            except Exception as e:
                self.log(LogLevel.ERROR, f"Error updating dashboard: {e}", "observability")
    
    def start_trace(self, operation_name: str, tags: Dict[str, Any] = None) -> str:
        """
        Start a new trace
        
        Args:
            operation_name: Name of the operation
            tags: Optional tags for the trace
            
        Returns:
            Trace ID
        """
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=None,
            operation_name=operation_name,
            start_time=time.time(),
            tags=tags or {}
        )
        
        self.traces[trace_id].append(span)
        self.active_spans[span_id] = span
        
        # OpenTelemetry integration
        if self.tracer:
            otel_span = self.tracer.start_span(operation_name)
            if tags:
                for key, value in tags.items():
                    otel_span.set_attribute(key, str(value))
            span.tags["otel_span"] = otel_span
        
        self.dashboard_metrics["total_traces"] += 1
        self.dashboard_metrics["active_traces"] += 1
        
        return trace_id
    
    def start_span(self, trace_id: str, operation_name: str, 
                   parent_span_id: Optional[str] = None,
                   tags: Dict[str, Any] = None) -> str:
        """
        Start a new span within a trace
        
        Args:
            trace_id: ID of the parent trace
            operation_name: Name of the operation
            parent_span_id: Optional parent span ID
            tags: Optional tags for the span
            
        Returns:
            Span ID
        """
        span_id = str(uuid.uuid4())
        
        # Find parent span if not specified
        if not parent_span_id and trace_id in self.traces:
            # Use the most recent active span as parent
            for span in reversed(self.traces[trace_id]):
                if span.status == "in_progress":
                    parent_span_id = span.span_id
                    break
        
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=time.time(),
            tags=tags or {}
        )
        
        self.traces[trace_id].append(span)
        self.active_spans[span_id] = span
        
        # OpenTelemetry integration
        if self.tracer:
            parent_context = None
            if parent_span_id and parent_span_id in self.active_spans:
                parent_otel_span = self.active_spans[parent_span_id].tags.get("otel_span")
                if parent_otel_span:
                    parent_context = trace.set_span_in_context(parent_otel_span)
            
            otel_span = self.tracer.start_span(operation_name, context=parent_context)
            if tags:
                for key, value in tags.items():
                    otel_span.set_attribute(key, str(value))
            span.tags["otel_span"] = otel_span
        
        return span_id
    
    def end_span(self, span_id: str, error: Optional[str] = None, tags: Dict[str, Any] = None):
        """End a span"""
        if span_id in self.active_spans:
            span = self.active_spans[span_id]
            span.end(error)
            
            if tags:
                span.tags.update(tags)
            
            # OpenTelemetry integration
            if "otel_span" in span.tags:
                otel_span = span.tags["otel_span"]
                if error:
                    otel_span.record_exception(Exception(error))
                    otel_span.set_status(trace.Status(trace.StatusCode.ERROR, error))
                otel_span.end()
            
            # Track slow operations
            if span.duration > 10:  # Operations taking more than 10 seconds
                self.slow_operations.append({
                    "operation": span.operation_name,
                    "duration": span.duration,
                    "trace_id": span.trace_id,
                    "timestamp": span.start_time
                })
                
                # Keep only last 100 slow operations
                if len(self.slow_operations) > 100:
                    self.slow_operations = self.slow_operations[-100:]
            
            # Track error patterns
            if error:
                self.error_patterns[error[:100]] += 1  # Track first 100 chars of error
            
            del self.active_spans[span_id]
            
            # Update active traces count
            if not any(s.status == "in_progress" for s in self.traces[span.trace_id]):
                self.dashboard_metrics["active_traces"] -= 1
    
    def log(self, level: LogLevel, message: str, source: str,
            trace_id: Optional[str] = None, span_id: Optional[str] = None,
            context: Dict[str, Any] = None, error_details: Optional[str] = None):
        """
        Add a log entry to centralized logging
        
        Args:
            level: Log level
            message: Log message
            source: Source of the log (agent name, component, etc.)
            trace_id: Optional trace ID for correlation
            span_id: Optional span ID for correlation
            context: Additional context data
            error_details: Detailed error information (stack trace, etc.)
        """
        entry = LogEntry(
            timestamp=time.time(),
            level=level,
            message=message,
            source=source,
            trace_id=trace_id,
            span_id=span_id,
            context=context or {},
            error_details=error_details
        )
        
        # Add to memory buffer
        self.log_buffer.append(entry)
        
        # Write to file
        self._write_log_to_file(entry)
        
        # Add to span if available
        if span_id and span_id in self.active_spans:
            self.active_spans[span_id].logs.append({
                "timestamp": entry.timestamp,
                "level": entry.level.value,
                "message": entry.message
            })
        
        # Update dashboard metrics
        self.dashboard_metrics["total_logs"] += 1
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.dashboard_metrics["error_count"] += 1
    
    def _write_log_to_file(self, entry: LogEntry):
        """Write log entry to file"""
        try:
            log_line = {
                "timestamp": entry.timestamp,
                "datetime": datetime.fromtimestamp(entry.timestamp).isoformat(),
                "level": entry.level.value,
                "message": entry.message,
                "source": entry.source,
                "trace_id": entry.trace_id,
                "span_id": entry.span_id,
                "context": entry.context,
                "error_details": entry.error_details
            }
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_line) + "\n")
                
        except Exception as e:
            print(f"Failed to write log to file: {e}")
    
    def record_metric(self, metric_name: str, value: float, 
                     tags: Dict[str, str] = None, unit: str = ""):
        """
        Record a performance metric
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for the metric
            unit: Unit of measurement
        """
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_name=metric_name,
            value=value,
            tags=tags or {},
            unit=unit
        )
        
        self.metrics_buffer[metric_name].append(metric)
        
        # Update baseline for anomaly detection
        self._update_baseline(metric_name, value)
    
    def _update_baseline(self, metric_name: str, value: float):
        """Update statistical baseline for a metric"""
        if metric_name not in self.baseline_metrics:
            self.baseline_metrics[metric_name] = {
                "values": deque(maxlen=100),
                "mean": value,
                "std": 0,
                "min": value,
                "max": value
            }
        
        baseline = self.baseline_metrics[metric_name]
        baseline["values"].append(value)
        
        if len(baseline["values"]) > 1:
            baseline["mean"] = statistics.mean(baseline["values"])
            baseline["std"] = statistics.stdev(baseline["values"]) if len(baseline["values"]) > 1 else 0
            baseline["min"] = min(baseline["values"])
            baseline["max"] = max(baseline["values"])
    
    def _detect_anomalies(self, metric_name: str, metrics: List[PerformanceMetric]):
        """Detect anomalies in metrics"""
        if metric_name not in self.baseline_metrics:
            return
        
        baseline = self.baseline_metrics[metric_name]
        
        if baseline["std"] == 0:
            return  # No variation, can't detect anomalies
        
        # Get threshold for this metric type
        threshold = self.anomaly_thresholds.get(metric_name, 2.0)
        
        # Check recent metrics for anomalies
        recent_metrics = metrics[-10:]  # Check last 10 data points
        
        for metric in recent_metrics:
            # Calculate z-score
            z_score = abs((metric.value - baseline["mean"]) / baseline["std"]) if baseline["std"] > 0 else 0
            
            if z_score > threshold:
                # Anomaly detected
                severity = self._calculate_severity(z_score, threshold)
                
                anomaly = AnomalyEvent(
                    timestamp=metric.timestamp,
                    metric_name=metric_name,
                    expected_value=baseline["mean"],
                    actual_value=metric.value,
                    deviation=z_score,
                    severity=severity,
                    description=f"{metric_name} deviates significantly from baseline",
                    context={"tags": metric.tags, "unit": metric.unit}
                )
                
                # Check if we already reported this anomaly recently
                recent_anomalies = [
                    a for a in self.anomaly_history[-10:]
                    if a.metric_name == metric_name and 
                    abs(a.timestamp - anomaly.timestamp) < 60
                ]
                
                if not recent_anomalies:
                    self.anomaly_history.append(anomaly)
                    self.dashboard_metrics["anomaly_count"] += 1
                    
                    # Log the anomaly
                    self.log(
                        LogLevel.WARNING,
                        f"Anomaly detected in {metric_name}: {metric.value:.2f} (expected: {baseline['mean']:.2f})",
                        "anomaly_detector",
                        context={"severity": severity, "z_score": z_score}
                    )
    
    def _calculate_severity(self, z_score: float, threshold: float) -> str:
        """Calculate anomaly severity based on z-score"""
        if z_score > threshold * 3:
            return "critical"
        elif z_score > threshold * 2:
            return "high"
        elif z_score > threshold * 1.5:
            return "medium"
        else:
            return "low"
    
    def _update_dashboard_metrics(self):
        """Update dashboard metrics summary"""
        # Calculate success rate from recent traces
        recent_traces = []
        cutoff_time = time.time() - 3600  # Last hour
        
        for trace_id, spans in self.traces.items():
            if spans and spans[0].start_time > cutoff_time:
                recent_traces.extend(spans)
        
        if recent_traces:
            successful = sum(1 for s in recent_traces if s.status == "success")
            total = sum(1 for s in recent_traces if s.status in ["success", "error"])
            
            if total > 0:
                self.dashboard_metrics["success_rate"] = successful / total
            
            # Calculate average response time
            completed_spans = [s for s in recent_traces if s.duration is not None]
            if completed_spans:
                self.dashboard_metrics["avg_response_time"] = statistics.mean(s.duration for s in completed_spans)
    
    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """Get all spans for a trace"""
        return self.traces.get(trace_id, [])
    
    def get_recent_logs(self, count: int = 100, level: Optional[LogLevel] = None,
                       source: Optional[str] = None) -> List[LogEntry]:
        """Get recent log entries with optional filtering"""
        logs = list(self.log_buffer)
        
        # Apply filters
        if level:
            logs = [l for l in logs if l.level == level]
        if source:
            logs = [l for l in logs if l.source == source]
        
        # Return most recent
        return logs[-count:]
    
    def get_metrics_summary(self, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """Get summary statistics for metrics"""
        summary = {}
        
        metric_names = [metric_name] if metric_name else list(self.metrics_buffer.keys())
        
        for name in metric_names:
            if name in self.metrics_buffer and self.metrics_buffer[name]:
                values = [m.value for m in self.metrics_buffer[name]]
                
                summary[name] = {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1] if values else None
                }
        
        return summary
    
    def get_anomalies(self, limit: int = 50, severity: Optional[str] = None) -> List[AnomalyEvent]:
        """Get recent anomalies with optional severity filter"""
        anomalies = self.anomaly_history
        
        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]
        
        return anomalies[-limit:]
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get comprehensive performance insights"""
        insights = {
            "slow_operations": self.slow_operations[-20:],
            "error_patterns": dict(sorted(
                self.error_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            "dashboard_metrics": self.dashboard_metrics.copy(),
            "trace_statistics": {},
            "recommendations": []
        }
        
        # Analyze trace patterns
        if self.traces:
            all_spans = []
            for spans in self.traces.values():
                all_spans.extend(spans)
            
            if all_spans:
                # Group by operation
                operation_stats = defaultdict(list)
                for span in all_spans:
                    if span.duration:
                        operation_stats[span.operation_name].append(span.duration)
                
                # Calculate statistics per operation
                for op_name, durations in operation_stats.items():
                    insights["trace_statistics"][op_name] = {
                        "count": len(durations),
                        "avg_duration": statistics.mean(durations),
                        "p50": statistics.median(durations),
                        "p95": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0],
                        "p99": sorted(durations)[int(len(durations) * 0.99)] if len(durations) > 1 else durations[0]
                    }
        
        # Generate recommendations
        if insights["dashboard_metrics"]["success_rate"] < 0.9:
            insights["recommendations"].append({
                "type": "reliability",
                "message": f"Success rate is {insights['dashboard_metrics']['success_rate']:.1%}. Review error patterns and implement retry logic."
            })
        
        if insights["dashboard_metrics"]["avg_response_time"] > 10:
            insights["recommendations"].append({
                "type": "performance",
                "message": f"Average response time is {insights['dashboard_metrics']['avg_response_time']:.1f}s. Consider optimizing slow operations."
            })
        
        if len(self.anomaly_history) > 10:
            recent_anomalies = self.anomaly_history[-10:]
            critical_count = sum(1 for a in recent_anomalies if a.severity == "critical")
            if critical_count > 2:
                insights["recommendations"].append({
                    "type": "stability",
                    "message": f"{critical_count} critical anomalies detected recently. Investigate system stability."
                })
        
        return insights
    
    def export_traces(self, output_file: str, format: str = "json"):
        """Export traces to file for analysis"""
        output_path = Path(output_file)
        
        if format == "json":
            # Export as JSON
            export_data = {
                "traces": {},
                "metadata": {
                    "export_time": datetime.now().isoformat(),
                    "total_traces": len(self.traces),
                    "total_spans": sum(len(spans) for spans in self.traces.values())
                }
            }
            
            for trace_id, spans in self.traces.items():
                export_data["traces"][trace_id] = [
                    {
                        "span_id": s.span_id,
                        "parent_span_id": s.parent_span_id,
                        "operation": s.operation_name,
                        "start_time": s.start_time,
                        "end_time": s.end_time,
                        "duration": s.duration,
                        "status": s.status,
                        "error": s.error,
                        "tags": s.tags,
                        "logs": s.logs
                    }
                    for s in spans
                ]
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        elif format == "jaeger":
            # Export in Jaeger format (simplified)
            jaeger_data = {
                "data": []
            }
            
            for trace_id, spans in self.traces.items():
                trace_data = {
                    "traceID": trace_id,
                    "spans": [],
                    "processes": {
                        "p1": {
                            "serviceName": "agent-swarm",
                            "tags": []
                        }
                    }
                }
                
                for span in spans:
                    trace_data["spans"].append({
                        "traceID": trace_id,
                        "spanID": span.span_id,
                        "operationName": span.operation_name,
                        "references": [
                            {"refType": "CHILD_OF", "spanID": span.parent_span_id}
                        ] if span.parent_span_id else [],
                        "startTime": int(span.start_time * 1000000),  # Convert to microseconds
                        "duration": int((span.duration or 0) * 1000000),
                        "tags": [{"key": k, "value": str(v)} for k, v in span.tags.items()],
                        "logs": span.logs,
                        "processID": "p1"
                    })
                
                jaeger_data["data"].append(trace_data)
            
            with open(output_path, 'w') as f:
                json.dump(jaeger_data, f, indent=2)
        
        print(f"Traces exported to {output_path}")


# Example usage and testing
if __name__ == "__main__":
    import random
    
    async def demo():
        # Create observability platform
        platform = ObservabilityPlatform()
        
        # Simulate a workflow with tracing
        print("Starting workflow simulation...")
        
        # Start main trace
        trace_id = platform.start_trace("workflow_execution", {
            "workflow": "web_app",
            "requirements": 5
        })
        
        # Simulate agent executions
        agents = ["project-architect", "rapid-builder", "frontend-specialist", "quality-guardian"]
        
        for agent in agents:
            # Start agent span
            span_id = platform.start_span(trace_id, f"agent_{agent}", tags={
                "agent": agent,
                "model": "claude-sonnet-4"
            })
            
            # Log agent start
            platform.log(
                LogLevel.INFO,
                f"Starting agent {agent}",
                agent,
                trace_id=trace_id,
                span_id=span_id
            )
            
            # Simulate execution time
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Record metrics
            execution_time = random.uniform(50, 200)
            platform.record_metric("agent_execution_time", execution_time, 
                                 tags={"agent": agent}, unit="seconds")
            
            tokens = random.randint(1000, 10000)
            platform.record_metric("token_usage", tokens, 
                                 tags={"agent": agent}, unit="tokens")
            
            cost = tokens * 0.00002
            platform.record_metric("cost", cost, 
                                 tags={"agent": agent}, unit="dollars")
            
            # Simulate possible error
            error = None
            if random.random() < 0.1:  # 10% error rate
                error = "Agent execution failed"
                platform.log(
                    LogLevel.ERROR,
                    f"Agent {agent} failed",
                    agent,
                    trace_id=trace_id,
                    span_id=span_id,
                    error_details=traceback.format_exc()
                )
            
            # End agent span
            platform.end_span(span_id, error=error, tags={
                "tokens": tokens,
                "cost": cost
            })
            
            # Simulate anomaly
            if agent == "frontend-specialist":
                # Inject anomaly - very high token usage
                platform.record_metric("token_usage", 50000, 
                                     tags={"agent": agent}, unit="tokens")
        
        # Wait for background processing
        await asyncio.sleep(2)
        
        # Get insights
        print("\n=== Performance Insights ===")
        insights = platform.get_performance_insights()
        print(f"Dashboard Metrics: {json.dumps(insights['dashboard_metrics'], indent=2)}")
        print(f"Slow Operations: {len(insights['slow_operations'])}")
        print(f"Error Patterns: {list(insights['error_patterns'].keys())[:3]}")
        
        # Get metrics summary
        print("\n=== Metrics Summary ===")
        metrics_summary = platform.get_metrics_summary()
        for metric_name, stats in metrics_summary.items():
            print(f"{metric_name}: mean={stats['mean']:.2f}, std={stats['std']:.2f}")
        
        # Get anomalies
        print("\n=== Detected Anomalies ===")
        anomalies = platform.get_anomalies(limit=5)
        for anomaly in anomalies:
            print(f"- {anomaly.metric_name}: {anomaly.actual_value:.2f} "
                  f"(expected: {anomaly.expected_value:.2f}, severity: {anomaly.severity})")
        
        # Get recent logs
        print("\n=== Recent Error Logs ===")
        error_logs = platform.get_recent_logs(count=5, level=LogLevel.ERROR)
        for log_entry in error_logs:
            print(f"- [{log_entry.source}] {log_entry.message}")
        
        # Export traces
        platform.export_traces("traces_export.json", format="json")
        
        print("\n=== Recommendations ===")
        for rec in insights["recommendations"]:
            print(f"- [{rec['type']}] {rec['message']}")
    
    # Run demo
    asyncio.run(demo())