#!/usr/bin/env python3
"""
Agent Runtime - Real API integration for agent execution with Claude

Features:
- Anthropic API integration for actual Claude execution
- Tool calling implementation with reasoning
- Streaming responses for real-time feedback
- Error recovery and retry logic
- Integration with agent logger
"""

import os
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from anthropic import Anthropic, AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Warning: Anthropic not installed. Install with: pip install anthropic")

from .agent_logger import ReasoningLogger, get_logger

class ModelType(Enum):
    HAIKU = "claude-3-5-haiku-20241022"  # Fast & cost-optimized (~$1/1M input, $5/1M output)
    SONNET = "claude-sonnet-4-20250514"  # Balanced performance (~$3/1M input, $15/1M output)
    OPUS = "claude-opus-4-20250514"  # Complex reasoning (~$15/1M input, $75/1M output)

def get_optimal_model(agent_name: str, task_complexity: str = "standard") -> ModelType:
    """Select the optimal model based on agent type and task complexity.
    
    Args:
        agent_name: Name of the agent
        task_complexity: "simple", "standard", or "complex"
    
    Returns:
        ModelType enum value for the optimal model
    """
    # Agents that should always use Opus for complex reasoning
    opus_agents = ["project-architect", "ai-specialist", "debug-specialist", 
                   "project-orchestrator", "meta-agent"]
    
    # Agents that can use Haiku for simple tasks
    haiku_agents = ["documentation-writer", "api-integrator"]
    
    if agent_name in opus_agents and task_complexity != "simple":
        return ModelType.OPUS
    elif agent_name in haiku_agents or task_complexity == "simple":
        return ModelType.HAIKU
    else:
        return ModelType.SONNET

