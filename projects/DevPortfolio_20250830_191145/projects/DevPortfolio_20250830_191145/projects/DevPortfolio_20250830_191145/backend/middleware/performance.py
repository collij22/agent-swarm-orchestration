"""
Performance Monitoring Middleware
Tracks API response times and identifies bottlenecks for <200ms target
"""

import time
import logging
import asyncio
from typing import Dict, List, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
import json
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
import os

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive performance monitoring for API endpoints
    Tracks response times, throughput, and resource usage
    """
    
    def __init__(self, app, redis_url: str = "redis://localhost:6379/2"):
        super().__init__(app)
        self.redis_url = redis_url
        self.redis_client = None
        
        # Performance targets
        self.target_response_time = 200  # 200ms target
        self.slow_query_threshold = 500  # 500ms considered slow
        
        # In-memory metrics (for immediate alerts)
        self.recent_metrics = deque(maxlen=1000)
        self.endpoint_stats = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "min_time": float('inf'),
            "max_time": 0,
            "slow_queries": 0,
            "errors": 0
        })
        
        # Performance alerts
        self.alert_thresholds = {
            "avg_response_time": 150,  # Alert if avg > 150ms
            "slow_query_rate": 0.1,    # Alert if >10% queries are slow
            "error_rate": 0.05,        # Alert if >5% error rate
            "cpu_usage": 80,           # Alert if CPU > 80%
            "memory_usage": 85,        # Alert if memory > 85%
        }
    
    async def get_redis_client(self):
        """Get Redis client for metrics storage"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True,
                max_connections=10,
            )
        return self.redis_client
    
    async def record_metric(self, metric_data: Dict):
        """Record performance metric to Redis and memory"""
        try:
            # Store in Redis for persistence
            redis_client = await self.get_redis_client()
            timestamp = datetime.utcnow().isoformat()
            
            # Store individual metric
            await redis_client.lpush(
                "performance_metrics",
                json.dumps({**metric_data, "timestamp": timestamp})
            )
            
            # Keep only last 10000 metrics
            await redis_client.ltrim("performance_metrics", 0, 9999)
            
            # Update endpoint aggregates
            endpoint = metric_data["endpoint"]
            await redis_client.hincrby(f"endpoint_stats:{endpoint}", "count", 1)
            await redis_client.hincrbyfloat(f"endpoint_stats:{endpoint}", "total_time", metric_data["response_time"])
            
            # Store in memory for immediate access
            self.recent_metrics.append(metric_data)
            
            # Update endpoint stats
            stats = self.endpoint_stats[endpoint]
            stats["count"] += 1
            stats["total_time"] += metric_data["response_time"]
            stats["min_time"] = min(stats["min_time"], metric_data["response_time"])
            stats["max_time"] = max(stats["max_time"], metric_data["response_time"])
            
            if metric_data["response_time"] > self.slow_query_threshold:
                stats["slow_queries"] += 1
            
            if metric_data["status_code"] >= 400:
                stats["errors"] += 1
            
        except Exception as e:
            logger.warning(f"Failed to record metric: {e}")
    
    async def check_performance_alerts(self, metric_data: Dict):
        """Check for performance issues and trigger alerts"""
        endpoint = metric_data["endpoint"]
        stats = self.endpoint_stats[endpoint]
        
        if stats["count"] < 10:  # Need minimum samples
            return
        
        # Calculate current metrics
        avg_response_time = stats["total_time"] / stats["count"]
        slow_query_rate = stats["slow_queries"] / stats["count"]
        error_rate = stats["errors"] / stats["count"]
        
        # System resource usage
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        
        alerts = []
        
        # Check thresholds
        if avg_response_time > self.alert_thresholds["avg_response_time"]:
            alerts.append(f"High average response time: {avg_response_time:.2f}ms")
        
        if slow_query_rate > self.alert_thresholds["slow_query_rate"]:
            alerts.append(f"High slow query rate: {slow_query_rate:.1%}")
        
        if error_rate > self.alert_thresholds["error_rate"]:
            alerts.append(f"High error rate: {error_rate:.1%}")
        
        if cpu_usage > self.alert_thresholds["cpu_usage"]:
            alerts.append(f"High CPU usage: {cpu_usage:.1f}%")
        
        if memory_usage > self.alert_thresholds["memory_usage"]:
            alerts.append(f"High memory usage: {memory_usage:.1f}%")
        
        # Log alerts
        if alerts:
            logger.warning(f"Performance alerts for {endpoint}: {'; '.join(alerts)}")
            
            # Store alert in Redis
            try:
                redis_client = await self.get_redis_client()
                alert_data = {
                    "endpoint": endpoint,
                    "alerts": alerts,
                    "metrics": {
                        "avg_response_time": avg_response_time,
                        "slow_query_rate": slow_query_rate,
                        "error_rate": error_rate,
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_usage,
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                await redis_client.lpush("performance_alerts", json.dumps(alert_data))
                await redis_client.ltrim("performance_alerts", 0, 999)  # Keep last 1000 alerts
            except Exception as e:
                logger.warning(f"Failed to store alert: {e}")
    
    async def dispatch(self, request: Request, call_next):
        """Process request with performance monitoring"""
        start_time = time.time()
        
        # Get system metrics before request
        cpu_before = psutil.cpu_percent()
        memory_before = psutil.virtual_memory().percent
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            # Handle errors
            logger.error(f"Request error: {e}")
            response = Response(
                content=json.dumps({"error": "Internal server error"}),
                status_code=500,
                media_type="application/json"
            )
            status_code = 500
            error = str(e)
        
        # Calculate metrics
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Get system metrics after request
        cpu_after = psutil.cpu_percent()
        memory_after = psutil.virtual_memory().percent
        
        # Prepare metric data
        metric_data = {
            "endpoint": f"{request.method} {request.url.path}",
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "response_time": response_time,
            "user_agent": request.headers.get("user-agent", ""),
            "ip_address": request.client.host if request.client else "",
            "query_params": dict(request.query_params),
            "cpu_usage": cpu_after,
            "memory_usage": memory_after,
            "cpu_delta": cpu_after - cpu_before,
            "memory_delta": memory_after - memory_before,
            "error": error,
        }
        
        # Record metric (async to not block response)
        asyncio.create_task(self.record_metric(metric_data))
        
        # Check for performance alerts (async)
        asyncio.create_task(self.check_performance_alerts(metric_data))
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
        response.headers["X-CPU-Usage"] = f"{cpu_after:.1f}%"
        response.headers["X-Memory-Usage"] = f"{memory_after:.1f}%"
        
        # Add performance warning if slow
        if response_time > self.target_response_time:
            response.headers["X-Performance-Warning"] = f"Slow response: {response_time:.2f}ms"
        
        return response
    
    def get_performance_summary(self) -> Dict:
        """Get current performance summary"""
        if not self.recent_metrics:
            return {"message": "No metrics available"}
        
        # Calculate overall stats
        total_requests = len(self.recent_metrics)
        total_response_time = sum(m["response_time"] for m in self.recent_metrics)
        avg_response_time = total_response_time / total_requests
        
        slow_requests = sum(1 for m in self.recent_metrics if m["response_time"] > self.slow_query_threshold)
        error_requests = sum(1 for m in self.recent_metrics if m["status_code"] >= 400)
        
        # Get system resources
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        
        # Endpoint breakdown
        endpoint_summary = {}
        for endpoint, stats in self.endpoint_stats.items():
            if stats["count"] > 0:
                endpoint_summary[endpoint] = {
                    "count": stats["count"],
                    "avg_response_time": stats["total_time"] / stats["count"],
                    "min_response_time": stats["min_time"],
                    "max_response_time": stats["max_time"],
                    "slow_query_rate": stats["slow_queries"] / stats["count"],
                    "error_rate": stats["errors"] / stats["count"],
                }
        
        return {
            "overall": {
                "total_requests": total_requests,
                "avg_response_time": avg_response_time,
                "slow_request_rate": slow_requests / total_requests,
                "error_rate": error_requests / total_requests,
                "target_met": avg_response_time <= self.target_response_time,
            },
            "system": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
            },
            "endpoints": endpoint_summary,
            "alerts": {
                "high_response_time": avg_response_time > self.alert_thresholds["avg_response_time"],
                "high_slow_query_rate": (slow_requests / total_requests) > self.alert_thresholds["slow_query_rate"],
                "high_error_rate": (error_requests / total_requests) > self.alert_thresholds["error_rate"],
                "high_cpu": cpu_usage > self.alert_thresholds["cpu_usage"],
                "high_memory": memory_usage > self.alert_thresholds["memory_usage"],
            }
        }


# Global performance monitor instance
performance_monitor = None

def get_performance_monitor():
    """Get global performance monitor instance"""
    global performance_monitor
    if performance_monitor is None:
        performance_monitor = PerformanceMonitoringMiddleware(None)
    return performance_monitor