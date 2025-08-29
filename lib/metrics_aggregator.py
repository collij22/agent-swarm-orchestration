#!/usr/bin/env python3
"""
Metrics Aggregator - Aggregate and analyze metrics across multiple sessions

Features:
- Cross-session metrics aggregation
- Performance trend analysis
- Agent performance rankings
- Cost estimation and tracking
- Resource utilization analysis
"""

import json
import statistics
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
from enum import Enum

from session_manager import SessionManager, SessionData, SessionStatus

class AggregationPeriod(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"

class MetricType(Enum):
    EXECUTION_TIME = "execution_time"
    SUCCESS_RATE = "success_rate"
    API_CALLS = "api_calls"
    ERROR_RATE = "error_rate"
    COST = "cost"
    TOOL_USAGE = "tool_usage"

@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for a single agent across sessions"""
    agent_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration_ms: int = 0
    min_duration_ms: int = float('inf')
    max_duration_ms: int = 0
    tool_usage: Dict[str, int] = None
    error_types: Dict[str, int] = None
    
    def __post_init__(self):
        if self.tool_usage is None:
            self.tool_usage = {}
        if self.error_types is None:
            self.error_types = {}
    
    @property
    def average_duration_ms(self) -> float:
        return self.total_duration_ms / self.total_executions if self.total_executions > 0 else 0
    
    @property
    def success_rate(self) -> float:
        return (self.successful_executions / self.total_executions * 100) if self.total_executions > 0 else 0
    
    @property
    def error_rate(self) -> float:
        return (self.failed_executions / self.total_executions * 100) if self.total_executions > 0 else 0

@dataclass
class AggregatedMetrics:
    """Aggregated metrics across multiple sessions"""
    period: AggregationPeriod
    start_date: str
    end_date: str
    total_sessions: int = 0
    successful_sessions: int = 0
    failed_sessions: int = 0
    total_agents_used: int = 0
    total_api_calls: int = 0
    total_estimated_cost: float = 0.0
    average_session_duration_ms: float = 0.0
    agent_metrics: Dict[str, AgentPerformanceMetrics] = None
    project_type_distribution: Dict[str, int] = None
    error_distribution: Dict[str, int] = None
    hourly_distribution: Dict[int, int] = None  # Hour of day -> count
    
    def __post_init__(self):
        if self.agent_metrics is None:
            self.agent_metrics = {}
        if self.project_type_distribution is None:
            self.project_type_distribution = {}
        if self.error_distribution is None:
            self.error_distribution = {}
        if self.hourly_distribution is None:
            self.hourly_distribution = {i: 0 for i in range(24)}

class MetricsAggregator:
    """Aggregates metrics across multiple sessions"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.cache_dir = Path("./metrics_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Model pricing (example rates)
        self.model_pricing = {
            "claude-3-opus": {"input": 0.015, "output": 0.075},  # per 1K tokens
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
        }
    
    def aggregate_metrics(self,
                         period: AggregationPeriod = AggregationPeriod.DAILY,
                         date_from: Optional[datetime] = None,
                         date_to: Optional[datetime] = None,
                         project_type: Optional[str] = None) -> AggregatedMetrics:
        """Aggregate metrics for a specific period"""
        
        # Set default date range
        if not date_to:
            date_to = datetime.now()
        if not date_from:
            if period == AggregationPeriod.HOURLY:
                date_from = date_to - timedelta(hours=1)
            elif period == AggregationPeriod.DAILY:
                date_from = date_to - timedelta(days=1)
            elif period == AggregationPeriod.WEEKLY:
                date_from = date_to - timedelta(weeks=1)
            elif period == AggregationPeriod.MONTHLY:
                date_from = date_to - timedelta(days=30)
            else:  # ALL_TIME
                date_from = datetime(2020, 1, 1)
        
        # Get sessions in date range
        sessions = self.session_manager.list_sessions(
            project_type=project_type,
            date_from=date_from,
            date_to=date_to
        )
        
        # Initialize aggregated metrics
        aggregated = AggregatedMetrics(
            period=period,
            start_date=date_from.isoformat(),
            end_date=date_to.isoformat()
        )
        
        session_durations = []
        
        # Process each session
        for session_info in sessions:
            session = self.session_manager.load_session(session_info["session_id"])
            if not session:
                continue
            
            aggregated.total_sessions += 1
            
            # Session status
            if session.metadata.status == SessionStatus.COMPLETED:
                aggregated.successful_sessions += 1
            elif session.metadata.status == SessionStatus.FAILED:
                aggregated.failed_sessions += 1
            
            # Session duration
            if session.metadata.duration_ms:
                session_durations.append(session.metadata.duration_ms)
            
            # Project type distribution
            proj_type = session.metadata.project_type
            aggregated.project_type_distribution[proj_type] = \
                aggregated.project_type_distribution.get(proj_type, 0) + 1
            
            # Hourly distribution
            if session.metadata.created_at:
                hour = datetime.fromisoformat(session.metadata.created_at).hour
                aggregated.hourly_distribution[hour] += 1
            
            # API calls and cost
            aggregated.total_api_calls += session.api_calls.get("total", 0)
            aggregated.total_estimated_cost += session.api_calls.get("estimated_cost", 0)
            
            # Process agent metrics
            for agent_name, metrics in session.metrics.items():
                if agent_name not in aggregated.agent_metrics:
                    aggregated.agent_metrics[agent_name] = AgentPerformanceMetrics(agent_name)
                
                agent_perf = aggregated.agent_metrics[agent_name]
                agent_perf.total_executions += metrics.get("total_calls", 0)
                agent_perf.successful_executions += metrics.get("successful_calls", 0)
                agent_perf.failed_executions += metrics.get("failed_calls", 0)
                
                # Duration metrics
                avg_duration = metrics.get("average_duration_ms", 0)
                if avg_duration > 0:
                    agent_perf.total_duration_ms += avg_duration * metrics.get("total_calls", 1)
                    agent_perf.min_duration_ms = min(agent_perf.min_duration_ms, avg_duration)
                    agent_perf.max_duration_ms = max(agent_perf.max_duration_ms, avg_duration)
                
                # Tool usage
                for tool, count in metrics.get("tool_calls", {}).items():
                    agent_perf.tool_usage[tool] = agent_perf.tool_usage.get(tool, 0) + count
            
            # Process errors
            for error in session.errors:
                error_type = error.get("type", "Unknown")
                aggregated.error_distribution[error_type] = \
                    aggregated.error_distribution.get(error_type, 0) + 1
        
        # Calculate averages
        if session_durations:
            aggregated.average_session_duration_ms = statistics.mean(session_durations)
        
        aggregated.total_agents_used = len(aggregated.agent_metrics)
        
        return aggregated
    
    def get_agent_rankings(self, 
                          metric: MetricType = MetricType.SUCCESS_RATE,
                          top_n: int = 10) -> List[Tuple[str, float]]:
        """Get agent rankings by specified metric"""
        aggregated = self.aggregate_metrics(period=AggregationPeriod.ALL_TIME)
        
        rankings = []
        for agent_name, metrics in aggregated.agent_metrics.items():
            if metric == MetricType.SUCCESS_RATE:
                value = metrics.success_rate
            elif metric == MetricType.EXECUTION_TIME:
                value = metrics.average_duration_ms
            elif metric == MetricType.ERROR_RATE:
                value = metrics.error_rate
            else:
                value = 0
            
            rankings.append((agent_name, value))
        
        # Sort based on metric (ascending for time/error, descending for success)
        reverse = metric not in [MetricType.EXECUTION_TIME, MetricType.ERROR_RATE]
        rankings.sort(key=lambda x: x[1], reverse=reverse)
        
        return rankings[:top_n]
    
    def get_performance_trends(self,
                              agent_name: Optional[str] = None,
                              metric: MetricType = MetricType.SUCCESS_RATE,
                              periods: int = 7) -> List[Dict]:
        """Get performance trends over time"""
        trends = []
        
        for i in range(periods):
            date_to = datetime.now() - timedelta(days=i)
            date_from = date_to - timedelta(days=1)
            
            aggregated = self.aggregate_metrics(
                period=AggregationPeriod.DAILY,
                date_from=date_from,
                date_to=date_to
            )
            
            if agent_name and agent_name in aggregated.agent_metrics:
                agent_metrics = aggregated.agent_metrics[agent_name]
                if metric == MetricType.SUCCESS_RATE:
                    value = agent_metrics.success_rate
                elif metric == MetricType.EXECUTION_TIME:
                    value = agent_metrics.average_duration_ms
                else:
                    value = 0
            else:
                # Overall metrics
                if metric == MetricType.SUCCESS_RATE:
                    value = (aggregated.successful_sessions / aggregated.total_sessions * 100) \
                           if aggregated.total_sessions > 0 else 0
                elif metric == MetricType.API_CALLS:
                    value = aggregated.total_api_calls
                elif metric == MetricType.COST:
                    value = aggregated.total_estimated_cost
                else:
                    value = 0
            
            trends.append({
                "date": date_from.strftime("%Y-%m-%d"),
                "value": value
            })
        
        trends.reverse()  # Chronological order
        return trends
    
    def estimate_costs(self, 
                      date_from: Optional[datetime] = None,
                      date_to: Optional[datetime] = None) -> Dict:
        """Estimate API costs for sessions"""
        sessions = self.session_manager.list_sessions(
            date_from=date_from,
            date_to=date_to
        )
        
        total_cost = 0
        cost_by_model = defaultdict(float)
        cost_by_agent = defaultdict(float)
        
        for session_info in sessions:
            session = self.session_manager.load_session(session_info["session_id"])
            if not session:
                continue
            
            # Use stored cost if available
            if session.api_calls.get("estimated_cost"):
                total_cost += session.api_calls["estimated_cost"]
            
            # Break down by model
            for model, count in session.api_calls.get("by_model", {}).items():
                if model in self.model_pricing:
                    # Rough estimation (assuming average tokens)
                    estimated_tokens = count * 1000  # Assume 1K tokens per call
                    cost = (self.model_pricing[model]["input"] + 
                           self.model_pricing[model]["output"]) * count
                    cost_by_model[model] += cost
            
            # Break down by agent
            for agent_name, metrics in session.metrics.items():
                # Rough cost allocation based on execution time
                agent_ratio = metrics.get("total_calls", 0) / max(1, sum(
                    m.get("total_calls", 0) for m in session.metrics.values()
                ))
                cost_by_agent[agent_name] += session.api_calls.get("estimated_cost", 0) * agent_ratio
        
        return {
            "total_cost": total_cost,
            "cost_by_model": dict(cost_by_model),
            "cost_by_agent": dict(cost_by_agent),
            "average_cost_per_session": total_cost / len(sessions) if sessions else 0
        }
    
    def get_tool_usage_stats(self) -> Dict[str, int]:
        """Get overall tool usage statistics"""
        aggregated = self.aggregate_metrics(period=AggregationPeriod.ALL_TIME)
        
        tool_usage = defaultdict(int)
        for agent_metrics in aggregated.agent_metrics.values():
            for tool, count in agent_metrics.tool_usage.items():
                tool_usage[tool] += count
        
        # Sort by usage
        return dict(sorted(tool_usage.items(), key=lambda x: x[1], reverse=True))
    
    def get_error_analysis(self) -> Dict:
        """Analyze error patterns across sessions"""
        aggregated = self.aggregate_metrics(period=AggregationPeriod.ALL_TIME)
        
        error_analysis = {
            "total_errors": sum(aggregated.error_distribution.values()),
            "error_types": aggregated.error_distribution,
            "agents_with_highest_errors": [],
            "common_error_patterns": []
        }
        
        # Find agents with highest error rates
        agent_errors = []
        for agent_name, metrics in aggregated.agent_metrics.items():
            if metrics.failed_executions > 0:
                agent_errors.append((agent_name, metrics.error_rate, metrics.failed_executions))
        
        agent_errors.sort(key=lambda x: x[1], reverse=True)
        error_analysis["agents_with_highest_errors"] = [
            {"agent": name, "error_rate": rate, "failures": failures}
            for name, rate, failures in agent_errors[:5]
        ]
        
        # Find common error patterns
        if aggregated.error_distribution:
            sorted_errors = sorted(aggregated.error_distribution.items(), 
                                 key=lambda x: x[1], reverse=True)
            error_analysis["common_error_patterns"] = [
                {"type": error_type, "count": count}
                for error_type, count in sorted_errors[:5]
            ]
        
        return error_analysis
    
    def export_metrics(self, 
                      format: str = "json",
                      output_file: Optional[str] = None) -> str:
        """Export aggregated metrics"""
        aggregated = self.aggregate_metrics(period=AggregationPeriod.ALL_TIME)
        
        if format == "json":
            data = {
                "period": aggregated.period.value,
                "date_range": f"{aggregated.start_date} to {aggregated.end_date}",
                "summary": {
                    "total_sessions": aggregated.total_sessions,
                    "successful_sessions": aggregated.successful_sessions,
                    "failed_sessions": aggregated.failed_sessions,
                    "total_api_calls": aggregated.total_api_calls,
                    "total_estimated_cost": aggregated.total_estimated_cost,
                    "average_session_duration_ms": aggregated.average_session_duration_ms
                },
                "agent_metrics": {
                    name: {
                        "executions": metrics.total_executions,
                        "success_rate": metrics.success_rate,
                        "avg_duration_ms": metrics.average_duration_ms
                    }
                    for name, metrics in aggregated.agent_metrics.items()
                },
                "distributions": {
                    "project_types": aggregated.project_type_distribution,
                    "errors": aggregated.error_distribution,
                    "hourly": aggregated.hourly_distribution
                }
            }
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                return f"Metrics exported to {output_file}"
            else:
                return json.dumps(data, indent=2)
        
        elif format == "csv":
            # CSV export for spreadsheet analysis
            import csv
            rows = []
            
            for agent_name, metrics in aggregated.agent_metrics.items():
                rows.append({
                    "agent": agent_name,
                    "executions": metrics.total_executions,
                    "success_rate": metrics.success_rate,
                    "error_rate": metrics.error_rate,
                    "avg_duration_ms": metrics.average_duration_ms,
                    "min_duration_ms": metrics.min_duration_ms,
                    "max_duration_ms": metrics.max_duration_ms
                })
            
            if output_file:
                with open(output_file, 'w', newline='') as f:
                    if rows:
                        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)
                return f"Metrics exported to {output_file}"
            
        return "Export complete"

