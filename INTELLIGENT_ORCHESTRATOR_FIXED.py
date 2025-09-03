#!/usr/bin/env python3
"""
FIXED INTELLIGENT ORCHESTRATOR - Handles both sync and async execution
"""

import sys
import os
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

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

class DependencyGraph:
    """Manages agent dependencies and execution order"""
    
    def __init__(self):
        self.tasks: Dict[str, AgentTask] = {}
        self.completed: Set[str] = set()
        self.in_progress: Set[str] = set()
        self.failed: Set[str] = set()
    
    def add_task(self, task: AgentTask):
        self.tasks[task.name] = task
    
    def get_ready_tasks(self) -> List[str]:
        ready = []
        for name, task in self.tasks.items():
            if name in self.completed or name in self.in_progress or name in self.failed:
                continue
            
            if all(dep in self.completed for dep in task.dependencies):
                ready.append(name)
        
        ready.sort(key=lambda x: self.tasks[x].priority, reverse=True)
        return ready
    
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
    
    def mark_completed(self, task_name: str):
        self.in_progress.discard(task_name)
        self.completed.add(task_name)
    
    def mark_in_progress(self, task_name: str):
        self.in_progress.add(task_name)
    
    def mark_failed(self, task_name: str):
        self.in_progress.discard(task_name)
        self.failed.add(task_name)
    
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

