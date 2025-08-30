#!/usr/bin/env python3
"""Run test orchestration in mock mode to demonstrate agent swarm functionality"""

import sys
import os
from pathlib import Path

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / "lib"))

# Set mock mode environment variable
os.environ['MOCK_MODE'] = 'true'

# Import after setting mock mode
from lib.agent_logger import create_new_session
from lib.mock_anthropic import MockAnthropicRunner
from lib.agent_runtime import AgentContext, Tool, create_standard_tools
import yaml
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

async def run_mock_orchestration():
    """Run orchestration with mock agents"""
    
    # Load requirements
    with open('test_requirements.yaml', 'r') as f:
        requirements = yaml.safe_load(f)
    
    # Create session and mock runtime
    logger = create_new_session()
    runtime = MockAnthropicRunner(logger=logger)
    
    # Register standard tools
    for tool in create_standard_tools():
        runtime.register_tool(tool)
    
    # Create initial context
    context = AgentContext(
        project_requirements=requirements,
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase="planning"
    )
    
    # Define agent workflow for API service
    workflow = [
        ("requirements-analyst", "Parse and validate requirements"),
        ("project-architect", "Design system architecture"),
        ("database-expert", "Design database schema"),
        ("rapid-builder", "Build API scaffolding"),
        ("api-integrator", "Integrate external APIs"),
        ("frontend-specialist", "Create React frontend"),
        ("ai-specialist", "Implement AI categorization"),
        ("documentation-writer", "Generate API documentation"),
        ("quality-guardian", "Run tests and security audit"),
        ("devops-engineer", "Create Docker configuration")
    ]
    
    console.print(Panel.fit(
        "[bold cyan]Starting Agent Swarm Test Orchestration[/bold cyan]\n"
        f"Project: {requirements['project']['name']}\n"
        f"Type: {requirements['project']['type']}\n"
        f"Agents: {len(workflow)}",
        title="🤖 Agent Swarm"
    ))
    
    # Execute agents in sequence
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        for agent_name, description in workflow:
            task = progress.add_task(f"[cyan]{agent_name}[/cyan]: {description}", total=None)
            
            # Simulate agent execution
            success, result, context = await runtime.run_agent_async(
                agent_name=agent_name,
                agent_prompt=f"Execute {description} for {requirements['project']['name']}",
                context=context
            )
            
            if success:
                progress.update(task, description=f"[green]✓[/green] {agent_name}: {description}")
            else:
                progress.update(task, description=f"[red]✗[/red] {agent_name}: Failed")
            
            await asyncio.sleep(0.5)  # Brief pause for visibility
    
    # Summary
    console.print("\n[bold green]✅ Agent Swarm Execution Complete![/bold green]\n")
    
    # Show artifacts created
    console.print(Panel.fit(
        f"Completed Tasks: {len(context.completed_tasks)}\n"
        f"Artifacts Created: {len(context.artifacts)}\n"
        f"Decisions Made: {len(context.decisions)}",
        title="📊 Results"
    ))
    
    # List completed agents
    console.print("\n[bold]Agents Executed Successfully:[/bold]")
    for i, task in enumerate(context.completed_tasks, 1):
        console.print(f"  {i}. [green]✓[/green] {task}")
    
    logger.close_session()
    
    return context

if __name__ == "__main__":
    console.print("\n[bold yellow]Running in MOCK MODE - No API costs[/bold yellow]\n")
    context = asyncio.run(run_mock_orchestration())
    console.print("\n[bold cyan]Test orchestration completed successfully![/bold cyan]")