#!/usr/bin/env python3
"""
Pre-Tool Use Hook - Validation and modification before tool execution

Capabilities:
- Tool parameter validation
- Security checks (prevent dangerous operations)
- Rate limiting enforcement
- Cost estimation for API calls
- Parameter modification/enrichment
- Logging tool invocation intent
- Performance prediction
"""

import os
import re
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import hashlib

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.hook_manager import HookContext, HookEvent
from lib.agent_logger import get_logger


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    max_calls: int = 100
    time_window: int = 60  # seconds
    per_tool_limits: Dict[str, int] = None


class PreToolUseHook:
    """Pre-tool execution hook for validation and security"""
    
    def __init__(self):
        self.logger = get_logger()
        self.call_history: Dict[str, List[float]] = {}
        self.blocked_patterns: List[str] = []
        self.cost_estimates: Dict[str, float] = {}
        self.rate_limit_config = RateLimitConfig()
        
        # Load security patterns
        self._load_security_patterns()
        
        # Initialize cost estimates for common operations
        self.cost_estimates = {
            "gpt-4": 0.03,  # per 1K tokens
            "gpt-3.5": 0.002,  # per 1K tokens
            "claude-opus": 0.015,  # per 1K tokens
            "claude-sonnet": 0.003,  # per 1K tokens
            "api_call": 0.0001,  # per call
        }
    
    def __call__(self, context: HookContext) -> HookContext:
        """Main hook execution"""
        self.logger.log_reasoning(
            "PreToolHook",
            f"Validating tool '{context.tool_name}' for agent '{context.agent_name}'"
        )
        
        # 1. Security validation
        if not self._validate_security(context):
            context.error = "Security validation failed"
            return context
        
        # 2. Rate limiting check
        if not self._check_rate_limit(context):
            context.error = "Rate limit exceeded"
            return context
        
        # 3. Parameter validation
        if not self._validate_parameters(context):
            context.error = "Parameter validation failed"
            return context
        
        # 4. Cost estimation
        estimated_cost = self._estimate_cost(context)
        context.set("estimated_cost", estimated_cost)
        
        # 5. Parameter enrichment
        context = self._enrich_parameters(context)
        
        # 6. Performance prediction
        predicted_time = self._predict_performance(context)
        context.set("predicted_time", predicted_time)
        
        # 7. Log intent
        self._log_intent(context)
        
        return context
    
    def _validate_security(self, context: HookContext) -> bool:
        """Validate security constraints"""
        tool_name = context.tool_name
        params = context.parameters
        
        # Check for dangerous file operations
        if tool_name in ["write_file", "delete_file", "run_command"]:
            # Check for system paths
            if "file_path" in params:
                path = Path(params["file_path"])
                dangerous_paths = [
                    "/etc", "/sys", "/proc", "C:\\Windows", "C:\\System32",
                    "/usr/bin", "/usr/sbin", "~/.ssh", "~/.aws"
                ]
                for danger_path in dangerous_paths:
                    if str(path).startswith(danger_path):
                        self.logger.log_error(
                            "PreToolHook",
                            f"Blocked access to system path: {path}",
                            f"Security: Protecting system files"
                        )
                        return False
            
            # Check for dangerous commands
            if "command" in params:
                command = params["command"]
                dangerous_commands = [
                    "rm -rf", "format", "del /f", "shutdown", "reboot",
                    "kill -9", "sudo", "chmod 777", "curl | bash",
                    "wget | sh", ">", ">>", "|"  # Prevent redirects and pipes initially
                ]
                for danger_cmd in dangerous_commands:
                    if danger_cmd in command.lower():
                        self.logger.log_error(
                            "PreToolHook",
                            f"Blocked dangerous command: {command}",
                            f"Security: Preventing potentially harmful operation"
                        )
                        return False
        
        # Check for secrets in parameters
        if self._contains_secrets(params):
            self.logger.log_error(
                "PreToolHook",
                "Blocked operation containing potential secrets",
                "Security: Preventing secret exposure"
            )
            return False
        
        return True
    
    def _check_rate_limit(self, context: HookContext) -> bool:
        """Check rate limiting"""
        tool_name = context.tool_name
        current_time = time.time()
        
        # Clean old entries
        if tool_name in self.call_history:
            self.call_history[tool_name] = [
                t for t in self.call_history[tool_name]
                if current_time - t < self.rate_limit_config.time_window
            ]
        else:
            self.call_history[tool_name] = []
        
        # Check per-tool limits
        if self.rate_limit_config.per_tool_limits:
            tool_limit = self.rate_limit_config.per_tool_limits.get(
                tool_name,
                self.rate_limit_config.max_calls
            )
        else:
            tool_limit = self.rate_limit_config.max_calls
        
        # Check if limit exceeded
        if len(self.call_history[tool_name]) >= tool_limit:
            self.logger.log_error(
                "PreToolHook",
                f"Rate limit exceeded for tool '{tool_name}': {tool_limit} calls in {self.rate_limit_config.time_window}s",
                "Rate limiting to prevent abuse"
            )
            return False
        
        # Record this call
        self.call_history[tool_name].append(current_time)
        return True
    
    def _validate_parameters(self, context: HookContext) -> bool:
        """Validate tool parameters"""
        tool_name = context.tool_name
        params = context.parameters
        
        # Tool-specific validation
        if tool_name == "write_file":
            if "content" in params and len(params["content"]) > 10_000_000:  # 10MB limit
                self.logger.log_error(
                    "PreToolHook",
                    "File content too large (>10MB)",
                    "Preventing excessive resource usage"
                )
                return False
        
        elif tool_name == "run_command":
            if "timeout" not in params:
                # Add default timeout
                params["timeout"] = 30
                self.logger.log_reasoning(
                    "PreToolHook",
                    "Added default 30s timeout to command execution"
                )
        
        elif tool_name in ["api_call", "web_request"]:
            if "url" in params:
                url = params["url"]
                # Validate URL format
                if not url.startswith(("http://", "https://")):
                    self.logger.log_error(
                        "PreToolHook",
                        f"Invalid URL format: {url}",
                        "URLs must start with http:// or https://"
                    )
                    return False
                
                # Check for local network access
                local_patterns = [
                    "localhost", "127.0.0.1", "0.0.0.0",
                    "192.168.", "10.", "172.16."
                ]
                for pattern in local_patterns:
                    if pattern in url:
                        self.logger.log_error(
                            "PreToolHook",
                            f"Blocked local network access: {url}",
                            "Security: Preventing local network scanning"
                        )
                        return False
        
        return True
    
    def _estimate_cost(self, context: HookContext) -> float:
        """Estimate cost of tool execution"""
        tool_name = context.tool_name
        params = context.parameters
        estimated_cost = 0.0
        
        # Estimate based on tool type
        if tool_name in ["gpt_call", "claude_call"]:
            # Estimate token count
            text_length = sum(len(str(v)) for v in params.values())
            estimated_tokens = text_length / 4  # Rough estimate
            
            if "gpt" in tool_name:
                model = params.get("model", "gpt-3.5")
                if "gpt-4" in model:
                    estimated_cost = (estimated_tokens / 1000) * self.cost_estimates["gpt-4"]
                else:
                    estimated_cost = (estimated_tokens / 1000) * self.cost_estimates["gpt-3.5"]
            else:
                model = params.get("model", "claude-sonnet")
                if "opus" in model:
                    estimated_cost = (estimated_tokens / 1000) * self.cost_estimates["claude-opus"]
                else:
                    estimated_cost = (estimated_tokens / 1000) * self.cost_estimates["claude-sonnet"]
        
        elif tool_name in ["api_call", "web_request"]:
            estimated_cost = self.cost_estimates["api_call"]
        
        # Log if cost is significant
        if estimated_cost > 0.10:  # More than 10 cents
            self.logger.log_reasoning(
                "PreToolHook",
                f"High cost operation: ${estimated_cost:.4f}"
            )
        
        return estimated_cost
    
    def _enrich_parameters(self, context: HookContext) -> HookContext:
        """Enrich parameters with additional context"""
        tool_name = context.tool_name
        params = context.parameters
        
        # Add metadata to all tools
        if "metadata" not in params:
            params["metadata"] = {}
        
        params["metadata"].update({
            "agent": context.agent_name,
            "timestamp": time.time(),
            "request_id": self._generate_request_id(context)
        })
        
        # Tool-specific enrichment
        if tool_name == "write_file":
            # Add backup path
            if "file_path" in params:
                backup_path = f"{params['file_path']}.backup.{int(time.time())}"
                params["metadata"]["backup_path"] = backup_path
        
        elif tool_name in ["api_call", "web_request"]:
            # Add standard headers
            if "headers" not in params:
                params["headers"] = {}
            
            params["headers"].update({
                "User-Agent": "AgentSwarm/1.0",
                "X-Request-ID": params["metadata"]["request_id"]
            })
        
        context.parameters = params
        return context
    
    def _predict_performance(self, context: HookContext) -> float:
        """Predict execution time"""
        tool_name = context.tool_name
        params = context.parameters
        
        # Base predictions
        predictions = {
            "write_file": 0.1,
            "read_file": 0.05,
            "run_command": 1.0,
            "api_call": 2.0,
            "web_request": 3.0,
            "gpt_call": 5.0,
            "claude_call": 4.0
        }
        
        base_time = predictions.get(tool_name, 1.0)
        
        # Adjust based on parameters
        if tool_name == "write_file" and "content" in params:
            # Adjust for file size
            size_mb = len(params["content"]) / (1024 * 1024)
            base_time += size_mb * 0.1
        
        elif tool_name == "run_command" and "command" in params:
            # Adjust for known slow commands
            slow_commands = ["npm install", "pip install", "docker build", "git clone"]
            for slow_cmd in slow_commands:
                if slow_cmd in params["command"]:
                    base_time = 30.0
                    break
        
        return base_time
    
    def _log_intent(self, context: HookContext):
        """Log the intent of the tool use"""
        tool_name = context.tool_name
        agent_name = context.agent_name
        params_summary = {k: str(v)[:100] for k, v in context.parameters.items()}
        
        self.logger.log_tool_call(
            agent_name,
            tool_name,
            params_summary,
            f"Pre-validated: cost=${context.get('estimated_cost', 0):.4f}, "
            f"time={context.get('predicted_time', 0):.1f}s"
        )
    
    def _contains_secrets(self, params: Dict[str, Any]) -> bool:
        """Check if parameters contain potential secrets"""
        secret_patterns = [
            r"api[_-]?key",
            r"api[_-]?secret",
            r"password",
            r"passwd",
            r"token",
            r"bearer",
            r"authorization",
            r"private[_-]?key",
            r"secret[_-]?key",
            r"aws[_-]?access",
            r"aws[_-]?secret"
        ]
        
        params_str = json.dumps(params).lower()
        
        for pattern in secret_patterns:
            if re.search(pattern, params_str):
                # Check if it's actually a secret value (not just a field name)
                for value in self._extract_values(params):
                    if isinstance(value, str) and len(value) > 20:
                        # Looks like a potential secret
                        if re.match(r'^[A-Za-z0-9+/=_-]{20,}$', value):
                            return True
        
        return False
    
    def _extract_values(self, obj: Any, values: List = None) -> List:
        """Recursively extract all values from nested structure"""
        if values is None:
            values = []
        
        if isinstance(obj, dict):
            for v in obj.values():
                self._extract_values(v, values)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_values(item, values)
        else:
            values.append(obj)
        
        return values
    
    def _generate_request_id(self, context: HookContext) -> str:
        """Generate unique request ID"""
        data = f"{context.agent_name}-{context.tool_name}-{time.time()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def _load_security_patterns(self):
        """Load security patterns from configuration"""
        patterns_file = Path(".claude/hooks/security_patterns.json")
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    patterns = json.load(f)
                    self.blocked_patterns = patterns.get("blocked_patterns", [])
            except Exception as e:
                self.logger.log_error(
                    "PreToolHook",
                    f"Failed to load security patterns: {str(e)}"
                )


