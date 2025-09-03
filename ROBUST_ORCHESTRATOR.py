#!/usr/bin/env python3
"""
ROBUST ORCHESTRATOR v8.0 - The Most Resilient Multi-Agent System
================================================================

Key Improvements from Session b2e1d40b Analysis:
- Tool call interception to fix missing parameters
- Auto-content generation for missing content
- Clearer examples in agent prompts  
- Better error recovery with specific guidance
- Communication flow validation

Critical Fix: Agents were calling write_file without content parameter
Solution: Intercept and fix tool calls before they fail
"""

import json
import os
import sys
import time
import asyncio
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import networkx as nx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import our libraries
from lib.agent_runtime import AnthropicAgentRunner, AgentContext, create_standard_tools, ModelType

# Configure UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('robust_orchestrator.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RequirementNode:
    """Represents a requirement with dependencies"""
    id: str
    description: str
    priority: int
    agents: List[str]
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    assigned_agent: Optional[str] = None
    completion: float = 0.0
    artifacts: List[str] = field(default_factory=list)
    error_count: int = 0

class ToolCallInterceptor:
    """Intercepts and fixes tool calls with missing parameters"""
    
    def __init__(self):
        self.content_templates = {
            '.py': '"""TODO: Implement this module"""\n\nraise NotImplementedError("This module needs implementation")',
            '.js': '// TODO: Implement this module\nthrow new Error("This module needs implementation");',
            '.ts': '// TODO: Implement this module\nthrow new Error("This module needs implementation");',
            '.tsx': 'import React from "react";\n\nexport default function Component() {\n  return <div>TODO: Implement component</div>;\n}',
            '.jsx': 'import React from "react";\n\nexport default function Component() {\n  return <div>TODO: Implement component</div>;\n}',
            '.json': '{\n  "error": "TODO: Add actual content",\n  "placeholder": true\n}',
            '.md': '# TODO: Add Documentation\n\nThis file needs proper content.',
            '.yaml': '# TODO: Add configuration\nplaceholder: true',
            '.yml': '# TODO: Add configuration\nplaceholder: true',
            '.html': '<!DOCTYPE html>\n<html>\n<head><title>TODO</title></head>\n<body><h1>TODO: Add content</h1></body>\n</html>',
            '.css': '/* TODO: Add styles */\nbody { margin: 0; padding: 0; }',
            '.scss': '/* TODO: Add styles */\nbody { margin: 0; padding: 0; }',
            '.sh': '#!/bin/bash\n# TODO: Add script\necho "Script needs implementation"',
            '.bat': '@echo off\nREM TODO: Add script\necho Script needs implementation',
            '.env': '# TODO: Add environment variables\n# EXAMPLE_VAR=value',
            '.txt': 'TODO: Add content',
            '.sql': '-- TODO: Add SQL queries\n-- This file needs implementation',
            '.dockerfile': '# TODO: Add Dockerfile content\nFROM alpine:latest',
            '.gitignore': '# TODO: Add ignore patterns\n*.log\nnode_modules/',
            'default': 'TODO: Add content for this file'
        }
        
        self.intercepted_calls = []
        self.fixed_calls = []
    
    def intercept_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intercept tool calls and fix missing parameters
        """
        self.intercepted_calls.append({
            "tool": tool_name,
            "original_params": params.copy(),
            "timestamp": datetime.now().isoformat()
        })
        
        if tool_name == "write_file":
            # Check if content is missing or empty
            if "content" not in params or not params.get("content") or params.get("content").strip() == "":
                file_path = params.get("file_path", "unknown.txt")
                
                # Generate appropriate content based on file extension
                ext = Path(file_path).suffix.lower()
                content = self.content_templates.get(ext, self.content_templates['default'])
                
                # Add warning header
                warning_header = f"# WARNING: Auto-generated content - Agent failed to provide content\n# File: {file_path}\n# Time: {datetime.now()}\n\n"
                
                if ext in ['.py', '.js', '.ts', '.tsx', '.jsx']:
                    params["content"] = f'"""\n{warning_header}"""\n\n{content}'
                elif ext in ['.md', '.yaml', '.yml', '.sh', '.sql']:
                    params["content"] = f"{warning_header}{content}"
                else:
                    params["content"] = content
                
                self.fixed_calls.append({
                    "file": file_path,
                    "generated_content": True,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.warning(f"🔧 Auto-generated content for {file_path} - agent didn't provide content")
        
        return params
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get interception statistics"""
        return {
            "total_intercepted": len(self.intercepted_calls),
            "total_fixed": len(self.fixed_calls),
            "files_needing_content": [f["file"] for f in self.fixed_calls]
        }

