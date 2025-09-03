#!/usr/bin/env python3
"""
FINAL OPTIMIZED INTELLIGENT ORCHESTRATOR v5.0
Complete fix with file creation verification
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
import uuid

# Add the parent directory to the path to import from lib
sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_runtime import (
    AnthropicAgentRunner, 
    AgentContext,
    create_standard_tools
)

# ===================== Data Classes =====================

@dataclass
class AgentResult:
    """Store structured agent execution results"""
    agent_name: str
    success: bool
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)  
    duration: float = 0.0
    error_message: Optional[str] = None
    artifacts_produced: Dict[str, Any] = field(default_factory=dict)
    tool_calls_made: List[Dict[str, Any]] = field(default_factory=list)

class CommunicationHub:
    """Enhanced centralized communication and artifact management"""
    
    def __init__(self):
        self.agent_outputs: Dict[str, AgentResult] = {}
        self.shared_artifacts: Dict[str, Any] = {}
        self.file_registry: Dict[str, str] = {}  # filename -> creating_agent
        self.agent_messages: List[Dict[str, str]] = []
        self.tool_call_log: Dict[str, List[Dict]] = {}  # agent -> tool calls
        
    def register_output(self, agent_name: str, result: AgentResult):
        """Register agent output with enhanced tracking"""
        self.agent_outputs[agent_name] = result
        
        # Track files created by this agent
        for file in result.files_created:
            self.file_registry[file] = agent_name
            
        # Log tool calls
        if result.tool_calls_made:
            if agent_name not in self.tool_call_log:
                self.tool_call_log[agent_name] = []
            self.tool_call_log[agent_name].extend(result.tool_calls_made)
    
    def get_agent_summary(self, agent_name: str) -> str:
        """Get formatted summary of agent output"""
        if agent_name not in self.agent_outputs:
            return f"{agent_name}: Not executed yet"
        
        result = self.agent_outputs[agent_name]
        if result.success:
            files_info = ""
            if result.files_created:
                files_info = f"\n  - Created: {', '.join(result.files_created)}"
            if result.files_modified:
                files_info += f"\n  - Modified: {', '.join(result.files_modified)}"
            
            tool_info = ""
            if agent_name in self.tool_call_log:
                tool_counts = {}
                for call in self.tool_call_log[agent_name]:
                    tool_name = call.get('tool', 'unknown')
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
                tool_info = f"\n  - Tools used: {', '.join([f'{tool}({count})' for tool, count in tool_counts.items()])}"
            
            return f"{agent_name}: SUCCESS ({result.duration:.1f}s){files_info}{tool_info}"
        else:
            return f"{agent_name}: FAILED - {result.error_message}"
    
    def share_artifact(self, key: str, value: Any, agent_name: str):
        """Share an artifact between agents"""
        self.shared_artifacts[key] = {
            "value": value,
            "shared_by": agent_name,
            "timestamp": datetime.now().isoformat()
        }
        
    def get_artifact(self, key: str) -> Any:
        """Get a shared artifact"""
        if key in self.shared_artifacts:
            return self.shared_artifacts[key]["value"]
        return None
    
    def add_message(self, from_agent: str, to_agent: str, message: str):
        """Add inter-agent message"""
        self.agent_messages.append({
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

class FileTracker:
    """Enhanced file tracking with verification"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.file_snapshots: Dict[str, Set[Path]] = {}
        
    def snapshot(self, label: str) -> Set[Path]:
        """Take a snapshot of current files"""
        current_files = self.get_current_files()
        self.file_snapshots[label] = current_files
        return current_files
        
    def get_current_files(self) -> Set[Path]:
        """Get all files in output directory (excluding directories)"""
        files = set()
        if self.output_dir.exists():
            for item in self.output_dir.rglob('*'):
                if item.is_file():
                    files.add(item)
        return files
    
    def get_new_files(self, before_label: str, after_label: str = None) -> List[str]:
        """Get files created between two snapshots"""
        if after_label:
            after_files = self.file_snapshots.get(after_label, set())
        else:
            after_files = self.get_current_files()
            
        before_files = self.file_snapshots.get(before_label, set())
        new_files = after_files - before_files
        
        # Return relative paths as strings
        return [str(f.relative_to(self.output_dir)) for f in new_files]
    
    def verify_file_exists(self, file_path: str) -> bool:
        """Verify a file actually exists on disk"""
        full_path = self.output_dir / file_path
        return full_path.exists() and full_path.is_file()
    
    def get_file_content_preview(self, file_path: str, max_lines: int = 5) -> str:
        """Get a preview of file content"""
        full_path = self.output_dir / file_path
        if not full_path.exists():
            return "File not found"
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:max_lines]
                preview = ''.join(lines)
                if len(lines) == max_lines:
                    preview += f"\n... ({len(open(full_path).readlines())} total lines)"
                return preview
        except Exception as e:
            return f"Error reading file: {e}"

