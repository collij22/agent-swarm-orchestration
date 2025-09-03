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
import sys
import io
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum

# Set UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (ValueError, AttributeError, OSError):
        # If stdout/stderr are closed or unavailable, skip encoding setup
        pass

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

try:
    from .file_coordinator import FileCoordinator, get_file_coordinator
except ImportError:
    # For standalone imports
    try:
        from file_coordinator import FileCoordinator, get_file_coordinator
    except ImportError:
        # Fallback if file_coordinator doesn't exist yet
        FileCoordinator = None
        get_file_coordinator = None

def clean_reasoning(text: str, max_lines: int = 3) -> str:
    """
    Clean and deduplicate reasoning text to prevent loops.
    
    Args:
        text: Raw reasoning text
        max_lines: Maximum number of unique lines to keep
        
    Returns:
        Cleaned reasoning text
    """
    if not text:
        return text
    
    lines = text.split('\n')
    unique_lines = []
    seen = set()
    
    for line in lines:
        # Strip whitespace for comparison
        line_stripped = line.strip()
        
        # Skip empty lines and duplicates
        if line_stripped and line_stripped not in seen:
            unique_lines.append(line)
            seen.add(line_stripped)
            
            # Stop after max_lines unique lines
            if len(unique_lines) >= max_lines:
                break
    
    return '\n'.join(unique_lines)

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
                   "project-orchestrator", "meta-agent", "automated-debugger"]
    
    # Agents that can use Haiku for simple tasks
    haiku_agents = ["documentation-writer", "api-integrator"]
    
    if agent_name in opus_agents and task_complexity != "simple":
        return ModelType.OPUS
    elif agent_name in haiku_agents or task_complexity == "simple":
        return ModelType.HAIKU
    else:
        return ModelType.SONNET