class CommunicationFlowValidator:
    """Validates and improves agent communication flow"""
    
    def __init__(self):
        self.communication_log = []
        self.error_patterns = {}
        self.successful_patterns = []
    
    def validate_agent_response(self, agent_name: str, response: str) -> Tuple[bool, str]:
        """
        Validate agent response and provide guidance
        """
        issues = []
        
        # Check for common communication issues
        if "TODO" in response and "content" not in response.lower():
            issues.append("Agent mentioned TODO but didn't provide actual implementation")
        
        if "let me" in response.lower() and response.count("let me") > 2:
            issues.append("Agent is repeating intentions without taking action")
        
        if "write_file" in response and '"content":' not in response:
            issues.append("Agent calling write_file without content parameter")
        
        if issues:
            guidance = self._generate_guidance(agent_name, issues)
            return False, guidance
        
        return True, ""
    
    def _generate_guidance(self, agent_name: str, issues: List[str]) -> str:
        """Generate specific guidance for the agent"""
        guidance = f"\n⚠️ CRITICAL INSTRUCTIONS FOR {agent_name}:\n\n"
        
        for issue in issues:
            if "content parameter" in issue:
                guidance += """
CORRECT write_file usage - BOTH parameters in SAME call:
```python
write_file(
    file_path="example.py",
    content="actual file content here"  # REQUIRED!
)
```

WRONG (what you're doing):
```python
write_file(file_path="example.py")  # Missing content!
```

You MUST include the actual file content in the SAME tool call!
"""
            elif "TODO" in issue:
                guidance += """
You mentioned TODO but didn't provide implementation.
Write the ACTUAL code/content, not placeholders!
"""
            elif "repeating intentions" in issue:
                guidance += """
Stop saying what you'll do and DO IT!
Take action immediately with the correct parameters.
"""
        
        return guidance

