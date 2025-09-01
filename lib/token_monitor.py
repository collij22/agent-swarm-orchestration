"""
Token Usage Monitoring System - Phase 5.2
Tracks token usage per agent and enforces limits
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class TokenUsage:
    """Track token usage for an agent"""
    agent_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    api_calls: int = 0
    estimated_cost: float = 0.0
    timestamp: str = ""
    
    def update(self, input_tokens: int, output_tokens: int, model_type: str = "sonnet"):
        """Update token usage statistics"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens = self.input_tokens + self.output_tokens
        self.api_calls += 1
        self.timestamp = datetime.now().isoformat()
        
        # Update cost estimate based on model type
        if model_type == "opus":
            # Claude 3 Opus: ~$15/1M input, $75/1M output
            self.estimated_cost += (input_tokens * 0.000015) + (output_tokens * 0.000075)
        elif model_type == "haiku":
            # Claude 3.5 Haiku: ~$1/1M input, $5/1M output
            self.estimated_cost += (input_tokens * 0.000001) + (output_tokens * 0.000005)
        else:  # sonnet
            # Claude 4 Sonnet: ~$3/1M input, $15/1M output
            self.estimated_cost += (input_tokens * 0.000003) + (output_tokens * 0.000015)


class TokenMonitor:
    """Monitor and control token usage across agents"""
    
    # Token limits per agent (can be configured)
    DEFAULT_TOKEN_LIMIT = 100000  # 100k tokens per agent
    WARNING_THRESHOLD = 0.8  # Warn at 80% usage
    CHECKPOINT_THRESHOLD = 0.9  # Create checkpoint at 90% usage
    
    def __init__(self, 
                 token_limit: Optional[int] = None,
                 checkpoint_callback: Optional[callable] = None,
                 logger: Optional[object] = None):
        self.token_limit = token_limit or self.DEFAULT_TOKEN_LIMIT
        self.checkpoint_callback = checkpoint_callback
        self.logger = logger
        self.usage_by_agent: Dict[str, TokenUsage] = {}
        self.total_usage = TokenUsage("_total")
        self.checkpoints_created = []
        self.split_tasks = []
        
        # Persistence
        self.usage_file = Path("token_usage.json")
        self.load_usage()
    
    def track_usage(self, 
                   agent_name: str, 
                   input_tokens: int, 
                   output_tokens: int,
                   model_type: str = "sonnet") -> Dict:
        """Track token usage for an agent"""
        
        # Initialize agent usage if not exists
        if agent_name not in self.usage_by_agent:
            self.usage_by_agent[agent_name] = TokenUsage(agent_name)
        
        # Update agent usage
        agent_usage = self.usage_by_agent[agent_name]
        agent_usage.update(input_tokens, output_tokens, model_type)
        
        # Update total usage
        self.total_usage.update(input_tokens, output_tokens, model_type)
        
        # Check thresholds
        usage_ratio = agent_usage.total_tokens / self.token_limit
        
        response = {
            "agent": agent_name,
            "tokens_used": agent_usage.total_tokens,
            "tokens_limit": self.token_limit,
            "usage_percentage": usage_ratio * 100,
            "estimated_cost": agent_usage.estimated_cost,
            "action": "continue"
        }
        
        # Warning threshold
        if usage_ratio >= self.WARNING_THRESHOLD and usage_ratio < self.CHECKPOINT_THRESHOLD:
            response["action"] = "warning"
            response["message"] = f"Token usage at {usage_ratio*100:.1f}% for {agent_name}"
            
            if self.logger:
                self.logger.log_warning(
                    "token_monitor",
                    f"High token usage for {agent_name}",
                    f"{agent_usage.total_tokens}/{self.token_limit} tokens used"
                )
        
        # Checkpoint threshold
        elif usage_ratio >= self.CHECKPOINT_THRESHOLD and usage_ratio < 1.0:
            response["action"] = "checkpoint"
            response["message"] = f"Creating checkpoint - token usage at {usage_ratio*100:.1f}%"
            
            # Create checkpoint
            checkpoint_id = self._create_checkpoint(agent_name, agent_usage)
            response["checkpoint_id"] = checkpoint_id
            
            if self.logger:
                self.logger.log_reasoning(
                    "token_monitor",
                    f"Checkpoint created for {agent_name}",
                    f"Token usage: {agent_usage.total_tokens}/{self.token_limit}"
                )
        
        # Limit exceeded
        elif usage_ratio >= 1.0:
            response["action"] = "split_task"
            response["message"] = f"Token limit exceeded - splitting task for {agent_name}"
            
            # Split the task
            split_info = self._split_task(agent_name, agent_usage)
            response["split_info"] = split_info
            
            if self.logger:
                self.logger.log_error(
                    "token_monitor",
                    f"Token limit exceeded for {agent_name}",
                    f"Used {agent_usage.total_tokens} tokens, limit is {self.token_limit}"
                )
        
        # Save usage to disk
        self.save_usage()
        
        return response
    
    def _create_checkpoint(self, agent_name: str, usage: TokenUsage) -> str:
        """Create a checkpoint when approaching token limit"""
        
        checkpoint_id = f"checkpoint_{agent_name}_{int(time.time())}"
        
        checkpoint_data = {
            "id": checkpoint_id,
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "token_usage": asdict(usage),
            "reason": "approaching_token_limit"
        }
        
        # Call checkpoint callback if provided
        if self.checkpoint_callback:
            self.checkpoint_callback(checkpoint_data)
        
        # Store checkpoint reference
        self.checkpoints_created.append(checkpoint_data)
        
        # Save checkpoint to file
        checkpoint_file = Path("checkpoints") / f"{checkpoint_id}.json"
        checkpoint_file.parent.mkdir(exist_ok=True)
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        return checkpoint_id
    
    def _split_task(self, agent_name: str, usage: TokenUsage) -> Dict:
        """Split task when token limit is exceeded"""
        
        split_info = {
            "original_agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "tokens_at_split": usage.total_tokens,
            "suggested_splits": []
        }
        
        # Suggest how to split the task
        if "builder" in agent_name.lower():
            split_info["suggested_splits"] = [
                f"{agent_name}_backend",
                f"{agent_name}_frontend",
                f"{agent_name}_database"
            ]
        elif "specialist" in agent_name.lower():
            split_info["suggested_splits"] = [
                f"{agent_name}_core",
                f"{agent_name}_features",
                f"{agent_name}_optimization"
            ]
        else:
            split_info["suggested_splits"] = [
                f"{agent_name}_part1",
                f"{agent_name}_part2"
            ]
        
        # Reset token counter for agent (allow continuation with split)
        usage.input_tokens = 0
        usage.output_tokens = 0
        usage.total_tokens = 0
        
        # Store split information
        self.split_tasks.append(split_info)
        
        return split_info
    
    def get_usage_summary(self) -> Dict:
        """Get comprehensive usage summary"""
        
        summary = {
            "total_tokens": self.total_usage.total_tokens,
            "total_cost": self.total_usage.estimated_cost,
            "total_api_calls": self.total_usage.api_calls,
            "agents": {},
            "checkpoints_created": len(self.checkpoints_created),
            "tasks_split": len(self.split_tasks)
        }
        
        # Add per-agent statistics
        for agent_name, usage in self.usage_by_agent.items():
            summary["agents"][agent_name] = {
                "tokens": usage.total_tokens,
                "cost": usage.estimated_cost,
                "api_calls": usage.api_calls,
                "usage_percentage": (usage.total_tokens / self.token_limit) * 100
            }
        
        return summary
    
    def generate_usage_report(self) -> str:
        """Generate a detailed usage report"""
        
        report = ["# Token Usage Report", ""]
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        # Overall summary
        report.append("## Overall Summary")
        report.append(f"- Total Tokens Used: {self.total_usage.total_tokens:,}")
        report.append(f"- Total Estimated Cost: ${self.total_usage.estimated_cost:.2f}")
        report.append(f"- Total API Calls: {self.total_usage.api_calls}")
        report.append(f"- Checkpoints Created: {len(self.checkpoints_created)}")
        report.append(f"- Tasks Split: {len(self.split_tasks)}")
        report.append("")
        
        # Per-agent breakdown
        report.append("## Agent Usage Breakdown")
        report.append("")
        
        # Sort agents by token usage
        sorted_agents = sorted(
            self.usage_by_agent.items(),
            key=lambda x: x[1].total_tokens,
            reverse=True
        )
        
        for agent_name, usage in sorted_agents:
            usage_pct = (usage.total_tokens / self.token_limit) * 100
            status = "🔴" if usage_pct >= 100 else "🟡" if usage_pct >= 80 else "🟢"
            
            report.append(f"### {agent_name} {status}")
            report.append(f"- Tokens: {usage.total_tokens:,} / {self.token_limit:,} ({usage_pct:.1f}%)")
            report.append(f"- Input Tokens: {usage.input_tokens:,}")
            report.append(f"- Output Tokens: {usage.output_tokens:,}")
            report.append(f"- API Calls: {usage.api_calls}")
            report.append(f"- Estimated Cost: ${usage.estimated_cost:.4f}")
            report.append(f"- Last Updated: {usage.timestamp}")
            report.append("")
        
        # Cost optimization suggestions
        report.append("## Cost Optimization Suggestions")
        
        # Find high-cost agents
        high_cost_agents = [
            (name, usage) for name, usage in self.usage_by_agent.items()
            if usage.estimated_cost > self.total_usage.estimated_cost * 0.2  # >20% of total
        ]
        
        if high_cost_agents:
            report.append("### High-Cost Agents (>20% of total cost)")
            for name, usage in high_cost_agents:
                cost_pct = (usage.estimated_cost / self.total_usage.estimated_cost) * 100
                report.append(f"- {name}: ${usage.estimated_cost:.4f} ({cost_pct:.1f}% of total)")
                report.append(f"  - Consider using Haiku model for this agent")
                report.append(f"  - Or split into smaller subtasks")
            report.append("")
        
        # Token efficiency
        report.append("### Token Efficiency Analysis")
        for agent_name, usage in self.usage_by_agent.items():
            if usage.api_calls > 0:
                avg_tokens = usage.total_tokens / usage.api_calls
                if avg_tokens > 10000:
                    report.append(f"- {agent_name}: High tokens per call ({avg_tokens:.0f})")
                    report.append(f"  - Consider breaking into smaller prompts")
        
        return "\n".join(report)
    
    def save_usage(self):
        """Save usage data to disk"""
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "total": asdict(self.total_usage),
            "agents": {name: asdict(usage) for name, usage in self.usage_by_agent.items()},
            "checkpoints": self.checkpoints_created,
            "split_tasks": self.split_tasks
        }
        
        with open(self.usage_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_usage(self):
        """Load usage data from disk"""
        
        if self.usage_file.exists():
            try:
                with open(self.usage_file) as f:
                    data = json.load(f)
                
                # Restore total usage
                if "total" in data:
                    self.total_usage = TokenUsage(**data["total"])
                
                # Restore agent usage
                if "agents" in data:
                    for name, usage_data in data["agents"].items():
                        self.usage_by_agent[name] = TokenUsage(**usage_data)
                
                # Restore checkpoints and splits
                self.checkpoints_created = data.get("checkpoints", [])
                self.split_tasks = data.get("split_tasks", [])
                
            except Exception as e:
                if self.logger:
                    self.logger.log_warning(
                        "token_monitor",
                        f"Could not load previous usage data: {e}"
                    )
    
    def reset_agent_usage(self, agent_name: str):
        """Reset token usage for a specific agent"""
        
        if agent_name in self.usage_by_agent:
            self.usage_by_agent[agent_name] = TokenUsage(agent_name)
            self.save_usage()
    
    def get_agent_budget_remaining(self, agent_name: str) -> int:
        """Get remaining token budget for an agent"""
        
        if agent_name not in self.usage_by_agent:
            return self.token_limit
        
        used = self.usage_by_agent[agent_name].total_tokens
        return max(0, self.token_limit - used)