# Agent Registry for centralized agent configuration
AGENT_REGISTRY = {
    'automated-debugger': {
        'model': ModelType.OPUS,
        'path': '.claude/agents/automated-debugger.md',
        'capabilities': ['error_recovery', 'build_fixing', 'validation_retry']
    },
    'project-architect': {
        'model': ModelType.OPUS,
        'path': '.claude/agents/project-architect.md',
        'capabilities': ['system_design', 'database_architecture', 'api_planning']
    },
    'rapid-builder': {
        'model': ModelType.SONNET,
        'path': '.claude/agents/rapid-builder.md',
        'capabilities': ['prototyping', 'scaffolding', 'integration']
    },
    'quality-guardian': {
        'model': ModelType.SONNET,
        'path': '.claude/agents/quality-guardian.md',
        'capabilities': ['testing', 'security_audit', 'code_review']
    },
    'quality-guardian-enhanced': {
        'model': ModelType.SONNET,
        'path': '.claude/agents/quality-guardian-enhanced.md',
        'capabilities': ['validation', 'build_testing', 'error_reporting']
    }
}

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
            self.client = None  # Explicitly set client to None for invalid keys
        
        # Only require API key if we have the anthropic library AND we're not in test mode
        if HAS_ANTHROPIC and self.api_key:
            self.logger.log_reasoning("agent_runtime", f"Creating Anthropic client with key: {self.api_key[:20]}...")
            try:
                # Create the client with a timeout-enabled HTTP client
                import httpx
                # Use httpx client with timeout for all API calls
                # Claude API calls can take a long time, especially with complex prompts
                # Set much longer timeouts to avoid premature timeouts
                http_client = httpx.Client(
                    timeout=httpx.Timeout(
                        connect=10.0,    # 10 seconds to connect
                        read=120.0,      # 120 seconds to read response (Claude can take time)  
                        write=10.0,      # 10 seconds to write request
                        pool=10.0        # 10 seconds to acquire connection from pool
                    )
                )
                self.client = Anthropic(api_key=self.api_key, http_client=http_client)
                
                # Validate the API key by making a minimal test call
                if not os.environ.get('SKIP_API_VALIDATION'):
                    import threading
                    import queue
                    
                    def validate_api_key():
                        """Validate API key in a thread to prevent hanging"""
                        try:
                            self.logger.log_reasoning("agent_runtime", "Validating API key with test call...")
                            # Make a minimal API call to validate the key
                            # Use a very simple prompt that should return quickly
                            test_response = self.client.messages.create(
                                model="claude-3-5-haiku-20241022",  # Use cheapest model
                                max_tokens=1,  # Minimal tokens
                                messages=[{"role": "user", "content": "Hi"}],
                                temperature=0
                            )
                            return True, None
                        except Exception as e:
                            return False, str(e)
                    
                    # Run validation in a thread with timeout
                    result_queue = queue.Queue()
                    
                    def run_validation():
                        success, error = validate_api_key()
                        result_queue.put((success, error))
                    
                    validation_thread = threading.Thread(target=run_validation)
                    validation_thread.daemon = True
                    validation_thread.start()
                    
                    # Wait for validation with timeout
                    validation_thread.join(timeout=30.0)  # 30 second timeout for validation (increased for slower connections)
                    
                    if validation_thread.is_alive():
                        # Validation timed out
                        self.logger.log_error("agent_runtime", "API validation timed out after 30 seconds", "Validation timeout")
                        self.client = None
                        self.api_key = None
                    else:
                        # Get validation result
                        try:
                            success, error = result_queue.get_nowait()
                            if success:
                                self.logger.log_reasoning("agent_runtime", "API key validated successfully")
                            else:
                                # API key validation failed
                                if "401" in error or "authentication" in error.lower() or "invalid" in error.lower():
                                    self.logger.log_error("agent_runtime", "Invalid API key - authentication failed", "API validation failed")
                                else:
                                    self.logger.log_error("agent_runtime", f"API validation failed: {error[:200]}", "Validation error")
                                
                                # Set client to None so orchestrator knows to exit
                                self.client = None
                                self.api_key = None
                        except queue.Empty:
                            # No result in queue (shouldn't happen)
                            self.logger.log_error("agent_runtime", "API validation failed - no result", "Validation error")
                            self.client = None
                            self.api_key = None
                        
            except Exception as e:
                # If client creation fails immediately, handle it
                self.client = None
                self.logger.log_error("agent_runtime", f"Failed to create Anthropic client: {str(e)}", "Client initialization error")
                self.api_key = None
        else:
            self.client = None
            if not self.api_key:
                if HAS_ANTHROPIC:
                    # Only warn, don't fail - allows for mock mode testing
                    self.logger.log_error("agent_runtime", "No API key provided, running in simulation mode", "API key missing")
                else:
                    self.logger.log_reasoning("agent_runtime", "Anthropic library not available, using mock mode")
    
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
            if os.environ.get('MOCK_MODE') != 'true':
                # We're in API mode but have no client
                if not self.api_key:
                    error_msg = "API mode requested but no valid ANTHROPIC_API_KEY found. Set it with: set ANTHROPIC_API_KEY=your-key-here"
                else:
                    error_msg = "API mode requested but Anthropic client initialization failed. Check your API key and network connection."
                self.logger.log_error("agent_runtime", error_msg, "API client unavailable")
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
                    # Import unicode stripper to handle emojis
                    try:
                        from .unicode_stripper import strip_unicode
                        combined_text = strip_unicode(combined_text)
                    except ImportError:
                        pass  # Continue without stripping if module not available
                    
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
                        
                        # Debug: Log the exact tool name the agent is trying to call
                        if tool_name not in self.tools:
                            self.logger.log_warning(
                                agent_name,
                                f"Agent trying to call unknown tool: '{tool_name}'",
                                f"Available tools: {list(self.tools.keys())[:10]}"
                            )
                            # Try to fix common naming mistakes
                            if tool_name.endswith("_tool"):
                                fixed_name = tool_name[:-5]  # Remove "_tool" suffix
                                if fixed_name in self.tools:
                                    self.logger.log_reasoning(
                                        agent_name,
                                        f"Fixing tool name: '{tool_name}' -> '{fixed_name}'"
                                    )
                                    tool_name = fixed_name
                        
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
                                error_msg = str(e)
                                self.logger.log_error(agent_name, error_msg, reasoning)
                                
                                # Special handling for write_file errors - don't immediately fail
                                if tool_name == "write_file" and "without content" in error_msg:
                                    # Log but continue - let error recovery handle it
                                    self.logger.log_reasoning(
                                        agent_name,
                                        "write_file error detected - will be handled by error recovery",
                                        error_msg
                                    )
                                    # Provide clear guidance to the agent
                                    error_guidance = (
                                        f"Error: {error_msg}\n\n"
                                        "IMPORTANT: The write_file tool requires both 'file_path' and 'content' parameters.\n"
                                        "Please call write_file again with BOTH parameters:\n"
                                        "- file_path: The path where to save the file\n"
                                        "- content: The actual content to write to the file\n\n"
                                        "Example:\n"
                                        "write_file(file_path='path/to/file.py', content='actual file content here')\n\n"
                                        "Do NOT try to create content in a separate step. Include it directly in the write_file call."
                                    )
                                    # Return error message as tool result to continue execution
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
                                                "content": error_guidance
                                            }
                                        ]
                                    })
                                    # Continue execution instead of breaking
                                else:
                                    # Other errors fail immediately
                                    success = False
                                    final_result = f"Tool execution failed: {error_msg}"
                                    break
                        else:
                            self.logger.log_error(agent_name, f"Unknown tool: {tool_name}")
                            success = False
                            break
                
                # If no tools were called, agent is done
                if not tool_called:
                    # Use the combined text from all blocks
                    final_result = clean_text if combined_text else "Complete"
                    # Strip unicode from final result to prevent encoding issues
                    try:
                        from .unicode_stripper import strip_unicode
                        final_result = strip_unicode(final_result)
                    except ImportError:
                        pass
                    break
                
        except Exception as e:
            self.logger.log_error(agent_name, str(e))
            success = False
            final_result = str(e)
        
        # Update context with agent results
        if success:
            context.completed_tasks.append(agent_name)
            context.artifacts[agent_name] = final_result
        
        # Strip unicode from result before logging to prevent truncation
        log_result = final_result
        try:
            from .unicode_stripper import strip_unicode
            log_result = strip_unicode(final_result)
        except ImportError:
            pass
            
        self.logger.log_agent_complete(agent_name, success, log_result[:500])
        
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
        
        # Debug: Log the signature for write_file
        if tool.name == "write_file":
            self.logger.log_reasoning(
                agent_name or "unknown",
                f"write_file signature parameters: {list(sig.parameters.keys())}"
            )
        
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
                    # Track write_file attempts for loop detection PER AGENT
                    if not hasattr(self, '_write_file_attempts'):
                        self._write_file_attempts = {}
                    
                    # Clean up old entries to prevent memory leak (keep only last 50)
                    if len(self._write_file_attempts) > 50:
                        # Keep only the most recent 25 entries
                        keys_to_keep = list(self._write_file_attempts.keys())[-25:]
                        self._write_file_attempts = {k: self._write_file_attempts[k] for k in keys_to_keep}
                    
                    file_path = args.get("file_path", "unknown")
                    # Use agent_name + file_path as key to track per-agent attempts
                    attempt_key = f"{agent_name or 'unknown'}::{file_path}"
                    
                    # Count attempts for this agent+file combination
                    if attempt_key not in self._write_file_attempts:
                        self._write_file_attempts[attempt_key] = 0
                    self._write_file_attempts[attempt_key] += 1
                    
                    # If we've tried too many times, raise an error to trigger loop breaker
                    # Increased to 4 attempts to give agents more chances
                    if self._write_file_attempts[attempt_key] > 4:
                        error_msg = f"Agent repeatedly failing to provide content for {file_path} after {self._write_file_attempts[attempt_key]} attempts"
                        self.logger.log_error(
                            agent_name or "unknown",
                            error_msg,
                            "Triggering loop breaker due to repeated failures"
                        )
                        # Reset counter for this agent+file combination
                        self._write_file_attempts[attempt_key] = 0
                        raise ValueError(error_msg)
                    
                    # Import content generator to create real content
                    try:
                        from .content_generator import ContentGenerator
                        generator = ContentGenerator({"project_name": "QuickShop MVP"})
                        
                        # Generate real content based on file type and context
                        args["content"] = generator.generate_content(file_path, "")
                        
                        # Enhanced warning with more details
                        self.logger.log_warning(
                            agent_name or "unknown",
                            f"Generated REAL content for {file_path}",
                            f"Size: {len(args['content'])} bytes | Attempt: {self._write_file_attempts[attempt_key]}/2 | Type: {file_path.split('.')[-1] if '.' in file_path else 'unknown'}"
                        )
                        # Debug: Confirm content was added
                        self.logger.log_reasoning(
                            agent_name or "unknown",
                            f"After fix - args now has keys: {list(args.keys())}"
                        )
                    except ImportError:
                        # Fallback to basic content if generator not available
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
                        
                        self.logger.log_warning(
                            agent_name or "unknown",
                            f"WARNING: Generated placeholder content for {file_path}",
                            "Agent must provide actual content in write_file call - placeholders indicate missing content parameter"
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
            
            # Check if content has placeholders even when provided
            if "content" in args and args["content"]:
                content_lower = args["content"].lower()
                if any(placeholder in content_lower for placeholder in ["todo", "fixme", "add content", "placeholder"]):
                    # Replace placeholder content with real content
                    try:
                        from .content_generator import ContentGenerator
                        generator = ContentGenerator({"project_name": "QuickShop MVP"})
                        file_path = args.get("file_path", "unknown")
                        
                        old_content = args["content"]
                        args["content"] = generator.generate_content(file_path, "")
                        
                        self.logger.log_warning(
                            agent_name or "unknown",
                            f"Replaced placeholder content with REAL content for {file_path} ({len(args['content'])} bytes)",
                            f"Agent provided placeholder: '{old_content[:50]}...'"
                        )
                    except ImportError:
                        self.logger.log_warning(
                            agent_name or "unknown",
                            "Agent provided placeholder content but generator not available",
                            f"Content: {args['content'][:100]}..."
                        )
        
        # Fix parameters for specific tools that agents commonly get wrong
        if tool.name == "share_artifact":
            # Ensure required parameters are present
            if "artifact_type" not in args:
                # Try to infer from context or use default
                args["artifact_type"] = "general"
                self.logger.log_warning(
                    agent_name or "unknown",
                    "share_artifact_tool missing artifact_type - using 'general'",
                    "Agent must provide artifact_type parameter"
                )
            
            if "content" not in args:
                # Try to extract from other parameters or use empty dict
                if "data" in args:
                    args["content"] = args.pop("data")
                elif "artifact" in args:
                    args["content"] = args.pop("artifact")
                else:
                    args["content"] = {}
                self.logger.log_warning(
                    agent_name or "unknown",
                    "share_artifact_tool missing content - using empty dict",
                    "Agent must provide content parameter"
                )
            else:
                # Even if content exists, remove alternative parameter names to avoid conflicts
                args.pop("data", None)
                args.pop("artifact", None)
        
        elif tool.name == "verify_deliverables":
            # Ensure deliverables list is present
            if "deliverables" not in args:
                # Try to extract from other parameters or use empty list
                if "files" in args:
                    args["deliverables"] = args.pop("files")
                elif "items" in args:
                    args["deliverables"] = args.pop("items")
                elif "list" in args:
                    args["deliverables"] = args.pop("list")
                else:
                    # Use a default list of common deliverables
                    args["deliverables"] = ["README.md", "requirements.txt", "main.py"]
                self.logger.log_warning(
                    agent_name or "unknown",
                    f"verify_deliverables missing deliverables - using default list",
                    f"Default: {args['deliverables']}"
                )
                # Debug: Confirm deliverables was added
                self.logger.log_reasoning(
                    agent_name or "unknown",
                    f"After fix - args now contains: {list(args.keys())}"
                )
            else:
                # Even if deliverables exists, remove alternative parameter names to avoid conflicts
                args.pop("files", None)
                args.pop("items", None)
                args.pop("list", None)
        
        elif tool.name == "dependency_check":
            # Ensure agent_name is present
            if "agent_name" not in args:
                # Use the current agent name if available
                if agent_name:
                    args["agent_name"] = agent_name
                else:
                    args["agent_name"] = "current_agent"
                self.logger.log_warning(
                    agent_name or "unknown",
                    f"dependency_check_tool missing agent_name - using '{args['agent_name']}'",
                    "Agent must provide agent_name parameter"
                )
        
        elif tool.name == "record_decision":
            # Ensure required parameters are present
            if "decision" not in args:
                args["decision"] = "Decision not specified"
                self.logger.log_warning(
                    agent_name or "unknown",
                    "record_decision_tool missing decision parameter",
                    "Using placeholder decision"
                )
            
            if "rationale" not in args:
                # Try alternative parameter names
                if "reason" in args:
                    args["rationale"] = args.pop("reason")
                elif "reasoning" in args and args["reasoning"] != args.get("rationale"):
                    args["rationale"] = args["reasoning"]
                else:
                    args["rationale"] = "Rationale not provided"
                self.logger.log_warning(
                    agent_name or "unknown",
                    "record_decision_tool missing rationale parameter",
                    f"Using: {args['rationale'][:50]}..."
                )
            else:
                # Even if rationale exists, remove alternative parameter names to avoid conflicts
                args.pop("reason", None)
                # Note: We don't remove "reasoning" as it's often a valid parameter for tools
        
        elif tool.name == "complete_task":
            # Log what we're starting with for debugging
            self.logger.log_reasoning(
                agent_name or "unknown",
                f"complete_task initial args: {list(args.keys())}"
            )
            
            # Ensure summary is present
            if "summary" not in args:
                # Try alternative parameter names
                if "description" in args:
                    args["summary"] = args.pop("description")
                elif "task" in args:
                    args["summary"] = args.pop("task")
                else:
                    args["summary"] = "Task completed"
                self.logger.log_warning(
                    agent_name or "unknown",
                    "complete_task_tool missing summary parameter",
                    f"Using: {args['summary']}"
                )
            
            # ALWAYS remove alternative parameter names to avoid conflicts
            # This must happen whether summary exists or not
            args.pop("description", None)  # Remove if exists
            args.pop("task", None)  # Remove if exists
            
            # Log what we're ending with for debugging
            self.logger.log_reasoning(
                agent_name or "unknown",
                f"complete_task after cleanup: {list(args.keys())}"
            )
        
        # Prepare function arguments
        func_args = {}
        
        # FIRST: Check if this is a wrapped function (only has 'kwargs' parameter)
        is_wrapped = len(sig.parameters) == 1 and 'kwargs' in sig.parameters
        
        if is_wrapped:
            # This is a wrapped function - pass ALL args as kwargs
            self.logger.log_reasoning(
                agent_name or "unknown",
                f"Detected wrapped function {tool.name} - passing all args as kwargs"
            )
            # Log exactly what we're passing for debugging
            if tool.name == "complete_task":
                self.logger.log_reasoning(
                    agent_name or "unknown",
                    f"complete_task wrapped: passing args keys: {list(args.keys())}"
                )
            # Pass everything including reasoning
            func_args = dict(args)  # Copy all arguments
        else:
            # Normal function - only pass parameters that are in the signature
            
            # Handle reasoning parameter if the function expects it
            if 'reasoning' in sig.parameters and 'reasoning' in args:
                func_args['reasoning'] = args['reasoning']
            
            # Copy other parameters
            for k, v in args.items():
                if k != 'reasoning':
                    if k in sig.parameters:
                        func_args[k] = v
                    else:
                        # Log when we skip a parameter
                        if tool.name in ["verify_deliverables", "share_artifact", "write_file"]:
                            self.logger.log_warning(
                                agent_name or "unknown",
                                f"Skipping parameter '{k}' - not in function signature",
                                f"Function expects: {list(sig.parameters.keys())}"
                            )
        
        # Debug: Log what we're about to call
        if tool.name in ["write_file", "share_artifact", "verify_deliverables", "dependency_check"]:
            self.logger.log_reasoning(
                agent_name or "unknown",
                f"Calling {tool.name} with func_args: {list(func_args.keys())}, original args: {list(args.keys())}"
            )
            # Extra debug for verify_deliverables
            if tool.name == "verify_deliverables" and "deliverables" not in func_args:
                self.logger.log_error(
                    agent_name or "unknown",
                    f"CRITICAL: deliverables not in func_args even after fix!",
                    f"sig.parameters: {list(sig.parameters.keys())}"
                )
        
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
        # List available MCP tools
        mcp_tools = [name for name in self.tools.keys() if name.startswith('mcp_')]
        
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
            incomplete_summary = "\n".join([f"    - {task['agent']}: {task.get('task', 'unknown task')} ({task.get('reason', task.get('error', 'unknown'))})"
                                          for task in context.incomplete_tasks[-5:]])
        
        # Build verification required summary
        verification_summary = ""
        if context.verification_required:
            verification_summary = ", ".join(context.verification_required[:10])
        
        context_str = f"""
<context>
    <project_requirements>{json.dumps(context.project_requirements, indent=2)}</project_requirements>
    <completed_tasks>{', '.join([str(task) if isinstance(task, str) else task.get('agent', 'unknown') for task in context.completed_tasks])}</completed_tasks>
    <current_phase>{context.current_phase}</current_phase>
    <previous_decisions>{json.dumps(context.decisions[-5:], indent=2) if context.decisions else 'None'}</previous_decisions>
    <created_files>
{files_summary if files_summary else '    No files created yet'}
    </created_files>
    <incomplete_tasks>
{incomplete_summary if incomplete_summary else '    No incomplete tasks'}
    </incomplete_tasks>
    <verification_required>{verification_summary if verification_summary else 'None'}</verification_required>
    <mcp_tools_available>{', '.join(mcp_tools) if mcp_tools else 'No MCP tools available'}</mcp_tools_available>
</context>

{agent_prompt}

Remember to:
1. Provide reasoning for every decision and tool use
2. Use dependency_check tool if you need artifacts from other agents
3. IMPORTANT: When using write_file, ALWAYS include both 'file_path' AND 'content' parameters in the same call
4. Never try to split file creation into multiple steps - provide the complete content immediately
3. Use request_artifact tool to get specific files or data from previous agents
4. Use verify_deliverables tool to ensure critical files exist
5. PRIORITIZE mcp_ref_search and mcp_get_docs for documentation lookups (saves 60% tokens)
6. Use mcp_ref_search BEFORE implementing features to get accurate, current patterns
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
    # Get file coordinator for locking
    coordinator = get_file_coordinator() if get_file_coordinator else None
    
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
    
    # Validate content parameter - NEVER accept empty content
    if content is None or (isinstance(content, str) and content.strip() == ""):
        # Log the error with clear guidance
        error_message = (
            f"write_file called without valid content for {file_path}\n"
            "CRITICAL: Content parameter is required and cannot be empty.\n"
            "The agent MUST provide the actual file content in the write_file call.\n"
            "Placeholder content will be generated but this indicates an error in the agent's behavior."
        )
        if context and hasattr(context, 'logger'):
            context.logger.log_error(
                agent_name or "unknown",
                error_message,
                "Agent failed to provide content - generating placeholder"
            )
        
        # Generate appropriate content based on file type
        file_ext = path.suffix.lower()
        file_name = path.stem
        
        # Generate meaningful content based on file extension
        if file_ext == '.py':
            content = f'''"""
{file_name} - Auto-generated module
This file was created because content was missing.
TODO: Implement actual functionality
"""

def main():
    """Main function - TODO: Implement"""
    raise NotImplementedError("This module needs implementation")

if __name__ == "__main__":
    main()
'''
        elif file_ext in ['.js', '.ts', '.tsx']:
            content = f'''// {file_name} - Auto-generated module
// This file was created because content was missing.
// TODO: Implement actual functionality

export default function {file_name.replace('-', '_')}() {{
    throw new Error("This module needs implementation");
}}
'''
        elif file_ext == '.json':
            content = '{\n    "error": "Content was missing - auto-generated",\n    "todo": "Replace with actual configuration"\n}'
        elif file_ext in ['.md', '.txt']:
            content = f'# {file_name}\n\nThis file was auto-generated because content was missing.\nTODO: Add actual content.'
        elif file_ext in ['.yml', '.yaml']:
            content = f'# {file_name} - Auto-generated configuration\n# TODO: Add actual configuration\n\nplaceholder: true'
        elif file_ext == '.html':
            content = f'<!DOCTYPE html>\n<html>\n<head><title>{file_name}</title></head>\n<body>\n<h1>TODO: Implement {file_name}</h1>\n</body>\n</html>'
        elif file_ext in ['.css', '.scss']:
            content = f'/* {file_name} - Auto-generated styles */\n/* TODO: Add actual styles */\n\n.placeholder {{\n    /* TODO */\n}}'
        elif file_ext == '.sh':
            content = f'#!/bin/bash\n# {file_name} - Auto-generated script\n# TODO: Add actual script\n\necho "TODO: Implement {file_name}"'
        elif file_ext == '.bat':
            content = f'@echo off\nREM {file_name} - Auto-generated script\nREM TODO: Add actual script\n\necho TODO: Implement {file_name}'
        elif file_ext in ['.env', '.ini', '.conf', '.config']:
            content = f'# {file_name} - Auto-generated configuration\n# TODO: Add actual configuration\n\nPLACEHOLDER_KEY=placeholder_value'
        else:
            # For truly unknown file types, create with a comment if possible
            content = f'# Auto-generated file: {file_name}\n# Content was missing - please add actual content\n# File type: {file_ext}'
            # Log warning if logger is available
            from .agent_logger import get_logger
            logger = get_logger()
            if logger:
                logger.log_warning(
                    agent_name or "unknown",
                    f"Unknown file type {file_ext} - creating with generic placeholder content",
                    f"File: {file_path}"
                )
        
        # Mark this as needing verification
        if context:
            if "files_needing_fix" not in context.artifacts:
                context.artifacts["files_needing_fix"] = []
            context.artifacts["files_needing_fix"].append(str(path))
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
        # Acquire file lock if coordinator is available
        if coordinator and agent_name:
            lock_acquired = coordinator.acquire_lock(
                str(path), 
                agent_name, 
                lock_type="exclusive",
                wait=True  # Wait if file is locked
            )
            
            if not lock_acquired:
                # If we can't get the lock after waiting, log warning
                if reasoning:
                    print(f"Warning: Could not acquire lock for {file_path}, proceeding anyway")
        
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
            
            # Track modification if coordinator is available
            if coordinator and agent_name:
                coordinator.track_modification(
                    str(path),
                    agent_name,
                    "create" if not path.exists() else "update"
                )
            
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
            
            # Release lock if coordinator is available
            if coordinator and agent_name:
                coordinator.release_lock(str(path), agent_name)
            
            return f"File written successfully: {file_path} (verified: {path.exists()})"
            
        except Exception as e:
            # Release lock on error
            if coordinator and agent_name:
                coordinator.release_lock(str(path), agent_name)
            
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            else:
                error_msg = f"Failed to write file after {max_retries} attempts: {str(e)}"
                if context and agent_name:
                    context.add_incomplete_task(agent_name, f"write_file: {file_path}", error_msg)
                return f"Error: {error_msg}"
        finally:
            # Always try to release lock at the end of each attempt
            if coordinator and agent_name:
                coordinator.release_lock(str(path), agent_name)
    
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

async def complete_task_tool(summary: str, artifacts: Optional[Dict] = None, reasoning: str = None, 
                           context: AgentContext = None, agent_name: str = None) -> str:
    """Mark current agent task as complete"""
    # Store artifacts if provided
    if artifacts and context:
        for key, value in artifacts.items():
            context.artifacts[f"{agent_name}_{key}" if agent_name else key] = value
    
    # Mark task as completed
    if context and agent_name:
        context.completed_tasks.append(f"{agent_name}: {summary}")
    
    return f"Task completed: {summary}"

async def share_artifact_tool(artifact_type: str, content: Any, description: str = None,
                             reasoning: str = None, context: AgentContext = None, 
                             agent_name: str = None) -> str:
    """
    Share an artifact with other agents for coordination.
    
    Args:
        artifact_type: Type of artifact (e.g., "api_schema", "database_model", "config")
        content: The actual artifact content (can be dict, list, str, etc.)
        description: Optional description of the artifact
        reasoning: Why this artifact is being shared
        context: Agent context for storing artifacts
        agent_name: Name of the agent sharing the artifact
    
    Returns:
        Confirmation message
    """
    if context is None:
        return "Error: No context available for sharing artifacts"
    
    # Create artifact key
    artifact_key = f"{agent_name}_{artifact_type}" if agent_name else artifact_type
    
    # Store the artifact with metadata
    artifact_data = {
        "content": content,
        "type": artifact_type,
        "shared_by": agent_name or "unknown",
        "description": description or f"Shared {artifact_type}",
        "timestamp": time.time()
    }
    
    context.artifacts[artifact_key] = artifact_data
    
    # Log the sharing
    if description:
        return f"Shared {artifact_type}: {description}"
    else:
        return f"Shared {artifact_type} for other agents to use"

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
        description="Write content to a file. CRITICAL: You MUST provide BOTH file_path AND content in the SAME call. Never call write_file without the actual file content. Include the complete code/text content, not placeholders.",
        parameters={
            "file_path": {"type": "string", "description": "Path to file", "required": True},
            "content": {"type": "string", "description": "ACTUAL content to write - the complete file contents, not a placeholder or description", "required": True}
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
        name="share_artifact",
        description="Share an artifact with other agents for coordination",
        parameters={
            "artifact_type": {"type": "string", "description": "Type of artifact (e.g., 'api_schema', 'database_model', 'config')", "required": True},
            "content": {"type": "object", "description": "The actual artifact content", "required": True},
            "description": {"type": "string", "description": "Description of the artifact", "required": False}
        },
        function=share_artifact_tool
    ))
    
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
            "deliverables": {"type": "array", "items": {"type": "string"}, "description": "List of file paths to verify", "required": True}
        },
        function=verify_deliverables_tool
    ))
    
    return tools

def create_mcp_enhanced_tools() -> List[Tool]:
    """Create MCP-enhanced tools if MCP servers are available"""
    try:
        from .mcp_tools import create_mcp_tools
        return create_mcp_tools()
    except ImportError:
        # MCP not available, return empty list
        return []

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