class RobustOrchestrator:
    """Enhanced orchestrator with robust error handling and communication flow"""
    
    def __init__(self, requirements_file: str = None, output_dir: str = None, max_workers: int = 3):
        self.start_time = time.time()
        self.requirements_file = requirements_file or "requirements.yaml"
        self.output_dir = Path(output_dir or "projects/quickshop-mvp-robust")
        self.max_workers = max_workers
        
        # Initialize components
        self.interceptor = ToolCallInterceptor()
        self.flow_validator = CommunicationFlowValidator()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize agent runtime with interception
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        # Wrap the runner to intercept tool calls
        original_runner = AnthropicAgentRunner(api_key=api_key)
        self.runner = self._create_intercepting_runner(original_runner)
        
        # Initialize tracking
        self.requirements: List[RequirementNode] = []
        self.dependency_graph = nx.DiGraph()
        self.context = AgentContext(
            project_requirements={
                "project_name": "QuickShop MVP",
                "description": "Modern e-commerce platform",
                "tech_stack": {
                    "frontend": "React + TypeScript + Tailwind CSS",
                    "backend": "FastAPI + PostgreSQL",
                    "deployment": "Docker + docker-compose"
                }
            },
            completed_tasks=[],
            artifacts={
                "output_dir": str(self.output_dir),
                "project_directory": str(self.output_dir),
                "project_base": str(self.output_dir),
                "files_created": [],
                "files_needing_fix": []
            }
        )
        
        # Agent configuration with enhanced prompts
        self.agents = self._get_enhanced_agent_configs()
        
        # Execution tracking
        self.execution_log = []
        self.failed_agents: Set[str] = set()
        self.agent_retries: Dict[str, int] = {}
        self.max_retries = 3
    
    def _create_intercepting_runner(self, original_runner):
        """Create a wrapper that intercepts tool calls"""
        class InterceptingRunner:
            def __init__(self, runner, interceptor):
                self.runner = runner
                self.interceptor = interceptor
            
            def run_agent(self, agent_name: str, agent_prompt: str, context: AgentContext):
                # Intercept the tools
                original_tools = create_standard_tools(context)
                
                # Wrap each tool to intercept calls
                intercepted_tools = {}
                for tool_name, tool_func in original_tools.items():
                    def make_intercepted_tool(name, func):
                        def intercepted(**kwargs):
                            # Intercept and fix parameters
                            fixed_params = self.interceptor.intercept_tool_call(name, kwargs)
                            return func(**fixed_params)
                        return intercepted
                    
                    intercepted_tools[tool_name] = make_intercepted_tool(tool_name, tool_func)
                
                # Temporarily replace tools
                import lib.agent_runtime
                original_create_tools = lib.agent_runtime.create_standard_tools
                lib.agent_runtime.create_standard_tools = lambda ctx: intercepted_tools
                
                try:
                    # Run with intercepted tools
                    result = self.runner.run_agent(agent_name, agent_prompt, context)
                finally:
                    # Restore original tools
                    lib.agent_runtime.create_standard_tools = original_create_tools
                
                return result
        
        return InterceptingRunner(original_runner, self.interceptor)
    
    def _get_enhanced_agent_configs(self) -> Dict[str, Dict]:
        """Get agent configurations with enhanced prompts for content requirement"""
        
        base_instruction = """
⚠️ CRITICAL TOOL USAGE INSTRUCTIONS ⚠️

When using write_file tool, you MUST include BOTH parameters in the SAME call:

CORRECT ✅:
```
write_file(
    file_path="path/to/file.py",
    content="actual file content here"
)
```

WRONG ❌ (what causes errors):
```
write_file(file_path="path/to/file.py")  # Missing content!
```

NEVER split parameters across multiple calls!
ALWAYS include the complete file content in the content parameter!
"""
        
        return {
            "requirements-analyst": {
                "model": ModelType.SONNET,
                "system_prompt": f"""You are a requirements analyst creating comprehensive documentation.

{base_instruction}

Your task is to analyze requirements and create detailed specification documents.
When creating files, include the FULL content in the write_file call.

Example for creating a requirements file:
```
write_file(
    file_path="REQUIREMENTS.md",
    content="# Requirements\\n\\nFull requirements content here..."
)
```

DO NOT create files without content!
""",
                "priority": 1
            },
            "rapid-builder": {
                "model": ModelType.SONNET,
                "system_prompt": f"""You are a rapid application builder.

{base_instruction}

Create working implementations with actual code, not placeholders.
Every file must have complete, functional content.

Example:
```
write_file(
    file_path="src/main.py",
    content='\"\"\"Main application module\"\"\"\\n\\nimport fastapi\\n\\napp = fastapi.FastAPI()\\n\\n@app.get("/")\\ndef root():\\n    return {{"message": "Hello World"}}'
)
```
""",
                "priority": 2
            },
            "automated-debugger": {
                "model": ModelType.HAIKU,
                "system_prompt": f"""You are an automated debugger that fixes issues.

{base_instruction}

When you fix files, always provide the complete corrected content.
Never leave placeholders or TODOs without implementation.
""",
                "priority": 3
            }
        }
    
    def _load_requirements(self):
        """Load and parse requirements"""
        # For now, create default requirements
        self.requirements = [
            RequirementNode(
                id="REQ-001",
                description="Create project documentation",
                priority=1,
                agents=["requirements-analyst"]
            ),
            RequirementNode(
                id="REQ-002", 
                description="Build core application",
                priority=2,
                agents=["rapid-builder"],
                dependencies=["REQ-001"]
            )
        ]
        
        # Build dependency graph
        for req in self.requirements:
            self.dependency_graph.add_node(req.id, requirement=req)
            for dep in req.dependencies:
                self.dependency_graph.add_edge(dep, req.id)
    
    def _get_ready_requirements(self) -> List[RequirementNode]:
        """Get requirements that are ready to execute"""
        ready = []
        for req in self.requirements:
            if req.status == "pending":
                # Check if all dependencies are completed
                deps_completed = all(
                    self._get_requirement(dep).status == "completed"
                    for dep in req.dependencies
                )
                if deps_completed:
                    ready.append(req)
        return ready
    
    def _get_requirement(self, req_id: str) -> Optional[RequirementNode]:
        """Get requirement by ID"""
        for req in self.requirements:
            if req.id == req_id:
                return req
        return None
    
    def _execute_agent(self, agent_name: str, requirement: RequirementNode) -> bool:
        """Execute an agent with enhanced error handling"""
        
        logger.info(f"🚀 Executing {agent_name} for {requirement.id}")
        
        # Get agent config
        agent_config = self.agents.get(agent_name, {})
        
        # Build prompt with specific instructions
        prompt = f"""
{agent_config.get('system_prompt', '')}

CURRENT TASK: {requirement.description}

Project Context:
- Output Directory: {self.output_dir}
- Tech Stack: React + TypeScript + Tailwind (Frontend), FastAPI + PostgreSQL (Backend)

⚠️ REMEMBER: Always include content parameter when calling write_file!

Previous attempts that failed (if any):
{self._get_retry_context(agent_name)}

Complete the task with actual implementations, not placeholders.
"""
        
        try:
            # Execute agent
            success, response, updated_context = self.runner.run_agent(
                agent_name=agent_name,
                agent_prompt=prompt,
                context=self.context
            )
            
            # Validate communication flow
            valid, guidance = self.flow_validator.validate_agent_response(agent_name, str(response))
            
            if not valid and self.agent_retries.get(agent_name, 0) < self.max_retries:
                # Retry with guidance
                self.agent_retries[agent_name] = self.agent_retries.get(agent_name, 0) + 1
                logger.warning(f"❌ Communication issue detected, retrying with guidance")
                
                retry_prompt = f"{prompt}\n\n{guidance}"
                success, response, updated_context = self.runner.run_agent(
                    agent_name=agent_name,
                    agent_prompt=retry_prompt,
                    context=self.context
                )
            
            if success:
                self.context = updated_context
                requirement.status = "completed"
                requirement.completion = 100.0
                
                # Check if any files need fixing
                if self.interceptor.fixed_calls:
                    self.context.artifacts["files_needing_fix"] = [
                        f["file"] for f in self.interceptor.fixed_calls
                    ]
                    logger.warning(f"⚠️ {len(self.interceptor.fixed_calls)} files need proper content")
                
                logger.info(f"✅ {agent_name} completed successfully")
                return True
            else:
                logger.error(f"❌ {agent_name} failed: {response}")
                requirement.error_count += 1
                
                # Try automated debugger if available
                if agent_name != "automated-debugger" and requirement.error_count <= 2:
                    logger.info("🔧 Triggering automated debugger")
                    self._trigger_debugger(agent_name, requirement, str(response))
                
                return False
                
        except Exception as e:
            logger.error(f"❌ Error executing {agent_name}: {e}")
            traceback.print_exc()
            requirement.error_count += 1
            return False
    
    def _get_retry_context(self, agent_name: str) -> str:
        """Get context about previous retry attempts"""
        if agent_name not in self.agent_retries:
            return "None"
        
        return f"""
This agent has failed {self.agent_retries[agent_name]} times.
Common issue: Not providing content parameter in write_file calls.
Fix: Include BOTH file_path AND content in the SAME tool call.
"""
    
    def _trigger_debugger(self, failed_agent: str, requirement: RequirementNode, error: str):
        """Trigger automated debugger to fix issues"""
        
        debug_prompt = f"""
An agent failed with the following error:
Agent: {failed_agent}
Requirement: {requirement.description}
Error: {error}

Files that need proper content:
{json.dumps(self.context.artifacts.get("files_needing_fix", []), indent=2)}

Please fix any files with placeholder content and resolve the issues.
Remember to provide COMPLETE file content, not just placeholders.
"""
        
        try:
            success, response, updated_context = self.runner.run_agent(
                agent_name="automated-debugger",
                agent_prompt=debug_prompt,
                context=self.context
            )
            
            if success:
                self.context = updated_context
                logger.info("✅ Automated debugger fixed issues")
            else:
                logger.warning("⚠️ Automated debugger couldn't fix all issues")
                
        except Exception as e:
            logger.error(f"❌ Debugger error: {e}")
    
    def execute(self):
        """Execute the orchestration with robust error handling"""
        
        logger.info("=" * 80)
        logger.info("ROBUST ORCHESTRATOR v8.0 - Starting Execution")
        logger.info("=" * 80)
        
        # Load requirements
        self._load_requirements()
        logger.info(f"📋 Loaded {len(self.requirements)} requirements")
        
        # Execute requirements
        completed = 0
        failed = 0
        
        while True:
            ready = self._get_ready_requirements()
            
            if not ready:
                if all(req.status == "completed" for req in self.requirements):
                    logger.info("✅ All requirements completed!")
                    break
                elif all(req.status in ["completed", "failed"] for req in self.requirements):
                    logger.warning("⚠️ Some requirements failed, cannot continue")
                    break
                else:
                    logger.info("⏳ Waiting for dependencies...")
                    time.sleep(2)
                    continue
            
            # Execute ready requirements
            for req in ready:
                req.status = "in_progress"
                
                # Select agent
                agent_name = req.agents[0] if req.agents else "rapid-builder"
                
                # Execute
                if self._execute_agent(agent_name, req):
                    completed += 1
                else:
                    if req.error_count >= 3:
                        req.status = "failed"
                        failed += 1
                        self.failed_agents.add(agent_name)
                    else:
                        req.status = "pending"  # Retry later
        
        # Final report
        self._generate_final_report(completed, failed)
    
    def _generate_final_report(self, completed: int, failed: int):
        """Generate final execution report"""
        
        duration = time.time() - self.start_time
        
        report = f"""
{"=" * 80}
ROBUST ORCHESTRATOR v8.0 - EXECUTION COMPLETE
{"=" * 80}

📊 EXECUTION METRICS:
- Total Requirements: {len(self.requirements)}
- Completed: {completed}
- Failed: {failed}
- Success Rate: {(completed / len(self.requirements) * 100):.1f}%
- Duration: {duration:.2f} seconds

🔧 TOOL INTERCEPTION STATISTICS:
{json.dumps(self.interceptor.get_statistics(), indent=2)}

📁 OUTPUT:
- Directory: {self.output_dir}
- Files Created: {len(self.context.artifacts.get('files_created', []))}
- Files Needing Fix: {len(self.context.artifacts.get('files_needing_fix', []))}

{"=" * 80}
"""
        
        logger.info(report)
        
        # Save report
        report_file = self.output_dir / "execution_report.json"
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "completed": completed,
            "failed": failed,
            "interception_stats": self.interceptor.get_statistics(),
            "artifacts": self.context.artifacts
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"📄 Report saved to {report_file}")

def main():
    """Main entry point"""
    try:
        orchestrator = RobustOrchestrator(
            output_dir="projects/quickshop-mvp-robust",
            max_workers=3
        )
        orchestrator.execute()
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Execution interrupted by user")
        return 2
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())