#!/usr/bin/env python3
"""
Post-Tool Use Hook - Result processing and logging after tool execution

Capabilities:
- Result validation and sanitization
- Error detection and recovery
- Metrics collection
- Result caching for reuse
- Side effect tracking
- Success/failure logging
- Performance measurement
"""

import os
import time
import json
import hashlib
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.hook_manager import HookContext, HookEvent
from lib.agent_logger import get_logger


@dataclass
class ToolMetrics:
    """Metrics for tool execution"""
    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    max_time: float = 0.0
    min_time: float = float('inf')
    errors: List[str] = field(default_factory=list)
    last_call: Optional[datetime] = None


class ResultCache:
    """Simple result cache for tool outputs"""
    
    def __init__(self, cache_dir: Path = Path(".cache/tool_results")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_cache_key(self, tool_name: str, params: Dict) -> str:
        """Generate cache key from tool and parameters"""
        # Sort params for consistent hashing
        params_str = json.dumps(params, sort_keys=True)
        data = f"{tool_name}:{params_str}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get(self, tool_name: str, params: Dict) -> Optional[Any]:
        """Get cached result if available"""
        key = self.get_cache_key(tool_name, params)
        
        # Check memory cache first
        if key in self.memory_cache:
            self.cache_hits += 1
            return self.memory_cache[key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            try:
                # Check if cache is still valid (24 hour TTL)
                if time.time() - cache_file.stat().st_mtime < 86400:
                    with open(cache_file, 'rb') as f:
                        result = pickle.load(f)
                        self.memory_cache[key] = result
                        self.cache_hits += 1
                        return result
            except Exception:
                pass
        
        self.cache_misses += 1
        return None
    
    def set(self, tool_name: str, params: Dict, result: Any):
        """Cache a tool result"""
        key = self.get_cache_key(tool_name, params)
        
        # Store in memory
        self.memory_cache[key] = result
        
        # Store on disk
        cache_file = self.cache_dir / f"{key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception:
            pass  # Ignore cache write failures


class PostToolUseHook:
    """Post-tool execution hook for result processing and metrics"""
    
    def __init__(self):
        self.logger = get_logger()
        self.metrics: Dict[str, ToolMetrics] = {}
        self.cache = ResultCache()
        self.side_effects: List[Dict[str, Any]] = []
        self.error_patterns: Dict[str, str] = {}
        
        # Load error patterns for recovery suggestions
        self._load_error_patterns()
    
    def __call__(self, context: HookContext) -> HookContext:
        """Main hook execution"""
        start_time = context.get("tool_start_time", time.time())
        execution_time = time.time() - start_time
        
        self.logger.log_reasoning(
            "PostToolHook",
            f"Processing result for tool '{context.tool_name}' (took {execution_time:.2f}s)"
        )
        
        # 1. Validate result
        is_valid = self._validate_result(context)
        
        # 2. Detect errors and suggest recovery
        if context.error or not is_valid:
            recovery_suggestion = self._suggest_recovery(context)
            context.set("recovery_suggestion", recovery_suggestion)
        
        # 3. Collect metrics
        self._collect_metrics(context, execution_time)
        
        # 4. Cache successful results
        if is_valid and not context.error:
            self._cache_result(context)
        
        # 5. Track side effects
        self._track_side_effects(context)
        
        # 6. Sanitize result
        context = self._sanitize_result(context)
        
        # 7. Log outcome
        self._log_outcome(context, execution_time)
        
        # 8. Performance analysis
        self._analyze_performance(context, execution_time)
        
        return context
    
    def _validate_result(self, context: HookContext) -> bool:
        """Validate tool execution result"""
        tool_name = context.tool_name
        result = context.result
        
        # Check for explicit error
        if context.error:
            return False
        
        # Tool-specific validation
        if tool_name == "write_file":
            # Check if file was actually written
            if "file_path" in context.parameters:
                file_path = Path(context.parameters["file_path"])
                if not file_path.exists():
                    context.error = "File was not created"
                    return False
        
        elif tool_name == "run_command":
            # Check for command failure
            if isinstance(result, dict):
                if result.get("return_code", 0) != 0:
                    context.error = f"Command failed with code {result.get('return_code')}"
                    return False
        
        elif tool_name in ["api_call", "web_request"]:
            # Check for HTTP errors
            if isinstance(result, dict):
                status_code = result.get("status_code", 200)
                if status_code >= 400:
                    context.error = f"HTTP error {status_code}"
                    return False
        
        return True
    
    def _suggest_recovery(self, context: HookContext) -> str:
        """Suggest recovery action for errors"""
        error = context.error or "Unknown error"
        tool_name = context.tool_name
        
        # Common error patterns and recovery suggestions
        suggestions = {
            "permission denied": "Check file permissions or run with appropriate privileges",
            "file not found": "Verify the file path exists and is accessible",
            "connection refused": "Check if the service is running and accessible",
            "timeout": "Increase timeout or check network connectivity",
            "rate limit": "Wait before retrying or reduce request frequency",
            "out of memory": "Free up memory or increase available resources",
            "syntax error": "Review and fix the syntax in your code or command",
            "authentication": "Check credentials and authentication tokens",
            "not found": "Verify the resource exists and the path is correct"
        }
        
        error_lower = error.lower()
        for pattern, suggestion in suggestions.items():
            if pattern in error_lower:
                self.logger.log_reasoning(
                    "PostToolHook",
                    f"Recovery suggestion: {suggestion}"
                )
                return suggestion
        
        # Tool-specific suggestions
        if tool_name == "write_file":
            return "Check directory exists and you have write permissions"
        elif tool_name == "run_command":
            return "Verify command syntax and required dependencies are installed"
        elif tool_name in ["api_call", "web_request"]:
            return "Check API endpoint, headers, and request format"
        
        return "Review the error message and adjust parameters accordingly"
    
    def _collect_metrics(self, context: HookContext, execution_time: float):
        """Collect execution metrics"""
        tool_name = context.tool_name
        
        if tool_name not in self.metrics:
            self.metrics[tool_name] = ToolMetrics(tool_name=tool_name)
        
        metrics = self.metrics[tool_name]
        metrics.total_calls += 1
        
        if context.error:
            metrics.failed_calls += 1
            metrics.errors.append(f"{datetime.now()}: {context.error}")
            # Keep only last 10 errors
            metrics.errors = metrics.errors[-10:]
        else:
            metrics.successful_calls += 1
        
        metrics.total_time += execution_time
        metrics.avg_time = metrics.total_time / metrics.total_calls
        metrics.max_time = max(metrics.max_time, execution_time)
        metrics.min_time = min(metrics.min_time, execution_time)
        metrics.last_call = datetime.now()
        
        # Add metrics to context
        context.set("metrics", {
            "execution_time": execution_time,
            "success_rate": metrics.successful_calls / metrics.total_calls if metrics.total_calls > 0 else 0,
            "avg_time": metrics.avg_time
        })
    
    def _cache_result(self, context: HookContext):
        """Cache successful results"""
        tool_name = context.tool_name
        
        # Only cache certain tools
        cacheable_tools = ["read_file", "api_call", "web_request", "expensive_computation"]
        
        if tool_name in cacheable_tools:
            # Check if result is cacheable
            if context.result and not context.get("no_cache", False):
                self.cache.set(tool_name, context.parameters, context.result)
                self.logger.log_reasoning(
                    "PostToolHook",
                    f"Cached result for {tool_name}"
                )
    
    def _track_side_effects(self, context: HookContext):
        """Track side effects of tool execution"""
        tool_name = context.tool_name
        
        side_effect = None
        
        if tool_name == "write_file":
            side_effect = {
                "type": "file_created",
                "path": context.parameters.get("file_path"),
                "size": len(context.parameters.get("content", ""))
            }
        
        elif tool_name == "delete_file":
            side_effect = {
                "type": "file_deleted",
                "path": context.parameters.get("file_path")
            }
        
        elif tool_name == "run_command":
            side_effect = {
                "type": "command_executed",
                "command": context.parameters.get("command"),
                "cwd": context.parameters.get("cwd", os.getcwd())
            }
        
        elif tool_name in ["api_call", "web_request"]:
            side_effect = {
                "type": "network_request",
                "url": context.parameters.get("url"),
                "method": context.parameters.get("method", "GET")
            }
        
        if side_effect:
            side_effect.update({
                "agent": context.agent_name,
                "timestamp": datetime.now().isoformat(),
                "success": not bool(context.error)
            })
            self.side_effects.append(side_effect)
            context.set("side_effect", side_effect)
    
    def _sanitize_result(self, context: HookContext) -> HookContext:
        """Sanitize sensitive information from results"""
        if not context.result:
            return context
        
        # Patterns to sanitize
        sensitive_patterns = [
            (r'api[_-]?key["\']?\s*[:=]\s*["\']?([A-Za-z0-9+/=_-]{20,})', 'API_KEY_REDACTED'),
            (r'password["\']?\s*[:=]\s*["\']?([^\s"\']+)', 'PASSWORD_REDACTED'),
            (r'token["\']?\s*[:=]\s*["\']?([A-Za-z0-9+/=_-]{20,})', 'TOKEN_REDACTED'),
            (r'secret["\']?\s*[:=]\s*["\']?([A-Za-z0-9+/=_-]{20,})', 'SECRET_REDACTED'),
            (r'Bearer\s+([A-Za-z0-9+/=_-]{20,})', 'Bearer TOKEN_REDACTED')
        ]
        
        # Sanitize string results
        if isinstance(context.result, str):
            import re
            sanitized = context.result
            for pattern, replacement in sensitive_patterns:
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            
            if sanitized != context.result:
                context.result = sanitized
                context.set("sanitized", True)
                self.logger.log_reasoning(
                    "PostToolHook",
                    "Sanitized sensitive information from result"
                )
        
        return context
    
    def _log_outcome(self, context: HookContext, execution_time: float):
        """Log the outcome of tool execution"""
        tool_name = context.tool_name
        agent_name = context.agent_name
        
        if context.error:
            self.logger.log_error(
                agent_name,
                f"Tool '{tool_name}' failed: {context.error}",
                f"Execution time: {execution_time:.2f}s"
            )
        else:
            result_summary = str(context.result)[:200] if context.result else "No result"
            self.logger.log_tool_call(
                agent_name,
                tool_name,
                {"status": "success", "time": f"{execution_time:.2f}s"},
                f"Completed successfully: {result_summary}"
            )
    
    def _analyze_performance(self, context: HookContext, execution_time: float):
        """Analyze performance and flag issues"""
        tool_name = context.tool_name
        predicted_time = context.get("predicted_time", 1.0)
        
        # Check if execution was significantly slower than predicted
        if execution_time > predicted_time * 2:
            self.logger.log_reasoning(
                "PostToolHook",
                f"Performance issue: {tool_name} took {execution_time:.2f}s "
                f"(predicted: {predicted_time:.2f}s)"
            )
            context.set("performance_issue", True)
        
        # Check against historical average
        if tool_name in self.metrics:
            metrics = self.metrics[tool_name]
            if execution_time > metrics.avg_time * 1.5:
                self.logger.log_reasoning(
                    "PostToolHook",
                    f"Slower than average: {execution_time:.2f}s vs avg {metrics.avg_time:.2f}s"
                )
    
    def _load_error_patterns(self):
        """Load error patterns from configuration"""
        patterns_file = Path(".claude/hooks/error_patterns.json")
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    self.error_patterns = json.load(f)
            except Exception:
                pass
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {
            "tools": {},
            "cache": {
                "hits": self.cache.cache_hits,
                "misses": self.cache.cache_misses,
                "hit_rate": self.cache.cache_hits / (self.cache.cache_hits + self.cache.cache_misses)
                           if (self.cache.cache_hits + self.cache.cache_misses) > 0 else 0
            },
            "side_effects": len(self.side_effects)
        }
        
        for tool_name, metrics in self.metrics.items():
            summary["tools"][tool_name] = {
                "total_calls": metrics.total_calls,
                "success_rate": metrics.successful_calls / metrics.total_calls if metrics.total_calls > 0 else 0,
                "avg_time": metrics.avg_time,
                "max_time": metrics.max_time,
                "recent_errors": len(metrics.errors)
            }
        
        return summary


# Export the hook function for registration
post_tool_use_hook = PostToolUseHook()


# Registration helper
def register(hook_manager):
    """Register this hook with the hook manager"""
    from lib.hook_manager import HookEvent
    
    hook_manager.register_hook(
        name="post_tool_use",
        event_type=HookEvent.POST_TOOL_USE,
        function=post_tool_use_hook,
        priority=90,  # Run late
        config={
            "enabled": True,
            "features": {
                "result_caching": True,
                "metrics_collection": True,
                "error_recovery": True,
                "side_effect_tracking": True
            }
        }
    )


if __name__ == "__main__":
    # Test the hook
    from lib.hook_manager import HookContext, HookEvent
    
    # Create test context
    context = HookContext(
        event=HookEvent.POST_TOOL_USE,
        agent_name="test-agent",
        tool_name="write_file",
        parameters={
            "file_path": "/home/user/test.txt",
            "content": "Hello World"
        },
        result="File written successfully"
    )
    context.set("tool_start_time", time.time() - 0.5)  # Simulate 0.5s execution
    
    # Execute hook
    hook = PostToolUseHook()
    result = hook(context)
    
    print(f"Validation passed: {result.error is None}")
    print(f"Metrics: {result.get('metrics')}")
    print(f"Side effect: {result.get('side_effect')}")
    
    # Get metrics summary
    print("\nMetrics Summary:")
    print(json.dumps(hook.get_metrics_summary(), indent=2))