# Example usage
if __name__ == "__main__":
    from session_manager import SessionManager
    
    # Create managers
    session_manager = SessionManager()
    aggregator = MetricsAggregator(session_manager)
    
    # Aggregate metrics for the last day
    metrics = aggregator.aggregate_metrics(period=AggregationPeriod.DAILY)
    print(f"Daily Metrics Summary:")
    print(f"  Total Sessions: {metrics.total_sessions}")
    print(f"  Success Rate: {(metrics.successful_sessions/max(1, metrics.total_sessions)*100):.1f}%")
    print(f"  Total API Calls: {metrics.total_api_calls}")
    print(f"  Estimated Cost: ${metrics.total_estimated_cost:.2f}")
    
    # Get agent rankings
    rankings = aggregator.get_agent_rankings(metric=MetricType.SUCCESS_RATE)
    print(f"\nTop Agents by Success Rate:")
    for agent, rate in rankings[:5]:
        print(f"  {agent}: {rate:.1f}%")
    
    # Get performance trends
    trends = aggregator.get_performance_trends(periods=7)
    print(f"\nWeekly Performance Trend:")
    for trend in trends:
        print(f"  {trend['date']}: {trend['value']:.1f}%")
    
    # Get error analysis
    errors = aggregator.get_error_analysis()
    print(f"\nError Analysis:")
    print(f"  Total Errors: {errors['total_errors']}")
    if errors['common_error_patterns']:
        print(f"  Most Common Error: {errors['common_error_patterns'][0]}")