class DependencyGraph:
    """Manage agent dependencies"""
    
    def __init__(self):
        self.dependencies = {
            "requirements-analyst": [],
            "project-architect": ["requirements-analyst"],
            "database-expert": ["project-architect"],
            "rapid-builder": ["project-architect", "database-expert"],
            "frontend-specialist": ["project-architect"],
            "api-integrator": ["rapid-builder", "frontend-specialist"],
            "devops-engineer": ["rapid-builder", "api-integrator"],
            "quality-guardian": ["devops-engineer"]
        }
        
        # Define which agents can run in parallel
        self.parallel_groups = [
            ["database-expert", "rapid-builder", "frontend-specialist"],
            ["devops-engineer", "quality-guardian"]
        ]
        
    def can_run(self, agent: str, completed: Set[str]) -> bool:
        """Check if agent can run based on completed dependencies"""
        return all(dep in completed for dep in self.dependencies.get(agent, []))
    
    def get_ready_agents(self, completed: Set[str], running: Set[str] = None) -> List[str]:
        """Get agents ready to run"""
        running = running or set()
        ready = []
        
        for agent in self.dependencies:
            if agent not in completed and agent not in running:
                if self.can_run(agent, completed):
                    ready.append(agent)
                    
        return ready
    
    def get_parallel_group(self, ready_agents: List[str]) -> List[str]:
        """Get agents that can run in parallel"""
        for group in self.parallel_groups:
            # Check if all agents in group are ready
            if all(agent in ready_agents for agent in group):
                return group
        
        # No parallel group found, return first ready agent
        return [ready_agents[0]] if ready_agents else []

# ===================== Orchestrator =====================

