"""Loop Breaker - Detects and breaks infinite retry loops"""

import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import deque
from pathlib import Path
import json

class LoopBreaker:
    """Detects when agents get stuck in loops and forces strategy changes"""
    
    def __init__(self, max_retries: int = 2, similarity_threshold: float = 0.9):
        self.max_retries = max_retries
        self.similarity_threshold = similarity_threshold
        self.agent_histories = {}
        self.recovery_strategies = [
            "fix_missing_parameters",
            "regenerate_with_examples", 
            "force_structured_output",
            "bypass_agent_create_directly"
        ]
        self.strategy_index = {}
    
    def reset(self, agent_name: str):
        """Reset tracking for an agent"""
        self.agent_histories[agent_name] = {
            "recent_errors": deque(maxlen=10),
            "recent_calls": deque(maxlen=10),
            "error_counts": {},
            "loop_detected": False,
            "current_strategy": None,
            "strategy_attempts": {},
            "last_reset": datetime.now()
        }
        self.strategy_index[agent_name] = 0
    
    def detect_loop(self, agent_name: str, response: Any) -> bool:
        """Detect if agent is in a loop"""
        if agent_name not in self.agent_histories:
            self.reset(agent_name)
        
        history = self.agent_histories[agent_name]
        
        # Extract error information from response
        error_signature = self._extract_error_signature(response)
        
        if error_signature:
            # Add to error history
            history["recent_errors"].append({
                "signature": error_signature,
                "timestamp": datetime.now().isoformat(),
                "response": str(response)[:500]  # Store truncated response
            })
            
            # Count occurrences of this error
            if error_signature not in history["error_counts"]:
                history["error_counts"][error_signature] = 0
            history["error_counts"][error_signature] += 1
            
            # Check if we've seen this error too many times
            if history["error_counts"][error_signature] >= self.max_retries:
                history["loop_detected"] = True
                print(f"🔴 [LoopBreaker] Loop detected for {agent_name}!")
                print(f"   Error '{error_signature}' occurred {history['error_counts'][error_signature]} times")
                return True
        
        # Also check for repetitive tool calls
        tool_signature = self._extract_tool_signature(response)
        if tool_signature:
            history["recent_calls"].append(tool_signature)
            
            # Check for repeated patterns in recent calls
            if self._has_repetitive_pattern(history["recent_calls"]):
                history["loop_detected"] = True
                print(f"🔴 [LoopBreaker] Repetitive pattern detected for {agent_name}!")
                return True
        
        return False
    
    def break_loop(self, agent_name: str) -> Dict[str, Any]:
        """Break the loop by suggesting a new strategy"""
        if agent_name not in self.agent_histories:
            self.reset(agent_name)
        
        history = self.agent_histories[agent_name]
        
        # Get next recovery strategy
        strategy = self._get_next_strategy(agent_name)
        history["current_strategy"] = strategy
        
        # Track strategy attempts
        if strategy not in history["strategy_attempts"]:
            history["strategy_attempts"][strategy] = 0
        history["strategy_attempts"][strategy] += 1
        
        print(f"🔧 [LoopBreaker] Applying strategy: {strategy} for {agent_name}")
        
        # Clear error counts to allow retry with new strategy
        history["error_counts"] = {}
        history["loop_detected"] = False
        
        # Return strategy details
        return {
            "strategy": strategy,
            "instructions": self._get_strategy_instructions(strategy),
            "attempt": history["strategy_attempts"][strategy]
        }
    
    def _extract_error_signature(self, response: Any) -> Optional[str]:
        """Extract a signature from an error response"""
        if not response:
            return None
        
        response_str = str(response).lower()
        
        # Common error patterns
        error_patterns = [
            "missing 1 required positional argument",
            "missing required parameter",
            "content parameter is required",
            "file_path is required",
            "invalid json",
            "syntax error",
            "type error",
            "value error",
            "attribute error"
        ]
        
        for pattern in error_patterns:
            if pattern in response_str:
                # Create a signature from the error type
                return hashlib.md5(pattern.encode()).hexdigest()[:8]
        
        # Check for TODO patterns
        if any(word in response_str for word in ["todo", "placeholder", "add content"]):
            return "placeholder_content"
        
        return None
    
    def _extract_tool_signature(self, response: Any) -> Optional[str]:
        """Extract tool call signature from response"""
        if not response:
            return None
        
        response_str = str(response)
        
        # Look for tool call patterns
        if "write_file" in response_str:
            # Extract file path if available
            import re
            match = re.search(r'file_path["\']?\s*[:=]\s*["\']([^"\']+)', response_str)
            if match:
                return f"write_file:{match.group(1)}"
            return "write_file:unknown"
        
        return None
    
    def _has_repetitive_pattern(self, calls: deque) -> bool:
        """Check if recent calls show a repetitive pattern"""
        if len(calls) < 4:
            return False
        
        # Convert to list for easier pattern matching
        call_list = list(calls)
        
        # Check for exact repetition
        if len(set(call_list[-4:])) == 1:
            return True
        
        # Check for alternating pattern
        if len(call_list) >= 6:
            if (call_list[-1] == call_list[-3] == call_list[-5] and
                call_list[-2] == call_list[-4] == call_list[-6]):
                return True
        
        return False
    
    def _get_next_strategy(self, agent_name: str) -> str:
        """Get the next recovery strategy to try"""
        if agent_name not in self.strategy_index:
            self.strategy_index[agent_name] = 0
        
        idx = self.strategy_index[agent_name]
        strategy = self.recovery_strategies[idx % len(self.recovery_strategies)]
        
        # Move to next strategy for next time
        self.strategy_index[agent_name] += 1
        
        return strategy
    
    def _get_strategy_instructions(self, strategy: str) -> Dict[str, Any]:
        """Get detailed instructions for a recovery strategy"""
        instructions = {
            "fix_missing_parameters": {
                "action": "add_missing_params",
                "prompt_addition": """
CRITICAL: You MUST include ALL parameters in tool calls.
For write_file, you MUST include both:
- file_path: The exact path to the file
- content: The COMPLETE content to write (not a placeholder)

Example:
write_file(
    file_path="path/to/file.txt",
    content="Actual content here, not TODO"
)
""",
                "interceptor_action": "auto_fill_params"
            },
            
            "regenerate_with_examples": {
                "action": "show_examples",
                "prompt_addition": """
Here are WORKING examples of tool usage:

write_file(
    file_path="api_spec.md",
    content="# API Specification\\n\\n## Endpoints\\n\\n### GET /users\\nReturns list of users...\\n"
)

write_file(
    file_path="config.json",
    content='{"app": {"name": "MyApp", "version": "1.0.0"}, "database": {"host": "localhost"}}'
)

Follow these examples EXACTLY.
""",
                "interceptor_action": "provide_templates"
            },
            
            "force_structured_output": {
                "action": "structured_format",
                "prompt_addition": """
You MUST respond in this EXACT format:

TOOL_CALL_START
tool_name: write_file
param_file_path: exact/path/to/file.ext
param_content: |
  Multi-line content goes here.
  This is the actual content.
  Not a placeholder.
TOOL_CALL_END

Fill in the actual values, not placeholders.
""",
                "interceptor_action": "parse_structured"
            },
            
            "bypass_agent_create_directly": {
                "action": "orchestrator_override",
                "prompt_addition": """
The orchestrator will now create the files directly based on requirements.
Please list the files that need to be created with their purposes.
""",
                "interceptor_action": "direct_creation"
            }
        }
        
        return instructions.get(strategy, {
            "action": "default",
            "prompt_addition": "Please try a different approach.",
            "interceptor_action": "monitor"
        })
    
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get current status of an agent"""
        if agent_name not in self.agent_histories:
            return {"status": "not_tracked"}
        
        history = self.agent_histories[agent_name]
        
        return {
            "agent": agent_name,
            "loop_detected": history["loop_detected"],
            "current_strategy": history["current_strategy"],
            "error_count": sum(history["error_counts"].values()),
            "unique_errors": len(history["error_counts"]),
            "recent_errors": len(history["recent_errors"]),
            "strategy_attempts": history["strategy_attempts"],
            "last_reset": history["last_reset"].isoformat()
        }
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all tracked agents"""
        return {
            agent: self.get_agent_status(agent)
            for agent in self.agent_histories
        }
    
    def save_history(self, filepath: str):
        """Save loop detection history to file"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "agents": {}
        }
        
        for agent, history in self.agent_histories.items():
            data["agents"][agent] = {
                "error_counts": dict(history["error_counts"]),
                "loop_detected": history["loop_detected"],
                "current_strategy": history["current_strategy"],
                "strategy_attempts": dict(history["strategy_attempts"]),
                "recent_errors": list(history["recent_errors"]),
                "recent_calls": list(history["recent_calls"])
            }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 [LoopBreaker] History saved to {filepath}")