#!/usr/bin/env python3
"""
Cost Control Hook - Track API costs and enforce budget limits

Capabilities:
- Track API costs in real-time
- Enforce budget limits
- Alert on high spending
- Suggest cheaper alternatives
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import sys
import json

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.hook_manager import HookContext, HookEvent
from lib.agent_logger import get_logger


@dataclass
class CostTracker:
    """Track costs over time"""
    hourly_costs: Dict[str, float] = field(default_factory=dict)
    daily_costs: Dict[str, float] = field(default_factory=dict)
    total_cost: float = 0.0
    cost_by_tool: Dict[str, float] = field(default_factory=dict)
    cost_by_agent: Dict[str, float] = field(default_factory=dict)
    last_reset_hour: int = -1
    last_reset_day: int = -1


class CostControlHook:
    """Cost tracking and control hook"""
    
    def __init__(self):
        self.logger = get_logger()
        self.tracker = CostTracker()
        
        # Budget limits
        self.hourly_budget = 10.00
        self.daily_budget = 100.00
        self.monthly_budget = 2000.00
        
        # Cost per token (in dollars per 1K tokens)
        self.token_costs = {
            "gpt-4": 0.03,
            "gpt-4-32k": 0.06,
            "gpt-3.5-turbo": 0.002,
            "claude-3-opus": 0.015,
            "claude-3-sonnet": 0.003,
            "claude-3-haiku": 0.00025,
            "claude-2.1": 0.008,
            "claude-instant": 0.0008
        }
        
        # Cost per API call
        self.api_costs = {
            "openai_embedding": 0.0001,
            "pinecone_query": 0.0001,
            "pinecone_upsert": 0.0002,
            "web_search": 0.005,
            "web_scrape": 0.002
        }
        
        # Alert thresholds
        self.alert_threshold_percent = 80
        self.critical_threshold_percent = 95
        
        # Alternatives mapping
        self.cheaper_alternatives = {
            "gpt-4": ["gpt-3.5-turbo", "claude-3-haiku"],
            "claude-3-opus": ["claude-3-sonnet", "claude-3-haiku"],
            "claude-3-sonnet": ["claude-3-haiku", "claude-instant"]
        }
    
    def __call__(self, context: HookContext) -> HookContext:
        """Execute cost control hook"""
        # Reset counters if needed
        self._reset_counters_if_needed()
        
        # Calculate cost for this operation
        operation_cost = self._calculate_operation_cost(context)
        
        # Check if operation would exceed budget
        if not self._check_budget(operation_cost, context):
            context.error = "Operation blocked: would exceed budget"
            context.set("budget_exceeded", True)
            return context
        
        # Track the cost
        self._track_cost(operation_cost, context)
        
        # Check for alerts
        self._check_alerts(context)
        
        # Suggest alternatives if cost is high
        if operation_cost > 0.10:  # More than 10 cents
            alternatives = self._suggest_alternatives(context)
            if alternatives:
                context.set("cheaper_alternatives", alternatives)
        
        # Add cost info to context
        context.set("operation_cost", operation_cost)
        context.set("cost_summary", self._get_cost_summary())
        
        return context
    
    def _calculate_operation_cost(self, context: HookContext) -> float:
        """Calculate cost for the operation"""
        tool_name = context.tool_name
        params = context.parameters
        
        # Check if cost was already estimated
        if "estimated_cost" in context.metadata:
            return context.metadata["estimated_cost"]
        
        cost = 0.0
        
        # Calculate based on tool type
        if tool_name in ["gpt_call", "openai_call"]:
            model = params.get("model", "gpt-3.5-turbo")
            tokens = self._estimate_tokens(params)
            cost = (tokens / 1000) * self.token_costs.get(model, 0.002)
            
        elif tool_name in ["claude_call", "anthropic_call"]:
            model = params.get("model", "claude-3-sonnet")
            tokens = self._estimate_tokens(params)
            cost = (tokens / 1000) * self.token_costs.get(model, 0.003)
            
        elif tool_name in self.api_costs:
            cost = self.api_costs[tool_name]
            
        elif "api" in tool_name.lower() or "web" in tool_name.lower():
            # Generic API call cost
            cost = 0.0001
        
        return cost
    
    def _estimate_tokens(self, params: Dict) -> int:
        """Estimate token count from parameters"""
        # Simple estimation: ~4 characters per token
        text_length = 0
        
        for key, value in params.items():
            if key in ["prompt", "message", "text", "content", "query"]:
                text_length += len(str(value))
        
        # Add some overhead for system prompts
        return (text_length // 4) + 100
    
    def _check_budget(self, operation_cost: float, context: HookContext) -> bool:
        """Check if operation would exceed budget"""
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        current_day = datetime.now().strftime("%Y-%m-%d")
        
        hourly_total = self.tracker.hourly_costs.get(current_hour, 0.0) + operation_cost
        daily_total = self.tracker.daily_costs.get(current_day, 0.0) + operation_cost
        
        if hourly_total > self.hourly_budget:
            self.logger.log_error(
                "CostControlHook",
                f"Hourly budget exceeded: ${hourly_total:.2f} > ${self.hourly_budget:.2f}",
                "Blocking operation to prevent overspend"
            )
            return False
        
        if daily_total > self.daily_budget:
            self.logger.log_error(
                "CostControlHook",
                f"Daily budget exceeded: ${daily_total:.2f} > ${self.daily_budget:.2f}",
                "Blocking operation to prevent overspend"
            )
            return False
        
        return True
    
    def _track_cost(self, cost: float, context: HookContext):
        """Track the cost"""
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        current_day = datetime.now().strftime("%Y-%m-%d")
        
        # Update totals
        self.tracker.total_cost += cost
        
        # Update hourly
        if current_hour not in self.tracker.hourly_costs:
            self.tracker.hourly_costs[current_hour] = 0.0
        self.tracker.hourly_costs[current_hour] += cost
        
        # Update daily
        if current_day not in self.tracker.daily_costs:
            self.tracker.daily_costs[current_day] = 0.0
        self.tracker.daily_costs[current_day] += cost
        
        # Update by tool
        tool_name = context.tool_name
        if tool_name:
            if tool_name not in self.tracker.cost_by_tool:
                self.tracker.cost_by_tool[tool_name] = 0.0
            self.tracker.cost_by_tool[tool_name] += cost
        
        # Update by agent
        agent_name = context.agent_name
        if agent_name:
            if agent_name not in self.tracker.cost_by_agent:
                self.tracker.cost_by_agent[agent_name] = 0.0
            self.tracker.cost_by_agent[agent_name] += cost
        
        # Log significant costs
        if cost > 0.01:  # More than 1 cent
            self.logger.log_reasoning(
                "CostControlHook",
                f"Cost tracked: ${cost:.4f} for {tool_name} by {agent_name}"
            )
    
    def _check_alerts(self, context: HookContext):
        """Check for cost alerts"""
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        current_day = datetime.now().strftime("%Y-%m-%d")
        
        hourly_total = self.tracker.hourly_costs.get(current_hour, 0.0)
        daily_total = self.tracker.daily_costs.get(current_day, 0.0)
        
        # Check hourly alerts
        hourly_percent = (hourly_total / self.hourly_budget) * 100
        if hourly_percent > self.critical_threshold_percent:
            self.logger.log_error(
                "CostControlHook",
                f"CRITICAL: Hourly spending at {hourly_percent:.1f}% of budget (${hourly_total:.2f}/${self.hourly_budget:.2f})"
            )
            context.set("cost_alert", "critical")
        elif hourly_percent > self.alert_threshold_percent:
            self.logger.log_reasoning(
                "CostControlHook",
                f"WARNING: Hourly spending at {hourly_percent:.1f}% of budget"
            )
            context.set("cost_alert", "warning")
        
        # Check daily alerts
        daily_percent = (daily_total / self.daily_budget) * 100
        if daily_percent > self.alert_threshold_percent:
            self.logger.log_reasoning(
                "CostControlHook",
                f"Daily spending at {daily_percent:.1f}% of budget (${daily_total:.2f}/${self.daily_budget:.2f})"
            )
    
    def _suggest_alternatives(self, context: HookContext) -> List[Dict[str, Any]]:
        """Suggest cheaper alternatives"""
        tool_name = context.tool_name
        params = context.parameters
        alternatives = []
        
        # Check for model alternatives
        if "model" in params:
            current_model = params["model"]
            if current_model in self.cheaper_alternatives:
                for alt_model in self.cheaper_alternatives[current_model]:
                    alt_cost = self._calculate_alternative_cost(context, alt_model)
                    if alt_cost < context.get("operation_cost", 0):
                        alternatives.append({
                            "model": alt_model,
                            "estimated_cost": alt_cost,
                            "savings": context.get("operation_cost", 0) - alt_cost
                        })
        
        # Suggest caching for repeated operations
        if tool_name in ["api_call", "web_request", "gpt_call", "claude_call"]:
            alternatives.append({
                "suggestion": "Enable result caching for repeated queries",
                "potential_savings": "50-90% for duplicate requests"
            })
        
        if alternatives:
            self.logger.log_reasoning(
                "CostControlHook",
                f"Found {len(alternatives)} cheaper alternatives"
            )
        
        return alternatives
    
    def _calculate_alternative_cost(self, context: HookContext, alt_model: str) -> float:
        """Calculate cost with alternative model"""
        params = context.parameters.copy()
        params["model"] = alt_model
        
        tokens = self._estimate_tokens(params)
        return (tokens / 1000) * self.token_costs.get(alt_model, 0.001)
    
    def _reset_counters_if_needed(self):
        """Reset hourly/daily counters if needed"""
        current_hour = datetime.now().hour
        current_day = datetime.now().day
        
        # Reset hourly counter
        if current_hour != self.tracker.last_reset_hour:
            # Keep only last 24 hours
            cutoff = datetime.now() - timedelta(hours=24)
            cutoff_str = cutoff.strftime("%Y-%m-%d-%H")
            
            self.tracker.hourly_costs = {
                k: v for k, v in self.tracker.hourly_costs.items()
                if k >= cutoff_str
            }
            self.tracker.last_reset_hour = current_hour
        
        # Reset daily counter
        if current_day != self.tracker.last_reset_day:
            # Keep only last 30 days
            cutoff = datetime.now() - timedelta(days=30)
            cutoff_str = cutoff.strftime("%Y-%m-%d")
            
            self.tracker.daily_costs = {
                k: v for k, v in self.tracker.daily_costs.items()
                if k >= cutoff_str
            }
            self.tracker.last_reset_day = current_day
    
    def _get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        current_day = datetime.now().strftime("%Y-%m-%d")
        
        return {
            "total_cost": self.tracker.total_cost,
            "hourly_cost": self.tracker.hourly_costs.get(current_hour, 0.0),
            "daily_cost": self.tracker.daily_costs.get(current_day, 0.0),
            "hourly_budget_remaining": self.hourly_budget - self.tracker.hourly_costs.get(current_hour, 0.0),
            "daily_budget_remaining": self.daily_budget - self.tracker.daily_costs.get(current_day, 0.0),
            "top_tools": sorted(
                self.tracker.cost_by_tool.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "top_agents": sorted(
                self.tracker.cost_by_agent.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def get_detailed_report(self) -> str:
        """Generate detailed cost report"""
        summary = self._get_cost_summary()
        
        report = f"""
Cost Report
===========
Total Cost: ${summary['total_cost']:.2f}
Hourly: ${summary['hourly_cost']:.2f} / ${self.hourly_budget:.2f}
Daily: ${summary['daily_cost']:.2f} / ${self.daily_budget:.2f}

Top Tools by Cost:
{json.dumps(summary['top_tools'], indent=2)}

Top Agents by Cost:
{json.dumps(summary['top_agents'], indent=2)}
"""
        return report


# Export the hook
cost_control_hook = CostControlHook()


def register(hook_manager):
    """Register this hook with the hook manager"""
    from lib.hook_manager import HookEvent
    
    # Register for cost check events
    hook_manager.register_hook(
        name="cost_control",
        event_type=HookEvent.COST_CHECK,
        function=cost_control_hook,
        priority=20,
        config={
            "enabled": True,
            "enforce_budget": True,
            "alert_on_overspend": True,
            "suggest_alternatives": True
        }
    )
    
    # Also register for pre-tool to check costs before execution
    hook_manager.register_hook(
        name="cost_control_pre",
        event_type=HookEvent.PRE_TOOL_USE,
        function=cost_control_hook,
        priority=20,  # Run after security but before execution
        config={
            "enabled": True,
            "enforce_budget": True
        }
    )