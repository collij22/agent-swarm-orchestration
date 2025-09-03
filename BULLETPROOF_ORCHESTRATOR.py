#!/usr/bin/env python3
"""
BULLETPROOF INTELLIGENT ORCHESTRATOR v6.0
Complete fix with infinite loop prevention and proper error handling
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
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

class CommunicationHub:
    """Centralized communication and artifact management"""
    
    def __init__(self):
        self.agent_outputs: Dict[str, AgentResult] = {}
        self.shared_artifacts: Dict[str, Any] = {}
        self.file_registry: Dict[str, str] = {}  # filename -> creating_agent
        self.agent_messages: List[Dict[str, str]] = []
        
    def register_output(self, agent_name: str, result: AgentResult):
        """Register agent output"""
        self.agent_outputs[agent_name] = result
        
        # Track files created by this agent
        for file in result.files_created:
            self.file_registry[file] = agent_name
    
    def get_agent_summary(self, agent_name: str) -> str:
        """Get formatted summary of agent output"""
        if agent_name not in self.agent_outputs:
            return f"{agent_name}: Not executed yet"
        
        result = self.agent_outputs[agent_name]
        if result.success:
            files_info = f" ({len(result.files_created)} files)" if result.files_created else ""
            return f"{agent_name}: SUCCESS{files_info}"
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

class FileTracker:
    """File tracking with verification"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.file_snapshots: Dict[str, Set[Path]] = {}
        
    def snapshot(self, label: str) -> Set[Path]:
        """Take a snapshot of current files"""
        current_files = self.get_current_files()
        self.file_snapshots[label] = current_files
        return current_files
        
    def get_current_files(self) -> Set[Path]:
        """Get all files in output directory"""
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
    
    def get_ready_agents(self, completed: Set[str], failed: Set[str], running: Set[str] = None) -> List[str]:
        """Get agents ready to run, excluding failed and running agents"""
        running = running or set()
        ready = []
        
        for agent in self.dependencies:
            # Skip if already completed, failed, or currently running
            if agent in completed or agent in failed or agent in running:
                continue
                
            # Check if dependencies are met
            if self.can_run(agent, completed):
                # Check if any dependency failed - if so, this agent can't run
                deps_failed = any(dep in failed for dep in self.dependencies.get(agent, []))
                if not deps_failed:
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