@dataclass
class Tool:
    """Tool definition for agent use"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    requires_reasoning: bool = True

@dataclass
class AgentContext:
    """Context passed between agents"""
    project_requirements: Dict
    completed_tasks: List[str]
    artifacts: Dict[str, Any]
    decisions: List[Dict[str, str]]
    current_phase: str
    
    def to_dict(self):
        return {
            "project_requirements": self.project_requirements,
            "completed_tasks": self.completed_tasks,
            "artifacts": self.artifacts,
            "decisions": self.decisions,
            "current_phase": self.current_phase
        }

class AnthropicAgentRunner:
    """Runs agents with real Anthropic API integration"""
    
    def __init__(self, api_key: Optional[str] = None, logger: Optional[ReasoningLogger] = None):
        # Initialize all attributes first
        self.logger = logger or get_logger()
        self.tools: Dict[str, Tool] = {}
        self.max_retries = 5  # Increased for rate limit handling
        self.retry_delay = 2
        
        # Rate limiting: Track API calls to prevent rate limit hits
        self.api_calls_per_minute = []
        self.max_calls_per_minute = 20  # Conservative limit to avoid 30k token limit
        
        # Add inter-agent delays for sequential execution
        self.min_delay_between_agents = 3  # 3 second delay between agents
        
        # Set up API client (only if anthropic is available)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        # Only require API key if we have the anthropic library AND we're not in test mode
        if HAS_ANTHROPIC and self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
            if not self.api_key and HAS_ANTHROPIC:
                # Only warn, don't fail - allows for mock mode testing
                self.logger.log_error("agent_runtime", "No API key provided, running in simulation mode", "API key missing")
    
    def register_tool(self, tool: Tool):
        """Register a tool for agent use"""
        self.tools[tool.name] = tool
    
    def _convert_tool_for_anthropic(self, tool: Tool) -> Dict:
        """Convert tool to Anthropic format"""
        properties = {}
        required = []
        
        # Always add reasoning parameter if required
        if tool.requires_reasoning:
            properties["reasoning"] = {
                "type": "string",
                "description": f"Explanation for why we're using {tool.name}"
            }
            required.append("reasoning")
        
        # Add tool-specific parameters
        for param_name, param_info in tool.parameters.items():
            # Create clean parameter definition without 'required' field
            param_def = {k: v for k, v in param_info.items() if k != "required"}
            properties[param_name] = param_def
            
            # Check if parameter is required
            if param_info.get("required", False):
                required.append(param_name)
        
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False
            }
        }
    
    async def run_agent_async(
        self,
        agent_name: str,
        agent_prompt: str,
        context: AgentContext,
        model: ModelType = ModelType.SONNET,
        max_iterations: int = 10,
        temperature: float = 0.7
    ) -> Tuple[bool, str, AgentContext]:
        """Run an agent asynchronously with real Claude API"""
        
        if not HAS_ANTHROPIC:
            # Simulation mode
            return self._simulate_agent(agent_name, context)
        
        self.logger.log_agent_start(agent_name, json.dumps(context.to_dict())[:500], 
                                   f"Executing {agent_name} with {model.name}")
        
        # Build messages with context
        messages = [
            {
                "role": "user",
                "content": self._build_agent_prompt(agent_prompt, context)
            }
        ]
        
        # Convert tools for Anthropic
        anthropic_tools = [self._convert_tool_for_anthropic(tool) for tool in self.tools.values()]
        
        iterations = 0
        success = True
        final_result = ""
        
        try:
            while iterations < max_iterations:
                iterations += 1
                
                # Make API call with retries
                response = await self._call_claude_with_retry(
                    messages=messages,
                    model=model.value,
                    tools=anthropic_tools,
                    temperature=temperature,
                    max_tokens=4096
                )
                
                if not response:
                    raise Exception("Failed to get response from Claude")
                
                # Process response
                assistant_message = response.content[0] if response.content else None
                
                # Handle text responses
                if hasattr(assistant_message, 'text'):
                    self.logger.log_reasoning(agent_name, assistant_message.text[:500])
                    messages.append({"role": "assistant", "content": assistant_message.text})
                
                # Handle tool calls
                tool_called = False
                for block in response.content:
                    if hasattr(block, 'type') and block.type == 'tool_use':
                        tool_called = True
                        tool_name = block.name
                        tool_args = block.input
                        tool_id = block.id
                        
                        # Log tool call with reasoning
                        reasoning = tool_args.get('reasoning', 'No reasoning provided')
                        self.logger.log_tool_call(agent_name, tool_name, tool_args, reasoning)
                        
                        # Execute tool
                        if tool_name in self.tools:
                            try:
                                # Execute the tool function
                                tool_result = await self._execute_tool(
                                    self.tools[tool_name],
                                    tool_args,
                                    context
                                )
                                
                                # Add tool result to messages
                                messages.append({
                                    "role": "assistant",
                                    "content": response.content
                                })
                                
                                messages.append({
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": tool_id,
                                            "content": str(tool_result)
                                        }
                                    ]
                                })
                                
                            except Exception as e:
                                self.logger.log_error(agent_name, str(e), reasoning)
                                success = False
                                final_result = f"Tool execution failed: {str(e)}"
                                break
                        else:
                            self.logger.log_error(agent_name, f"Unknown tool: {tool_name}")
                            success = False
                            break
                
                # If no tools were called, agent is done
                if not tool_called:
                    final_result = assistant_message.text if hasattr(assistant_message, 'text') else "Complete"
                    break
                
        except Exception as e:
            self.logger.log_error(agent_name, str(e))
            success = False
            final_result = str(e)
        
        # Update context with agent results
        if success:
            context.completed_tasks.append(agent_name)
            context.artifacts[agent_name] = final_result
        
        self.logger.log_agent_complete(agent_name, success, final_result[:500])
        
        return success, final_result, context
    
    def run_agent(
        self,
        agent_name: str,
        agent_prompt: str,
        context: AgentContext,
        model: ModelType = ModelType.SONNET,
        max_iterations: int = 10,
        temperature: float = 0.7
    ) -> Tuple[bool, str, AgentContext]:
        """Synchronous wrapper for run_agent_async"""
        return asyncio.run(self.run_agent_async(
            agent_name, agent_prompt, context, model, max_iterations, temperature
        ))
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        import time
        
        current_time = time.time()
        # Remove calls older than 1 minute
        self.api_calls_per_minute = [
            call_time for call_time in self.api_calls_per_minute 
            if current_time - call_time < 60
        ]
        
        # Check if we're hitting rate limit
        if len(self.api_calls_per_minute) >= self.max_calls_per_minute:
            wait_time = 60 - (current_time - self.api_calls_per_minute[0])
            if wait_time > 0:
                self.logger.log_error(
                    "rate_limiter", 
                    f"Rate limit prevention: waiting {wait_time:.1f}s", 
                    f"Preventing rate limit hit ({len(self.api_calls_per_minute)}/{self.max_calls_per_minute} calls)"
                )
                await asyncio.sleep(wait_time + 1)  # Add 1s buffer
                # Clean up the list again after waiting
                current_time = time.time()
                self.api_calls_per_minute = [
                    call_time for call_time in self.api_calls_per_minute 
                    if current_time - call_time < 60
                ]
        
        # Record this API call
        self.api_calls_per_minute.append(current_time)

    async def _call_claude_with_retry(self, **kwargs) -> Any:
        """Call Claude API with retry logic and rate limiting"""
        # Check rate limiting before making the call
        await self._check_rate_limit()
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(**kwargs)
                return response
            except Exception as e:
                error_str = str(e).lower()
                
                # Handle rate limiting specifically
                if "rate_limit" in error_str or "429" in error_str:
                    if attempt < self.max_retries - 1:
                        # Exponential backoff with longer delays for rate limits
                        wait_time = min(60, self.retry_delay * (2 ** attempt) * 3)  # Up to 60 seconds
                        self.logger.log_error(
                            "claude_api", 
                            f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}", 
                            "Implementing exponential backoff for rate limiting"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        # Final attempt failed, log and raise
                        self.logger.log_error("claude_api", f"Rate limit exceeded after {self.max_retries} attempts", str(e))
                        raise e
                
                # Handle other errors with standard retry logic
                elif attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    self.logger.log_error(
                        "claude_api", 
                        f"API error, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})", 
                        str(e)
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.log_error("claude_api", f"API call failed after {self.max_retries} attempts", str(e))
                    raise e
        return None
    
    async def _execute_tool(self, tool: Tool, args: Dict, context: AgentContext) -> Any:
        """Execute a tool function"""
        import inspect
        sig = inspect.signature(tool.function)
        
        # Prepare function arguments
        func_args = {}
        
        # Handle reasoning parameter if the function expects it
        if 'reasoning' in sig.parameters and 'reasoning' in args:
            func_args['reasoning'] = args['reasoning']
        
        # Add other parameters (excluding reasoning to avoid duplication)
        for k, v in args.items():
            if k != 'reasoning' and k in sig.parameters:
                func_args[k] = v
        
        # Add context if the function expects it
        if 'context' in sig.parameters:
            func_args['context'] = context
        
        # Execute function (handle both sync and async)
        if asyncio.iscoroutinefunction(tool.function):
            return await tool.function(**func_args)
        else:
            return tool.function(**func_args)
    
    def _build_agent_prompt(self, agent_prompt: str, context: AgentContext) -> str:
        """Build the full prompt with context"""
        context_str = f"""
