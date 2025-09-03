"""Universal Tool Interceptor - Intercepts and fixes ALL tool calls"""

import json
import inspect
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime
from .content_generator import ContentGenerator

class UniversalInterceptor:
    """Intercepts all tool calls and ensures they have proper parameters"""
    
    def __init__(self, project_context: Optional[Dict] = None):
        self.content_generator = ContentGenerator(project_context)
        self.tool_call_history = []
        self.agent_contexts = {}
        self.intercept_stats = {
            "total_calls": 0,
            "fixed_calls": 0,
            "failed_calls": 0,
            "generated_content": 0
        }
    
    def register_agent(self, agent_name: str):
        """Register an agent for tracking"""
        self.agent_contexts[agent_name] = {
            "tool_calls": [],
            "errors": [],
            "files_created": [],
            "current_task": None
        }
    
    def intercept_tool_call(self, tool_name: str, params: Dict, agent_name: str = "unknown") -> Dict:
        """Intercept and fix tool calls before execution"""
        self.intercept_stats["total_calls"] += 1
        
        # Record the call
        call_record = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "tool": tool_name,
            "original_params": params.copy(),
            "fixed": False
        }
        
        # Fix based on tool type
        if tool_name == "write_file":
            params = self._fix_write_file(params, agent_name)
            call_record["fixed"] = True
            self.intercept_stats["fixed_calls"] += 1
        elif tool_name == "run_command":
            params = self._fix_run_command(params)
        elif tool_name == "record_decision":
            params = self._fix_record_decision(params)
        elif tool_name == "complete_task":
            params = self._fix_complete_task(params)
        
        # Record fixed parameters
        call_record["fixed_params"] = params
        self.tool_call_history.append(call_record)
        
        if agent_name in self.agent_contexts:
            self.agent_contexts[agent_name]["tool_calls"].append(call_record)
        
        return params
    
    def _fix_write_file(self, params: Dict, agent_name: str) -> Dict:
        """Fix write_file tool calls"""
        file_path = params.get("file_path", "")
        content = params.get("content", "")
        
        # If no file path, generate one
        if not file_path:
            file_path = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            params["file_path"] = file_path
            print(f"⚠️ [Interceptor] No file_path provided, using: {file_path}")
        
        # If no content or placeholder content, generate real content
        if not content or self._is_placeholder(content):
            print(f"🔧 [Interceptor] Generating real content for {file_path}")
            
            # Try to extract context from agent's recent activity
            context = self._extract_context_for_file(file_path, agent_name)
            
            # Generate appropriate content
            content = self.content_generator.generate_content(file_path, context)
            params["content"] = content
            self.intercept_stats["generated_content"] += 1
            
            print(f"✅ [Interceptor] Generated {len(content)} bytes of real content")
        
        # Ensure content is a string
        if not isinstance(content, str):
            if isinstance(content, (dict, list)):
                # If it's JSON-like and file is .json, convert properly
                if file_path.endswith('.json'):
                    params["content"] = json.dumps(content, indent=2)
                else:
                    params["content"] = str(content)
            else:
                params["content"] = str(content)
        
        # Track file creation
        if agent_name in self.agent_contexts:
            self.agent_contexts[agent_name]["files_created"].append(file_path)
        
        return params
    
    def _fix_run_command(self, params: Dict) -> Dict:
        """Fix run_command tool calls"""
        command = params.get("command", "")
        
        if not command:
            params["command"] = "echo 'No command provided'"
            print(f"⚠️ [Interceptor] No command provided, using echo")
        
        # Add safety checks for dangerous commands
        dangerous_commands = ["rm -rf /", "format", "del /f /s /q"]
        for dangerous in dangerous_commands:
            if dangerous in command.lower():
                params["command"] = f"echo 'BLOCKED: Dangerous command attempted: {command}'"
                print(f"🛡️ [Interceptor] Blocked dangerous command: {command}")
                break
        
        return params
    
    def _fix_record_decision(self, params: Dict) -> Dict:
        """Fix record_decision tool calls"""
        if not params.get("decision"):
            params["decision"] = "Decision recorded at " + datetime.now().isoformat()
        
        if not params.get("rationale"):
            params["rationale"] = "Automated decision based on current context"
        
        return params
    
    def _fix_complete_task(self, params: Dict) -> Dict:
        """Fix complete_task tool calls"""
        # Fix: complete_task uses 'summary' not 'task'
        if not params.get("summary"):
            # Check if 'task' was provided instead and convert it
            if params.get("task"):
                params["summary"] = params.pop("task")
            else:
                params["summary"] = "Task completed at " + datetime.now().isoformat()
        else:
            # Remove 'task' if it exists to avoid conflicts
            params.pop("task", None)
        
        # Fix: complete_task uses 'artifacts' not 'result'
        if not params.get("artifacts"):
            if params.get("result"):
                params["artifacts"] = params.pop("result")
            else:
                params["artifacts"] = {"status": "completed", "timestamp": datetime.now().isoformat()}
        else:
            # Remove 'result' if it exists to avoid conflicts
            params.pop("result", None)
        
        return params
    
    def _is_placeholder(self, content: str) -> bool:
        """Check if content is a placeholder"""
        if not content:
            return True
        
        placeholders = [
            "TODO", "todo", "FIXME", "XXX", "PLACEHOLDER",
            "Add content", "add content", "Insert content",
            "Content goes here", "Not implemented",
            "Coming soon", "Under construction"
        ]
        
        content_lower = content.lower().strip()
        
        # Check for common placeholders
        for placeholder in placeholders:
            if placeholder.lower() in content_lower:
                return True
        
        # Check if content is too short (likely placeholder)
        if len(content) < 50 and "content" in content_lower:
            return True
        
        return False
    
    def _extract_context_for_file(self, file_path: str, agent_name: str) -> str:
        """Extract context for file generation from agent activity"""
        context_parts = []
        
        # Get filename info
        filename = Path(file_path).stem
        context_parts.append(f"File: {filename}")
        
        # Check agent's current task
        if agent_name in self.agent_contexts:
            agent_ctx = self.agent_contexts[agent_name]
            if agent_ctx.get("current_task"):
                context_parts.append(f"Task: {agent_ctx['current_task']}")
            
            # Look at recent tool calls for context
            recent_calls = agent_ctx["tool_calls"][-5:]
            for call in recent_calls:
                if call["tool"] == "record_decision":
                    decision = call["original_params"].get("decision", "")
                    if decision:
                        context_parts.append(f"Decision: {decision}")
        
        # Add file-specific context based on naming patterns
        if "api" in filename.lower():
            context_parts.append("Type: API documentation/specification")
        elif "database" in filename.lower() or "schema" in filename.lower():
            context_parts.append("Type: Database schema definition")
        elif "config" in filename.lower():
            context_parts.append("Type: Configuration file")
        elif "test" in filename.lower():
            context_parts.append("Type: Test suite")
        elif "readme" in filename.lower():
            context_parts.append("Type: Project documentation")
        
        return "\n".join(context_parts)
    
    def get_agent_report(self, agent_name: str) -> Dict:
        """Get report for a specific agent"""
        if agent_name not in self.agent_contexts:
            return {"error": f"Agent {agent_name} not registered"}
        
        ctx = self.agent_contexts[agent_name]
        return {
            "agent": agent_name,
            "total_tool_calls": len(ctx["tool_calls"]),
            "files_created": ctx["files_created"],
            "errors": ctx["errors"],
            "current_task": ctx["current_task"]
        }
    
    def get_statistics(self) -> Dict:
        """Get interceptor statistics"""
        return {
            **self.intercept_stats,
            "agents_tracked": len(self.agent_contexts),
            "total_files_created": sum(
                len(ctx["files_created"]) 
                for ctx in self.agent_contexts.values()
            )
        }
    
    def wrap_tool(self, tool_func: Callable, tool_name: str) -> Callable:
        """Wrap a tool function with interception"""
        async def wrapped_tool(**kwargs):
            # Get agent name from context if available
            agent_name = kwargs.pop("_agent_name", "unknown")
            
            # Intercept and fix parameters
            fixed_params = self.intercept_tool_call(tool_name, kwargs, agent_name)
            
            # Call original tool with fixed parameters
            try:
                result = await tool_func(**fixed_params)
                return result
            except Exception as e:
                # Record error
                if agent_name in self.agent_contexts:
                    self.agent_contexts[agent_name]["errors"].append({
                        "tool": tool_name,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                raise
        
        # Preserve function metadata
        wrapped_tool.__name__ = tool_func.__name__
        wrapped_tool.__doc__ = tool_func.__doc__
        
        return wrapped_tool