class BulletproofOrchestrator:
    """Bulletproof orchestrator with complete error handling"""
    
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
        self.running_agents = set()
        self.execution_log = []
        self.max_retries = 2
        
    def initialize_context(self, requirements: Dict) -> AgentContext:
        """Initialize context with proper project directory"""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        context = AgentContext(
            project_requirements=requirements,
            completed_tasks=[],  # For strings only
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
        """Build agent prompt"""
        
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
        
        prompt = f"""You are {agent_name}, a specialized AI agent building a QuickShop MVP e-commerce application.

## CRITICAL INSTRUCTIONS
1. You MUST create actual files using the write_file tool
2. Files should be created in relative paths like "backend/main.py" or "frontend/src/App.tsx"
3. DO NOT use absolute paths starting with C:\\ or /
4. Create real implementation code, not just placeholders

## Your Role
{self._get_agent_description(agent_name)}

## Dependencies Completed
{chr(10).join(dependency_summaries) if dependency_summaries else "No dependencies"}

## Shared Artifacts
{json.dumps(relevant_artifacts, indent=2) if relevant_artifacts else "No shared artifacts"}

## Project Requirements
Build a QuickShop MVP e-commerce platform with:
- Frontend: React + TypeScript + Tailwind CSS
- Backend: FastAPI + PostgreSQL
- Features: User auth, product catalog, shopping cart, orders, admin dashboard
- Deployment: Docker + docker-compose

## Expected Deliverables
{self._get_agent_deliverables(agent_name)}

Create the files now with actual working code!
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
            "requirements-analyst": "Create REQUIREMENTS.md and API_SPEC.md files",
            "project-architect": "Create ARCHITECTURE.md and PROJECT_STRUCTURE.md files",
            "database-expert": "Create database/schema.sql and database/migrations/ files",
            "rapid-builder": "Create backend/ directory with main.py, models.py, routes/, etc.",
            "frontend-specialist": "Create frontend/ directory with src/App.tsx, components/, etc.",
            "api-integrator": "Create API integration code and middleware",
            "devops-engineer": "Create docker-compose.yml, Dockerfiles, and .env.example",
            "quality-guardian": "Create tests/ directory and TEST_REPORT.md"
        }
        return deliverables.get(agent_name, "Create relevant files for your role")
    
    def execute_agent(self, agent_name: str) -> AgentResult:
        """Execute a single agent with proper error handling"""
        
        print(f"\n{'='*60}")
        print(f"Executing: {agent_name}")
        print(f"{'='*60}")
        
        # Mark as running
        self.running_agents.add(agent_name)
        
        # Take file snapshot before execution
        before_snapshot = self.file_tracker.snapshot(f"{agent_name}_before")
        
        # Build prompt
        prompt = self.build_agent_prompt(agent_name)
        
        # Execute agent with retries
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    print(f"  Retry {attempt}/{self.max_retries-1}...")
                    prompt += f"\n\n## Previous Error\n{last_error}\nPlease fix the issue and try again."
                
                # Execute agent (using synchronous version to avoid async issues)
                success, response, updated_context = self.runner.run_agent(
                    agent_name=agent_name,
                    agent_prompt=prompt,  # Fixed: use agent_prompt instead of prompt
                    context=self.context
                )
                
                # Update context from agent execution
                self.context = updated_context
                
                # Check if successful
                if not success:
                    raise Exception(f"Agent execution failed: {response}")
                
                # Success! Update context
                self.context.completed_tasks.append(f"{agent_name}: SUCCESS")
                
                # Take snapshot after execution
                after_snapshot = self.file_tracker.snapshot(f"{agent_name}_after")
                new_files = self.file_tracker.get_new_files(f"{agent_name}_before", f"{agent_name}_after")
                
                # Create result
                agent_result = AgentResult(
                    agent_name=agent_name,
                    success=True,
                    files_created=new_files,
                    duration=time.time() - start_time
                )
                
                # Register with communication hub
                self.comm_hub.register_output(agent_name, agent_result)
                
                # Share artifacts if needed
                if agent_name == "database-expert" and new_files:
                    for file in new_files:
                        if 'schema' in file.lower():
                            self.comm_hub.share_artifact("database_schema", file, agent_name)
                            break
                
                print(f"  Status: SUCCESS")
                print(f"  Files created: {len(new_files)}")
                if new_files:
                    for f in new_files[:5]:  # Show first 5 files
                        print(f"    - {f}")
                print(f"  Duration: {agent_result.duration:.1f}s")
                
                # Remove from running, add to completed
                self.running_agents.discard(agent_name)
                self.completed_agents.add(agent_name)
                
                return agent_result
                
            except Exception as e:
                last_error = str(e)
                print(f"  Error (attempt {attempt+1}): {last_error[:200]}")
                
                if attempt == self.max_retries - 1:
                    # Final failure
                    self.context.completed_tasks.append(f"{agent_name}: FAILED")
                    
                    agent_result = AgentResult(
                        agent_name=agent_name,
                        success=False,
                        duration=time.time() - start_time,
                        error_message=last_error[:500]  # Truncate long errors
                    )
                    
                    self.comm_hub.register_output(agent_name, agent_result)
                    
                    print(f"  Status: FAILED after {self.max_retries} attempts")
                    
                    # Remove from running, add to failed
                    self.running_agents.discard(agent_name)
                    self.failed_agents.add(agent_name)
                    
                    return agent_result
        
        # Should not reach here
        self.running_agents.discard(agent_name)
        self.failed_agents.add(agent_name)
        return AgentResult(agent_name=agent_name, success=False, error_message="Unknown error")
    
    def orchestrate(self) -> Dict:
        """Main orchestration logic with proper error handling"""
        
        print("\n" + "="*60)
        print("BULLETPROOF INTELLIGENT ORCHESTRATOR v6.0")
        print("With Infinite Loop Prevention")
        print("="*60)
        
        start_time = time.time()
        
        # Track all agents
        all_agents = list(self.dependency_graph.dependencies.keys())
        max_iterations = len(all_agents) * 3  # Safety limit to prevent infinite loops
        iteration = 0
        
        while len(self.completed_agents) + len(self.failed_agents) < len(all_agents):
            iteration += 1
            
            # Safety check for infinite loop
            if iteration > max_iterations:
                print("\n❌ ERROR: Maximum iterations exceeded, breaking to prevent infinite loop")
                break
            
            # Get ready agents (excluding failed and running)
            ready = self.dependency_graph.get_ready_agents(
                self.completed_agents,
                self.failed_agents,
                self.running_agents
            )
            
            if not ready:
                if len(self.failed_agents) > 0:
                    print(f"\n⚠️ Cannot continue: {len(self.failed_agents)} agents failed")
                    # List failed agents
                    for agent in self.failed_agents:
                        error = self.comm_hub.agent_outputs.get(agent, {})
                        print(f"  - {agent}: {getattr(error, 'error_message', 'Unknown error')[:100]}")
                    break
                elif len(self.running_agents) > 0:
                    print(f"\n⏳ Waiting for {len(self.running_agents)} agents to complete...")
                    time.sleep(1)
                    continue
                else:
                    print("\n⚠️ No agents ready to run, checking for deadlock...")
                    # List pending agents
                    pending = set(all_agents) - self.completed_agents - self.failed_agents
                    if pending:
                        print(f"  Pending agents: {', '.join(pending)}")
                    break
            
            # Execute ready agents (sequentially for now to avoid async issues)
            for agent in ready[:1]:  # Take only first agent to run sequentially
                result = self.execute_agent(agent)
                
            # Save checkpoint periodically
            if len(self.completed_agents) % 2 == 0 or len(self.failed_agents) > 0:
                self.save_checkpoint()
        
        # Final summary
        total_duration = time.time() - start_time
        
        print("\n" + "="*60)
        print("ORCHESTRATION COMPLETE")
        print("="*60)
        print(f"Total Duration: {total_duration:.1f}s")
        print(f"Agents Completed: {len(self.completed_agents)}/{len(all_agents)}")
        print(f"Agents Failed: {len(self.failed_agents)}")
        
        # List completed agents
        if self.completed_agents:
            print("\n✅ Completed Agents:")
            for agent in self.completed_agents:
                result = self.comm_hub.agent_outputs.get(agent)
                if result and result.files_created:
                    print(f"  - {agent}: {len(result.files_created)} files")
                else:
                    print(f"  - {agent}")
        
        # List failed agents
        if self.failed_agents:
            print("\n❌ Failed Agents:")
            for agent in self.failed_agents:
                result = self.comm_hub.agent_outputs.get(agent)
                if result:
                    print(f"  - {agent}: {result.error_message[:100]}")
        
        # Verify files
        print("\n📁 File Verification:")
        all_files = self.file_tracker.get_current_files()
        project_files = [f for f in all_files if not f.name.endswith('.json')]
        
        print(f"Total files created: {len(project_files)}")
        for file in sorted(project_files)[:10]:  # Show first 10 files
            rel_path = file.relative_to(self.output_dir)
            print(f"  ✓ {rel_path}")
        
        if len(project_files) > 10:
            print(f"  ... and {len(project_files) - 10} more files")
        
        # Save final context
        self.save_final_context()
        
        return {
            "success": len(self.failed_agents) == 0,
            "completed_agents": list(self.completed_agents),
            "failed_agents": list(self.failed_agents),
            "total_duration": total_duration,
            "files_created": len(project_files)
        }
    
    def save_checkpoint(self):
        """Save checkpoint"""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "completed_agents": list(self.completed_agents),
            "failed_agents": list(self.failed_agents),
            "running_agents": list(self.running_agents),
            "context": {
                "completed_tasks": self.context.completed_tasks[-20:],  # Last 20 tasks only
                "artifacts": self.context.artifacts
            },
            "files_created": len(self.file_tracker.get_current_files()),
            "communication_hub": {
                "agent_outputs": {
                    k: asdict(v) for k, v in self.comm_hub.agent_outputs.items()
                },
                "shared_artifacts": self.comm_hub.shared_artifacts
            }
        }
        
        checkpoint_file = self.output_dir / "checkpoint.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
    
    def save_final_context(self):
        """Save final context"""
        all_files = self.file_tracker.get_current_files()
        file_list = [str(f.relative_to(self.output_dir)) for f in all_files]
        
        final_context = {
            "timestamp": datetime.now().isoformat(),
            "completed_agents": list(self.completed_agents),
            "failed_agents": list(self.failed_agents),
            "total_files": len(file_list),
            "files": sorted(file_list),
            "context": {
                "completed_tasks": self.context.completed_tasks[-50:],  # Last 50 tasks
                "artifacts": self.context.artifacts,
                "decisions": self.context.decisions
            },
            "communication_hub": {
                "agent_outputs": {
                    k: asdict(v) for k, v in self.comm_hub.agent_outputs.items()
                },
                "shared_artifacts": self.comm_hub.shared_artifacts,
                "file_registry": self.comm_hub.file_registry
            }
        }
        
        context_file = self.output_dir / "final_context.json"
        with open(context_file, 'w') as f:
            json.dump(final_context, f, indent=2, default=str)

# ===================== Main Entry Point =====================

def main():
    """Main execution"""
    
    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please run: set ANTHROPIC_API_KEY=your-key-here")
        return 1
    
    # Set up output directory
    output_dir = Path.cwd() / "projects" / "quickshop-mvp-bulletproof"
    
    # Clean output directory
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory: {output_dir}")
    
    # Define requirements
    requirements = {
        "project_name": "QuickShop MVP",
        "description": "Modern e-commerce platform with essential features",
        "tech_stack": {
            "frontend": "React + TypeScript + Tailwind CSS",
            "backend": "FastAPI + PostgreSQL",
            "deployment": "Docker + docker-compose"
        }
    }
    
    # Create orchestrator
    orchestrator = BulletproofOrchestrator(api_key, output_dir)
    
    # Initialize context
    orchestrator.context = orchestrator.initialize_context(requirements)
    
    # Run orchestration
    try:
        result = orchestrator.orchestrate()
        
        # Print final summary
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        
        if result["success"]:
            print("✅ All agents completed successfully!")
        else:
            print(f"⚠️ {len(result['failed_agents'])} agents failed")
        
        print(f"\n📊 Statistics:")
        print(f"  - Duration: {result['total_duration']:.1f}s")
        print(f"  - Files Created: {result['files_created']}")
        print(f"  - Success Rate: {len(result['completed_agents'])}/{len(result['completed_agents']) + len(result['failed_agents'])}")
        
        print(f"\n📁 Output Directory: {output_dir}")
        
        return 0 if result["success"] else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Orchestration interrupted by user")
        orchestrator.save_checkpoint()
        return 2
    except Exception as e:
        print(f"\n❌ Orchestration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)