#!/usr/bin/env python3
"""
ULTRA-FIXED INTELLIGENT ORCHESTRATOR
Resolves all communication issues and ensures optimal execution flow
"""

import sys
import os
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, asdict
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
    """Stores agent execution results"""
    agent_name: str
    success: bool
    result: str
    files_created: List[str]
    timestamp: str
    duration: float
    error_message: Optional[str] = None

class DependencyGraph:
    """Manages agent dependencies and execution order"""
    
    def __init__(self):
        self.tasks: Dict[str, AgentTask] = {}
        self.completed: Set[str] = set()
        self.in_progress: Set[str] = set()
        self.failed: Set[str] = set()
        self.results: Dict[str, AgentResult] = {}
    
    def add_task(self, task: AgentTask):
        self.tasks[task.name] = task
    
    def get_ready_tasks(self) -> List[str]:
        ready = []
        for name, task in self.tasks.items():
            if name in self.completed or name in self.in_progress or name in self.failed:
                continue
            
            # Check if all dependencies are completed
            if all(dep in self.completed for dep in task.dependencies):
                ready.append(name)
        
        # Sort by priority (higher first)
        ready.sort(key=lambda x: self.tasks[x].priority, reverse=True)
        return ready
    
    def get_retryable_failed_tasks(self) -> List[str]:
        """Get failed tasks that can be retried"""
        retryable = []
        for name in self.failed:
            task = self.tasks[name]
            if task.retry_count < task.max_retries:
                # Check if dependencies are still satisfied
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
        self.results[task_name] = result
    
    def mark_in_progress(self, task_name: str):
        self.failed.discard(task_name)
        self.in_progress.add(task_name)
    
    def mark_failed(self, task_name: str, error: str):
        self.in_progress.discard(task_name)
        self.failed.add(task_name)
        self.tasks[task_name].retry_count += 1
        
        # Store failure result
        self.results[task_name] = AgentResult(
            agent_name=task_name,
            success=False,
            result="",
            files_created=[],
            timestamp=datetime.now().isoformat(),
            duration=0,
            error_message=error
        )
    
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

