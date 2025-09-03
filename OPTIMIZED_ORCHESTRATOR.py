#!/usr/bin/env python3
"""
OPTIMIZED INTELLIGENT ORCHESTRATOR v4.0
- Fixed completed_tasks string handling
- Enhanced communication flow
- Improved file tracking
- Better error recovery
"""

import sys
import os
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import traceback

# Force UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

sys.path.insert(0, str(Path.cwd()))

from lib.agent_runtime import (
    AgentContext,
    AnthropicAgentRunner,
    ModelType,
    get_optimal_model,
    create_standard_tools
)

@dataclass
class AgentTask:
    """Represents an agent task with dependencies"""
    name: str
    dependencies: List[str]
    can_parallel: bool = True
    priority: int = 0
    estimated_time: int = 30
    retry_count: int = 0
    max_retries: int = 2

@dataclass
class AgentResult:
    """Stores detailed agent execution results"""
    agent_name: str
    success: bool
    result: str
    files_created: List[str] = field(default_factory=list)
    timestamp: str = ""
    duration: float = 0.0
    error_message: Optional[str] = None
    artifacts_produced: Dict[str, Any] = field(default_factory=dict)

class CommunicationHub:
    """Centralized communication management between agents"""
    
    def __init__(self):
        self.agent_outputs: Dict[str, AgentResult] = {}
        self.shared_artifacts: Dict[str, Any] = {}
        self.file_registry: Dict[str, str] = {}  # filename -> creating_agent
        self.agent_messages: List[Dict[str, str]] = []
        
    def register_output(self, agent_name: str, result: AgentResult):
        """Register agent output for sharing"""
        self.agent_outputs[agent_name] = result
        
        # Track files
        for file_path in result.files_created:
            self.file_registry[file_path] = agent_name
    
    def get_agent_summary(self, agent_name: str) -> str:
        """Get a text summary of an agent's output"""
        if agent_name not in self.agent_outputs:
            return f"{agent_name}: not yet executed"
        
        result = self.agent_outputs[agent_name]
        if result.success:
            files_count = len(result.files_created)
            return f"{agent_name}: SUCCESS ({files_count} files created)"
        else:
            return f"{agent_name}: FAILED ({result.error_message[:50]}...)"
    
    def get_all_summaries(self) -> str:
        """Get summaries of all completed agents"""
        summaries = []
        for agent_name in self.agent_outputs:
            summaries.append(self.get_agent_summary(agent_name))
        return " | ".join(summaries) if summaries else "None completed yet"
    
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
        """Add an inter-agent message"""
        self.agent_messages.append({
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

class DependencyGraph:
    """Enhanced dependency graph with communication support"""
    
    def __init__(self, comm_hub: CommunicationHub):
        self.tasks: Dict[str, AgentTask] = {}
        self.completed: Set[str] = set()
        self.in_progress: Set[str] = set()
        self.failed: Set[str] = set()
        self.comm_hub = comm_hub
    
    def add_task(self, task: AgentTask):
        self.tasks[task.name] = task
    
    def get_ready_tasks(self) -> List[str]:
        ready = []
        for name, task in self.tasks.items():
            if name in self.completed or name in self.in_progress or name in self.failed:
                continue
            
            # Check dependencies
            if all(dep in self.completed for dep in task.dependencies):
                ready.append(name)
        
        ready.sort(key=lambda x: self.tasks[x].priority, reverse=True)
        return ready
    
    def get_retryable_failed_tasks(self) -> List[str]:
        retryable = []
        for name in self.failed:
            task = self.tasks[name]
            if task.retry_count < task.max_retries:
                if all(dep in self.completed for dep in task.dependencies):
                    retryable.append(name)
        return retryable
    
    def get_parallel_groups(self, ready_tasks: List[str]) -> List[List[str]]:
        if not ready_tasks:
            return []
        
        groups = []
        current_group = []
        
        for task_name in ready_tasks:
            task = self.tasks[task_name]
            
            if not task.can_parallel:
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([task_name])
            else:
                current_group.append(task_name)
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def mark_completed(self, task_name: str, result: AgentResult):
        self.in_progress.discard(task_name)
        self.failed.discard(task_name)
        self.completed.add(task_name)
        self.comm_hub.register_output(task_name, result)
    
    def mark_in_progress(self, task_name: str):
        self.failed.discard(task_name)
        self.in_progress.add(task_name)
    
    def mark_failed(self, task_name: str, error: str):
        self.in_progress.discard(task_name)
        self.failed.add(task_name)
        self.tasks[task_name].retry_count += 1
        
        # Store failure
        result = AgentResult(
            agent_name=task_name,
            success=False,
            result="",
            error_message=error,
            timestamp=datetime.now().isoformat()
        )
        self.comm_hub.register_output(task_name, result)
    
    def get_status(self) -> Dict:
        total = len(self.tasks)
        return {
            "total": total,
            "completed": len(self.completed),
            "in_progress": len(self.in_progress),
            "failed": len(self.failed),
            "pending": total - len(self.completed) - len(self.in_progress) - len(self.failed),
            "progress_percentage": (len(self.completed) / total * 100) if total > 0 else 0
        }

class FileTracker:
    """Accurate file tracking system"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.initial_files: Set[Path] = set()
        self.scan_initial_files()
    
    def scan_initial_files(self):
        """Scan initial files in the directory"""
        if self.output_dir.exists():
            self.initial_files = {f for f in self.output_dir.rglob("*") if f.is_file()}
    
    def get_current_files(self) -> Set[Path]:
        """Get current files in the directory"""
        if self.output_dir.exists():
            return {f for f in self.output_dir.rglob("*") if f.is_file()}
        return set()
    
    def get_new_files(self, before_files: Set[Path]) -> List[str]:
        """Get files created since a checkpoint"""
        current_files = self.get_current_files()
        new_files = current_files - before_files
        return [str(f.relative_to(self.output_dir)) for f in new_files]
    
    def count_files(self) -> int:
        """Count total files"""
        return len(self.get_current_files())

class OptimizedOrchestrator:
    """Orchestrator with optimized communication and proper string handling"""
    
    def __init__(self, runner: AnthropicAgentRunner, output_dir: Path):
        self.runner = runner
        self.output_dir = output_dir
        self.comm_hub = CommunicationHub()
        self.dependency_graph = DependencyGraph(self.comm_hub)
        self.file_tracker = FileTracker(output_dir)
        self.context = None
        self.requirements = None
        self.has_async = hasattr(runner, 'run_agent_async')
        
    def define_quickshop_workflow(self):
        """Define the QuickShop MVP workflow"""
        
        # Level 0: Foundation
        self.dependency_graph.add_task(AgentTask(
            name="requirements-analyst",
            dependencies=[],
            can_parallel=False,
            priority=100,
            estimated_time=10
        ))
        
        # Level 1: Architecture
        self.dependency_graph.add_task(AgentTask(
            name="project-architect",
            dependencies=["requirements-analyst"],
            can_parallel=False,
            priority=90,
            estimated_time=15
        ))
        
        # Level 2: Core Development
        self.dependency_graph.add_task(AgentTask(
            name="database-expert",
            dependencies=["project-architect"],
            can_parallel=True,
            priority=80,
            estimated_time=20
        ))
        
        self.dependency_graph.add_task(AgentTask(
            name="rapid-builder",
            dependencies=["project-architect", "database-expert"],
            can_parallel=True,
            priority=75,
            estimated_time=30
        ))
        
        self.dependency_graph.add_task(AgentTask(
            name="frontend-specialist",
            dependencies=["project-architect"],
            can_parallel=True,
            priority=75,
            estimated_time=30
        ))
        
        # Level 3: Integration
        self.dependency_graph.add_task(AgentTask(
            name="api-integrator",
            dependencies=["rapid-builder", "frontend-specialist"],
            can_parallel=False,
            priority=60,
            estimated_time=20
        ))
        
        # Level 4: Finalization
        self.dependency_graph.add_task(AgentTask(
            name="devops-engineer",
            dependencies=["rapid-builder", "frontend-specialist", "database-expert"],
            can_parallel=True,
            priority=50,
            estimated_time=25
        ))
        
        self.dependency_graph.add_task(AgentTask(
            name="quality-guardian",
            dependencies=["api-integrator", "devops-engineer"],
            can_parallel=False,
            priority=30,
            estimated_time=15
        ))
    
    def build_agent_prompt(self, agent_name: str) -> str:
        """Build optimized prompt with proper communication context"""
        
        # Get summaries from communication hub
        completed_summary = self.comm_hub.get_all_summaries()
        
        # Build dependency context
        task = self.dependency_graph.tasks[agent_name]
        dependency_outputs = {}
        for dep in task.dependencies:
            if dep in self.comm_hub.agent_outputs:
                result = self.comm_hub.agent_outputs[dep]
                dependency_outputs[dep] = {
                    "files_created": result.files_created,
                    "success": result.success
                }
        
        # Get shared artifacts relevant to this agent
        relevant_artifacts = {}
        if agent_name == "rapid-builder":
            # Rapid builder needs database schema
            schema = self.comm_hub.get_artifact("database_schema")
            if schema:
                relevant_artifacts["database_schema"] = schema
        elif agent_name == "api-integrator":
            # API integrator needs endpoints from backend
            endpoints = self.comm_hub.get_artifact("api_endpoints")
            if endpoints:
                relevant_artifacts["api_endpoints"] = endpoints
        
        prompt = f"""You are {agent_name}, a specialized AI agent building a QuickShop MVP e-commerce application.

## Project Requirements
{json.dumps(self.requirements, indent=2)}

## Previous Agents Completed
{completed_summary}

## Dependencies Output
{json.dumps(dependency_outputs, indent=2) if dependency_outputs else "No direct dependencies"}

## Shared Artifacts
{json.dumps(relevant_artifacts, indent=2) if relevant_artifacts else "No shared artifacts"}

## Output Directory
{self.output_dir}

## Your Specific Role
Complete your specialized tasks for this project. Create actual working files with complete implementation.

### Key Instructions:
1. Use write_file tool to create complete, working code files
2. Include all necessary imports and proper structure
3. No placeholder code or TODO comments without implementation
4. Build upon what previous agents have created
5. Share important artifacts for downstream agents

### Expected Deliverables:
- Create all files needed for your component
- Ensure files are syntactically correct and complete
- Test that your component integrates with existing work
- Document any important decisions or configurations"""
        
        return prompt
    
    async def execute_agent(self, agent_name: str, retry_attempt: int = 0) -> Tuple[bool, str]:
        """Execute a single agent with optimized communication"""
        
        print(f"\n{'='*60}")
        print(f"[AGENT] {agent_name}")
        if retry_attempt > 0:
            print(f"  Retry: {retry_attempt + 1}/{self.dependency_graph.tasks[agent_name].max_retries}")
        print(f"  Model: {get_optimal_model(agent_name)}")
        print(f"  Started: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
        
        self.dependency_graph.mark_in_progress(agent_name)
        start_time = time.time()
        files_before = self.file_tracker.get_current_files()
        
        try:
            # Build optimized prompt
            prompt = self.build_agent_prompt(agent_name)
            
            # Validate context before execution
            if not hasattr(self.context, 'completed_tasks'):
                self.context.completed_tasks = []
            
            # Execute agent
            if self.has_async:
                success, result, updated_context = await self.runner.run_agent_async(
                    agent_name=agent_name,
                    agent_prompt=prompt,
                    context=self.context,
                    model=get_optimal_model(agent_name),
                    max_iterations=3
                )
            else:
                loop = asyncio.get_event_loop()
                success, result, updated_context = await loop.run_in_executor(
                    None,
                    self.runner.run_agent,
                    agent_name,
                    prompt,
                    self.context,
                    get_optimal_model(agent_name),
                    3
                )
            
            duration = time.time() - start_time
            
            if success:
                # Update context
                self.context = updated_context
                
                # Track new files
                new_files = self.file_tracker.get_new_files(files_before)
                
                # IMPORTANT: Add to completed_tasks as STRING (not dict)
                self.context.completed_tasks.append(f"{agent_name}: SUCCESS ({len(new_files)} files)")
                
                # Create detailed result for our tracking
                agent_result = AgentResult(
                    agent_name=agent_name,
                    success=True,
                    result=str(result)[:500],
                    files_created=new_files,
                    timestamp=datetime.now().isoformat(),
                    duration=duration
                )
                
                # Mark completed
                self.dependency_graph.mark_completed(agent_name, agent_result)
                
                # Share artifacts based on agent type
                if agent_name == "database-expert":
                    # Share database schema
                    self.comm_hub.share_artifact("database_schema", 
                                                 {"tables": ["users", "products", "orders", "carts"]},
                                                 agent_name)
                elif agent_name == "rapid-builder":
                    # Share API endpoints
                    self.comm_hub.share_artifact("api_endpoints",
                                                {"auth": "/api/auth", "products": "/api/products"},
                                                agent_name)
                
                print(f"  Status: [SUCCESS]")
                print(f"  Duration: {duration:.1f}s")
                print(f"  Files created: {len(new_files)}")
                if new_files:
                    print(f"  New files: {', '.join(new_files[:3])}")
                print(f"  Total project files: {self.file_tracker.count_files()}")
                
                return True, result
            else:
                error_msg = str(result)
                print(f"  Status: [FAILED]")
                print(f"  Error: {error_msg[:200]}")
                
                # Add failure to completed_tasks as STRING
                self.context.completed_tasks.append(f"{agent_name}: FAILED")
                
                self.dependency_graph.mark_failed(agent_name, error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = str(e)
            print(f"  Status: [ERROR]")
            print(f"  Exception: {error_msg[:200]}")
            
            # Add error to completed_tasks as STRING
            if hasattr(self.context, 'completed_tasks'):
                self.context.completed_tasks.append(f"{agent_name}: ERROR")
            
            self.dependency_graph.mark_failed(agent_name, error_msg)
            return False, error_msg
    
    async def execute_parallel_group(self, agents: List[str]) -> Dict[str, Tuple[bool, str]]:
        """Execute agents in parallel with communication support"""
        
        if len(agents) == 1:
            result = await self.execute_agent(agents[0])
            return {agents[0]: result}
        
        print(f"\n{'='*80}")
        print(f"[PARALLEL EXECUTION] {len(agents)} agents")
        print(f"  Agents: {', '.join(agents)}")
        print(f"{'='*80}")
        
        # Create parallel tasks
        tasks = []
        for agent_name in agents:
            task = asyncio.create_task(self.execute_agent(agent_name))
            tasks.append((agent_name, task))
        
        # Execute and collect results
        results = {}
        for agent_name, task in tasks:
            try:
                result = await task
                results[agent_name] = result
            except Exception as e:
                results[agent_name] = (False, str(e))
        
        return results
    
    async def handle_failed_agents(self):
        """Retry failed agents with enhanced context"""
        
        retryable = self.dependency_graph.get_retryable_failed_tasks()
        
        if retryable:
            print(f"\n{'='*80}")
            print(f"[RETRY MECHANISM] Attempting to recover failed agents")
            print(f"  Retrying: {', '.join(retryable)}")
            print(f"{'='*80}")
            
            for agent_name in retryable:
                task = self.dependency_graph.tasks[agent_name]
                print(f"\n[RETRY] {agent_name} (attempt {task.retry_count + 1}/{task.max_retries})")
                
                # Remove from failed set
                self.dependency_graph.failed.discard(agent_name)
                
                # Add recovery context
                if self.comm_hub.agent_outputs.get(agent_name):
                    prev_error = self.comm_hub.agent_outputs[agent_name].error_message
                    print(f"  Previous error: {prev_error[:100]}...")
                
                # Retry with enhanced context
                success, result = await self.execute_agent(agent_name, retry_attempt=task.retry_count)
                
                if success:
                    print(f"  [RETRY SUCCESS] {agent_name} recovered")
                else:
                    print(f"  [RETRY FAILED] {agent_name} still failing")
    
    def save_checkpoint(self):
        """Save execution checkpoint with communication data"""
        
        try:
            checkpoint_file = self.output_dir / "checkpoint.json"
            
            checkpoint = {
                "timestamp": datetime.now().isoformat(),
                "completed_agents": list(self.dependency_graph.completed),
                "failed_agents": list(self.dependency_graph.failed),
                "agent_outputs": {
                    name: {
                        "success": result.success,
                        "files_created": result.files_created,
                        "duration": result.duration
                    }
                    for name, result in self.comm_hub.agent_outputs.items()
                },
                "shared_artifacts": self.comm_hub.shared_artifacts,
                "total_files": self.file_tracker.count_files()
            }
            
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=2, ensure_ascii=False)
            
            print(f"[CHECKPOINT] Saved to {checkpoint_file}")
        except Exception as e:
            print(f"[WARN] Checkpoint save failed: {e}")
    
    async def orchestrate(self, context: AgentContext, requirements: Dict):
        """Main orchestration with optimized communication"""
        
        self.context = context
        self.requirements = requirements
        
        print("=" * 80)
        print("OPTIMIZED INTELLIGENT ORCHESTRATOR v4.0")
        print("=" * 80)
        print()
        print("Key Improvements:")
        print("  ✓ Fixed completed_tasks string handling")
        print("  ✓ Enhanced agent communication hub")
        print("  ✓ Accurate file tracking system")
        print("  ✓ Artifact sharing between agents")
        print("  ✓ Improved error recovery")
        print()
        
        # Define workflow
        self.define_quickshop_workflow()
        
        print("Workflow Configuration:")
        print(f"  Total agents: {len(self.dependency_graph.tasks)}")
        print(f"  Output directory: {self.output_dir}")
        print(f"  Async support: {'Yes' if self.has_async else 'No'}")
        print()
        
        # Main execution loop
        iteration = 0
        max_iterations = 20
        no_progress_count = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get ready tasks
            ready_tasks = self.dependency_graph.get_ready_tasks()
            
            if not ready_tasks:
                # Try recovery
                await self.handle_failed_agents()
                
                ready_tasks = self.dependency_graph.get_ready_tasks()
                
                if not ready_tasks:
                    status = self.dependency_graph.get_status()
                    
                    if status["pending"] == 0 and status["in_progress"] == 0:
                        print("\n" + "=" * 80)
                        print("ORCHESTRATION COMPLETE")
                        print("=" * 80)
                        break
                    
                    if status["in_progress"] > 0:
                        await asyncio.sleep(1)
                        continue
                    
                    no_progress_count += 1
                    if no_progress_count > 3:
                        print("\n[WARNING] Workflow stuck")
                        break
                    
                    await asyncio.sleep(2)
                    continue
            
            no_progress_count = 0
            
            # Get execution groups
            parallel_groups = self.dependency_graph.get_parallel_groups(ready_tasks)
            
            print(f"\n[ITERATION {iteration}]")
            print(f"  Ready: {ready_tasks}")
            print(f"  Plan: {parallel_groups}")
            
            # Execute groups
            for group in parallel_groups:
                if len(group) > 1:
                    results = await self.execute_parallel_group(group)
                    
                    for agent, (success, _) in results.items():
                        status_icon = "✓" if success else "✗"
                        print(f"  [{status_icon}] {agent}")
                else:
                    print(f"\n[SEQUENTIAL] {group[0]}")
                    success, _ = await self.execute_agent(group[0])
                    
                    status_icon = "✓" if success else "✗"
                    print(f"  [{status_icon}] {group[0]}")
            
            # Progress update
            status = self.dependency_graph.get_status()
            print(f"\n[PROGRESS] {status['completed']}/{status['total']} ({status['progress_percentage']:.1f}%)")
            
            # Save checkpoint
            if status['completed'] % 2 == 0 and status['completed'] > 0:
                self.save_checkpoint()

async def main():
    """Main execution entry point"""
    
    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("[ERROR] No ANTHROPIC_API_KEY found!")
        print("Set it with: set ANTHROPIC_API_KEY=your-key-here")
        return
    
    # Setup output directory
    output_dir = Path("projects/quickshop-mvp-optimized")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Requirements
    requirements = {
        "name": "QuickShop MVP",
        "type": "E-commerce platform",
        "description": "Modern e-commerce platform with essential features",
        "features": [
            "User authentication (register, login, logout)",
            "Product catalog with categories",
            "Shopping cart functionality",
            "Order management",
            "Admin dashboard"
        ],
        "tech_stack": {
            "frontend": "React + TypeScript + Tailwind CSS",
            "backend": "FastAPI (Python)",
            "database": "PostgreSQL",
            "deployment": "Docker + docker-compose"
        }
    }
    
    # Create context with proper initialization
    context = AgentContext(
        project_requirements=requirements,
        completed_tasks=[],  # Start with empty list for strings
        artifacts={
            "output_dir": str(output_dir),
            "project_directory": str(output_dir)  # Add this for write_file_tool compatibility
        },
        decisions=[],
        current_phase="initialization"
    )
    
    print(f"Output directory: {output_dir}")
    print(f"API Key: {api_key[:20]}...")
    
    # Create runner and register tools
    runner = AnthropicAgentRunner(api_key=api_key)
    
    for tool in create_standard_tools():
        runner.register_tool(tool)
    
    print(f"Registered {len(runner.tools)} tools")
    
    # Create and run orchestrator
    orchestrator = OptimizedOrchestrator(runner, output_dir)
    
    start_time = time.time()
    
    try:
        await orchestrator.orchestrate(context, requirements)
    except Exception as e:
        print(f"\n[ERROR] Orchestration failed: {e}")
        traceback.print_exc()
    
    execution_time = time.time() - start_time
    
    # Save final context
    try:
        final_context = {
            "execution_time": execution_time,
            "completed_agents": list(orchestrator.dependency_graph.completed),
            "failed_agents": list(orchestrator.dependency_graph.failed),
            "agent_outputs": {
                name: {
                    "success": result.success,
                    "files_created": result.files_created,
                    "duration": result.duration
                }
                for name, result in orchestrator.comm_hub.agent_outputs.items()
            },
            "shared_artifacts": orchestrator.comm_hub.shared_artifacts,
            "total_files": orchestrator.file_tracker.count_files(),
            "completed_tasks": context.completed_tasks  # These are now strings
        }
        
        context_file = output_dir / "final_context.json"
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(final_context, f, indent=2, ensure_ascii=False)
        
        print(f"\n[SAVED] Final context to {context_file}")
    except Exception as e:
        print(f"[WARN] Failed to save context: {e}")
    
    # Final summary
    print()
    print("=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Execution time: {execution_time:.2f}s ({execution_time/60:.1f}m)")
    print(f"Output directory: {output_dir}")
    print(f"Total files created: {orchestrator.file_tracker.count_files()}")
    
    # Agent results
    print("\nAgent Results:")
    print("-" * 40)
    for agent_name in ["requirements-analyst", "project-architect", "database-expert",
                      "rapid-builder", "frontend-specialist", "api-integrator",
                      "devops-engineer", "quality-guardian"]:
        if agent_name in orchestrator.comm_hub.agent_outputs:
            result = orchestrator.comm_hub.agent_outputs[agent_name]
            if result.success:
                print(f"  ✓ {agent_name}: {len(result.files_created)} files, {result.duration:.1f}s")
            else:
                print(f"  ✗ {agent_name}: FAILED")
        else:
            print(f"  ⊗ {agent_name}: NOT EXECUTED")
    
    # Show sample files
    if orchestrator.file_tracker.count_files() > 0:
        print("\nSample Files Created:")
        all_files = list(orchestrator.file_tracker.get_current_files())
        for f in all_files[:10]:
            print(f"  - {f.relative_to(output_dir)}")
        if len(all_files) > 10:
            print(f"  ... and {len(all_files) - 10} more")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOPPED] User cancelled")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        traceback.print_exc()