# Export the hook function for registration
pre_tool_use_hook = PreToolUseHook()


# Registration helper
def register(hook_manager):
    """Register this hook with the hook manager"""
    from lib.hook_manager import HookEvent
    
    hook_manager.register_hook(
        name="pre_tool_use",
        event_type=HookEvent.PRE_TOOL_USE,
        function=pre_tool_use_hook,
        priority=10,  # Run early
        config={
            "enabled": True,
            "features": {
                "validation": True,
                "rate_limiting": True,
                "cost_estimation": True,
                "security_checks": True
            }
        }
    )


if __name__ == "__main__":
    # Test the hook
    from lib.hook_manager import HookContext, HookEvent
    
    # Create test context
    context = HookContext(
        event=HookEvent.PRE_TOOL_USE,
        agent_name="test-agent",
        tool_name="write_file",
        parameters={
            "file_path": "/home/user/test.txt",
            "content": "Hello World"
        }
    )
    
    # Execute hook
    hook = PreToolUseHook()
    result = hook(context)
    
    print(f"Validation passed: {result.error is None}")
    print(f"Estimated cost: ${result.get('estimated_cost', 0):.4f}")
    print(f"Predicted time: {result.get('predicted_time', 0):.1f}s")
    print(f"Enriched params: {result.parameters}")