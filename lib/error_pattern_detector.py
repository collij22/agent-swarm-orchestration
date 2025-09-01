"""
Error Pattern Detector for Agent Swarm

Tracks repeated errors and triggers recovery strategies to prevent
agents from getting stuck in failure loops.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import json


class ErrorPattern:
    """Represents a specific error pattern"""
    
    def __init__(self, error_message: str, agent_name: str):
        self.error_message = error_message
        self.agent_name = agent_name
        self.first_occurrence = datetime.now()
        self.last_occurrence = datetime.now()
        self.count = 1
        self.attempted_fixes = []
        
    def increment(self):
        """Record another occurrence of this error"""
        self.count += 1
        self.last_occurrence = datetime.now()
        
    def add_attempted_fix(self, fix_type: str):
        """Record that we tried to fix this error"""
        self.attempted_fixes.append({
            "type": fix_type,
            "timestamp": datetime.now().isoformat()
        })
        
    def should_escalate(self, threshold: int = 3) -> bool:
        """Check if this error pattern needs escalation"""
        return self.count >= threshold
        
    def time_since_first(self) -> timedelta:
        """Time since first occurrence"""
        return datetime.now() - self.first_occurrence


class ErrorPatternDetector:
    """Detects and manages error patterns across agent executions"""
    
    def __init__(self, logger=None, max_retries=5):
        self.logger = logger
        self.patterns: Dict[str, ErrorPattern] = {}
        self.agent_error_counts: Dict[str, int] = defaultdict(int)
        self.max_retries = max_retries
        self.recovery_strategies = {
            1: "retry_same",
            2: "retry_with_context", 
            3: "trigger_debugger",
            4: "use_alternative_agent",
            5: "manual_intervention"
        }
        # Track which strategies have been tried
        self.strategy_attempts: Dict[str, List[str]] = defaultdict(list)
        
    def _generate_pattern_key(self, agent_name: str, error_message: str) -> str:
        """Generate a unique key for an error pattern"""
        # Normalize the error message to catch similar errors
        normalized = self._normalize_error(error_message)
        # Create hash for consistent key
        pattern_text = f"{agent_name}:{normalized}"
        return hashlib.md5(pattern_text.encode()).hexdigest()
        
    def _normalize_error(self, error_message: str) -> str:
        """Normalize error messages to group similar errors"""
        # Keep original for checking specific parameters
        original = error_message.lower().strip()
        normalized = original
        
        # Remove specific file paths but keep the type
        import re
        normalized = re.sub(r'["\'].*?["\']', '<path>', normalized)
        
        # Group common parameter errors - check in original message
        if "missing required" in original or "called without" in original or ("missing" in original and "argument" in original):
            if "content" in original:
                return "missing_content_parameter"
            elif "file_path" in original:
                return "missing_filepath_parameter"
            elif "command" in original:
                return "missing_command_parameter"
            else:
                return "missing_required_parameter"
                
        # Group tool execution errors
        if "tool execution failed" in normalized:
            return "tool_execution_failed"
            
        # Group API/rate limit errors
        if "rate limit" in normalized or "429" in normalized:
            return "rate_limit_exceeded"
            
        # Group timeout errors
        if "timeout" in normalized or "timed out" in normalized:
            return "operation_timeout"
            
        return normalized[:100]  # Truncate long errors
        
    def record_error(self, agent_name: str, error_message: str) -> Tuple[int, str]:
        """
        Record an error and return (occurrence_count, recommended_strategy)
        """
        pattern_key = self._generate_pattern_key(agent_name, error_message)
        
        # Update or create pattern
        if pattern_key in self.patterns:
            self.patterns[pattern_key].increment()
        else:
            self.patterns[pattern_key] = ErrorPattern(error_message, agent_name)
            
        # Track agent error count
        self.agent_error_counts[agent_name] += 1
        
        pattern = self.patterns[pattern_key]
        
        # Log if available
        if self.logger:
            self.logger.log_reasoning(
                "error_detector",
                f"Error pattern detected for {agent_name}",
                f"Occurrence #{pattern.count}: {self._normalize_error(error_message)}"
            )
            
        # Determine recovery strategy based on count
        strategy_level = min(pattern.count, 5)
        strategy = self.recovery_strategies[strategy_level]
        
        return pattern.count, strategy
        
    def get_recovery_recommendation(self, agent_name: str, error_message: str) -> Dict:
        """Get detailed recovery recommendation for an error"""
        count, strategy = self.record_error(agent_name, error_message)
        pattern_key = self._generate_pattern_key(agent_name, error_message)
        pattern = self.patterns[pattern_key]
        
        recommendation = {
            "strategy": strategy,
            "occurrence_count": count,
            "agent_name": agent_name,
            "time_since_first": str(pattern.time_since_first()),
            "attempted_fixes": pattern.attempted_fixes,
            "details": {}
        }
        
        # Add strategy-specific details
        if strategy == "retry_same":
            recommendation["details"] = {
                "action": "Retry the same agent with identical parameters",
                "reason": "First failure, might be transient"
            }
        elif strategy == "retry_with_context":
            recommendation["details"] = {
                "action": "Retry with additional context about the error",
                "reason": "Second failure, agent needs more information",
                "additional_context": f"Previous attempt failed with: {error_message}"
            }
        elif strategy == "trigger_debugger":
            recommendation["details"] = {
                "action": "Trigger automated-debugger agent",
                "reason": "Third failure, needs automated intervention",
                "debugger_context": {
                    "failed_agent": agent_name,
                    "error_pattern": self._normalize_error(error_message),
                    "failure_count": count
                }
            }
        elif strategy == "use_alternative_agent":
            recommendation["details"] = {
                "action": "Use an alternative agent",
                "reason": "Fourth failure, this agent cannot complete the task",
                "alternatives": self._get_alternative_agents(agent_name)
            }
        elif strategy == "manual_intervention":
            recommendation["details"] = {
                "action": "Request manual intervention",
                "reason": "Fifth+ failure, automated recovery exhausted",
                "summary": f"Agent {agent_name} has failed {count} times with similar errors"
            }
            
        return recommendation
        
    def _get_alternative_agents(self, failed_agent: str) -> List[str]:
        """Suggest alternative agents based on the failed agent"""
        alternatives = {
            "ai-specialist": ["rapid-builder", "api-integrator"],
            "frontend-specialist": ["rapid-builder", "frontend-specialist"],
            "api-integrator": ["rapid-builder", "ai-specialist"],
            "database-expert": ["rapid-builder", "devops-engineer"],
            "performance-optimizer": ["quality-guardian", "debug-specialist"],
        }
        return alternatives.get(failed_agent, ["rapid-builder", "debug-specialist"])
        
    def mark_fix_attempted(self, agent_name: str, error_message: str, fix_type: str):
        """Mark that a fix was attempted for this error pattern"""
        pattern_key = self._generate_pattern_key(agent_name, error_message)
        if pattern_key in self.patterns:
            self.patterns[pattern_key].add_attempted_fix(fix_type)
            
    def get_agent_health(self, agent_name: str) -> Dict:
        """Get health status of a specific agent"""
        total_errors = self.agent_error_counts[agent_name]
        
        # Find all patterns for this agent
        agent_patterns = [
            p for p in self.patterns.values() 
            if p.agent_name == agent_name
        ]
        
        # Determine health status
        if total_errors == 0:
            status = "healthy"
        elif total_errors < 3:
            status = "warning"
        elif total_errors < 5:
            status = "critical"
        else:
            status = "failed"
            
        return {
            "agent": agent_name,
            "status": status,
            "total_errors": total_errors,
            "unique_patterns": len(agent_patterns),
            "most_common_error": max(agent_patterns, key=lambda p: p.count).error_message if agent_patterns else None,
            "recommendation": "Replace agent" if status == "failed" else "Monitor closely" if status == "critical" else "Normal operation"
        }
        
    def get_summary(self) -> Dict:
        """Get summary of all error patterns"""
        return {
            "total_patterns": len(self.patterns),
            "total_errors": sum(p.count for p in self.patterns.values()),
            "agents_with_errors": list(self.agent_error_counts.keys()),
            "critical_agents": [
                agent for agent, count in self.agent_error_counts.items()
                if count >= 3
            ],
            "top_errors": [
                {
                    "agent": p.agent_name,
                    "error": self._normalize_error(p.error_message),
                    "count": p.count
                }
                for p in sorted(self.patterns.values(), key=lambda x: x.count, reverse=True)[:5]
            ]
        }
        
    def reset_agent(self, agent_name: str):
        """Reset error tracking for a specific agent (e.g., after successful fix)"""
        # Remove patterns for this agent
        patterns_to_remove = [
            key for key, pattern in self.patterns.items()
            if pattern.agent_name == agent_name
        ]
        for key in patterns_to_remove:
            del self.patterns[key]
            
        # Reset error count
        self.agent_error_counts[agent_name] = 0
        
        if self.logger:
            self.logger.log_reasoning(
                "error_detector",
                f"Reset error tracking for {agent_name}",
                "Agent errors cleared after successful recovery"
            )