class IntelligentOrchestrator:
    """Orchestrates agent execution with optimal parallelization"""
    
    def __init__(self, runner: AnthropicAgentRunner):
        self.runner = runner
        self.dependency_graph = DependencyGraph()
        self.context = None
        self.requirements = None
        # Check if runner has async method
        self.has_async = hasattr(runner, 'run_agent_async')
        
    def define_quickshop_workflow(self):
        """Define the QuickShop MVP workflow with dependencies"""
        
        # Level 0: No dependencies
        self.dependency_graph.add_task(AgentTask(
            name="requirements-analyst",
            dependencies=[],
            can_parallel=False,
            priority=100,
            estimated_time=10
        ))
        
        # Level 1: Depends on requirements
        self.dependency_graph.add_task(AgentTask(
            name="project-architect",
            dependencies=["requirements-analyst"],
            can_parallel=False,
            priority=90,
            estimated_time=15
        ))
        
        # Level 2: Can work in parallel after architecture
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
        
        # Level 3: Integration phase
        self.dependency_graph.add_task(AgentTask(
            name="api-integrator",
            dependencies=["rapid-builder", "frontend-specialist"],
            can_parallel=False,
            priority=60,
            estimated_time=20
        ))
        
        # Level 4: Deployment and validation
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
    
    async def execute_agent(self, agent_name: str) -> Tuple[bool, str]:
        """Execute a single agent"""
        print(f"\n{'='*60}")
        print(f"[AGENT] {agent_name}")
        print(f"  Model: {get_optimal_model(agent_name)}")
        print(f"  Started: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
        
        self.dependency_graph.mark_in_progress(agent_name)
        
        try:
            # Build agent prompt
            prompt = f"""You are {agent_name}, a specialized AI agent building a QuickShop MVP e-commerce application.

Project Requirements:
{json.dumps(self.requirements, indent=2)}

Previous agents completed: {list(self.dependency_graph.completed)}

Output directory: {self.context.artifacts.get('output_dir')}

Your role: Complete your specialized tasks for this project. Create actual files with working code.
Use the write_file tool to create files with complete content."""
            
            # Run agent
            if self.has_async:
                # Use async method if available
                success, result, updated_context = await self.runner.run_agent_async(
                    agent_name=agent_name,
                    agent_prompt=prompt,
                    context=self.context,
                    model=get_optimal_model(agent_name),
                    max_iterations=2
                )
            else:
                # Wrap synchronous method in executor
                loop = asyncio.get_event_loop()
                success, result, updated_context = await loop.run_in_executor(
                    None,
                    self.runner.run_agent,
                    agent_name,
                    prompt,
                    self.context,
                    get_optimal_model(agent_name),
                    2  # max_iterations
                )
            
            if success:
                print(f"  Status: [SUCCESS] at {datetime.now().strftime('%H:%M:%S')}")
                self.dependency_graph.mark_completed(agent_name)
                self.context = updated_context
                
                # Update context
                self.context.completed_tasks.append({
                    "agent": agent_name,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                })
                
                # Check files created
                output_dir = Path(self.context.artifacts.get('output_dir', '.'))
                files = list(output_dir.rglob("*"))
                file_count = len([f for f in files if f.is_file()])
                print(f"  Total files in project: {file_count}")
                
                return True, result
            else:
                print(f"  Status: [FAILED]")
                self.dependency_graph.mark_failed(agent_name)
                return False, str(result)
                
        except Exception as e:
            print(f"  Status: [ERROR] {str(e)}")
            self.dependency_graph.mark_failed(agent_name)
            return False, str(e)
    
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
    
    async def orchestrate(self, context: AgentContext, requirements: Dict):
        """Main orchestration logic"""
        self.context = context
        self.requirements = requirements
        
        print("=" * 80)
        print("INTELLIGENT ORCHESTRATOR")
        print("=" * 80)
        print()
        
        # Define workflow
        self.define_quickshop_workflow()
        
        print("Workflow Analysis:")
        print(f"  Total agents: {len(self.dependency_graph.tasks)}")
        print(f"  Execution strategy: Optimized parallel/sequential")
        print(f"  Async support: {'Yes' if self.has_async else 'No (using sync wrapper)'}")
        print()
        
        # Execute workflow
        iteration = 0
        while True:
            iteration += 1
            
            # Get ready tasks
            ready_tasks = self.dependency_graph.get_ready_tasks()
            
            if not ready_tasks:
                # Check if we're done or stuck
                status = self.dependency_graph.get_status()
                
                if status["pending"] == 0 and status["in_progress"] == 0:
                    print("\n" + "=" * 80)
                    print("ORCHESTRATION COMPLETE")
                    print("=" * 80)
                    print(f"  Completed: {status['completed']}")
                    print(f"  Failed: {status['failed']}")
                    print(f"  Progress: {status['progress_percentage']:.1f}%")
                    break
                    
                # Wait for in-progress tasks
                if status["in_progress"] > 0:
                    await asyncio.sleep(1)
                    continue
                    
                # We're stuck
                print("\n[WARNING] Workflow stuck - some dependencies failed")
                break
            
            # Get parallel groups
            parallel_groups = self.dependency_graph.get_parallel_groups(ready_tasks)
            
            print(f"\n[ITERATION {iteration}]")
            print(f"  Ready tasks: {ready_tasks}")
            print(f"  Parallel groups: {parallel_groups}")
            
            # Execute each group
            for group in parallel_groups:
                if len(group) > 1:
                    print(f"\n[PARALLEL EXECUTION] {group}")
                    results = await self.execute_parallel_group(group)
                    
                    for agent, (success, _) in results.items():
                        if success:
                            print(f"  [OK] {agent}")
                        else:
                            print(f"  [FAIL] {agent}")
                else:
                    print(f"\n[SEQUENTIAL EXECUTION] {group[0]}")
                    success, _ = await self.execute_agent(group[0])
                    
                    if success:
                        print(f"  [OK] {group[0]}")
                    else:
                        print(f"  [FAIL] {group[0]}")
            
            # Show progress
            status = self.dependency_graph.get_status()
            print(f"\n[PROGRESS] {status['completed']}/{status['total']} agents completed ({status['progress_percentage']:.1f}%)")

async def main():
    """Main execution"""
    
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
    await orchestrator.orchestrate(context, requirements)
    execution_time = time.time() - start_time
    
    # Save final context
    context_file = output_dir / "final_context.json"
    with open(context_file, 'w', encoding='utf-8') as f:
        json.dump(context.to_dict(), f, indent=2, default=str, ensure_ascii=True)
    
    # Final report
    print()
    print("=" * 80)
    print(f"Execution time: {execution_time:.2f} seconds")
    print(f"Output: {output_dir}")
    
    # List files created
    files_created = 0
    for file in output_dir.rglob("*"):
        if file.is_file():
            files_created += 1
    print(f"Files created: {files_created}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOPPED] User cancelled")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