<context>
    <project_requirements>{json.dumps(context.project_requirements, indent=2)}</project_requirements>
    <completed_tasks>{', '.join(context.completed_tasks)}</completed_tasks>
    <current_phase>{context.current_phase}</current_phase>
    <previous_decisions>{json.dumps(context.decisions[-5:], indent=2) if context.decisions else 'None'}</previous_decisions>
</context>

{agent_prompt}

Remember to provide reasoning for every decision and tool use.
"""
        return context_str
    
    def _simulate_agent(self, agent_name: str, context: AgentContext) -> Tuple[bool, str, AgentContext]:
        """Simulate agent execution when API not available"""
        self.logger.log_agent_start(agent_name, "Simulation mode", "No API key - simulating")
        time.sleep(1)  # Simulate processing
        
        result = f"Simulated output from {agent_name}"
        context.completed_tasks.append(agent_name)
        context.artifacts[agent_name] = result
        
        self.logger.log_agent_complete(agent_name, True, result)
        return True, result, context

# Standard tool implementations

async def write_file_tool(file_path: str, content: str, reasoning: str = None) -> str:
        """Write content to a file"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove Unicode characters that cause Windows encoding issues
        import re
        # Replace common problematic Unicode characters with ASCII equivalents
        content = re.sub(r'[\u2192\u2190\u2191\u2193]', ' -> ', content)  # Arrows
        content = re.sub(r'[\u2713\u2714]', '[OK]', content)  # Checkmarks
        content = re.sub(r'[\u2717\u2718]', '[X]', content)   # X marks
        content = re.sub(r'[\u2705]', '[DONE]', content)      # Done emoji
        content = re.sub(r'[\U0001F4DD\U0001F4CB\U0001F4CA]', '[DOC]', content)  # Document emojis
        
        try:
            path.write_text(content, encoding='utf-8')
        except UnicodeEncodeError:
            # Fallback: remove all non-ASCII characters
            content_ascii = content.encode('ascii', 'ignore').decode('ascii')
            path.write_text(content_ascii, encoding='utf-8')
        
        return f"File written: {file_path}"

