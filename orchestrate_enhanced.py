#!/usr/bin/env python3
"""
Enhanced Agent Swarm Orchestrator - Section 8 Implementation

Features:
- Adaptive workflow with dynamic agent selection
- Requirement tracking with ID mapping  
- Advanced error recovery and retry logic
- Real-time progress monitoring
- Parallel execution with dependency management
- Manual intervention points
- WebSocket-based dashboard integration

Usage:
    python orchestrate_enhanced.py --project-type=web_app --requirements=requirements.yaml --dashboard
    python orchestrate_enhanced.py --chain=project-architect,rapid-builder --interactive --progress
    python orchestrate_enhanced.py --resume-checkpoint checkpoints/workflow_*.json
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
from datetime import datetime

# Load environment variables from .env file if it exists
env_file = Path(".env")
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / "lib"))

from lib.agent_logger import ReasoningLogger, create_new_session
from lib.agent_runtime import (
    AnthropicAgentRunner, AgentContext, ModelType, Tool, 
    create_standard_tools, create_quality_tools
)
from lib.orchestration_enhanced import (
    AdaptiveWorkflowEngine, RequirementItem, AgentExecutionPlan,
    RequirementStatus, AgentExecutionStatus
)
from lib.progress_streamer import (
    ProgressStreamer, ProgressEventType, create_orchestration_progress_callback
)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("Warning: Rich not installed. Install with: pip install rich")

console = Console() if HAS_RICH else None


class EnhancedOrchestrator:
    """Enhanced orchestrator with Section 8 capabilities"""
    
    def __init__(self, api_key: Optional[str] = None, session_id: Optional[str] = None, 
                 enable_dashboard: bool = False):
        self.logger = create_new_session(session_id)
        self.runtime = AnthropicAgentRunner(api_key, self.logger)
        self.agents = self._load_agent_configs()
        
        # Enhanced orchestration components
        self.workflow_engine = AdaptiveWorkflowEngine(self.logger)
        self.progress_streamer = ProgressStreamer(self.logger) if enable_dashboard else None
        
        # Register progress callback
        if self.progress_streamer:
            callback = create_orchestration_progress_callback(self.progress_streamer)
            self.workflow_engine.add_progress_callback(callback)
        
        # Directories
        self.checkpoints_dir = Path("checkpoints")
        self.checkpoints_dir.mkdir(exist_ok=True)
        self.progress_dir = Path("progress")
        self.progress_dir.mkdir(exist_ok=True)
        
        # Register standard tools
        for tool in create_standard_tools():
            self.runtime.register_tool(tool)
        
        # Register quality validation tools
        for tool in create_quality_tools():
            self.runtime.register_tool(tool)
        
        # Add enhanced orchestration tools
        self._register_enhanced_tools()
    
    def _load_agent_configs(self) -> Dict:
        """Load agent configurations and prompts"""
        agents = {}
        agent_dir = Path(".claude/agents")
        
        if not agent_dir.exists():
            self.logger.log_error("orchestrator", "Agent directory not found: .claude/agents")
            return agents
        
        # Load each agent's prompt from their .md files
        for agent_file in agent_dir.glob("*.md"):
            agent_name = agent_file.stem
            content = agent_file.read_text()
            
            # Parse YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1])
                    prompt = parts[2].strip()
                    
                    agents[agent_name] = {
                        "name": agent_name,
                        "model": frontmatter.get("model", "sonnet"),
                        "tools": frontmatter.get("tools", []),
                        "prompt": prompt,
                        "description": frontmatter.get("description", "")
                    }
        
        self.logger.log_reasoning(
            "orchestrator",
            f"Loaded {len(agents)} agent configurations",
            "Agent configs parsed from .claude/agents/*.md"
        )
        
        return agents
    
    def _register_enhanced_tools(self):
        """Register enhanced orchestration tools"""
        
        async def adaptive_agent_selection(
            reasoning: str, 
            requirements: List[str], 
            context: AgentContext
        ) -> str:
            """Dynamically select optimal agents for requirements"""
            self.logger.log_reasoning("orchestrator", reasoning, "Adaptive agent selection")
            
            # Parse requirements into RequirementItems
            parsed_reqs = {}
            for idx, req in enumerate(requirements):
                req_id = f"DYNAMIC-{idx+1:03d}"
                assigned_agents, priority = self.workflow_engine._analyze_feature_requirements(req)
                
                parsed_reqs[req_id] = RequirementItem(
                    id=req_id,
                    description=req,
                    priority=priority,
                    assigned_agents=assigned_agents
                )
            
            # Create execution plan
            available_agents = list(self.agents.keys())
            plans = {}
            
            for req_id, req_item in parsed_reqs.items():
                for agent in req_item.assigned_agents:
                    if agent in available_agents:
                        if agent not in plans:
                            plans[agent] = AgentExecutionPlan(
                                agent_name=agent,
                                requirements=[],
                                dependencies=[],
                                priority=req_item.priority
                            )
                        plans[agent].requirements.append(req_id)
            
            # Sort by priority
            selected_agents = sorted(plans.keys(), key=lambda a: plans[a].priority)
            
            return f"Selected agents: {', '.join(selected_agents)} for {len(requirements)} requirements"
        
        self.runtime.register_tool(Tool(
            name="adaptive_agent_selection",
            description="Dynamically select optimal agents for given requirements",
            parameters={
                "requirements": {"type": "array", "description": "List of requirements", "required": True}
            },
            function=adaptive_agent_selection
        ))
        
        async def checkpoint_workflow_state(reasoning: str, checkpoint_name: str) -> str:
            """Save enhanced checkpoint with full workflow state"""
            checkpoint_file = self.checkpoints_dir / f"{checkpoint_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            self.workflow_engine.save_checkpoint(checkpoint_file)
            
            if self.progress_streamer:
                await self.progress_streamer.notify_checkpoint_saved(
                    str(checkpoint_file), 
                    self.workflow_engine.workflow_id
                )
            
            return f"Enhanced checkpoint saved: {checkpoint_file}"
        
        self.runtime.register_tool(Tool(
            name="checkpoint_workflow_state",
            description="Save comprehensive workflow checkpoint",
            parameters={
                "checkpoint_name": {"type": "string", "description": "Checkpoint name", "required": True}
            },
            function=checkpoint_workflow_state
        ))
        
        async def request_manual_intervention(
            reasoning: str, 
            agent_name: str, 
            issue_description: str
        ) -> str:
            """Request manual intervention for failed agent"""
            self.logger.log_reasoning("orchestrator", reasoning, f"Manual intervention for {agent_name}")
            
            if self.progress_streamer:
                await self.progress_streamer.notify_manual_intervention(
                    agent_name,
                    issue_description,
                    ["Skip", "Retry with modifications", "Abort workflow"]
                )
            
            return f"Manual intervention requested for {agent_name}: {issue_description}"
        
        self.runtime.register_tool(Tool(
            name="request_manual_intervention", 
            description="Request manual intervention for agent issues",
            parameters={
                "agent_name": {"type": "string", "description": "Agent needing intervention", "required": True},
                "issue_description": {"type": "string", "description": "Description of the issue", "required": True}
            },
            function=request_manual_intervention
        ))
    
    async def execute_enhanced_workflow(
        self,
        project_type: str,
        requirements: Dict,
        interactive: bool = False,
        checkpoint_file: Optional[str] = None,
        max_parallel: int = 3
    ) -> bool:
        """Execute enhanced workflow with all Section 8 capabilities"""
        
        self.workflow_engine.max_parallel_agents = max_parallel
        
        # Load checkpoint if provided
        if checkpoint_file and Path(checkpoint_file).exists():
            if self.workflow_engine.load_checkpoint(Path(checkpoint_file)):
                console.print(Panel(
                    f"[green]Checkpoint loaded successfully[/green]\n"
                    f"Workflow ID: {self.workflow_engine.workflow_id}\n"
                    f"Progress: {self.workflow_engine.progress.overall_completion:.1f}%",
                    title="Resuming from Checkpoint",
                    border_style="green"
                ))
            else:
                console.print("[red]Failed to load checkpoint, starting fresh[/red]")
                return False
        else:
            # Parse requirements with intelligent ID mapping
            self.workflow_engine.parse_requirements_with_ids(requirements)
            
            # Create adaptive execution plan
            available_agents = list(self.agents.keys())
            self.workflow_engine.create_adaptive_execution_plan(available_agents)
        
        # Start progress streaming
        if self.progress_streamer:
            await self.progress_streamer.start_websocket_server()
            await self.progress_streamer.notify_workflow_started(
                self.workflow_engine.workflow_id,
                len(self.workflow_engine.requirements),
                len(self.workflow_engine.agent_plans)
            )
        
        # Initialize context
        context = AgentContext(
            project_requirements=requirements,
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="enhanced_orchestration"
        )
        
        try:
            # Execute workflow with adaptive orchestration
            success = await self._execute_adaptive_workflow(context, interactive)
            
            # Generate final summary
            summary = self.workflow_engine.get_execution_summary()
            
            # Notify completion
            if self.progress_streamer:
                await self.progress_streamer.notify_workflow_completed(
                    self.workflow_engine.workflow_id,
                    success,
                    summary
                )
            
            # Display results
            self._display_workflow_results(success, summary)
            
            return success
        
        finally:
            if self.progress_streamer:
                await self.progress_streamer.stop_websocket_server()
    
    async def _execute_adaptive_workflow(
        self, 
        context: AgentContext, 
        interactive: bool
    ) -> bool:
        """Execute workflow with adaptive agent scheduling"""
        
        completed_agents = set()
        failed_agents = set()
        
        while True:
            # Get agents ready to execute
            ready_agents = self.workflow_engine.get_ready_agents()
            ready_agents = [a for a in ready_agents if a not in completed_agents and a not in failed_agents]
            
            if not ready_agents:
                # Check if we're done or blocked
                remaining_agents = set(self.workflow_engine.agent_plans.keys()) - completed_agents - failed_agents
                if not remaining_agents:
                    break  # All done
                
                # Check for blocked agents
                blocked = True
                for agent in remaining_agents:
                    plan = self.workflow_engine.agent_plans[agent]
                    if plan.status != AgentExecutionStatus.BLOCKED:
                        blocked = False
                        break
                
                if blocked:
                    self.logger.log_error("orchestrator", "All remaining agents are blocked")
                    return False
                
                # Wait for running agents
                await asyncio.sleep(2)
                continue
            
            # Execute agents in parallel (up to max_parallel)
            batch_size = min(len(ready_agents), self.workflow_engine.max_parallel_agents)
            batch = ready_agents[:batch_size]
            
            if interactive and batch:
                if not Confirm.ask(f"Execute agents: {', '.join(batch)}?"):
                    console.print("[yellow]Batch skipped[/yellow]")
                    for agent in batch:
                        completed_agents.add(agent)
                    continue
            
            # Execute batch in parallel
            tasks = []
            for agent_name in batch:
                if agent_name in self.agents:
                    task = self._execute_agent_with_enhanced_features(
                        agent_name, context, interactive
                    )
                    tasks.append((agent_name, task))
            
            # Wait for batch completion
            results = await asyncio.gather(
                *[task for _, task in tasks], 
                return_exceptions=True
            )
            
            # Process results
            for i, (agent_name, result) in enumerate(zip([name for name, _ in tasks], results)):
                if isinstance(result, Exception):
                    self.logger.log_error("orchestrator", f"Agent {agent_name} failed with exception: {result}")
                    failed_agents.add(agent_name)
                elif result[0]:  # Success
                    completed_agents.add(agent_name)
                    # Update context with results
                    _, _, updated_context = result
                    context.completed_tasks.extend(updated_context.completed_tasks)
                    context.artifacts.update(updated_context.artifacts)
                    context.decisions.extend(updated_context.decisions)
                else:
                    failed_agents.add(agent_name)
            
            # Update progress
            self.workflow_engine._update_progress()
            
            # Save periodic checkpoint
            if len(completed_agents) % 3 == 0:  # Every 3 agents
                checkpoint_file = self.checkpoints_dir / f"auto_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.workflow_engine.save_checkpoint(checkpoint_file)
        
        # Check final success
        total_agents = len(self.workflow_engine.agent_plans)
        success_rate = len(completed_agents) / total_agents if total_agents > 0 else 0
        
        return success_rate >= 0.8  # 80% success rate considered successful
    
    async def _execute_agent_with_enhanced_features(
        self,
        agent_name: str,
        context: AgentContext,
        interactive: bool
    ) -> Tuple[bool, str, AgentContext]:
        """Execute agent with all enhanced Section 8 features"""
        
        if agent_name not in self.agents:
            self.logger.log_error("orchestrator", f"Unknown agent: {agent_name}")
            return False, "Agent not found", context
        
        agent_config = self.agents[agent_name]
        
        # Update progress streamer
        if self.progress_streamer:
            plan = self.workflow_engine.agent_plans[agent_name]
            await self.progress_streamer.update_agent_status(agent_name, plan)
        
        # Execute with retry logic and error recovery
        success, result, updated_context = await self.workflow_engine.execute_agent_with_retry(
            agent_name,
            self.runtime,
            context,
            agent_config
        )
        
        # Update progress streamer with final result
        if self.progress_streamer:
            plan = self.workflow_engine.agent_plans[agent_name]
            await self.progress_streamer.update_agent_status(agent_name, plan)
            
            # Update requirement statuses
            for req_id in plan.requirements:
                if req_id in self.workflow_engine.requirements:
                    requirement = self.workflow_engine.requirements[req_id]
                    await self.progress_streamer.update_requirement_status(req_id, requirement)
        
        return success, result, updated_context
    
    def _display_workflow_results(self, success: bool, summary: Dict):
        """Display comprehensive workflow results"""
        if not HAS_RICH:
            return
        
        progress = summary["progress"]
        
        # Main results panel
        status_color = "green" if success else "red"
        status_text = "SUCCESS" if success else "FAILED"
        
        console.print(Panel(
            f"[bold {status_color}]Workflow {status_text}[/bold {status_color}]\n\n"
            f"Workflow ID: {summary['workflow_id']}\n"
            f"Overall Completion: {progress['overall_completion']:.1f}%\n"
            f"Requirements: {progress['completed_requirements']}/{progress['total_requirements']} completed\n"
            f"Agents: {progress['completed_agents']}/{progress['total_agents']} successful\n"
            f"Duration: {progress['started_at']} - {progress['updated_at']}",
            title="Enhanced Orchestration Results",
            border_style=status_color
        ))
        
        # Requirements table
        if summary.get("requirements"):
            req_table = Table(title="Requirements Status")
            req_table.add_column("ID", style="cyan")
            req_table.add_column("Description", style="white")
            req_table.add_column("Status", style="green")
            req_table.add_column("Completion", style="yellow")
            req_table.add_column("Assigned Agents", style="blue")
            
            for req_id, req_data in summary["requirements"].items():
                status_color = {
                    "completed": "green",
                    "failed": "red",
                    "blocked": "orange",
                    "pending": "yellow"
                }.get(req_data["status"], "white")
                
                req_table.add_row(
                    req_id,
                    req_data["description"][:50] + ("..." if len(req_data["description"]) > 50 else ""),
                    f"[{status_color}]{req_data['status'].upper()}[/{status_color}]",
                    f"{req_data['completion_percentage']:.1f}%",
                    ", ".join(req_data["assigned_agents"][:2])  # Show first 2 agents
                )
            
            console.print(req_table)
        
        # Agent execution table
        if summary.get("agent_plans"):
            agent_table = Table(title="Agent Execution Summary")
            agent_table.add_column("Agent", style="cyan")
            agent_table.add_column("Status", style="green")
            agent_table.add_column("Duration", style="yellow")
            agent_table.add_column("Retries", style="orange")
            agent_table.add_column("Requirements", style="blue")
            
            for agent_name, plan_data in summary["agent_plans"].items():
                status_color = {
                    "completed": "green",
                    "failed": "red",
                    "running": "yellow"
                }.get(plan_data["status"], "white")
                
                duration = f"{plan_data['execution_time']:.1f}s" if plan_data.get('execution_time') else "N/A"
                
                agent_table.add_row(
                    agent_name,
                    f"[{status_color}]{plan_data['status'].upper()}[/{status_color}]",
                    duration,
                    str(plan_data['current_retry']),
                    str(len(plan_data['requirements']))
                )
            
            console.print(agent_table)


async def main():
    parser = argparse.ArgumentParser(description="Enhanced Agent Swarm Orchestrator - Section 8")
    parser.add_argument("--project-type", choices=["web_app", "api_service", "ai_solution", "full_stack_api"])
    parser.add_argument("--requirements", help="Path to requirements.yaml")
    parser.add_argument("--chain", help="Execute agents in chain (comma-separated)")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--resume-checkpoint", help="Resume from checkpoint file")
    parser.add_argument("--dashboard", action="store_true", help="Enable real-time dashboard")
    parser.add_argument("--progress", action="store_true", help="Show detailed progress")
    parser.add_argument("--max-parallel", type=int, default=3, help="Max parallel agents")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Handle API key
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    
    # Create enhanced orchestrator
    orchestrator = EnhancedOrchestrator(api_key, enable_dashboard=args.dashboard or args.progress)
    
    try:
        if args.project_type and args.requirements:
            # Enhanced workflow execution
            with open(args.requirements) as f:
                requirements = yaml.safe_load(f)
            
            if HAS_RICH:
                console.print(Panel(
                    f"[bold]Enhanced {args.project_type} Workflow[/bold]\n" +
                    f"Project: {requirements.get('project', {}).get('name', 'Unknown')}\n" +
                    f"Requirements: {args.requirements}\n" +
                    f"Dashboard: {'Enabled' if args.dashboard else 'Disabled'}\n" +
                    f"Max Parallel: {args.max_parallel}",
                    border_style="green"
                ))
            
            success = await orchestrator.execute_enhanced_workflow(
                args.project_type,
                requirements,
                interactive=args.interactive,
                checkpoint_file=args.resume_checkpoint,
                max_parallel=args.max_parallel
            )
            
            orchestrator.logger.close_session()
            sys.exit(0 if success else 1)
        
        elif args.chain:
            # Chain execution (simplified for compatibility)
            agents = [a.strip() for a in args.chain.split(",")]
            if HAS_RICH:
                console.print(Panel(
                    f"[bold]Executing Enhanced Chain[/bold]\n" +
                    f"Agents: {' → '.join(agents)}",
                    border_style="blue"
                ))
            
            # Create simple requirements for chain
            requirements = {
                "project": {"name": "Chain Execution"},
                "features": [f"Execute {agent}" for agent in agents]
            }
            
            success = await orchestrator.execute_enhanced_workflow(
                "api_service",  # Default project type
                requirements,
                interactive=args.interactive,
                max_parallel=1  # Sequential for chain
            )
            
            orchestrator.logger.close_session()
            sys.exit(0 if success else 1)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        if HAS_RICH:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        orchestrator.logger.close_session()
        sys.exit(1)
    except Exception as e:
        if HAS_RICH:
            console.print(f"[red]Error: {str(e)}[/red]")
        if args.verbose:
            import traceback
            traceback.print_exc()
        orchestrator.logger.close_session()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())