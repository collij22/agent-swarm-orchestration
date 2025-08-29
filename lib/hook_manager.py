#!/usr/bin/env python3
"""
Hook Manager - Central coordinator for all hooks in the agent swarm

Features:
- Hook registration and execution with priority ordering
- Async/sync hook support
- Error handling and recovery
- Hook configuration management
- Integration with session manager and logger
- Shared context between hooks
"""

import asyncio
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml

# Import existing components
from .agent_logger import ReasoningLogger, get_logger


class HookEvent(Enum):
    """Hook event types"""
    # Tool execution events
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"
    
    # Agent lifecycle events
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    
    # Checkpoint events
    CHECKPOINT_SAVE = "checkpoint_save"
    CHECKPOINT_RESTORE = "checkpoint_restore"
    
    # Workflow events
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_ERROR = "workflow_error"
    
    # Performance events
    MEMORY_CHECK = "memory_check"
    PERFORMANCE_CHECK = "performance_check"
    COST_CHECK = "cost_check"
    
    # Progress events
    PROGRESS_UPDATE = "progress_update"
    MILESTONE_REACHED = "milestone_reached"


@dataclass
class HookContext:
    """Shared context passed between hooks"""
    event: HookEvent
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def set(self, key: str, value: Any):
        """Set a value in metadata"""
        self.metadata[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from metadata"""
        return self.metadata.get(key, default)
    
    def to_dict(self) -> Dict:
        """Convert context to dictionary"""
        return {
            "event": self.event.value,
            "agent_name": self.agent_name,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class Hook:
    """Hook definition"""
    name: str
    event_type: HookEvent
    function: Callable
    priority: int = 100  # Lower values execute first
    enabled: bool = True
    async_hook: bool = False
    timeout: float = 5.0  # seconds
    config: Dict[str, Any] = field(default_factory=dict)


class HookManager:
    """Central hook manager for coordinating all hooks"""
    
    def __init__(self, logger: Optional[ReasoningLogger] = None, config_path: Optional[Path] = None):
        self.logger = logger or get_logger()
        self.hooks: Dict[HookEvent, List[Hook]] = {}
        self.hook_metrics: Dict[str, Dict[str, Any]] = {}
        self.config_path = config_path or Path(".claude/hooks/config.yaml")
        self.global_config: Dict[str, Any] = {}
        
        # Load configuration if exists
        self._load_configuration()
        
        # Initialize hook storage
        for event in HookEvent:
            self.hooks[event] = []
    
    def register_hook(
        self,
        name: str,
        event_type: HookEvent,
        function: Callable,
        priority: int = 100,
        config: Dict[str, Any] = None,
        timeout: float = 5.0
    ) -> bool:
        """Register a new hook"""
        try:
            # Check if async
            is_async = asyncio.iscoroutinefunction(function)
            
            # Create hook
            hook = Hook(
                name=name,
                event_type=event_type,
                function=function,
                priority=priority,
                async_hook=is_async,
                config=config or {},
                timeout=timeout
            )
            
            # Add to registry
            self.hooks[event_type].append(hook)
            
            # Sort by priority
            self.hooks[event_type].sort(key=lambda h: h.priority)
            
            # Initialize metrics
            self.hook_metrics[name] = {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "last_error": None
            }
            
            self.logger.log_reasoning(
                "HookManager",
                f"Registered hook '{name}' for event {event_type.value} with priority {priority}"
            )
            
            return True
            
        except Exception as e:
            self.logger.log_error("HookManager", f"Failed to register hook '{name}': {str(e)}")
            return False
    
    async def execute_hooks(self, context: HookContext) -> HookContext:
        """Execute all hooks for a given event"""
        event_type = context.event
        hooks_to_run = [h for h in self.hooks.get(event_type, []) if h.enabled]
        
        if not hooks_to_run:
            return context
        
        self.logger.log_reasoning(
            "HookManager",
            f"Executing {len(hooks_to_run)} hooks for event {event_type.value}"
        )
        
        for hook in hooks_to_run:
            try:
                start_time = time.time()
                
                # Check if hook should run based on config
                if not self._should_run_hook(hook, context):
                    continue
                
                # Execute hook with timeout
                if hook.async_hook:
                    result = await asyncio.wait_for(
                        hook.function(context),
                        timeout=hook.timeout
                    )
                else:
                    # Run sync hook in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, hook.function, context),
                        timeout=hook.timeout
                    )
                
                # Update metrics
                elapsed = time.time() - start_time
                self._update_metrics(hook.name, True, elapsed)
                
                # Update context if hook returned a modified version
                if isinstance(result, HookContext):
                    context = result
                
            except asyncio.TimeoutError:
                self.logger.log_error(
                    "HookManager",
                    f"Hook '{hook.name}' timed out after {hook.timeout}s"
                )
                self._update_metrics(hook.name, False, hook.timeout)
                
            except Exception as e:
                error_msg = f"Hook '{hook.name}' failed: {str(e)}\n{traceback.format_exc()}"
                self.logger.log_error("HookManager", error_msg)
                self._update_metrics(hook.name, False, 0, str(e))
                
                # Continue with other hooks unless critical
                if hook.config.get("critical", False):
                    context.error = error_msg
                    break
        
        return context
    
    def execute_hooks_sync(self, context: HookContext) -> HookContext:
        """Synchronous wrapper for execute_hooks"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.execute_hooks(context))
        finally:
            loop.close()
    
    def configure_hook(self, hook_name: str, config: Dict[str, Any]) -> bool:
        """Update hook configuration"""
        for event_hooks in self.hooks.values():
            for hook in event_hooks:
                if hook.name == hook_name:
                    hook.config.update(config)
                    self.logger.log_reasoning(
                        "HookManager",
                        f"Updated configuration for hook '{hook_name}'"
                    )
                    return True
        return False
    
    def disable_hook(self, hook_name: str) -> bool:
        """Disable a specific hook"""
        for event_hooks in self.hooks.values():
            for hook in event_hooks:
                if hook.name == hook_name:
                    hook.enabled = False
                    self.logger.log_reasoning(
                        "HookManager",
                        f"Disabled hook '{hook_name}'"
                    )
                    return True
        return False
    
    def enable_hook(self, hook_name: str) -> bool:
        """Enable a specific hook"""
        for event_hooks in self.hooks.values():
            for hook in event_hooks:
                if hook.name == hook_name:
                    hook.enabled = True
                    self.logger.log_reasoning(
                        "HookManager",
                        f"Enabled hook '{hook_name}'"
                    )
                    return True
        return False
    
    def get_hook_metrics(self, hook_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for hooks"""
        if hook_name:
            return self.hook_metrics.get(hook_name, {})
        return self.hook_metrics
    
    def _should_run_hook(self, hook: Hook, context: HookContext) -> bool:
        """Determine if a hook should run based on configuration"""
        config = hook.config
        
        # Check agent filter
        if "agents" in config:
            allowed_agents = config["agents"]
            if context.agent_name and context.agent_name not in allowed_agents:
                return False
        
        # Check tool filter
        if "tools" in config:
            allowed_tools = config["tools"]
            if context.tool_name and context.tool_name not in allowed_tools:
                return False
        
        # Check conditions
        if "conditions" in config:
            for condition in config["conditions"]:
                if not self._evaluate_condition(condition, context):
                    return False
        
        return True
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: HookContext) -> bool:
        """Evaluate a condition against context"""
        # Simple condition evaluation - can be extended
        field = condition.get("field")
        operator = condition.get("operator", "equals")
        value = condition.get("value")
        
        if not field:
            return True
        
        # Get field value from context
        if "." in field:
            parts = field.split(".")
            current = context
            for part in parts:
                if hasattr(current, part):
                    current = getattr(current, part)
                elif isinstance(current, dict):
                    current = current.get(part)
                else:
                    return False
            field_value = current
        else:
            field_value = getattr(context, field, None)
        
        # Evaluate condition
        if operator == "equals":
            return field_value == value
        elif operator == "not_equals":
            return field_value != value
        elif operator == "contains":
            return value in str(field_value)
        elif operator == "greater_than":
            return field_value > value
        elif operator == "less_than":
            return field_value < value
        
        return True
    
    def _update_metrics(self, hook_name: str, success: bool, elapsed: float, error: str = None):
        """Update hook metrics"""
        metrics = self.hook_metrics.get(hook_name, {})
        
        metrics["executions"] += 1
        if success:
            metrics["successes"] += 1
        else:
            metrics["failures"] += 1
            if error:
                metrics["last_error"] = error
        
        metrics["total_time"] += elapsed
        metrics["avg_time"] = metrics["total_time"] / metrics["executions"]
        
        self.hook_metrics[hook_name] = metrics
    
    def _load_configuration(self):
        """Load hook configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self.global_config = config.get("hooks", {})
                    self.logger.log_reasoning(
                        "HookManager",
                        f"Loaded hook configuration from {self.config_path}"
                    )
            except Exception as e:
                self.logger.log_error(
                    "HookManager",
                    f"Failed to load configuration: {str(e)}"
                )
    
    def save_configuration(self):
        """Save current hook configuration"""
        config = {
            "hooks": self.global_config,
            "registered": {}
        }
        
        # Save hook states
        for event_type, hooks in self.hooks.items():
            for hook in hooks:
                config["registered"][hook.name] = {
                    "event": event_type.value,
                    "priority": hook.priority,
                    "enabled": hook.enabled,
                    "config": hook.config
                }
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        self.logger.log_reasoning(
            "HookManager",
            f"Saved hook configuration to {self.config_path}"
        )
    
    async def hook_context(self, event_type: HookEvent, **kwargs):
        """Context manager for hook execution"""
        context = HookContext(event=event_type, **kwargs)
        
        # Execute pre-hooks if this is a compound event
        context = await self.execute_hooks(context)
        
        return context


# Singleton instance
_hook_manager_instance: Optional[HookManager] = None


def get_hook_manager(logger: Optional[ReasoningLogger] = None) -> HookManager:
    """Get or create the singleton HookManager instance"""
    global _hook_manager_instance
    if _hook_manager_instance is None:
        _hook_manager_instance = HookManager(logger=logger)
    return _hook_manager_instance


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_hook_manager():
        # Create manager
        manager = get_hook_manager()
        
        # Define sample hooks
        def pre_tool_hook(context: HookContext) -> HookContext:
            print(f"Pre-tool hook: {context.tool_name}")
            context.set("validated", True)
            return context
        
        async def post_tool_hook(context: HookContext) -> HookContext:
            print(f"Post-tool hook: {context.tool_name}")
            await asyncio.sleep(0.1)  # Simulate async work
            context.set("processed", True)
            return context
        
        # Register hooks
        manager.register_hook(
            "validation_hook",
            HookEvent.PRE_TOOL_USE,
            pre_tool_hook,
            priority=50
        )
        
        manager.register_hook(
            "processing_hook",
            HookEvent.POST_TOOL_USE,
            post_tool_hook,
            priority=100
        )
        
        # Create context and execute hooks
        context = HookContext(
            event=HookEvent.PRE_TOOL_USE,
            agent_name="test-agent",
            tool_name="write_file",
            parameters={"file": "test.txt", "content": "Hello"}
        )
        
        # Execute pre-tool hooks
        context = await manager.execute_hooks(context)
        print(f"After pre-hooks: validated={context.get('validated')}")
        
        # Simulate tool execution
        context.result = "File written successfully"
        context.event = HookEvent.POST_TOOL_USE
        
        # Execute post-tool hooks
        context = await manager.execute_hooks(context)
        print(f"After post-hooks: processed={context.get('processed')}")
        
        # Print metrics
        print("\nHook Metrics:")
        for name, metrics in manager.get_hook_metrics().items():
            print(f"  {name}: {metrics}")
        
        # Save configuration
        manager.save_configuration()
    
    # Run test
    asyncio.run(test_hook_manager())