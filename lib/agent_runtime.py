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

try:
    from .agent_logger import ReasoningLogger, get_logger
except ImportError:
    # For standalone imports
    from agent_logger import ReasoningLogger, get_logger

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
    """Enhanced context with file tracking and verification"""
    project_requirements: Dict
    completed_tasks: List[str]
    artifacts: Dict[str, Any]
    decisions: List[Dict[str, str]]
    current_phase: str
    # New fields for enhanced tracking
    created_files: Dict[str, Dict] = None  # Maps agent -> list of files created
    verification_required: List[str] = None  # Critical deliverables to verify
    agent_dependencies: Dict[str, List[str]] = None  # Maps agent -> required artifacts
    incomplete_tasks: List[Dict] = None  # Tasks that failed or need retry
    
    def __post_init__(self):
        """Initialize default values for new fields"""
        if self.created_files is None:
            self.created_files = {}
        if self.verification_required is None:
            self.verification_required = []
        if self.agent_dependencies is None:
            self.agent_dependencies = {}
        if self.incomplete_tasks is None:
            self.incomplete_tasks = []
    
    def add_created_file(self, agent_name: str, file_path: str, file_type: str = "code", verified: bool = False):
        """Track a file created by an agent"""
        if agent_name not in self.created_files:
            self.created_files[agent_name] = []
        
        self.created_files[agent_name].append({
            "path": file_path,
            "type": file_type,
            "verified": verified,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def get_agent_files(self, agent_name: str) -> List[Dict]:
        """Get all files created by a specific agent"""
        return self.created_files.get(agent_name, [])
    
    def get_all_files(self) -> List[str]:
        """Get all file paths created across all agents"""
        all_files = []
        for agent_files in self.created_files.values():
            all_files.extend([f["path"] for f in agent_files])
        return all_files
    
    def add_verification_required(self, deliverable: str):
        """Mark a deliverable as requiring verification"""
        if deliverable not in self.verification_required:
            self.verification_required.append(deliverable)
    
    def add_incomplete_task(self, agent_name: str, task: str, reason: str):
        """Track an incomplete or failed task"""
        self.incomplete_tasks.append({
            "agent": agent_name,
            "task": task,
            "reason": reason,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def set_agent_dependency(self, agent_name: str, required_artifacts: List[str]):
        """Set required artifacts for an agent"""
        self.agent_dependencies[agent_name] = required_artifacts
    
    def check_dependencies(self, agent_name: str) -> Tuple[bool, List[str]]:
        """Check if agent dependencies are met"""
        if agent_name not in self.agent_dependencies:
            return True, []
        
        required = self.agent_dependencies[agent_name]
        missing = []
        
        for artifact in required:
            # Check in artifacts
            if artifact not in self.artifacts:
                # Check in created files
                if artifact not in self.get_all_files():
                    missing.append(artifact)
        
        return len(missing) == 0, missing
    
    def to_dict(self):
        return {
            "project_requirements": self.project_requirements,
            "completed_tasks": self.completed_tasks,
            "artifacts": self.artifacts,
            "decisions": self.decisions,
            "current_phase": self.current_phase,
            "created_files": self.created_files,
            "verification_required": self.verification_required,
            "agent_dependencies": self.agent_dependencies,
            "incomplete_tasks": self.incomplete_tasks
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
        
        # Validate API key format (should start with 'sk-ant-' for real keys)
        if self.api_key and not (self.api_key.startswith('sk-ant-') or os.environ.get('MOCK_MODE') == 'true'):
            self.logger.log_error(
                "agent_runtime",
                f"Invalid API key format. Expected 'sk-ant-...' but got '{self.api_key[:10]}...'",
                "API key validation failed"
            )
            # Treat invalid key format as no key to avoid hanging on API calls
            self.api_key = None
        
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
        
        # Use simulation mode only if no client is available (neither real nor mock)
        if self.client is None:
            # Check if we're supposed to be in API mode but missing key
            import os
            if os.environ.get('MOCK_MODE') != 'true' and not self.api_key:
                error_msg = "API mode requested but no ANTHROPIC_API_KEY found. Set it with: set ANTHROPIC_API_KEY=your-key-here"
                self.logger.log_error("agent_runtime", error_msg, "Missing API key")
                return False, error_msg, context
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
                
                # Process response - collect all text blocks
                text_blocks = []
                for block in response.content:
                    if hasattr(block, 'type') and block.type == 'text' and hasattr(block, 'text'):
                        text_blocks.append(block.text)
                
                # Combine text blocks if multiple exist
                combined_text = "\n".join(text_blocks) if text_blocks else ""
                
                # Handle text responses
                if combined_text:
                    # Strip trailing whitespace to avoid Claude API errors
                    clean_text = combined_text.rstrip()
                    # Prevent repetitive text by checking for duplicates
                    lines = clean_text.split('\n')
                    unique_lines = []
                    for line in lines:
                        if not unique_lines or line != unique_lines[-1]:
                            unique_lines.append(line)
                    clean_text = '\n'.join(unique_lines)
                    
                    self.logger.log_reasoning(agent_name, clean_text[:500])
                    messages.append({"role": "assistant", "content": clean_text})
                
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
                                    context,
                                    agent_name
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
                    # Use the combined text from all blocks
                    final_result = clean_text if combined_text else "Complete"
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
                
                # Check for authentication errors (401) - don't retry these
                if "401" in error_str or "authentication_error" in error_str or "invalid x-api-key" in error_str:
                    self.logger.log_error(
                        "claude_api",
                        "Authentication failed - invalid API key",
                        str(e)
                    )
                    raise e  # Don't retry authentication errors
                
                # Handle rate limiting specifically
                elif "rate_limit" in error_str or "429" in error_str:
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
    
    async def _execute_tool(self, tool: Tool, args: Dict, context: AgentContext, agent_name: str = None) -> Any:
        """Execute a tool function with enhanced context"""
        import inspect
        sig = inspect.signature(tool.function)
        
        # Enhanced handling for write_file tool to prevent missing content errors
        if tool.name == "write_file":
            if "content" not in args:
                self.logger.log_error(
                    agent_name or "unknown",
                    "write_file called without content parameter",
                    f"Args provided: {list(args.keys())}"
                )
                
                # Check if there's a "text" or "data" parameter that might contain the content
                if "text" in args:
                    args["content"] = args.pop("text")
                    self.logger.log_reasoning(agent_name or "unknown", "Using 'text' parameter as content")
                elif "data" in args:
                    args["content"] = str(args.pop("data"))
                    self.logger.log_reasoning(agent_name or "unknown", "Using 'data' parameter as content")
                else:
                    # Generate placeholder content based on file type
                    file_path = args.get("file_path", "unknown")
                    if file_path.endswith(".py"):
                        args["content"] = f"# TODO: Implement {file_path}\n# File created by {agent_name}\n\npass"
                    elif file_path.endswith(".json"):
                        args["content"] = "{}"
                    elif file_path.endswith(".md"):
                        args["content"] = f"# {file_path}\n\nTODO: Add content"
                    elif file_path.endswith(".txt"):
                        args["content"] = f"TODO: Add content for {file_path}"
                    elif file_path.endswith(".yml") or file_path.endswith(".yaml"):
                        args["content"] = "# TODO: Add configuration"
                    else:
                        args["content"] = ""
                    
                    self.logger.log_reasoning(
                        agent_name or "unknown",
                        f"Generated placeholder content for {file_path}"
                    )
            elif args["content"] is None:
                self.logger.log_error(
                    agent_name or "unknown",
                    "write_file called with None content",
                    "Converting None to empty string"
                )
                args["content"] = ""
            elif not isinstance(args["content"], str):
                # Convert non-string content to string
                self.logger.log_reasoning(
                    agent_name or "unknown",
                    f"Converting non-string content ({type(args['content'])}) to string"
                )
                args["content"] = str(args["content"])
        
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
        
        # Add agent_name if the function expects it
        if 'agent_name' in sig.parameters and agent_name:
            func_args['agent_name'] = agent_name
        
        # Execute function (handle both sync and async)
        if asyncio.iscoroutinefunction(tool.function):
            return await tool.function(**func_args)
        else:
            return tool.function(**func_args)
    
    def _build_agent_prompt(self, agent_prompt: str, context: AgentContext) -> str:
        """Build the full prompt with enhanced context"""
        # Build file summary
        files_summary = ""
        if context.created_files:
            files_by_type = {}
            for agent, files in context.created_files.items():
                for file_info in files:
                    file_type = file_info.get("type", "unknown")
                    if file_type not in files_by_type:
                        files_by_type[file_type] = []
                    files_by_type[file_type].append(file_info["path"])
            
            files_summary = "\n".join([f"    - {ftype}: {', '.join(files[:5])}" 
                                      for ftype, files in files_by_type.items()])
        
        # Build incomplete tasks summary
        incomplete_summary = ""
        if context.incomplete_tasks:
            incomplete_summary = "\n".join([f"    - {task['agent']}: {task['task']} ({task['reason']})"
                                          for task in context.incomplete_tasks[-5:]])
        
        # Build verification required summary
        verification_summary = ""
        if context.verification_required:
            verification_summary = ", ".join(context.verification_required[:10])
        
        context_str = f"""
<context>
    <project_requirements>{json.dumps(context.project_requirements, indent=2)}</project_requirements>
    <completed_tasks>{', '.join(context.completed_tasks)}</completed_tasks>
    <current_phase>{context.current_phase}</current_phase>
    <previous_decisions>{json.dumps(context.decisions[-5:], indent=2) if context.decisions else 'None'}</previous_decisions>
    <created_files>
{files_summary if files_summary else '    No files created yet'}
    </created_files>
    <incomplete_tasks>
{incomplete_summary if incomplete_summary else '    No incomplete tasks'}
    </incomplete_tasks>
    <verification_required>{verification_summary if verification_summary else 'None'}</verification_required>
</context>

{agent_prompt}

Remember to:
1. Provide reasoning for every decision and tool use
2. Use dependency_check tool if you need artifacts from other agents
3. Use request_artifact tool to get specific files or data from previous agents
4. Use verify_deliverables tool to ensure critical files exist
5. Track important files you create for other agents to use
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

async def write_file_tool(file_path: str, content: str, reasoning: str = None, 
                         context: AgentContext = None, agent_name: str = None,
                         verify: bool = True, max_retries: int = 3) -> str:
    """Enhanced write content to a file with verification and tracking"""
    # Get project directory from context if available
    if context and "project_directory" in context.artifacts:
        project_base = Path(context.artifacts["project_directory"])
    else:
        # Fallback to creating a default project directory
        project_base = Path.cwd() / 'project_output'
    
    # Check if the file_path already contains the project directory to avoid duplication
    project_name = project_base.name if project_base else ""
    
    # Handle different path formats
    if file_path.startswith('/project/'):
        # Use the project directory from context
        file_path = str(project_base / file_path[9:])  # Remove '/project/' prefix
    elif file_path.startswith('/'):
        # Other absolute paths - put them in the project directory
        file_path = str(project_base / file_path[1:])  # Remove leading '/'
    elif not Path(file_path).is_absolute():
        # For relative paths, check if they already contain the project directory
        if project_name and project_name in file_path:
            # The path already contains the project directory, extract the relative part
            # Split by the project directory name and take the part after it
            parts = file_path.split(project_name)
            if len(parts) > 1:
                # Take the last occurrence and clean up any leading slashes
                relative_path = parts[-1].lstrip('/\\')
                file_path = str(project_base / relative_path)
            else:
                # Fallback: treat as relative to project directory
                file_path = str(project_base / file_path)
        else:
            # Normal relative path - add to project directory
            file_path = str(project_base / file_path)
    
    path = Path(file_path)
    
    # Ensure content is a string (handle None or other types)
    if content is None:
        content = ""
    elif not isinstance(content, str):
        content = str(content)
    
    # Remove Unicode characters that cause Windows encoding issues
    import re
    # Replace common problematic Unicode characters with ASCII equivalents
    content = re.sub(r'[\u2192\u2190\u2191\u2193]', ' -> ', content)  # Arrows
    content = re.sub(r'[\u2713\u2714]', '[OK]', content)  # Checkmarks
    content = re.sub(r'[\u2717\u2718]', '[X]', content)   # X marks
    content = re.sub(r'[\u2705]', '[DONE]', content)      # Done emoji
    content = re.sub(r'[\U0001F4DD\U0001F4CB\U0001F4CA]', '[DOC]', content)  # Document emojis
    
    # Retry logic for file operations
    for attempt in range(max_retries):
        try:
            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            try:
                path.write_text(content, encoding='utf-8')
            except UnicodeEncodeError:
                # Fallback: remove all non-ASCII characters
                content_ascii = content.encode('ascii', 'ignore').decode('ascii')
                path.write_text(content_ascii, encoding='utf-8')
            
            # Verify file was created if requested
            if verify and not path.exists():
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)  # Wait before retry
                    continue
                else:
                    error_msg = f"File verification failed after {max_retries} attempts: {file_path}"
                    if context and agent_name:
                        context.add_incomplete_task(agent_name, f"write_file: {file_path}", error_msg)
                    return f"Error: {error_msg}"
            
            # Track in context if available
            if context and agent_name:
                # Determine file type
                file_type = "code"
                if file_path.endswith(('.md', '.txt', '.rst')):
                    file_type = "documentation"
                elif file_path.endswith(('.json', '.yaml', '.yml', '.toml')):
                    file_type = "config"
                elif file_path.endswith(('.test.py', '_test.py', '.spec.js', '.test.js')):
                    file_type = "test"
                    
                context.add_created_file(agent_name, file_path, file_type, verified=verify)
                
                # Add to verification list if critical
                critical_patterns = ['main.py', 'app.py', 'index.js', 'package.json', 
                                   'requirements.txt', 'Dockerfile', 'docker-compose.yml']
                if any(pattern in file_path for pattern in critical_patterns):
                    context.add_verification_required(file_path)
            
            return f"File written successfully: {file_path} (verified: {path.exists()})"
            
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            else:
                error_msg = f"Failed to write file after {max_retries} attempts: {str(e)}"
                if context and agent_name:
                    context.add_incomplete_task(agent_name, f"write_file: {file_path}", error_msg)
                return f"Error: {error_msg}"
    
    return f"File operation completed: {file_path}"

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

async def dependency_check_tool(agent_name: str, reasoning: str = None, context: AgentContext = None) -> str:
    """Check if agent dependencies are met before execution"""
    if context is None:
        return "Error: No context available for dependency check"
    
    dependencies_met, missing = context.check_dependencies(agent_name)
    
    if dependencies_met:
        return f"All dependencies met for {agent_name}"
    else:
        # Track as incomplete task
        context.add_incomplete_task(
            agent_name, 
            "dependency_check", 
            f"Missing artifacts: {', '.join(missing)}"
        )
        return f"Missing dependencies for {agent_name}: {', '.join(missing)}"

async def request_artifact_tool(artifact_name: str, from_agent: str = None, 
                               reasoning: str = None, context: AgentContext = None) -> str:
    """Request a specific artifact from a previous agent"""
    if context is None:
        return "Error: No context available for artifact request"
    
    # Check if artifact exists in context
    if artifact_name in context.artifacts:
        return f"Artifact found: {artifact_name}\nContent: {str(context.artifacts[artifact_name])[:500]}"
    
    # Check if it's a file that was created
    all_files = context.get_all_files()
    if artifact_name in all_files:
        # Try to read the file
        try:
            path = Path(artifact_name)
            if path.exists():
                content = path.read_text()[:500]  # First 500 chars
                return f"File artifact found: {artifact_name}\nContent preview: {content}"
        except Exception as e:
            return f"Error reading artifact file {artifact_name}: {str(e)}"
    
    # Check specific agent's files if specified
    if from_agent:
        agent_files = context.get_agent_files(from_agent)
        matching_files = [f for f in agent_files if artifact_name in f["path"]]
        if matching_files:
            return f"Found {len(matching_files)} matching files from {from_agent}: {matching_files}"
    
    # Not found
    context.add_incomplete_task(
        "current_agent",
        f"request_artifact: {artifact_name}",
        f"Artifact not found in context or files"
    )
    return f"Artifact '{artifact_name}' not found. Available artifacts: {list(context.artifacts.keys())[:10]}"

async def verify_deliverables_tool(deliverables: List[str], reasoning: str = None, 
                                   context: AgentContext = None) -> str:
    """Verify that critical deliverables exist and are valid"""
    if context is None:
        return "Error: No context available for verification"
    
    verification_results = []
    all_verified = True
    
    for deliverable in deliverables:
        path = Path(deliverable)
        if path.exists():
            size = path.stat().st_size
            if size > 0:
                verification_results.append(f"✓ {deliverable} (size: {size} bytes)")
            else:
                verification_results.append(f"✗ {deliverable} (empty file)")
                all_verified = False
                context.add_incomplete_task("verification", deliverable, "Empty file")
        else:
            verification_results.append(f"✗ {deliverable} (not found)")
            all_verified = False
            context.add_incomplete_task("verification", deliverable, "File not found")
    
    # Mark deliverables as requiring verification
    for deliverable in deliverables:
        context.add_verification_required(deliverable)
    
    status = "All deliverables verified" if all_verified else "Some deliverables missing or invalid"
    return f"{status}\n" + "\n".join(verification_results)

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
    
    # New inter-agent communication tools
    tools.append(Tool(
        name="dependency_check",
        description="Check if agent dependencies are met before execution",
        parameters={
            "agent_name": {"type": "string", "description": "Name of agent to check", "required": True}
        },
        function=dependency_check_tool
    ))
    
    tools.append(Tool(
        name="request_artifact",
        description="Request a specific artifact from a previous agent",
        parameters={
            "artifact_name": {"type": "string", "description": "Name or path of artifact needed", "required": True},
            "from_agent": {"type": "string", "description": "Specific agent that created it", "required": False}
        },
        function=request_artifact_tool
    ))
    
    tools.append(Tool(
        name="verify_deliverables",
        description="Verify that critical deliverables exist and are valid",
        parameters={
            "deliverables": {"type": "array", "description": "List of file paths to verify", "required": True}
        },
        function=verify_deliverables_tool
    ))
    
    return tools

def create_quality_tools() -> List[Tool]:
    """Create quality validation tools for quality-guardian agent"""
    # Import quality validation functions
    try:
        from quality_validation import (
            validate_requirements_tool,
            test_endpoints_tool,
            validate_docker_tool,
            generate_completion_report_tool
        )
    except ImportError:
        # If not available, return empty list
        return []
    
    tools = []
    
    tools.append(Tool(
        name="validate_requirements",
        description="Validate all project requirements and generate completion report",
        parameters={
            "requirements_file": {"type": "string", "description": "Path to requirements file", "required": False},
            "requirements_dict": {"type": "object", "description": "Requirements dictionary", "required": False},
            "project_path": {"type": "string", "description": "Project path to validate", "required": False}
        },
        function=validate_requirements_tool
    ))
    
    tools.append(Tool(
        name="test_endpoints",
        description="Test API endpoints for availability and functionality",
        parameters={
            "endpoints": {"type": "array", "description": "List of endpoints to test", "required": True},
            "base_url": {"type": "string", "description": "Base URL for API", "required": False}
        },
        function=test_endpoints_tool
    ))
    
    tools.append(Tool(
        name="validate_docker",
        description="Validate Docker configuration and optionally test build",
        parameters={
            "project_path": {"type": "string", "description": "Project path", "required": False},
            "test_build": {"type": "boolean", "description": "Test Docker build", "required": False}
        },
        function=validate_docker_tool
    ))
    
    tools.append(Tool(
        name="generate_completion_report",
        description="Generate detailed completion metrics report",
        parameters={
            "project_path": {"type": "string", "description": "Project path", "required": False}
        },
        function=generate_completion_report_tool
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