class ContextManager:
    """Manages context serialization and sharing between agents"""
    
    @staticmethod
    def serialize_context(context: AgentContext) -> Dict[str, Any]:
        """Safely serialize context for JSON"""
        try:
            # Convert context to dict, handling all types
            context_dict = context.to_dict() if hasattr(context, 'to_dict') else {}
            
            # Ensure all values are JSON serializable
            def make_serializable(obj):
                if isinstance(obj, (str, int, float, bool, type(None))):
                    return obj
                elif isinstance(obj, (list, tuple)):
                    return [make_serializable(item) for item in obj]
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif hasattr(obj, '__dict__'):
                    return make_serializable(obj.__dict__)
                else:
                    return str(obj)
            
            return make_serializable(context_dict)
        except Exception as e:
            print(f"[WARN] Context serialization error: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_completed_agents_summary(dependency_graph: DependencyGraph) -> str:
        """Get a string summary of completed agents and their outputs"""
        if not dependency_graph.completed:
            return "None"
        
        summaries = []
        for agent_name in dependency_graph.completed:
            if agent_name in dependency_graph.results:
                result = dependency_graph.results[agent_name]
                files = len(result.files_created)
                summaries.append(f"{agent_name} (created {files} files)")
            else:
                summaries.append(agent_name)
        
        return ", ".join(summaries)
    
    @staticmethod
    def build_agent_context(dependency_graph: DependencyGraph) -> Dict[str, Any]:
        """Build context information for agents"""
        context = {
            "completed_agents": list(dependency_graph.completed),
            "agent_results": {}
        }
        
        # Add results from completed agents
        for agent_name in dependency_graph.completed:
            if agent_name in dependency_graph.results:
                result = dependency_graph.results[agent_name]
                context["agent_results"][agent_name] = {
                    "success": result.success,
                    "files_created": result.files_created,
                    "timestamp": result.timestamp
                }
        
        return context

class IntelligentOrchestrator:
    """Orchestrates agent execution with optimal parallelization and error recovery"""
    
    def __init__(self, runner: AnthropicAgentRunner):
        self.runner = runner
        self.dependency_graph = DependencyGraph()
        self.context = None
        self.requirements = None
        self.context_manager = ContextManager()
        self.has_async = hasattr(runner, 'run_agent_async')
        
    def define_quickshop_workflow(self):
        """Define the QuickShop MVP workflow with dependencies"""
        
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
        
        # Level 2: Core Development (can work in parallel)
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
    
    def count_project_files(self) -> int:
        """Accurately count files in the project directory"""
        try:
            output_dir = Path(self.context.artifacts.get('output_dir', '.'))
            if output_dir.exists():
                files = [f for f in output_dir.rglob("*") if f.is_file()]
                return len(files)
            return 0
        except Exception as e:
            print(f"[WARN] Error counting files: {e}")
            return 0
    
    def get_created_files(self, before_count: int) -> List[str]:
        """Get list of files created during agent execution"""
        try:
            output_dir = Path(self.context.artifacts.get('output_dir', '.'))
            if output_dir.exists():
                all_files = [f for f in output_dir.rglob("*") if f.is_file()]
                # Return files created after the before_count
                if len(all_files) > before_count:
                    new_files = all_files[before_count:]
                    return [str(f.relative_to(output_dir)) for f in new_files]
            return []
        except Exception as e:
            print(f"[WARN] Error getting created files: {e}")
            return []
    
    async def execute_agent(self, agent_name: str, retry_attempt: int = 0) -> Tuple[bool, str]:
        """Execute a single agent with improved error handling"""
        print(f"\n{'='*60}")
        print(f"[AGENT] {agent_name}")
        if retry_attempt > 0:
            print(f"  Retry Attempt: {retry_attempt + 1}")
        print(f"  Model: {get_optimal_model(agent_name)}")
        print(f"  Started: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
        
        self.dependency_graph.mark_in_progress(agent_name)
        start_time = time.time()
        files_before = self.count_project_files()
        
        try:
            # Build context information
            agent_context = self.context_manager.build_agent_context(self.dependency_graph)
            completed_summary = self.context_manager.get_completed_agents_summary(self.dependency_graph)
            
            # Build agent prompt with proper formatting
            prompt = f"""You are {agent_name}, a specialized AI agent building a QuickShop MVP e-commerce application.

Project Requirements:
{json.dumps(self.requirements, indent=2)}

Previous agents completed: {completed_summary}

Agent Results So Far:
{json.dumps(agent_context, indent=2)}

Output directory: {self.context.artifacts.get('output_dir')}

Your role: Complete your specialized tasks for this project. Create actual files with working code.

IMPORTANT: Use the write_file tool to create files with complete content. Include all necessary imports,
proper structure, and working implementation. Do not leave placeholder code or TODO comments.

Focus on your specific responsibilities and build upon what previous agents have created."""
            
            # Execute agent
            if self.has_async:
                success, result, updated_context = await self.runner.run_agent_async(
                    agent_name=agent_name,
                    agent_prompt=prompt,
                    context=self.context,
                    model=get_optimal_model(agent_name),
                    max_iterations=3  # Increased for better completion
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
                
                # Count files created
                files_after = self.count_project_files()
                files_created = self.get_created_files(files_before)
                
                # Create result
                agent_result = AgentResult(
                    agent_name=agent_name,
                    success=True,
                    result=str(result)[:500],  # Limit result size
                    files_created=files_created,
                    timestamp=datetime.now().isoformat(),
                    duration=duration
                )
                
                # Mark completed
                self.dependency_graph.mark_completed(agent_name, agent_result)
                
                # Update context tasks
                if not hasattr(self.context, 'completed_tasks'):
                    self.context.completed_tasks = []
                
                self.context.completed_tasks.append({
                    "agent": agent_name,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "files_created": len(files_created)
                })
                
                print(f"  Status: [SUCCESS] at {datetime.now().strftime('%H:%M:%S')}")
                print(f"  Duration: {duration:.1f}s")
                print(f"  Files created: {len(files_created)}")
                print(f"  Total project files: {files_after}")
                
                return True, result
            else:
                error_msg = str(result)
                print(f"  Status: [FAILED]")
                print(f"  Error: {error_msg[:200]}")
                self.dependency_graph.mark_failed(agent_name, error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = str(e)
            print(f"  Status: [ERROR]")
            print(f"  Exception: {error_msg}")
            traceback.print_exc()
            self.dependency_graph.mark_failed(agent_name, error_msg)
            return False, error_msg
    
    async def execute_parallel_group(self, agents: List[str]) -> Dict[str, Tuple[bool, str]]:
        """Execute a group of agents in parallel"""
        if len(agents) == 1:
            result = await self.execute_agent(agents[0])
            return {agents[0]: result}
        
        print(f"\n{'='*80}")
        print(f"EXECUTING PARALLEL GROUP: {agents}")
        print(f"{'='*80}")
        
        # Create tasks for parallel execution
        tasks = []
        for agent_name in agents:
            task = asyncio.create_task(self.execute_agent(agent_name))
            tasks.append((agent_name, task))
        
        # Wait for all tasks to complete
        results = {}
        for agent_name, task in tasks:
            try:
                result = await task
                results[agent_name] = result
            except Exception as e:
                results[agent_name] = (False, str(e))
        
        return results
    
    async def handle_failed_agents(self):
        """Attempt to retry failed agents"""
        retryable = self.dependency_graph.get_retryable_failed_tasks()
        
        if retryable:
            print(f"\n{'='*80}")
            print(f"RETRYING FAILED AGENTS: {retryable}")
            print(f"{'='*80}")
            
            for agent_name in retryable:
                task = self.dependency_graph.tasks[agent_name]
                print(f"\n[RETRY] Attempting to retry {agent_name} (attempt {task.retry_count + 1}/{task.max_retries})")
                
                # Remove from failed set temporarily
                self.dependency_graph.failed.discard(agent_name)
                
                # Retry execution
                success, result = await self.execute_agent(agent_name, retry_attempt=task.retry_count)
                
                if success:
                    print(f"  [RETRY SUCCESS] {agent_name} completed on retry")
                else:
                    print(f"  [RETRY FAILED] {agent_name} failed again")
    
    async def orchestrate(self, context: AgentContext, requirements: Dict):
        """Main orchestration logic with improved error recovery"""
        self.context = context
        self.requirements = requirements
        
        print("=" * 80)
        print("ULTRA-INTELLIGENT ORCHESTRATOR v3.0")
        print("=" * 80)
        print()
        print("Features:")
        print("  - Enhanced error recovery with retry mechanism")
        print("  - Improved inter-agent communication")
        print("  - Accurate file tracking")
        print("  - Robust context serialization")
        print()
        
        # Define workflow
        self.define_quickshop_workflow()
        
        print("Workflow Analysis:")
        print(f"  Total agents: {len(self.dependency_graph.tasks)}")
        print(f"  Execution strategy: Optimized parallel/sequential")
        print(f"  Retry policy: Max 2 attempts per agent")
        print(f"  Async support: {'Yes' if self.has_async else 'No (using sync wrapper)'}")
        print()
        
        # Main execution loop
        iteration = 0
        max_iterations = 20  # Prevent infinite loops
        no_progress_count = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get ready tasks
            ready_tasks = self.dependency_graph.get_ready_tasks()
            
            if not ready_tasks:
                # Try to retry failed tasks
                await self.handle_failed_agents()
                
                # Check again for ready tasks
                ready_tasks = self.dependency_graph.get_ready_tasks()
                
                if not ready_tasks:
                    # Check if we're done or stuck
                    status = self.dependency_graph.get_status()
                    
                    if status["pending"] == 0 and status["in_progress"] == 0:
                        print("\n" + "=" * 80)
                        print("ORCHESTRATION COMPLETE")
                        print("=" * 80)
                        print(f"  Completed: {status['completed']} agents")
                        print(f"  Failed: {status['failed']} agents")
                        print(f"  Success Rate: {status['progress_percentage']:.1f}%")
                        
                        # Show failed agents if any
                        if status['failed'] > 0:
                            print("\nFailed Agents:")
                            for agent in self.dependency_graph.failed:
                                if agent in self.dependency_graph.results:
                                    error = self.dependency_graph.results[agent].error_message
                                    print(f"  - {agent}: {error[:100]}")
                        break
                    
                    # Wait for in-progress tasks
                    if status["in_progress"] > 0:
                        await asyncio.sleep(1)
                        continue
                    
                    # Check for no progress
                    no_progress_count += 1
                    if no_progress_count > 3:
                        print("\n[WARNING] Workflow stuck - unable to proceed")
                        print(f"Failed agents blocking progress: {list(self.dependency_graph.failed)}")
                        break
                    
                    await asyncio.sleep(2)
                    continue
            
            # Reset no progress counter
            no_progress_count = 0
            
            # Get parallel groups
            parallel_groups = self.dependency_graph.get_parallel_groups(ready_tasks)
            
            print(f"\n[ITERATION {iteration}]")
            print(f"  Ready tasks: {ready_tasks}")
            print(f"  Execution plan: {parallel_groups}")
            
            # Execute each group
            for group in parallel_groups:
                if len(group) > 1:
                    print(f"\n[PARALLEL EXECUTION] Running {len(group)} agents simultaneously")
                    results = await self.execute_parallel_group(group)
                    
                    # Report results
                    for agent, (success, _) in results.items():
                        if success:
                            print(f"  [OK] {agent}")
                        else:
                            print(f"  [FAIL] {agent}")
                else:
                    # Single agent, execute sequentially
                    print(f"\n[SEQUENTIAL EXECUTION] {group[0]}")
                    success, _ = await self.execute_agent(group[0])
                    
                    if success:
                        print(f"  [OK] {group[0]}")
                    else:
                        print(f"  [FAIL] {group[0]}")
            
            # Show progress
            status = self.dependency_graph.get_status()
            print(f"\n[PROGRESS] {status['completed']}/{status['total']} agents completed ({status['progress_percentage']:.1f}%)")
            
            # Save checkpoint
            if status['completed'] % 2 == 0:
                self.save_checkpoint()
    
    def save_checkpoint(self):
        """Save current progress as checkpoint"""
        try:
            output_dir = Path(self.context.artifacts.get('output_dir', '.'))
            checkpoint_file = output_dir / "checkpoint.json"
            
            checkpoint = {
                "timestamp": datetime.now().isoformat(),
                "completed_agents": list(self.dependency_graph.completed),
                "failed_agents": list(self.dependency_graph.failed),
                "agent_results": {
                    name: {
                        "success": result.success,
                        "files_created": result.files_created,
                        "timestamp": result.timestamp
                    }
                    for name, result in self.dependency_graph.results.items()
                }
            }
            
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=2, ensure_ascii=False)
            
            print(f"[CHECKPOINT] Saved progress to {checkpoint_file}")
        except Exception as e:
            print(f"[WARN] Failed to save checkpoint: {e}")

async def main():
    """Main execution with enhanced error handling"""
    
    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("[ERROR] No ANTHROPIC_API_KEY found!")
        print("Set it with: set ANTHROPIC_API_KEY=your-key-here")
        return
    
    # Create output directory
    output_dir = Path("projects/quickshop-mvp-intelligent")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Requirements
    requirements = {
        "name": "QuickShop MVP",
        "type": "E-commerce platform",
        "description": "A modern e-commerce platform with essential features",
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
        },
        "output_directory": str(output_dir)
    }
    
    # Create context
    context = AgentContext(
        project_requirements=requirements,
        completed_tasks=[],
        artifacts={"output_dir": str(output_dir)},
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
    
    # Create orchestrator and run
    orchestrator = IntelligentOrchestrator(runner)
    
    start_time = time.time()
    
    try:
        await orchestrator.orchestrate(context, requirements)
    except Exception as e:
        print(f"\n[ERROR] Orchestration failed: {e}")
        traceback.print_exc()
    
    execution_time = time.time() - start_time
    
    # Save final context
    try:
        context_file = output_dir / "final_context.json"
        context_dict = orchestrator.context_manager.serialize_context(context)
        
        # Add execution summary
        context_dict["execution_summary"] = {
            "total_time": execution_time,
            "agents_completed": list(orchestrator.dependency_graph.completed),
            "agents_failed": list(orchestrator.dependency_graph.failed),
            "total_files": orchestrator.count_project_files()
        }
        
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(context_dict, f, indent=2, default=str, ensure_ascii=False)
        
        print(f"\n[SAVED] Final context to {context_file}")
    except Exception as e:
        print(f"[WARN] Failed to save final context: {e}")
    
    # Final report
    print()
    print("=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total execution time: {execution_time:.2f} seconds ({execution_time/60:.1f} minutes)")
    print(f"Output directory: {output_dir}")
    
    # List files created
    files_created = 0
    sample_files = []
    for file in output_dir.rglob("*"):
        if file.is_file():
            files_created += 1
            if len(sample_files) < 10:
                sample_files.append(file.relative_to(output_dir))
    
    print(f"Total files created: {files_created}")
    
    if sample_files:
        print("\nSample files created:")
        for f in sample_files:
            print(f"  - {f}")
        if files_created > 10:
            print(f"  ... and {files_created - 10} more files")
    
    # Show agent results
    print("\nAgent Execution Results:")
    print("-" * 40)
    for agent_name in ["requirements-analyst", "project-architect", "database-expert", 
                      "rapid-builder", "frontend-specialist", "api-integrator",
                      "devops-engineer", "quality-guardian"]:
        if agent_name in orchestrator.dependency_graph.completed:
            result = orchestrator.dependency_graph.results.get(agent_name)
            if result:
                print(f"  [OK] {agent_name}: {len(result.files_created)} files, {result.duration:.1f}s")
            else:
                print(f"  [OK] {agent_name}")
        elif agent_name in orchestrator.dependency_graph.failed:
            print(f"  [FAIL] {agent_name}")
        else:
            print(f"  [SKIP] {agent_name} (not executed)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOPPED] User cancelled")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        traceback.print_exc()