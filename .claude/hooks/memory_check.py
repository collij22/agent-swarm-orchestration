#!/usr/bin/env python3
"""
Memory Management Hook - Monitor and manage memory usage

Capabilities:
- Monitor memory usage
- Trigger garbage collection
- Alert on high usage
- Prevent OOM errors
"""

import os
import gc
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.hook_manager import HookContext, HookEvent
from lib.agent_logger import get_logger


@dataclass
class MemoryMetrics:
    """Memory usage metrics"""
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    percent: float  # Percentage of system memory
    available_mb: float  # Available system memory
    timestamp: float


class MemoryCheckHook:
    """Memory management hook"""
    
    def __init__(self):
        self.logger = get_logger()
        self.last_check = 0
        self.check_interval = 30  # seconds
        self.warning_threshold_mb = 512
        self.critical_threshold_mb = 1024
        self.max_threshold_mb = 2048
        self.gc_triggered_count = 0
        self.memory_history: List[MemoryMetrics] = []
        self.max_history = 100
        
        # Try to import psutil
        try:
            import psutil
            self.psutil = psutil
            self.has_psutil = True
        except ImportError:
            self.has_psutil = False
            self.logger.log_reasoning(
                "MemoryHook",
                "psutil not available - memory monitoring limited"
            )
    
    def __call__(self, context: HookContext) -> HookContext:
        """Execute memory check"""
        current_time = time.time()
        
        # Check if it's time for a memory check
        if current_time - self.last_check < self.check_interval:
            return context
        
        self.last_check = current_time
        
        # Get memory metrics
        metrics = self._get_memory_metrics()
        if not metrics:
            return context
        
        # Add to history
        self.memory_history.append(metrics)
        if len(self.memory_history) > self.max_history:
            self.memory_history.pop(0)
        
        # Add metrics to context
        context.set("memory_metrics", {
            "rss_mb": metrics.rss_mb,
            "percent": metrics.percent,
            "available_mb": metrics.available_mb
        })
        
        # Check thresholds and take action
        self._check_thresholds(metrics, context)
        
        # Analyze trends
        self._analyze_memory_trends(context)
        
        return context
    
    def _get_memory_metrics(self) -> Optional[MemoryMetrics]:
        """Get current memory metrics"""
        if not self.has_psutil:
            return None
        
        try:
            process = self.psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # Get system memory
            virtual_memory = self.psutil.virtual_memory()
            
            return MemoryMetrics(
                rss_mb=memory_info.rss / (1024 * 1024),
                vms_mb=memory_info.vms / (1024 * 1024),
                percent=memory_percent,
                available_mb=virtual_memory.available / (1024 * 1024),
                timestamp=time.time()
            )
        except Exception as e:
            self.logger.log_error(
                "MemoryHook",
                f"Failed to get memory metrics: {str(e)}"
            )
            return None
    
    def _check_thresholds(self, metrics: MemoryMetrics, context: HookContext):
        """Check memory thresholds and take action"""
        rss_mb = metrics.rss_mb
        
        if rss_mb > self.max_threshold_mb:
            # Critical - abort operation
            self.logger.log_error(
                "MemoryHook",
                f"Memory usage critical: {rss_mb:.1f}MB > {self.max_threshold_mb}MB",
                "Aborting to prevent OOM"
            )
            context.error = f"Memory limit exceeded: {rss_mb:.1f}MB"
            context.set("abort_operation", True)
            
        elif rss_mb > self.critical_threshold_mb:
            # Critical - aggressive GC
            self.logger.log_reasoning(
                "MemoryHook",
                f"Memory usage high: {rss_mb:.1f}MB - triggering aggressive GC"
            )
            self._trigger_aggressive_gc()
            context.set("memory_warning", "critical")
            
        elif rss_mb > self.warning_threshold_mb:
            # Warning - normal GC
            self.logger.log_reasoning(
                "MemoryHook",
                f"Memory usage warning: {rss_mb:.1f}MB - triggering GC"
            )
            gc.collect()
            self.gc_triggered_count += 1
            context.set("memory_warning", "warning")
    
    def _trigger_aggressive_gc(self):
        """Trigger aggressive garbage collection"""
        # Force multiple GC passes
        for _ in range(3):
            gc.collect(2)  # Collect all generations
        
        self.gc_triggered_count += 3
        
        # Clear caches if possible
        try:
            # Clear functools caches
            import functools
            functools._lru_cache_clear_all()
        except:
            pass
        
        # Log result
        metrics_after = self._get_memory_metrics()
        if metrics_after:
            self.logger.log_reasoning(
                "MemoryHook",
                f"After GC: {metrics_after.rss_mb:.1f}MB"
            )
    
    def _analyze_memory_trends(self, context: HookContext):
        """Analyze memory usage trends"""
        if len(self.memory_history) < 5:
            return
        
        # Calculate trend over last 5 measurements
        recent = self.memory_history[-5:]
        memory_values = [m.rss_mb for m in recent]
        
        # Check if memory is steadily increasing
        is_increasing = all(memory_values[i] <= memory_values[i+1] 
                           for i in range(len(memory_values)-1))
        
        if is_increasing:
            growth_rate = (memory_values[-1] - memory_values[0]) / len(memory_values)
            
            if growth_rate > 10:  # More than 10MB per measurement
                self.logger.log_reasoning(
                    "MemoryHook",
                    f"Memory leak detected: growing at {growth_rate:.1f}MB per check"
                )
                context.set("memory_leak_suspected", True)
                context.set("memory_growth_rate", growth_rate)


# Export the hook
memory_check_hook = MemoryCheckHook()


def register(hook_manager):
    """Register this hook with the hook manager"""
    from lib.hook_manager import HookEvent
    
    # Register for performance check events
    hook_manager.register_hook(
        name="memory_check",
        event_type=HookEvent.PERFORMANCE_CHECK,
        function=memory_check_hook,
        priority=60,
        config={
            "enabled": True,
            "check_interval": 30,
            "thresholds": {
                "warning_mb": 512,
                "critical_mb": 1024,
                "max_mb": 2048
            }
        }
    )