async def run_command_tool(command: str, reasoning: str = None) -> str:
    """Run a shell command"""
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return f"stdout: {result.stdout}\nstderr: {result.stderr}"

async def record_decision_tool(decision: str, rationale: str, reasoning: str = None, context: AgentContext = None) -> str:
    """Record an important decision"""
    import time
    
    if context is None:
        # This shouldn't happen in normal execution but provides a fallback
        return f"Decision recorded (no context): {decision}"
    
    context.decisions.append({
        "decision": decision,
        "rationale": rationale,
        "reasoning": reasoning or "No reasoning provided",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    return f"Decision recorded: {decision}"

async def complete_task_tool(summary: str, artifacts: Optional[Dict] = None, reasoning: str = None) -> str:
    """Mark current agent task as complete"""
    return f"Task completed: {summary}"

def create_standard_tools() -> List[Tool]:
    """Create standard tools available to all agents"""
    tools = []
    
    tools.append(Tool(
        name="write_file",
        description="Write content to a file",
        parameters={
            "file_path": {"type": "string", "description": "Path to file", "required": True},
            "content": {"type": "string", "description": "Content to write", "required": True}
        },
        function=write_file_tool
    ))
    
    tools.append(Tool(
        name="run_command",
        description="Execute a shell command",
        parameters={
            "command": {"type": "string", "description": "Command to run", "required": True}
        },
        function=run_command_tool
    ))
    
    tools.append(Tool(
        name="record_decision",
        description="Record an important architectural or technical decision",
        parameters={
            "decision": {"type": "string", "description": "The decision made", "required": True},
            "rationale": {"type": "string", "description": "Why this decision was made", "required": True}
        },
        function=record_decision_tool
    ))
    
    tools.append(Tool(
        name="complete_task",
        description="Mark the current agent's task as complete",
        parameters={
            "summary": {"type": "string", "description": "Summary of what was accomplished", "required": True},
            "artifacts": {"type": "object", "description": "Any artifacts produced", "required": False}
        },
        function=complete_task_tool
    ))
    
    return tools

# Example usage
if __name__ == "__main__":
    # Demo the runtime
    import asyncio
    
    async def demo():
        # Create logger and runtime
        logger = get_logger()
        runtime = AnthropicAgentRunner(logger=logger)
        
        # Register standard tools
        for tool in create_standard_tools():
            runtime.register_tool(tool)
        
        # Create context
        context = AgentContext(
            project_requirements={"name": "TestApp", "type": "web_app"},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="planning"
        )
        
        # Simulate agent execution
        agent_prompt = """You are a project architect. 
        Analyze the requirements and create a high-level system design.
        Use the available tools to record your decisions and create artifacts."""
        
        success, result, updated_context = await runtime.run_agent_async(
            "project-architect",
            agent_prompt,
            context,
            model=ModelType.SONNET,
            max_iterations=5
        )
        
        print(f"\nAgent completed: {success}")
        print(f"Result: {result}")
        print(f"Context: {updated_context.to_dict()}")
        
        logger.close_session()
    
    # Run demo
    asyncio.run(demo())