class FinalOptimizedOrchestrator:
    """Final optimized orchestrator with complete file creation fix"""
    
    def __init__(self, api_key: str, output_dir: Path):
        self.api_key = api_key
        self.output_dir = output_dir
        self.runner = AnthropicAgentRunner(api_key=api_key)
        self.context = None
        self.comm_hub = CommunicationHub()
        self.file_tracker = FileTracker(output_dir)
        self.dependency_graph = DependencyGraph()
        
        # Register tools
        for tool in create_standard_tools():
            self.runner.register_tool(tool)
            
        # Track execution
        self.completed_agents = set()
        self.failed_agents = set()
        self.execution_log = []
        
    def initialize_context(self, requirements: Dict) -> AgentContext:
        """Initialize context with proper project directory"""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        context = AgentContext(
            project_requirements=requirements,
            completed_tasks=[],  # For strings
            artifacts={
                "output_dir": str(self.output_dir),
                "project_directory": str(self.output_dir),  # Critical for write_file_tool
                "project_base": str(self.output_dir),       # Additional fallback
                "working_directory": str(self.output_dir)   # Extra safety
            },
            decisions=[],
            current_phase="initialization"
        )
        
        return context
    
    def build_agent_prompt(self, agent_name: str) -> str:
        """Build enhanced prompt with file creation emphasis"""
        
        # Get dependency outputs
        dependency_summaries = []
        for dep in self.dependency_graph.dependencies.get(agent_name, []):
            summary = self.comm_hub.get_agent_summary(dep)
            dependency_summaries.append(summary)
        
        # Get shared artifacts
        relevant_artifacts = {}
        if agent_name == "rapid-builder":
            schema = self.comm_hub.get_artifact("database_schema")
            if schema:
                relevant_artifacts["database_schema"] = schema
        elif agent_name == "api-integrator":
            endpoints = self.comm_hub.get_artifact("api_endpoints")
            if endpoints:
                relevant_artifacts["api_endpoints"] = endpoints
        
        prompt = f"""You are {agent_name}, a specialized AI agent building a QuickShop MVP e-commerce application.

## CRITICAL INSTRUCTIONS
1. You MUST create actual files using the write_file tool
2. Files should be created in the project directory: {self.output_dir}
3. Use paths like "backend/main.py" or "frontend/src/App.tsx" (relative paths)
4. DO NOT use absolute paths starting with C:\\ or /
5. ALWAYS verify your files are created by checking the response

## Your Role
{self._get_agent_description(agent_name)}

## Output Directory
All files should be created under: {self.output_dir}

## Dependencies Completed
{chr(10).join(dependency_summaries) if dependency_summaries else "No dependencies"}

## Shared Artifacts
{json.dumps(relevant_artifacts, indent=2) if relevant_artifacts else "No shared artifacts"}

## Project Requirements
{json.dumps(self.context.project_requirements, indent=2)}

## Expected Deliverables
{self._get_agent_deliverables(agent_name)}

## File Creation Examples
- Backend: "backend/main.py", "backend/models.py", "backend/database.py"
- Frontend: "frontend/src/App.tsx", "frontend/src/components/Header.tsx"
- Config: "docker-compose.yml", ".env.example", "README.md"
- Database: "database/schema.sql", "database/migrations/001_initial.sql"

IMPORTANT: You must create actual working files with real implementation code, not just placeholders!
"""
        return prompt
    
    def _get_agent_description(self, agent_name: str) -> str:
        """Get agent-specific description"""
        descriptions = {
            "requirements-analyst": "Analyze requirements and create detailed specifications",
            "project-architect": "Design system architecture and create technical blueprints",
            "database-expert": "Design and implement database schema with PostgreSQL",
            "rapid-builder": "Build the backend API with FastAPI",
            "frontend-specialist": "Create the React frontend with TypeScript",
            "api-integrator": "Integrate frontend with backend APIs",
            "devops-engineer": "Set up Docker containers and deployment configuration",
            "quality-guardian": "Perform testing and quality assurance"
        }
        return descriptions.get(agent_name, "Specialized development agent")
    
    def _get_agent_deliverables(self, agent_name: str) -> str:
        """Get expected deliverables for each agent"""
        deliverables = {
            "requirements-analyst": """
- REQUIREMENTS.md with detailed specifications
- DATABASE_SCHEMA.md with schema design
- API_SPEC.md with endpoint definitions
""",
            "project-architect": """
- ARCHITECTURE.md with system design
- TECH_STACK.md with technology choices
- PROJECT_STRUCTURE.md with folder organization
""",
            "database-expert": """
- database/schema.sql with complete schema
- database/migrations/ with migration files
- database/seed_data.sql with test data
""",
            "rapid-builder": """
- backend/main.py with FastAPI application
- backend/models.py with Pydantic models
- backend/database.py with database connection
- backend/routes/ with API endpoints
- backend/requirements.txt with dependencies
""",
            "frontend-specialist": """
- frontend/src/App.tsx main application
- frontend/src/components/ React components
- frontend/src/pages/ page components
- frontend/package.json with dependencies
- frontend/tsconfig.json TypeScript config
""",
            "api-integrator": """
- frontend/src/api/ API client functions
- frontend/src/hooks/ custom React hooks
- backend/middleware/ CORS and auth middleware
- Integration tests
""",
            "devops-engineer": """
- docker-compose.yml for local development
- Dockerfile for backend
- Dockerfile for frontend
- .env.example with environment variables
- nginx.conf for reverse proxy
""",
            "quality-guardian": """
- tests/ directory with test files
- TEST_REPORT.md with test results
- QUALITY_CHECKLIST.md with verification
- Performance metrics
"""
        }
        return deliverables.get(agent_name, "Create relevant files for your role")
    
    async def execute_agent(self, agent_name: str, retries: int = 2) -> AgentResult:
        """Execute a single agent with file verification"""
        
        print(f"\n{'='*60}")
        print(f"Executing: {agent_name}")
        print(f"{'='*60}")
        
        # Take file snapshot before execution
        before_snapshot = self.file_tracker.snapshot(f"{agent_name}_before")
        
        # Build prompt
        prompt = self.build_agent_prompt(agent_name)
        
        # Track tool calls
        tool_calls = []
        
        # Execute agent
        start_time = time.time()
        last_error = None
        
        for attempt in range(retries):
            try:
                if attempt > 0:
                    print(f"  Retry {attempt}/{retries-1}...")
                    prompt += f"\n\n## Previous Error\n{last_error}\nPlease fix the issue and try again."
                
                # Execute agent
                result = await self.runner.run_agent_async(
                    agent_name=agent_name,
                    prompt=prompt,
                    context=self.context
                )
                
                # Extract tool calls from result if available
                if hasattr(result, 'tool_calls'):
                    tool_calls = result.tool_calls
                elif isinstance(result, dict) and 'tool_calls' in result:
                    tool_calls = result.get('tool_calls', [])
                
                # Success! Update context
                self.context.completed_tasks.append(f"{agent_name}: SUCCESS")
                
                # Take snapshot after execution
                after_snapshot = self.file_tracker.snapshot(f"{agent_name}_after")
                new_files = self.file_tracker.get_new_files(f"{agent_name}_before", f"{agent_name}_after")
                
                # Verify files were actually created
                verified_files = []
                for file in new_files:
                    if self.file_tracker.verify_file_exists(file):
                        verified_files.append(file)
                        print(f"  ✓ Created: {file}")
                    else:
                        print(f"  ✗ Missing: {file}")
                
                # Create result
                agent_result = AgentResult(
                    agent_name=agent_name,
                    success=True,
                    files_created=verified_files,
                    duration=time.time() - start_time,
                    tool_calls_made=tool_calls
                )
                
                # Register with communication hub
                self.comm_hub.register_output(agent_name, agent_result)
                
                # Share artifacts if needed
                if agent_name == "database-expert" and verified_files:
                    # Find and share schema file
                    for file in verified_files:
                        if 'schema' in file.lower():
                            self.comm_hub.share_artifact("database_schema", file, agent_name)
                            break
                
                print(f"  Status: SUCCESS")
                print(f"  Files created: {len(verified_files)}")
                print(f"  Duration: {agent_result.duration:.1f}s")
                
                return agent_result
                
            except Exception as e:
                last_error = str(e)
                print(f"  Error: {last_error}")
                
                if attempt == retries - 1:
                    # Final failure
                    self.context.completed_tasks.append(f"{agent_name}: FAILED")
                    
                    agent_result = AgentResult(
                        agent_name=agent_name,
                        success=False,
                        duration=time.time() - start_time,
                        error_message=last_error
                    )
                    
                    self.comm_hub.register_output(agent_name, agent_result)
                    
                    print(f"  Status: FAILED after {retries} attempts")
                    return agent_result
    
    async def run_parallel_agents(self, agents: List[str]) -> List[AgentResult]:
        """Run multiple agents in parallel"""
        print(f"\n{'='*60}")
        print(f"Running in parallel: {', '.join(agents)}")
        print(f"{'='*60}")
        
        tasks = [self.execute_agent(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                # Handle exception
                error_result = AgentResult(
                    agent_name=agent,
                    success=False,
                    error_message=str(result)
                )
                processed_results.append(error_result)
                self.failed_agents.add(agent)
            else:
                processed_results.append(result)
                if result.success:
                    self.completed_agents.add(agent)
                else:
                    self.failed_agents.add(agent)
        
        return processed_results
    
    async def orchestrate(self) -> Dict:
        """Main orchestration logic with file verification"""
        
        print("\n" + "="*60)
        print("FINAL OPTIMIZED INTELLIGENT ORCHESTRATOR v5.0")
        print("With Complete File Creation Fix")
        print("="*60)
        
        start_time = time.time()
        
        # Track all agents
        all_agents = list(self.dependency_graph.dependencies.keys())
        
        while len(self.completed_agents) + len(self.failed_agents) < len(all_agents):
            # Get ready agents
            ready = self.dependency_graph.get_ready_agents(
                self.completed_agents,
                set()  # No running agents in async context
            )
            
            if not ready:
                if len(self.failed_agents) > 0:
                    print("\n⚠️ Some agents failed, cannot continue with dependencies")
                    break
                else:
                    print("\n⚠️ No agents ready to run, possible deadlock")
                    break
            
            # Check for parallel execution
            parallel_group = self.dependency_graph.get_parallel_group(ready)
            
            if len(parallel_group) > 1:
                # Execute in parallel
                results = await self.run_parallel_agents(parallel_group)
                for agent in parallel_group:
                    if agent not in self.failed_agents:
                        self.completed_agents.add(agent)
            else:
                # Execute single agent
                agent = ready[0]
                result = await self.execute_agent(agent)
                if result.success:
                    self.completed_agents.add(agent)
                else:
                    self.failed_agents.add(agent)
            
            # Save checkpoint
            if len(self.completed_agents) % 2 == 0:
                self.save_checkpoint()
        
        # Final summary
        total_duration = time.time() - start_time
        
        print("\n" + "="*60)
        print("ORCHESTRATION COMPLETE")
        print("="*60)
        print(f"Total Duration: {total_duration:.1f}s")
        print(f"Agents Completed: {len(self.completed_agents)}/{len(all_agents)}")
        
        # Verify all files
        print("\n📁 File Verification:")
        all_files = self.file_tracker.get_current_files()
        project_files = [f for f in all_files if not f.name.endswith('.json')]
        
        print(f"Total files created: {len(project_files)}")
        for file in sorted(project_files)[:20]:  # Show first 20 files
            rel_path = file.relative_to(self.output_dir)
            print(f"  ✓ {rel_path}")
        
        if len(project_files) > 20:
            print(f"  ... and {len(project_files) - 20} more files")
        
        # Save final context
        self.save_final_context()
        
        return {
            "success": len(self.failed_agents) == 0,
            "completed_agents": list(self.completed_agents),
            "failed_agents": list(self.failed_agents),
            "total_duration": total_duration,
            "files_created": len(project_files),
            "communication_hub": {
                "agent_outputs": {k: asdict(v) for k, v in self.comm_hub.agent_outputs.items()},
                "shared_artifacts": self.comm_hub.shared_artifacts,
                "file_registry": self.comm_hub.file_registry
            }
        }
    
    def save_checkpoint(self):
        """Save checkpoint with file verification"""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "completed_agents": list(self.completed_agents),
            "failed_agents": list(self.failed_agents),
            "context": {
                "completed_tasks": self.context.completed_tasks,
                "artifacts": self.context.artifacts
            },
            "files_created": len(self.file_tracker.get_current_files()),
            "communication_hub": {
                "agent_outputs": {k: asdict(v) for k, v in self.comm_hub.agent_outputs.items()},
                "shared_artifacts": self.comm_hub.shared_artifacts
            }
        }
        
        checkpoint_file = self.output_dir / "checkpoint.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
    
    def save_final_context(self):
        """Save final context with complete file list"""
        all_files = self.file_tracker.get_current_files()
        file_list = [str(f.relative_to(self.output_dir)) for f in all_files]
        
        final_context = {
            "timestamp": datetime.now().isoformat(),
            "completed_agents": list(self.completed_agents),
            "failed_agents": list(self.failed_agents),
            "total_files": len(file_list),
            "files": sorted(file_list),
            "context": {
                "completed_tasks": self.context.completed_tasks,
                "artifacts": self.context.artifacts,
                "decisions": self.context.decisions
            },
            "communication_hub": {
                "agent_outputs": {k: asdict(v) for k, v in self.comm_hub.agent_outputs.items()},
                "shared_artifacts": self.comm_hub.shared_artifacts,
                "file_registry": self.comm_hub.file_registry,
                "tool_call_summary": {
                    agent: len(calls) for agent, calls in self.comm_hub.tool_call_log.items()
                }
            }
        }
        
        context_file = self.output_dir / "final_context.json"
        with open(context_file, 'w') as f:
            json.dump(final_context, f, indent=2, default=str)

# ===================== Main Entry Point =====================

async def main():
    """Main execution with comprehensive error handling"""
    
    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please run: set ANTHROPIC_API_KEY=your-key-here")
        return 1
    
    # Set up output directory
    output_dir = Path.cwd() / "projects" / "quickshop-mvp-final"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean output directory (optional)
    clean = input("Clean output directory? (y/N): ").lower() == 'y'
    if clean:
        import shutil
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Cleaned: {output_dir}")
    
    # Define requirements
    requirements = {
        "project_name": "QuickShop MVP",
        "description": "Modern e-commerce platform with essential features",
        "tech_stack": {
            "frontend": "React + TypeScript + Tailwind CSS",
            "backend": "FastAPI + PostgreSQL",
            "deployment": "Docker + docker-compose"
        },
        "features": [
            "User authentication",
            "Product catalog",
            "Shopping cart",
            "Order management",
            "Admin dashboard"
        ]
    }
    
    # Create orchestrator
    orchestrator = FinalOptimizedOrchestrator(api_key, output_dir)
    
    # Initialize context
    orchestrator.context = orchestrator.initialize_context(requirements)
    
    # Run orchestration
    try:
        result = await orchestrator.orchestrate()
        
        # Print final summary
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        
        if result["success"]:
            print("✅ All agents completed successfully!")
        else:
            print(f"⚠️ {len(result['failed_agents'])} agents failed")
            for agent in result["failed_agents"]:
                error = orchestrator.comm_hub.agent_outputs.get(agent, {})
                print(f"  - {agent}: {error.error_message if error else 'Unknown error'}")
        
        print(f"\n📊 Statistics:")
        print(f"  - Duration: {result['total_duration']:.1f}s")
        print(f"  - Files Created: {result['files_created']}")
        print(f"  - Agents Run: {len(result['completed_agents'])}")
        
        print(f"\n📁 Output Directory: {output_dir}")
        
        return 0 if result["success"] else 1
        
    except Exception as e:
        print(f"\n❌ Orchestration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)