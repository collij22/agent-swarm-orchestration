#!/usr/bin/env python3
"""
Metrics Exporter
Exports metrics from ProductionMonitor to Prometheus/Grafana and other monitoring systems
"""

import json
import time
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse


class PrometheusMetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint"""
    
    def do_GET(self):
        """Handle GET requests for metrics"""
        if self.path == '/metrics':
            # Get metrics from the exporter
            if hasattr(self.server, 'metrics_exporter'):
                metrics = self.server.metrics_exporter.get_prometheus_metrics()
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; version=0.0.4')
                self.end_headers()
                self.wfile.write(metrics.encode())
            else:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Metrics exporter not configured")
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


class MetricsExporter:
    """
    Exports metrics to various monitoring systems
    """
    
    def __init__(self, production_monitor=None, port: int = 9090):
        """
        Initialize metrics exporter
        
        Args:
            production_monitor: ProductionMonitor instance
            port: Port for Prometheus metrics endpoint
        """
        self.monitor = production_monitor
        self.port = port
        self.server = None
        self.server_thread = None
        
        # Metric definitions for Prometheus
        self.metric_definitions = {
            # Agent metrics
            "agent_executions_total": {
                "type": "counter",
                "help": "Total number of agent executions",
                "labels": ["agent", "status"]
            },
            "agent_duration_seconds": {
                "type": "histogram",
                "help": "Agent execution duration in seconds",
                "labels": ["agent"],
                "buckets": [1, 5, 10, 30, 60, 120, 300, 600]
            },
            "agent_success_rate": {
                "type": "gauge",
                "help": "Agent success rate (0-1)",
                "labels": ["agent"]
            },
            "agent_api_calls_total": {
                "type": "counter",
                "help": "Total API calls made by agent",
                "labels": ["agent"]
            },
            "agent_tokens_used_total": {
                "type": "counter",
                "help": "Total tokens used by agent",
                "labels": ["agent"]
            },
            "agent_cost_dollars_total": {
                "type": "counter",
                "help": "Total cost in dollars for agent",
                "labels": ["agent"]
            },
            
            # Requirement metrics
            "requirement_completion_percent": {
                "type": "gauge",
                "help": "Requirement completion percentage",
                "labels": ["requirement_id"]
            },
            "requirement_executions_total": {
                "type": "counter",
                "help": "Total executions for requirement",
                "labels": ["requirement_id"]
            },
            
            # System metrics
            "system_active_agents": {
                "type": "gauge",
                "help": "Number of currently active agents"
            },
            "system_queued_tasks": {
                "type": "gauge",
                "help": "Number of queued tasks"
            },
            "system_cpu_percent": {
                "type": "gauge",
                "help": "System CPU usage percentage"
            },
            "system_memory_percent": {
                "type": "gauge",
                "help": "System memory usage percentage"
            },
            "system_disk_percent": {
                "type": "gauge",
                "help": "System disk usage percentage"
            },
            "system_api_rate_limit_remaining": {
                "type": "gauge",
                "help": "Remaining API rate limit calls"
            },
            
            # Cost metrics
            "cost_total_dollars": {
                "type": "counter",
                "help": "Total cost in dollars"
            },
            "cost_hourly_rate_dollars": {
                "type": "gauge",
                "help": "Current hourly cost rate in dollars"
            },
            "cost_daily_total_dollars": {
                "type": "gauge",
                "help": "Total cost today in dollars"
            },
            
            # Error metrics
            "errors_total": {
                "type": "counter",
                "help": "Total number of errors",
                "labels": ["agent", "error_type"]
            },
            "error_rate": {
                "type": "gauge",
                "help": "Current error rate (errors per hour)"
            },
            
            # Performance metrics
            "throughput_per_hour": {
                "type": "gauge",
                "help": "Agent executions per hour"
            },
            "avg_response_time_seconds": {
                "type": "gauge",
                "help": "Average response time in seconds"
            },
            
            # Alert metrics
            "alerts_active": {
                "type": "gauge",
                "help": "Number of active alerts",
                "labels": ["severity"]
            }
        }
        
        # Grafana dashboard configuration
        self.grafana_config = None
    
    def start_prometheus_server(self):
        """Start HTTP server for Prometheus metrics"""
        if self.server:
            return  # Already running
        
        self.server = HTTPServer(('', self.port), PrometheusMetricsHandler)
        self.server.metrics_exporter = self
        
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"📊 Prometheus metrics endpoint started on port {self.port}")
        print(f"   Access metrics at: http://localhost:{self.port}/metrics")
    
    def stop_prometheus_server(self):
        """Stop the Prometheus server"""
        if self.server:
            self.server.shutdown()
            self.server_thread.join()
            self.server = None
            print("Prometheus metrics endpoint stopped")
    
    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus format metrics"""
        if not self.monitor:
            return "# No monitor configured\n"
        
        lines = []
        timestamp = int(time.time() * 1000)  # Prometheus uses millisecond timestamps
        
        # Get current metrics from monitor
        agent_report = self.monitor.get_agent_performance_report()
        requirement_report = self.monitor.get_requirement_coverage_report()
        error_analysis = self.monitor.get_error_analysis(24)
        performance_summary = self.monitor.get_performance_summary()
        cost_analysis = self.monitor.get_cost_analysis()
        
        # Get latest system metrics
        if self.monitor.system_metrics_history:
            system_metrics = self.monitor.system_metrics_history[-1]
        else:
            system_metrics = None
        
        # Agent metrics
        for agent_name, metrics in agent_report.items():
            safe_agent = agent_name.replace("-", "_")
            
            # Executions
            lines.append(f'# HELP agent_executions_total {self.metric_definitions["agent_executions_total"]["help"]}')
            lines.append(f'# TYPE agent_executions_total counter')
            lines.append(f'agent_executions_total{{agent="{agent_name}",status="success"}} {metrics["successful_executions"]}')
            lines.append(f'agent_executions_total{{agent="{agent_name}",status="failed"}} {metrics["failed_executions"]}')
            
            # Duration
            lines.append(f'# HELP agent_duration_seconds {self.metric_definitions["agent_duration_seconds"]["help"]}')
            lines.append(f'# TYPE agent_duration_seconds histogram')
            if metrics["average_duration"]:
                lines.append(f'agent_duration_seconds_sum{{agent="{agent_name}"}} {metrics["total_duration"]}')
                lines.append(f'agent_duration_seconds_count{{agent="{agent_name}"}} {metrics["total_executions"]}')
            
            # Success rate
            lines.append(f'agent_success_rate{{agent="{agent_name}"}} {metrics["success_rate"]}')
            
            # API calls and tokens
            lines.append(f'agent_api_calls_total{{agent="{agent_name}"}} {metrics["total_api_calls"]}')
            lines.append(f'agent_tokens_used_total{{agent="{agent_name}"}} {metrics["total_tokens"]}')
            
            # Cost
            lines.append(f'agent_cost_dollars_total{{agent="{agent_name}"}} {metrics["total_cost"]}')
            
            # Errors by type
            for error_type, count in metrics["error_types"].items():
                lines.append(f'errors_total{{agent="{agent_name}",error_type="{error_type}"}} {count}')
        
        # Requirement metrics
        if requirement_report["requirements"]:
            lines.append(f'\n# Requirement metrics')
            for req_id, req_data in requirement_report["requirements"].items():
                lines.append(f'requirement_completion_percent{{requirement_id="{req_id}"}} {req_data["completion_percentage"]}')
                lines.append(f'requirement_executions_total{{requirement_id="{req_id}"}} {req_data["execution_count"]}')
        
        # System metrics
        if system_metrics:
            lines.append(f'\n# System metrics')
            lines.append(f'system_active_agents {system_metrics.active_agents}')
            lines.append(f'system_queued_tasks {system_metrics.queued_tasks}')
            lines.append(f'system_cpu_percent {system_metrics.cpu_percent}')
            lines.append(f'system_memory_percent {system_metrics.memory_percent}')
            lines.append(f'system_disk_percent {system_metrics.disk_usage_percent}')
            lines.append(f'system_api_rate_limit_remaining {system_metrics.api_rate_limit_remaining}')
        
        # Cost metrics
        lines.append(f'\n# Cost metrics')
        lines.append(f'cost_total_dollars {cost_analysis["total"]}')
        lines.append(f'cost_hourly_rate_dollars {cost_analysis["hourly_rate"]}')
        lines.append(f'cost_daily_total_dollars {cost_analysis["today"]}')
        
        # Error metrics
        lines.append(f'\n# Error metrics')
        if error_analysis["total_errors"] > 0:
            error_rate = error_analysis["total_errors"] / error_analysis["time_window_hours"]
            lines.append(f'error_rate {error_rate}')
        
        # Performance metrics
        lines.append(f'\n# Performance metrics')
        lines.append(f'throughput_per_hour {performance_summary["throughput_per_hour"]}')
        lines.append(f'avg_response_time_seconds {performance_summary["average_duration"]}')
        
        # Alert metrics
        alerts = self.monitor.get_alerts(active_only=True)
        alert_counts = {"info": 0, "warning": 0, "critical": 0}
        for alert in alerts:
            severity = alert.get("severity", "info")
            alert_counts[severity] += 1
        
        lines.append(f'\n# Alert metrics')
        for severity, count in alert_counts.items():
            lines.append(f'alerts_active{{severity="{severity}"}} {count}')
        
        return "\n".join(lines) + "\n"
    
    def export_to_json(self, filepath: str = None) -> str:
        """Export metrics to JSON format"""
        if not self.monitor:
            return json.dumps({"error": "No monitor configured"})
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "agent_performance": self.monitor.get_agent_performance_report(),
            "requirement_coverage": self.monitor.get_requirement_coverage_report(),
            "error_analysis": self.monitor.get_error_analysis(),
            "performance_summary": self.monitor.get_performance_summary(),
            "cost_analysis": self.monitor.get_cost_analysis(),
            "alerts": self.monitor.get_alerts()
        }
        
        json_str = json.dumps(metrics, indent=2, default=str)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def generate_grafana_dashboard(self) -> Dict:
        """Generate Grafana dashboard configuration"""
        dashboard = {
            "dashboard": {
                "title": "Agent Swarm Production Metrics",
                "panels": [
                    # Agent performance panel
                    {
                        "id": 1,
                        "title": "Agent Success Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "agent_success_rate",
                                "legendFormat": "{{agent}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    # Throughput panel
                    {
                        "id": 2,
                        "title": "Throughput (executions/hour)",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "throughput_per_hour",
                                "legendFormat": "Throughput"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                    },
                    # Cost panel
                    {
                        "id": 3,
                        "title": "Cost Tracking",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "cost_hourly_rate_dollars",
                                "legendFormat": "Hourly Rate"
                            },
                            {
                                "expr": "cost_daily_total_dollars",
                                "legendFormat": "Daily Total"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                    },
                    # System resources panel
                    {
                        "id": 4,
                        "title": "System Resources",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "system_cpu_percent",
                                "legendFormat": "CPU %"
                            },
                            {
                                "expr": "system_memory_percent",
                                "legendFormat": "Memory %"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                    },
                    # Error rate panel
                    {
                        "id": 5,
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(errors_total[5m])",
                                "legendFormat": "{{agent}} - {{error_type}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
                    },
                    # Active alerts panel
                    {
                        "id": 6,
                        "title": "Active Alerts",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(alerts_active) by (severity)",
                                "legendFormat": "{{severity}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
                    },
                    # Requirement completion panel
                    {
                        "id": 7,
                        "title": "Requirement Completion",
                        "type": "bargauge",
                        "targets": [
                            {
                                "expr": "requirement_completion_percent",
                                "legendFormat": "{{requirement_id}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 24}
                    }
                ],
                "refresh": "5s",
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "uid": "agent_swarm_prod",
                "version": 1
            }
        }
        
        return dashboard
    
    def export_grafana_dashboard(self, filepath: str):
        """Export Grafana dashboard configuration to file"""
        dashboard = self.generate_grafana_dashboard()
        
        with open(filepath, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"📊 Grafana dashboard exported to {filepath}")
        print(f"   Import this JSON in Grafana to create the dashboard")
    
    def push_to_pushgateway(self, gateway_url: str, job_name: str = "agent_swarm"):
        """Push metrics to Prometheus Pushgateway"""
        import requests
        
        metrics = self.get_prometheus_metrics()
        
        try:
            response = requests.post(
                f"{gateway_url}/metrics/job/{job_name}",
                data=metrics,
                headers={'Content-Type': 'text/plain'}
            )
            
            if response.status_code == 200:
                print(f"✅ Metrics pushed to Pushgateway at {gateway_url}")
            else:
                print(f"❌ Failed to push metrics: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error pushing to Pushgateway: {e}")
    
    async def continuous_export(self, interval_seconds: int = 30):
        """Continuously export metrics at specified interval"""
        print(f"📊 Starting continuous metrics export (every {interval_seconds}s)")
        
        while True:
            try:
                # Export to JSON file with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                json_file = f"metrics/export_{timestamp}.json"
                self.export_to_json(json_file)
                
                # Push to Pushgateway if configured
                # self.push_to_pushgateway("http://localhost:9091")
                
                # The Prometheus endpoint is already serving metrics
                # Just record that we exported
                if self.monitor:
                    self.monitor.save_metrics()
                
            except Exception as e:
                print(f"Error in continuous export: {e}")
            
            await asyncio.sleep(interval_seconds)


# Example Prometheus configuration (prometheus.yml)
PROMETHEUS_CONFIG = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'agent_swarm'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
"""

# Example docker-compose snippet for Prometheus + Grafana
DOCKER_COMPOSE_MONITORING = """
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9091:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false

volumes:
  prometheus_data:
  grafana_data:
"""


if __name__ == "__main__":
    # Example usage
    from production_monitor import ProductionMonitor
    
    # Create monitor and exporter
    monitor = ProductionMonitor()
    exporter = MetricsExporter(monitor)
    
    # Start Prometheus endpoint
    exporter.start_prometheus_server()
    
    # Generate Grafana dashboard
    exporter.export_grafana_dashboard("grafana_dashboard.json")
    
    # Save Prometheus config
    with open("prometheus.yml", "w") as f:
        f.write(PROMETHEUS_CONFIG)
    
    # Save Docker Compose config
    with open("docker-compose.monitoring.yml", "w") as f:
        f.write(DOCKER_COMPOSE_MONITORING)
    
    print("\n📊 Monitoring setup complete!")
    print("1. Prometheus endpoint: http://localhost:9090/metrics")
    print("2. Start monitoring stack: docker-compose -f docker-compose.monitoring.yml up")
    print("3. Access Grafana at: http://localhost:3000 (admin/admin)")
    print("4. Import grafana_dashboard.json in Grafana")
    
    # Keep server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        exporter.stop_prometheus_server()